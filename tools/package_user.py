#!/usr/bin/env python3
"""Build, verify and smoke-test the current user runtime, without source history."""
from pathlib import Path
from types import MappingProxyType
import argparse
import ast
import json
import os
import stat
import subprocess
import sys
import tempfile
import zipfile

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from core import __version__
from core.bundle import SKILLS, build_payload
from core.storage import CoreError, ProjectFiles
from tools.check_core import payload_link_errors
from tools.release_package import (
    MAX_FILE, MAX_TOTAL, PATH_PATTERN, TOKEN_PATTERN,
    ReleaseError, digest, encoded, safe_name, exclusive_output,
)

PROFILE = 'user-runtime'
ARCHIVE_ROOT = 'research-workflow-template'
MANIFEST = 'USER-PACKAGE-MANIFEST.json'
SOURCE_URL = 'https://github.com/CheshireCat-D/research-workflow-template'
GUIDES = {
    'docs/user-package-guide.md': '中文介绍与使用说明.md',
    'docs/user-package-guide.en.md': 'USER_GUIDE.en.md',
}
CORE_FILES = (
    '__init__.py', 'bundle.py', 'cli.py', 'model.py', 'project.py', 'storage.py',
    'windows_storage.py', 'protocol.md', 'skill-bridge.md',
)
SCHEMAS = (
    'activity', 'artifact', 'decision', 'evidence', 'method-binding',
    'project', 'registry', 'relation', 'source', 'statement',
)
DISCIPLINES = (
    'agriculture-life', 'engineering', 'humanities', 'law', 'medicine-health',
    'natural-sciences', 'social-sciences',
)
METHODS = (
    'computational', 'conceptual-normative', 'empirical-quantitative',
    'engineering-design', 'evidence-synthesis', 'formal-theory',
    'historical-interpretive', 'legal-analysis', 'measurement-experiment', 'qualitative',
)
# Current executable/guidance resources are reviewed explicitly. An unrelated
# file added anywhere under a skill or profile must never become a user asset
# merely because the project-local bundle collector walks that directory.
SKILL_RESOURCES = (
    'rw-figures/agents/openai.yaml',
    'rw-figures/assets/synthetic-figure-spec.json',
    'rw-figures/assets/synthetic-workflow.svg',
    'rw-figures/examples/plot_demo.py',
    'rw-figures/references/editable-schematics.md',
    'rw-figures/scripts/audit_svg_schematic.py',
    'rw-literature/references/search-and-library.md',
    'rw-review/references/cross-material-consistency.md',
    'rw-review/references/review-modes.md',
    'rw-review/references/review-response.md',
    'rw-review/references/submission-delivery.md',
    'rw-review/scripts/check_revision_plan.py',
)
RUNTIME_FILES = frozenset((
    'design/catalog.json',
    'tools/research.py', 'tools/connect_skills.py', 'profiles/sources.json',
    'profiles/selection.md', 'profiles/governance.md',
    'profiles/templates/legal-research.md', 'profiles/templates/legal-source.json',
    *('profiles/disciplines/' + name + '.md' for name in DISCIPLINES),
    *('profiles/methods/' + name + '.md' for name in METHODS),
    *('core/' + name for name in CORE_FILES),
    *('core/schemas/' + name + '.schema.json' for name in SCHEMAS),
    *('skills/' + skill + '/SKILL.md' for skill in SKILLS),
    *('skills/' + name for name in SKILL_RESOURCES),
))
REQUIRED = RUNTIME_FILES | frozenset((
    'README.md', 'README.en.md', '中文介绍与使用说明.md', 'USER_GUIDE.en.md',
    'LICENSE', 'SECURITY.md', 'provenance/ORIGIN.md',
))


