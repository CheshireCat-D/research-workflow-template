"""Offline preservation and arithmetic checks for completed quality exercises.

Review judgments and source visits are recorded observations, not CI scores.
These tests preserve their input identities and rerun only local calculations.
They neither repeat model review/search nor certify general research quality.
"""
from collections import Counter
from fractions import Fraction
from itertools import product
from pathlib import Path, PurePosixPath
import csv
import hashlib
import json
import math
import re
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
QUALITY = ROOT / 'evals/quality'

# These are identities of the nine inputs actually adjudicated, not keywords
# for automatically deciding whether a review is scientifically correct.
REVIEW_INPUT_SHA256 = {
    'cases/R17.md': 'f29691e6a4d546fd01a0c1150701a7d229b128a7a732f3993255bc1fdd91ced7',
    'reports/R17.md': '96f6afa6748563ef794d3913b0f7f761487debc48a6cbaea93686c86426d2f7b',
    'cases/R42.md': 'd7cf1ca8dd1cfe434c13807f96024fae3ed407c4fcd8b4de4028dc966efd21f0',
    'reports/R42.md': '3d7206371ff4d189caf0db444e6b07e36995e1518620c57fb10ce4130af03606',
    'cases/R63.md': '9afd80b7b3af71486d49ec59ffc4d400ef21af3ae01c38d6525146ea296952f6',
    'reports/R63.md': 'c44b3ac34797e9d0bd85c6cf74a866884daf0bd834cb1ef33912b046afb7707d',
    'cases/R88.md': '1525eb2367a1e6814e49caee11eff1e8cc1558da4d39e8d1bcec7a17221f9ad5',
    'reports/R88.md': '025fb8cf7430cc1029d5c90f40b477e67648d7c4177399409f56ab1f0145f233',
    'reference-key.json': '08b7b46735ebe577a084796e6e9eced6a1d636d3c53a43b93b7a8d242f557420',
}
OBSERVED = {
    'R17': ('no-major-error', 'no-major-error', 0),
    'R42': ('major-error-found', 'major-error', 1),
    'R63': ('no-major-error', 'no-major-error', 0),
    'R88': ('major-error-found', 'major-error', 1),
}


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(paths):
    return {str(path): (sha(path), path.stat().st_mtime_ns) for path in paths}


