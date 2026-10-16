"""Regression cases for final-image integrity, public packaging and failed inputs."""
import hashlib
import importlib.util
import json
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from test_scripts import write_png

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'scripts'


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Regressions(unittest.TestCase):
    def run_cmd(self, *args):
        return subprocess.run([sys.executable, *map(str, args)], text=True, capture_output=True)

    def project(self, parent, count=1, status='complete'):
        project = Path(parent) / 'post'
        (project / 'images' / 'final').mkdir(parents=True)
        manifest = {
            'schema_version': 1, 'page_count': count, 'canvas': '3:4',
            'target_pixels': [120, 160], 'image_generation_status': status,
        }
        (project / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
        write_png(project / 'images' / 'final' / '01.png', 120, 160)
        return project

    def qa(self, project):
        report = project / 'reviews' / 'qa-report.json'
        result = self.run_cmd(SCRIPTS / 'qa_images.py', project, '--strict', '--report', report)
        return result, report

    def header_only_png(self):
        return b'\x89PNG\r\n\x1a\n' + struct.pack('>I', 13) + b'IHDR' + struct.pack('>II', 120, 160)

    def test_valid_png_and_jpeg_are_fully_decoded(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as td:
            project = self.project(td, count=2)
            Image.new('RGB', (120, 160), (20, 80, 160)).save(project / 'images' / 'final' / '02.jpg')
            result, report = self.qa(project)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            data = json.loads(report.read_text(encoding='utf-8'))
            self.assertEqual(data.get('image_integrity_check'), 'full_decode')
            self.assertEqual([p.get('image_integrity') for p in data['pages']], ['full_decode', 'full_decode'])

    def test_strict_qa_rejects_header_only_png(self):
        with tempfile.TemporaryDirectory() as td:
            project = self.project(td)
            (project / 'images' / 'final' / '01.png').write_bytes(self.header_only_png())
            result, report = self.qa(project)
            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertEqual(json.loads(report.read_text(encoding='utf-8'))['automated_status'], 'failed')

    def test_strict_qa_rejects_bad_png_crc_and_truncated_jpeg(self):
        from PIL import Image
        for kind in ('bad-png-crc', 'truncated-jpeg'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as td:
                project = self.project(td)
                file = project / 'images' / 'final' / '01.png'
                if kind == 'bad-png-crc':
                    data = bytearray(file.read_bytes())
                    data[29] ^= 1  # IHDR CRC; dimensions remain readable.
                    file.write_bytes(data)
                else:
                    file.unlink()
                    file = project / 'images' / 'final' / '01.jpg'
                    Image.new('RGB', (120, 160)).save(file)
                    data = file.read_bytes()
                    file.write_bytes(data[:data.index(b'\xff\xc0') + 9])
                result, _ = self.qa(project)
                self.assertNotEqual(result.returncode, 0, result.stdout)

    def test_final_verifier_rechecks_image_decode_even_with_matching_hash(self):
        with tempfile.TemporaryDirectory() as td:
            project = self.project(td)
            result, report = self.qa(project)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            file = project / 'images' / 'final' / '01.png'
            file.write_bytes(self.header_only_png())
            data = json.loads(report.read_text(encoding='utf-8'))
            data['pages'][0]['sha256'] = hashlib.sha256(file.read_bytes()).hexdigest()
            data['pages'][0]['size_bytes'] = file.stat().st_size
            report.write_text(json.dumps(data), encoding='utf-8')
            result = self.run_cmd(SCRIPTS / 'verify_final_qa.py', project, '--report', report)
            self.assertNotEqual(result.returncode, 0, result.stdout)

    def test_strict_qa_requires_exact_positive_integer_page_count(self):
        qa_images = load_script('qa_images')
        for count in (None, 0, -1, True, 1.5, '1'):
            with self.subTest(count=count), tempfile.TemporaryDirectory() as td:
                project = self.project(td, count=count)
                result, _ = self.qa(project)
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertIn('page_count', result.stdout)
                data = qa_images.inspect(project)
                self.assertTrue(any('page_count' in error for error in data['errors']))

    def test_draft_may_keep_page_count_unresolved(self):
        qa_images = load_script('qa_images')
        with tempfile.TemporaryDirectory() as td:
            project = self.project(td, count=None, status='not_started')
            data = qa_images.inspect(project)
            self.assertEqual(data['errors'], [])
            self.assertTrue(any('page_count' in warning for warning in data['warnings']))

    def test_strict_qa_fails_explicitly_without_pillow(self):
        qa_images = load_script('qa_images')
        preflight = load_script('preflight')
        with tempfile.TemporaryDirectory() as td:
            project = self.project(td)
            with mock.patch.dict(sys.modules, {'PIL': None, 'PIL.Image': None}):
                data = qa_images.inspect(project, strict=True)
                capabilities = preflight.check()
            self.assertEqual(data['automated_status'], 'failed')
            self.assertTrue(any('Pillow' in error for error in data['errors']))
            self.assertFalse(capabilities['full_image_decode_available'])
            self.assertFalse(capabilities['strict_image_qa_ready'])

    def test_non_strict_qa_labels_header_only_check_without_pillow(self):
        qa_images = load_script('qa_images')
        with tempfile.TemporaryDirectory() as td:
            project = self.project(td, status='not_started')
            with mock.patch.dict(sys.modules, {'PIL': None, 'PIL.Image': None}):
                data = qa_images.inspect(project)
            self.assertEqual(data['errors'], [])
            self.assertEqual(data.get('image_integrity_check'), 'header_only')
            self.assertTrue(any('Pillow' in warning for warning in data['warnings']))

    def source_with_nested_references(self, parent):
        source = Path(parent) / 'source'
        shutil.copytree(ROOT, source, ignore=shutil.ignore_patterns('.git', '__pycache__', '*.pyc'))
        style = source / 'styles' / 'minimal-editorial'
        references = ['examples/nested/private-reference.png', 'examples/nested/vector.SVG',
                      'assets/brand.JPG', 'assets/reference.WEBP']
        for ref in references:
            file = style / ref
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_bytes(b'private reference fixture')
        info = json.loads((style / 'style.json').read_text(encoding='utf-8'))
        info['references'] = references + ['style.md']
        (style / 'style.json').write_text(json.dumps(info), encoding='utf-8')
        return source, references

    def test_public_package_excludes_nested_and_non_example_style_images(self):
        with tempfile.TemporaryDirectory() as td:
            source, references = self.source_with_nested_references(td)
            destination = Path(td) / 'public.zip'
            result = self.run_cmd(SCRIPTS / 'package_skill.py', '--root', source, '--output', destination)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            with zipfile.ZipFile(destination) as archive:
                for ref in references:
                    self.assertNotIn('visual-post-studio/styles/minimal-editorial/' + ref, archive.namelist())
                data = json.loads(archive.read('visual-post-studio/styles/minimal-editorial/style.json'))
                self.assertEqual(data['references'], ['style.md'])
                self.assertTrue(data['example_images_excluded'])

    def test_reference_image_package_keeps_nested_assets_and_metadata(self):
        with tempfile.TemporaryDirectory() as td:
            source, references = self.source_with_nested_references(td)
            destination = Path(td) / 'with-images.zip'
            result = self.run_cmd(SCRIPTS / 'package_skill.py', '--root', source, '--output', destination, '--include-example-images')
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            with zipfile.ZipFile(destination) as archive:
                for ref in references:
                    self.assertIn('visual-post-studio/styles/minimal-editorial/' + ref, archive.namelist())
                data = json.loads(archive.read('visual-post-studio/styles/minimal-editorial/style.json'))
                self.assertEqual(data['references'], references + ['style.md'])
                self.assertNotIn('example_images_excluded', data)

    def test_runtime_packages_include_image_qa_dependency_file(self):
        with tempfile.TemporaryDirectory() as td:
            for with_images in (False, True):
                with self.subTest(with_images=with_images):
                    destination = Path(td) / ('images.zip' if with_images else 'public.zip')
                    args = ['--include-example-images'] if with_images else []
                    result = self.run_cmd(SCRIPTS / 'package_skill.py', '--root', ROOT, '--output', destination, *args)
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    with zipfile.ZipFile(destination) as archive:
                        dependency = 'visual-post-studio/requirements-image-qa.txt'
                        self.assertIn(dependency, archive.namelist())
                        self.assertIn('Pillow', archive.read(dependency).decode('utf-8'))

    def test_invalid_pixels_leave_no_project_and_corrected_retry_succeeds(self):
        with tempfile.TemporaryDirectory() as td:
            args = [SCRIPTS / 'new_project.py', '--slug', 'retry', '--out', td]
            bad = self.run_cmd(*args, '--pixels', 'invalid')
            self.assertNotEqual(bad.returncode, 0)
            self.assertFalse((Path(td) / 'retry').exists())
            self.assertNotIn('Traceback', bad.stderr)
            good = self.run_cmd(*args, '--pixels', '120x160')
            self.assertEqual(good.returncode, 0, good.stdout + good.stderr)
            manifest = json.loads((Path(td) / 'retry' / 'manifest.json').read_text(encoding='utf-8'))
            self.assertEqual(manifest['target_pixels'], [120, 160])

    def test_invalid_second_reference_leaves_no_style_and_retry_succeeds(self):
        with tempfile.TemporaryDirectory() as td:
            first, second = Path(td) / 'first.png', Path(td) / 'second.png'
            write_png(first, 120, 160)
            parent = Path(td) / 'styles'
            args = [SCRIPTS / 'new_style_pack.py', '--id', 'retry', '--out', parent,
                    '--reference', first, '--reference', second]
            bad = self.run_cmd(*args)
            self.assertNotEqual(bad.returncode, 0)
            self.assertFalse((parent / 'retry').exists())
            self.assertNotIn('Traceback', bad.stderr)
            write_png(second, 120, 160)
            good = self.run_cmd(*args)
            self.assertEqual(good.returncode, 0, good.stdout + good.stderr)
            manifest = json.loads((parent / 'retry' / 'style.json').read_text(encoding='utf-8'))
            self.assertEqual(len(manifest['references']), 2)


if __name__ == '__main__':
    unittest.main()
