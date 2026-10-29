"""First-use evidence identity and the real packaged offline guide examples.

No model calls, network requests, scientific-quality keyword scores or global
skill installation. The published cases are excerpts, not runnable projects.
"""
from pathlib import Path
import csv
from datetime import datetime
from decimal import Decimal
import hashlib
import importlib.util
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
import unittest
import zipfile

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'evals/usability'
ORIGINAL_IDENTITIES = {
    'cases/zh-interest/request.md': '6856788fa4bd41ffcdf58b9446a2bb8ffb158f0a4c8bd0c2bb3db00ee69a2063',
    'cases/zh-interest/first-output.md': '2ac68d45b271bc50ef819f18281089dc73245d87bae704202fe83b8182ed6007',
    'cases/en-pilot/request.md': '56a922934258fc52b62da929e62b0863f9f9efa6778af2a3b46ee4f1cf76625b',
    'cases/en-pilot/input.csv': '09ab10d28406c6dd4f3091f8a66b2f71ff14ea24d12fbf30606062a7fd9a9857',
    'cases/en-pilot/first-output.md': '0c1f183043f14686865acaef86b9b8f156ed65fabd4dd3c6e5b9f64e11836745',
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def snapshot(root):
    return {p.relative_to(root).as_posix(): (digest(p.read_bytes()), p.stat().st_mtime_ns)
            for p in root.rglob('*') if p.is_file()}


class FirstUse(unittest.TestCase):
    def setUp(self):
        self.record = json.loads((EVIDENCE / 'recording.json').read_text(encoding='utf-8'))

    def test_published_case_review_identity_and_manifest_closure(self):
        record = self.record
        self.assertEqual(record['tested_distribution']['commit'],
                         'df511bba4f9e9c0719e001ad62c8c0d34cf4ae9a')
        self.assertEqual(record['tested_distribution']['user_zip_sha256'],
                         'e8c3f21a12b084fc8f6e2862ed76bb531f0fd34c3d21d31c82630b14f75c6550')
        self.assertEqual(record['study_scope']['human_participants'], 0)
        self.assertEqual(record['study_scope']['multilingual_ai_scenarios'], 2)
        self.assertFalse(record['study_scope']['english_only_human_usability_tested'])
        self.assertEqual(record['independent_review']['original_assessment_json_sha256'],
                         '1326544f8bdeaaa51b59647b0446123e3a0b8cefbf2b057413a5a3a5d8f6bd5f')
        self.assertEqual(record['independent_review']['original_assessment_md_sha256'],
                         '63417afa7ee028b705485dae56b980ae4abaaa15765351bcc6a4c0813e5a2332')
        published = record['published_files']
        expected = {p.relative_to(ROOT).as_posix() for p in EVIDENCE.rglob('*')
                    if p.is_file() and p.name != 'recording.json'}
        expected.add('tests/test_first_use.py')
        self.assertEqual(set(published), expected)
        for name, identity in published.items():
            path = ROOT / name
            self.assertFalse(path.is_symlink(), name)
            self.assertEqual(path.stat().st_size, identity['bytes'], name)
            self.assertEqual(digest(path.read_bytes()), identity['sha256'], name)
        originals = record['original_case_identities']
        self.assertEqual(set(originals), set(ORIGINAL_IDENTITIES))
        for name, checksum in ORIGINAL_IDENTITIES.items():
            self.assertEqual(digest((EVIDENCE / name).read_bytes()), checksum, name)
            self.assertEqual(originals[name]['sha256'], checksum, name)
            self.assertEqual(originals[name]['published_bytes'], 'unchanged', name)
        for role, reference in record['original_audited_source_aliases'].items():
            section, name = reference.split('/', 1)
            self.assertEqual(record[section][name]['sha256'], ORIGINAL_IDENTITIES[name], role)
        self.assertEqual(set(record['historical_constraints']['applies_to_case_ids']),
                         {case['id'] for case in record['cases']})
        self.assertEqual({case['id'] for case in record['cases']}, {'zh-interest', 'en-pilot'})
        self.assertTrue(record['independent_review']['current_reexecution']['sha256_size_mtime_unchanged'])
        self.assertEqual(record['independent_review']['current_reexecution']['commands_passed'], 6)

    def test_en_original_csv_independent_descriptive_arithmetic(self):
        with (EVIDENCE / 'cases/en-pilot/input.csv').open(newline='', encoding='utf-8') as stream:
            reader = csv.DictReader(stream)
            self.assertEqual(reader.fieldnames, ['method', 'seed', 'accuracy', 'train_seconds'])
            rows = list(reader)
        parsed = {}
        for row in rows:
            key = row['method'], int(row['seed'])
            self.assertNotIn(key, parsed)
            accuracy, seconds = Decimal(row['accuracy']), Decimal(row['train_seconds'])
            self.assertTrue(accuracy.is_finite() and 0 <= accuracy <= 1)
            self.assertTrue(seconds.is_finite() and seconds > 0)
            parsed[key] = accuracy, seconds
        self.assertEqual(set(parsed), {(method, seed) for method in ('baseline', 'candidate')
                                       for seed in (1, 2, 3)})
        means = {method: [sum(parsed[method, seed][column] for seed in (1, 2, 3)) / 3
                          for column in (0, 1)] for method in ('baseline', 'candidate')}
        self.assertEqual(means['baseline'], [Decimal('0.79'), Decimal(19)])
        self.assertEqual(means['candidate'][0], Decimal('2.42') / 3)
        self.assertEqual(means['candidate'][1], Decimal(21))
        actual = self.record['independent_review']['csv_recomputation']
        self.assertAlmostEqual(float((means['candidate'][0] - means['baseline'][0]) * 100),
                               actual['accuracy_difference_pp'])
        self.assertAlmostEqual(float((means['candidate'][1] / means['baseline'][1] - 1) * 100),
                               actual['training_time_increase_percent'])
        self.assertEqual([(parsed['candidate', seed][0] - parsed['baseline', seed][0]) * 100
                          for seed in (1, 2, 3)], list(map(Decimal, ('3', '2', '0'))))
        self.assertEqual([parsed['candidate', seed][1] - parsed['baseline', seed][1]
                          for seed in (1, 2, 3)], [3, 2, 1])

    def test_corrected_registration_event_is_not_help(self):
        timing = self.record['en_registration_correction']
        start = datetime.fromisoformat(timing['start_at_utc'])
        help_event, registration = timing['help_event'], timing['registration_event']
        self.assertIn('--help', help_event['command_tokens'])
        self.assertFalse(help_event['is_registration'])
        self.assertNotIn('--help', registration['command_tokens'])
        self.assertIn('--file', registration['command_tokens'])
        self.assertTrue(registration['is_registration'])
        self.assertEqual(registration['exit_code'], 0)
        self.assertTrue(registration['registered'])
        self.assertEqual(registration['registered_count'], 13)
        self.assertEqual((datetime.fromisoformat(help_event['ended_at_utc']) - start).total_seconds(),
                         timing['original_reported_seconds'])
        self.assertEqual((datetime.fromisoformat(registration['ended_at_utc']) - start).total_seconds(),
                         timing['corrected_seconds'])
        self.assertEqual(timing['corrected_seconds'], 147.135799)

    def test_bilingual_offline_examples_execute_from_actual_user_zip(self):
        spec = importlib.util.spec_from_file_location('first_use_package', ROOT / 'tools/package_user.py')
        package = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(package)
        with tempfile.TemporaryDirectory(prefix='rw-first-use-guide-') as temporary:
            base = Path(temporary)
            archive = base / 'user.zip'
            self.assertTrue(package.build(archive, ROOT)['passed'])
            self.assertTrue(package.verify(archive)['passed'])
            for language, guide in [('zh', '中文介绍与使用说明.md'), ('en', 'USER_GUIDE.en.md')]:
                with self.subTest(language=language):
                    with zipfile.ZipFile(archive) as zipped:
                        self.assertIsNone(zipped.testzip())
                        zipped.extractall(base / language)
                    toolkit = base / language / package.ARCHIVE_ROOT
                    text = (toolkit / guide).read_text(encoding='utf-8')
                    blocks = list(re.finditer(r'^```json[^\S\n]*\n(.*?)^```[^\S\n]*$',
                                              text, re.MULTILINE | re.DOTALL))
                    self.assertTrue(blocks, 'Keep the runnable minimal statement example first')
                    block = blocks[0]
                    batch = json.loads(block.group(1))
                    self.assertIsInstance(batch, list)
                    self.assertEqual(len(batch), 1)
                    self.assertEqual(batch[0]['kind'], 'statement')
                    statement = batch[0]['record']
                    batch_file = toolkit / 'statement-batch.json'
                    batch_file.write_text(block.group(1), encoding='utf-8')
                    following = re.search(r'^```sh[^\S\n]*\n(.*?)^```[^\S\n]*$',
                                          text[block.end():], re.MULTILINE | re.DOTALL)
                    self.assertIsNotNone(following, 'JSON example needs its actual CLI commands')
                    documented = [shlex.split(line) for line in following.group(1).splitlines()
                                  if line.strip()]
                    self.assertEqual(len(documented), 2)
                    project = base / language / 'new project'
                    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')

                    def invoke(script, *arguments):
                        result = subprocess.run([sys.executable, '-X', 'utf8', '-I', '-B', str(script),
                                                 *map(str, arguments)], cwd=toolkit, env=environment,
                                                capture_output=True, text=True, encoding='utf-8', timeout=30)
                        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                        return json.loads(result.stdout)

                    def guide_command(tokens, expected_subcommand):
                        self.assertEqual(tokens[:3], ['python3', 'tools/research.py', expected_subcommand])
                        return invoke(toolkit / tokens[1],
                                      *[str(project) if token == 'PROJECT' else token for token in tokens[2:]])

                    source_before = snapshot(toolkit)
                    self.assertTrue(invoke(toolkit / 'tools/research.py', 'init', '--output', project,
                                           '--title', 'Offline documented example', '--language', language)['initialized'])
                    invoke(toolkit / 'tools/connect_skills.py', 'install', '--root', project)
                    registered = guide_command(documented[0], 'register-batch')
                    self.assertTrue(registered['registered'])
                    self.assertEqual(registered['registered_count'], len(batch))
                    next_action = 'Continue after reading the saved synthetic record.'
                    invoke(toolkit / 'tools/research.py', 'checkpoint', '--root', project,
                           '--next-action', next_action)
                    before = snapshot(project)
                    shown = guide_command(documented[1], 'show')
                    self.assertEqual(shown['envelope']['data'], statement)
                    self.assertTrue(shown['read_only'])
                    local = project / '.agents/skills/_rw-runtime/tools'
                    resumed = invoke(local / 'research.py', 'resume', '--root', project)
                    self.assertTrue(resumed['passed'])
                    self.assertTrue(resumed['read_only'])
                    self.assertEqual(resumed['checkpoint']['status'], 'current')
                    self.assertEqual(resumed['next_action'], next_action)
                    self.assertEqual(resumed['counts']['statements'], 1)
                    self.assertEqual(resumed['scientific_validity'], 'not-assessed')
                    installed = invoke(local / 'connect_skills.py', 'check', '--installed-only', '--root', project)
                    self.assertTrue(installed['passed'])
                    self.assertTrue(installed['read_only'])
                    self.assertTrue(installed['installed_integrity'])
                    self.assertFalse(installed['source_comparison_performed'])
                    self.assertEqual(snapshot(project), before)
                    self.assertEqual(snapshot(toolkit), source_before)


if __name__ == '__main__':
    unittest.main()
