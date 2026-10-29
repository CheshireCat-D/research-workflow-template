"""Actual CSV-to-source delivery; TeX rendering is checked separately when available."""
from pathlib import Path
from decimal import Decimal
from fractions import Fraction
import csv
import hashlib
import io
import json
import re
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'examples/submission-table/build.py'
FIELDS = ('block', 'control_mean_g', 'treatment_mean_g', 'difference_g')


def rows():
    controls = (1000, 1050, 1100, 1000, 950, 1000)
    changes = (20, -10, 30, 0, 10, -20)
    return [dict(zip(FIELDS, (f'B{i+1}', str(control), str(control+change), str(change))))
            for i, (control, change) in enumerate(zip(controls, changes))]


def csv_bytes(values, fields=FIELDS):
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
    writer.writeheader()
    writer.writerows(values)
    return stream.getvalue().encode('utf-8')


class SubmissionTable(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='rw-table-source-')
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.input = self.base / 'paired input.csv'
        self.output = self.base / 'editable delivery'

    def invoke(self, data, expected=0, output=None):
        self.input.write_bytes(data)
        before = (self.input.read_bytes(), self.input.stat().st_mtime_ns)
        command = [sys.executable, '-X', 'utf8', '-I', '-B', str(SCRIPT),
                   '--data', str(self.input), '--output', str(output or self.output)]
        result = subprocess.run(command, cwd=self.base, capture_output=True, text=True,
                                encoding='utf-8', timeout=20)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        self.assertEqual((self.input.read_bytes(), self.input.stat().st_mtime_ns), before)
        return json.loads(result.stdout)

    def manifest(self, output=None):
        return json.loads(((output or self.output) / 'manifest.json').read_text(encoding='utf-8'))

    def test_real_csv_is_copied_and_every_table_row_retains_its_values(self):
        data = csv_bytes(rows())
        result = self.invoke(data)
        self.assertTrue(result['passed'])
        self.assertEqual({p.name for p in self.output.iterdir()}, {'main.tex', 'paired-differences.csv', 'manifest.json'})
        self.assertEqual((self.output / 'paired-differences.csv').read_bytes(), data)
        text = (self.output / 'main.tex').read_text(encoding='utf-8')
        actual = re.findall(r'^(B[1-6]) & (-?[0-9.]+) & (-?[0-9.]+) & (-?[0-9.]+) \\\\$', text, re.M)
        expected = [(r['block'], *(r[f] for f in FIELDS[1:])) for r in rows()]
        self.assertEqual(actual, expected)
        analysis = self.manifest()['analysis']
        self.assertEqual(Decimal(analysis['mean_difference_g']), Decimal(5))
        self.assertEqual((analysis['randomization_extreme'], analysis['randomization_total']), (44, 64))
        self.assertEqual(Decimal(analysis['exact_two_sided_p']), Decimal('0.6875'))
        self.assertEqual(self.manifest()['checks']['compilation'], 'not-run')

    def test_manifest_binds_actual_source_and_outputs_and_is_deterministic(self):
        data = csv_bytes(rows())
        self.invoke(data)
        manifest = self.manifest()
        self.assertEqual(manifest['input']['sha256'], hashlib.sha256(data).hexdigest())
        for name, item in manifest['files'].items():
            content = (self.output / name).read_bytes()
            self.assertEqual(item['bytes'], len(content))
            self.assertEqual(item['sha256'], hashlib.sha256(content).hexdigest())
        self.assertNotIn('manifest.json', manifest['files'])
        second = self.base / 'another delivery'
        self.invoke(data, output=second)
        self.assertEqual({p.name: p.read_bytes() for p in self.output.iterdir()},
                         {p.name: p.read_bytes() for p in second.iterdir()})

    def test_changed_measurements_change_the_actual_rows_and_summary(self):
        initial = rows()
        changed = rows()
        changed[0]['treatment_mean_g'] = '1022'
        changed[0]['difference_g'] = '22'
        self.invoke(csv_bytes(initial))
        second = self.base / 'changed delivery'
        self.invoke(csv_bytes(changed), output=second)
        mean = Decimal(self.manifest(second)['analysis']['mean_difference_g'])
        self.assertLess(abs(Fraction(mean) - Fraction(32, 6)), Fraction(1, 10**30))
        self.assertNotEqual(self.manifest()['input']['sha256'], self.manifest(second)['input']['sha256'])
        self.assertIn('B1 & 1000 & 1022 & 22', (second / 'main.tex').read_text(encoding='utf-8'))
        self.assertIn('Feed B minus control & 5.33', (second / 'main.tex').read_text(encoding='utf-8'))

    def test_input_decimal_precision_negative_zero_and_tex_labels_are_preserved(self):
        values = rows()
        values[0].update(block=r'A&B_1%#$\{}~^', control_mean_g='1000.00', treatment_mean_g='1020.000', difference_g='20.000')
        values[3]['difference_g'] = '-0.00'
        self.invoke(csv_bytes(values))
        text = (self.output / 'main.tex').read_text(encoding='utf-8')
        self.assertIn(r'A\&B\_1\%\#\$\textbackslash{}\{\}\textasciitilde{}\textasciicircum{} & 1000.00 & 1020.000 & 20.000', text)
        self.assertIn('B4 & 1000 & 1000 & -0.00', text)

    def test_invalid_material_is_rejected_before_output_creation(self):
        invalid = []
        one = rows(); one[1]['block'] = 'B1'; invalid.append(csv_bytes(one))
        one = rows(); one[0]['difference_g'] = '19'; invalid.append(csv_bytes(one))
        for token in ('NaN', 'Infinity', '1e3', '', '1.0000000000001'):
            one = rows(); one[0]['control_mean_g'] = token; invalid.append(csv_bytes(one))
        invalid += [csv_bytes(rows()[:-1]), b'block,control_mean_g,control_mean_g,difference_g\nB1,1,2,1\n', b'\xffbad encoding']
        for number, data in enumerate(invalid):
            with self.subTest(number=number):
                report = self.invoke(data, expected=2)
                self.assertFalse(report['passed'])
                self.assertFalse(self.output.exists())

    def test_existing_output_and_input_are_not_overwritten(self):
        self.output.mkdir()
        marker = self.output / 'author-notes.txt'
        marker.write_text('Keep this original.', encoding='utf-8')
        report = self.invoke(csv_bytes(rows()), expected=2)
        self.assertFalse(report['passed'])
        self.assertEqual(marker.read_text(encoding='utf-8'), 'Keep this original.')
        self.assertEqual({p.name for p in self.output.iterdir()}, {'author-notes.txt'})
        self.invoke(csv_bytes(rows()), expected=2, output=self.input)

    def test_constant_differences_keep_exact_test_without_a_zero_width_reference_interval(self):
        values = rows()
        for row in values:
            row['treatment_mean_g'] = row['control_mean_g']
            row['difference_g'] = '0'
        self.invoke(csv_bytes(values))
        analysis = self.manifest()['analysis']
        self.assertEqual(Decimal(analysis['mean_difference_g']), Decimal(0))
        self.assertIsNone(analysis['reference_95_interval_g'])
        self.assertEqual(Decimal(analysis['exact_two_sided_p']), Decimal(1))
        text = (self.output / 'main.tex').read_text(encoding='utf-8')
        self.assertIn(r'Feed B minus control & 0.00 & \multicolumn{1}{c}{---} & \multicolumn{1}{c}{---} & 1.0000', text)


if __name__ == '__main__':
    unittest.main()
