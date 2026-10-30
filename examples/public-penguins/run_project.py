#!/usr/bin/env python3
"""Build one NEW, recoverable penguin-analysis project; Python 3.11+, stdlib only.

By default the existing fetcher downloads only the input pinned in source.json.
--input copies a local CSV without network access; its identity is checked before
calling it the pinned public dataset. Registration does not assess scientific validity.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys


EXAMPLE = Path(__file__).resolve().parent
TOOLKIT = EXAMPLE.parents[1]
NEXT_ACTION = ('Read results/results.md and both SVGs; check the original individual/nest '
               'identities and sampling design before choosing any inferential model.')


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def identity(path):
    data = path.read_bytes()
    return {'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}


def write_json(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as handle:
        json.dump(value, handle, ensure_ascii=False, allow_nan=False, indent=2)
        handle.write('\n')


def snapshot(root):
    return {p.relative_to(root).as_posix(): (identity(p), p.stat().st_mtime_ns)
            for p in root.rglob('*') if p.is_file()}


class CommandFailure(ValueError):
    """Retain structured CLI error codes without matching diagnostic prose."""
    def __init__(self, message, codes=()):
        super().__init__(message)
        self.codes = frozenset(codes)


class ProjectRun:
    def __init__(self, project):
        self.project = project
        self.stage = 'preflight'
        self.created = False
        self.initialized = False
        self.observed_partial_path = None
        self.receipt = {'format_version': 1, 'status': 'in-progress',
                        'started_at_utc': timestamp(), 'project': str(project),
                        'scientific_validity': 'not-assessed', 'commands': []}

    def command(self, script, *arguments):
        argv = [sys.executable, '-X', 'utf8', '-I', '-B', str(script), *map(str, arguments)]
        row = {'stage': self.stage, 'argv': argv, 'cwd': str(self.project.parent),
               'script_identity': identity(script), 'started_at_utc': timestamp()}
        self.receipt['commands'].append(row)
        try:
            result = subprocess.run(argv, cwd=self.project.parent, capture_output=True,
                                    text=True, encoding='utf-8', timeout=90)
        except subprocess.TimeoutExpired as exc:
            row.update({'ended_at_utc': timestamp(), 'timed_out': True,
                        'stdout': str(exc.stdout or ''), 'stderr': str(exc.stderr or '')})
            raise ValueError('Command exceeded its 90-second wall timeout') from exc
        row.update({'ended_at_utc': timestamp(), 'exit_code': result.returncode,
                    'stdout': result.stdout, 'stderr': result.stderr})
        if result.returncode:
            try:
                failure = json.loads(result.stdout)
            except ValueError:
                failure = None
            errors = failure.get('errors') if isinstance(failure, dict) else None
            codes = [error['code'] for error in errors
                     if isinstance(error, dict) and isinstance(error.get('code'), str)] \
                if isinstance(errors, list) else []
            raise CommandFailure(f'Command exited {result.returncode}: '
                                 f'{result.stderr.strip() or result.stdout.strip()}', codes)
        try:
            payload = json.loads(result.stdout)
        except ValueError as exc:
            raise ValueError('Command did not return the expected JSON receipt') from exc
        if not isinstance(payload, dict) or payload.get('passed') is False:
            raise ValueError('Command receipt does not report successful execution')
        return payload

    def save_receipt(self):
        path = self.project / 'notes/run-receipt.json'
        if self.initialized and path.parent.is_dir():
            write_json(path, self.receipt)
            return str(path)
        return None


def records(project, summary, input_record):
    """Describe actual files and computations, leaving content assessments unset."""
    pinned = input_record['matches_pinned_public_input']
    label = 'Pinned public palmerpenguins CSV' if pinned else 'User-supplied / test CSV'
    scope = ('Descriptive comparisons within this supplied CSV; no causal, population '
             'inference, independent review or scientific-validity certification.')
    source = {'id': 'SRC_DATA', 'title': label,
              'locator': input_record['pinned_source']['url'] if pinned else 'data/penguins.csv',
              'version': input_record['observed']['sha256'], 'content_access': 'full',
              'rights': 'public' if pinned else 'unknown', 'limitations': scope,
              'notes': ('Data license CC0-1.0; source.json identifies the pinned upstream commit.'
                        if pinned else 'Does not match the pinned public input; supplied rights are not inferred.')}
    evidence = {'id': 'E_DATA', 'type': 'public-observational-data' if pinned else 'user-supplied-data',
                'description': label, 'provenance': input_record['acquisition'],
                'source_ids': ['SRC_DATA'], 'location': {'kind': 'local', 'path': 'data/penguins.csv'},
                'limitations': scope}
    question = {'id': 'Q_MASS', 'type': 'question', 'work_status': 'draft',
                'text': 'Within each species, how large is mean male minus mean female body mass, '
                        'and how does it vary across island-year strata?', 'scope': scope}
    method = {'id': 'M_DESCRIPTIVE', 'type': 'design', 'work_status': 'draft',
              'text': 'Use available sex/mass records within species, report missing denominators, '
                      'all 27 island-year cells, common-stratum weights and missing-sex assignment bounds; '
                      'do not compute p values or population confidence intervals.', 'scope': scope}
    comparisons = '; '.join(f"{row['species']}: {row['male_minus_female_g']!r} g"
                            for row in summary['species'])
    result = {'id': 'R_MASS', 'type': 'empirical', 'work_status': 'draft',
              'text': f"Computed {summary['n_complete_overall']} complete sex/mass records of "
                      f"{summary['n_raw']} input rows. Male-minus-female means: {comparisons}. "
                      'None denotes an unavailable comparison.',
              'scope': label + '. ' + scope, 'depends_on': ['Q_MASS', 'M_DESCRIPTIVE']}
    result_evidence = {'id': 'E_SUMMARY', 'type': 'computed-descriptive-summary',
                       'description': 'Actual analyzer output; input hash checked against the saved CSV.',
                       'provenance': 'code/analyze.py; command and environment identities in notes/execution.json '
                                     'and notes/environment.json.',
                       'source_ids': ['SRC_DATA'],
                       'location': {'kind': 'local', 'path': 'results/summary.json'}, 'limitations': scope}
    batch = [{'kind': kind, 'record': record} for kind, record in
             [('source', source), ('evidence', evidence), ('statement', question),
              ('statement', method), ('statement', result), ('evidence', result_evidence)]]
    paths = ['notes/question-method.md', 'notes/input-identity.json', 'notes/environment.json',
             'notes/execution.json', 'code/analyze.py', 'code/fetch_data.py', 'code/source.json',
             'data/source.json']
    paths += ['results/' + path.name for path in sorted((project / 'results').iterdir()) if path.is_file()]
    artifact_ids = []
    for index, path in enumerate(paths, 1):
        identifier = f'F{index:02d}'
        artifact_ids.append('artifact:' + identifier)
        batch.append({'kind': 'artifact', 'record': {
            'id': identifier, 'type': 'analysis-output' if path.startswith('results/') else 'reproduction-input',
            'description': path, 'path': path,
            'derived_from': ['evidence:E_DATA'] if path.startswith('results/') else [],
            'notes': 'Saved local file identity; neither registration nor a completed activity is content review.'}})
    batch += [{'kind': 'relation', 'record': {
        'id': 'REL_COMPUTED', 'statement_id': 'R_MASS', 'evidence_id': 'E_SUMMARY',
        'relation': 'derived_from', 'rationale': 'Descriptive values produced from the saved CSV.', 'scope': scope}},
        {'kind': 'activity', 'record': {
            'id': 'A_ANALYZE', 'title': 'Compute and save this descriptive analysis', 'status': 'done',
            'inputs': ['evidence:E_DATA', 'statement:Q_MASS', 'statement:M_DESCRIPTIVE'],
            'outputs': artifact_ids + ['evidence:E_SUMMARY', 'statement:R_MASS'],
            'note': 'Execution completed; scientific review and visual inspection are not recorded as completed.'}},
        {'kind': 'activity', 'record': {
            'id': 'A_REVIEW', 'title': 'Review output and original sampling identities', 'status': 'pending',
            'depends_on': ['A_ANALYZE'], 'inputs': ['evidence:E_DATA', 'evidence:E_SUMMARY'],
            'outputs': [], 'note': NEXT_ACTION}}]
    return batch


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path, help='new project; parent directory must exist')
    parser.add_argument('--input', type=Path, help='existing local CSV; disables downloading')
    args = parser.parse_args(argv)
    project = args.output.expanduser().absolute()
    run = ProjectRun(project)
    try:
        if project.exists() or project.is_symlink():
            raise ValueError('Output must be a new path; existing files, directories and symlinks are refused')
        if not project.parent.is_dir():
            raise ValueError('Output parent directory must already exist')
        helpers = [EXAMPLE / name for name in ('analyze.py', 'fetch_data.py', 'source.json', 'question-method.md')]
        cli, connector = TOOLKIT / 'tools/research.py', TOOLKIT / 'tools/connect_skills.py'
        for path in helpers + [cli, connector]:
            if not path.is_file():
                raise ValueError(f'Required toolkit file is missing: {path}')
        pinned = json.loads((EXAMPLE / 'source.json').read_text(encoding='utf-8'))
        supplied = args.input.expanduser().resolve(strict=True) if args.input else None
        original_identity = identity(supplied) if supplied is not None else None
        run.stage = 'initialize-project'
        try:
            initialized = run.command(
                cli, 'init', '--output', project, '--title', 'Penguin mass: descriptive secondary analysis',
                '--interest', 'Compare mass by sex within species and island-year strata.',
                '--discipline', 'agriculture-life', '--method', 'empirical-quantitative', '--mode', 'reproducible')
            if initialized.get('initialized') is not True:
                raise ValueError('Initialization did not confirm creation of a new project')
        except (OSError, ValueError, KeyError, TypeError) as exc:
            refused = isinstance(exc, CommandFailure) and 'output_exists' in exc.codes
            if not refused and project.is_dir() and not project.is_symlink():
                # A failed initialization can leave a partial path, but its
                # ownership is unconfirmed. Report it without writing inside.
                run.observed_partial_path = str(project)
            raise
        run.created = run.initialized = True
        (project / 'notes').mkdir(exist_ok=True)
        run.stage = 'install-project-skills'
        run.command(connector, 'install', '--root', project)
        local = project / '.agents/skills/_rw-runtime/tools'
        run.stage = 'save-project-code'
        (project / 'code').mkdir()
        for path in helpers[:3]:
            shutil.copyfile(path, project / 'code' / path.name)
        run.stage = 'acquire-input'
        if supplied is None:
            run.command(project / 'code/fetch_data.py', '--output', project / 'data')
            acquisition = 'Downloaded by the bundled fetcher from the single pinned source.json URL.'
        else:
            (project / 'data').mkdir()
            shutil.copyfile(supplied, project / 'data/penguins.csv')
            shutil.copyfile(EXAMPLE / 'source.json', project / 'data/source.json')
            if identity(project / 'data/penguins.csv') != original_identity:
                raise ValueError('Local input changed during copying')
            acquisition = f'Copied without network from the user-supplied file: {supplied}'
        observed = identity(project / 'data/penguins.csv')
        matches = observed['sha256'] == pinned['sha256'] and observed['bytes'] == pinned['bytes']
        if supplied is None and not matches:
            raise ValueError('Downloaded input does not match the pinned public source')
        input_record = {'observed': observed, 'matches_pinned_public_input': matches,
                        'input_kind': 'pinned-public-observations' if matches else 'user-supplied-or-test',
                        'acquisition': acquisition, 'pinned_source': pinned,
                        'original_local_path': str(supplied) if supplied else None}
        write_json(project / 'notes/input-identity.json', input_record)
        run.receipt['input'] = input_record
        run.stage = 'save-question-and-environment'
        prefix = ('本次输入匹配固定公开 CSV。\n\n' if matches else
                  '本次输入不匹配固定公开 CSV，按自备/测试输入解释；以下方案只作为分析模板。\n\n')
        (project / 'notes/question-method.md').write_text(
            prefix + (EXAMPLE / 'question-method.md').read_text(encoding='utf-8'), encoding='utf-8')
        environment = {'python_executable': sys.executable, 'python_version': sys.version,
                       'platform': platform.platform(), 'implementation': platform.python_implementation(),
                       'invocation': [sys.executable, str(Path(__file__).resolve()),
                                      *list(argv if argv is not None else sys.argv[1:])],
                       'invocation_cwd': str(Path.cwd()), 'runner_identity': identity(Path(__file__)),
                       'copied_resources': {p.name: identity(p) for p in (project / 'code').iterdir()},
                       'project_runtime_manifest': identity(local.parent / 'bundle-manifest.json'),
                       'analysis_replay': [sys.executable, '-X', 'utf8', '-I', '-B', 'code/analyze.py',
                                           '--input', 'data/penguins.csv', '--output', 'new-analysis-output'],
                       'scientific_validity': 'not-assessed'}
        write_json(project / 'notes/environment.json', environment)
        run.stage = 'analyze-input'
        run.command(project / 'code/analyze.py', '--input', project / 'data/penguins.csv',
                    '--output', project / 'results')
        summary = json.loads((project / 'results/summary.json').read_text(encoding='utf-8'))
        if (summary['input_sha256'] != observed['sha256'] or
                summary['matches_pinned_public_input'] != matches or
                identity(project / 'data/penguins.csv') != observed):
            raise ValueError('Analysis/input identity mismatch')
        if supplied is not None and identity(supplied) != original_identity:
            raise ValueError('Original local input changed during the run')
        # Freeze execution evidence before registration/checkpoint. The final operational
        # receipt remains separate so writing it cannot stale a tracked checkpoint.
        write_json(project / 'notes/execution.json', {
            'scope': 'Actual commands through analysis; later registration and read-only verification in run-receipt.json.',
            'commands': list(run.receipt['commands']), 'scientific_validity': 'not-assessed'})
        run.stage = 'register-records'
        batch = project / 'notes/registration-batch.json'
        write_json(batch, records(project, summary, input_record))
        registration = run.command(local / 'research.py', 'register-batch', '--root', project, '--file', batch)
        if not registration.get('registered'):
            raise ValueError('Registration receipt lacks registered=true')
        run.stage = 'checkpoint'
        run.command(local / 'research.py', 'checkpoint', '--root', project, '--activity', 'A_ANALYZE',
                    '--next-action', NEXT_ACTION)
        run.stage = 'verify-installed-skills'
        run.command(local / 'connect_skills.py', 'check', '--installed-only', '--root', project)
        run.stage = 'verify-readonly-resume'
        before = snapshot(project)
        resumed = run.command(local / 'research.py', 'resume', '--root', project)
        if (not resumed.get('passed') or resumed.get('needs_review') or
                resumed['checkpoint']['status'] != 'current' or resumed['next_action'] != NEXT_ACTION):
            raise ValueError('Saved project did not resume with a current checkpoint and expected next action')
        if snapshot(project) != before:
            raise ValueError('Read-only resume changed project files')
        run.receipt.update({'status': 'completed', 'completed_at_utc': timestamp(),
                            'registration_count': registration['registered_count'],
                            'checkpoint_status': resumed['checkpoint']['status'],
                            'resume_readonly_bytes_and_mtime_unchanged': True,
                            'final_receipt_tracking': 'Operational receipt is unregistered; execution.json is the frozen tracked evidence.'})
        run.stage = 'save-final-receipt'
        receipt = run.save_receipt()
        print(json.dumps({'passed': True, 'project': str(project), 'input_kind': input_record['input_kind'],
                          'matches_pinned_public_input': matches, 'scientific_validity': 'not-assessed',
                          'first_deliverable': str(project / 'results/results.md'),
                          'figures': [str(project / 'results' / name) for name in
                                      ('species-mass.svg', 'stratum-differences.svg')],
                          'checkpoint_status': 'current', 'receipt': receipt,
                          'resume_command': [sys.executable, '-X', 'utf8', '-I', '-B',
                                             str(local / 'research.py'), 'resume', '--root', str(project)]},
                         ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        run.receipt.update({'status': 'failed', 'failed_stage': run.stage,
                            'ended_at_utc': timestamp(), 'error': str(exc)})
        try:
            receipt = run.save_receipt()
        except OSError:
            receipt = None
        print(json.dumps({'passed': False, 'stage': run.stage, 'message': str(exc),
                          'project_created': run.created, 'project_initialized': run.initialized,
                          'project_ownership_confirmed': run.initialized,
                          'observed_partial_path': run.observed_partial_path,
                          'recovery_path': str(project) if run.created else run.observed_partial_path,
                          'receipt': receipt, 'scientific_validity': 'not-assessed',
                          'recovery': 'Inspect the reported stage and saved partial files. Existing outputs are never '
                                      'overwritten; reuse any saved input with --input and a new --output path.'},
                         ensure_ascii=False, indent=2), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