def readme(english=False):
    if english:
        return ('# Research Workflow Template\n\n'
                '[中文](README.md) · [English user guide](USER_GUIDE.en.md) · '
                '[中文使用说明](中文介绍与使用说明.md)\n\n'
                'The current local runtime contains nine research skills, method guidance, '
                'and standard-library Python tools. Use Python 3.11+ on macOS, Linux or Windows.\n\n'
                '```sh\n'
                "python3 tools/research.py init --output ../my-research --title 'My research question'\n"
                'python3 tools/connect_skills.py install --root ../my-research\n'
                'python3 tools/research.py resume --root ../my-research\n'
                '```\n\n'
                'In Windows PowerShell, replace `python3` with `py -3` '
                '(or `python` if that is your Python 3.11+ command). Use a local '
                'project folder; close other writers before upgrading skills.\n\n'
                'Choose a new output directory, then open that project in a compatible skill host. '
                'The guide covers daily use, records and upgrades. The '
                '[source repository](' + SOURCE_URL + ') provides development checks and '
                'evaluation evidence separately. This runtime carries no evaluation cases, '
                'development logs or previous editions.\n\n'
                '[MIT license](LICENSE) · [Source attribution](provenance/ORIGIN.md) · '
                '[Data and security boundaries](SECURITY.md)\n')
    return ('# 通用科研工作流模板\n\n'
            '[English](README.en.md) · [中文介绍与使用说明](中文介绍与使用说明.md) · '
            '[English user guide](USER_GUIDE.en.md)\n\n'
            '当前用户包包含九个科研技能、方法指导与标准库 Python 工具。'
            '需要 Python 3.11 或更新版本，支持 macOS、Linux 与 Windows。\n\n'
            '```sh\n'
            "python3 tools/research.py init --output ../my-research --title '我的研究问题'\n"
            'python3 tools/connect_skills.py install --root ../my-research\n'
            'python3 tools/research.py resume --root ../my-research\n'
            '```\n\n'
            'Windows PowerShell 中将 `python3` 换成 `py -3`，或已配置为 '
            'Python 3.11+ 的 `python`。使用本地项目目录，技能升级前先暂停其他写入者。\n\n'
            '将输出路径换成尚不存在的新目录，再在兼容的技能宿主中打开新项目。'
            '指南说明日常使用、登记与升级。开发检查和评估证据另见'
            '[源码仓库](' + SOURCE_URL + ')；用户包不携带评估案例、开发日志或旧版。\n\n'
            '[MIT许可证](LICENSE) · [来源归属](provenance/ORIGIN.md) · '
            '[数据与安全边界](SECURITY.md)\n')


def origin():
    return ('# Source attribution\n\n'
            'This current user runtime contains independently authored project code, '
            'instructions and synthetic demonstration assets, with agent assistance. '
            'They use the root [MIT license](../LICENSE). The separate personal Skills '
            'package and its third-party files are not included.\n\n'
            'External methods and reviewed design influences are recorded in '
            '[profiles/sources.json](../profiles/sources.json). These include the '
            'conditional coding guidance, research figure practices, source indexing, '
            'and Light-skills cross-material consistency idea. External works retain '
            'their own rights; no upstream skill, script, figure or full publication '
            'is copied into this package. Full attribution is maintained in the '
            '[public source record](' + SOURCE_URL + '/blob/main/provenance/ORIGIN.md).\n\n'
            '`USER-PACKAGE-MANIFEST.json` identifies the delivered profile and file '
            'bytes. Its hashes detect changes; they do not certify authorship, '
            'scientific validity or legal correctness.\n')


def inventory(root=ROOT):
    """Use the portable runtime closure, restoring the original skill layout."""
    root = Path(root)
    portable = build_payload(root)
    entries = {}
    with ProjectFiles(root) as files:
        for name, data in portable.items():
            if name.startswith('_rw-runtime/'):
                relative = name.removeprefix('_rw-runtime/')
            else:
                relative = 'skills/' + name
            if relative not in RUNTIME_FILES:
                raise ReleaseError('Unreviewed resource outside the current user runtime: ' + relative)
            # The standard source layout keeps all original skill links.
            entries[relative] = (files.read(relative) if relative.startswith('skills/') else data)
        for name in ('LICENSE', 'SECURITY.md'):
            entries[name] = files.read(name)
        for source, destination in GUIDES.items():
            entries[destination] = files.read(source)
    entries.update({
        'README.md': readme().encode('utf-8'),
        'README.en.md': readme(True).encode('utf-8'),
        'provenance/ORIGIN.md': origin().encode('utf-8'),
    })
    return entries