class QualityEvaluations(unittest.TestCase):
    def setUp(self):
        self.manifest = read(QUALITY / 'manifest.json')

    def assert_same_result(self, actual, recorded, location='$'):
        """Check every JSON field with a small allowance for libm variation."""
        self.assertIs(type(actual), type(recorded), location)
        if isinstance(actual, dict):
            self.assertEqual(set(actual), set(recorded), location)
            for key in actual:
                self.assert_same_result(actual[key], recorded[key], location + '.' + key)
        elif isinstance(actual, list):
            self.assertEqual(len(actual), len(recorded), location)
            for index, (value, previous) in enumerate(zip(actual, recorded)):
                self.assert_same_result(value, previous, f'{location}[{index}]')
        elif isinstance(actual, float):
            self.assertTrue(math.isfinite(actual) and math.isfinite(recorded), location)
            self.assertTrue(math.isclose(actual, recorded, rel_tol=1e-12, abs_tol=1e-12), location)
        else:
            self.assertEqual(actual, recorded, location)

    def run_python(self, script, arguments, cwd):
        result = subprocess.run([sys.executable, '-X', 'utf8', '-I', '-B', str(script),
                                 *map(str, arguments)], cwd=cwd, capture_output=True,
                                text=True, encoding='utf-8', timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        receipt = json.loads(result.stdout)
        self.assertTrue(receipt['passed'])
        return receipt

    def test_manifest_closes_files_hashes_and_guidance_bindings(self):
        manifest = self.manifest
        files = manifest['files']
        actual = {path.relative_to(QUALITY).as_posix() for path in QUALITY.rglob('*')
                  if path.is_file() and path != QUALITY / 'manifest.json'}
        self.assertEqual(set(files), actual)
        for name, expected in files.items():
            with self.subTest(file=name):
                path = PurePosixPath(name)
                self.assertFalse(path.is_absolute())
                self.assertNotIn('..', path.parts)
                self.assertFalse((QUALITY / name).is_symlink())
                self.assertEqual(sha(QUALITY / name), expected)
        groups = manifest['guidance_groups']
        required = {
            'review_math': {'skills/rw-review/SKILL.md', 'profiles/methods/formal-theory.md'},
            'review_empirical': {'skills/rw-review/SKILL.md', 'profiles/methods/measurement-experiment.md',
                                 'profiles/methods/empirical-quantitative.md'},
            'literature': {'skills/rw-literature/SKILL.md',
                           'skills/rw-literature/references/search-and-library.md'},
            'adaptation': {'skills/rw-candidates/SKILL.md', 'skills/rw-validation/SKILL.md',
                           'profiles/methods/measurement-experiment.md',
                           'profiles/methods/empirical-quantitative.md'},
            'delivery': {'skills/rw-review/references/submission-delivery.md',
                         'examples/paired-pens/analyze.py', 'examples/paired-pens/observations.csv',
                         'examples/submission-table/build.py'},
        }
        for group, names in required.items():
            self.assertTrue(names <= set(groups[group]), group)
            self.assertEqual(len(groups[group]), len(set(groups[group])), group)
        bound_guidance = {name for group in groups.values() for name in group}
        self.assertEqual(bound_guidance, set(manifest['guidance_sha256']))
        for name, expected in manifest['guidance_sha256'].items():
            self.assertEqual(sha(ROOT / name), expected, name)
        for case in manifest['review']['cases']:
            expected = 'review_math' if case['id'] in ('R17', 'R42') else 'review_empirical'
            self.assertEqual(case['guidance_group'], expected)
            self.assertIn(expected, groups)
            self.assertIn(case['input'], files)
            self.assertIn(case['report'], files)
        references = {
            'review': ('reference_key', 'assessment', 'assessment_report', 'calculation_evidence'),
            'literature': ('report', 'independent_audit'),
            'adaptation': ('report', 'receipt', 'request', 'input', 'script', 'result'),
        }
        for section, fields in references.items():
            for field in fields:
                self.assertIn(manifest[section][field], files, (section, field))
        for section in ('literature', 'adaptation', 'delivery'):
            self.assertEqual(manifest[section]['guidance_group'], section)
            self.assertTrue(groups[section])

    def test_review_preserves_nine_adjudicated_inputs_key_and_observed_judgments(self):
        review = self.manifest['review']
        cases = {case['id']: case for case in review['cases']}
        self.assertEqual(len(review['cases']), 4)
        self.assertEqual(set(cases), set(OBSERVED))
        assessment = read(QUALITY / review['assessment'])
        checks = read(QUALITY / review['calculation_evidence'])
        key = read(QUALITY / review['reference_key'])
        scope = assessment['scope']
        self.assertEqual(scope['content_input_count'], 9)
        self.assertEqual(len(scope['content_inputs']), 9)
        self.assertEqual(set(scope['content_inputs']), set(REVIEW_INPUT_SHA256))
        self.assertEqual(scope['content_inputs_sha256'], REVIEW_INPUT_SHA256)
        self.assertEqual(checks['inputs_sha256'], REVIEW_INPUT_SHA256)
        self.assertTrue(scope['inputs_unchanged_during_check'])
        self.assertTrue(checks['inputs_unchanged_during_check'])
        for name, expected in REVIEW_INPUT_SHA256.items():
            self.assertEqual(sha(QUALITY / 'review' / name), expected, name)
            self.assertEqual(self.manifest['files']['review/' + name], expected)
        self.assertEqual(assessment['key_status'], 'valid_without_correction')
        self.assertEqual(assessment['key_corrections'], [])
        self.assertEqual(assessment['assessment_type'], 'post_report_reference_key_adjudication')
        self.assertEqual(assessment['computed_evidence_file'], Path(review['calculation_evidence']).name)
        results = {result['case_id']: result for result in assessment['results']}
        self.assertEqual(len(assessment['results']), 4)
        self.assertEqual(set(results), set(OBSERVED))
        self.assertEqual(set(key), set(OBSERVED))
        for case_id, (judgment, expected, supported) in OBSERVED.items():
            with self.subTest(case=case_id):
                self.assertEqual(cases[case_id]['input'], f'review/cases/{case_id}.md')
                self.assertEqual(cases[case_id]['report'], f'review/reports/{case_id}.md')
                self.assertEqual(key[case_id]['expected'], expected)
                result = results[case_id]
                self.assertEqual((result['judgment'], result['reference_expected']), (judgment, expected))
                self.assertTrue(result['reference_key_valid'])
                self.assertFalse(result['key_disagreement'])
                self.assertEqual(result['supported_major_findings'], supported)
                self.assertEqual(len(result['supported_findings']), supported)
                self.assertEqual(result['unsupported_major_findings'], 0)
                self.assertEqual(result['unsupported_findings'], [])
                self.assertFalse(result['missed_reference_defect'])

    def test_perfectly_correlated_two_point_counterexample_uses_exact_expectations(self):
        recorded = read(QUALITY / self.manifest['review']['calculation_evidence'])['R42']
        # Two joint states, with X1 = X2 in each state. Marginal equality alone
        # therefore allows a nonzero covariance; this is an exact counterexample.
        states = [(Fraction(1, 2), -1, -1), (Fraction(1, 2), 1, 1)]
        self.assertEqual(sum(p for p, _, _ in states), 1)
        means = [sum(p * state[i] for p, *state in states) for i in (0, 1)]
        variances = [sum(p * (state[i] - means[i]) ** 2 for p, *state in states)
                     for i in (0, 1)]
        covariance = sum(p * (x - means[0]) * (y - means[1]) for p, x, y in states)
        mean_average = sum(p * Fraction(x + y, 2) for p, x, y in states)
        variance_average = sum(p * (Fraction(x + y, 2) - mean_average) ** 2
                               for p, x, y in states)
        self.assertEqual(means, [0, 0])
        self.assertEqual(variances, [1, 1])
        self.assertEqual(recorded['n'], 2)
        self.assertEqual(recorded['support'], [-1, 1])
        self.assertEqual(list(map(Fraction, recorded['probabilities'])), [Fraction(1, 2)] * 2)
        for field, value in [('mean', mean_average), ('variance_each', variances[0]),
                             ('covariance', covariance), ('variance_average', variance_average),
                             ('claimed_variance', variances[0] / 2)]:
            self.assertEqual(Fraction(recorded[field]), value, field)
        self.assertNotEqual(variance_average, variances[0] / 2)

    def test_six_blocks_and_sixty_duplicates_recompute_exact_ties_and_central_quantities(self):
        checks = read(QUALITY / self.manifest['review']['calculation_evidence'])
        paired, duplicated = checks['paired_pen_checks'], checks['R88_duplicated_record_checks']
        differences = list(map(Fraction, (20, -10, 30, 0, 10, -20)))
        n = len(differences)
        mean = sum(differences) / n
        ss = sum((value - mean) ** 2 for value in differences)
        variance = ss / (n - 1)
        self.assertEqual(paired['differences'], differences)
        for field, value in [('mean_exact', mean), ('centered_sum_squares_exact', ss),
                             ('sample_variance_exact', variance)]:
            self.assertEqual(Fraction(paired[field]), value, field)
        se = math.sqrt(float(variance / n))
        self.assertAlmostEqual(paired['standard_error'], se, places=12)
        self.assertAlmostEqual(paired['t5_statistic'], float(mean) / se, places=12)

        def t5_cdf(t):
            theta = math.atan(t / math.sqrt(5))
            return (0.5 + theta / math.pi + 2 * math.sin(2 * theta) / (3 * math.pi)
                    + math.sin(4 * theta) / (12 * math.pi))

        critical = paired['t5_critical_given']
        self.assertAlmostEqual(t5_cdf(critical), 0.975, places=13)
        self.assertAlmostEqual(paired['t5_cdf_at_given_critical'], t5_cdf(critical), places=13)
        self.assertAlmostEqual(paired['t5_two_sided_p'], 2 * (1 - t5_cdf(float(mean) / se)), places=12)
        for actual, expected in zip(paired['reference_interval'], (float(mean) - critical * se,
                                                                  float(mean) + critical * se)):
            self.assertAlmostEqual(actual, expected, places=12)
        counts = Counter(sum(sign * value for sign, value in zip(signs, differences))
                         for signs in product((-1, 1), repeat=n))
        observed = abs(sum(differences))
        ties = sum(count for value, count in counts.items() if abs(value) == observed)
        strict = sum(count for value, count in counts.items() if abs(value) > observed)
        assignments = sum(counts.values())
        self.assertEqual((assignments, ties, strict, ties + strict), (64, 20, 24, 44))
        self.assertEqual(paired['randomization_assignments'], assignments)
        self.assertEqual((paired['ties'], paired['strictly_more_extreme'], paired['at_least_as_extreme']),
                         (ties, strict, ties + strict))
        self.assertEqual(paired['signed_sum_counts'], {str(int(value)): count for value, count in counts.items()})
        self.assertEqual(Fraction(paired['p_exact']), Fraction(ties + strict, assignments))
        self.assertEqual(paired['p_decimal'], float(Fraction(ties + strict, assignments)))
        # The zero-difference block still has two distinct label assignments.
        offsets = (-18, -14, -10, -6, -2, 2, 6, 10, 14, 18)
        copies = [d + offset - offset for d in differences for offset in offsets]
        copy_mean = sum(copies) / len(copies)
        copy_ss = sum((value - copy_mean) ** 2 for value in copies)
        copy_variance = copy_ss / (len(copies) - 1)
        naive_se = math.sqrt(float(copy_variance / len(copies)))
        self.assertEqual((copy_mean, copy_ss, copy_variance), (mean, 17500, Fraction(17500, 59)))
        self.assertEqual(duplicated['offset_sum'], sum(offsets))
        self.assertEqual(duplicated['records'], len(copies))
        self.assertEqual(Fraction(duplicated['sum_squares_exact']), copy_ss)
        self.assertEqual(Fraction(duplicated['sample_variance_exact']), copy_variance)
        self.assertAlmostEqual(duplicated['naive_standard_error'], naive_se, places=12)
        self.assertAlmostEqual(duplicated['naive_t_statistic'], float(copy_mean) / naive_se, places=12)
        nominal = duplicated['nominal_critical_given']
        for actual, expected in zip(duplicated['naive_interval_using_given_critical'],
                                    (float(copy_mean) - nominal * naive_se, float(copy_mean) + nominal * naive_se)):
            self.assertAlmostEqual(actual, expected, places=12)
        self.assertEqual(duplicated['independent_randomization_decisions'], n)

    def test_adaptation_reexecutes_from_new_cwd_and_one_pen_perturbation_changes_estimate(self):
        adaptation = self.manifest['adaptation']
        original_paths = [QUALITY / adaptation[name] for name in ('input', 'script')]
        original = snapshot(original_paths)
        with tempfile.TemporaryDirectory(prefix='rwt quality adaptation ') as temporary:
            base = Path(temporary)
            results = []
            for changed in (False, True):
                work = base / ('changed pen means' if changed else 'original pen means')
                inputs, cwd, output = work / 'copied inputs', work / 'unrelated cwd', work / 'fresh outputs'
                for directory in (inputs, cwd, output):
                    directory.mkdir(parents=True)
                source, script = inputs / 'pen-summary.csv', inputs / 'calculate.py'
                shutil.copyfile(original_paths[0], source)
                shutil.copyfile(original_paths[1], script)
                if changed:
                    with source.open(encoding='utf-8', newline='') as stream:
                        rows = list(csv.DictReader(stream))
                    target = next(row for row in rows if row['treatment'] == 'B')
                    target['mean_live_weight_kg'] = str(float(Fraction(target['mean_live_weight_kg']) + Fraction(1, 100)))
                    with source.open('w', encoding='utf-8', newline='') as stream:
                        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n')
                        writer.writeheader()
                        writer.writerows(rows)
                before = snapshot([source, script])
                destination = output / 'results.json'
                receipt = self.run_python(script, [source, destination], cwd)
                self.assertEqual(snapshot([source, script]), before)
                self.assertEqual(sha(script), original[str(original_paths[1])][0])
                result = read(destination)
                self.assertEqual(receipt['output_sha256'], sha(destination))
                self.assertEqual(result['input_sha256'], sha(source))
                if not changed:
                    self.assert_same_result(result, read(QUALITY / adaptation['result']))
                with source.open(encoding='utf-8', newline='') as stream:
                    rows = list(csv.DictReader(stream))
                cells = {}
                for row in rows:
                    cells.setdefault(row['block'], {})[row['treatment']] = Fraction(row['mean_live_weight_kg'])
                independent = [cells[block]['B'] - cells[block]['control'] for block in sorted(cells)]
                self.assertAlmostEqual(result['mean_B_minus_control_kg'], float(sum(independent) / 4), places=12)
                self.assertEqual(result['checks']['blocks'], len(independent))
                for index, row in enumerate(result['leave_one_block_out']):
                    self.assertAlmostEqual(row['mean_B_minus_control_kg'],
                                           float((sum(independent) - independent[index]) / 3), places=12)
                results.append(result)
            baseline, changed = results
            self.assertAlmostEqual(changed['mean_B_minus_control_kg'] - baseline['mean_B_minus_control_kg'],
                                   0.0025, places=12)
            self.assertNotEqual(changed['input_sha256'], baseline['input_sha256'])
            self.assertEqual(changed['not_identified'], baseline['not_identified'])
        self.assertEqual(snapshot(original_paths), original)

    def test_adaptation_receipt_binds_decision_history_commands_and_registry_scope(self):
        adaptation = self.manifest['adaptation']
        receipt = read(QUALITY / adaptation['receipt'])
        result = read(QUALITY / adaptation['result'])
        self.assertTrue(receipt['synthetic'])
        self.assertTrue(receipt['frozen_stage1_unchanged'])
        inputs = {row['path']: row['sha256'] for row in receipt['inputs']}
        outputs = {row['path']: row['sha256'] for row in receipt['outputs']}
        self.assertEqual(len(inputs), 3)
        self.assertEqual(len(outputs), 3)
        self.assertEqual(inputs['inputs/stage1-report.md'], adaptation['original_stage1_report_sha256'])
        for recorded, field in [('inputs/resource-update.md', 'request'), ('inputs/pen-summary.csv', 'input')]:
            self.assertEqual(inputs[recorded], sha(QUALITY / adaptation[field]))
        for recorded, field in [('stage2.md', 'report'), ('stage2_compute.py', 'script'),
                                ('practice-project/outputs/summary-results.json', 'result')]:
            self.assertEqual(outputs[recorded], sha(QUALITY / adaptation[field]))
        expected_guidance = {name: self.manifest['guidance_sha256'][name]
                             for name in self.manifest['guidance_groups']['adaptation']}
        self.assertEqual(receipt['guidance_sha256'], expected_guidance)
        decision = receipt['decision']
        self.assertEqual(decision['id'], 'D_PRIORITY')
        self.assertEqual((decision['before']['version'], decision['after']['version']), (1, 2))
        self.assertTrue(decision['before']['choice'])
        self.assertTrue(decision['after']['choice'])
        self.assertNotEqual(decision['before']['choice'], decision['after']['choice'])
        self.assertTrue(decision['old_version_preserved_in_history'])
        commands = {row['name']: row for row in receipt['commands']}
        self.assertEqual(len(commands), len(receipt['commands']))
        for row in commands.values():
            self.assertEqual(row['exit_code'], 0)
            self.assertGreaterEqual(len(row['argv']), 3)
        names = [row['name'] for row in receipt['commands']]
        sequence = ['register-stage1', 'show-decision-v1', 'minimum-calculation',
                    'replace-decision-v2', 'show-decision-v2', 'save-checkpoint',
                    'final-check', 'final-resume', 'final-decision-history']
        self.assertEqual([names.index(name) for name in sequence], sorted(names.index(name) for name in sequence))
        replacement = commands['replace-decision-v2']['argv']
        self.assertEqual(replacement[2], 'register')
        self.assertIn('--replace', replacement)
        self.assertEqual(replacement[replacement.index('--expected-version') + 1], '1')
        for name, operation in [('final-check', 'check'), ('final-resume', 'resume')]:
            self.assertEqual(commands[name]['argv'][2], operation)
            self.assertIn('--root', commands[name]['argv'])
        for field in ('exit_code', 'passed', 'errors', 'warnings', 'checkpoint_status',
                      'activity_effective_status', 'scientific_validity'):
            expected = {'exit_code': 0, 'passed': True, 'errors': [], 'warnings': [],
                        'checkpoint_status': 'current', 'activity_effective_status': 'done',
                        'scientific_validity': 'not-assessed'}[field]
            self.assertEqual(receipt['check'][field], expected)
        self.assertEqual(receipt['resume']['exit_code'], 0)
        self.assertTrue(receipt['resume']['passed'])
        self.assertFalse(receipt['resume']['needs_review'])
        checkpoint = commands['save-checkpoint']['argv']
        self.assertEqual(receipt['resume']['next_action'], checkpoint[checkpoint.index('--next-action') + 1])
        self.assertTrue(receipt['boundaries'])
        self.assertTrue(all(value is False for value in receipt['boundaries'].values()))
        minimum = receipt['minimum_calculation']
        self.assertEqual((minimum['input_rows'], minimum['block_differences'], minimum['bird_records_reconstructed']), (8, 4, 0))
        self.assertEqual(minimum['reported_bird_count_total'], result['checks']['sum_of_reported_counts'])
        self.assertEqual(minimum['pens_per_treatment'], result['checks']['pens_per_treatment'])
        self.assertAlmostEqual(minimum['mean_B_minus_control_g'], 1000 * result['mean_B_minus_control_kg'], places=8)
        self.assertEqual(minimum['not_identified'], result['not_identified'])
        self.assertEqual(len(minimum['leave_one_block_out_g']), len(result['leave_one_block_out']))
        for actual, expected in zip(minimum['leave_one_block_out_g'], result['leave_one_block_out']):
            self.assertAlmostEqual(actual, 1000 * expected['mean_B_minus_control_kg'], places=8)
        interval = result['conditional_normal_block_difference_interval']['bounds_kg']
        self.assertEqual(len(minimum['conditional_95_percent_interval_g']), len(interval))
        for actual, expected in zip(minimum['conditional_95_percent_interval_g'], interval):
            self.assertAlmostEqual(actual, 1000 * expected, places=8)

    def test_literature_preserves_source_identity_and_execution_record_closure_offline(self):
        literature = self.manifest['literature']
        audit = read(QUALITY / literature['independent_audit'])
        report = QUALITY / literature['report']
        text = report.read_text(encoding='utf-8')
        original = audit['original_report']
        self.assertEqual({original[key] for key in ('expected_sha256', 'observed_sha256_before', 'observed_sha256_after')},
                         {literature['original_report_sha256']})
        self.assertFalse(original['modified'])
        self.assertEqual(literature['original_report_sha256'], self.manifest['adaptation']['original_stage1_report_sha256'])
        public = audit['outputs']['public-notes.md']
        self.assertEqual(public['sha256'], sha(report))
        self.assertEqual(public['bytes'], len(report.read_bytes()))
        source_identity = {
            'S1': ('https://arriveguidelines.org/arrive-guidelines/study-design/1b/explanation', None),
            'S2': ('https://pmc.ncbi.nlm.nih.gov/articles/PMC10239017/', '10.1016/j.psj.2023.102698'),
            'S3': ('https://pmc.ncbi.nlm.nih.gov/articles/PMC13087773/', '10.1016/j.psj.2026.106879'),
            'S4': ('https://fieldreport.caes.uga.edu/publications/B1417/pen-size-optimization-workbook-of-experimental-research-design-power-for-poultry/', None),
            'S5': ('https://pubmed.ncbi.nlm.nih.gov/17517755/', '10.3168/jds.2006-612'),
            'S6': ('https://academic.oup.com/jas/article/doi/10.1093/jas/skae088/7640097', '10.1093/jas/skae088'),
            'S7': ('https://scholarworks.uark.edu/poscpub/4/', '10.1016/j.japr.2022.100324'),
        }
        sources = {source['id']: source for source in audit['sources']}
        self.assertEqual(len(sources), len(audit['sources']))
        self.assertEqual(set(sources), set(source_identity))
        links = set(re.findall(r'\]\((https://[^\s)]+)\)', text))
        for source_id, (url, doi) in source_identity.items():
            source = sources[source_id]
            self.assertEqual((source['url'], source.get('doi')), (url, doi))
            self.assertIn(url, links)
            if doi is not None:
                self.assertIn('https://doi.org/' + doi, links)
            self.assertTrue(source['anchors'])
            self.assertTrue(source['audit_access'])
        queries = re.findall(r'^\| [A-E] \| Q(\d+) \| `(.+)` \|$', text, re.M)
        self.assertEqual([int(number) for number, _ in queries], list(range(1, 14)))
        self.assertEqual(len({expression for _, expression in queries}), 13)
        self.assertEqual(literature['performed_queries'], len(queries))
        self.assertEqual(audit['scope']['primary_sources'], ['S1', 'S2', 'S3', 'S4'])
        self.assertEqual(literature['primary_sources_checked_by_auditor'], len(audit['scope']['primary_sources']))
        self.assertEqual(audit['scope']['web_search_queries_executed_by_auditor'], 0)
        self.assertFalse(audit['scope']['original_13_queries_replayed'])
        self.assertTrue(audit['scope']['original_search_counts_and_execution_not_independently_reconstructed'])
        self.assertFalse(literature['network_required_for_ci'])
        for field in ('data_eligibility_confirmed', 'global_novelty_confirmed', 'feed_efficacy_assessed'):
            self.assertFalse(audit['recommendation_assessment'][field])

    def test_delivery_regenerates_csv_and_tex_in_isolated_output_without_tex_installation(self):
        delivery = self.manifest['delivery']
        paths = [ROOT / name for name in self.manifest['guidance_groups']['delivery']]
        before = snapshot(paths)
        with tempfile.TemporaryDirectory(prefix='rwt quality delivery ') as temporary:
            base = Path(temporary)
            scripts, inputs, cwd = base / 'copied scripts', base / 'copied inputs', base / 'new cwd'
            for directory in (scripts, inputs, cwd):
                directory.mkdir()
            analyze, build = scripts / 'analyze.py', scripts / 'build.py'
            observations = inputs / 'observations.csv'
            shutil.copyfile(ROOT / 'examples/paired-pens/analyze.py', analyze)
            shutil.copyfile(ROOT / 'examples/submission-table/build.py', build)
            shutil.copyfile(ROOT / 'examples/paired-pens/observations.csv', observations)
            copied_before = snapshot([analyze, build, observations])
            paired, tables = base / 'new paired analysis', base / 'new editable tables'
            self.run_python(analyze, ['--input', observations, '--output', paired], cwd)
            csv_path = paired / 'paired-differences.csv'
            self.assertEqual(sha(csv_path), delivery['input_sha256'])
            csv_before = snapshot([csv_path])
            generated = self.run_python(build, ['--data', csv_path, '--output', tables], cwd)
            self.assertEqual(snapshot([csv_path]), csv_before)
            self.assertEqual(snapshot([analyze, build, observations]), copied_before)
            self.assertEqual(generated['input_sha256'], delivery['input_sha256'])
            self.assertEqual((tables / 'paired-differences.csv').read_bytes(), csv_path.read_bytes())
            self.assertEqual(sha(tables / 'main.tex'), delivery['tex_sha256'])
            table_manifest = read(tables / 'manifest.json')
            self.assertEqual(table_manifest['input']['sha256'], delivery['input_sha256'])
            self.assertEqual(set(table_manifest['files']), {'main.tex', 'paired-differences.csv'})
            for name, item in table_manifest['files'].items():
                self.assertEqual(item['sha256'], sha(tables / name))
                self.assertEqual(item['bytes'], len((tables / name).read_bytes()))
            self.assertEqual(table_manifest['checks']['compilation'], 'not-run')
            self.assertEqual(table_manifest['checks']['visual_review'], 'not-run')
        self.assertEqual(snapshot(paths), before)


if __name__ == '__main__':
    unittest.main()
