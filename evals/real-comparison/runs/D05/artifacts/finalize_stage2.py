#!/usr/bin/env python3
"""Finalize this execution record without replacing any first numerical result."""
from pathlib import Path
import hashlib
import json

w = Path(__file__).resolve().parent
base = w.parents[2]
sha = lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
baseline = json.loads((w/'stage2_read_baseline.json').read_text(encoding='utf-8'))
report = (w/'report.md').read_text(encoding='utf-8')
assert len(report) <= 12000
for text in ('7.966722%','9.967439%','11.589625%','24.231724%','64.875799%','64.425318%'):
    assert text in report
assert json.loads((w/'results2012/verification.json').read_text())['status'] == 'passed'
assert json.loads((w/'results2012/provenance.json').read_text())['refit'] is False
preserved = {'report.md','handoff.md','RUN.md','execution.json','verification.json','artifacts.sha256'}
for rec in baseline['reads']:
    logical=rec['logical_name']
    if logical.startswith('workspace/'):
        name=logical[len('workspace/'):]
        target = w/'stage1_snapshot'/name if name in preserved else w/name
        assert sha(target) == rec['sha256'], (logical,'original evidence changed')
        if name in preserved:
            rec['preserved_as'] = 'workspace/stage1_snapshot/'+name
    rec['phase'] = 'original_material_or_input'
reads = baseline['reads']
files = [p for p in sorted(w.rglob('*')) if p.is_file() and p.name not in ('execution.json','artifacts_stage2.sha256')]
manifest=[]
for path in files:
    logical='workspace/'+path.relative_to(w).as_posix()
    digest=sha(path)
    manifest.append(f'{digest}  {path.relative_to(w).as_posix()}')
    if not any(x['logical_name']==logical and x['sha256']==digest for x in reads):
        reads.append({'logical_name':logical,'sha256':digest,'phase':'artifact_verification'})
(w/'artifacts_stage2.sha256').write_text('\n'.join(manifest)+'\n',encoding='utf-8')
reads.append({'logical_name':'workspace/artifacts_stage2.sha256','sha256':sha(w/'artifacts_stage2.sha256'),'phase':'artifact_verification'})
template=base/'runs/D05/execution.template.json'
execution=json.loads(template.read_text(encoding='utf-8'))
execution.update({'status':'executed','tool_calls':9,'network_calls':0,'violations':[],
                  'reads':reads,'duration_seconds':None,'failure':None,'report_characters':len(report)})
execution['commands']=[
    {'outer_call':1,'commands':['cat D05/EXECUTOR.md D05/execution.template.json D05/input/TASK.md'],'exit_codes':[0]},
    {'outer_call':2,'commands':['cat guidance/scikit-learn/SKILL.md guidance/scikit-learn/references/model_evaluation.md','rg --files D03/workspace D05/input'],'exit_codes':[0]},
    {'outer_call':3,'commands':['cat workspace/analyze.py workspace/handoff.md workspace/report.md workspace/RUN.md workspace/results/model.json workspace/results/results.json workspace/results/runtime.json input/data-b/INPUT_MANIFEST.json input/data-b/SOURCES.md input/data-b/ORIGINAL_README.txt input/data-b/UCI_PAGE_EXCERPT.txt'],'exit_codes':[0]},
    {'outer_call':4,'commands':['cat workspace/report.md workspace/RUN.md workspace/verification.json prior-input/data-a/TASK.md workspace/execution.json'],'exit_codes':[0]},
    {'outer_call':5,'commands':['apply_patch: add workspace/update_2012.py'],'exit_codes':[0]},
    {'outer_call':6,'commands':['EVAL_PYTHON -I -B - [inline: preserve original documentation and create stage2_read_baseline.json]',
       'EVAL_PYTHON -I -B WORKSPACE/update_2012.py --input-dir INPUT_DIR --output-dir WORKSPACE/results2012 --model WORKSPACE/results/model.json --prior-results WORKSPACE/results'], 'exit_codes':[0,0]},
    {'outer_call':7,'commands':['apply_patch: add workspace/write_stage2_delivery.py',
       'EVAL_PYTHON -I -B WORKSPACE/write_stage2_delivery.py'],'exit_codes':[0,0]},
    {'outer_call':8,'commands':['apply_patch: add workspace/finalize_stage2.py'],'exit_codes':[0]},
    {'outer_call':9,'commands':['EVAL_PYTHON -I -B WORKSPACE/finalize_stage2.py'],'exit_codes':[0]}
]
provenance=json.loads((w/'results2012/provenance.json').read_text(encoding='utf-8'))
execution['runtime']={'evaluation_python':'EVAL_PYTHON',
                      'python_flags':['-I','-B'],'python':provenance['python'],
                      'independent_metric_check_sklearn':'1.9.1',
                      'evaluation_seconds':provenance['seconds'],
                      'whole_trial_duration':'not measured; duration_seconds remains null'}
execution['read_scope']='Supplied stage-B input, own previous-stage workspace, permitted original stage-A TASK, assigned guidance snapshot, common interpreter libraries; no other trial, private/raw/design/answer, memory, personal skill, network, installation or agent communication.'
execution['command_notation']='Read and search paths in calls 1-4 are logical aliases: D05 is this execution/input directory; D03/workspace is the permitted own previous workspace. SHA256 records above bind exact content. Inline preparation command is described; scientific rerun command is stored verbatim.'
execution['checks']={'original_model_and_results_preserved':True,'report_within_character_limit':True,
                     'training_parameters_verified':72,'2011_history_replay_equal':True,
                     '2012_independent_metrics_checked':True,'2012_model_refit':False,
                     'original_documents_preserved_in':'workspace/stage1_snapshot/'}
(w/'execution.json').write_text(json.dumps(execution,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
reloaded=json.loads((w/'execution.json').read_text(encoding='utf-8'))
assert reloaded['status']=='executed' and reloaded['requested']['model_override'] is None
assert all(value is None for value in reloaded['effective'].values())
assert reloaded['tool_calls']<=reloaded['requested']['max_tool_calls']
print(json.dumps({'status':reloaded['status'],'tool_calls':reloaded['tool_calls'],
                   'report_characters':len(report),'model_sha256':sha(w/'results/model.json'),
                   'original_model_results_docs_preserved':True,'record':str(w/'execution.json')},ensure_ascii=False))