def allowed(name):
    return name in REQUIRED


def _check_entries(entries):
    errors = [{'code': 'required_file_missing', 'path': name}
              for name in sorted(REQUIRED - entries.keys())]
    total = 0
    for name, data in entries.items():
        safe_name(name)
        if not allowed(name):
            errors.append({'code': 'outside_user_profile', 'path': name})
        if name.rsplit('/', 1)[-1].startswith('.env') or name.endswith(('.key', '.pem', '.p12')):
            errors.append({'code': 'private_resource', 'path': name})
        total += len(data)
        if len(data) > MAX_FILE:
            errors.append({'code': 'resource_too_large', 'path': name})
        text = data.decode('utf-8')
        if PATH_PATTERN.search(text) or TOKEN_PATTERN.search(text):
            errors.append({'code': 'private_content', 'path': name})
        if name.endswith('.py'):
            try:
                ast.parse(text, filename=name, feature_version=(3, 11))
            except SyntaxError:
                errors.append({'code': 'invalid_python_resource', 'path': name})
    if total > MAX_TOTAL:
        errors.append({'code': 'profile_too_large'})
    if entries.get('LICENSE', b'').splitlines()[:1] != [b'MIT License']:
        errors.append({'code': 'unexpected_license'})
    if 'design/catalog.json' in entries:
        catalog = json.loads(entries['design/catalog.json'])
        implemented = {item['id'] for item in catalog['skills'] if item['status'] == 'implemented'}
        if implemented != set(SKILLS):
            errors.append({'code': 'skill_catalog_differs'})
        profiles = [item['profile'] for item in catalog['disciplines']]
        profiles += [item['implementation']['profile'] for item in catalog['methods']
                     if item.get('implementation', {}).get('status') == 'guidance-slice']
        for name in profiles:
            if name not in entries:
                errors.append({'code': 'profile_resource_missing', 'path': name})
        for method in catalog['methods']:
            evidence = method.get('implementation', {}).get('task_evidence')
            if evidence and evidence.get('availability') != 'not-included-in-project-runtime':
                errors.append({'code': 'evaluation_scope_not_sanitized', 'path': method['id']})
    errors.extend({'code': 'broken_local_link', **item} for item in payload_link_errors(entries))
    return {'passed': not errors, 'profile': PROFILE, 'version': __version__,
            'files': len(entries), 'errors': errors,
            'scope': 'Current runtime closure, local links and declared source hygiene only.'}


def check(root=ROOT):
    return _check_entries(inventory(root))


def build(output, root=ROOT):
    entries = MappingProxyType(dict(inventory(root)))
    report = _check_entries(entries)
    if not report['passed']:
        raise ReleaseError('User profile check failed: ' + json.dumps(report['errors']))
    manifest = {'format_version': 1, 'profile': PROFILE, 'version': __version__,
                'prefix': ARCHIVE_ROOT, 'license': 'MIT',
                'origin': 'independently-authored-project-content',
                'files': {name: digest(data) for name, data in sorted(entries.items())}}
    output = Path(output)
    if not output.parent.is_dir():
        raise ReleaseError('Archive output parent must already exist')
    fd = exclusive_output(output)
    try:
        with os.fdopen(fd, 'wb') as stream:
            with zipfile.ZipFile(stream, 'w', compression=zipfile.ZIP_STORED) as archive:
                for name, data in sorted({**entries, MANIFEST: encoded(manifest)}.items()):
                    info = zipfile.ZipInfo(ARCHIVE_ROOT + '/' + name, (1980, 1, 1, 0, 0, 0))
                    info.create_system = 3
                    info.external_attr = (stat.S_IFREG | 0o644) << 16
                    archive.writestr(info, data)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        output.unlink(missing_ok=True)
        raise
    return {'passed': True, 'profile': PROFILE, 'version': __version__,
            'prefix': ARCHIVE_ROOT, 'files': len(entries),
            'sha256': digest(output.read_bytes()), 'archive_name': output.name,
            'scope': 'Deterministic current user package; no remote publication.'}


