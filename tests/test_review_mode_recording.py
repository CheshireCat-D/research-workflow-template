"""Recorded forward-task identity and real delivery bytes, not review quality."""
from pathlib import Path
import hashlib
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]


def digest(value):
    return hashlib.sha256(value).hexdigest()


class ReviewModeRecording(unittest.TestCase):
    def setUp(self):
        self.record = json.loads((ROOT / 'evals/current/review-mode-checks.json').read_text(encoding='utf-8'))

    def test_forward_task_binds_actual_guidance_inputs_and_frozen_report_excerpts(self):
        record = self.record
        historical = record['historical_guidance']
        self.assertEqual(historical['recovered_from_commit'],
                         '6843fbef19fceb06c0774f0f3d12cd992f46157a')
        sources = historical['sources']
        self.assertEqual(set(sources), {
            'skills/rw-review/SKILL.md',
            'skills/rw-review/references/review-response.md',
        })
        for name, expected in record['guidance_sha256'].items():
            # Bind the old task to the guidance actually read then. The
            # snapshot keeps this check self-contained in a source archive.
            source = (sources[name]['source_text'].encode('utf-8') if name in sources
                      else (ROOT / name).read_bytes())
            self.assertEqual(digest(source), expected, name)
        self.assertEqual(set(record['input_files']), set(record['input_sha256']))
        for name, content in record['input_files'].items():
            self.assertEqual(digest(content.encode('utf-8')), record['input_sha256'][name], name)
        review = record['blind_review']
        self.assertEqual(review['requested_reports'], 2)
        self.assertEqual(set(review['reports']), {'A', 'B'})
        for name, report in review['reports'].items():
            self.assertEqual(digest(report['published_excerpt'].encode('utf-8')), report['excerpt_sha256'])
            self.assertEqual(report['raw_report_sha256'], review['freeze']['reports']['review-' + name + '.md'])
        # Identity checks do not derive review correctness or independence.

    def test_actual_delivery_manifest_binds_anonymized_source_and_selected_files(self):
        record = self.record
        files = record['response_delivery']['files']
        manifest = json.loads(files['manifest.json'])
        self.assertEqual(set(manifest['package_files']), set(files))
        self.assertEqual({item['path'] for item in manifest['entries']}, set(files) - {'manifest.json'})
        for item in manifest['entries']:
            data = files[item['path']].encode('utf-8')
            self.assertEqual(len(data), item['bytes'])
            self.assertEqual(digest(data), item['sha256'])
        self.assertTrue(set(manifest['required_files']) <= set(files))
        self.assertNotIn('working-notes.md', files)
        original = record['input_files']['response-delivery/manuscript.md']
        self.assertEqual(files['manuscript.md'], original.replace('Author: Example Person (fictional)\n', ''))
        self.assertEqual(files['figure1.svg'], record['input_files']['response-delivery/figure1.svg'])
        self.assertFalse(record['response_delivery']['submitted'])
        self.assertFalse(record['response_delivery']['uploaded'])


class WritingTaskRecording(unittest.TestCase):
    def test_recorded_tasks_bind_the_guidance_actually_used(self):
        record = json.loads((ROOT / 'evals/current/skill-task-checks.json').read_text(encoding='utf-8'))['direct_prose']
        self.assertIn(record['source_entrypoint'], record['guidance_sha256'])
        for name, expected in record['guidance_sha256'].items():
            self.assertEqual(digest((ROOT / name).read_bytes()), expected, name)
        cases = record['cases']
        self.assertEqual({case['id'] for case in cases}, {
            'agriculture-results', 'observational-association',
            'requested-statistical-explanation',
        })
        self.assertEqual(len(cases), 3)
        for case in cases:
            self.assertTrue(case['request'].strip())
            self.assertTrue(case['output'].strip())
        # These are traceable observations; wording checks do not measure style.


class RevisionWorkflowRecording(unittest.TestCase):
    def test_actual_revision_tasks_bind_guidance_inputs_and_output_bytes(self):
        record = json.loads((ROOT / 'evals/current/skill-task-checks.json').read_text(encoding='utf-8'))['revision_workflow']
        for name, expected in record['guidance_sha256'].items():
            self.assertEqual(digest((ROOT / name).read_bytes()), expected, name)
        self.assertEqual({case['id'] for case in record['cases']}, {'time-bounded-plan', 'executed-revision'})
        self.assertEqual(len(record['cases']), 2)
        for case in record['cases']:
            for group in ('input', 'output'):
                files, hashes = case[group + '_files'], case[group + '_sha256']
                self.assertEqual(set(files), set(hashes))
                self.assertTrue(files)
                for name, content in files.items():
                    self.assertEqual(digest(content.encode('utf-8')), hashes[name], name)


if __name__ == '__main__':
    unittest.main()
