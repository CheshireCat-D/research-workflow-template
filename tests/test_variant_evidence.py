"""Read-only guidance discovery distinguishes declarations from task records."""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from core.bundle import variant_evidence, build_payload


def snapshot(root):
    return {path.relative_to(root).as_posix():
            (hashlib.sha256(path.read_bytes()).hexdigest(), path.stat().st_mtime_ns)
            for path in root.rglob('*') if path.is_file()}


class VariantEvidence(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='rw-variant-view-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.method = {'id': 'test-method', 'variants': ['alpha', 'beta', 'gamma'],
                       'implementation': {'supported_variants': ['alpha', 'gamma'],
                                          'task_evidence': {'cases': ['explicit', 'd2:unspecified']}}}

    def record(self, phase, name, bindings):
        path = self.root/'evals'/phase/'recordings'/name/'recording.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({'records': [{'kind': 'method-binding', 'record': value}
                                                for value in bindings]}), encoding='utf-8')

    def test_explicit_bindings_do_not_infer_guidance_or_missing_variant(self):
        self.record('d3', 'explicit', [{'method_id': 'test-method', 'variant': 'beta'},
                                      {'method_id': 'test-method', 'variant': 'beta'}])
        self.record('d2', 'unspecified', [{'method_id': 'test-method'}])
        method = deepcopy(self.method)
        before = snapshot(self.root)
        result = variant_evidence(self.method, self.root)
        self.assertEqual(result['availability'], 'available')
        self.assertEqual(result['method_only_cases'], ['d2:unspecified'])
        rows = {item['id']: item for item in result['variants']}
        self.assertTrue(rows['alpha']['guidance_declared'])
        self.assertEqual(rows['alpha']['explicit_case_bindings'], [])
        self.assertFalse(rows['beta']['guidance_declared'])
        self.assertEqual(rows['beta']['explicit_case_bindings'], ['explicit'])
        self.assertEqual(self.method, method)
        self.assertEqual(snapshot(self.root), before)

    def test_missing_invalid_and_wrong_method_records_are_not_empty_successes(self):
        self.record('d3', 'explicit', [{'method_id': 'test-method', 'variant': 'alpha'}])
        self.record('d2', 'unspecified', [{'method_id': 'different-method', 'variant': 'alpha'}])
        self.method['implementation']['task_evidence']['cases'] += ['missing', '../escape']
        result = variant_evidence(self.method, self.root)
        self.assertEqual(result['availability'], 'partial')
        self.assertEqual({row['case'] for row in result['unavailable_cases']},
                         {'d2:unspecified', 'missing', '../escape'})
        self.assertEqual(result['method_only_cases'], [])

    def test_unknown_variant_and_malformed_recording_are_reported_without_guessing(self):
        self.record('d3', 'explicit', [{'method_id': 'test-method', 'variant': 'unknown'}])
        path = self.root/'evals/d2/recordings/unspecified/recording.json'
        path.parent.mkdir(parents=True)
        path.write_text('{broken', encoding='utf-8')
        result = variant_evidence(self.method, self.root)
        self.assertEqual(result['availability'], 'partial')
        self.assertEqual(result['unrecognized_variant_records'], [{'case': 'explicit', 'variant': 'unknown'}])
        self.assertTrue(all(not row['explicit_case_bindings'] for row in result['variants']))

    def test_portable_runtime_never_inherits_full_distribution_evidence(self):
        self.record('d3', 'explicit', [{'method_id': 'test-method', 'variant': 'alpha'}])
        before = snapshot(self.root)
        result = variant_evidence(self.method, self.root, project_runtime=True)
        self.assertEqual(result['availability'], 'not-included-in-project-runtime')
        self.assertEqual(result['method_only_cases'], [])
        self.assertTrue(all(not row['explicit_case_bindings'] for row in result['variants']))
        self.assertEqual(snapshot(self.root), before)

    def test_source_cli_and_generated_catalog_expose_the_same_guidance_with_distinct_evidence(self):
        result = subprocess.run([sys.executable, '-B', str(ROOT/'tools/research.py'), 'options'],
                                capture_output=True, text=True, check=True,
                                env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
        source = json.loads(result.stdout)
        self.assertTrue(source['read_only'])
        self.assertEqual(source['scientific_validity'], 'not-assessed')
        payload = build_payload()
        portable = json.loads(payload['_rw-runtime/design/catalog.json'])
        for full, copied in zip(source['methods'], portable['methods']):
            self.assertEqual(full['id'], copied['id'])
            declared = full['implementation']['variant_evidence']
            unavailable = copied['implementation']['variant_evidence']
            self.assertEqual(declared['availability'], 'available')
            self.assertEqual(unavailable['availability'], 'not-included-in-project-runtime')
            self.assertEqual([(r['id'], r['guidance_declared']) for r in declared['variants']],
                             [(r['id'], r['guidance_declared']) for r in unavailable['variants']])
        self.assertIn('_rw-runtime/profiles/selection.md', payload)


if __name__ == '__main__':
    unittest.main()
