"""Offline end-to-end project journeys; synthetic inputs never stand in for real data."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import contextlib
import io


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / 'examples/public-penguins'
RUNNER = EXAMPLE / 'run_project.py'
FIXTURE = EXAMPLE / 'synthetic.csv'


def snapshot(root):
    return {p.relative_to(root).as_posix():
            (hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_mtime_ns)
            for p in root.rglob('*') if p.is_file()}


class PenguinProjectTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='rwt penguin project ')
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.cwd = self.base / 'unrelated 工作目录'
        self.cwd.mkdir()
        self.project = self.base / 'new penguin 项目'

    def invoke(self, *arguments, expected=0, script=RUNNER):
        result = subprocess.run([sys.executable, '-X', 'utf8', '-I', '-B', str(script),
                                 *map(str, arguments)], cwd=self.cwd, capture_output=True,
                                text=True, encoding='utf-8', timeout=90)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        if expected == 0:
            self.assertEqual(result.stderr, '')
        else:
            self.assertEqual(result.stdout, '')
        return json.loads(result.stdout if expected == 0 else result.stderr)

    def run_fixture(self):
        return self.invoke('--input', FIXTURE, '--output', self.project)

    def load(self, relative):
        return json.loads((self.project / relative).read_text(encoding='utf-8'))

    def test_offline_project_saves_actual_outputs_records_and_current_readonly_recovery(self):
        before = (FIXTURE.read_bytes(), FIXTURE.stat().st_mtime_ns)
        result = self.run_fixture()
        self.assertEqual((FIXTURE.read_bytes(), FIXTURE.stat().st_mtime_ns), before)
        self.assertTrue(result['passed'])
        self.assertEqual(result['scientific_validity'], 'not-assessed')
        self.assertFalse(result['matches_pinned_public_input'])
        self.assertEqual(result['input_kind'], 'user-supplied-or-test')
        summary = self.load('results/summary.json')
        self.assertEqual((summary['n_raw'], summary['n_complete_overall']), (12, 9))
        self.assertAlmostEqual(summary['species'][0]['male_minus_female_g'], 1400 / 3)
        observed_sha = hashlib.sha256(FIXTURE.read_bytes()).hexdigest()
        self.assertEqual(self.load('notes/input-identity.json')['observed']['sha256'], observed_sha)
        self.assertIn('自备/测试数据', (self.project / 'results/results.md').read_text(encoding='utf-8'))
        self.assertIn('不匹配固定公开', (self.project / 'notes/question-method.md').read_text(encoding='utf-8'))
        for path in result['figures'] + [result['first_deliverable']]:
            self.assertTrue(Path(path).is_file())
        for name in ('analyze.py', 'fetch_data.py', 'source.json'):
            self.assertEqual((self.project / 'code' / name).read_bytes(), (EXAMPLE / name).read_bytes())
        environment = self.load('notes/environment.json')
        self.assertEqual(environment['python_executable'], sys.executable)
        self.assertEqual(Path(environment['invocation_cwd']).resolve(), self.cwd.resolve())
        self.assertEqual(environment['copied_resources']['analyze.py']['sha256'],
                         hashlib.sha256((EXAMPLE / 'analyze.py').read_bytes()).hexdigest())
        receipt = self.load('notes/run-receipt.json')
        self.assertEqual(receipt['status'], 'completed')
        self.assertTrue(receipt['resume_readonly_bytes_and_mtime_unchanged'])
        self.assertNotIn('acquire-input', [row['stage'] for row in receipt['commands']])
        self.assertEqual(receipt['commands'][-1]['stage'], 'verify-readonly-resume')
        for command in receipt['commands']:
            self.assertEqual(command['exit_code'], 0)
            self.assertEqual(len(command['script_identity']['sha256']), 64)
        batch = self.load('notes/registration-batch.json')
        self.assertTrue({'source', 'evidence', 'statement', 'relation', 'artifact', 'activity'} <=
                        {row['kind'] for row in batch})
        statements = [row['record'] for row in batch if row['kind'] == 'statement']
        self.assertTrue(all('assessment' not in row and row['work_status'] == 'draft' for row in statements))
        source = next(row['record'] for row in batch if row['kind'] == 'source')
        self.assertEqual(source['rights'], 'unknown')
        saved = snapshot(self.project)
        resumed = self.invoke('resume', '--root', self.project,
                              script=self.project / '.agents/skills/_rw-runtime/tools/research.py')
        self.assertEqual(snapshot(self.project), saved)
        self.assertEqual(resumed['checkpoint']['status'], 'current')
        self.assertFalse(resumed['needs_review'])
        self.assertEqual(resumed['scientific_validity'], 'not-assessed')
        for path in ('data/penguins.csv', 'notes/question-method.md', 'results/results.md',
                     'results/summary.json', 'code/analyze.py', 'notes/environment.json'):
            self.assertIn(path, resumed['file_tracking']['local_files'])
        self.assertEqual(resumed['file_tracking']['source_ids_without_local_evidence'], [])

    def test_moved_project_recovers_with_only_its_local_runtime_and_detects_changed_input(self):
        self.run_fixture()
        moved = self.base / 'moved 完整项目'
        self.project.rename(moved)
        cli = moved / '.agents/skills/_rw-runtime/tools/research.py'
        before = snapshot(moved)
        resumed = self.invoke('resume', '--root', moved, script=cli)
        self.assertEqual(snapshot(moved), before)
        self.assertTrue(resumed['passed'])
        self.assertEqual(resumed['checkpoint']['status'], 'current')
        csv = moved / 'data/penguins.csv'
        csv.write_bytes(csv.read_bytes().replace(b'1000', b'1100', 1))
        result = subprocess.run([sys.executable, '-X', 'utf8', '-I', '-B', str(cli),
                                 'resume', '--root', str(moved)], cwd=self.cwd,
                                capture_output=True, text=True, encoding='utf-8', timeout=30)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        stale = json.loads(result.stdout)
        self.assertTrue(stale['needs_review'])
        self.assertIn('file_changed', {row['code'] for row in stale['findings']})

    def test_existing_output_is_refused_without_touching_its_contents(self):
        self.project.mkdir()
        (self.project / 'retain.txt').write_text('Keep original bytes.', encoding='utf-8')
        before = snapshot(self.project)
        result = self.invoke('--output', self.project, '--input', FIXTURE, expected=2)
        self.assertEqual(result['stage'], 'preflight')
        self.assertFalse(result['project_created'])
        self.assertIsNone(result['recovery_path'])
        self.assertEqual(snapshot(self.project), before)

    def test_invalid_csv_reports_failed_stage_and_keeps_partial_project_for_recovery(self):
        invalid = self.base / 'bad.csv'
        invalid.write_text('not,the,required,columns\n1,2,3,4\n', encoding='utf-8')
        original = invalid.read_bytes()
        result = self.invoke('--output', self.project, '--input', invalid, expected=2)
        self.assertEqual(result['stage'], 'analyze-input')
        self.assertTrue(result['project_created'])
        self.assertEqual(result['recovery_path'], str(self.project))
        self.assertEqual(invalid.read_bytes(), original)
        self.assertEqual((self.project / 'data/penguins.csv').read_bytes(), original)
        self.assertFalse((self.project / 'results').exists())
        receipt = self.load('notes/run-receipt.json')
        self.assertEqual(receipt['failed_stage'], 'analyze-input')
        self.assertEqual(receipt['commands'][-1]['exit_code'], 2)
        self.assertNotIn('checkpoint', [row['stage'] for row in receipt['commands']])

    def test_missing_input_or_parent_is_rejected_before_project_creation(self):
        missing = self.base / 'missing.csv'
        failure = self.invoke('--input', missing, '--output', self.project, expected=2)
        self.assertEqual(failure['stage'], 'preflight')
        self.assertFalse(self.project.exists())
        failure = self.invoke('--input', FIXTURE, '--output', self.base / 'missing-parent/project', expected=2)
        self.assertFalse(failure['project_created'])
        self.assertFalse((self.base / 'missing-parent').exists())

    def test_default_acquisition_calls_only_fixed_fetcher_and_preserves_failure_receipt(self):
        # Stub only this integration's command boundary: no request leaves this test.
        spec = importlib.util.spec_from_file_location('penguin_project_runner', RUNNER)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        actual = module.ProjectRun.command

        def commands(run, script, *arguments):
            if run.stage == 'acquire-input':
                self.assertEqual(script, self.project / 'code/fetch_data.py')
                self.assertEqual(arguments, ('--output', self.project / 'data'))
                self.assertEqual((script.parent / 'source.json').read_bytes(),
                                 (EXAMPLE / 'source.json').read_bytes())
                raise ValueError('Injected offline download failure; no network attempted')
            return actual(run, script, *arguments)

        output, error = io.StringIO(), io.StringIO()
        with mock.patch.object(module.ProjectRun, 'command', commands), \
                contextlib.redirect_stdout(output), contextlib.redirect_stderr(error):
            status = module.main(['--output', str(self.project)])
        self.assertEqual(status, 2)
        self.assertEqual(output.getvalue(), '')
        failure = json.loads(error.getvalue())
        self.assertEqual(failure['stage'], 'acquire-input')
        self.assertTrue(failure['project_created'])
        self.assertEqual(self.load('notes/run-receipt.json')['status'], 'failed')
        self.assertFalse((self.project / 'results').exists())

    def test_failed_initialization_reports_partial_directory_without_claiming_ready_project(self):
        spec = importlib.util.spec_from_file_location('penguin_partial_init', RUNNER)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        def fail_after_mkdir(run, script, *arguments):
            self.assertEqual(run.stage, 'initialize-project')
            self.project.mkdir()
            (self.project / '.research').mkdir()
            (self.project / '.research/write.lock').write_text('')
            (self.project / 'notes').mkdir()
            raise OSError('Injected disk quota failure after directory creation')

        error = io.StringIO()
        with mock.patch.object(module.ProjectRun, 'command', fail_after_mkdir), \
                contextlib.redirect_stderr(error):
            status = module.main(['--input', str(FIXTURE), '--output', str(self.project)])
        failure = json.loads(error.getvalue())
        self.assertEqual(status, 2)
        self.assertFalse(failure['project_created'])
        self.assertFalse(failure['project_initialized'])
        self.assertFalse(failure['project_ownership_confirmed'])
        self.assertEqual(Path(failure['observed_partial_path']), self.project)
        self.assertEqual(Path(failure['recovery_path']), self.project)
        self.assertIsNone(failure['receipt'])
        self.assertFalse((self.project / 'notes/run-receipt.json').exists())
        self.assertFalse((self.project / 'project.json').exists())

    def test_concurrent_initializer_is_refused_without_writing_into_its_project(self):
        spec = importlib.util.spec_from_file_location('penguin_concurrent_init', RUNNER)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        actual = module.ProjectRun.command
        before = None

        def tree():
            return {path.relative_to(self.project).as_posix():
                    (path.stat().st_mtime_ns, path.stat().st_mode,
                     hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None)
                    for path in [self.project, *self.project.rglob('*')]}

        def competing_initializer(run, script, *arguments):
            nonlocal before
            self.assertEqual(run.stage, 'initialize-project')
            # Another real CLI invocation wins after the runner's preflight,
            # before this invocation attempts to initialize the same path.
            competitor = subprocess.run(
                [sys.executable, '-X', 'utf8', '-I', '-B', str(script), 'init',
                 '--output', str(self.project), '--title', 'Other initializer owns this project'],
                cwd=self.cwd, capture_output=True, text=True, encoding='utf-8', timeout=30)
            self.assertEqual(competitor.returncode, 0, competitor.stdout + competitor.stderr)
            (self.project / 'notes').mkdir()
            before = tree()
            return actual(run, script, *arguments)

        error = io.StringIO()
        with mock.patch.object(module.ProjectRun, 'command', competing_initializer), \
                contextlib.redirect_stderr(error):
            status = module.main(['--input', str(FIXTURE), '--output', str(self.project)])
        failure = json.loads(error.getvalue())
        self.assertEqual(status, 2)
        self.assertFalse(failure['project_created'])
        self.assertFalse(failure['project_initialized'])
        self.assertFalse(failure['project_ownership_confirmed'])
        self.assertIsNone(failure['observed_partial_path'])
        self.assertIsNone(failure['recovery_path'])
        self.assertIsNone(failure['receipt'])
        self.assertEqual(tree(), before)
        self.assertEqual(self.load('project.json')['title'], 'Other initializer owns this project')


if __name__ == '__main__':
    unittest.main()
