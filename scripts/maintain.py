#!/usr/bin/env python3
"""Validate, save and deploy committed skill revisions; development use only."""
import argparse
from contextlib import contextmanager
from datetime import date
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from urllib.parse import unquote, urlsplit
import zipfile

from package_skill import package
from validate_skill import check

NAME = 'visual-post-studio'
ROOT = Path(__file__).resolve().parents[1]
RECEIPT = '.installation.json'
REGISTRY = '.local/installations.json'


def git(root, *args, env=None):
    result = subprocess.run(['git', '-C', str(root), *args], env=env,
                            capture_output=True)
    if result.returncode:
        detail = result.stderr.decode('utf-8', errors='replace').strip()
        raise ValueError('Git failed: ' + detail)
    return result.stdout


def named_files(root, paths):
    """Accept explicit files, including tracked deletions; reject directories/globs."""
    result = []
    for raw in paths:
        if any(c in raw for c in '*?[]'):
            raise ValueError('List explicit files, without glob patterns: ' + raw)
        target = (root / raw).resolve()
        try:
            relative = target.relative_to(root).as_posix()
        except ValueError:
            raise ValueError('File is outside the source repository: ' + raw)
        if relative == '.' or target.is_dir() or relative.startswith(('.git/', '.local/')):
            raise ValueError('Not a source file: ' + raw)
        tracked = git(root, 'ls-files', '--', relative)
        if not target.is_file() and not tracked:
            raise ValueError('Missing, untracked file: ' + raw)
        if relative not in result:
            result.append(relative)
    if not result:
        raise ValueError('Name the files belonging to this change.')
    return result


@contextmanager
def snapshot(root, paths=None, revision='HEAD'):
    """Use a temporary index; the user's real index is never part of the candidate."""
    with tempfile.TemporaryDirectory(prefix='visual-post-snapshot-') as td:
        work = Path(td)
        if paths is not None:
            env = dict(os.environ, GIT_INDEX_FILE=str(work / 'index'))
            git(root, 'read-tree', revision, env=env)
            git(root, 'add', '--all', '--', *paths, env=env)
            revision = git(root, 'write-tree', env=env).decode().strip()
        data = git(root, '-c', 'core.autocrlf=false', 'archive', '--format=zip', revision)
        target = work / NAME
        target.mkdir()
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            archive.extractall(target)
        yield target


def metadata(root):
    try:
        import yaml
    except ImportError:
        raise ValueError('Install development dependencies: python -m pip install -r requirements-dev.txt')
    body = (root / 'SKILL.md').read_text(encoding='utf-8')
    match = re.match(r'\A---\n(.*?)\n---\n', body, re.S)
    if not match:
        raise ValueError('SKILL.md requires YAML frontmatter.')
    try:
        data = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        raise ValueError('Invalid YAML frontmatter: ' + str(exc))
    if not isinstance(data, dict):
        raise ValueError('SKILL.md frontmatter must be a mapping.')
    allowed = {'name', 'description', 'license', 'allowed-tools', 'metadata'}
    if set(data) - allowed:
        raise ValueError('Unsupported frontmatter keys: ' + ', '.join(sorted(set(data) - allowed)))
    if data.get('name') != NAME:
        raise ValueError('Skill name must be ' + NAME)
    description = data.get('description')
    if not isinstance(description, str) or not 1 <= len(description) <= 1024 or re.search(r'[<>]', description):
        raise ValueError('description must be 1–1024 characters without angle brackets.')
    info = data.get('metadata')
    if not isinstance(info, dict) or not re.fullmatch(r'\d+\.\d+\.\d+', str(info.get('version', ''))):
        raise ValueError('metadata.version must have the form X.Y.Z.')
    return data


def link_errors(root):
    """Check written Markdown links; skip fenced examples and inline code."""
    errors = []
    for file in sorted(root.rglob('*.md')):
        relative = file.relative_to(root)
        if any(part in {'.git', '.local', '__pycache__', 'projects', 'outputs', 'personal'} for part in relative.parts):
            continue
        fence = None
        for number, line in enumerate(file.read_text(encoding='utf-8').splitlines(), 1):
            marker = re.match(r'^\s*(`{3,}|~{3,})', line)
            if marker:
                token = marker.group(1)[0]
                fence = None if fence == token else token
                continue
            if fence:
                continue
            line = re.sub(r'(`+).*?\1', '', line)
            targets = re.findall(r'\]\(\s*(<[^>]+>|[^\s)]+)', line)
            reference = re.match(r'^\s*\[[^]]+\]:\s*(<[^>]+>|\S+)', line)
            if reference:
                targets.append(reference.group(1))
            for target in targets:
                target = target.strip('<>')
                url = urlsplit(target)
                if url.scheme or url.netloc or not url.path:
                    continue
                path = (file.parent / unquote(url.path)).resolve()
                if not path.exists():
                    errors.append(f'{relative.as_posix()}:{number}: Missing local link: {target}')
    return errors


