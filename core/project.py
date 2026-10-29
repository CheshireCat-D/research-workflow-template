"""Registration, reference integrity and derived recovery state, never science certification."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import os
from pathlib import Path
import uuid

from .model import SCHEMA_VERSION, RECORD_KINDS, COLLECTIONS
from .model import validate_project, validate_registry, validate_record
from .storage import CoreError, ProjectFiles, json_bytes, object_sha, parse_json, sha, path_parts

REGISTRY = 'records/registry.json'
SCOPE = 'Local registration, references, fingerprints and workflow state only; no scientific, ethics, venue or submission certification.'


def now():
    return datetime.now(timezone.utc).isoformat()


def catalog():
    return parse_json((Path(__file__).resolve().parents[1] / 'design/catalog.json').read_bytes())


def require(errors):
    if errors:
        raise CoreError('invalid_registration', '; '.join(errors[:12]))


def require_record(kind, data):
    if isinstance(data, dict) and 'envelope' in data:
        raise CoreError('wrapped_record',
                        'register expects the record data, not a show response. '
                        'Export it with show --kind KIND --id ID --data-only; '
                        'read the current expected version from normal show: envelope.version.')
    require(validate_record(kind, data))


def envelope(registry, reference):
    try:
        kind, identifier = reference.split(':', 1)
        return registry['records'][COLLECTIONS[kind]][identifier]
    except (ValueError, KeyError, AttributeError) as exc:
        raise CoreError('missing_reference', 'Unknown typed reference: ' + str(reference)) from exc


def items(registry):
    for kind, collection in COLLECTIONS.items():
        for identifier, entry in registry['records'][collection].items():
            yield kind, identifier, entry


def references(kind, data, registry):
    if kind == 'statement':
        refs = ['statement:' + x for x in data.get('depends_on', [])]
        refs += ['relation:' + key for key, entry in registry['records']['relations'].items()
                 if entry['data']['statement_id'] == data['id']]
        return refs
    if kind == 'evidence':
        return ['source:' + x for x in data.get('source_ids', [])]
    if kind == 'relation':
        return ['statement:' + data['statement_id'], 'evidence:' + data['evidence_id']]
    if kind == 'activity':
        return (['activity:' + x for x in data.get('depends_on', [])] +
                data.get('inputs', []) + data.get('outputs', []))
    if kind == 'decision':
        return ['evidence:' + x for x in data.get('evidence_refs', [])]
    if kind == 'artifact':
        return data.get('derived_from', [])
    if kind == 'method-binding':
        return data['applies_to']
    return []


def local_path(kind, data):
    if kind == 'evidence' and data['location']['kind'] == 'local':
        return data['location']['path']
    if kind == 'artifact':
        return data['path']
    return None


def validate_links(project, registry, files=None):
    errors = []
    protected, state_directory = files.internal_identities() if files is not None else (set(), None)
    cat = catalog()
    for field, pool in [('disciplines', {x['id'] for x in cat['disciplines']}),
                        ('methods', {x['id'] for x in cat['methods']})]:
        if len(set(project[field])) != len(project[field]) or not set(project[field]) <= pool:
            errors.append('Unknown or repeated project ' + field)
    if project['entry_activity'] not in cat['activities'] or project['workflow_mode'] not in cat['workflow_modes']:
        errors.append('Unknown project entry activity or workflow mode')
    if project['project_id'] != registry['project_id']:
        errors.append('Project and registry identities differ')
    if registry['cursor']['activity_id'] is not None and registry['cursor']['activity_id'] not in registry['records']['activities']:
        errors.append('Cursor references an unknown activity')
    for kind, identifier, entry in items(registry):
        data = entry['data']
        if identifier != data['id']:
            errors.append('Map key differs from record ID: ' + kind + ':' + identifier)
        for ref in references(kind, data, registry):
            try:
                envelope(registry, ref)
            except CoreError as exc:
                errors.append(exc.message)
        path = local_path(kind, data)
        if path is not None:
            try:
                parts = path_parts(path)
                internal = path in ('project.json', REGISTRY) or path.startswith('.research/')
                if files is not None and not internal:
                    try:
                        internal = files.identity(path) in protected
                    except FileNotFoundError:
                        pass  # Missing research resources are reported by inspection.
                    if not internal and state_directory is not None and len(parts) > 1:
                        try:
                            internal = files.directory_identity(parts[0]) == state_directory
                        except FileNotFoundError:
                            pass
                if internal:
                    errors.append('Internal configuration/state cannot serve as its own research evidence: ' + path)
            except CoreError as exc:
                errors.append(exc.message)
        if kind == 'activity' and data['status'] in ('failed', 'skipped') and not data.get('note', '').strip():
            errors.append('Failed/skipped activity needs a reason: ' + identifier)
        if kind == 'method-binding':
            method = next((x for x in cat['methods'] if x['id'] == data['method_id']), None)
            if method is None or ('variant' in data and data['variant'] not in method['variants']):
                errors.append('Unknown method or method variant: ' + identifier)
            if not data['applies_to']:
                errors.append('Method binding needs a concrete scope: ' + identifier)
    for collection in ('statements', 'activities'):
        active, visited = set(), set()
        def visit(identifier):
            if identifier in active:
                raise CoreError('dependency_cycle', 'Dependency cycle in ' + collection)
            if identifier in visited or identifier not in registry['records'][collection]:
                return
            active.add(identifier)
            for dep in registry['records'][collection][identifier]['data'].get('depends_on', []):
                visit(dep)
            active.remove(identifier)
            visited.add(identifier)
        try:
            for identifier in registry['records'][collection]:
                visit(identifier)
        except (CoreError, RecursionError):
            errors.append('Cyclic or excessively deep dependencies in ' + collection)
    return errors


def load(files):
    try:
        project_raw, registry_raw = files.read('project.json'), files.read(REGISTRY)
    except FileNotFoundError as exc:
        raise CoreError('incomplete_project',
                        'Project needs project.json and records/registry.json. '
                        'Point --root at an initialized RWT project. For an existing materials folder, '
                        'create a separate new project and follow the existing-materials section in the user guide.') from exc
    project, registry = parse_json(project_raw), parse_json(registry_raw)
    require(validate_project(project) + validate_registry(registry))
    require(validate_links(project, registry, files))
    return project, registry, project_raw, registry_raw


def closure(files, registry, initial, *, exclude=()):
    records, fingerprints, seen = {}, {}, set(exclude)
    pending = list(initial)
    while pending:
        ref = pending.pop()
        if ref in seen:
            continue
        seen.add(ref)
        entry = envelope(registry, ref)
        kind = ref.split(':', 1)[0]
        records[ref] = object_sha({'data': entry['data'], 'version': entry['version']})
        path = local_path(kind, entry['data'])
        if path:
            fingerprints[path] = files.fingerprint(path)
        pending.extend(references(kind, entry['data'], registry))
    return {'records': records, 'files': fingerprints}


def activity_states(files, registry):
    result, computed = [], {}
    def state(identifier):
        if identifier in computed:
            return computed[identifier]
        entry = registry['records']['activities'][identifier]
        data = entry['data']
        effective, reasons = data['status'], []
        parents = [state(dep) for dep in data.get('depends_on', [])]
        if effective == 'done':
            if any(x['effective_status'] != 'done' for x in parents):
                reasons.append('A required activity is no longer done')
            try:
                current = closure(files, registry, references('activity', data, registry),
                                  exclude=('activity:' + identifier,))
                if entry['bindings'] is None or current != entry['bindings']:
                    reasons.append('Bound records or local files changed')
            except FileNotFoundError:
                reasons.append('A bound local file is missing')
            if reasons:
                effective = 'stale'
        computed[identifier] = {'id': identifier, 'title': data['title'], 'declared_status': data['status'],
                                'effective_status': effective, 'stale_reasons': reasons}
        return computed[identifier]
    for identifier in registry['records']['activities']:
        result.append(state(identifier))
    return result


def record_files(files, registry):
    values = {}
    for kind, _, entry in items(registry):
        path = local_path(kind, entry['data'])
        if path:
            values[path] = files.fingerprint(path)
    return values


def inspect(files):
    project, registry, project_raw, registry_raw = load(files)
    findings, warnings, file_values = [], [], {}
    for kind, identifier, entry in items(registry):
        path = local_path(kind, entry['data'])
        if path:
            try:
                value = files.fingerprint(path)
                file_values[path] = value
                expected = (entry['bindings'] or {}).get('files', {}).get(path)
                if value != expected:
                    findings.append({'code': 'file_changed', 'record': kind + ':' + identifier, 'path': path})
            except FileNotFoundError:
                file_values[path] = None
                findings.append({'code': 'file_missing', 'record': kind + ':' + identifier, 'path': path})
        elif kind == 'evidence':
            warnings.append({'code': 'evidence_not_inspected', 'record': kind + ':' + identifier,
                             'location_kind': entry['data']['location']['kind']})
    locally_bound_sources = {
        source_id
        for entry in registry['records']['evidence'].values()
        if entry['data']['location']['kind'] == 'local'
        for source_id in entry['data'].get('source_ids', [])
    }
    file_tracking = {
        'local_files': sorted(file_values),
        'local_file_count': len(file_values),
        'source_ids_without_local_evidence': sorted(set(registry['records']['sources']) - locally_bound_sources),
    }
    states = activity_states(files, registry)
    for state in states:
        if state['effective_status'] == 'stale':
            findings.append({'code': 'activity_stale', 'record': 'activity:' + state['id']})
    checkpoint = registry['checkpoint']
    changed = []
    if checkpoint is not None:
        if checkpoint['config_sha256'] != sha(project_raw):
            changed.append('project-config')
        if checkpoint['records_sha256'] != object_sha(registry['records']):
            changed.append('registered-records')
        if checkpoint['files'] != file_values:
            changed.append('local-files')
        if changed:
            findings.append({'code': 'checkpoint_stale', 'changed': changed})
    if files.read('project.json') != project_raw or files.read(REGISTRY) != registry_raw:
        raise CoreError('concurrent_change', 'Metadata changed during the read-only inspection; retry')
    return {
        'scope': SCOPE, 'schema_version': SCHEMA_VERSION, 'project_id': project['project_id'],
        'revision': registry['revision'], 'passed': not findings, 'read_only': True,
        'scientific_validity': 'not-assessed', 'governance_approval': 'not-assessed',
        'venue_compliance': 'not-assessed', 'errors': [], 'warnings': warnings,
        'findings': findings, 'counts': {k: len(v) for k, v in registry['records'].items()},
        'configuration': project, 'file_tracking': file_tracking,
        'activities': states, 'cursor': registry['cursor'],
        'checkpoint': {'recorded': checkpoint is not None,
                       'status': ('stale' if changed else 'current') if checkpoint else 'not-recorded',
                       'changed': changed},
    }


def initialize(output, title, *, interest=None, disciplines=(), methods=(), mode='light', language='zh', entry='question'):
    target = Path(output).absolute()
    exists_hint = ('Initialization requires a new project directory. '
                   'Resume an existing RWT project with resume --root PROJECT. '
                   'For a materials folder, choose a new sibling directory and follow '
                   'the existing-materials section in the user guide; existing files are not overwritten.')
    if target.name in ('', '.', '..') or os.path.lexists(target):
        raise CoreError('output_exists', exists_hint)
    if not target.parent.is_dir():
        raise CoreError('missing_parent', 'The output parent directory must already exist')
    project_id = 'P' + uuid.uuid4().hex
    project = {
        'schema_version': SCHEMA_VERSION, 'project_id': project_id, 'title': title,
        'interest': interest or title, 'disciplines': list(disciplines), 'methods': list(methods),
        'entry_activity': entry, 'workflow_mode': mode,
        'deliverable': {'kind': 'undecided', 'language': language, 'venue': None, 'contribution_benchmarks': []},
        'resources': {'deadline': None, 'budget': None, 'available_capabilities': []},
        'governance': {'applicability': 'unknown', 'relevant_requirements': []},
    }
    registry = {
        'schema_version': SCHEMA_VERSION, 'project_id': project_id, 'revision': 0,
        'records': {value: {} for value in COLLECTIONS.values()},
        'cursor': {'activity_id': None, 'next_action': 'Clarify the current question, scope and next evidence check.'},
        'checkpoint': None, 'history': [],
    }
    require(validate_project(project) + validate_registry(registry) + validate_links(project, registry))
    try:
        target.mkdir(mode=0o700)
    except FileExistsError as exc:
        raise CoreError('output_exists', exists_hint) from exc
    with ProjectFiles(target) as files:
        with files.lock():
            files.write('PROJECT.md', ('# ' + title + '\n\n' +
                        'This project has no validated results at initialization.\n\n' +
                        '## Question and scope\n\n' + project['interest'] + '\n\n' +
                        '## Research notes\n\nKeep authored reasoning here. JSON records and the recovery cursor are managed separately.\n').encode('utf-8'))
            files.write('.gitignore', b'.research/\nlocal-config/\nprivate-data/\n.DS_Store\n')
            files.write(REGISTRY, json_bytes(registry))
            files.write('project.json', json_bytes(project))
    return {'initialized': True, 'project_id': project_id, 'revision': 0,
            'scientific_validity': 'not-assessed', 'scope': SCOPE}


def _apply_registration(files, project, updated, kind, data, *, replace=False, expected_version=None):
    """Apply one sequential registration to a private candidate registry."""
    require_record(kind, data)
    if type(replace) is not bool or (expected_version is not None and
            (type(expected_version) is not int or expected_version < 1)):
        raise CoreError('version_conflict', 'replace must be boolean and expected_version must be a positive integer')
    collection = updated['records'][COLLECTIONS[kind]]
    identifier = data['id']
    previous = collection.get(identifier)
    if previous:
        if not replace or expected_version != previous['version']:
            raise CoreError('version_conflict',
                            'Existing ID needs --replace and its current --expected-version. '
                            'Read envelope.version with show --kind ' + kind + ' --id ' + identifier +
                            '; export editable record data with --data-only.')
    elif replace or expected_version is not None:
        raise CoreError('version_conflict', 'Cannot replace a record that does not exist')
    # Compute parent status before replacing the current activity. Each earlier
    # batch operation is already present, exactly as for sequential CLI calls.
    prior_states = ({x['id']: x for x in activity_states(files, updated)}
                    if kind == 'activity' and data['status'] == 'done' else {})
    entry = {'version': previous['version'] + 1 if previous else 1,
             'registered_at': now(), 'data': deepcopy(data), 'bindings': None}
    collection[identifier] = entry
    require(validate_registry(updated) + validate_links(project, updated, files))
    path = local_path(kind, data)
    if path:
        try:
            entry['bindings'] = {'records': {}, 'files': {path: files.fingerprint(path)}}
        except FileNotFoundError as exc:
            raise CoreError('file_missing', 'Cannot register a missing local resource: ' + path) from exc
    if kind == 'activity' and data['status'] == 'done':
        if any(prior_states[x]['effective_status'] != 'done' for x in data.get('depends_on', [])):
            raise CoreError('incomplete_dependency', 'Required activities must be effectively done')
        try:
            entry['bindings'] = closure(files, updated, references(kind, data, updated),
                                        exclude=('activity:' + identifier,))
        except FileNotFoundError as exc:
            raise CoreError('file_missing', 'A bound local resource is missing') from exc
    updated['revision'] += 1
    updated['history'].append({'revision': updated['revision'], 'at': now(),
                               'action': 'replace' if previous else 'register', 'kind': kind,
                               'id': identifier, 'previous': previous})
    require(validate_registry(updated))
    return {'registered': True, 'kind': kind, 'id': identifier, 'version': entry['version'],
            'revision': updated['revision'], 'scientific_validity': 'not-assessed', 'scope': SCOPE}


def register(root, kind, data, *, replace=False, expected_version=None):
    require_record(kind, data)
    with ProjectFiles(root) as files, files.lock():
        project, registry, _, _ = load(files)
        updated = deepcopy(registry)
        result = _apply_registration(files, project, updated, kind, data, replace=replace,
                                     expected_version=expected_version)
        files.write(REGISTRY, json_bytes(updated))
        return result


def register_batch(root, operations):
    """Commit an ordered batch through one writer lock and one registry replace."""
    if not isinstance(operations, list) or not operations:
        raise CoreError('invalid_batch', 'A batch must be a nonempty JSON array')
    for operation in operations:
        if (not isinstance(operation, dict) or not {'kind', 'record'} <= operation.keys()
                or set(operation) - {'kind', 'record', 'replace', 'expected_version'}):
            raise CoreError('invalid_batch', 'Each batch item needs kind and record, with optional replace and expected_version')
        if not isinstance(operation['kind'], str) or operation['kind'] not in RECORD_KINDS:
            raise CoreError('invalid_batch', 'Unknown batch record kind')
        require_record(operation['kind'], operation['record'])
    with ProjectFiles(root) as files:
        load(files)  # Invalid projects must not gain a new writer lock.
        with files.lock():
            project, registry, _, _ = load(files)
            updated, results = deepcopy(registry), []
            for operation in operations:
                results.append(_apply_registration(
                    files, project, updated, operation['kind'], operation['record'],
                    replace=operation.get('replace', False),
                    expected_version=operation.get('expected_version')))
            files.write(REGISTRY, json_bytes(updated))
            return {'registered': True, 'registered_count': len(results), 'records': results,
                    'revision': updated['revision'], 'scientific_validity': 'not-assessed', 'scope': SCOPE}


def show(root, *, kind=None, identifier=None, data_only=False):
    """Read registered envelopes or version summaries, without taking a writer lock."""
    if identifier is not None and kind is None:
        raise CoreError('arguments', '--id requires --kind')
    if kind is not None and kind not in RECORD_KINDS:
        raise CoreError('arguments', 'Unknown record kind')
    if data_only and (kind is None or identifier is None):
        raise CoreError('arguments', '--data-only requires --kind and --id')
    with ProjectFiles(root) as files:
        project, registry, project_raw, registry_raw = load(files)
        result = {'passed': True, 'read_only': True, 'scope': SCOPE,
                  'scientific_validity': 'not-assessed', 'project_id': project['project_id'],
                  'revision': registry['revision']}
        if identifier is not None:
            result.update(kind=kind, id=identifier,
                          envelope=deepcopy(envelope(registry, kind + ':' + identifier)))
        else:
            def summary(record_kind):
                return [{'id': key, 'version': entry['version']} for key, entry in
                        sorted(registry['records'][COLLECTIONS[record_kind]].items())]
            if kind is not None:
                result.update(kind=kind, records=summary(kind))
            else:
                result['records'] = {record_kind: summary(record_kind) for record_kind in RECORD_KINDS}
        if files.read('project.json') != project_raw or files.read(REGISTRY) != registry_raw:
            raise CoreError('concurrent_change', 'Metadata changed during the read-only query; retry')
        return result['envelope']['data'] if data_only else result


def configure(root, *, add_disciplines=(), add_methods=(), mode=None, venue=None,
              interest=None, deadline=None, budget=None, add_capabilities=(),
              governance_applicability=None, add_governance_requirements=()):
    """Update supported configuration fields through one atomic project write.

    Registry revisions track registry mutations, not configuration writes. An
    existing checkpoint's config digest therefore becomes stale naturally.
    """
    add_disciplines, add_methods = tuple(add_disciplines), tuple(add_methods)
    add_capabilities = tuple(add_capabilities)
    add_governance_requirements = tuple(add_governance_requirements)
    def candidate(project, registry, files):
        updated = deepcopy(project)
        for field, values in (('disciplines', add_disciplines), ('methods', add_methods)):
            for value in values:
                if value not in updated[field]:
                    updated[field].append(value)
        if mode is not None:
            updated['workflow_mode'] = mode
        if venue is not None:
            updated['deliverable']['venue'] = venue
        if interest is not None:
            updated['interest'] = interest
        for field, value in (('deadline', deadline), ('budget', budget)):
            if value is not None:
                updated['resources'][field] = value
        for capability in add_capabilities:
            if capability not in updated['resources']['available_capabilities']:
                updated['resources']['available_capabilities'].append(capability)
        if governance_applicability is not None:
            updated['governance']['applicability'] = governance_applicability
        for value in add_governance_requirements:
            if value not in updated['governance']['relevant_requirements']:
                updated['governance']['relevant_requirements'].append(value)
        require(validate_project(updated))
        require(validate_links(updated, registry, files))
        return updated
    def result(updated, registry, data, changed):
        return {'passed': True, 'configured': changed, 'configuration': updated,
                'config_sha256': sha(data), 'registry_revision': registry['revision'],
                'scientific_validity': 'not-assessed', 'governance_approval': 'not-assessed',
                'venue_compliance': 'not-assessed', 'scope': SCOPE}
    with ProjectFiles(root) as files:
        project, registry, project_raw, registry_raw = load(files)
        updated = candidate(project, registry, files)
        if updated == project:
            # An explicit no-op query needs no writer lock or lock repair.
            if files.read('project.json') != project_raw or files.read(REGISTRY) != registry_raw:
                raise CoreError('concurrent_change', 'Metadata changed during the configuration query; retry')
            return result(updated, registry, project_raw, False)
        with files.lock():
            project, registry, project_raw, _ = load(files)
            updated = candidate(project, registry, files)
            changed = updated != project
            new_bytes = json_bytes(updated) if changed else project_raw
            if changed:
                files.write('project.json', new_bytes)
            return result(updated, registry, new_bytes, changed)


def checkpoint(root, next_action, *, activity=None, note=None):
    if not next_action.strip():
        raise CoreError('empty_next_action', 'A concrete next action is required')
    with ProjectFiles(root) as files, files.lock():
        project, registry, project_raw, _ = load(files)
        if activity is not None and activity not in registry['records']['activities']:
            raise CoreError('missing_reference', 'Unknown checkpoint activity')
        updated = deepcopy(registry)
        updated['cursor'] = {'activity_id': activity, 'next_action': next_action}
        try:
            fingerprints = record_files(files, updated)
        except FileNotFoundError as exc:
            raise CoreError('file_missing', 'Cannot checkpoint a missing local resource') from exc
        updated['checkpoint'] = {'created_at': now(), 'config_sha256': sha(project_raw),
                                 'records_sha256': object_sha(updated['records']),
                                 'files': fingerprints, 'note': note or 'Recovery checkpoint; not scientific certification.'}
        updated['revision'] += 1
        updated['history'].append({'revision': updated['revision'], 'at': now(), 'action': 'checkpoint',
                                   'kind': None, 'id': None, 'previous': None})
        require(validate_registry(updated))
        files.write(REGISTRY, json_bytes(updated))
        return {'checkpoint_saved': True, 'revision': updated['revision'],
                'cursor': updated['cursor'], 'scientific_validity': 'not-assessed', 'scope': SCOPE}
