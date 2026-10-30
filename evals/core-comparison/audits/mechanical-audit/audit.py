#!/usr/bin/env python3
"""Independent mechanical audit. Only sealed/allowed evidence; mutations in copies."""
from pathlib import Path
import copy,csv,hashlib,json,math,os,re,shutil,subprocess,sys,zipfile
S=Path('STUDY_ROOT')
A=S/'mechanical-audit'
PY='EVAL_PYTHON'
PLAN=json.loads((S/'plan.json').read_text())
RECEIPTS=[]
def load(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def snap(root):
 d={'files':{},'directories':{}}
 for p in [root,*sorted(root.rglob('*'))]:
  rel=str(p.relative_to(root)) if p!=root else '.';st=p.lstat()
  if p.is_symlink():d['files'][rel]={'symlink':os.readlink(p),'mtime_ns':st.st_mtime_ns}
  elif p.is_file():d['files'][rel]={'sha256':sha(p),'bytes':st.st_size,'mtime_ns':st.st_mtime_ns}
  elif p.is_dir():d['directories'][rel]=st.st_mtime_ns
 return d
def clone(c,phase,name):
 dst=A/c/name/'project';shutil.copytree(S/'runs'/c/phase/'sealed-project',dst);return dst
def run(name,argv,cwd,root=None):
 before=snap(root) if root else None
 p=subprocess.run([str(v) for v in argv],cwd=str(cwd),capture_output=True,text=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','HOME':str(A/'empty-home'),'XDG_CACHE_HOME':str(A/'empty-cache')})
 d={'name':name,'argv':[str(v) for v in argv],'cwd':str(cwd),'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
 if root:
  after=snap(root);dump(A/'receipts'/f'{name}.before.json',before);dump(A/'receipts'/f'{name}.after.json',after)
  d['project_identical_bytes_mtime_directory_mtime']=before==after
  d['changed_files']=[x for x in sorted(set(before['files'])|set(after['files'])) if before['files'].get(x)!=after['files'].get(x)]
  d['changed_directories']=[x for x in sorted(set(before['directories'])|set(after['directories'])) if before['directories'].get(x)!=after['directories'].get(x)]
 dump(A/'receipts'/f'{name}.json',d);RECEIPTS.append(d)
 return d
def prun(name,root,script,args=(),readonly=False):return run(name,[PY,'-I','-B',root/script,*args],root,root if readonly else None)
def cli(name,root,args,readonly=False):return prun(name,root,'.agents/skills/_rw-runtime/tools/research.py',args,readonly)
def payload(r):
 try:return json.loads(r['stdout'])
 except (ValueError,KeyError):return {}
def identity(p):return {'sha256':sha(p),'bytes':p.stat().st_size}

def independent(root,spec):
 if spec['case_id']=='T':
  # Deliberately use ordinary log of the quotient form rather than calculator log1p.
  rho=spec['rho'];alpha=spec['alpha']
  return {'values':[{'v':v,'boundary':math.sqrt((v+rho)*math.log((1+v/rho)/(alpha*alpha)))} for v in spec['intrinsic_time_grid']]}
 model=load(root/'model/frozen.json');rows=[]
 with (root/'data/hour_2011.csv').open(newline='') as f:
  for row in csv.DictReader(f):
   if spec['evaluation_start']<=row['dteday']<=spec['evaluation_end']:rows.append(row)
 result={'observed_hours':len(rows),'observed_days':len({r['dteday'] for r in rows})}
 for k in ['C0','C1']:
  errors=[]
  for r in rows:
   prediction=model['C0'][r['hr']] if k=='C0' else model['C1'].get(r['workingday']+':'+r['hr'],model['C0'][r['hr']])
   errors.append(prediction-int(r['cnt']))
  result[k+'_MAE']=math.fsum(map(abs,errors))/len(errors)
  result[k+'_RMSE']=math.sqrt(math.fsum(e*e for e in errors)/len(errors))
  result[k+'_bias_prediction_minus_actual']=math.fsum(errors)/len(errors)
 result['MAE_reduction_fraction']=(result['C0_MAE']-result['C1_MAE'])/result['C0_MAE']
 return result

def numeric_audit():
 ans=[]
 for chain in PLAN:
  c=chain['chain_id'];case=chain['case_id'];key=load(S/'design'/case/'reference/answer.json')
  for phase in ['A','C']:
   root=clone(c,phase,'numeric-'+phase);spec=load(root/'notes/parameters.json');canonical=load(root/'results/result.json')
   output=root.parent/'fresh-calculation';r=prun(c+'-'+phase+'-compute',root,'scripts/compute.py',['--root',root,'--output',output])
   actual=load(output/'result.json') if (output/'result.json').exists() else None
   expected=independent(root,spec);errors=[]
   if case=='T':
    errors=[abs(x['boundary']-y['boundary']) for x,y in zip(expected['values'],canonical['values'])]
    summary_values=[canonical['values'][2]['boundary']] if phase=='A' else [v['boundary'] for v in canonical['values']]
   else:
    errors=[abs(canonical[k]-v) for k,v in expected.items()]
    summary_values=[canonical[k] for k in ['C0_MAE','C1_MAE']]
    if phase=='C':summary_values += [canonical[k] for k in ['C0_RMSE','C1_RMSE','C0_bias_prediction_minus_actual','C1_bias_prediction_minus_actual']]
   summary=(root/'results/summary.md').read_text()
   rounded=[f'{v:.12f}' for v in summary_values]
   if case=='D':rounded.append(f"{canonical['MAE_reduction_fraction']*100:.8f}%")
   protected=['scripts/compute.py','notes/source-check.md']+(['sources/howard2021-arxiv-v9.pdf'] if case=='T' else ['data/hour_2011.csv','model/frozen.json'])
   identities={f:{'actual':sha(root/f),'supplied':sha(S/'design'/case/'initial/project_payload'/f),'equal':sha(root/f)==sha(S/'design'/case/'initial/project_payload'/f)} for f in protected}
   input_bindings={'parameters':sha(root/'notes/parameters.json'),'calculator':sha(root/'scripts/compute.py')}
   if case=='D':input_bindings.update(hour_2011=sha(root/'data/hour_2011.csv'),frozen_model=sha(root/'model/frozen.json'))
   # Table shape and numeric values are checked independently, beyond byte equality with rerun.
   table=list(csv.DictReader((root/'results/table.csv').open(newline='')))
   if case=='T':te=[abs(float(x['boundary'])-y['boundary']) for x,y in zip(table,expected['values'])];table_shape=len(table)==len(expected['values']) and [float(x['v']) for x in table]==[x['v'] for x in expected['values']]
   else:te=[abs(float(x['value'])-expected[x['metric']]) for x in table];table_shape={x['metric'] for x in table}=={'observed_hours','observed_days','C0_MAE','C1_MAE','C0_RMSE','C1_RMSE','MAE_reduction_fraction'}
   row={'chain':c,'phase':phase,'case':case,'compute_exit':r['exit_code'],'parameter_semantics_match_key':spec==key['initial_parameters' if phase=='A' else 'revised_parameters'],'canonical_equals_rerun_semantically':actual==canonical,'canonical_result_bytes_equal_rerun':(output/'result.json').read_bytes()==(root/'results/result.json').read_bytes(),'canonical_table_bytes_equal_rerun':(output/'table.csv').read_bytes()==(root/'results/table.csv').read_bytes(),'max_absolute_independent_result_error':max(errors),'max_absolute_independent_table_error':max(te),'table_shape_matches':table_shape,'summary_required_rounded_tokens':rounded,'summary_tokens_present':all(x in summary for x in rounded),'input_sha256_actual':input_bindings,'input_sha256_matches_result':canonical.get('input_sha256')==input_bindings,'protected':identities,'receipt':str(A/'receipts'/f'{c}-{phase}-compute.json')}
   ans.append(row)
 dump(A/'numeric.json',ans);return ans

def archive_audit():
 seals=[];readonly=[];events=[];migrations=[]
 for chain in PLAN:
  c=chain['chain_id'];case=chain['case_id']
  for phase in 'ABCD':
   p=S/'runs'/c/phase;seal=load(p/'seal.json');proj=p/'sealed-project';out=p/'sealed-output'
   mismatches=[f for f,h in seal['outputs'].items() if not (out/f).is_file() or sha(out/f)!=h]
   files=[f for f in proj.rglob('*') if f.is_file()]
   seals.append({'chain':c,'phase':phase,'sealed_project_exists':proj.is_dir(),'sealed_project_files':len(files),'seal_files_claim':seal['files'],'count_equal':len(files)==seal['files'],'sealed_output_hash_mismatches':mismatches,'assignment_matches':load(p/'assignment.json')['case_id']==case and load(p/'assignment.json')['stage']==phase})
   if phase in 'BD':
    b=load(p/'project-before.json');a=load(p/'project-after.json');audi=load(p/'readonly-audit.json')
    # Recompute equality; do not rely on passed field.
    readonly.append({'chain':c,'phase':phase,'before_after_equal':a==b,'files':len(b['files']),'directories':len(b['directories']),'every_file_has_sha_bytes_mtime':all(set(['sha256','bytes','mtime_ns'])<=set(x) for x in b['files'].values()),'receipt_consistent':audi['passed']==(a==b),'sealed_project_files_match_after':all((proj/f).is_file() and identity(proj/f)=={'sha256':v['sha256'],'bytes':v['bytes']} for f,v in a['files'].items())})
  initial=S/'runs'/c/'A/sealed-project';b=S/'runs'/c/'B/sealed-project';inj=load(S/'runs'/c/'B/injection.json')
  f0={str(p.relative_to(initial)):sha(p) for p in initial.rglob('*') if p.is_file()};f1={str(p.relative_to(b)):sha(p) for p in b.rglob('*') if p.is_file()}
  changed=[f for f in sorted(set(f0)|set(f1)) if f0.get(f)!=f1.get(f)]
  events.append({'chain':c,'case':case,'changed_paths_recomputed_A_to_B':changed,'only_parameter_changed':changed==['notes/parameters.json'],'before_sha_matches':f0['notes/parameters.json']==inj['before_sha256'],'after_sha_matches':f1['notes/parameters.json']==inj['after_sha256'],'event_applied':inj['event_applied'],'uniform_parameters':load(b/'notes/parameters.json')==load(S/'design'/case/'reference/answer.json')['revised_parameters']})
  mig=load(S/'runs'/c/'D/migration.json');old=Path(load(S/'runs'/c/'A/assignment.json')['project']);tool=S/'toolkits'/c/'research-workflow-template'
  migrations.append({'chain':c,'receipt':mig,'old_project_path':str(old),'old_project_exists_now':old.exists(),'old_toolkit_path':str(tool),'old_toolkit_exists_now':tool.exists(),'not_os_access_audit':True,'old_path_existence_only':True})
 ans={'seals':seals,'readonly':readonly,'events':events,'migrations':migrations};dump(A/'archive.json',ans);return ans

if __name__=='__main__':
 A.mkdir(exist_ok=True);(A/'empty-home').mkdir(exist_ok=True);(A/'empty-cache').mkdir(exist_ok=True)
 dump(A/'attempt_notes.json',{'delegation_attempt':{'task':'numeric','outcome':'collab spawn failed: agent thread limit reached','external_content_received':False,'actual_delegation':False},'allowed_evidence_only':True,'no_network_or_install':True,'no_personal_memory_or_skills_read':True,'tool_calls_before_script':'Interface help/schemas and sealed evidence inspected. Initial broad rg listed disallowed route filenames but no route file content was opened.'})
 archive_audit();numeric_audit();dump(A/'all-receipts.json',RECEIPTS)
