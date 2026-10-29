"""Original hand-calculable synthetic data; no real input and no network required."""
import contextlib
import hashlib
import importlib.util
import io
import json
import math
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / 'examples/public-penguins'
spec = importlib.util.spec_from_file_location('analyze', EXAMPLE/'analyze.py')
analysis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analysis)
FIXTURE = EXAMPLE/'synthetic.csv'


class AnalysisTests(unittest.TestCase):
    def test_publication_record_closes_resources_and_frozen_review_outputs(self):
        root = Path(__file__).resolve().parents[1]
        evidence = root/'evals/public-data'
        record = json.loads((evidence/'recording.json').read_text(encoding='utf-8'))
        expected = {p.relative_to(root).as_posix() for directory in (EXAMPLE, evidence)
                    for p in directory.rglob('*') if p.is_file()
                    and '__pycache__' not in p.parts and p != evidence/'recording.json'}
        expected.add('tests/test_public_penguins.py')
        self.assertEqual(set(record['published_files']), expected)
        for name, identity in record['published_files'].items():
            data = (root/name).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), identity['sha256'], name)
            self.assertEqual(len(data), identity['bytes'], name)
        review = json.loads((evidence/'assessment.json').read_text(encoding='utf-8'))
        self.assertEqual(review['comparison_summary']['failures'], 0)
        self.assertEqual(review['source']['sha256'], analysis.PUBLIC_INPUT_SHA256)
        summary = json.loads((EXAMPLE/'observed/summary.json').read_text(encoding='utf-8'))
        self.assertEqual(summary['input_sha256'], review['source']['sha256'])
        self.assertEqual(summary['n_complete_overall'], review['scientific_summary']['rows_included'])
        for path in (EXAMPLE/'observed').iterdir():
            data = path.read_bytes()
            if path.suffix == '.csv':
                self.assertNotIn(b'\r', data)
                data = data.replace(b'\n', b'\r\n')
            self.assertEqual(hashlib.sha256(data).hexdigest(),
                             review['reviewed_snapshot_sha256']['real-results-v2/'+path.name])
        self.assertEqual(record['parent_completion']['final_record_count'], 36)
        self.assertEqual(record['parent_completion']['visual_activity_version'], 2)
        self.assertTrue(record['parent_completion']['final_project_sha256_size_mode_mtime_unchanged'])

    def setUp(self):
        self.rows = analysis.read_rows(FIXTURE)
        self.summary,self.grouped,self.strata,self.audit = analysis.compute(self.rows, 'synthetic')

    def test_hand_calculated_means_standard_deviation_and_differences(self):
        female = next(r for r in self.grouped if r['species']=='Adelie' and r['sex']=='female')
        adelie = self.summary['species'][0]
        self.assertEqual(female['n'],3)
        self.assertEqual(female['mean_g'],1400)
        self.assertAlmostEqual(female['sd_g'], math.sqrt(280000))
        self.assertEqual(female['median_g'],1200)
        self.assertAlmostEqual(adelie['male_minus_female_g'],1400/3)
        self.assertEqual(adelie['stratum_min_difference_g'],400)
        self.assertEqual(adelie['stratum_max_difference_g'],600)
        self.assertAlmostEqual(adelie['standardized_difference_g'],1400/3)

    def test_missing_flow_empty_and_one_sex_cells(self):
        s=self.summary
        self.assertEqual((s['n_raw'],s['n_complete_overall'],s['n_excluded_overall']),(12,9,3))
        self.assertEqual(s['missing_counts']['sex'],2)
        self.assertEqual(s['missing_counts']['body_mass_g'],2)
        self.assertEqual(s['n_missing_sex_and_mass'],1)
        self.assertEqual(s['stratum_status_counts'],{'comparable':3,'no_observations':22,'no_complete_sex_comparison':2})
        self.assertEqual(len(self.strata),27)
        for row in self.strata:
            if row['status']!='comparable':
                self.assertIsNone(row['male_minus_female_g'])
        gentoo=self.summary['species'][2]
        self.assertIsNone(gentoo['male_minus_female_g'])
        self.assertIsNone(gentoo['standardized_difference_g'])

    def test_exact_missing_sex_assignment_bounds(self):
        b=self.summary['missing_sex_sensitivity']['Adelie']
        self.assertEqual(b['assignments'],2)
        self.assertAlmostEqual(b['min_difference_g'],1175/3)
        self.assertAlmostEqual(b['max_difference_g'],425)

    def test_common_weight_is_not_mixed_sex_composition(self):
        # Add one low-stratum female; direct means now mix strata differently.
        row=dict(self.rows[0]); row['csv_row']=100
        summary,*_=analysis.compute(self.rows+[row],'synthetic')
        s=summary['species'][0]
        self.assertAlmostEqual(s['male_minus_female_g'],1700/3)
        self.assertAlmostEqual(s['standardized_difference_g'],10100/21)

    def test_cli_outputs_hash_native_svg_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            out=Path(directory)/'results'
            original=hashlib.sha256(FIXTURE.read_bytes()).hexdigest()
            with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(analysis.main(['--input',str(FIXTURE),'--output',str(out)]),0)
                before={p.name:p.read_bytes() for p in out.iterdir()}
                self.assertEqual(analysis.main(['--input',str(FIXTURE),'--output',str(out)]),2)
            self.assertEqual(before,{p.name:p.read_bytes() for p in out.iterdir()})
            self.assertEqual(original,hashlib.sha256(FIXTURE.read_bytes()).hexdigest())
            for csv_path in out.glob('*.csv'):
                self.assertNotIn(b'\r\n', csv_path.read_bytes())
            data=json.loads((out/'summary.json').read_text())
            self.assertEqual(data['input_sha256'],original)
            self.assertFalse(data['matches_pinned_public_input'])
            for name in ('species-mass.svg','stratum-differences.svg'):
                root=ET.fromstring((out/name).read_text())
                self.assertTrue(root.findall('.//{http://www.w3.org/2000/svg}text'))
                self.assertFalse(root.findall('.//{http://www.w3.org/2000/svg}image'))

    def test_validation_rejects_nonfinite_unknown_level_duplicate_header(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'bad.csv'
            cases=[('species,island,year,sex,body_mass_g\nAdelie,Biscoe,2007,male,nan\n'),
                   ('species,island,year,sex,body_mass_g\nAdelie,Biscoe,2007,unknown,2000\n'),
                   ('species,island,year,sex,body_mass_g,sex\nAdelie,Biscoe,2007,male,2000,male\n')]
            for content in cases:
                path.write_text(content)
                with self.assertRaises(ValueError):
                    analysis.read_rows(path)


if __name__=='__main__':
    unittest.main()
