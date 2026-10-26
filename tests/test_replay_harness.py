"""Real CLI batch reconstruction retains sequential versions and dependencies."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest import mock

from replay_support import ReplayHarness, ROOT


def without_generated_timestamps(registry):
    """Ignore only clock values generated independently by the two CLI runs."""
    value = deepcopy(registry)
    for collection in value['records'].values():
        for envelope in collection.values():
            del envelope['registered_at']
    for event in value['history']:
        del event['at']
        if event['previous'] is not None:
            del event['previous']['registered_at']
    return value


class ReplayBatchEquivalence(unittest.TestCase):
    def test_real_batch_matches_sequential_registry_versions_and_bindings(self):
        with tempfile.TemporaryDirectory(prefix='rw-replay-equivalence-') as temporary:
            base = Path(temporary)
            harness = ReplayHarness(base, 'synthetic-not-a-recording')
            sequential, batch = base/'sequential', base/'batch'
            runtime = ROOT/'tools/research.py'
            harness.invoke(runtime, 'init', '--output', sequential,
                           '--title', 'Synthetic replay equivalence', '--method', 'formal-theory')
            # The same initialized identity and exact material bytes make every
            # generated binding comparable, including previous-version bindings.
            (sequential/'input.txt').write_bytes(b'synthetic source\n')
            (sequential/'result.txt').write_bytes(b'synthetic result\n')
            shutil.copytree(sequential, batch)
            statement = {'id':'S1', 'type':'formal', 'text':'first candidate',
                         'scope':'synthetic finite example'}
            activity = {'id':'A1', 'title':'Review current candidate', 'status':'done',
                        'inputs':['statement:S1', 'evidence:E1', 'decision:D1',
                                  'method-binding:M1'], 'outputs':['artifact:F1']}
            records = [
                {'kind':'source', 'record':{'id':'SRC1', 'title':'Synthetic material',
                    'locator':'input.txt', 'version':'fixture-v1', 'content_access':'full'}},
                {'kind':'statement', 'record':statement},
                {'kind':'evidence', 'record':{'id':'E1', 'type':'finite-check',
                    'description':'Synthetic observation', 'provenance':'test-only material',
                    'location':{'kind':'local', 'path':'input.txt'}, 'source_ids':['SRC1']}},
                {'kind':'relation', 'record':{'id':'R1', 'statement_id':'S1',
                    'evidence_id':'E1', 'relation':'qualifies', 'rationale':'Finite scope only',
                    'scope':'synthetic finite example'}},
                {'kind':'statement', 'record':dict(statement, text='second candidate'),
                 'expected_version':1},
                {'kind':'artifact', 'record':{'id':'F1', 'type':'report',
                    'description':'Synthetic result', 'path':'result.txt',
                    'derived_from':['statement:S1', 'evidence:E1']}},
                {'kind':'decision', 'record':{'id':'D1', 'choice':'Continue minimum check',
                    'rationale':'Finite evidence only', 'responsible':'Synthetic author',
                    'decided_at':'fixture-time', 'evidence_refs':['E1']}},
                {'kind':'method-binding', 'record':{'id':'M1', 'method_id':'formal-theory',
                    'profile_version':'0.1', 'reason':'Synthetic proof obligation',
                    'applies_to':['statement:S1'], 'variant':'proof'}},
                {'kind':'activity', 'record':activity},
                {'kind':'statement', 'record':dict(statement, text='third candidate'),
                 'expected_version':2},
                {'kind':'activity', 'record':dict(activity, note='Rechecked third candidate'),
                 'expected_version':1},
                {'kind':'activity', 'record':{'id':'A2', 'title':'Recover after parent review',
                    'status':'done', 'depends_on':['A1'], 'inputs':['statement:S1']}},
            ]
            single_input = base/'single.json'
            for record in records:
                single_input.write_text(json.dumps(record['record']), encoding='utf-8')
                arguments = ['register', '--root', sequential, '--kind', record['kind'],
                             '--file', single_input]
                if 'expected_version' in record:
                    arguments.extend(['--replace', '--expected-version', record['expected_version']])
                harness.invoke(runtime, *arguments)
            with mock.patch.object(harness, 'invoke', wraps=harness.invoke) as invoked:
                result = harness.register_records(batch, runtime, records)
            self.assertEqual(invoked.call_count, 1, 'Reconstruction must use one real registration process')
            self.assertEqual(invoked.call_args.args[1], 'register-batch')
            self.assertEqual(result['registered_count'], len(records))
            registries = [json.loads((project/'records/registry.json').read_text(encoding='utf-8'))
                          for project in (sequential, batch)]
            self.assertEqual(*(without_generated_timestamps(value) for value in registries))
            value = registries[1]
            self.assertEqual(value['revision'], len(records))
            self.assertEqual([entry['revision'] for entry in value['history']],
                             list(range(1, len(records)+1)))
            self.assertEqual(value['records']['statements']['S1']['version'], 3)
            self.assertEqual(value['records']['activities']['A1']['version'], 2)
            previous = value['history'][10]['previous']
            self.assertEqual(previous['version'], 1)
            current = value['records']['activities']['A1']
            self.assertNotEqual(previous['bindings']['records']['statement:S1'],
                                current['bindings']['records']['statement:S1'])
            self.assertEqual(current['bindings']['files']['input.txt'],
                             hashlib.sha256(b'synthetic source\n').hexdigest())
            # Recovery and inspection still execute in fresh real CLI processes,
            # independently of the batch process and of this test interpreter.
            recovered = []
            for project in (sequential, batch):
                checkpoint = harness.invoke(runtime, 'checkpoint', '--root', project,
                    '--activity', 'A2', '--next-action', 'Inspect the next synthetic obligation')
                self.assertEqual(checkpoint['revision'], len(records)+1)
                checked = harness.invoke(runtime, 'check', '--root', project)
                self.assertTrue(checked['passed'])
                state = harness.invoke(runtime, 'resume', '--root', project)
                self.assertFalse(state['needs_review'])
                recovered.append(state)
            self.assertEqual(recovered[0]['counts'], recovered[1]['counts'])
            self.assertEqual(recovered[0]['activities'], recovered[1]['activities'])
            self.assertEqual(recovered[0]['next_action'], recovered[1]['next_action'])


if __name__ == '__main__':
    unittest.main()
