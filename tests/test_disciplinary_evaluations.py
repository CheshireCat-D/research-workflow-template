"""Actual disciplinary task recordings, portable replay and independent arithmetic.

No model is called here. Humanistic/legal meanings and prose quality remain
separately agent-reviewed; hashes preserve the identity of those observations.
"""
from collections import defaultdict
from fractions import Fraction
from pathlib import Path
import csv
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import struct
import tempfile
import unittest
from replay_support import ReplayHarness

ROOT = Path(__file__).resolve().parents[1]
EVAL = ROOT / 'evals/disciplinary'
CASES = ('compartment-exchange', 'index-build-cost', 'missing-outcomes',
         'factorial-animal', 'weighted-survey', 'artwork-versions', 'legal-language-scope')


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def snapshot(root):
    return {p.relative_to(root).as_posix(): (sha(p), p.stat().st_mtime_ns)
            for p in root.rglob('*') if p.is_file()}


class DisciplinaryRecordings(unittest.TestCase):
    def test_seven_contexts_bind_actual_inputs_outputs_guidance_and_separate_review(self):
        coverage = read(EVAL / 'coverage.json')
        reviews = read(EVAL / 'independent-review.json')
        self.assertEqual(set(coverage['cases']), set(CASES))
        self.assertEqual(set(reviews['cases']), set(CASES))
        disciplines = set()
        for case in CASES:
            with self.subTest(case=case):
                manifest = read(EVAL / 'recordings' / case / 'recording.json')
                review = reviews['cases'][case]
                disciplines.update(manifest['project_init']['disciplines'])
                self.assertEqual(review['status'], 'pass-in-scope')
                self.assertEqual(review['input_sha256'], manifest['case_input_sha256'])
                projection = manifest['distribution_projection']
                self.assertEqual(projection['review_receipt_sha256'], sha(EVAL / 'independent-review.json'))
                omitted = [name for group in projection['omitted_outputs'] for name in group['files']]
                self.assertEqual(len(omitted), len(set(omitted)))
                self.assertFalse(set(omitted) & set(manifest['output_files']))
                self.assertEqual(set(manifest['output_files']) | set(omitted), set(review['output_sha256']))
                self.assertEqual(manifest['output_sha256'], {
                    name: review['output_sha256'][name] for name in manifest['output_files']
                })
                self.assertEqual(manifest['executed_output_sha256'], {
                    name: review['executed_output_sha256'][name] for name in manifest['output_files']
                })
                for group in projection['omitted_outputs']:
                    self.assertTrue(group['reason'])
                    self.assertTrue(group['retained_at'])
                    for locator in group['retained_at']:
                        prefix, name = locator.split(':', 1)
                        base = {'output': EVAL / 'recordings' / case / 'outputs',
                                'recording': EVAL / 'recordings' / case,
                                'case': EVAL / 'cases' / case}[prefix]
                        retained = base / name.split('#', 1)[0]
                        self.assertTrue(retained.is_file(), locator)
                    if group['reason'].startswith('Byte-identical copy'):
                        prefix, canonical = group['retained_at'][0].split(':', 1)
                        base = {'output': EVAL / 'recordings' / case / 'outputs',
                                'recording': EVAL / 'recordings' / case,
                                'case': EVAL / 'cases' / case}[prefix]
                        digest = sha(base / canonical)
                        self.assertTrue(all(review['output_sha256'][name] == digest
                                            for name in group['files']))
                    if group['reason'].startswith('Empty command stream'):
                        self.assertTrue(all(review['output_sha256'][name] == hashlib.sha256(b'').hexdigest()
                                            for name in group['files']))
                self.assertEqual(review['guidance_sha256'], manifest['guidance_sha256'])
                inputs = EVAL / 'cases' / case
                outputs = EVAL / 'recordings' / case / 'outputs'
                self.assertEqual(set(manifest['case_input_sha256']),
                                 {p.relative_to(inputs).as_posix() for p in inputs.rglob('*') if p.is_file()})
                self.assertEqual(set(manifest['output_files']), set(manifest['output_sha256']))
                self.assertEqual(set(manifest['output_files']),
                                 {p.relative_to(outputs).as_posix() for p in outputs.rglob('*') if p.is_file()})
                for name, digest in manifest['case_input_sha256'].items():
                    self.assertEqual(sha(inputs / name), digest, name)
                for name, digest in manifest['output_sha256'].items():
                    self.assertEqual(sha(outputs / name), digest, name)
                normalized = {row['path']: row for row in manifest['output_normalizations']}
                self.assertEqual(set(normalized), {
                    name for name, digest in manifest['executed_output_sha256'].items()
                    if digest != manifest['output_sha256'][name]
                })
                for name, change in normalized.items():
                    self.assertEqual(change['original_sha256'], manifest['executed_output_sha256'][name])
                    self.assertEqual(change['published_sha256'], manifest['output_sha256'][name])
                    self.assertFalse(name.endswith('.py'), 'Portable scientific code must not need path rewriting')
                    self.assertNotIn(name, {'artifacts/results.json', 'manuscript/report.md'})
                for duplicate in manifest['omitted_identical_outputs']:
                    self.assertNotIn(duplicate['path'], manifest['output_files'])
                    self.assertEqual(duplicate['sha256'], manifest['output_sha256'][duplicate['canonical']])
                for name, digest in manifest['guidance_sha256'].items():
                    self.assertEqual(sha(ROOT / name), digest, name)
                for name in ('observed-check.json', 'observed-resume.json'):
                    self.assertEqual(sha(EVAL / 'recordings' / case / name),
                                     manifest[name.removesuffix('.json').replace('-', '_') + '_sha256'])
                self.assertTrue(review['findings'])
                self.assertTrue(review['reviewer'])
                self.assertNotEqual(review['reviewer'], review['executor'])
        self.assertEqual(disciplines, {d['id'] for d in read(ROOT / 'design/catalog.json')['disciplines']})

    def test_distribution_cleanup_preserves_replay_state_and_research_resources(self):
        fields = ('project_init', 'case_files', 'case_input_sha256', 'records',
                  'record_counts', 'cursor', 'guidance_sha256', 'reproduction')
        for case in CASES:
            with self.subTest(case=case):
                manifest = read(EVAL / 'recordings' / case / 'recording.json')
                projection = manifest['distribution_projection']
                state = json.dumps({key: manifest[key] for key in fields}, ensure_ascii=False,
                                   sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')
                self.assertEqual(hashlib.sha256(state).hexdigest(), projection['replay_state_sha256'])
                outputs = EVAL / 'recordings' / case / 'outputs'
                for item in manifest['records']:
                    kind, data = item['kind'], item['record']
                    location = (data['path'] if kind == 'artifact' else
                                data.get('location', {}).get('path') if kind == 'evidence' else None)
                    if location and not location.startswith('inputs/'):
                        self.assertIn(location, manifest['output_files'])
                        self.assertTrue((outputs / location).is_file())
                reviewed = read(EVAL / 'independent-review.json')['cases'][case]['output_sha256']
                for name in reviewed:
                    if name.startswith(('artifacts/', 'notes/', 'manuscript/')) or name in {'review.md', 'execution.json'} or name.endswith('.py'):
                        self.assertIn(name, manifest['output_files'])
                        self.assertEqual(sha(outputs / name), reviewed[name])

    def test_recorded_projects_recover_read_only_and_changed_inputs_trigger_review(self):
        with tempfile.TemporaryDirectory(prefix='rw-disciplinary-replay-') as temporary:
            harness = ReplayHarness(Path(temporary), 'disciplinary')
            for case in CASES:
                with self.subTest(case=case):
                    project, manifest, runtime = harness.replay(case)
                    before = snapshot(project)
                    checked = harness.invoke(runtime, 'check', '--root', project)
                    resumed = harness.invoke(runtime, 'resume', '--root', project)
                    self.assertTrue(checked['passed'])
                    self.assertEqual(checked['counts'], manifest['record_counts'])
                    self.assertFalse(resumed['needs_review'])
                    self.assertEqual(resumed['next_action'], manifest['cursor']['next_action'])
                    self.assertEqual(snapshot(project), before)
                    evidence = {x['record']['id']: x['record'] for x in manifest['records']
                                if x['kind'] == 'evidence'}
                    linked = []
                    for entry in manifest['records']:
                        activity = entry['record']
                        if entry['kind'] == 'activity' and activity['status'] == 'done':
                            linked += [ref.split(':', 1)[1] for ref in activity.get('inputs', [])
                                       if ref.startswith('evidence:')]
                    inputs = [evidence[key]['location']['path'] for key in linked
                              if evidence[key]['location']['kind'] == 'local'
                              and evidence[key]['location']['path'] in manifest['case_files']]
                    self.assertTrue(inputs, 'A completed activity must use actual local task evidence')
                    target = project / inputs[0]
                    target.write_bytes(target.read_bytes() + b'\nChanged after the recorded task.\n')
                    before_resume = snapshot(project)
                    changed = harness.invoke(runtime, 'resume', '--root', project, expected=1)
                    self.assertTrue(changed['needs_review'])
                    self.assertIn('file_changed', {row['code'] for row in changed['findings']})
                    self.assertEqual(snapshot(project), before_resume)
                    self.assertTrue(any(row['effective_status'] == 'stale' for row in changed['activities']))


class DisciplinaryCalculations(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='rw-disciplinary-code-')
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)

    def assert_same_result(self, observed, recorded, location='$'):
        """Compare every field, allowing only bounded floating-point variation."""
        self.assertEqual(type(observed), type(recorded), location)
        if isinstance(observed, dict):
            self.assertEqual(set(observed), set(recorded), location)
            for key in observed:
                self.assert_same_result(observed[key], recorded[key], location + '.' + key)
        elif isinstance(observed, list):
            self.assertEqual(len(observed), len(recorded), location)
            for index, (actual, previous) in enumerate(zip(observed, recorded)):
                self.assert_same_result(actual, previous, f'{location}[{index}]')
        elif isinstance(observed, float):
            self.assertTrue(math.isfinite(observed) and math.isfinite(recorded), location)
            self.assertTrue(math.isclose(observed, recorded, rel_tol=1e-12, abs_tol=1e-12), location)
        else:
            self.assertEqual(observed, recorded, location)

    def run_case(self, case, mutate=None, expected=0):
        work = Path(tempfile.mkdtemp(prefix=case + '-', dir=self.base))
        inputs = work / 'inputs'
        shutil.copytree(EVAL / 'cases' / case, inputs)
        source = EVAL / 'recordings' / case / 'outputs/artifacts/run.py'
        local = work / 'run.py'
        shutil.copyfile(source, local)
        if mutate:
            mutate(inputs)
        before = snapshot(inputs)
        result = subprocess.run([sys.executable, '-X', 'utf8', '-I', '-B', str(local),
                                 '--input-dir', str(inputs), '--output-dir', str(work / 'new-output')],
                                cwd=work, capture_output=True, text=True, encoding='utf-8',
                                env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'),
                                timeout=60 if os.name == 'nt' else 20)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        self.assertEqual(snapshot(inputs), before)
        self.assertEqual(local.read_bytes(), source.read_bytes())
        if expected:
            self.assertFalse((work / 'new-output').exists())
            self.assertNotIn('Traceback', result.stdout + result.stderr)
            return result, inputs
        generated = read(work / 'new-output/results.json')
        if mutate is None:
            self.assert_same_result(generated, read(EVAL / 'recordings' / case / 'outputs/artifacts/results.json'))
        return generated, inputs

    def test_exchange_analytic_and_discrete_states_follow_changed_parameters(self):
        def mutate(inputs):
            p = inputs / 'parameters.json'
            v = read(p)
            v.update(a0=7, b0=1, k_per_hour=0.25)
            p.write_text(json.dumps(v), encoding='utf-8')
        for change in (None, mutate):
            result, inputs = self.run_case('compartment-exchange', change)
            p = read(inputs / 'parameters.json')
            mean, halfdiff = (p['a0'] + p['b0']) / 2, (p['a0'] - p['b0']) / 2
            self.assertEqual(result['invariants']['equilibrium_concentration'], mean)
            self.assertEqual([r['t_hours'] for r in result['analytic_comparison']], p['times_hours'])
            for row in result['analytic_comparison']:
                d = halfdiff * math.exp(-2 * p['k_per_hour'] * row['t_hours'])
                self.assertAlmostEqual(row['a'], mean + d, delta=1e-12)
                self.assertAlmostEqual(row['b'], mean - d, delta=1e-12)
            self.assertEqual([r['h_hours'] for r in result['euler_cases']], p['euler_steps_hours'])
            for block in result['euler_cases']:
                q = 1 - 2 * p['k_per_hour'] * block['h_hours']
                self.assertEqual(block['difference_mode_asymptotically_stable'], abs(q) < 1)
                self.assertEqual(block['preserves_nonnegativity_for_all_nonnegative_initial_states'],
                                 0 <= p['k_per_hour'] * block['h_hours'] <= 1)
                self.assertEqual(len(block['rows']), p['n_steps'] + 1)
                for row in block['rows']:
                    d = halfdiff * q ** row['step']
                    self.assertAlmostEqual(row['a'], mean + d, delta=1e-12)
                    self.assertAlmostEqual(row['b'], mean - d, delta=1e-12)

    def test_index_returns_and_total_cost_include_the_actual_build(self):
        def mutate(inputs):
            with (inputs / 'records.csv').open('a', encoding='utf-8') as f:
                f.write('a,99\n')
        for change in (None, mutate):
            result, inputs = self.run_case('index-build-cost', change)
            with (inputs / 'records.csv').open(encoding='utf-8', newline='') as f:
                records = list(csv.DictReader(f))
            config = read(inputs / 'queries.json')
            # Last match via reverse iteration, independent of either implementation.
            values = [next((int(row['value']) for row in reversed(records) if row['key'] == q), None)
                      for q in config['queries']]
            self.assertEqual(result['all_query_return_values'], values)
            self.assertEqual([r['query_count'] for r in result['workloads']], config['prefix_lengths'])
            for row in result['workloads']:
                n, m = len(records), row['query_count']
                self.assertEqual(row['L_total_cost'], n * m)
                self.assertEqual(row['I_build_cost'], n)
                self.assertEqual(row['I_total_cost'], n + m)
                self.assertEqual([r['I_value'] for r in row['query_trace']], values[:m])
                self.assertEqual([r['L_value'] for r in row['query_trace']], values[:m])

    def test_missing_outcome_bounds_and_count_grid_follow_observed_events(self):
        def mutate(inputs):
            p = inputs / 'outcomes.csv'
            p.write_text(p.read_text(encoding='utf-8').replace('A01,A,1', 'A01,A,0'), encoding='utf-8')
        for change in (None, mutate):
            result, inputs = self.run_case('missing-outcomes', change)
            with (inputs / 'outcomes.csv').open(encoding='utf-8', newline='') as f:
                rows = list(csv.DictReader(f))
            arms = {arm: [r for r in rows if r['arm'] == arm] for arm in ('A', 'B')}
            n = {arm: len(v) for arm, v in arms.items()}
            events = {arm: sum(r['event'] == '1' for r in v) for arm, v in arms.items()}
            missing = {arm: sum(r['event'] == '' for r in v) for arm, v in arms.items()}
            cc = Fraction(events['A'], n['A'] - missing['A']) - Fraction(events['B'], n['B'] - missing['B'])
            expected = {(a, b): Fraction(events['A'] + a, n['A']) - Fraction(events['B'] + b, n['B'])
                        for a in range(missing['A'] + 1) for b in range(missing['B'] + 1)}
            self.assertEqual(Fraction(result['complete_case_risk_difference']['fraction']), cc)
            bounds = result['assigned_cohort_risk_difference_bounds']
            self.assertEqual(Fraction(bounds['lower']['fraction']), min(expected.values()))
            self.assertEqual(Fraction(bounds['upper']['fraction']), max(expected.values()))
            actual = {(row['missing_events']['A'], row['missing_events']['B']):
                      Fraction(row['risk_difference']['fraction']) for row in result['count_combinations']}
            self.assertEqual(actual, expected)
            self.assertEqual(len(result['count_combinations']), len(expected))
            self.assertEqual(sum(r['individual_completion_count'] for r in result['count_combinations']),
                             2 ** sum(missing.values()))

    def test_factorial_contrasts_follow_cage_and_block_means(self):
        def mutate(inputs):
            p = inputs / 'observations.csv'
            with p.open(encoding='utf-8', newline='') as f:
                rows = list(csv.DictReader(f))
            for row in rows:
                if row['F'] == row['E'] == '1':
                    row['gain'] = str(float(row['gain']) + 2)
            with p.open('w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys()); writer.writeheader(); writer.writerows(rows)
        for change in (None, mutate):
            result, inputs = self.run_case('factorial-animal', change)
            with (inputs / 'observations.csv').open(encoding='utf-8', newline='') as f:
                rows = list(csv.DictReader(f))
            cages = defaultdict(list)
            for row in rows:
                cages[(row['block'], row['cage'], int(row['F']), int(row['E']))].append(Fraction(row['gain']))
            blocks = defaultdict(dict)
            for (block, cage, factor, environment), values in cages.items():
                blocks[block][factor, environment] = sum(values) / len(values)
            contrasts = []
            for cells in blocks.values():
                x00, x10, x01, x11 = (cells[key] for key in [(0, 0), (1, 0), (0, 1), (1, 1)])
                contrasts.append(((x10 + x11 - x00 - x01) / 2,
                                  (x01 + x11 - x00 - x10) / 2, x11 - x01 - x10 + x00))
            self.assertEqual(result['counts']['cages'], len(cages))
            self.assertEqual(result['counts']['animal_records'], len(rows))
            for i, key in enumerate(['F_marginal_g', 'E_marginal_g', 'interaction_g']):
                self.assertAlmostEqual(result['overall_equal_block_contrasts'][key],
                                       float(sum(c[i] for c in contrasts) / len(contrasts)), delta=1e-12)
            self.assertEqual([r['interaction_g'] for r in result['by_block']], [float(c[2]) for c in contrasts])

    def test_survey_weights_and_missing_ranges_follow_stratum_population(self):
        def mutate(inputs):
            p = inputs / 'strata.csv'
            p.write_text(p.read_text(encoding='utf-8').replace('H1,800,', 'H1,600,').replace('H2,200,', 'H2,400,'), encoding='utf-8')
        for change in (None, mutate):
            result, inputs = self.run_case('weighted-survey', change)
            with (inputs / 'strata.csv').open(encoding='utf-8', newline='') as f:
                rows = [{k: (v if k == 'stratum' else Fraction(v)) for k, v in r.items()} for r in csv.DictReader(f)]
            N = sum(r['population'] for r in rows); n = sum(r['sampled'] for r in rows)
            y = sum(r['yes'] for r in rows); respond = sum(r['respondents'] for r in rows)
            missing = sum(r['sampled'] - r['respondents'] for r in rows)
            wy = sum(r['population'] / r['sampled'] * r['yes'] for r in rows)
            wr = sum(r['population'] / r['sampled'] * r['respondents'] for r in rows)
            corrected = sum(r['population'] * r['yes'] / r['respondents'] for r in rows) / N
            expected = {'unweighted_respondents': y / respond, 'design_weighted_respondents': wy / wr,
                        'nonresponse_adjusted': corrected}
            for key, fraction in expected.items():
                self.assertEqual(Fraction(result['estimators'][key]['value']['fraction']), fraction)
            weighted_missing = sum(r['population'] / r['sampled'] * (r['sampled'] - r['respondents']) for r in rows)
            for key, low, high in [('sampled_raw', y / n, (y + missing) / n),
                                   ('design_weighted', wy / N, (wy + weighted_missing) / N)]:
                observed = result['missing_outcome_bounds'][key]
                self.assertEqual(Fraction(observed['lower']['fraction']), low)
                self.assertEqual(Fraction(observed['upper']['fraction']), high)

    def test_legal_enumeration_matches_clause_model_and_reads_applicant_facts(self):
        def mutate(inputs):
            p = inputs / 'source-packet.md'
            p.write_text(p.read_text(encoding='utf-8').replace('申请人乙：年龄17', '申请人乙：年龄18'), encoding='utf-8')
        for change in (None, mutate):
            result, inputs = self.run_case('legal-language-scope', change)
            rows = result['enumeration']['rows']
            self.assertEqual(len(rows), 32)
            self.assertEqual(len({tuple(r['facts'][key] for key in 'ARTSP') for r in rows}), 32)
            for row in rows:
                a, resident, training, supervision, prohibition = (row['facts'][key] for key in 'ARTSP')
                expected = a and resident and (training or supervision) and not prohibition
                self.assertEqual(row['factored'], expected)
                self.assertEqual(row['distributed'], expected)
            text = (inputs / 'source-packet.md').read_text(encoding='utf-8')
            ages = {name: int(age) for name, age in re.findall(r'申请人([甲乙丙])：年龄(\d+)', text)}
            self.assertEqual({r['name'] for r in result['applicants']}, set(ages))
            for person in result['applicants']:
                f = person['facts']
                self.assertEqual(f['A'], ages[person['name']] >= 18)
                self.assertEqual(person['may_apply_under_section_5'],
                                 f['A'] and f['R'] and (f['T'] or f['S']) and not f['P'])
                self.assertFalse(person['review_rule']['automatic_grant_established'])
                self.assertEqual(person['review_rule']['request_within_days_after_service'], 15)
        # Finite Boolean agreement checks the explicitly reviewed model;
        # the separate content review establishes its relation to the clauses.
        def extra_condition(inputs):
            p = inputs / 'source-packet.md'
            text = p.read_text(encoding='utf-8')
            text = text.replace('但第7条禁止者除外。', '但第7条禁止者除外。监督者还须培训。')
            text = text.replace('except a person prohibited under section 7.',
                                'except a person prohibited under section 7. A supervised applicant must also have completed training.')
            p.write_text(text, encoding='utf-8')
        self.run_case('legal-language-scope', extra_condition, expected=2)

    def test_artwork_script_checks_actual_image_bytes_without_scoring_meaning(self):
        def mutate(inputs):
            with (inputs / 'source-packet.md').open('a', encoding='utf-8') as f:
                f.write('\n补充目录索引说明，图像原件保持不变。\n')
        for change in (None, mutate):
            result, inputs = self.run_case('artwork-versions', change)
            for name in ('original.png', 'reproduction.png'):
                data = (inputs / name).read_bytes()
                self.assertEqual(data[:8], b'\x89PNG\r\n\x1a\n')
                width, height = struct.unpack('>II', data[16:24])
                self.assertEqual(result['images'][name]['width'], width)
                self.assertEqual(result['images'][name]['height'], height)
                self.assertEqual(result['input_sha256'][name], sha(inputs / name))
            self.assertEqual(result['input_sha256']['source-packet.md'], sha(inputs / 'source-packet.md'))
        # These assertions verify materials, not visual or historical interpretation.


if __name__ == '__main__':
    unittest.main()
