"""Build and inspect a project-local skill bundle, without global installation.

Source instructions are maintained in skills/, core/ and profiles/. Copies in a
project are generated artifacts; their manifest detects drift, not authorship.
"""
from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
import os
from pathlib import Path
import posixpath
import re
import shutil
import stat
from urllib.parse import quote, unquote, urlsplit, urlunsplit
import uuid

from .project import load
from .storage import CoreError, ProjectFiles, json_bytes, object_sha, parse_json, path_parts, sha

SKILLS = tuple('rw-' + name for name in (
    'workflow', 'question', 'literature', 'innovation', 'candidates',
    'validation', 'writing', 'review',
))
MANIFEST = '_rw-runtime/bundle-manifest.json'
BUNDLE_PATH = '.agents/skills'
BUNDLE_ID = 'research-workflow-template'
LEGACY_BUNDLE_ID = 'research-workflow-template-d2'
SCOPE = 'Project-local instruction/runtime copies and their integrity only; not host discovery, scientific validation or authorship authentication.'
_HASH = re.compile(r'[0-9a-f]{64}\Z')


def catalog_view(choices, toolkit, *, project_runtime=False):
    """Keep full-distribution evidence distinct from portable local guidance."""
    result = deepcopy(choices)
    note = ('Evaluation references use the full distribution at task_evidence.resource_base; '
            'check its availability before opening them as local resources.')
    for method in result['methods']:
        implementation = method.get('implementation', {})
        evidence = implementation.get('task_evidence')
        if not isinstance(evidence, dict):
            continue
        evidence['resource_base'] = 'full-distribution-root'
        evidence.setdefault('review', 'evals/d3/independent-review.json')
        if project_runtime:
            evidence['availability'] = 'not-included-in-project-runtime'
        else:
            paths = [evidence.get('coverage'), evidence.get('review')]
            evidence['availability'] = ('available' if all(
                isinstance(path, str) and (Path(toolkit)/path).is_file() for path in paths)
                else 'not-found-in-distribution')
        if note not in implementation.get('validation_scope', ''):
            implementation['validation_scope'] = (implementation.get('validation_scope', '') + ' ' + note).strip()
    return result


def source_root():
    return Path(__file__).resolve().parents[1]


def _source_bytes(root, path):
    # Use the same no-internal-symlink policy for build inputs and project data.
    with ProjectFiles(root) as files:
        try:
            return files.read(path)
        except FileNotFoundError as exc:
            raise CoreError('bundle_source_missing', 'Required source is missing: ' + path) from exc


def _rewrite_skill_links(text, relative):
    """Relocate Markdown destinations from one source skill into the runtime.

    Only inline/image link destinations and reference definitions are changed.
    Literal path examples, inline code, fences and links inside the skill stay
    as authored. Destination depth is derived from the actual source document.
    """
    source_parent = posixpath.dirname(relative)
    destination_parent = posixpath.dirname(relative.removeprefix('skills/'))

    def destination(value):
        angled = value.startswith('<') and value.endswith('>')
        href = value[1:-1] if angled else value
        parsed = urlsplit(href)
        if parsed.scheme or parsed.netloc or not parsed.path or parsed.path.startswith('/'):
            return value
        resolved = posixpath.normpath(posixpath.join(source_parent, unquote(parsed.path)))
        if resolved.split('/', 1)[0] not in {'core', 'profiles', 'tools'}:
            return value
        relocated = posixpath.relpath('_rw-runtime/' + resolved, destination_parent)
        if parsed.path.endswith('/'):
            relocated += '/'
        href = urlunsplit(('', '', quote(relocated, safe='/'), parsed.query, parsed.fragment))
        return '<' + href + '>' if angled else href

    inline = re.compile(r'(!?\[[^\]\n]*\]\([ \t]*)(<[^>\n]+>|[^\s()]+)')
    definition = re.compile(r'^([ \t]{0,3}\[[^\]\n]+\]:[ \t]*)(<[^>\n]+>|[^\s]+)')

    def rewrite_plain(value):
        return inline.sub(lambda m: m[1] + destination(m[2]), value)

    lines, fence = [], None
    for line in text.splitlines(keepends=True):
        marker = re.match(r'^[ \t]{0,3}(`{3,}|~{3,})', line)
        if fence is not None:
            lines.append(line)
            if marker and marker[1][0] == fence[0] and len(marker[1]) >= len(fence):
                fence = None
            continue
        if marker:
            fence = marker[1]
            lines.append(line)
            continue
        line = definition.sub(lambda m: m[1] + destination(m[2]), line)
        # A code span is closed by a run of the same length; unequal backticks
        # within it are content. Unclosed runs are ordinary Markdown text.
        parts, offset = [], 0
        for opening in re.finditer(r'`+', line):
            if opening.start() < offset:
                continue
            closing = re.search(r'(?<!`)' + re.escape(opening[0]) + r'(?!`)', line[opening.end():])
            if closing is None:
                continue
            end = opening.end() + closing.end()
            parts.extend((rewrite_plain(line[offset:opening.start()]), line[opening.start():end]))
            offset = end
        parts.append(rewrite_plain(line[offset:]))
        lines.append(''.join(parts))
    return ''.join(lines)