def _read_archive(path):
    """Capture and validate bytes once, before verification or isolated execution."""
    data = Path(path).read_bytes()
    import io
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        infos = archive.infolist()
        names = [safe_name(info.filename) for info in infos]
        if (not 1 <= len(names) <= 4096 or len(names) != len(set(names)) or
                len({name.casefold() for name in names}) != len(names) or
                sum(info.file_size for info in infos) > MAX_TOTAL or
                any(info.file_size > MAX_FILE or info.flag_bits & 1 or info.is_dir() or
                    stat.S_ISLNK(info.external_attr >> 16) for info in infos)):
            raise ReleaseError('Unsupported user archive entries')
        prefix = ARCHIVE_ROOT + '/'
        marker = prefix + MANIFEST
        if marker not in names or any(not name.startswith(prefix) for name in names):
            raise ReleaseError('User archive needs the fixed current root and manifest')
        manifest = json.loads(archive.read(marker))
        if (not isinstance(manifest, dict) or manifest.get('format_version') != 1 or
                manifest.get('profile') != PROFILE or manifest.get('version') != __version__ or
                manifest.get('prefix') != ARCHIVE_ROOT or manifest.get('license') != 'MIT' or
                manifest.get('origin') != 'independently-authored-project-content' or
                not isinstance(manifest.get('files'), dict)):
            raise ReleaseError('Invalid user package manifest')
        expected = {marker}
        entries = {}
        for name, checksum in manifest['files'].items():
            entry = prefix + safe_name(name)
            expected.add(entry)
            if entry not in names:
                raise ReleaseError('User archive resource missing: ' + name)
            content = archive.read(entry)
            if digest(content) != checksum:
                raise ReleaseError('User archive identity check failed: ' + name)
            entries[name] = content
        if set(names) != expected:
            raise ReleaseError('User archive contains unlisted resources')
        report = _check_entries(entries)
        if not report['passed']:
            raise ReleaseError('User archive profile failed: ' + json.dumps(report['errors']))
        marker_bytes = archive.read(marker)
    return entries, {'passed': True, 'profile': PROFILE, 'version': __version__,
                     'prefix': ARCHIVE_ROOT, 'files': len(entries), 'sha256': digest(data),
                     'scope': 'Archive byte identity, runtime closure and local links; no execution.'}, marker_bytes


def verify(path):
    return _read_archive(path)[1]


def _snapshot(root):
    return {path.relative_to(root).as_posix():
            (digest(path.read_bytes()), path.stat().st_mtime_ns)
            for path in root.rglob('*') if path.is_file()}


