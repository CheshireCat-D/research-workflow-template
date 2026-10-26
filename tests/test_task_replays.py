"""Replay recorded task states; scientific content is independently reviewed.

These tests do not call a model or infer proof/causal validity from text matches.
They exercise current skill connection, CLI registration and recovery using the
actual final records and artifacts from the three separately executed tasks.
"""
from pathlib import Path
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from replay_support import ReplayHarness

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / 'evals/d2/cases'
RECORDINGS = ROOT / 'evals/d2/recordings'
CASE_IDS = ('proof', 'computation', 'history')


def snapshot(root):
    return {p.relative_to(root).as_posix():
            (hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_mtime_ns)
            for p in root.rglob('*') if p.is_file()}


class RecordedResearchTasks(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='rw-task-replay-')
        self.base = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def invoke(self, script, *arguments, expected=0):
        result = subprocess.run([sys.executable, '-B', str(script), *map(str, arguments)],
                                cwd=ROOT, text=True, encoding='utf-8', capture_output=True, timeout=30,
                                env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return json.loads(result.stdout)

    def assemble(self, case, suffix=''):
        return ReplayHarness(self.base,'d2').assemble(case,suffix)

    def replay(self, case, suffix=''):
        return ReplayHarness(self.base,'d2').replay(case,suffix)

    def test_three_recorded_workflows_register_and_resume_with_current_connected_runtime(self):
        for case in CASE_IDS:
            with self.subTest(case=case):
                project, manifest, runtime = self.replay(case)
                report = self.invoke(runtime, 'check', '--root', project)
                recovered = self.invoke(runtime, 'resume', '--root', project)
                self.assertTrue(report['passed'])
                self.assertEqual(report['scientific_validity'], 'not-assessed')
                self.assertEqual(report['counts'], manifest['record_counts'])
                self.assertEqual(recovered['next_action'], manifest['cursor']['next_action'])
                self.assertFalse(recovered['needs_review'])
                for collection in ('sources', 'statements', 'evidence', 'relations', 'activities', 'artifacts'):
                    self.assertGreater(report['counts'][collection], 0)

    def test_task_recovery_is_read_only_and_material_drift_requires_review(self):
        for case in CASE_IDS:
            with self.subTest(case=case):
                project, manifest, runtime = self.replay(case)
                before = snapshot(project)
                for command in ('check', 'status', 'resume'):
                    self.invoke(runtime, command, '--root', project)
                self.assertEqual(before, snapshot(project))
                inputs = [entry['record']['location']['path'] for entry in manifest['records']
                          if entry['kind'] == 'evidence' and entry['record']['location']['kind'] == 'local'
                          and entry['record']['location']['path'] in manifest['case_files']]
                self.assertTrue(inputs, 'Task recording needs actual local source evidence')
                changed = project / inputs[0]
                changed.write_bytes(changed.read_bytes() + b'\nChanged after recorded review.\n')
                before_resume = snapshot(project)
                recovered = self.invoke(runtime, 'resume', '--root', project, expected=1)
                self.assertTrue(recovered['needs_review'])
                self.assertEqual(recovered['next_action'], manifest['cursor']['next_action'])
                self.assertIn('file_changed', {item['code'] for item in recovered['findings']})
                self.assertEqual(before_resume, snapshot(project))

    def test_recorded_input_identity_and_outputs_match_executed_task_snapshot(self):
        for case in CASE_IDS:
            with self.subTest(case=case):
                recording = RECORDINGS / case
                manifest = json.loads((recording / 'recording.json').read_text(encoding='utf-8'))
                for name, digest in manifest['case_input_sha256'].items():
                    self.assertEqual(hashlib.sha256((CASES / case / name).read_bytes()).hexdigest(), digest)
                for name, digest in manifest['output_sha256'].items():
                    self.assertEqual(hashlib.sha256((recording / 'outputs' / name).read_bytes()).hexdigest(), digest)

    def test_computational_task_reexecutes_all_cases_with_equal_calls_and_reference_errors(self):
        project, _ = self.assemble('computation')
        fresh = self.base / 'fresh-computation'
        source = project / 'artifacts/run.py'
        source_bytes = source.read_bytes()
        prefix = [str(ROOT / 'tests/recorded_platform.py')] if os.name == 'nt' else []
        completed = subprocess.run([sys.executable, '-X', 'utf8', '-B', *prefix, str(source),
                                    '--output-dir', str(fresh)], cwd=self.base,
                                   text=True, encoding='utf-8', capture_output=True, timeout=10,
                                   env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        result = json.loads((fresh / 'results.json').read_text(encoding='utf-8'))
        self.assertEqual(source.read_bytes(), source_bytes)
        self.assertEqual(result['configuration']['code_sha256'], hashlib.sha256(source_bytes).hexdigest())
        if os.name == 'nt':
            receipt = json.loads(completed.stderr)
            self.assertEqual(receipt['adapter'], 'windows-frozen-fixture-instrumentation')
            self.assertFalse(receipt['scientific_source_bytes_changed'])
            self.assertIsNone(result['execution']['max_rss'])
            limits = result['configuration']['resource_limits']
            self.assertEqual(limits['RLIMIT_CPU'], [None, None])
            self.assertIn('not applied:', limits['cpu_limit_setting'])
            self.assertIn('unavailable on Windows', limits['cpu_limit_setting'])
        functions = {
            'quadratic': (lambda x: x*x, 1/3),
            'exponential': (math.exp, math.exp(1)-1),
            'root': (math.sqrt, 2/3),
            'oscillation': (lambda x: math.cos(18*math.pi*x), 0.0),
            'kink': (lambda x: abs(x-0.37), (0.37**2+0.63**2)/2),
            'rational': (lambda x: 1/(1+25*x*x), math.atan(5)/5),
        }
        rows = result['raw_results']
        expected_keys = {(target, budget, method) for target in functions
                         for budget in (9, 33, 129) for method in ('midpoint', 'trapezoid')}
        self.assertEqual(len(rows), 36)
        self.assertEqual({(r['target_id'], r['budget'], r['method']) for r in rows}, expected_keys)
        self.assertEqual(result['failures'], [])
        self.assertEqual(result['execution']['formal_function_calls'], 2052)
        self.assertIsNone(result['configuration']['random_seed'])
        for row in rows:
            with self.subTest(target=row['target_id'], budget=row['budget'], method=row['method']):
                function, reference = functions[row['target_id']]
                budget = row['budget']
                self.assertEqual(row['actual_function_calls'], budget)
                self.assertEqual(row['subintervals'], budget if row['method'] == 'midpoint' else budget-1)
                self.assertEqual(row['status'], 'ok')
                self.assertIsNone(row['failure'])
                if row['method'] == 'midpoint':
                    expected = math.fsum(function((i+0.5)/budget) for i in range(budget))/budget
                else:
                    n = budget-1
                    expected = (function(0)/2 + math.fsum(function(i/n) for i in range(1,n)) + function(1)/2)/n
                self.assertTrue(math.isfinite(row['estimate']))
                self.assertAlmostEqual(row['estimate'], expected, delta=1e-12)
                self.assertAlmostEqual(row['reference_value'], reference, delta=1e-14)
                self.assertAlmostEqual(row['absolute_error'], abs(expected-reference), delta=1e-12)
        # Two closed-form diagnostics independent of a table-level success flag.
        quadratic = next(r for r in rows if (r['target_id'],r['budget'],r['method']) == ('quadratic',9,'midpoint'))
        self.assertAlmostEqual(quadratic['estimate'], 1/3-1/(12*9**2), delta=1e-14)
        alias = next(r for r in rows if (r['target_id'],r['budget'],r['method']) == ('oscillation',9,'midpoint'))
        self.assertAlmostEqual(alias['absolute_error'], 1.0, delta=1e-14)

    def test_proof_artifact_input_checker_reruns_with_all_traceability_inputs(self):
        project, _ = self.assemble('proof')
        expected = json.loads((project / 'notes/input-check.json').read_text(encoding='utf-8'))
        completed = subprocess.run([sys.executable, '-B', str(project / 'code/check_inputs.py')],
                                   cwd=self.base, text=True, encoding='utf-8', capture_output=True, timeout=10,
                                   env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(json.loads(completed.stdout), expected)
        self.assertEqual(json.loads((project / 'notes/input-check.json').read_text(encoding='utf-8')), expected)


if __name__ == '__main__':
    unittest.main()