def build_payload(root=None):
    """Return deterministic relative destination -> bytes, with no source writes."""
    root = Path(root) if root is not None else source_root()
    payload = {}
    for skill in SKILLS:
        folder = root / 'skills' / skill
        if not (folder / 'SKILL.md').is_file():
            raise CoreError('bundle_source_missing', 'Required skill is missing: ' + skill)
        for path in sorted(folder.rglob('*')):
            if path.is_symlink():
                raise CoreError('unsafe_path', 'Skill sources cannot contain symbolic links')
            if not path.is_file() or '__pycache__' in path.parts:
                continue
            relative = path.relative_to(root).as_posix()
            content = _source_bytes(root, relative)
            if path.suffix == '.md':
                content = _rewrite_skill_links(content.decode('utf-8'), relative).encode('utf-8')
            payload[path.relative_to(root / 'skills').as_posix()] = content
    runtime_paths = []
    for pattern in ('core/*.py', 'core/*.md', 'core/schemas/*.json',
                    'profiles/**/*.md', 'profiles/**/*.json'):
        runtime_paths.extend(root.glob(pattern))
    runtime_paths.extend(root / name for name in (
        'design/catalog.json', 'tools/research.py', 'tools/connect_skills.py',
    ))
    cat = parse_json(_source_bytes(root, 'design/catalog.json'))
    required = ['core/skill-bridge.md'] + [
        item['implementation']['profile'] for item in cat['methods']
        if item.get('implementation', {}).get('status') == 'guidance-slice'
    ] + [item['profile'] for item in cat['disciplines'] if 'profile' in item]
    for relative in required:
        _source_bytes(root, relative)
    for path in sorted(set(runtime_paths)):
        relative = path.relative_to(root).as_posix()
        content = _source_bytes(root, relative)
        if relative == 'design/catalog.json':
            content = json_bytes(catalog_view(parse_json(content), root, project_runtime=True))
        payload['_rw-runtime/' + relative] = content
    return payload


def _manifest(payload):
    fingerprints = {name: sha(content) for name, content in sorted(payload.items())}
    return {'format_version': '2', 'bundle_id': BUNDLE_ID, 'skills': list(SKILLS),
            'files': fingerprints, 'payload_sha256': object_sha(fingerprints)}


def _exists(parent, name):
    try:
        return os.stat(name, dir_fd=parent, follow_symlinks=False)
    except FileNotFoundError:
        return None


@contextmanager
def _directory(parent, name):
    try:
        fd = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
    except FileNotFoundError:
        raise
    except OSError as exc:
        raise CoreError('unsafe_path', 'A bundle directory is a link or not a directory') from exc
    try:
        yield fd
    finally:
        os.close(fd)


