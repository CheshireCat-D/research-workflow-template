"""Fault-injection tests for record integrity, not model or semantic scoring."""
from copy import deepcopy
import hashlib
from itertools import combinations, product
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import types
import unittest


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'evals/comparison'
MODULE = types.ModuleType('comparison_summary')
MODULE.__file__ = str(BASE / 'summary.py')
exec(compile((BASE / 'summary.py').read_text(), MODULE.__file__, 'exec'), MODULE.__dict__)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n',
                    encoding='utf-8')


class ComparisonIntegrity(unittest.TestCase):
    def test_published_pilot_binds_actual_reports_and_semantic_adjudications(self):
        current = MODULE.summarize(BASE)
        self.assertEqual(current['status'], 'complete')
        self.assertEqual(current['recorded_trials'], current['expected_trials'])
        self.assertEqual(current['scored_trials'], current['expected_trials'])
        self.assertEqual(current, read(BASE / 'summary.json'))

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name) / 'comparison'
        shutil.copytree(BASE, self.base, ignore=shutil.ignore_patterns(
            'trials', 'runs', 'adjudications', '__pycache__'))
        self.freeze = read(self.base / 'freeze.json')

    def make_trials(self):
        """Invent only harness metadata/scores, never real execution evidence."""
        for index, planned in enumerate(self.freeze['trial_plan']):
            task, arm = planned['task_id'], planned['arm']
            trial_id, submission = 'fixture-' + str(index), 'anon-' + str(index)
            run = self.base / 'runs' / trial_id
            run.mkdir(parents=True, exist_ok=True)
            report = run / 'report.md'
            report.write_text('Synthetic integrity-test fixture only.\n', encoding='utf-8')
            execution = read(self.base / 'templates/execution.template.json')
            execution.update(status='executed', tool_calls=2, network_calls=0,
                             duration_seconds=1.0, output_bytes=report.stat().st_size,
                             output_unicode_characters=len(report.read_text()))
            names = {'tasks/' + task + '.md',
                     *self.freeze['required_guidance'][arm]}
            if arm == 'rwt':
                names.add(self.freeze['method_guidance'][task])
            hashes = dict(self.freeze['files'], **self.freeze['guidance_sha256'])
            execution['actual_reads'] = [{'logical_name': name, 'sha256': hashes[name]}
                                         for name in sorted(names)]
            write(run / 'execution.json', execution)
            key = read(self.base / 'reference-key.json')['tasks'][task]
            judgment = {
                'schema_version': 1, 'submission_id': submission, 'task_id': task,
                'report_sha256': digest(report), 'scored': True,
                'judge_context': 'Synthetic test fixture only',
                'arm_visibility': 'hidden-by-instruction', 'os_audited': False,
                'verdict': key['expected_verdict'],
                'criteria': [{'id': c['id'], 'score': 2,
                              'evidence': 'Synthetic fixture paragraph1',
                              'rationale': 'Harness fixture; no semantic adjudication'}
                             for c in key['criteria']],
                'invented_major_objections': [], 'notes': 'Not an actual trial'}
            judgment_path = self.base / 'adjudications' / (submission + '.json')
            write(judgment_path, judgment)
            trial = {'schema_version': 1, 'trial_id': trial_id, 'task_id': task,
                     'arm': arm, 'freeze_sha256': digest(self.base / 'freeze.json'),
                     'task_sha256': self.freeze['files']['tasks/' + task + '.md'],
                     'report': {'path': report.relative_to(self.base).as_posix(),
                                'sha256': digest(report)},
                     'execution': {'path': (run / 'execution.json').relative_to(
                         self.base).as_posix(), 'sha256': digest(run / 'execution.json')},
                     'blind': {'submission_id': submission,
                               'arm_revealed_to_judge': False,
                               'adjudication': {'path': judgment_path.relative_to(
                                   self.base).as_posix(), 'sha256': digest(judgment_path)}}}
            write(self.base / 'trials' / (trial_id + '.json'), trial)

    def change_bound(self, section, mutation):
        path = sorted((self.base / 'trials').glob('*.json'))[0]
        trial = read(path)
        binding = trial['blind']['adjudication'] if section == 'adjudication' else trial[section]
        target = self.base / binding['path']
        value = read(target)
        mutation(value)
        write(target, value)
        binding['sha256'] = digest(target)
        write(path, trial)

    def test_freeze_pins_current_inputs_and_no_control_characters(self):
        result = MODULE.summarize(self.base)
        self.assertEqual(result['status'], 'incomplete')
        self.assertEqual(len(result['missing']), 12)
        self.assertEqual(result['scored_trials'], 0)
        for path in (self.base / 'tasks').glob('*.md'):
            self.assertFalse(any(ord(c) < 32 and c not in '\n\t'
                                 for c in path.read_text()))

    def test_cli_rejects_missing_by_default_and_explicitly_allows_incomplete(self):
        command = [sys.executable, '-B', str(BASE / 'summary.py'),
                   '--root', str(self.base)]
        strict = subprocess.run(command, capture_output=True, text=True, timeout=10)
        allowed = subprocess.run(command + ['--allow-incomplete'], capture_output=True,
                                 text=True, timeout=10)
        self.assertEqual(strict.returncode, 1)
        self.assertEqual(allowed.returncode, 0)
        self.assertEqual(json.loads(allowed.stdout)['status'], 'incomplete')

    def test_complete_metadata_does_not_invent_known_model_or_general_accuracy(self):
        self.make_trials()
        result = MODULE.summarize(self.base)
        self.assertEqual(result['status'], 'complete')
        self.assertEqual(result['scored_trials'], 12)
        self.assertIn('model', result['results'][0]['effective_configuration_unknown'])
        self.assertNotIn('accuracy', result)
        self.assertNotIn('passed', result)

    def test_duplicate_pair_rejected_even_if_identifiers_differ(self):
        self.make_trials()
        first = sorted((self.base / 'trials').glob('*.json'))[0]
        duplicate = read(first)
        duplicate['trial_id'] = 'different-id'
        write(self.base / 'trials/duplicate.json', duplicate)
        with self.assertRaisesRegex(ValueError, 'duplicate task/arm'):
            MODULE.summarize(self.base)

    def test_changed_frozen_task_rejected(self):
        (self.base / 'tasks/Q11.md').write_text('changed')
        with self.assertRaisesRegex(ValueError, 'bad SHA256'):
            MODULE.summarize(self.base)

    def test_modified_freeze_itself_rejected(self):
        freeze = deepcopy(self.freeze)
        freeze['scope'] = 'unfrozen change'
        write(self.base / 'freeze.json', freeze)
        with self.assertRaisesRegex(ValueError, 'bad SHA256'):
            MODULE.summarize(self.base)

    def test_tampered_report_rejected(self):
        self.make_trials()
        next((self.base / 'runs').glob('*/report.md')).write_text('tampered')
        with self.assertRaisesRegex(ValueError, 'bad SHA256'):
            MODULE.summarize(self.base)

    def test_unscored_is_incomplete_without_zero_imputation(self):
        self.make_trials()
        self.change_bound('adjudication', lambda j: j.update(scored=False))
        result = MODULE.summarize(self.base)
        self.assertEqual(result['status'], 'incomplete')
        self.assertEqual(result['scored_trials'], 11)
        self.assertEqual(sum(r['score'] is None for r in result['results']), 1)

    def test_missing_or_duplicate_criterion_rejected(self):
        for duplicate in (False, True):
            with self.subTest(duplicate=duplicate):
                self.make_trials()
                def mutate(j):
                    j['criteria'].pop()
                    if duplicate:
                        j['criteria'].append(deepcopy(j['criteria'][0]))
                self.change_bound('adjudication', mutate)
                with self.assertRaisesRegex(ValueError, 'criterion'):
                    MODULE.summarize(self.base)

    def test_scores_require_evidence_and_cannot_exceed_rubric(self):
        self.make_trials()
        self.change_bound('adjudication', lambda j: j['criteria'][0].update(score=3))
        with self.assertRaisesRegex(ValueError, 'invalid criterion score'):
            MODULE.summarize(self.base)
        self.make_trials()
        self.change_bound('adjudication', lambda j: j['criteria'][0].update(evidence=''))
        with self.assertRaisesRegex(ValueError, 'evidence/rationale'):
            MODULE.summarize(self.base)

    def test_failed_run_cannot_carry_a_score(self):
        self.make_trials()
        self.change_bound('execution', lambda e: e.update(status='failed', failure='timeout'))
        with self.assertRaisesRegex(ValueError, 'score attached'):
            MODULE.summarize(self.base)

    def test_bad_actual_read_hash_rejected(self):
        self.make_trials()
        self.change_bound('execution', lambda e: e['actual_reads'][0].update(sha256='0' * 64))
        with self.assertRaisesRegex(ValueError, 'actual read hash mismatch'):
            MODULE.summarize(self.base)

    def test_budget_violation_and_extra_read_are_recorded_as_incomplete(self):
        self.make_trials()
        def mutate(e):
            e['tool_calls'] = 9
            e['actual_reads'].append({'logical_name': 'reference-key.json',
                                      'sha256': self.freeze['files']['reference-key.json']})
        self.change_bound('execution', mutate)
        result = MODULE.summarize(self.base)
        self.assertEqual(result['status'], 'incomplete')
        issues = str(result['incomplete_trials'])
        self.assertIn('tool-budget-exceeded', issues)
        self.assertIn('forbidden-read:reference-key.json', issues)

    def test_nonfinite_duration_rejected(self):
        self.make_trials()
        self.change_bound('execution', lambda e: e.update(duration_seconds=float('nan')))
        with self.assertRaisesRegex(ValueError, 'non-finite'):
            MODULE.summarize(self.base)

    def test_path_escape_and_symlink_trial_rejected(self):
        self.make_trials()
        first = sorted((self.base / 'trials').glob('*.json'))[0]
        trial = read(first)
        trial['report']['path'] = '../outside.md'
        write(first, trial)
        with self.assertRaisesRegex(ValueError, 'unsafe file path'):
            MODULE.summarize(self.base)
        self.make_trials()
        outside = Path(self.temp.name) / 'outside.json'
        shutil.copyfile(first, outside)
        first.unlink()
        first.symlink_to(outside)
        with self.assertRaisesRegex(ValueError, 'symlink forbidden'):
            MODULE.summarize(self.base)

    def test_independent_small_randomization_counts(self):
        outcomes = [0, 0, 1, 1, 2, 2]
        tails = [c for c in combinations(range(6), 3)
                 if abs(2 * sum(outcomes[i] for i in c) - 6) >= 4]
        self.assertEqual(len(tails), 4)
        signs = list(product((-1, 1), repeat=8))
        self.assertEqual(sum(sum(s) >= 6 for s in signs), 9)
        self.assertEqual(sum(abs(sum(s)) >= 6 for s in signs), 18)


if __name__ == '__main__':
    unittest.main()
