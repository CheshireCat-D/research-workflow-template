"""Execute the shipped onboarding materials against fresh projects, without accounts."""
from pathlib import Path
import json
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / 'examples/synthetic'
CLI = ROOT / 'tools/research.py'


class OnboardingExamples(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='rw-onboarding-')
        self.addCleanup(self.temporary.cleanup)
        self.work = Path(self.temporary.name)
        self.project = self.work / 'project with spaces'

    def command(self, *args, expected=0):
        result = subprocess.run([sys.executable, '-B', str(CLI), *map(str, args)],
                                cwd=self.work, text=True, encoding='utf-8', capture_output=True, timeout=15)
        self.assertEqual(expected, result.returncode, result.stdout + result.stderr)
        return json.loads(result.stdout)

    def initialize(self, discipline, method, material):
        self.command('init', '--output', self.project, '--title', 'Synthetic onboarding',
                     '--discipline', discipline, '--method', method)
        (self.project / 'notes').mkdir()
        shutil.copyfile(EXAMPLES / material, self.project / 'notes' / material)

    def register(self, kind, data, version=None):
        record = self.work / 'input.json'
        record.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
        args = ['register', '--root', self.project, '--kind', kind, '--file', record]
        if version is not None:
            args += ['--replace', '--expected-version', str(version)]
        return self.command(*args)

    def test_finite_observation_onboarding_and_explicit_recovery(self):
        self.initialize('natural-sciences', 'formal-theory', 'finite-observations.txt')
        records = {}
        for kind in ('statement', 'evidence', 'relation', 'activity'):
            records[kind] = json.loads((EXAMPLES / ('math-' + kind + '.json')).read_text(encoding='utf-8'))
            self.register(kind, records[kind])
        activity = records['activity']['id']
        self.command('checkpoint', '--root', self.project, '--activity', activity,
                     '--next-action', 'Inspect the stated limitations')
        initial = self.command('resume', '--root', self.project)
        self.assertFalse(initial['needs_review'])
        self.assertEqual('not-assessed', initial['scientific_validity'])
        path = self.project / records['evidence']['location']['path']
        path.write_text(path.read_text(encoding='utf-8') + '\nSynthetic onboarding revision; no new mathematical result.\n', encoding='utf-8')
        drift = self.command('check', '--root', self.project, expected=1)
        self.assertEqual('stale', drift['activities'][0]['effective_status'])
        self.register('evidence', records['evidence'], version=1)
        self.assertEqual('stale', self.command('check', '--root', self.project, expected=1)['activities'][0]['effective_status'])
        self.register('activity', records['activity'], version=1)
        self.command('check', '--root', self.project, expected=1)
        self.command('checkpoint', '--root', self.project, '--activity', activity,
                     '--next-action', 'Continue within the reviewed scope')
        recovered = self.command('resume', '--root', self.project)
        self.assertFalse(recovered['needs_review'])
        self.assertEqual('not-assessed', recovered['scientific_validity'])

    def test_fictional_history_onboarding_preserves_competing_interpretations(self):
        self.initialize('humanities', 'historical-interpretive', 'fictional-excerpts.txt')
        rows = json.loads((EXAMPLES / 'history-records.json').read_text(encoding='utf-8'))
        for row in rows:
            self.register(row['kind'], row['record'])
        activities = [row['record'] for row in rows if row['kind'] == 'activity']
        self.command('checkpoint', '--root', self.project, '--activity', activities[0]['id'],
                     '--next-action', 'Compare the interpretations and their limits')
        result = self.command('resume', '--root', self.project)
        self.assertEqual(2, result['counts']['statements'])
        self.assertEqual(2, result['counts']['relations'])
        self.assertEqual('not-assessed', result['scientific_validity'])
        self.assertFalse(result['needs_review'])
        self.assertTrue(all(a['effective_status'] == 'done' for a in result['activities']))


if __name__ == '__main__':
    unittest.main()
