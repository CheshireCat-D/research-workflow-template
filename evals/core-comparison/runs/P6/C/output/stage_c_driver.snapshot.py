from pathlib import Path
import sys,json,hashlib,subprocess,copy,csv,io,math,os
ROOT=Path('PROJECT_ROOT')
OUT=ROOT.parent/'C/output'; IN=ROOT.parent/'C/input'; PY='EVAL_PYTHON'
LOG=OUT/'execution.json'
if LOG.exists(): E=json.loads(LOG.read_text())
else: E={'case_id':'D','stage':'C','commands':[], 'reads':[], 'writes':[], 'tool_calls':6, 'network_calls':0,'violations':[], 'failures':[], 'remedies':[], 'settings':{'model':None,'temperature':None,'seed':None,'token_budget':None,'system_limit':None}}
def read(p,access='full bytes'):
 p=Path(p);b=p.read_bytes();f={'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'access':access}
 if not any(x['path']==f['path'] and x['sha256']==f['sha256'] for x in E['reads']):E['reads'].append(f)
 return b
def fp(p):
 b=read(p,'full SHA256 bytes');return {'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def load(p):return json.loads(read(p))
def write(p,b):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 if isinstance(b,str):b=b.encode()
 p.write_bytes(b)
 if str(p) not in E['writes']:E['writes'].append(str(p))
def save(p,v):write(p,json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def flush():
 save(LOG,E)
def sig(r):return hashlib.sha256(json.dumps({k:v for k,v in r.items() if k!='completion_bindings'},ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def cp(s,next_action):
 return {'state_version':s['state_version'],'configuration_sha256':hashlib.sha256(json.dumps(s['configuration'],ensure_ascii=False,sort_keys=True).encode()).hexdigest(),'record_signatures':{r['id']:sig(r) for r in s['records']},'files':{r['path']:fp(ROOT/r['path']) for r in s['records'] if 'path' in r},'next_action':next_action,'meaning':'Saved current context only; completion binding validity is checked separately.'}
def run(argv,name,inputs=()):
 for p in inputs:fp(p)
 v=subprocess.run(argv,cwd=ROOT,text=True,capture_output=True)
 write(OUT/(name+'.stdout.json'),v.stdout);write(OUT/(name+'.stderr.txt'),v.stderr)
 E['commands'].append({'argv':list(map(str,argv)),'cwd':str(ROOT),'exit_code':v.returncode,'stdout_path':str(OUT/(name+'.stdout.json')),'stderr_path':str(OUT/(name+'.stderr.txt'))})
 flush();return v

def commit(s,old,reason,name):
 p=OUT/(name+'-candidate.json');save(p,s)
 v=run([PY,'-I','-B',str(ROOT/'scripts/guarded_state_update.py'),'--root',str(ROOT),'--candidate',str(p),'--expected-version',str(old['state_version']),'--expected-sha256',fp(ROOT/'records/state.json')['sha256'],'--reason',reason],name,[ROOT/'scripts/guarded_state_update.py',ROOT/'records/state.json',p])
 if v.returncode:raise RuntimeError('Guarded state commit failed; raw output retained')
 return load(ROOT/'records/state.json')
def status(name):
 s=load(ROOT/'records/state.json')
 return run([PY,'-I','-B',str(ROOT/'scripts/project_status.py'),'--root',str(ROOT)],name,[ROOT/'scripts/project_status.py',ROOT/'records/state.json']+[ROOT/r['path'] for r in s['records'] if 'path'in r])

def snapshot():
 # Earlier observed local read commands were successful, before this executable log existed.
 E['commands'] += [
 {'argv':['cat',str(ROOT.parent/'C/REQUEST.md')],'cwd':'TASK_WORKSPACE','exit_code':0,'tool_call':1},
 {'argv':['cat',str(IN/'PROTOCOL.md'),str(IN/'RECORDING.md'),str(IN/'STAGE-C.md')]+[str(Path('TOOLKIT_ROOT')/p) for p in ['skills/rw-workflow/SKILL.md','core/skill-bridge.md','core/protocol.md']],'cwd':'TASK_WORKSPACE','exit_code':0,'tool_call':2},
 {'argv':[PY,'-I','-B','-'],'cwd':'TASK_WORKSPACE','exit_code':0,'tool_call':3,'stdin_description':'List only own project and current input; try root-level revision filenames (absent); no file contents from absent files.'},
 {'argv':[PY,'-I','-B','-'],'cwd':'TASK_WORKSPACE','exit_code':0,'tool_call':4,'stdin_description':'Read current C author files, RECOVER, initial brief/constraints/obligations/source identities, state, three project scripts, parameters, source note, three results. Tool output was truncated; state record subset reread next.'},
 {'argv':[PY,'-I','-B','-'],'cwd':'TASK_WORKSPACE','exit_code':0,'tool_call':5,'stdin_description':'Read state D-CHOICE/D-RESULT/D-TABLE/D-SUMMARY/D-SOURCE-NOTE/three activities and frozen model.'},
 {'argv':[PY,'-I','-B','-'],'cwd':'TASK_WORKSPACE','exit_code':0,'tool_call':6,'stdin_description':'Create output directory and this controller using standard-library Path.write_text; controller full bytes retained.'}]
 for p in [ROOT.parent/'C/REQUEST.md',IN/'PROTOCOL.md',IN/'RECORDING.md',IN/'STAGE-C.md',IN/'author-revision/AUTHOR-REVISION.md',IN/'author-revision/approved-parameters.json']+[Path('TOOLKIT_ROOT')/p for p in ['skills/rw-workflow/SKILL.md','core/skill-bridge.md','core/protocol.md']]:read(p)
 for p in sorted(ROOT.rglob('*')):
  if p.is_file():fp(p)
 old=load(ROOT/'records/state.json');snap=ROOT/'snapshots/stage-C-before-recompute'
 assert not snap.exists(),'Do not overwrite original drift snapshot'
 paths=['records/state.json','RECOVER.md']+[r['path'] for r in old['records'] if 'path'in r]
 manifest={}
 for rel in paths:
  write(snap/rel,read(ROOT/rel));manifest[rel]=fp(snap/rel)
 save(snap/'manifest.json',{'purpose':'Drifted actual files before recomputation; Q4 completion bindings are deliberately preserved, not recertified','files':manifest})
 s=copy.deepcopy(old);s['state_version']+=1;s['checkpoint']=cp(s,'接受参数前先检查漂移：现参数为11月至12月，旧成果仍为Q4；保存断点不能恢复D-CALC或D-SYNTH的有效性。按授权真实复算后交作者内容复核。')
 commit(s,old,'Save drifted snapshot and fresh checkpoint before any recomputation; no material rebind and no activity revalidation','drift-checkpoint-save')
 v=status('intermediate-check')
 save(OUT/'intermediate-check.exit.json',{'exit_code':v.returncode,'expected':1,'checkpoint_does_not_revalidate':True})
 if v.returncode!=1:raise RuntimeError('Intermediate drift check did not report expected stale/conflict')
 x=json.loads(v.stdout)
 assert x['checkpoint_freshness']=='current'
 assert x['activities']['D-CALC']['effective_status']=='stale' and x['activities']['D-SYNTH']['effective_status']=='stale'
 assert x['activities']['D-SOURCE-CHECK']['effective_status']=='done'
 E['failures'].append({'kind':'expected pre-recomputation validity failure','exit_code':1,'output':'intermediate-check.stdout.json','details':'Fresh checkpoint; changed parameters; D-CALC/D-SYNTH stale; independent D-SOURCE-CHECK done.'})
 for rel in ['PROTOCOL.md','RECORDING.md','STAGE-C.md','author-revision/AUTHOR-REVISION.md','author-revision/approved-parameters.json']:
  write(ROOT/'provenance/task-C'/rel,read(IN/rel))
 write(ROOT/'records/intermediate-check-C.json',v.stdout)
 save(ROOT/'records/drift-checkpoint-C.json',load(ROOT/'records/state.json')['checkpoint'])
 flush();print(json.dumps({'snapshot':str(snap),'intermediate_exit':v.returncode,'checkpoint_freshness':x['checkpoint_freshness'],'activities':x['activities']},ensure_ascii=False))

if __name__=='__main__':
 E['tool_calls']+=1
 fp(Path(__file__))
 try:
  if sys.argv[1]=='snapshot':snapshot()
  else:raise ValueError('unknown mode')
 except Exception as e:
  E['failures'].append({'kind':'unexpected execution error','type':type(e).__name__,'message':str(e)});flush();raise
 flush()
