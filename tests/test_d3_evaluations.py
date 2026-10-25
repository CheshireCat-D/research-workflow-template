"""Replay real D3 task states and bind independent reviews to published artifacts.

No model is invoked here. Content judgments come from separately executed and
reviewed tasks; hashes prevent a later edit from inheriting an old review.
"""
from pathlib import Path
import hashlib
import json
import math
import os
import subprocess
import sys
import tempfile
import unittest
from replay_support import ReplayHarness

ROOT=Path(__file__).resolve().parents[1]
EVAL=ROOT/'evals/d3'
COVERAGE=json.loads((EVAL/'coverage.json').read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(root):
    return {p.relative_to(root).as_posix():(sha(p),p.stat().st_mtime_ns)
            for p in root.rglob('*') if p.is_file()}


class D3Evaluations(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory(prefix='rw-d3-regression-')
        self.base=Path(self.temporary.name)
        self.harness=ReplayHarness(self.base,'d3')

    def tearDown(self):
        self.temporary.cleanup()

    def test_all_recorded_d3_tasks_reconstruct_with_current_skills_and_read_only_recovery(self):
        for case in COVERAGE['d3_cases']:
            with self.subTest(case=case):
                project,manifest,runtime=self.harness.replay(case)
                before=snapshot(project)
                checked=self.harness.invoke(runtime,'check','--root',project)
                recovered=self.harness.invoke(runtime,'resume','--root',project)
                connector=runtime.with_name('connect_skills.py')
                installed=self.harness.invoke(connector,'check','--root',project)
                self.assertEqual(before,snapshot(project))
                self.assertTrue(checked['passed'])
                self.assertEqual(checked['counts'],manifest['record_counts'])
                self.assertEqual(checked['scientific_validity'],'not-assessed')
                self.assertEqual(recovered['next_action'],manifest['cursor']['next_action'])
                self.assertFalse(recovered['needs_review'])
                self.assertTrue(installed['installed_integrity'])
                self.assertEqual(len(installed['skills']),9)
                for kind in ('sources','statements','evidence','relations','activities','artifacts','method_bindings'):
                    self.assertGreater(checked['counts'][kind],0)

    def test_independent_reviews_bind_current_inputs_and_outputs_and_cover_original_scenarios(self):
        reviews=json.loads((EVAL/'independent-review.json').read_text(encoding='utf-8'))
        self.assertEqual(COVERAGE['status'],'executed-and-reviewed')
        self.assertEqual(set(reviews['cases']),set(COVERAGE['d3_cases']))
        for case in COVERAGE['d3_cases']:
            with self.subTest(case=case):
                manifest=json.loads((EVAL/'recordings'/case/'recording.json').read_text())
                review=reviews['cases'][case]
                self.assertEqual(review['status'],'pass-in-scope')
                self.assertEqual(review['input_sha256'],manifest['case_input_sha256'])
                self.assertEqual(review['published_output_sha256'],manifest['output_sha256'])
                for name,digest in review['input_sha256'].items():
                    self.assertEqual(sha(EVAL/'cases'/case/name),digest)
                for name,digest in review['published_output_sha256'].items():
                    self.assertEqual(sha(EVAL/'recordings'/case/'outputs'/name),digest)
                resources = manifest.get('runtime_resources', {})
                self.assertEqual(resources, review.get('runtime_resources', {}))
                for name, resource in resources.items():
                    self.assertTrue(name.startswith('.agents/skills/_rw-runtime/'))
                    self.assertEqual(sha(ROOT/resource['source_path']), resource['sha256'])
                    self.assertEqual(resource['sha256'], review['artifact_binding']['reviewed_runtime_resource_sha256'][name])
        scenarios=json.loads((ROOT/'design/scenarios.json').read_text())['cases']
        # D3 owns its frozen original scenarios. Later suites must account for
        # additions in their own coverage, without rewriting this old review.
        self.assertLessEqual(set(COVERAGE['original_scenarios']),{item['id'] for item in scenarios})
        for item in COVERAGE['original_scenarios'].values():
            self.assertEqual(item['status'],'pass-in-scope')
            if item['phase']=='d3':self.assertIn(item['case_id'],reviews['cases'])
            else:
                older=json.loads((ROOT/'evals/d2/independent-review.json').read_text())
                self.assertEqual(older['cases'][item['case_id']]['status'],'pass')
        catalog=json.loads((ROOT/'design/catalog.json').read_text())
        methods={item['id']:item for item in catalog['methods']}
        for method_id,cases in COVERAGE['method_cases'].items():
            self.assertIn(method_id,methods)
            method=methods[method_id]
            self.assertEqual(method['implementation']['task_evidence']['cases'],cases)
            self.assertTrue(cases)
            for case in cases:
                phase,identifier=case.split(':',1) if ':' in case else ('d3',case)
                manifest=json.loads((ROOT/'evals'/phase/'recordings'/identifier/'recording.json').read_text())
                bindings={entry['record']['method_id'] for entry in manifest['records']
                          if entry['kind']=='method-binding'}
                self.assertIn(method['id'],bindings,case+' does not apply this method')

    def test_task_code_reexecutes_with_recorded_scientific_result_fields(self):
        plans=json.loads((EVAL/'reproduction.json').read_text(encoding='utf-8'))['cases']
        self.assertEqual(set(plans),set(COVERAGE['d3_cases']))
        for case,plan in plans.items():
            with self.subTest(case=case):
                project,manifest=self.harness.assemble(case)
                if plan['script'] is None:
                    self.assertNotIn('artifacts/run.py',manifest['output_files'])
                    continue
                output=self.base/(case+'-rerun')
                arguments=[str(value).replace('{OUTPUT}',str(output)) for value in plan['arguments']]
                command=[sys.executable,'-B',str(project/plan['script']),*arguments]
                completed=subprocess.run(command,cwd=project,text=True,capture_output=True,timeout=10,
                                         env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
                self.assertEqual(completed.returncode,plan['expected_exit'],completed.stdout+completed.stderr)
                result_path=Path(str(plan['result']).replace('{PROJECT}',str(project)).replace('{OUTPUT}',str(output)))
                actual=json.loads(result_path.read_text(encoding='utf-8'))
                expected=json.loads((EVAL/'recordings'/case/'outputs'/plan['recorded_result']).read_text(encoding='utf-8'))
                ignored=set(plan.get('ignore_keys',[]))
                def compare(a,b,path='$'):
                    if isinstance(a,dict) and isinstance(b,dict):
                        self.assertEqual(set(a)-ignored,set(b)-ignored,path)
                        for key in set(a)-ignored:compare(a[key],b[key],path+'.'+key)
                    elif isinstance(a,list) and isinstance(b,list):
                        self.assertEqual(len(a),len(b),path)
                        for number,(left,right) in enumerate(zip(a,b)):compare(left,right,path+f'[{number}]')
                    elif isinstance(a,(int,float)) and not isinstance(a,bool) and isinstance(b,(int,float)) and not isinstance(b,bool):
                        self.assertTrue(math.isfinite(a) and math.isfinite(b),path)
                        self.assertTrue(math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-12),path+': '+str((a,b)))
                    else:self.assertEqual(a,b,path)
                for field in plan['scientific_fields']:
                    compare(actual[field],expected[field],'$.'+field)


if __name__=='__main__':unittest.main()