def _stage_payload(project, parent, staging, payload, manifest):
    """Fill a directory already created exclusively by the current operation."""
    with _directory(parent, staging) as stage_fd:
        staged = ProjectFiles.__new__(ProjectFiles)
        staged.fd = os.dup(stage_fd)
        staged.root = project.root / '.agents' / staging
        try:
            for relative, content in payload.items():
                staged.write(relative, content)
            staged.write(MANIFEST, json_bytes(manifest))
        finally:
            staged.close()


def install(root):
    """Publish one complete bundle into a previously absent .agents/skills.

    The writer lock coordinates our CLI writers. Whole-directory replacement by
    an adversarial writer outside this protocol is not a supported concurrency
    guarantee, consistent with the metadata core.
    """
    payload = build_payload()
    manifest = _manifest(payload)
    with ProjectFiles(root) as project:
        # Invalid roots must not gain a lock directory merely from validation.
        load(project)
        with project.lock():
            load(project)  # Recheck after acquiring the writer lock.
            with project.parent(BUNDLE_PATH, create=True) as (parent, name):
                if _exists(parent, name) is not None:
                    raise CoreError('skill_target_exists', 'Refusing to replace existing project .agents/skills')
                staging = '.rw-skills-' + uuid.uuid4().hex
                os.mkdir(staging, mode=0o700, dir_fd=parent)
                try:
                    _stage_payload(project, parent, staging, payload, manifest)
                    if _exists(parent, name) is not None:
                        raise CoreError('skill_target_exists', 'Project .agents/skills appeared during installation')
                    os.rename(staging, name, src_dir_fd=parent, dst_dir_fd=parent)
                    os.fsync(parent)
                finally:
                    if _exists(parent, staging) is not None:
                        shutil.rmtree(staging, dir_fd=parent)
    return {'passed': True, 'installed': True, 'scope': SCOPE,
            'target': BUNDLE_PATH, 'skills': list(SKILLS), 'files': len(payload),
            'payload_sha256': manifest['payload_sha256'], 'global_installation': False,
            'project_records_modified': False}


def _validate_manifest(value):
    if (not isinstance(value, dict) or set(value) != {
            'format_version', 'bundle_id', 'skills', 'files', 'payload_sha256'} or
            (value['format_version'], value['bundle_id']) not in (
                ('1', LEGACY_BUNDLE_ID), ('2', BUNDLE_ID)) or
            not isinstance(value['skills'], list) or not value['skills'] or
            any(not isinstance(s, str) for s in value['skills']) or
            len(set(value['skills'])) != len(value['skills']) or
            not set(value['skills']) <= set(SKILLS) or not isinstance(value['files'], dict) or
            not 1 <= len(value['files']) <= 1024):
        raise CoreError('invalid_bundle_manifest', 'Unsupported or malformed bundle manifest')
    for path, digest in value['files'].items():
        parts = path_parts(path)
        if (parts[0] not in (*value['skills'], '_rw-runtime') or len(parts) < 2 or path == MANIFEST or
                not isinstance(digest, str) or not _HASH.fullmatch(digest)):
            raise CoreError('invalid_bundle_manifest', 'Invalid managed resource path or digest')
    required = [skill + '/SKILL.md' for skill in value['skills']] + [
        '_rw-runtime/core/skill-bridge.md', '_rw-runtime/core/protocol.md',
        '_rw-runtime/core/cli.py', '_rw-runtime/tools/research.py',
        '_rw-runtime/design/catalog.json',
    ]
    if (not all(path in value['files'] for path in required) or
            value['payload_sha256'] != object_sha(value['files'])):
        raise CoreError('invalid_bundle_manifest', 'Manifest is incomplete or its resource map changed')
    return value