def validate(root):
    metadata(root)
    errors = check(root) + link_errors(root)
    ui = root / 'agents/openai.yaml'
    if ui.is_file():
        import yaml
        try:
            data = yaml.safe_load(ui.read_text(encoding='utf-8'))
            interface = data['interface']
            if not 25 <= len(interface['short_description']) <= 64:
                errors.append('agents/openai.yaml: short_description must be 25–64 characters.')
            if '$' + NAME not in interface['default_prompt']:
                errors.append('agents/openai.yaml: default_prompt must mention $' + NAME)
        except (KeyError, TypeError, yaml.YAMLError) as exc:
            errors.append('agents/openai.yaml: Invalid interface metadata: ' + str(exc))
    if errors:
        raise ValueError('Skill validation failed:\n' + '\n'.join(errors))


def run_tests(root):
    result = subprocess.run([sys.executable, '-B', '-X', 'utf8', '-m', 'unittest',
                             'discover', '-s', 'tests', '-v'], cwd=root,
                            capture_output=True, text=True, encoding='utf-8',
                            env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
    output = result.stdout + result.stderr
    print(output, end='', flush=True)
    if result.returncode or not re.search(r'Ran [1-9]\d* tests?', output):
        raise ValueError('Regression tests failed or no tests were discovered.')
    return output


def hashes(root):
    result = {}
    for file in sorted(root.rglob('*')):
        if file.is_symlink():
            raise ValueError('Symlinks are not supported in installed payloads: ' + str(file))
        if not file.is_file():
            continue
        relative = file.relative_to(root)
        if relative.as_posix() == RECEIPT or '__pycache__' in relative.parts or file.suffix == '.pyc':
            continue
        result[relative.as_posix()] = hashlib.sha256(file.read_bytes()).hexdigest()
    return result


def receipt(root, destination, check_files=True):
    file = destination / RECEIPT
    if not file.is_file():
        raise ValueError('Existing skill has no installation receipt; use --adopt only for an identical committed runtime.')
    data = json.loads(file.read_text(encoding='utf-8'))
    if data.get('schema_version') != 1 or Path(data.get('source_repository', '')).resolve() != root:
        raise ValueError('Installed skill belongs to another source repository: ' + str(destination))
    if check_files and hashes(destination) != data.get('files'):
        raise ValueError('Installed files were changed, added or deleted; preserve those edits in the source before syncing: ' + str(destination))
    return data


def destinations(root):
    paths = []
    registry = root / REGISTRY
    if registry.is_file():
        paths.extend(Path(path) for path in json.loads(registry.read_text(encoding='utf-8'))['destinations'])
    for base in ('.agents', '.codex', '.zcode'):
        destination = Path.home() / base / 'skills' / NAME
        file = destination / RECEIPT
        if file.is_file():
            info = json.loads(file.read_text(encoding='utf-8'))
            if Path(info.get('source_repository', '')).resolve() == root:
                paths.append(destination)
    return sorted({path.resolve() for path in paths}, key=str)


def register(root, destination):
    paths = destinations(root)
    if destination not in paths:
        paths.append(destination)
    file = root / REGISTRY
    file.parent.mkdir(exist_ok=True)
    file.write_text(json.dumps({'destinations': [str(path) for path in paths]},
                               ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def deploy(root, destination, adopt=False, preserve_local_changes=False):
    root = root.resolve()
    absolute = Path(os.path.abspath(destination))
    if absolute.is_symlink() or absolute.resolve() != absolute:
        raise ValueError('Use a real destination directory, without symlinks: ' + str(absolute))
    destination = absolute.resolve()
    if destination.name != NAME or destination == root or root in destination.parents or destination in root.parents:
        raise ValueError('Destination must be an external directory named ' + NAME)
    destination.parent.mkdir(parents=True, exist_ok=True)
    # All staging and backup removal is confined to this freshly created directory.
    work = Path(tempfile.mkdtemp(prefix='.' + NAME + '-deploy-', dir=destination.parent)).resolve()
    if work.parent != destination.parent or not work.name.startswith('.' + NAME + '-deploy-'):
        raise ValueError('Unsafe deployment work directory.')
    keep_work = False
    try:
        commit = git(root, 'rev-parse', 'HEAD').decode().strip()
        with snapshot(root, revision=commit) as source:
            validate(source)
            output = package(source, work / 'runtime.zip')
            with zipfile.ZipFile(output) as archive:
                archive.extractall(work / 'payload')
            staged = work / 'payload' / NAME
            validate(staged)
            expected = hashes(staged)
            if destination.exists():
                if (destination / RECEIPT).exists():
                    info = receipt(root, destination, check_files=not preserve_local_changes)
                    if preserve_local_changes and hashes(destination) != info.get('files'):
                        backups = root / '.local/installation-backups'
                        backups.mkdir(parents=True, exist_ok=True)
                        saved = Path(tempfile.mkdtemp(prefix='preserved-', dir=backups)) / NAME
                        shutil.copytree(destination, saved)
                        if hashes(saved) != hashes(destination):
                            raise ValueError('Installed files changed while backing up; no replacement performed. Backup: ' + str(saved))
                        print('LOCAL EDITS BACKUP:', saved, flush=True)
                elif not adopt or hashes(destination) != expected:
                    raise ValueError('Refusing to replace an unmanaged or different installed skill: ' + str(destination))
            data = {'schema_version': 1, 'skill': NAME, 'source_repository': str(root),
                    'commit': commit, 'version': metadata(source)['metadata']['version'],
                    'profile': 'public-runtime', 'files': expected}
            (staged / RECEIPT).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            backup = work / 'previous'
            had_previous = destination.exists()
            if had_previous:
                os.replace(destination, backup)
            try:
                os.replace(staged, destination)
            except BaseException:
                if had_previous:
                    try:
                        os.replace(backup, destination)
                    except BaseException as exc:
                        keep_work = True
                        raise ValueError('Replacement and rollback failed; the previous installation is preserved at '
                                         + str(backup) + ': ' + str(exc))
                raise
            register(root, destination)
            print(f'INSTALLED: {destination}\nVERSION: {data["version"]}\nCOMMIT: {commit}', flush=True)
    finally:
        if not keep_work:
            shutil.rmtree(work)


def sync(root):
    targets = destinations(root)
    # Inspect all copies first so a conflict is reported before any copy is changed.
    for destination in targets:
        receipt(root, destination)
    for destination in targets:
        deploy(root, destination)
    if not targets:
        print('No managed installation exists; use the install command first.')


def message_check(message):
    if '\n' in message or not re.fullmatch(r'[a-z][a-z0-9-]*: .{5,} — .{5,}', message.strip()):
        raise ValueError('Use a specific commit message: <area>: <what changed> — <why>')


def append_note(root, note):
    if not note or '\n' in note or '\r' in note:
        raise ValueError('--note requires one non-empty line.')
    file = root / 'CHANGELOG.md'
    text = file.read_text(encoding='utf-8')
    if re.search(r'^## Unreleased\s*$', text, re.M):
        text = re.sub(r'(^## Unreleased\s*\n)', lambda m: m.group(1) + '\n- ' + note + '\n', text, count=1, flags=re.M)
    else:
        text = text.replace('# Changelog\n', '# Changelog\n\n## Unreleased\n\n- ' + note + '\n', 1)
    file.write_text(text, encoding='utf-8')


def save(root, message, paths, note=None):
    message_check(message)
    paths = named_files(root, paths)
    if note:
        if git(root, 'status', '--porcelain', '--', 'CHANGELOG.md'):
            raise ValueError('CHANGELOG.md already has changes; save them explicitly without --note.')
        if 'CHANGELOG.md' not in paths:
            paths.append('CHANGELOG.md')
    if git(root, 'diff', '--cached', '--name-only', '--', *paths):
        raise ValueError('A named file already has staged changes; keep or commit that work explicitly before saving.')
    if not git(root, 'status', '--porcelain', '--', *paths) and not note:
        print('No change in the named files; checking installation sync.')
        sync(root)
        return
    before = git(root, 'rev-parse', 'HEAD').decode().strip()
    def file_state():
        return {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
                if (root / name).is_file() else None for name in paths}
    original_files = file_state()
    print('Checking HEAD plus named files; the real index is preserved.', flush=True)
    with snapshot(root, paths, revision=before) as candidate:
        if note:
            append_note(candidate, note)
        validate(candidate)
        run_tests(candidate)
    if git(root, 'rev-parse', 'HEAD').decode().strip() != before or file_state() != original_files:
        raise ValueError('Source changed during validation; preserve the new work and rerun save.')
    if git(root, 'diff', '--cached', '--name-only', '--', *paths):
        raise ValueError('A named file was staged during validation; preserve that work and rerun save.')
    for destination in destinations(root):
        receipt(root, destination)
    original = (root / 'CHANGELOG.md').read_bytes() if note else None
    try:
        if note:
            append_note(root, note)
        git(root, 'config', 'core.hooksPath', '.githooks')
        git(root, 'add', '--all', '--', *paths)
        output = git(root, 'commit', '--only', '-m', message, '--', *paths)
        print(output.decode('utf-8', errors='replace'), end='', flush=True)
    except Exception:
        # Named files had no staged edits at entry; restore only our index changes.
        if git(root, 'rev-parse', 'HEAD').decode().strip() == before:
            git(root, 'restore', '--staged', '--source', before, '--', *paths)
            if original is not None:
                (root / 'CHANGELOG.md').write_bytes(original)
        raise
    try:
        sync(root)
    except (ValueError, OSError) as exc:
        raise ValueError('Commit succeeded, but installation sync failed. Fix the reported issue and run sync again. ' + str(exc))


def status(root):
    print('SOURCE:', root)
    print('COMMIT:', git(root, 'rev-parse', 'HEAD').decode().strip())
    print(git(root, 'status', '--short').decode('utf-8', errors='replace') or 'Source working tree is clean.')
    current = git(root, 'rev-parse', 'HEAD').decode().strip()
    for destination in destinations(root):
        info = receipt(root, destination)
        print(f'INSTALLATION: {destination}\nVERSION: {info["version"]}\nIN_SYNC: {info["commit"] == current}')


def release(root, out):
    out = out.resolve()
    if out == root or root in out.parents:
        raise ValueError('Keep releases outside the source repository.')
    out.mkdir(parents=True, exist_ok=True)
    commit = git(root, 'rev-parse', 'HEAD').decode().strip()
    with snapshot(root, revision=commit) as source:
        validate(source)
        version = metadata(source)['metadata']['version']
        changelog = (source / 'CHANGELOG.md').read_text(encoding='utf-8')
        if not re.search(r'^## ' + re.escape(version) + r'\s*\(', changelog, re.M):
            raise ValueError('Record the release version and date in CHANGELOG.md first.')
        base = out / f'{NAME}_v{version}'
        public = Path(str(base) + '_public.zip')
        development = Path(str(base) + '_development-source.zip')
        report = Path(str(base) + '_validation.json')
        if any(path.exists() for path in (public, development, report)):
            raise ValueError('Release files already exist; keep versions immutable or choose another output directory.')
        evidence = run_tests(source)
        # Build everything in a temporary directory before publishing the artifacts.
        with tempfile.TemporaryDirectory(prefix='visual-post-release-', dir=out) as td:
            stage = Path(td)
            # Tests can create caches or modify their temporary checkout. Build
            # from a fresh pinned snapshot, and take the dev archive from Git.
            with snapshot(root, revision=commit) as release_source:
                package(release_source, stage / public.name)
            with zipfile.ZipFile(stage / public.name) as archive:
                archive.extractall(stage / 'check')
            validate(stage / 'check' / NAME)
            (stage / development.name).write_bytes(git(root, '-c', 'core.autocrlf=false', 'archive',
                                                       '--format=zip', '--prefix=' + NAME + '/', commit))
            archives = [public, development]
            details = {'schema_version': 1, 'version': version, 'commit': commit,
                       'date': date.today().isoformat(), 'tests': evidence,
                       'real_image_generation': 'not evaluated by this release command',
                       'artifacts': {path.name: hashlib.sha256((stage / path.name).read_bytes()).hexdigest() for path in archives}}
            (stage / report.name).write_text(json.dumps(details, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            for path in (*archives, report):
                shutil.copy2(stage / path.name, path)
                print('RELEASED:', path)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default=str(ROOT))
    commands = parser.add_subparsers(dest='command', required=True)
    command = commands.add_parser('validate')
    command.add_argument('--candidate', nargs='+')
    command = commands.add_parser('install')
    command.add_argument('--dest', default=str(Path.home() / '.agents/skills' / NAME))
    command.add_argument('--adopt', action='store_true', help='Adopt only an identical unmanaged committed runtime.')
    command.add_argument('--preserve-local-changes', action='store_true',
                         help='Back up modified files of a managed installation to .local before reinstalling HEAD.')
    commands.add_parser('sync')
    commands.add_parser('status')
    command = commands.add_parser('save')
    command.add_argument('message')
    command.add_argument('--note')
    command.add_argument('files', nargs='+')
    command = commands.add_parser('release')
    command.add_argument('--out', required=True)
    command = commands.add_parser('check-message')
    command.add_argument('--file', required=True)
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    try:
        if args.command == 'validate':
            if args.candidate:
                with snapshot(root, named_files(root, args.candidate)) as candidate:
                    validate(candidate)
            else:
                validate(root)
            print('PASS: YAML, bundle resources, UI metadata and Markdown links; visual quality is not evaluated.')
        elif args.command == 'install':
            deploy(root, Path(args.dest), args.adopt, args.preserve_local_changes)
        elif args.command == 'sync':
            sync(root)
        elif args.command == 'status':
            status(root)
        elif args.command == 'save':
            save(root, args.message, args.files, args.note)
        elif args.command == 'release':
            release(root, Path(args.out))
        else:
            lines = Path(args.file).read_text(encoding='utf-8').splitlines()
            message_check(next((line for line in lines if line.strip() and not line.startswith('#')), ''))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print('ERROR:', exc, file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
