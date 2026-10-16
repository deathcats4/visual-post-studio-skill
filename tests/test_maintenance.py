"""Regression checks for real candidate, Git, installation and release boundaries."""
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import zipfile

SOURCE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SOURCE / 'scripts'))
import maintain

MESSAGE = 'workflow: save only this change — preserve unrelated developer work'


class MaintenanceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='visual-post-maintenance-test-')
        self.addCleanup(self.temporary.cleanup)
        self.work = Path(self.temporary.name)
        self.root = self.work / maintain.NAME
        shutil.copytree(SOURCE, self.root, ignore=shutil.ignore_patterns(
            '.git', '.local', 'tests', '__pycache__', '*.pyc', 'personal', 'projects', 'outputs'))
        # The isolated repository has a small suite to exercise save orchestration
        # without recursively running this test class or touching real installations.
        self.write('tests/test_fixture.py', 'import unittest\nclass Fixture(unittest.TestCase):\n'
                   '    def test_suite_runs(self):\n        self.assertTrue(True)\n')
        for name in ('test_regressions.py', 'test_maintenance.py'):
            self.write('tests/' + name, '"""Link target in the isolated test repository."""\n')
        self.write('unrelated.md', 'Original unrelated work.\n')
        self.git('init', '--quiet')
        self.git('config', 'user.name', 'Visual Post Studio test')
        self.git('config', 'user.email', 'skill-test@example.invalid')
        self.git('config', 'commit.gpgsign', 'false')
        self.git('config', 'core.autocrlf', 'false')
        self.git('add', '.')
        self.git('commit', '--quiet', '-m', 'meta: establish a temporary test source — isolate maintenance checks')
        self.destination = self.work / 'installed/skills' / maintain.NAME

    def write(self, name, value):
        file = self.root / name
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(value, encoding='utf-8')

    def append(self, name, text):
        file = self.root / name
        file.write_text(file.read_text(encoding='utf-8') + text, encoding='utf-8')

    def git(self, *args):
        return maintain.git(self.root, *args)

    def head(self):
        return self.git('rev-parse', 'HEAD')

    def cli(self, *args):
        return subprocess.run([sys.executable, '-B', '-X', 'utf8', 'scripts/maintain.py', *args],
                              cwd=self.root, capture_output=True, text=True, encoding='utf-8')

    def assert_success(self, result):
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def commit_readme(self):
        self.append('README.md', '\nA committed maintenance test change.\n')
        self.git('add', 'README.md')
        self.git('commit', '--quiet', '-m', MESSAGE)

    def test_candidate_ignores_unnamed_new_and_staged_files(self):
        self.append('SKILL.md', '\n[required](references/new-case.md)\n')
        self.write('references/new-case.md', 'New reference not selected for this save.\n')
        self.git('add', 'references/new-case.md')
        self.append('unrelated.md', 'Unrelated staged change.\n')
        self.git('add', 'unrelated.md')
        index = self.git('ls-files', '--stage')
        maintain.validate(self.root)
        with maintain.snapshot(self.root, ['SKILL.md']) as candidate:
            with self.assertRaisesRegex(ValueError, 'Missing local link'):
                maintain.validate(candidate)
        with maintain.snapshot(self.root, ['SKILL.md', 'references/new-case.md']) as candidate:
            maintain.validate(candidate)
        self.assertEqual(index, self.git('ls-files', '--stage'))

    def test_candidate_rejects_deleted_link_target(self):
        self.write('references/guard.md', 'A required local reference.\n')
        self.append('README.md', '\n[required](references/guard.md)\n')
        self.git('add', 'README.md', 'references/guard.md')
        self.git('commit', '--quiet', '-m', MESSAGE)
        (self.root / 'references/guard.md').unlink()
        with maintain.snapshot(self.root, ['references/guard.md']) as candidate:
            with self.assertRaisesRegex(ValueError, 'Missing local link'):
                maintain.validate(candidate)
        self.assertEqual(b'', self.git('diff', '--cached'))

    def test_parsed_yaml_rejects_invalid_metadata(self):
        content = (self.root / 'SKILL.md').read_text(encoding='utf-8')
        for header in ('name: [unfinished', 'description: 42', 'metadata: invalid'):
            with self.subTest(header=header):
                self.write('SKILL.md', '---\n' + header + '\n---\n' + content.split('---', 2)[2])
                with self.assertRaises(ValueError):
                    maintain.validate(self.root)

    def test_named_files_reject_directories_globs_and_outside_paths(self):
        for name in ('.', 'references', '*.md', '../outside.md', '.git/config'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                maintain.named_files(self.root, [name])

    def test_save_preserves_other_staged_and_untracked_work(self):
        self.append('unrelated.md', 'Other staged content.\n')
        self.git('add', 'unrelated.md')
        staged = self.git('diff', '--cached', '--', 'unrelated.md')
        self.write('private-draft.md', 'Untracked draft must survive.\n')
        self.append('README.md', '\nA selected README change.\n')
        result = self.cli('save', MESSAGE, '--note', 'Record only the selected change.', 'README.md')
        self.assert_success(result)
        committed = self.git('diff-tree', '--no-commit-id', '--name-only', '-r', 'HEAD').decode().splitlines()
        self.assertEqual(set(committed), {'README.md', 'CHANGELOG.md'})
        self.assertEqual(staged, self.git('diff', '--cached', '--', 'unrelated.md'))
        self.assertTrue((self.root / 'private-draft.md').is_file())
        self.assertEqual(b'', self.git('ls-files', '--', 'private-draft.md'))
        self.assertIn('## Unreleased', (self.root / 'CHANGELOG.md').read_text(encoding='utf-8'))

    def test_validation_failure_does_not_mutate_index_note_or_head(self):
        self.append('README.md', '\n[missing](references/missing.md)\n')
        self.append('unrelated.md', 'Other staged content.\n')
        self.git('add', 'unrelated.md')
        before = (self.head(), self.git('ls-files', '--stage'), (self.root / 'CHANGELOG.md').read_bytes())
        result = self.cli('save', MESSAGE, '--note', 'This note must not be saved.', 'README.md')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Skill validation failed', result.stderr)
        self.assertEqual(before, (self.head(), self.git('ls-files', '--stage'), (self.root / 'CHANGELOG.md').read_bytes()))
        self.assertIn('references/missing.md', (self.root / 'README.md').read_text(encoding='utf-8'))

    def test_commit_rejection_restores_only_owned_index_and_note(self):
        self.append('README.md', '\nSelected work must survive hook rejection.\n')
        self.write('new-source.md', 'New selected file must survive hook rejection.\n')
        self.append('unrelated.md', 'Other staged work must survive.\n')
        self.git('add', 'unrelated.md')
        self.write('.githooks/commit-msg', '#!/bin/sh\nexit 1\n')
        (self.root / '.githooks/commit-msg').chmod(0o755)
        before = (self.head(), self.git('ls-files', '--stage'), (self.root / 'CHANGELOG.md').read_bytes())
        result = self.cli('save', MESSAGE, '--note', 'This note must be rolled back.', 'README.md', 'new-source.md')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(before, (self.head(), self.git('ls-files', '--stage'), (self.root / 'CHANGELOG.md').read_bytes()))
        self.assertIn('Selected work must survive', (self.root / 'README.md').read_text(encoding='utf-8'))
        self.assertTrue((self.root / 'new-source.md').is_file())

    def test_working_file_change_during_validation_stops_save(self):
        self.append('README.md', '\nOriginal selected change.\n')
        before = (self.head(), self.git('ls-files', '--stage'))
        def new_work(candidate):
            self.append('README.md', '\nWork arriving during validation.\n')
        with mock.patch.object(maintain, 'run_tests', side_effect=new_work):
            with self.assertRaisesRegex(ValueError, 'Source changed during validation'):
                maintain.save(self.root, MESSAGE, ['README.md'])
        self.assertEqual(before, (self.head(), self.git('ls-files', '--stage')))
        self.assertIn('Work arriving during validation', (self.root / 'README.md').read_text(encoding='utf-8'))

    def test_head_change_during_validation_preserves_other_commit(self):
        self.append('README.md', '\nSelected change must stay uncommitted.\n')
        before = self.head()
        def new_commit(candidate):
            self.append('unrelated.md', 'A separate developer change.\n')
            self.git('add', 'unrelated.md')
            self.git('commit', '--quiet', '-m', MESSAGE)
        with mock.patch.object(maintain, 'run_tests', side_effect=new_commit):
            with self.assertRaisesRegex(ValueError, 'Source changed during validation'):
                maintain.save(self.root, MESSAGE, ['README.md'])
        self.assertNotEqual(before, self.head())
        self.assertEqual(b'', self.git('diff', '--cached'))
        self.assertIn('Selected change must stay uncommitted', (self.root / 'README.md').read_text(encoding='utf-8'))

    def test_existing_staged_selected_file_is_preserved(self):
        self.append('README.md', '\nAlready staged work.\n')
        self.git('add', 'README.md')
        before = (self.head(), self.git('ls-files', '--stage'))
        result = self.cli('save', MESSAGE, 'README.md')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('already has staged changes', result.stderr)
        self.assertEqual(before, (self.head(), self.git('ls-files', '--stage')))

    def test_failed_regression_blocks_save(self):
        self.write('tests/test_fixture.py', 'import unittest\nclass Fixture(unittest.TestCase):\n'
                   '    def test_failure(self):\n        self.fail("reproduced failure")\n')
        before = (self.head(), self.git('ls-files', '--stage'))
        result = self.cli('save', MESSAGE, 'tests/test_fixture.py')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Regression tests failed', result.stderr)
        self.assertEqual(before, (self.head(), self.git('ls-files', '--stage')))

    def test_commit_message_has_scope_change_and_reason(self):
        maintain.message_check(MESSAGE)
        for message in ('update', 'fix', 'workflow: update', 'workflow: short — why', MESSAGE + '\nextra'):
            with self.subTest(message=message), self.assertRaises(ValueError):
                maintain.message_check(message)

    def test_install_uses_head_and_excludes_development_content(self):
        committed = self.git('show', 'HEAD:README.md')
        self.append('README.md', '\nUncommitted content must stay out of installation.\n')
        self.write('scripts/untracked-secret.py', 'secret = "not runtime"\n')
        maintain.deploy(self.root, self.destination)
        self.assertEqual(committed, (self.destination / 'README.md').read_bytes())
        info = maintain.receipt(self.root, self.destination)
        self.assertEqual(self.head().decode().strip(), info['commit'])
        self.assertEqual(str(self.root), info['source_repository'])
        for name in ('AGENTS.md', 'DEVELOPMENT.md', 'development', 'tests', 'requirements-dev.txt',
                     'scripts/maintain.py', 'scripts/save.sh', 'scripts/untracked-secret.py', '.local'):
            self.assertFalse((self.destination / name).exists(), name)
        self.assertTrue((self.destination / 'agents/openai.yaml').is_file())
        self.assertFalse(list((self.destination / 'styles').rglob('*.png')))

    def test_changed_installation_is_never_overwritten(self):
        maintain.deploy(self.root, self.destination)
        file = self.destination / 'README.md'
        file.write_text('User changed this installed copy.\n', encoding='utf-8')
        self.commit_readme()
        with self.assertRaisesRegex(ValueError, 'Installed files were changed'):
            maintain.sync(self.root)
        self.assertEqual('User changed this installed copy.\n', file.read_text(encoding='utf-8'))

    def test_installation_conflict_blocks_commit_before_save(self):
        maintain.deploy(self.root, self.destination)
        (self.destination / 'README.md').write_text('Preserve installed edit.\n', encoding='utf-8')
        self.append('README.md', '\nSelected source change.\n')
        before = (self.head(), self.git('ls-files', '--stage'))
        result = self.cli('save', MESSAGE, 'README.md')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Installed files were changed', result.stderr)
        self.assertEqual(before, (self.head(), self.git('ls-files', '--stage')))

    def test_explicit_reinstall_preserves_local_edits_in_backup(self):
        maintain.deploy(self.root, self.destination)
        changed = self.destination / 'README.md'
        changed.write_text('Installed edits requiring preservation.\n', encoding='utf-8')
        maintain.deploy(self.root, self.destination, preserve_local_changes=True)
        backups = list((self.root / '.local/installation-backups').glob('preserved-*/visual-post-studio'))
        self.assertEqual(len(backups), 1)
        self.assertEqual('Installed edits requiring preservation.\n', (backups[0] / 'README.md').read_text(encoding='utf-8'))
        self.assertEqual(self.git('show', 'HEAD:README.md'), (self.destination / 'README.md').read_bytes())
        maintain.receipt(self.root, self.destination)
        self.assertEqual(b'', self.git('status', '--porcelain'))

    def test_sync_updates_registered_copy_to_new_commit(self):
        maintain.deploy(self.root, self.destination)
        old = maintain.receipt(self.root, self.destination)['commit']
        self.commit_readme()
        maintain.sync(self.root)
        info = maintain.receipt(self.root, self.destination)
        self.assertNotEqual(old, info['commit'])
        self.assertEqual(self.head().decode().strip(), info['commit'])
        self.assertEqual(self.git('show', 'HEAD:README.md'), (self.destination / 'README.md').read_bytes())

    def test_save_automatically_syncs_managed_installation(self):
        maintain.deploy(self.root, self.destination)
        self.append('README.md', '\nSelected source change to deploy.\n')
        result = self.cli('save', MESSAGE, 'README.md')
        self.assert_success(result)
        self.assertEqual(self.head().decode().strip(), maintain.receipt(self.root, self.destination)['commit'])
        self.assertEqual(self.git('show', 'HEAD:README.md'), (self.destination / 'README.md').read_bytes())

    def test_adoption_requires_identical_committed_payload(self):
        maintain.deploy(self.root, self.destination)
        (self.destination / maintain.RECEIPT).unlink()
        with self.assertRaisesRegex(ValueError, 'unmanaged'):
            maintain.deploy(self.root, self.destination)
        maintain.deploy(self.root, self.destination, adopt=True)
        (self.destination / maintain.RECEIPT).unlink()
        (self.destination / 'extra-private.txt').write_text('Must be preserved.', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'unmanaged'):
            maintain.deploy(self.root, self.destination, adopt=True)
        self.assertTrue((self.destination / 'extra-private.txt').is_file())

    def test_replacement_failure_restores_previous_installation(self):
        maintain.deploy(self.root, self.destination)
        before = maintain.hashes(self.destination)
        old_commit = maintain.receipt(self.root, self.destination)['commit']
        self.commit_readme()
        original_replace = os.replace
        def fail_payload(source, target):
            if Path(source).parent.name == 'payload':
                raise OSError('Simulated replacement failure')
            return original_replace(source, target)
        with mock.patch.object(maintain.os, 'replace', side_effect=fail_payload):
            with self.assertRaisesRegex(OSError, 'Simulated replacement'):
                maintain.deploy(self.root, self.destination)
        self.assertEqual(before, maintain.hashes(self.destination))
        self.assertEqual(old_commit, maintain.receipt(self.root, self.destination)['commit'])
        self.assertFalse(list(self.destination.parent.glob('.visual-post-studio-deploy-*')))

    def test_failed_rollback_preserves_backup_for_recovery(self):
        maintain.deploy(self.root, self.destination)
        before = maintain.hashes(self.destination)
        self.commit_readme()
        original_replace = os.replace
        def fail_replacement_and_rollback(source, target):
            if Path(source).parent.name == 'payload' or Path(source).name == 'previous':
                raise OSError('Simulated locked destination')
            return original_replace(source, target)
        with mock.patch.object(maintain.os, 'replace', side_effect=fail_replacement_and_rollback):
            with self.assertRaisesRegex(ValueError, 'previous installation is preserved'):
                maintain.deploy(self.root, self.destination)
        backups = list(self.destination.parent.glob('.visual-post-studio-deploy-*/previous'))
        self.assertEqual(len(backups), 1)
        self.assertEqual(before, maintain.hashes(backups[0]))

    def test_public_package_has_only_production_scripts(self):
        output = self.work / 'public.zip'
        maintain.package(self.root, output)
        with zipfile.ZipFile(output) as archive:
            names = set(archive.namelist())
            for path in ('scripts/maintain.py', 'scripts/save.sh', 'AGENTS.md', 'DEVELOPMENT.md', 'requirements-dev.txt'):
                self.assertNotIn(maintain.NAME + '/' + path, names)
            self.assertIn(maintain.NAME + '/agents/openai.yaml', names)

    def test_release_uses_committed_source_and_preserves_old_artifacts(self):
        # Simulate test side effects inside the temporary checkout: generated
        # files and edited documentation must never enter either release ZIP.
        self.write('tests/test_fixture.py', 'import unittest\nfrom pathlib import Path\n'
                   'class Fixture(unittest.TestCase):\n    def test_suite_runs(self):\n'
                   '        cache = Path("scripts/__pycache__/generated.pyc")\n'
                   '        cache.parent.mkdir(exist_ok=True)\n'
                   '        cache.write_bytes(b"generated cache")\n'
                   '        Path("generated.tmp").write_text("generated data")\n'
                   '        Path("README.md").write_text("Temporary test-only README")\n'
                   '        self.assertTrue(cache.exists())\n')
        self.git('add', 'tests/test_fixture.py')
        self.git('commit', '--quiet', '-m', MESSAGE)
        committed = self.git('show', 'HEAD:README.md')
        self.append('README.md', '\nUncommitted source must not enter release.\n')
        out = self.work / 'releases'
        maintain.release(self.root, out)
        artifacts = {file.name: file.read_bytes() for file in out.iterdir()}
        public = next(out.glob('*_public.zip'))
        development = next(out.glob('*_development-source.zip'))
        with zipfile.ZipFile(public) as archive:
            self.assertEqual(committed, archive.read(maintain.NAME + '/README.md'))
            self.assertNotIn(maintain.NAME + '/scripts/maintain.py', archive.namelist())
        with zipfile.ZipFile(development) as archive:
            self.assertEqual(committed, archive.read(maintain.NAME + '/README.md'))
            self.assertIn(maintain.NAME + '/scripts/maintain.py', archive.namelist())
            self.assertFalse(any('/.local/' in name or name.endswith(maintain.RECEIPT) for name in archive.namelist()))
            actual = {item.filename: archive.read(item) for item in archive.infolist() if not item.is_dir()}
        committed_archive = self.git('-c', 'core.autocrlf=false', 'archive', '--format=zip', '--prefix=' + maintain.NAME + '/', 'HEAD')
        with zipfile.ZipFile(io.BytesIO(committed_archive)) as archive:
            expected = {item.filename: archive.read(item) for item in archive.infolist() if not item.is_dir()}
        self.assertEqual(expected, actual)
        report = json.loads(next(out.glob('*_validation.json')).read_text(encoding='utf-8'))
        self.assertEqual(self.head().decode().strip(), report['commit'])
        self.assertIn('not evaluated', report['real_image_generation'])
        with self.assertRaisesRegex(ValueError, 'already exist'):
            maintain.release(self.root, out)
        self.assertEqual(artifacts, {file.name: file.read_bytes() for file in out.iterdir()})


if __name__ == '__main__':
    unittest.main()