def _walk(parent, prefix=''):
    """Inventory without following links. Unknown links are findings, never read."""
    result = {}
    for name in os.listdir(parent):
        relative = prefix + name
        info = os.stat(name, dir_fd=parent, follow_symlinks=False)
        if stat.S_ISDIR(info.st_mode):
            result[relative + '/'] = 'directory'
            with _directory(parent, name) as child:
                result.update(_walk(child, relative + '/'))
        elif stat.S_ISREG(info.st_mode):
            result[relative] = 'file'
        else:
            result[relative] = 'unsafe'
        if len(result) > 4096:
            raise CoreError('bundle_too_large', 'Bundle inventory exceeds the local check limit')
    return result


def _inspect_installed(project):
    """Check one held installed directory, including otherwise-unlisted empty dirs."""
    try:
        with project.parent(BUNDLE_PATH + '/_inventory') as (bundle_fd, _):
            identity = os.fstat(bundle_fd)
            bundle = ProjectFiles.__new__(ProjectFiles)
            bundle.fd, bundle.root = os.dup(bundle_fd), project.root / BUNDLE_PATH
            try:
                manifest = _validate_manifest(parse_json(bundle.read(MANIFEST)))
                return _inspect_bundle(bundle, manifest), (identity.st_dev, identity.st_ino)
            finally:
                bundle.close()
    except FileNotFoundError as exc:
        raise CoreError('bundle_missing', 'No complete project-local bundle is present; use install for a new target') from exc


def _inspect_bundle(bundle, manifest):
    with bundle.parent('_inventory') as (bundle_fd, _):
        inventory = _walk(bundle_fd)
    findings = []
    expected = set(manifest['files']) | {MANIFEST}
    expected.update('/'.join(path.split('/')[:count]) + '/'
                    for path in tuple(expected) for count in range(1, len(path.split('/'))))
    for relative in sorted(set(inventory) - expected):
        findings.append({'code': 'unexpected_bundle_resource', 'path': relative})
    for relative, digest in manifest['files'].items():
        if relative not in inventory:
            findings.append({'code': 'bundle_resource_missing', 'path': relative})
        elif inventory[relative] != 'file':
            findings.append({'code': 'unsafe_bundle_resource', 'path': relative})
        else:
            try:
                current = sha(bundle.read(relative))
            except FileNotFoundError as exc:
                raise CoreError('concurrent_change', 'An installed resource disappeared during inspection; retry') from exc
            if current != digest:
                findings.append({'code': 'bundle_resource_changed', 'path': relative})
    return manifest, findings


def check(root, *, compare_source=True):
    """Inspect installed bytes and version, with no lock or filesystem mutation."""
    with ProjectFiles(root) as project:
        (manifest, findings), _ = _inspect_installed(project)
    source_matches = None
    if compare_source:
        current = _manifest(build_payload())
        source_matches = current['payload_sha256'] == manifest['payload_sha256']
    if source_matches is False:
        findings.append({'code': 'bundle_source_version_differs',
                         'note': 'The source bundle differs; review before connecting a fresh copy. No files were replaced.'})
    return {'passed': not findings, 'read_only': True, 'scope': SCOPE,
            'installed_integrity': not any(x['code'] != 'bundle_source_version_differs' for x in findings),
            'source_version_matches': source_matches,
            'source_comparison_performed': compare_source,
            'target': BUNDLE_PATH, 'skills': manifest['skills'], 'files': len(manifest['files']),
            'payload_sha256': manifest['payload_sha256'], 'findings': findings}


def _require_clean_bundle(project):
    (manifest, findings), identity = _inspect_installed(project)
    if findings:
        raise CoreError('bundle_modified',
                        'Installed resources changed, are missing or unknown; preserve/review local edits before upgrading')
    return manifest, identity


def _directory_identity(parent, name):
    info = _exists(parent, name)
    if info is None or not stat.S_ISDIR(info.st_mode):
        raise CoreError('concurrent_change', 'Installed bundle directory changed during upgrade')
    return info.st_dev, info.st_ino


