"""Legal research integration and frozen task replay, not legal adjudication.

Content judgments come from the separately executed and independently reviewed
synthetic tasks. These tests inspect registration, byte identity, recovery, and
coverage; they neither invoke a model nor certify substantive legal correctness.
"""
from copy import deepcopy
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest

from replay_support import ReplayHarness

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from core.bundle import build_payload, _rewrite_skill_links

CLI = ROOT / 'tools/research.py'
CONNECT = ROOT / 'tools/connect_skills.py'
EVAL = ROOT / 'evals/legal'
CASE_IDS = ('authority-time', 'comparative-precedent')
METHOD_ID = 'legal-analysis'
VARIANTS = {'doctrinal', 'case-analysis', 'comparative-law'}
SOURCE_TEMPLATE = 'profiles/templates/legal-source.json'
PROFILE = 'profiles/methods/legal-analysis.md'


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def snapshot(root):
    return {path.relative_to(root).as_posix():
            (sha(path), path.stat().st_mtime_ns)
            for path in root.rglob('*') if path.is_file()}


class LegalResearchIntegration(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='rw-legal-regression-')
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.harness = ReplayHarness(self.base, 'legal')

    def invoke(self, script, *arguments, expected=0):
        result = subprocess.run([sys.executable, '-B', str(script), *map(str, arguments)],
                                cwd=self.base, text=True, capture_output=True, timeout=30,
                                env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return json.loads(result.stdout)

    def initialize(self):
        project = self.base / 'legal project'
        self.invoke(CLI, 'init', '--output', project, '--title', 'Synthetic legal research',
                    '--discipline', 'law', '--method', METHOD_ID)
        return project

    def register(self, project, kind, record, *, expected=0):
        path = self.base / 'registration.json'
        path.write_text(json.dumps(record, ensure_ascii=False), encoding='utf-8')
        return self.invoke(CLI, 'register', '--root', project, '--kind', kind,
                           '--file', path, expected=expected)

    def test_options_and_project_runtime_keep_legal_guidance_after_moving(self):
        options = self.invoke(CLI, 'options')
        self.assertIn('law', {item['id'] for item in options['disciplines']})
        method = next(item for item in options['methods'] if item['id'] == METHOD_ID)
        self.assertEqual(set(method['variants']), VARIANTS)
        self.assertEqual(method['implementation']['profile'], PROFILE)
        self.assertEqual(method['implementation']['task_evidence']['review'],
                         'evals/legal/independent-review.json')
        project = self.initialize()
        self.invoke(CONNECT, 'install', '--root', project)
        moved = self.base / 'moved legal project'
        project.rename(moved)
        runtime = moved / '.agents/skills/_rw-runtime'
        before = snapshot(moved)
        copied = self.invoke(runtime/'tools/research.py', 'options')
        connected = self.invoke(runtime/'tools/connect_skills.py', 'check',
                                '--installed-only', '--root', moved)
        self.assertEqual(before, snapshot(moved))
        self.assertTrue(connected['installed_integrity'])
        self.assertIn('law', {item['id'] for item in copied['disciplines']})
        legal = next(item for item in copied['methods'] if item['id'] == METHOD_ID)
        evidence = legal['implementation']['task_evidence']
        self.assertEqual(evidence['availability'], 'not-included-in-project-runtime')
        self.assertEqual(evidence['review'], 'evals/legal/independent-review.json')
        for name in (PROFILE, SOURCE_TEMPLATE):
            self.assertEqual((runtime/name).read_bytes(), (ROOT/name).read_bytes())

    def test_source_template_legal_extension_round_trips_without_semantic_certification(self):
        project = self.initialize()
        record = deepcopy(read_json(ROOT/SOURCE_TEMPLATE))
        record['id'] = 'SRC-LEGAL-ROUNDTRIP'
        self.assertIsInstance(record['extensions']['legal'], dict)
        self.register(project, 'source', record)
        before = snapshot(project)
        shown = self.invoke(CLI, 'show', '--root', project, '--kind', 'source', '--id', record['id'])
        checked = self.invoke(CLI, 'check', '--root', project)
        self.assertEqual(shown['envelope']['data'], record)
        self.assertEqual(shown['scientific_validity'], 'not-assessed')
        self.assertEqual(checked['scientific_validity'], 'not-assessed')
        self.assertEqual(before, snapshot(project))

    def test_legal_variants_register_and_unknown_or_cross_method_variants_do_not_mutate(self):
        project = self.initialize()
        self.register(project, 'statement', {
            'id': 'S-LEGAL', 'text': 'Conditional interpretation of fictional supplied law.',
            'type': 'interpretive', 'scope': 'Synthetic jurisdiction and supplied snapshot only',
        })
        for index, variant in enumerate(sorted(VARIANTS)):
            self.register(project, 'method-binding', {
                'id': 'M-LEGAL-'+str(index), 'method_id': METHOD_ID, 'profile_version': '0.1',
                'reason': 'Exercise scoped legal research registration',
                'applies_to': ['statement:S-LEGAL'], 'variant': variant,
            })
        for method, variant in ((METHOD_ID, 'unknown'), (METHOD_ID, 'proof'),
                                ('formal-theory', 'doctrinal')):
            with self.subTest(method=method, variant=variant):
                before = snapshot(project)
                result = self.register(project, 'method-binding', {
                    'id': 'M-INVALID', 'method_id': method, 'profile_version': '0.1',
                    'reason': 'Synthetic invalid method/variant pairing',
                    'applies_to': ['statement:S-LEGAL'], 'variant': variant,
                }, expected=2)
                self.assertFalse(result['passed'])
                self.assertEqual(before, snapshot(project))

    def test_every_catalog_method_and_architecture_scenario_has_owned_task_coverage(self):
        catalog = read_json(ROOT/'design/catalog.json')
        old = read_json(ROOT/'evals/d3/coverage.json')
        legal = read_json(EVAL/'coverage.json')
        self.assertEqual(legal['status'], 'executed-and-reviewed')
        self.assertEqual(set(legal['cases']), set(CASE_IDS))
        self.assertEqual(set(legal['method_cases']), {METHOD_ID})
        self.assertFalse(set(old['method_cases']) & set(legal['method_cases']))
        self.assertEqual({item['id'] for item in catalog['methods']},
                         set(old['method_cases']) | set(legal['method_cases']))
        self.assertFalse(set(old['original_scenarios']) & set(legal['scenarios']))
        scenarios = read_json(ROOT/'design/scenarios.json')['cases']
        self.assertEqual({item['id'] for item in scenarios},
                         set(old['original_scenarios']) | set(legal['scenarios']))
        self.assertEqual({item['case_id'] for item in legal['scenarios'].values()}, set(CASE_IDS))
        for item in legal['scenarios'].values():
            self.assertEqual(item['status'], 'pass-in-scope')
        method = next(item for item in catalog['methods'] if item['id'] == METHOD_ID)
        cases = legal['method_cases'][METHOD_ID]
        self.assertEqual(method['implementation']['task_evidence']['cases'], cases)
        self.assertEqual(set(cases), {'legal:'+case for case in CASE_IDS})
        self.assertEqual(set(method['implementation']['supported_variants']), VARIANTS)
        executed_variants = set()
        for case in CASE_IDS:
            manifest = read_json(EVAL/'recordings'/case/'recording.json')
            self.assertIn('law', manifest['project_init']['disciplines'])
            bindings = [entry['record'] for entry in manifest['records'] if entry['kind'] == 'method-binding']
            legal_bindings = [item for item in bindings if item['method_id'] == METHOD_ID]
            self.assertTrue(legal_bindings)
            self.assertLessEqual({item['variant'] for item in legal_bindings}, VARIANTS)
            executed_variants.update(item['variant'] for item in legal_bindings)
        self.assertEqual(executed_variants, VARIANTS)

    def test_independent_reviews_bind_frozen_inputs_outputs_and_read_runtime_resources(self):
        reviews = read_json(EVAL/'independent-review.json')
        self.assertEqual(set(reviews['cases']), set(CASE_IDS))
        payload = build_payload(ROOT)
        snapshot = read_json(EVAL/'reviewed-guidance.json')
        self.assertEqual(snapshot['format_version'], 1)
        self.assertEqual(set(snapshot['sources']), {
            'skills/rw-workflow/SKILL.md', 'skills/rw-literature/SKILL.md',
            'skills/rw-writing/SKILL.md', 'skills/rw-review/SKILL.md',
        })
        for case in CASE_IDS:
            with self.subTest(case=case):
                recording = EVAL/'recordings'/case
                manifest = read_json(recording/'recording.json')
                review = reviews['cases'][case]
                self.assertEqual(review['status'], 'pass-in-scope')
                self.assertEqual(review['input_sha256'], manifest['case_input_sha256'])
                self.assertEqual(review['published_output_sha256'], manifest['output_sha256'])
                inputs = EVAL/'cases'/case
                self.assertEqual(set(manifest['case_input_sha256']),
                                 {path.relative_to(inputs).as_posix() for path in inputs.rglob('*') if path.is_file()})
                for name, checksum in manifest['case_input_sha256'].items():
                    self.assertEqual(sha(inputs/name), checksum)
                self.assertEqual(set(manifest['output_files']), set(manifest['output_sha256']))
                outputs = recording/'outputs'
                self.assertEqual(set(manifest['output_files']),
                                 {path.relative_to(outputs).as_posix() for path in outputs.rglob('*') if path.is_file()})
                for name, checksum in manifest['output_sha256'].items():
                    self.assertEqual(sha(outputs/name), checksum)
                resources = manifest['runtime_resources']
                self.assertTrue(resources)
                self.assertIn(PROFILE, {item['source_path'] for item in resources.values()})
                self.assertEqual(resources, review['runtime_resources'])
                binding = review['artifact_binding']
                reviewed_sources = binding['reviewed_source_resource_sha256']
                reviewed_executed = binding['reviewed_executed_resource_sha256']
                self.assertEqual(set(resources), set(reviewed_sources))
                self.assertEqual(set(resources), set(reviewed_executed))
                if 'reviewed_runtime_resource_sha256' in binding:
                    self.assertEqual(binding['reviewed_runtime_resource_sha256'], reviewed_executed)
                for destination, resource in resources.items():
                    self.assertTrue(destination.startswith('.agents/skills/'))
                    source_path = Path(resource['source_path'])
                    self.assertFalse(source_path.is_absolute())
                    self.assertNotIn('..', source_path.parts)
                    # Legacy sha256 means source identity only. Skill links and
                    # runtime catalog metadata can produce different copy bytes.
                    source_hash = resource.get('source_sha256', resource.get('sha256'))
                    if 'sha256' in resource:
                        self.assertEqual(resource['sha256'], source_hash)
                    # A historical content review binds the guidance actually
                    # read then, not an evolving shared workflow. Preserve that
                    # byte identity; current software/forward tasks run apart.
                    # Legal-specific resources remain tied to current sources.
                    frozen = snapshot['sources'].get(source_path.as_posix())
                    source_bytes = (frozen['source_text'].encode('utf-8') if frozen
                                    else (ROOT/source_path).read_bytes())
                    self.assertEqual(hashlib.sha256(source_bytes).hexdigest(), source_hash)
                    self.assertEqual(source_hash, reviewed_sources[destination])
                    payload_path = destination.removeprefix('.agents/skills/')
                    self.assertIn(payload_path, payload)
                    executed_bytes = (_rewrite_skill_links(frozen['source_text'],
                                      source_path.as_posix()).encode('utf-8') if frozen
                                      else payload[payload_path])
                    executed_hash = hashlib.sha256(executed_bytes).hexdigest()
                    self.assertEqual(executed_hash, resource['executed_sha256'])
                    self.assertEqual(executed_hash, reviewed_executed[destination])

    def test_two_recorded_legal_tasks_replay_and_recover_read_only(self):
        for case in CASE_IDS:
            with self.subTest(case=case):
                project, manifest, runtime = self.harness.replay(case)
                before = snapshot(project)
                for command in ('check', 'status', 'resume'):
                    report = self.invoke(runtime, command, '--root', project)
                    self.assertTrue(report['passed'])
                    self.assertEqual(report['scientific_validity'], 'not-assessed')
                    self.assertEqual(report['counts'], manifest['record_counts'])
                self.assertEqual(before, snapshot(project))
                for kind in ('sources', 'statements', 'evidence', 'relations', 'activities',
                             'artifacts', 'method_bindings'):
                    self.assertGreater(report['counts'][kind], 0)
                self.assertEqual(report['next_action'], manifest['cursor']['next_action'])
                self.assertFalse(report['needs_review'])

    def test_legal_input_drift_marks_work_stale_without_rewriting_the_assessment(self):
        for case in CASE_IDS:
            with self.subTest(case=case):
                project, manifest, runtime = self.harness.replay(case, '-drift')
                inputs = [entry['record']['location']['path'] for entry in manifest['records']
                          if entry['kind'] == 'evidence' and entry['record']['location']['kind'] == 'local'
                          and entry['record']['location']['path'] in manifest['case_files']]
                self.assertTrue(inputs)
                registry = project/'records/registry.json'
                registered = registry.read_bytes()
                changed = project/inputs[0]
                original = changed.read_bytes()
                changed.write_bytes(original+b'\nSynthetic amendment after the recorded review.\n')
                before = snapshot(project)
                report = self.invoke(runtime, 'resume', '--root', project, expected=1)
                self.assertTrue(report['needs_review'])
                self.assertEqual(report['next_action'], manifest['cursor']['next_action'])
                codes = {item['code'] for item in report['findings']}
                self.assertIn('file_changed', codes)
                self.assertIn('activity_stale', codes)
                self.assertEqual(registry.read_bytes(), registered)
                self.assertEqual(before, snapshot(project))
                # Restore the input, then isolate an actual guidance-resource
                # change. A profile version string alone is not freshness logic.
                changed.write_bytes(original)
                self.assertTrue(self.invoke(runtime, 'resume', '--root', project)['passed'])
                profile_path = '.agents/skills/_rw-runtime/'+PROFILE
                bound_profiles = [entry['record']['location']['path'] for entry in manifest['records']
                                  if entry['kind'] == 'evidence' and entry['record']['location']['kind'] == 'local']
                self.assertIn(profile_path, bound_profiles)
                profile = project/profile_path
                profile.write_bytes(profile.read_bytes()+b'\nSynthetic guidance change after review.\n')
                before = snapshot(project)
                report = self.invoke(runtime, 'resume', '--root', project, expected=1)
                codes = {item['code'] for item in report['findings']}
                self.assertIn('file_changed', codes)
                self.assertIn('activity_stale', codes)
                self.assertEqual(registry.read_bytes(), registered)
                self.assertEqual(before, snapshot(project))


if __name__ == '__main__':
    unittest.main()
