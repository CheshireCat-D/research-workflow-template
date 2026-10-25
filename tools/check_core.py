#!/usr/bin/env python3
"""Run repository checks; temporary projects only, no network or global installation."""
from pathlib import Path
import argparse
import ast
import json
import math
import os
import posixpath
import re
import subprocess
import sys
import tempfile
from urllib.parse import unquote, urlsplit

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from core.model import export_schemas
from core.bundle import SKILLS, build_payload

IGNORED_SOURCE_DIRS = {
    '.git', '.venv', 'venv', 'build', 'dist', '__pycache__',
    '.pytest_cache', '.mypy_cache', '.ruff_cache', 'node_modules',
    '.agents', '.research', 'private-data', 'local-config',
}


def plain_discovery_string(value):
    """Accept unambiguous YAML strings without adding a YAML runtime dependency.

    A host may interpret numeric/date/boolean-looking scalars as other types.
    Require quotes for them and for YAML mapping/comment syntax instead of
    silently accepting a description the host cannot discover as a string.
    """
    reserved = {'null', '~', 'true', 'false', 'yes', 'no', 'on', 'off',
                '.nan', '.inf', '+.inf', '-.inf'}
    number = r'[-+]?(?:(?:[0-9][0-9_]*(?::[0-5]?[0-9])*(?:\.[0-9_]*)?|\.[0-9_]+)(?:[eE][-+]?[0-9]+)?|0[xX][0-9a-fA-F_]+|0[bB][01_]+|0[oO][0-7_]+)'
    date = r'[0-9]{4}-[0-9]{1,2}-[0-9]{1,2}(?:(?:[Tt]|[ \t]+)[0-9]{1,2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]*)?(?:[ \t]*(?:[Zz]|[-+][0-9]{1,2}(?::[0-9]{2})?))?)?'
    return (bool(value) and value[0] not in '|>!&*[]{},#@%`' and
            value.lower() not in reserved and
            re.fullmatch(number, value) is None and re.fullmatch(date, value) is None and
            re.search(r':(?:\s|$)|(?:^|\s)#|^[-?:](?:\s|$)', value) is None)


def positive_seconds(value):
    try:
        seconds = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError('Expected a positive finite number of seconds') from exc
    if not math.isfinite(seconds) or seconds <= 0:
        raise argparse.ArgumentTypeError('Expected a positive finite number of seconds')
    return seconds


def captured_text(value):
    # TimeoutExpired can contain bytes even when the subprocess used text=True.
    return value.decode('utf-8', errors='replace') if isinstance(value, bytes) else value or ''


def skill_metadata(content):
    """Validate the two discovery fields without requiring a YAML dependency.

    Discovery values support plain/quoted single-line strings and indented
    description blocks (>, >-, >+, |, |-, |+). Other YAML structures are not
    interpreted as strings. This is a bounded frontmatter subset, not a YAML
    loader; optional fields are left to the host's skill loader.
    """
    front = re.match(r'\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)', content, re.S)
    if front is None:
        raise ValueError('Missing skill frontmatter')
    lines, fields = front[1].splitlines(), {}
    for index, line in enumerate(lines):
        field = re.match(r'^(name|description):[ \t]*(.*)$', line)
        if field is None:
            continue
        key, value = field.groups()
        value = value.strip()
        if key in fields:
            raise ValueError('Repeated skill discovery field: ' + key)
        if value in ('>', '>-', '>+', '|', '|-', '|+'):
            if key != 'description':
                raise ValueError('Skill name must be a single-line string')
            block = []
            for child in lines[index + 1:]:
                if child.strip() and not child.startswith(' '):
                    break
                if child.startswith('\t'):
                    raise ValueError('Description blocks must use space indentation')
                block.append(child.strip())
            value = '\n'.join(block).strip()
        elif value.startswith('"'):
            try:
                value = json.loads(value)
            except ValueError as exc:
                raise ValueError('Invalid quoted skill discovery string') from exc
        elif value.startswith("'"):
            if re.fullmatch(r"'(?:[^']|'')*'", value) is None:
                raise ValueError('Invalid quoted skill discovery string')
            value = value[1:-1].replace("''", "'")
        elif not plain_discovery_string(value):
            raise ValueError('Discovery fields need an unambiguous string; quote scalar-like values and YAML syntax')
        if not isinstance(value, str) or not value.strip():
            raise ValueError('Empty skill discovery field: ' + key)
        fields[key] = value
    if set(fields) != {'name', 'description'}:
        raise ValueError('Skill needs name and description')
    return fields


def markdown_links(content):
    """Read inline/image links and reference definitions outside fenced code."""
    lines, fence = [], None
    for line in content.splitlines():
        marker = re.match(r'^\s{0,3}(`{3,}|~{3,})', line)
        if marker:
            token = marker[1]
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
            continue
        if fence is None:
            lines.append(re.sub(r'(`+).*?\1', '', line))
    text = '\n'.join(lines)
    for match in re.finditer(r'\]\(\s*(<[^>\n]+>|[^\s)]+)', text):
        yield match[1].strip('<>')
    for match in re.finditer(r'^\s{0,3}\[[^\]\n]+\]:\s*(<[^>\n]+>|\S+)', text, re.M):
        yield match[1].strip('<>')


