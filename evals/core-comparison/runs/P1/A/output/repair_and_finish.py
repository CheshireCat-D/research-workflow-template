import hashlib
import json
import pathlib
import shutil
import subprocess
import sys

A=pathlib.Path('STUDY_ROOT/runs/P1/A')
P=A.parent/'project'
O=A/'output'
PY='EVAL_PYTHON'
RT=P/'.agents/skills/_rw-runtime'
commands=json.loads((O/'actual-commands.json').read_text())
def save(p,v):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def run(args,label):
    r=subprocess.run([str(x) for x in args],cwd=P,capture_output=True,text=True)
    v={'label':label,'argv':[str(x) for x in args],'cwd':str(P),'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
    commands.append(v)
    save(O/'actual-commands.json',commands)
    print(json.dumps({'label':label,'exit_code':r.returncode}),flush=True)
    if r.returncode:
        print(r.stdout,r.stderr)
        raise RuntimeError(label)
    return json.loads(r.stdout)
def cli(*args,label):
    return run([PY,'-I','-B',RT/'tools/research.py',*args],label)

# Keep the first, failed attempt. Its guidance incorrectly assumed the runtime
# was at project/_rw-runtime; the connection actually installed .agents/skills.
shutil.copy2(P/'RECOVERY.md',P/'history/stage-a-initial/RECOVERY-before-runtime-path-fix.md')
text=(P/'RECOVERY.md').read_text()
text=text.replace('_rw-runtime/tools/','.agents/skills/_rw-runtime/tools/')
(P/'RECOVERY.md').write_text(text,encoding='utf-8')
record=cli('show','--root',P,'--kind','artifact','--id','T-RECOVERY',label='read-recovery-artifact-version')
save(O/'recovery-artifact-replacement.json',record['envelope']['data'])
cli('register','--root',P,'--kind','artifact','--file',O/'recovery-artifact-replacement.json','--replace','--expected-version',str(record['envelope']['version']),label='replace-corrected-recovery-artifact')
runtime=run([PY,'-I','-B',RT/'tools/connect_skills.py','check','--installed-only','--root',P], 'verify-actual-installed-runtime')
save(O/'installed-runtime-check.json',runtime)
cli('check','--root',P,label='recheck-after-runtime-path-correction')
next_action=json.loads((O/'final-recovery.json').read_text())['next_action']
cli('checkpoint','--root',P,'--next-action',next_action,'--activity','T-SYNTH','--note','Recovery guide path corrected after retaining failed first runtime check. Local installed runtime then checked; substantive numerical activities unchanged.',label='checkpoint-after-recovery-guide-correction')
final=cli('resume','--root',P,label='final-project-local-resume')
save(O/'final-recovery.json',final)
save(O/'failure-and-remediation.json',{
    'controlled_invalid_input':{'command_label':'controlled-invalid-alpha','exit_code':2,'expected':True,'scope':'Intentional alpha=1 rejection, canonical four files unchanged.'},
    'unexpected_failure':{'command_label':'check-portable-runtime','exit_code':2,'message':'Python could not open project/_rw-runtime/tools/connect_skills.py; actual installed runtime is .agents/skills/_rw-runtime.', 'outer_script_exit_code':1,'original_script':'run_stage_a.py','retained_logs':'actual-commands.json'},
    'remediation':'Inspected actual init result and runtime paths in own project; retained old RECOVERY, corrected paths, read artifact version and replaced through formal interface, checked installed runtime, checked and checkpointed, then resumed with project-local runtime.',
    'remediation_outcome':'All remediation commands exit0; checkpoint current; three required activities effectively done.',
    'scientific_impact':'No canonical scientific file changed; operational path error only.'})
print(json.dumps({'project':str(P),'output':str(O),'freshness':final['checkpoint'],'activities':final['activities']},ensure_ascii=False))
