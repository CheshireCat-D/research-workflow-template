"""Record this completed execution and verify delivery artifacts without changing results."""
import hashlib
import json
from pathlib import Path

BASE=Path('STUDY_ROOT')
TRIAL=BASE/'runs/D03'
WORK=TRIAL/'workspace'
PY=BASE/'env/bin/python'
hashfile=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
entry=lambda logical,p:{'logical_name':logical,'sha256':hashfile(p)}
record=json.loads((TRIAL/'execution.template.json').read_text())
record['status']='executed'
record['tool_calls']=12
record['network_calls']=0
record['violations']=[]
record['reads']=[entry('common/executor.md',TRIAL/'EXECUTOR.md'),
                 entry('common/execution.template.json',TRIAL/'execution.template.json')]
for name in ['TASK.md','ORIGINAL_README.txt','UCI_PAGE_EXCERPT.txt','SOURCES.md','INPUT_MANIFEST.json','data/hour_2011.csv','data/day_2011.csv']:
    record['reads'].append(entry('input/data-a/'+name,TRIAL/'input'/name))
for name in ['SKILL.md','references/model_evaluation.md']:
    record['reads'].append(entry('guidance/scikit-learn/'+name,BASE/'guidance/scikit-learn'/name))
for p in sorted(WORK.rglob('*')):
    if p.is_file() and p.name not in ['execution.json','artifacts.sha256']:
        record['reads'].append(entry('workspace/'+str(p.relative_to(WORK)),p))
fit=f'{PY} -I -B {WORK}/analyze.py fit --input-dir {TRIAL}/input --output-dir {WORK}/results'
score=f'{PY} -I -B {WORK}/analyze.py score --hour-csv {WORK}/results/predictions.csv --model {WORK}/results/model.json --output-dir {WORK}/replay_check'
verify=f'{PY} -I -B {WORK}/verify.py {WORK} {TRIAL}/input'
record['commands']=[
 {'outer_call':1,'commands':[f'cat {TRIAL}/EXECUTOR.md {TRIAL}/execution.template.json'],'exit_codes':[0]},
 {'outer_call':2,'commands':[f'cat {TRIAL}/input/TASK.md {BASE}/guidance/scikit-learn/SKILL.md {BASE}/guidance/scikit-learn/references/model_evaluation.md'],'exit_codes':[0]},
 {'outer_call':3,'commands':[f'rg --files {TRIAL}/input'],'exit_codes':[0]},
 {'outer_call':4,'commands':[f'cat {TRIAL}/input/ORIGINAL_README.txt {TRIAL}/input/UCI_PAGE_EXCERPT.txt {TRIAL}/input/SOURCES.md {TRIAL}/input/INPUT_MANIFEST.json'],'exit_codes':[0]},
 {'outer_call':5,'commands':[f'mkdir -p {WORK}','apply_patch: add workspace/analyze.py'],'exit_codes':[0,0]},
 {'outer_call':6,'commands':[fit],'exit_codes':[0]},
 {'outer_call':7,'commands':[f'cat {WORK}/results/audit.json {WORK}/results/model.json',score],'exit_codes':[0,0]},
 {'outer_call':8,'commands':['apply_patch: add workspace/verify.py',verify],'exit_codes':[0,0]},
 {'outer_call':9,'commands':['apply_patch: add workspace/report.md, RUN.md, handoff.md'],'exit_codes':[0]},
 {'outer_call':10,'commands':[verify,f'cat {WORK}/results/runtime.json'],'exit_codes':[0,0]},
 {'outer_call':11,'commands':['apply_patch: correct RUN.md actual Python version; add workspace/finalize.py'],'exit_codes':[0]},
 {'outer_call':12,'commands':[f'{PY} -I -B {WORK}/finalize.py'],'exit_codes':[0]}
]
record['duration_seconds']=None
record['scope']='instruction-only; no OS audit'
record['failure']=None
record['runtime']={'python':'3.12.14','evaluation_python':str(PY),'python_flags':['-I','-B'],
                   'fit_and_score_dependencies':'Python standard library',
                   'independent_metric_check_sklearn':'1.9.1',
                   'whole_trial_duration':'not measured; individual execution durations in results/runtime.json and replay_check/runtime.json'}
record['read_scope']='Only this input, own workspace, assigned guidance snapshot and common interpreter libraries. No 2012 observations, other trials, private/raw/design/answer directories, personal skills, memory or agent messages.'
report=(WORK/'report.md').read_text(encoding='utf-8')
assert len(report)<=12000
assert record['tool_calls']<=18
modelhash=hashfile(WORK/'results/model.json')
assert modelhash=='dba591a44fff2d14514b4b38d00c8985e93f41cf2b1ab684a6abd2f2620d078d'
for name in ['results.json','predictions.csv','daily_errors.csv','bootstrap_7d.csv','bootstrap_28d.csv']:
    assert (WORK/'results'/name).read_bytes()==(WORK/'replay_check'/name).read_bytes()
assert json.loads((WORK/'verification.json').read_text())['verification']=='passed'
for name in ['analyze.py','report.md','RUN.md','handoff.md','results/model.json','results/results.json']:
    assert (WORK/name).is_file()
record['report_characters']=len(report)
(WORK/'execution.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
files=[p for p in sorted(WORK.rglob('*')) if p.is_file() and p.name!='artifacts.sha256']
(WORK/'artifacts.sha256').write_text(''.join(f'{hashfile(p)}  {p.relative_to(WORK)}\n' for p in files),encoding='utf-8')
print(json.dumps({'status':'executed','report_characters':len(report),'tool_calls':record['tool_calls'],'network_calls':0,
                  'model_sha256':modelhash,'artifact_files':len(files),'final_checks':'passed'},ensure_ascii=False,indent=2))