def payload_link_errors(payload):
    """Check the installed layout itself, without writing a generated bundle."""
    missing = []
    for document, data in payload.items():
        if not document.endswith('.md'):
            continue
        for link in markdown_links(data.decode('utf-8')):
            url = urlsplit(link)
            if url.scheme or url.netloc or not url.path:
                continue
            path = unquote(url.path)
            target = posixpath.normpath(posixpath.join(posixpath.dirname(document), path))
            inside = not path.startswith('/') and target != '..' and not target.startswith('../')
            exists = target in payload or any(p.startswith(target.rstrip('/') + '/') for p in payload)
            if not inside or not exists:
                missing.append({'document': document, 'link': link, 'target': target})
    return missing


def source_files(root, suffix):
    """Walk maintained sources, excluding generated/private trees and links."""
    root = Path(root)
    for current, directories, files in os.walk(root, followlinks=False):
        directories[:] = sorted(name for name in directories
                                if name not in IGNORED_SOURCE_DIRS and
                                not (Path(current)/name).is_symlink())
        for name in sorted(files):
            path = Path(current)/name
            if path.suffix == suffix and path.is_file() and not path.is_symlink():
                yield path


def source_link_errors(root):
    """Resolve source Markdown with the same link syntax as generated copies."""
    missing = []
    for document in source_files(root, '.md'):
        for link in markdown_links(document.read_text(encoding='utf-8')):
            url = urlsplit(link)
            if url.scheme or url.netloc or not url.path:
                continue
            if not (document.parent / unquote(url.path)).exists():
                missing.append({'document': document.relative_to(root).as_posix(), 'link': link})
    return missing