def upgrade(root):
    """Explicitly replace a clean installed bundle from a full source distribution.

    Portable POSIX rename cannot exchange two nonempty directories in one step.
    We stage a complete copy, retain the old directory until publication succeeds,
    and roll back caught publication errors. Readers can see a brief absent path;
    interruption/power-loss recovery is not a single-transaction guarantee.
    """
    source = source_root()
    if (source / 'bundle-manifest.json').is_file():
        raise CoreError('bundle_source_required', 'Run upgrade from the full template distribution, not its installed runtime')
    with ProjectFiles(root) as project:
        load(project)
        installed, identity = _require_clean_bundle(project)
        payload = build_payload()
        manifest = _manifest(payload)
        result = {'passed': True, 'upgraded': False, 'scope': SCOPE,
                  'target': BUNDLE_PATH, 'skills': list(SKILLS), 'files': len(payload),
                  'payload_sha256': manifest['payload_sha256'], 'global_installation': False,
                  'project_records_modified': False}
        if installed['payload_sha256'] == manifest['payload_sha256']:
            return result
        with project.lock():
            load(project)
            current, current_identity = _require_clean_bundle(project)
            if current['payload_sha256'] != installed['payload_sha256'] or current_identity != identity:
                raise CoreError('concurrent_change', 'Installed bundle changed before upgrade acquired the writer lock; retry')
            with project.parent(BUNDLE_PATH) as (parent, name):
                staging, backup = '.rw-skills-stage-' + uuid.uuid4().hex, '.rw-skills-backup-' + uuid.uuid4().hex
                published = False
                os.mkdir(staging, mode=0o700, dir_fd=parent)
                try:
                    _stage_payload(project, parent, staging, payload, manifest)
                    # Staging may be slow. Recheck edits just before moving the
                    # old tree rather than trusting only the preflight result.
                    latest, latest_identity = _require_clean_bundle(project)
                    if (latest['payload_sha256'] != installed['payload_sha256'] or latest_identity != identity
                            or _directory_identity(parent, name) != identity):
                        raise CoreError('concurrent_change', 'Installed bundle changed while staging the upgrade; retry')
                    stage_identity = _directory_identity(parent, staging)
                    if _exists(parent, backup) is not None:
                        raise CoreError('concurrent_change', 'Upgrade backup path already exists; nothing was replaced')
                    os.rename(name, backup, src_dir_fd=parent, dst_dir_fd=parent)
                    try:
                        os.rename(staging, name, src_dir_fd=parent, dst_dir_fd=parent)
                        published = True
                        os.fsync(parent)
                    except BaseException as exc:
                        restored_old = False
                        try:
                            if published:
                                if _directory_identity(parent, name) != stage_identity:
                                    raise CoreError('upgrade_recovery_required',
                                                    'Publication path changed; old bundle retained at .agents/' + backup)
                                os.rename(name, staging, src_dir_fd=parent, dst_dir_fd=parent)
                                published = False
                            if _exists(parent, name) is not None:
                                raise CoreError('upgrade_recovery_required',
                                                'Publication path appeared; old bundle retained at .agents/' + backup)
                            os.rename(backup, name, src_dir_fd=parent, dst_dir_fd=parent)
                            restored_old = True
                            os.fsync(parent)
                        except CoreError:
                            raise
                        except BaseException as rollback_error:
                            if restored_old:
                                raise CoreError('upgrade_recovery_required',
                                                'Old bundle restored, but directory synchronization failed; review before retry') from rollback_error
                            raise CoreError('upgrade_recovery_required',
                                            'Rollback failed; preserve .agents/' + backup + ' for recovery') from rollback_error
                        raise
                    try:
                        shutil.rmtree(backup, dir_fd=parent)
                    except OSError as exc:
                        raise CoreError('upgrade_cleanup_required',
                                        'New bundle installed; remove the leftover old bundle after review: .agents/' + backup) from exc
                finally:
                    if _exists(parent, staging) is not None:
                        shutil.rmtree(staging, dir_fd=parent)
                    # If rollback itself fails, keep the backup for explicit
                    # recovery. Never delete the only remaining old copy.
        result['upgraded'] = True
        result['previous_payload_sha256'] = installed['payload_sha256']
        return result
