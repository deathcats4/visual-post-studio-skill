import json
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'scripts'


def write_png(path, width, height):
    path.parent.mkdir(parents=True,exist_ok=True)
    def chunk(t, data):
        return struct.pack('>I',len(data))+t+data+struct.pack('>I',zlib.crc32(t+data)&0xffffffff)
    ihdr=struct.pack('>IIBBBBB',width,height,8,2,0,0,0)
    pixels=b''.join(b'\x00'+b'\xff\xff\xff'*width for _ in range(height))
    png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',ihdr)+chunk(b'IDAT',zlib.compress(pixels))+chunk(b'IEND',b'')
    path.write_bytes(png)


class TestHelpers(unittest.TestCase):
    def run_cmd(self,*args):
        return subprocess.run([sys.executable,*map(str,args)], text=True, capture_output=True)

    def test_agent_skill_bundle(self):
        p=self.run_cmd(SCRIPT/'validate_skill.py',ROOT)
        self.assertEqual(p.returncode,0,p.stderr+p.stdout)

    def test_new_project_and_structural_validator(self):
        with tempfile.TemporaryDirectory() as td:
            p=self.run_cmd(SCRIPT/'new_project.py','--topic','city walk','--slug','city-walk','--out',td,'--pages','2','--canvas','3:4','--pixels','300x400')
            self.assertEqual(p.returncode,0,p.stderr+p.stdout)
            pr=Path(td)/'city-walk'
            m=json.loads((pr/'manifest.json').read_text(encoding='utf-8'))
            self.assertEqual(m['page_count'],2)
            self.assertEqual(m['platform'],'unspecified')
            fail=self.run_cmd(SCRIPT/'validate_project.py',pr,'--strict')
            self.assertNotEqual(fail.returncode,0)
            write_png(pr/'images/final/01.png',300,400)
            write_png(pr/'images/final/02.png',300,400)
            m['image_generation_status']='complete'
            (pr/'manifest.json').write_text(json.dumps(m),encoding='utf-8')
            ok=self.run_cmd(SCRIPT/'validate_project.py',pr,'--strict')
            self.assertEqual(ok.returncode,0,ok.stderr+ok.stdout)
            write_png(pr/'images/final/02.png',301,400)
            fail2=self.run_cmd(SCRIPT/'validate_project.py',pr,'--strict')
            self.assertNotEqual(fail2.returncode,0)

    def test_new_style_does_not_fabricate_image_learning(self):
        with tempfile.TemporaryDirectory() as td:
            source=Path(td)/'my-ref.png'
            write_png(source,30,40)
            p=self.run_cmd(SCRIPT/'new_style_pack.py','--id','my-style','--out',Path(td)/'styles','--reference',source)
            self.assertEqual(p.returncode,0,p.stderr+p.stdout)
            pack=Path(td)/'styles/my-style'
            info=json.loads((pack/'style.json').read_text(encoding='utf-8'))
            self.assertEqual(info['image_analysis_status'],'pending_agent_inspection')
            self.assertTrue((pack/'examples/reference-01.png').exists())
            self.assertIn('UNCONFIRMED',(pack/'attribution.md').read_text(encoding='utf-8'))

    def test_reject_existing_project(self):
        with tempfile.TemporaryDirectory() as td:
            args=[SCRIPT/'new_project.py','--topic','hello','--slug','test','--out',td]
            a=self.run_cmd(*args)
            b=self.run_cmd(*args)
            self.assertEqual(a.returncode,0)
            self.assertNotEqual(b.returncode,0)

if __name__=='__main__':
    unittest.main()