def catalog_reference_errors(catalog, cases):
    """Check stable IDs before dictionary/set views can hide duplicates."""
    errors = []

    def unique_ids(entries, label):
        result = {}
        if not isinstance(entries, list):
            errors.append('Invalid ' + label + ' entries')
            return result
        for item in entries:
            if not isinstance(item, dict):
                errors.append('Invalid ' + label + ' entry')
                continue
            identifier = item.get('id')
            if not isinstance(identifier, str) or not identifier.strip():
                errors.append('Invalid ' + label + ' ID')
            elif identifier in result:
                errors.append('Repeated ' + label + ' ID: ' + identifier)
            else:
                result[identifier] = item
        return result

    def string_list(value, label):
        if (not isinstance(value, list) or
                any(not isinstance(item, str) or not item.strip() for item in value)):
            errors.append('Invalid ' + label + ' list')
            return []
        if len(set(value)) != len(value):
            errors.append('Repeated ' + label)
        return value

    methods = unique_ids(catalog['methods'], 'method')
    disciplines = unique_ids(catalog['disciplines'], 'discipline')
    unique_ids(catalog['skills'], 'skill')
    unique_ids(cases, 'scenario')
    for identifier, discipline in disciplines.items():
        suggested = string_list(discipline.get('suggested_methods', []), 'suggested methods: ' + identifier)
        if not set(suggested) <= methods.keys():
            errors.append('Unknown suggested method: ' + identifier)
    method_variants = {}
    for identifier, method in methods.items():
        variants = string_list(method.get('variants', []), 'method variants: ' + identifier)
        method_variants[identifier] = variants
        implementation = method.get('implementation', {})
        supported = string_list(implementation.get('supported_variants', []), 'supported variants: ' + identifier)
        if not set(supported) <= set(variants):
            errors.append('Unknown supported variant: ' + identifier)
    for case in cases:
        if not isinstance(case, dict):
            continue  # Already reported by unique_ids.
        identifier = str(case.get('id', '<missing>'))
        selected_disciplines = string_list(case.get('disciplines'), 'scenario disciplines: ' + identifier)
        selected_methods = string_list(case.get('methods'), 'scenario methods: ' + identifier)
        if not set(selected_disciplines) <= disciplines.keys() or not set(selected_methods) <= methods.keys():
            errors.append('Unknown scenario reference: ' + identifier)
            continue
        for owner, variants in case.get('method_variants', {}).items():
            variants = string_list(variants, 'scenario variants: ' + identifier)
            if owner not in selected_methods or not set(variants) <= set(method_variants[owner]):
                errors.append('Unknown scenario method variant: ' + identifier)
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--test-timeout', type=positive_seconds, default=180,
                        help='Maximum seconds for the complete unit/CLI suite (default: 180)')
    args = parser.parse_args(argv)
    checks = []
    def add(name, passed, detail):
        checks.append({'check': name, 'passed': bool(passed), 'detail': detail})
    with tempfile.TemporaryDirectory(prefix='rw-schema-check-') as temporary:
        generated = export_schemas(temporary)
        errors = []
        for path in generated:
            committed = ROOT / 'core/schemas' / path.name
            if not committed.is_file() or json.loads(path.read_text()) != json.loads(committed.read_text()):
                errors.append(path.name)
        extras = sorted({p.name for p in (ROOT / 'core/schemas').glob('*.json')} - {p.name for p in generated})
        add('schema-source-consistency', not errors and not extras,
            {'schemas': len(generated), 'different_or_missing': errors, 'unexpected': extras})
    catalog = json.loads((ROOT / 'design/catalog.json').read_text())
    cases = json.loads((ROOT / 'design/scenarios.json').read_text())['cases']
    errors = catalog_reference_errors(catalog, cases)
    add('design-reference-consistency', not errors,
        {'planned_scenarios': len(cases), 'invalid_references': errors,
         'scope': 'Design ID consistency only; task execution and content audit are checked separately in recorded evaluation regressions'})
    errors = []
    implemented = {item['id']: item for item in catalog['skills'] if item['status'] == 'implemented'}
    if set(implemented) != set(SKILLS):
        errors.append('Implemented catalog skills differ from the project bundle')
    for name, item in implemented.items():
        document = ROOT / item.get('entrypoint', '')
        if not document.is_file():
            errors.append('Missing skill entrypoint: ' + name)
            continue
        content = document.read_text(encoding='utf-8')
        try:
            fields = skill_metadata(content)
        except ValueError as exc:
            errors.append(str(exc) + ': ' + name)
            continue
        if fields.get('name') != name or not fields.get('description', '').strip():
            errors.append('Missing or mismatched skill metadata: ' + name)
    profiles = []
    for method in catalog['methods']:
        implementation = method.get('implementation', {})
        if implementation.get('status') == 'guidance-slice':
            profiles.append(method['id'])
            if (not (ROOT / implementation.get('profile', '')).is_file() or
                    not set(implementation.get('supported_variants', [])) <= set(method['variants'])):
                errors.append('Missing or inconsistent method profile: ' + method['id'])
    payload = build_payload()
    portraits = []
    for discipline in catalog['disciplines']:
        portraits.append(discipline['id'])
        if not (ROOT / discipline.get('profile', '')).is_file():
            errors.append('Missing discipline portrait: ' + discipline['id'])
    sources = json.loads((ROOT / 'profiles/sources.json').read_text(encoding='utf-8'))['sources']
    if len({item['id'] for item in sources}) != len(sources):
        errors.append('Repeated method source ID')
    for item in sources:
        if any(not item.get(field) for field in ('id','title','version','url','access','checked_scope','limits','accessed_on')):
            errors.append('Incomplete method source record: ' + str(item.get('id')))
    add('skill-and-method-connection-contract', not errors,
        {'implemented_skills': len(implemented), 'method_guidance_slices': len(profiles),
         'discipline_portraits': len(portraits), 'declared_method_sources': len(sources),
         'bundle_files': len(payload), 'errors': errors,
         'scope': 'Metadata, resources and generated connection contract; source declarations are not re-fetched and task success is separately tested'})
    syntax_errors = []
    python_files = list(source_files(ROOT, '.py'))
    for source in python_files:
        try:
            ast.parse(source.read_text(encoding='utf-8'), filename=source.relative_to(ROOT).as_posix(), feature_version=(3,11))
        except SyntaxError as exc:
            syntax_errors.append({'path':source.relative_to(ROOT).as_posix(),'error':str(exc)})
    add('minimum-python-syntax', not syntax_errors,
        {'target':'3.11','files_seen':len(python_files),'errors':syntax_errors,
         'scope':'Syntax only; actual interpreter and platform execution are separate evidence'})
    missing = source_link_errors(ROOT)
    add('local-document-links', not missing, missing)
    generated_missing = payload_link_errors(payload)
    add('installed-layout-document-links', not generated_missing, generated_missing)
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    timed_out = False
    try:
        result = subprocess.run([sys.executable, '-B', '-m', 'unittest', 'discover',
                                 '-s', str(ROOT / 'tests'), '-v'], cwd=ROOT,
                                env=environment, text=True, capture_output=True,
                                timeout=args.test_timeout)
        output, exit_code = result.stdout + result.stderr, result.returncode
    except subprocess.TimeoutExpired as exc:
        output = captured_text(exc.stdout) + captured_text(exc.stderr)
        exit_code, timed_out = None, True
    count = re.search(r'Ran (\d+) tests? in', output)
    add('actual-unit-and-cli-tests', not timed_out and exit_code == 0 and count is not None and int(count[1]) > 0,
        {'tests_run': int(count[1]) if count else 0, 'exit_code': exit_code,
         'timed_out': timed_out, 'timeout_seconds': args.test_timeout,
         'completion': 'Partial capture; suite did not finish.' if timed_out else 'Suite process completed.',
         'output': output[-16000:]})
    report = {'scope': 'Software, metadata, connection and recorded task regressions. Agent task execution and independent content review are separately recorded; no disciplinary certification or publication readiness.',
              'passed': all(check['passed'] for check in checks), 'checks': checks,
              'runtime': {'python': sys.version.split()[0], 'platform': sys.platform}}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
