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
        for name, expected in record['guidance_sha256'].items():
            self.assertEqual(digest((ROOT / name).read_bytes()), expected, name)
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


if __name__ == '__main__':
    unittest.main()
