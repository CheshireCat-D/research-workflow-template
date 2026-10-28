#!/usr/bin/env python3
"""Curated source inventory and deterministic local release archives; no network."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import stat
import sys
from types import MappingProxyType
import uuid
import zipfile

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from core import __version__

DIRECTORIES = ('core', 'tools', 'skills', 'profiles', 'design', 'docs',
               'examples', 'evals', 'tests', 'provenance', '.github')
TOP_FILES = ('README.md', 'README.en.md', 'LICENSE', 'CONTRIBUTING.md',
             'SECURITY.md', 'CITATION.cff', '.gitignore', '中文介绍与使用说明.md',
             'USER_GUIDE.en.md', '.gitattributes')
REQUIRED = ('README.md', 'README.en.md', '中文介绍与使用说明.md', 'USER_GUIDE.en.md',
            'LICENSE', 'CONTRIBUTING.md', 'SECURITY.md', 'CITATION.cff', '.gitattributes',
            '.github/workflows/check.yml', 'core/cli.py', 'core/bundle.py',
            'core/windows_storage.py',
            'tools/research.py', 'tools/connect_skills.py', 'tools/check_core.py',
            'provenance/ORIGIN.md')
INDEX = 'provenance/file-origins.json'
ARCHIVE_MANIFEST = 'RELEASE-MANIFEST.json'
ARCHIVE_ROOT = 'research-workflow-template'
SKIP_DIRS = {'__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache', '.git'}
PRIVATE_DIRS = {'.agents', '.research', 'private-data', 'local-config', '.venv', 'venv'}
MAX_FILE = 16 * 1024 * 1024
MAX_TOTAL = 64 * 1024 * 1024
# Only these reviewed original task images may bypass the UTF-8 source rule.
# New images or changed bytes require an explicit source review, not a glob.
BINARY_SOURCE_ASSETS = {
    'evals/disciplinary/cases/artwork-versions/original.png':
        '7f0361e7758b68be296f54ffba34a67920627fa15202f79d80a767fc3c0fe2a7',
    'evals/disciplinary/cases/artwork-versions/reproduction.png':
        '2fdfdaaed9b8f759bd6025b377f2e5fcda2c4debe6362a3acd8a182e554c3247',
}
PATH_PATTERN = re.compile(r'/(?:Users|home|private/tmp|private/var|var/folders|opt/homebrew|Library/Frameworks)/[^\s\"\x27<>]+')
TOKEN_PATTERN = re.compile(r'gh[pousr]_[A-Za-z0-9]{30,}|AKIA[0-9A-Z]{16}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----')


class ReleaseError(ValueError):
    pass


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)+'\n').encode('utf-8')


def safe_name(name):
    if (not isinstance(name, str) or not name or '\\' in name or ':' in name or
            '\x00' in name or name.startswith('/') or any(p in ('', '.', '..') for p in name.split('/'))):
        raise ReleaseError('Unsafe archive or inventory path')
    # Keep every published name portable to an ordinary Windows filesystem.
    # Device aliases and trailing dots/spaces are normalized by Win32 and can
    # otherwise escape the archive's apparent one-name/one-resource contract.
    reserved = {'CON', 'PRN', 'AUX', 'NUL', 'CLOCK$', 'CONIN$', 'CONOUT$'}
    reserved.update(prefix + suffix for prefix in ('COM', 'LPT')
                    for suffix in '123456789¹²³')
    for part in name.split('/'):
        if (part.endswith((' ', '.')) or any(ord(char) < 32 or char in '<>"|?*' for char in part)
                or part.split('.')[0].rstrip(' .').upper() in reserved):
            raise ReleaseError('Archive path is not portable to Windows')
    return name


def is_link(path):
    info = path.lstat()
    return (stat.S_ISLNK(info.st_mode) or
            bool(getattr(info, 'st_file_attributes', 0) & 0x400))


def exclusive_output(path):
    # O_EXCL rejects an existing final entry, including a reparse point.
    # O_BINARY prevents Windows CRLF translation from changing ZIP bytes.
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    flags |= getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_BINARY', 0)
    return os.open(path, flags, 0o600)


def inventory(root=ROOT):
    """Only explicitly maintained public roots; never traverse private state."""
    root = Path(root)
    entries = {}
    paths = [root / name for name in TOP_FILES if os.path.lexists(root / name)]
    for name in DIRECTORIES:
        directory = root/name
        if os.path.lexists(directory) and is_link(directory):
            raise ReleaseError('Source directory is a link: '+name)
        if not directory.is_dir():
            continue
        for current, dirs, files in os.walk(directory, followlinks=False):
            for child in dirs:
                if is_link(Path(current)/child):
                    raise ReleaseError('Source contains a directory link')
                if child in PRIVATE_DIRS:
                    raise ReleaseError('Private/generated project state inside public sources')
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            paths.extend(Path(current)/f for f in files if f != '.DS_Store' and not f.endswith(('.pyc', '.pyo')))
    total = 0
    for path in sorted(paths):
        relative = safe_name(path.relative_to(root).as_posix())
        if is_link(path) or not path.is_file():
            raise ReleaseError('Public source is a link or non-file: '+relative)
        if path.name == '.env' or path.name.startswith('.env.') or path.suffix.lower() in {'.pem', '.key', '.p12'}:
            raise ReleaseError('Credential/config file in public sources: '+relative)
        if path.stat().st_size > MAX_FILE:
            raise ReleaseError('Public source exceeds per-file limit: '+relative)
        data = path.read_bytes()
        total += len(data)
        if total > MAX_TOTAL:
            raise ReleaseError('Public source inventory exceeds total limit')
        if relative in BINARY_SOURCE_ASSETS:
            if digest(data) != BINARY_SOURCE_ASSETS[relative]:
                raise ReleaseError('Unreviewed binary source bytes: '+relative)
            entries[relative] = data
            continue
        try:
            text = data.decode('utf-8')
        except UnicodeError as exc:
            raise ReleaseError('Unexpected binary source: '+relative) from exc
        if PATH_PATTERN.search(text):
            raise ReleaseError('Machine-local path in public file: '+relative)
        if TOKEN_PATTERN.search(text):
            raise ReleaseError('Credential-like material in public file: '+relative)
        entries[relative] = data
    return entries


def classification(path):
    if '/cases/' in path or path.startswith('examples/'):
        return 'original-synthetic-input'
    if '/recordings/' in path:
        return 'synthetic-task-output-or-normalized-record'
    if path.startswith('profiles/'):
        return 'original-guidance-with-external-source-references'
    if path.startswith('.github/'):
        return 'original-workflow-referencing-pinned-external-actions'
    return 'original-project-content'


def index(root=ROOT):
    """Record reviewed, declared origin; this is not ownership verification."""
    root = Path(root)
    entries = inventory(root)
    records = {name: {'sha256':digest(data), 'license':'MIT',
                      'origin':'authored-for-this-independent-template',
                      'classification':classification(name)}
               for name,data in entries.items() if name != INDEX}
    result = {'format_version':1, 'scope':'Declared project origin and byte identity; external linked works retain their own rights.',
              'excluded_self':INDEX, 'files':records}
    path = root/INDEX
    path.parent.mkdir(parents=True, exist_ok=True)
    if os.path.lexists(path) and is_link(path):
        raise ReleaseError('Refusing to replace linked provenance index')
    temporary = path.with_name('.file-origins-'+uuid.uuid4().hex+'.tmp')
    try:
        with temporary.open('xb') as stream:
            stream.write(encoded(result));stream.flush();os.fsync(stream.fileno())
        os.replace(temporary,path)
    finally:
        temporary.unlink(missing_ok=True)
    return {'passed':True,'indexed_files':len(records),'scope':result['scope']}


def _check_entries(entries):
    """Validate one captured byte map without reading the source tree again."""
    errors = [{'code':'required_file_missing','path':name} for name in REQUIRED if name not in entries]
    errors += [{'code':'unreviewed_binary_source','path':name}
               for name, checksum in BINARY_SOURCE_ASSETS.items()
               if name in entries and digest(entries[name]) != checksum]
    if len({name.casefold() for name in entries}) != len(entries):
        errors.append({'code':'portable_path_collision'})
    if INDEX not in entries:
        errors.append({'code':'provenance_index_missing','path':INDEX})
    else:
        try:
            declared = json.loads(entries[INDEX])
            if not isinstance(declared,dict) or not isinstance(declared.get('files'),dict):
                raise ValueError('Provenance index needs an object and a file map')
            records = declared['files']
            actual = set(entries)-{INDEX}
            if declared.get('format_version') != 1 or set(records)!=actual:
                errors.append({'code':'provenance_inventory_differs'})
            for name in sorted(actual & set(records)):
                value=records[name]
                if (not isinstance(value,dict) or value.get('sha256')!=digest(entries[name]) or
                        value.get('license')!='MIT' or value.get('origin')!='authored-for-this-independent-template'):
                    errors.append({'code':'provenance_record_differs','path':name})
        except (ValueError,KeyError,TypeError):
            errors.append({'code':'provenance_index_invalid'})
    if 'LICENSE' in entries and entries['LICENSE'].splitlines()[:1] != [b'MIT License']:
        errors.append({'code':'unexpected_license'})
    return {'passed':not errors,'version':__version__,'files':len(entries),'errors':errors,
            'scope':'Local source packaging, declared provenance and hygiene only; scientific/task checks run separately.'}


def check(root=ROOT):
    return _check_entries(inventory(root))


def build(output, root=ROOT):
    root=Path(root); output=Path(output)
    # Bytes and the copied map are immutable for both validation and writing.
    entries=MappingProxyType(dict(inventory(root)))
    report=_check_entries(entries)
    if not report['passed']:
        raise ReleaseError('Release source check failed: '+json.dumps(report['errors']))
    prefix=ARCHIVE_ROOT
    manifest={'format_version':1,'version':__version__,'prefix':prefix,
              'files':{name:digest(data) for name,data in entries.items()}}
    if not output.parent.is_dir():
        raise ReleaseError('Archive output parent must already exist')
    fd=exclusive_output(output)
    try:
        with os.fdopen(fd,'wb') as stream:
            with zipfile.ZipFile(stream,'w',compression=zipfile.ZIP_STORED) as archive:
                for name,data in sorted({**entries,ARCHIVE_MANIFEST:encoded(manifest)}.items()):
                    info=zipfile.ZipInfo(prefix+'/'+safe_name(name),(1980,1,1,0,0,0))
                    info.create_system=3;info.external_attr=(stat.S_IFREG|0o644)<<16
                    archive.writestr(info,data)
            stream.flush();os.fsync(stream.fileno())
    except BaseException:
        output.unlink(missing_ok=True)
        raise
    return {'passed':True,'version':__version__,'prefix':prefix,
            'files':len(entries),'sha256':digest(output.read_bytes()),
            'archive_name':output.name,'scope':'Deterministic local archive; no remote publication.'}


def verify(path):
    with zipfile.ZipFile(path) as archive:
        infos=archive.infolist()
        names=[safe_name(i.filename) for i in infos]
        if (not 1 <= len(names) <= 4096 or len(set(names))!=len(names) or
                len({name.casefold() for name in names}) != len(names)):
            raise ReleaseError('Archive has duplicate entries or an unsupported file count')
        if sum(i.file_size for i in infos)>MAX_TOTAL or any(i.file_size>MAX_FILE for i in infos):
            raise ReleaseError('Archive expands beyond size limits')
        if any(stat.S_ISLNK(i.external_attr>>16) or i.flag_bits&1 or i.is_dir() for i in infos):
            raise ReleaseError('Archive includes a link, encryption or unexpected directory entry')
        roots={n.split('/')[0] for n in names}
        if len(roots)!=1:
            raise ReleaseError('Archive needs a single template root')
        prefix=next(iter(roots)); marker=prefix+'/'+ARCHIVE_MANIFEST
        if marker not in names:
            raise ReleaseError('Archive manifest missing')
        manifest=json.loads(archive.read(marker))
        if (not isinstance(manifest,dict) or
                manifest.get('format_version')!=1 or manifest.get('prefix')!=prefix or
                not isinstance(manifest.get('files'),dict) or
                not isinstance(manifest.get('version'),str) or
                prefix not in (ARCHIVE_ROOT, ARCHIVE_ROOT+'-'+manifest['version']) or
                not set((*REQUIRED,INDEX)) <= set(manifest['files'])):
            raise ReleaseError('Invalid archive manifest')
        expected={marker}; entries={}
        for name,checksum in manifest['files'].items():
            entry=prefix+'/'+safe_name(name);expected.add(entry)
            if entry not in names:
                raise ReleaseError('Archive identity check failed: '+name)
            data=archive.read(entry)
            if digest(data)!=checksum:
                raise ReleaseError('Archive identity check failed: '+name)
            entries[name]=data
        if set(names)!=expected:
            raise ReleaseError('Archive contains unlisted resources')
        report=_check_entries(entries)
        if not report['passed']:
            raise ReleaseError('Archive source check failed: '+json.dumps(report['errors']))
    return {'passed':True,'version':manifest['version'],'prefix':prefix,
            'files':len(manifest['files']),
            'sha256':digest(Path(path).read_bytes()),
            'scope':'Archive bytes, inventory and declared provenance; no extraction or publication.'}


def main(argv=None):
    try:
        parser=argparse.ArgumentParser(description=__doc__)
        commands=parser.add_subparsers(dest='command',required=True)
        commands.add_parser('index');commands.add_parser('check')
        commands.add_parser('build').add_argument('--output',required=True)
        commands.add_parser('verify').add_argument('--archive',required=True)
        args=parser.parse_args(argv)
        result=(index() if args.command=='index' else check() if args.command=='check' else
                build(args.output) if args.command=='build' else verify(args.archive))
        print(json.dumps(result,ensure_ascii=False,indent=2));return 0 if result['passed'] else 1
    except (OSError,ValueError,KeyError,TypeError,zipfile.BadZipFile) as exc:
        print(json.dumps({'passed':False,'errors':[{'code':'release_error','message':str(exc)}]},ensure_ascii=True));return 2


if __name__=='__main__':
    raise SystemExit(main())
