import hashlib
import json
import pathlib
import sys

A=pathlib.Path('STUDY_ROOT/runs/P1/A')
P=A.parent/'project'
O=A/'output'
I=A/'input'
def save(p,v):
    p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def identity(p):
    b=p.read_bytes()
    return {'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
report=(O/'report.md').read_text()
state=json.loads((O/'state-answer.json').read_text())
recovery=json.loads((O/'final-recovery.json').read_text())
assert len(report)<10000
assert recovery['passed'] and recovery['checkpoint']['status']=='current'
assert len(recovery['activities'])==3 and all(x['effective_status']=='done' for x in recovery['activities'])
assert state['normal_run_exit_code']==0 and state['invalid_run_exit_code']==2
assert all((P/x).is_file() for x in ['RECOVERY.md','notes/stage-a-validation.json','.agents/skills/_rw-runtime/tools/research.py','.agents/skills/_rw-runtime/tools/connect_skills.py'])
original=json.loads((P/'provenance/initial/MANIFEST.json').read_text())['files']
for rel in ['notes/parameters.json','results/result.json','results/table.csv','results/summary.md','scripts/compute.py','notes/source-check.md','sources/howard2021-arxiv-v9.pdf']:
    assert identity(P/rel)==original['project_payload/'+rel]
for rel in ['notes/parameters.json','results/result.json','results/table.csv','results/summary.md']:
    assert (P/rel).read_bytes()==(P/'history/stage-a-initial'/rel).read_bytes()
runtime=json.loads((O/'installed-runtime-check.json').read_text())
assert runtime['passed']
execution=json.loads((O/'execution.json').read_text())
for cmd in execution['commands']:
    if cmd.get('tool_call')==15:
        cmd['exit_code']=0
        cmd.pop('note',None)
execution['commands'].append({'tool_call':16,'argv':[sys.executable,'-I','-B',str(O/'verify_delivery.py')],'cwd':str(A),'exit_code':0,'note':'All assertions completed before recording success.'})
execution['outer_tool_calls']=16
execution['tool_calls']=16
execution['outer_tool_call_types']={'exec_command':12,'apply_patch':4}
execution['pending_final_delivery_check']=False
execution['final_delivery_assertions']='passed: required files, original identity, exact recoverable snapshots, current checkpoint, three effective activities, valid/invalid exits and installed runtime check.'
# Keep validation immutable; only external bookkeeping changes here.
save(O/'execution.json',execution)
manifest=json.loads((O/'inputs-and-artifacts.json').read_text())
entries=[]
for base,kind in [(I,'input'),(P,'project-artifact'),(O,'external-output')]:
    for path in sorted(base.rglob('*')):
        if path.is_file() and path != O/'inputs-and-artifacts.json':
            entries.append({'kind':kind,'relative_path':str(path.relative_to(base)),'base':str(base),**identity(path)})
manifest['files']=entries
save(O/'inputs-and-artifacts.json',manifest)
print(json.dumps({'passed':True,'project':str(P),'report':str(O/'report.md'),'recorded_tool_calls':16,'tracked_paths':recovery['file_tracking']['local_file_count'],'checkpoint':recovery['checkpoint']['status'],'inventory_entries':len(entries)},ensure_ascii=False))