def smoke(path):
    """Execute a verified current runtime in an empty temporary home and project."""
    entries, verified, marker_bytes = _read_archive(path)
    commands = 0
    with tempfile.TemporaryDirectory(prefix='rw-user-acceptance-') as temporary:
        base = Path(temporary)
        root = base / ARCHIVE_ROOT
        for name, data in entries.items():
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        # Exercise the delivered archive layout, including its profile marker.
        (root / MANIFEST).write_bytes(marker_bytes)
        home, scratch = base / 'home', base / 'tmp'
        home.mkdir()
        scratch.mkdir()
        environment = dict(os.environ, HOME=str(home), USERPROFILE=str(home),
                           TMPDIR=str(scratch), TMP=str(scratch), TEMP=str(scratch),
                           PYTHONDONTWRITEBYTECODE='1')

        def invoke(script, *arguments, record=None):
            nonlocal commands
            commands += 1
            result = subprocess.run([sys.executable, '-X', 'utf8', '-I', '-B', str(script),
                                     *map(str, arguments)], cwd=base, env=environment,
                                    input=json.dumps(record) if record is not None else None,
                                    capture_output=True, text=True, encoding='utf-8', timeout=30)
            if result.returncode:
                raise ReleaseError('User runtime command failed: ' + result.stdout + result.stderr)
            report = json.loads(result.stdout)
            if not report.get('passed', True):
                raise ReleaseError('User runtime reported a failed command')
            return report

        before_source = _snapshot(root)
        choices = invoke(root / 'tools/research.py', 'options')
        for method in choices['methods']:
            implementation = method.get('implementation', {})
            evidence = implementation.get('task_evidence')
            if evidence and (evidence.get('availability') != 'not-included-in-project-runtime' or
                             implementation['variant_evidence']['availability'] !=
                             'not-included-in-project-runtime'):
                raise ReleaseError('Extracted user runtime misreported evaluation availability')
        project = base / 'research project'
        invoke(root / 'tools/research.py', 'init', '--output', project,
               '--title', 'Synthetic user-package acceptance', '--discipline', 'law',
               '--method', 'legal-analysis')
        invoke(root / 'tools/connect_skills.py', 'install', '--root', project)
        invoke(root / 'tools/connect_skills.py', 'check', '--root', project)
        invoke(root / 'tools/research.py', 'register', '--root', project,
               '--kind', 'statement', '--file', '-', record={
                   'id': 'Q-USER', 'text': 'A synthetic scoped question.',
                   'type': 'question', 'scope': 'Package engineering acceptance only',
               })
        invoke(root / 'tools/research.py', 'checkpoint', '--root', project,
               '--next-action', 'Inspect the supplied sources')
        before_project = _snapshot(project)
        invoke(root / 'tools/research.py', 'resume', '--root', project)
        if _snapshot(project) != before_project or _snapshot(root) != before_source:
            raise ReleaseError('Read-only recovery or source integrity check failed')
        moved = base / 'moved research 项目'
        project.rename(moved)
        root.rename(base / 'relocated toolkit')
        runtime = moved / '.agents/skills/_rw-runtime'
        before_moved = _snapshot(moved)
        invoke(runtime / 'tools/research.py', 'options')
        connected = invoke(runtime / 'tools/connect_skills.py', 'check',
                           '--installed-only', '--root', moved)
        for command in ('check', 'status', 'resume'):
            invoke(runtime / 'tools/research.py', command, '--root', moved)
        if not connected['installed_integrity'] or _snapshot(moved) != before_moved:
            raise ReleaseError('Moved runtime integrity or read-only check failed')
    return {'passed': True, 'profile': PROFILE, 'sha256': verified['sha256'],
            'commands_executed': commands, 'empty_home_and_tmp': True,
            'extracted_user_runtime_evaluation_scope_preserved': True,
            'source_bytes_and_mtime_unchanged': True,
            'read_only_project_bytes_and_mtime_unchanged': True,
            'moved_runtime_without_source_dependency': True,
            'scope': 'Clean current user-package engineering execution; no research certification.'}


def main(argv=None):
    try:
        parser = argparse.ArgumentParser(description=__doc__)
        commands = parser.add_subparsers(dest='command', required=True)
        commands.add_parser('check')
        commands.add_parser('build').add_argument('--output', required=True)
        for command in ('verify', 'smoke'):
            commands.add_parser(command).add_argument('--archive', required=True)
        args = parser.parse_args(argv)
        result = (check() if args.command == 'check' else
                  build(args.output) if args.command == 'build' else
                  verify(args.archive) if args.command == 'verify' else smoke(args.archive))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result['passed'] else 1
    except (OSError, ValueError, KeyError, TypeError, CoreError,
            subprocess.SubprocessError, zipfile.BadZipFile) as exc:
        print(json.dumps({'passed': False, 'errors': [
            {'code': 'user_package_error', 'message': str(exc)}]}, ensure_ascii=True))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
