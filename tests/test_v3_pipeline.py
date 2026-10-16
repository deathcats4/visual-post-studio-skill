"""Runtime smoke tests: production integrity, approval freshness and public packaging."""
import importlib.util
import json
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import zipfile
import zlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPTS=ROOT/'scripts'


def png_file(path,w,h,channel=0):
    path.parent.mkdir(parents=True,exist_ok=True)
    def chunk(t,d):return struct.pack('>I',len(d))+t+d+struct.pack('>I',zlib.crc32(t+d)&0xffffffff)
    ihdr=struct.pack('>IIBBBBB',w,h,8,2,0,0,0)
    image=b''.join(b'\x00'+bytes((channel,120,180))*w for _ in range(h))
    path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',ihdr)+chunk(b'IDAT',zlib.compress(image))+chunk(b'IEND',b''))


class Pipeline(unittest.TestCase):
    def run_cmd(self,*args):
        return subprocess.run([sys.executable,*map(str,args)],text=True,capture_output=True)

    def prepare(self,td,count=2):
        create=self.run_cmd(SCRIPTS/'new_project.py','--slug','caravan','--topic','出门旅行常用清单','--out',td,'--pages',str(count),'--canvas','3:4','--pixels','120x160')
        self.assertEqual(create.returncode,0,create.stdout+create.stderr)
        proj=Path(td)/'caravan'
        for i in range(1,count+1): png_file(proj/'images/final'/f'{i:02d}.png',120,160,channel=i*20)
        m=json.loads((proj/'manifest.json').read_text(encoding='utf-8'))
        m['image_generation_status']='complete'
        (proj/'manifest.json').write_text(json.dumps(m,ensure_ascii=False),encoding='utf-8')
        return proj

    def qa(self,proj):
        report=proj/'reviews'/'qa-report.json'
        result=self.run_cmd(SCRIPTS/'qa_images.py',proj,'--strict','--report',report)
        return result,report

    def test_static_skill_no_subject_lockin(self):
        body=(ROOT/'SKILL.md').read_text(encoding='utf-8')
        self.assertNotIn('Zotero',body)
        self.assertNotIn('1080×1440',body)
        self.assertNotIn('7页',body)
        r=self.run_cmd(SCRIPTS/'validate_skill.py',ROOT)
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)

    def test_two_topic_inputs_do_not_force_visual_theme(self):
        for topic in ('露营装备', '职场穿搭'):
            with self.subTest(topic=topic), tempfile.TemporaryDirectory() as td:
                r=self.run_cmd(SCRIPTS/'new_project.py','--slug','topic','--topic',topic,'--out',td,'--pages','3','--canvas','1:1')
                self.assertEqual(r.returncode,0,r.stdout+r.stderr)
                data=json.loads((Path(td)/'topic'/'manifest.json').read_text(encoding='utf-8'))
                self.assertEqual(data['topic'],topic)
                self.assertEqual(data['style'],'auto')
                self.assertEqual(data['canvas'],'1:1')

    def test_qa_hash_invalidates_after_edit(self):
        with tempfile.TemporaryDirectory() as td:
            pr=self.prepare(td)
            result,rep=self.qa(pr)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            good=self.run_cmd(SCRIPTS/'verify_final_qa.py',pr,'--report',rep)
            self.assertEqual(good.returncode,0,good.stdout+good.stderr)
            png_file(pr/'images/final'/'02.png',120,160,channel=77)
            bad=self.run_cmd(SCRIPTS/'verify_final_qa.py',pr,'--report',rep)
            self.assertNotEqual(bad.returncode,0)
            self.assertIn('changed since QA',bad.stdout)

    def test_qa_detects_duplicate_page_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            pr=self.prepare(td)
            (pr/'images/final'/'02.png').write_bytes((pr/'images/final'/'01.png').read_bytes())
            result,_=self.qa(pr)
            self.assertNotEqual(result.returncode,0)
            self.assertIn('Identical image bytes',result.stdout)

    def test_qa_detects_wrong_dimensions(self):
        with tempfile.TemporaryDirectory() as td:
            pr=self.prepare(td)
            png_file(pr/'images/final'/'01.png',120,120,channel=20)
            result,_=self.qa(pr)
            self.assertNotEqual(result.returncode,0)
            self.assertIn('!= requested',result.stdout)

    def test_review_is_explicit_not_faked(self):
        with tempfile.TemporaryDirectory() as td:
            pr=self.prepare(td)
            result,rep=self.qa(pr)
            self.assertEqual(result.returncode,0)
            bad=self.run_cmd(SCRIPTS/'verify_final_qa.py',pr,'--report',rep,'--require-review')
            self.assertNotEqual(bad.returncode,0)
            info=json.loads(rep.read_text(encoding='utf-8'))
            manual={'schema_version':1,'reviewed_by':'sample human reviewer','reviewed_at':'2026-10-13T12:00:00Z','pages':[
                {'file':page['file'],'sha256':page['sha256'],'status':'approved','source_fidelity':'checked','text_and_readability':'checked','visual_consistency':'checked','rights':'checked'}
                for page in info['pages']
            ]}
            (pr/'reviews'/'page-review.json').write_text(json.dumps(manual),encoding='utf-8')
            ok=self.run_cmd(SCRIPTS/'verify_final_qa.py',pr,'--report',rep,'--require-review')
            self.assertEqual(ok.returncode,0,ok.stdout+ok.stderr)
            # Also invalidate manual review when page changes.
            png_file(pr/'images/final'/'01.png',120,160,channel=44)
            bad2=self.run_cmd(SCRIPTS/'verify_final_qa.py',pr,'--report',rep,'--require-review')
            self.assertNotEqual(bad2.returncode,0)

    def test_public_runtime_zip_removes_samples(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'public.zip'
            run=self.run_cmd(SCRIPTS/'package_skill.py','--root',ROOT,'--output',p)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            with zipfile.ZipFile(p) as z:
                names=z.namelist()
                self.assertIn('visual-post-studio/SKILL.md',names)
                self.assertIn('visual-post-studio/references/visual-dna.md',names)
                self.assertIn('visual-post-studio/scripts/qa_images.py',names)
                self.assertNotIn('visual-post-studio/tests/test_v3_pipeline.py',names)
                self.assertFalse(any(name.lower().endswith(('.png','.jpg','.jpeg')) for name in names))
                style=json.loads(z.read('visual-post-studio/styles/editorial-tech/style.json'))
                self.assertEqual(style['references'],[])
                z.extractall(Path(td)/'unzipped')
            valid=self.run_cmd(Path(td)/'unzipped'/'visual-post-studio'/'scripts'/'validate_skill.py',Path(td)/'unzipped'/'visual-post-studio')
            self.assertEqual(valid.returncode,0,valid.stdout+valid.stderr)

    def test_private_runtime_keeps_four_reference_pages(self):
        with tempfile.TemporaryDirectory() as td:
            source=Path(td)/'visual-post-studio'
            shutil.copytree(ROOT,source,ignore=shutil.ignore_patterns(
                '.git','.local','__pycache__','*.pyc','personal','projects','outputs','*.png'))
            examples=source/'styles'/'editorial-tech'/'examples'
            filenames=['cover-light.png','cover-dark.png','process.png','screenshot-led.png']
            for index,name in enumerate(filenames):
                png_file(examples/name,12,16,channel=index*20)
            style_file=source/'styles'/'editorial-tech'/'style.json'
            style=json.loads(style_file.read_text(encoding='utf-8'))
            style['references']=['examples/'+name for name in filenames]
            style_file.write_text(json.dumps(style),encoding='utf-8')
            p=Path(td)/'examples.zip'
            run=self.run_cmd(SCRIPTS/'package_skill.py','--root',source,'--output',p,'--include-example-images')
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            with zipfile.ZipFile(p) as z:
                names=z.namelist()
                visual_assets=[n for n in names if n.startswith('visual-post-studio/styles/editorial-tech/examples/') and n.endswith('.png')]
                self.assertEqual(len(visual_assets),4)
                for name in filenames:
                    self.assertEqual(z.read('visual-post-studio/styles/editorial-tech/examples/'+name),(examples/name).read_bytes())


if __name__=='__main__':unittest.main()
