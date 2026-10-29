"""Recompute the public paired-pen example from actual individual CSV inputs."""
from pathlib import Path
from decimal import Decimal
from fractions import Fraction
import csv
import hashlib
import json
import math
import random
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / 'examples/paired-pens'


class PairedPensExample(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='rwt paired pens ')
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)
        with (EXAMPLE / 'observations.csv').open(encoding='utf-8', newline='') as stream:
            self.rows = list(csv.DictReader(stream))

    def run_example(self, rows=None, expected=0, output=None):
        source = self.work / 'individual observations 数据.csv'
        arguments = []
        if rows is not None:
            with source.open('w', encoding='utf-8', newline='') as stream:
                writer = csv.DictWriter(stream, fieldnames=list(self.rows[0]), lineterminator='\n')
                writer.writeheader()
                writer.writerows(rows)
            arguments = ['--input', str(source)]
        else:
            source = EXAMPLE / 'observations.csv'
        before = (source.read_bytes(), source.stat().st_mtime_ns)
        if output is None:
            output = self.work / 'fresh output 结果'
        completed = subprocess.run([sys.executable, '-X', 'utf8', '-I', '-B',
                                    str(EXAMPLE / 'analyze.py'), *arguments, '--output', str(output)],
                                   cwd=self.work, capture_output=True, text=True, encoding='utf-8', timeout=30)
        self.assertEqual(completed.returncode, expected, completed.stdout + completed.stderr)
        self.assertEqual((source.read_bytes(), source.stat().st_mtime_ns), before)
        receipt = json.loads(completed.stdout)
        self.assertEqual(receipt['passed'], expected == 0)
        return output, receipt

    def assert_independent_summary(self, output, differences):
        result = json.loads((output / 'summary.json').read_text(encoding='utf-8'))
        total = sum(Fraction(d) for d in differences)
        count = len(differences)
        average = total / count
        sample_variance = (sum(Fraction(d) ** 2 for d in differences) - total ** 2 / count) / (count - 1)
        self.assertAlmostEqual(result['estimate_g'], float(average))
        self.assertAlmostEqual(result['standard_error_g'], math.sqrt(float(sample_variance / count)))
        extreme = 0
        for mask in range(1 << count):
            signed = sum((d if mask & (1 << i) else -d) for i, d in enumerate(differences))
            extreme += abs(signed) >= abs(total)
        self.assertEqual(result['randomization_test']['at_least_as_extreme'], extreme)
        self.assertEqual(result['randomization_test']['assignments'], 1 << count)
        self.assertEqual(result['randomization_test']['p_value'], extreme / (1 << count))
        return result

    def test_default_input_is_portable_and_matches_independent_statistics(self):
        output, receipt = self.run_example()
        result = self.assert_independent_summary(output, [20, -10, 30, 0, 10, -20])
        self.assertEqual(result['individual_observations'], 120)
        self.assertEqual(result['pens'], 12)
        self.assertEqual(result['matched_blocks'], 6)
        self.assertEqual(result['input_sha256'], hashlib.sha256((EXAMPLE / 'observations.csv').read_bytes()).hexdigest())
        self.assertFalse(result['significant_at_alpha'])
        lower, upper = result['reference_interval_95_g']
        self.assertAlmostEqual(lower, -14.633143069803243, places=10)
        self.assertAlmostEqual(upper, 24.633143069803243, places=10)
        # Independent closed-form CDF for df=5 checks the quantile, not its literal spelling.
        quantile = (upper - result['estimate_g']) / result['standard_error_g']
        theta = math.atan(quantile / math.sqrt(5))
        cdf = 0.5 + theta / math.pi + 2 * math.sin(2 * theta) / (3 * math.pi) + math.sin(4 * theta) / (12 * math.pi)
        self.assertAlmostEqual(cdf, 0.975, places=13)
        self.assertEqual(set(p.name for p in output.iterdir()), set(receipt['files']))
        with (output / 'paired-differences.csv').open(encoding='utf-8', newline='') as stream:
            pairs = list(csv.DictReader(stream))
        self.assertEqual([float(row['difference_g']) for row in pairs], [20, -10, 30, 0, 10, -20])

    def test_changed_actual_individual_data_changes_results(self):
        for row in self.rows:
            if row['block'] == 'B6' and row['treatment'] == 'B':
                row['gain_g'] = str(int(row['gain_g']) + 10)
        output, _ = self.run_example(self.rows)
        result = self.assert_independent_summary(output, [20, -10, 30, 0, 10, -10])
        self.assertAlmostEqual(result['estimate_g'], 20 / 3)
        self.assertNotEqual(result['input_sha256'], hashlib.sha256((EXAMPLE / 'observations.csv').read_bytes()).hexdigest())

    def test_microgram_changes_flow_into_submission_source_without_precision_loss(self):
        for change in ('0.000001', '-0.000001'):
            with self.subTest(change=change):
                rows = [dict(row) for row in self.rows]
                bird = next(row for row in rows if row['block'] == 'B4' and row['treatment'] == 'B')
                bird['gain_g'] = format(Decimal(bird['gain_g']) + Decimal(change), 'f')
                output, _ = self.run_example(rows, output=self.work / ('analysis ' + change))
                source = output / 'paired-differences.csv'
                before = (source.read_bytes(), source.stat().st_mtime_ns)
                with source.open(encoding='utf-8', newline='') as stream:
                    pair = next(row for row in csv.DictReader(stream) if row['block'] == 'B4')
                expected_difference = Decimal(change) / 10
                self.assertEqual(Decimal(pair['difference_g']), expected_difference)
                self.assertNotIn('e', pair['difference_g'].lower())
                self.assertEqual(Decimal(pair['treatment_mean_g']) - Decimal(pair['control_mean_g']),
                                 expected_difference)
                delivery = self.work / ('table delivery ' + change)
                completed = subprocess.run(
                    [sys.executable, '-X', 'utf8', '-I', '-B',
                     str(ROOT / 'examples/submission-table/build.py'),
                     '--data', str(source), '--output', str(delivery)],
                    cwd=self.work, capture_output=True, text=True, encoding='utf-8', timeout=30)
                self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
                self.assertTrue(json.loads(completed.stdout)['passed'])
                self.assertEqual((source.read_bytes(), source.stat().st_mtime_ns), before)
                self.assertEqual((delivery / 'paired-differences.csv').read_bytes(), before[0])
                manuscript = (delivery / 'main.tex').read_text(encoding='utf-8')
                self.assertIn('B4 & ' + ' & '.join(pair[field] for field in
                              ('control_mean_g', 'treatment_mean_g', 'difference_g')), manuscript)
                manifest = json.loads((delivery / 'manifest.json').read_text(encoding='utf-8'))
                self.assertEqual(manifest['input']['sha256'], hashlib.sha256(before[0]).hexdigest())
                expected_mean = Fraction(5) + Fraction(change) / 60
                self.assertLess(abs(Fraction(manifest['analysis']['mean_difference_g']) - expected_mean),
                                Fraction(1, 10**30))

    def test_row_order_does_not_change_paired_analysis(self):
        random.Random(27).shuffle(self.rows)
        output, _ = self.run_example(self.rows)
        self.assert_independent_summary(output, [20, -10, 30, 0, 10, -20])

    def test_constant_paired_differences_do_not_create_a_false_precision_interval(self):
        adjustments = {'B1': -15, 'B2': 15, 'B3': -25, 'B4': 5, 'B5': -5, 'B6': 25}
        for row in self.rows:
            if row['treatment'] == 'B':
                row['gain_g'] = str(int(row['gain_g']) + adjustments[row['block']])
        output, _ = self.run_example(self.rows)
        result = self.assert_independent_summary(output, [5, 5, 5, 5, 5, 5])
        self.assertIsNone(result['reference_interval_95_g'])
        self.assertEqual(result['standard_error_g'], 0)
        self.assertEqual(result['randomization_test']['p_value'], 2 / 64)

    def test_duplicate_individual_is_rejected_before_output(self):
        self.rows[1]['bird_id'] = self.rows[0]['bird_id']
        output, _ = self.run_example(self.rows, expected=2)
        self.assertFalse(output.exists())

    def test_invalid_designs_are_rejected_without_output(self):
        variants = [self.rows[:-1], [dict(row) for row in self.rows if row['block'] != 'B6']]
        mixed = [dict(row) for row in self.rows]
        mixed[0]['treatment'] = 'control' if mixed[0]['treatment'] == 'B' else 'B'
        variants.append(mixed)
        unknown = [dict(row) for row in self.rows]
        unknown[0]['treatment'] = 'other'
        variants.append(unknown)
        crossed = [dict(row) for row in self.rows]
        crossed[0]['block'] = 'B2'
        variants.append(crossed)
        for rows in variants:
            with self.subTest(rows=len(rows), first=rows[0]):
                output, _ = self.run_example(rows, expected=2)
                self.assertFalse(output.exists())

    def test_nonfinite_or_unsupported_numbers_are_rejected(self):
        for value in ('NaN', 'Infinity', '-inf', '1e999999999', '', 'not-a-number'):
            with self.subTest(value=value):
                rows = [dict(row) for row in self.rows]
                rows[0]['gain_g'] = value
                output, _ = self.run_example(rows, expected=2)
                self.assertFalse(output.exists())

    def test_existing_output_or_input_path_is_never_overwritten(self):
        target = self.work / 'already exists'
        target.mkdir()
        sentinel = target / 'do not change.txt'
        sentinel.write_text('original', encoding='utf-8')
        self.run_example(expected=2, output=target)
        self.assertEqual(sentinel.read_text(encoding='utf-8'), 'original')
        self.assertEqual(list(target.iterdir()), [sentinel])
        file_target = self.work / 'existing file'
        file_target.write_text('original file', encoding='utf-8')
        self.run_example(expected=2, output=file_target)
        self.assertEqual(file_target.read_text(encoding='utf-8'), 'original file')
        self.run_example(expected=2, output=EXAMPLE / 'observations.csv')


if __name__ == '__main__':
    unittest.main()
