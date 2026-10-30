from pathlib import Path
import csv, hashlib, json, math, os, platform, shutil, subprocess, sys, datetime
BASE=Path('STUDY_ROOT/runs/P6')
IN=BASE/'A/input'; OUT=BASE/'A/output'; ROOT=BASE/'project'
PYTHON='EVAL_PYTHON'
TOOLKIT=Path('TOOLKIT_ROOT')
reads=[]; commands=[]; written=[]
def digest(p):
 b=Path(p).read_bytes();return {'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def read(p,scope='full'):
 p=Path(p);b=p.read_bytes();reads.append({'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'access':scope});return b
def load(p):return json.loads(read(p))
def save(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8');written.append(str(p))
def textfile(p,s):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s,encoding='utf-8');written.append(str(p))
def run(argv,cwd):
 p=subprocess.run(argv,cwd=str(cwd),text=True,capture_output=True)
 commands.append({'argv':argv,'cwd':str(cwd),'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
 return p
# A new directory is created atomically; existing projects are never overwritten.
ROOT.mkdir()
for p in sorted((IN/'initial/project_payload').rglob('*')):
 if p.is_file():
  content=read(p,'full-byte preservation; scientific parsing separately documented')
  dest=ROOT/p.relative_to(IN/'initial/project_payload');dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(content);written.append(str(dest))
for name in ['BRIEF.md','constraints.json','obligations.json','source-identities.json','MANIFEST.json']:
 textfile(ROOT/'provenance/initial'/name,read(IN/'initial'/name).decode('utf-8'))
for name in ['PROTOCOL.md','RECORDING.md','STAGE-A.md']:
 textfile(ROOT/'provenance/task-A'/name,read(IN/name).decode('utf-8'))
read(BASE/'A/REQUEST.md')
for name in ['skills/rw-workflow/SKILL.md','core/skill-bridge.md','core/protocol.md']:
 read(TOOLKIT/name)
read(Path(__file__))
constraints=load(IN/'initial/constraints.json');obligations=load(IN/'initial/obligations.json');sources=load(IN/'initial/source-identities.json');manifest=load(IN/'initial/MANIFEST.json')
manifest_checks={}
for name, expected in manifest['files'].items():
 actual=digest(IN/'initial'/name);manifest_checks[name]={'actual':actual,'expected':expected,'matches':actual==expected}
assert all(v['matches'] for v in manifest_checks.values())
# Copy only four small, explicitly requested canonical versions. Large raw data remain a single private cache copy.
for rel in ['notes/parameters.json','results/result.json','results/table.csv','results/summary.md']:
 dest=ROOT/'snapshots/initial'/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(read(ROOT/rel));written.append(str(dest))
tracked=set(obligations['local_tracking_paths']+[obligations['companion_deliverable']])
before={rel:digest(ROOT/rel) for rel in sorted(tracked)}
valid=run([PYTHON,'-I','-B',str(ROOT/'scripts/compute.py'),'--root',str(ROOT),'--output',str(OUT/'validation-valid')],ROOT)
assert valid.returncode==0,valid.stderr
computed=load(OUT/'validation-valid/result.json');canonical=load(ROOT/'results/result.json')
result_equal=computed==canonical
csv_equal=read(OUT/'validation-valid/table.csv')==read(ROOT/'results/table.csv')
result_byte_equal=read(OUT/'validation-valid/result.json')==read(ROOT/'results/result.json')
assert result_equal and csv_equal and result_byte_equal
before_invalid={rel:digest(ROOT/rel) for rel in sorted(tracked)}
invalid=run([PYTHON,'-I','-B',str(ROOT/'scripts/compute.py'),'--root',str(ROOT),'--output',str(OUT/'validation-rejected'),'--spec',str(ROOT/'notes/rejected-parameters.json')],ROOT)
assert invalid.returncode==2,invalid.stdout
assert not (OUT/'validation-rejected').exists()
after={rel:digest(ROOT/rel) for rel in sorted(tracked)}
assert before==after and before_invalid==after
# Read original scientific materials without re-fitting models.
data=read(ROOT/'data/hour_2011.csv')
rows=list(csv.DictReader(data.decode('utf-8').splitlines()))
spec=load(ROOT/'notes/parameters.json');model=load(ROOT/'model/frozen.json')
summary=read(ROOT/'results/summary.md').decode('utf-8');source_note=read(ROOT/'notes/source-check.md').decode('utf-8')
read(ROOT/'scripts/compute.py');read(ROOT/'notes/rejected-parameters.json')
assert len(rows)==sources['primary']['rows']==8645
assert digest(ROOT/'data/hour_2011.csv')['sha256']==sources['primary']['sha256']
assert all(r['yr']=='0' and r['dteday'].startswith('2011-') for r in rows)
assert '2203' in summary and '92' in summary and '58.825190494512' in summary and '44.570832407532' in summary and '24.23172448%' in summary
checks={'input_manifest_matches':manifest_checks,'valid_exit_code':valid.returncode,'result_semantic_equal':result_equal,'result_byte_equal':result_byte_equal,'table_byte_equal':csv_equal,'row_count':len(rows),'date_min':min(r['dteday'] for r in rows),'date_max':max(r['dteday'] for r in rows),'all_2011_yr0':True,'invalid_exit_code':invalid.returncode,'invalid_stdout':invalid.stdout,'invalid_stderr':invalid.stderr,'invalid_output_directory_exists':False,'all_registered_files_unchanged_after_trials':before==after,'before_invalid':before_invalid,'after_invalid':after,'summary_numeric_fields_checked':['evaluation dates','observed hours','observed days','C0 MAE','C1 MAE','MAE reduction percent'],'source_limits':['Local slice identity and full row count verified against supplied identity card; original ZIP, full hour.csv and live UCI metadata not supplied or fetched.','Model training provenance is supplied metadata; no refit or independent training reconstruction.','The note claims 17379 original hour.csv rows versus 17389 website metadata; this discrepancy is retained but not rechecked remotely.']}
save(OUT/'validation.json',checks);save(ROOT/'records/validation-A.json',checks)
textfile(ROOT/'records/commands-A.json',json.dumps(commands,ensure_ascii=False,indent=2)+'\n')
# This is a project-specific ledger, with no dependency on any external research manager.
records=[]
def add(id,kind,**kw):
 r={'id':id,'kind':kind,'version':1,**kw};records.append(r);return r
add('D-SRC','source',identity=sources['primary'],access={'level':'full local slice; metadata-only remote identity','local_range':'8645 2011 rows parsed; full file SHA verified','remote_fetched':False,'original_zip_or_full_hour_csv_read':False,'verification_scope':'Supplied cached identity, not independently established official provenance'})
add('D-REMOTE','source',identity=sources['source_only'],access={'level':'metadata-only','remote_fetched':False,'local_copy':None,'content_fingerprint':None})
add('D-RAW','material',path='data/hour_2011.csv',source_ids=['D-SRC'],immutable=True)
add('D-PARAM','material',path='notes/parameters.json',meaning='Author working specification, separate from original dataset',specification=spec,revision_reason='Initial author-supplied evaluation scope',recoverable_content='snapshots/initial/notes/parameters.json')
add('D-CLAIM','statement',text=constraints['interest'],scope='2011-10-01 through 2011-12-31; observed-hour weighting; supplied frozen C0/C1; descriptive time holdout',assessment={'scientific_certification':False,'formal_proof':'not-applicable','human_expert_approval':False})
add('D-REL','relation',from_id='D-PARAM',to_id='D-CLAIM',relation='qualifies scope',rationale='Evaluation parameters bound the current numerical comparison, not proof by registration')
add('D-CHOICE','decision',choice='Use supplied initial frozen-model parameters',rationale='Initial benchmark author specification',responsible='Benchmark author; executor only implements this supplied choice',decided_at=None,evidence=['D-PARAM'])
add('D-CODE','artifact',path='scripts/compute.py',description='Supplied calculator preserved byte for byte')
add('D-MODEL','artifact',path='model/frozen.json',derived_from=['D-RAW'],derivation_access='Supplied provenance only; frozen Jan-Sep model consumed without refit')
add('D-RESULT','artifact',path='results/result.json',derived_from=['D-PARAM','D-RAW','D-CODE','D-CHOICE','D-MODEL'],recoverable_content='snapshots/initial/results/result.json')
add('D-TABLE','artifact',path='results/table.csv',derived_from=['D-RESULT'],description='Explicitly tracked companion deliverable',recoverable_content='snapshots/initial/results/table.csv')
add('D-SUMMARY','artifact',path='results/summary.md',derived_from=['D-CLAIM','D-RESULT'],recoverable_content='snapshots/initial/results/summary.md')
add('D-SOURCE-NOTE','artifact',path='notes/source-check.md',description='Supplied fixed identity and coverage note; original remote counts remain supplied assertions')
add('D-SOURCE-CHECK','activity',title='Check supplied primary source identity and coverage card',status='done',inputs=['D-SRC','D-RAW'],outputs=['D-SOURCE-NOTE'],depends_on=[],executor='AI agent plus standard-library file/CSV checks',completion_scope='Local full SHA and 8645 yr=0 rows agree with supplied identity; note reviewed; no full-source or remote scientific certification')
add('D-CALC','activity',title='Evaluate supplied calculator and compare canonical outputs',status='done',inputs=['D-PARAM','D-RAW','D-CODE','D-CHOICE','D-MODEL'],outputs=['D-RESULT','D-TABLE'],depends_on=[],executor='AI agent running supplied Python calculator',completion_scope='Actual normal execution exit 0; generated result and table byte-identical to canonical artifacts',evidence=['records/validation-A.json','records/commands-A.json'])
add('D-SYNTH','activity',title='Verify supplied summary against current claim and numeric result',status='done',inputs=['D-CLAIM','D-RESULT'],outputs=['D-SUMMARY'],depends_on=['D-CALC'],executor='AI agent',completion_scope='Existing author-supplied summary read and checked against dates, counts, MAEs, reduction and stated scope; not authored from scratch or human-reviewed')
byid={r['id']:r for r in records}
for r in records:
 if 'path' in r:r['binding']=digest(ROOT/r['path'])
# Completed activities freeze record versions and fingerprints across the full transitive dependency closure.
def closure(id,seen=None):
 seen=set() if seen is None else seen
 if id in seen:return seen
 seen.add(id);r=byid[id]
 for k in ['inputs','outputs','depends_on','derived_from','evidence']:
  for dep in r.get(k,[]):
   if dep in byid:closure(dep,seen)
 return seen
def signature(r):return hashlib.sha256(json.dumps({k:v for k,v in r.items() if k!='completion_bindings'},ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
for r in records:
 if r['kind']=='activity':
  r['completion_bindings']={dep:{'version':byid[dep]['version'],'record_sha256':signature(byid[dep]),**({'path':byid[dep]['path'],'file':byid[dep]['binding']} if 'path' in byid[dep] else {})} for dep in sorted(closure(r['id'])-{r['id']})}
state={'format':'local-research-ledger-v1','state_version':1,'authority':'This JSON contains current configuration and logical records. prose notes, source cards, command logs and old handoffs do not overwrite it. Bound material files remain scientific byte authority; mismatches are conflicts requiring explicit review.','configuration':constraints,'records':records,'history':[],'coverage_limits':{'source_only':['D-REMOTE'],'unregistered':['notes/unregistered-scratch.md'],'rejected_trial_not_current_input':'notes/rejected-parameters.json','untracked_files_not_automatically_scientific_dependencies':True},'checkpoint':{'state_version':1,'configuration_sha256':hashlib.sha256(json.dumps(constraints,ensure_ascii=False,sort_keys=True).encode()).hexdigest(),'record_signatures':{r['id']:signature(r) for r in records},'files':after,'next_action':'将已核对的2011第四季度冻结模型指标与摘要交作者讨论；只比较指定观察小时，不重训、不外推2012。若材料或配置发生修订，先运行只读状态检查，定位D-CALC及D-SYNTH的失效范围，再显式复核和更新其版本。','meaning':'Saved recovery context, not additional scientific validation'},'settings':{'model':None,'temperature':None,'seed':None,'token_budget':None,'system_limit':None}}
save(ROOT/'records/state.json',state)
# A self-contained, strictly read-only status program; no bytecode writes when called with -I -B.
textfile(ROOT/'scripts/project_status.py',r'''from pathlib import Path
import argparse, hashlib, json, sys
p=argparse.ArgumentParser(description='Read-only local ledger identity/dependency check')
p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);a=p.parse_args();root=a.root.resolve()
def fp(path):
 if path.is_symlink() or not path.is_file():return None
 b=path.read_bytes();return {'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def sig(r):return hashlib.sha256(json.dumps({k:v for k,v in r.items() if k!='completion_bindings'},ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
try:
 state_path=root/'records/state.json';state=json.loads(state_path.read_text(encoding='utf-8'));records={r['id']:r for r in state['records']}
 files={};changes=[]
 for id,r in records.items():
  if 'path' not in r:continue
  rel=Path(r['path'])
  if rel.is_absolute() or '..' in rel.parts:raise ValueError('Unsafe relative path '+str(rel))
  full=root/rel
  if any(v.is_symlink() for v in [full,*list(full.parents)[:len(rel.parts)-1]]):raise ValueError('Symlink in tracked path '+str(rel))
  actual=fp(full);files[str(rel)]={'record':id,'expected':r.get('binding'),'actual':actual,'state':'missing' if actual is None else ('current' if actual==r.get('binding') else 'changed')}
  if files[str(rel)]['state']!='current':changes.append(str(rel))
 activities={}
 for id,r in records.items():
  if r['kind']!='activity':continue
  reasons=[]
  for dep,b in r.get('completion_bindings',{}).items():
   current=records.get(dep)
   if current is None:reasons.append('missing record '+dep);continue
   if current['version']!=b['version'] or sig(current)!=b['record_sha256']:reasons.append('changed record '+dep)
   if 'path' in b and fp(root/b['path'])!=b['file']:reasons.append('changed or missing file '+b['path'])
  activities[id]={'declared_status':r['status'],'effective_status':'stale' if r['status']=='done' and reasons else r['status'],'reasons':reasons}
 for _ in activities:
  for id,v in activities.items():
   for dep in records[id].get('depends_on',[]):
    if activities.get(dep,{}).get('effective_status')!='done':
     reason='dependency activity not current: '+dep
     if reason not in v['reasons']:v['reasons'].append(reason)
     if v['declared_status']=='done':v['effective_status']='stale'
 cp=state.get('checkpoint',{});cp_reasons=[]
 if state['state_version']!=cp.get('state_version'):cp_reasons.append('ledger version changed')
 config_sha=hashlib.sha256(json.dumps(state['configuration'],ensure_ascii=False,sort_keys=True).encode()).hexdigest()
 if config_sha!=cp.get('configuration_sha256'):cp_reasons.append('configuration changed')
 if cp.get('record_signatures')!={id:sig(r) for id,r in records.items()}:cp_reasons.append('logical records changed')
 for rel,expected in cp.get('files',{}).items():
  if fp(root/rel)!=expected:cp_reasons.append('changed or missing checkpoint file '+rel)
 mismatch=[]
 param=next((r for r in records.values() if r['id']=='D-PARAM'),None)
 if param and (root/param['path']).is_file():
  spec=json.loads((root/param['path']).read_text(encoding='utf-8'))
  for key,val in state['configuration'].get('current_scope',{}).items():
   if key in spec and spec[key]!=val:mismatch.append(key)
 out={'root':str(root),'authority':str(state_path),'state_version':state['state_version'],'state_sha256':fp(state_path)['sha256'],'files':files,'changed_or_missing_paths':changes,'activities':activities,'checkpoint_freshness':'stale' if cp_reasons else 'current','checkpoint_reasons':cp_reasons,'configuration_parameter_conflicts':mismatch,'configuration':state['configuration'],'next_action':cp.get('next_action'),'coverage_limits':state['coverage_limits'],'scientific_validity':'not-certified by identity check'}
 print(json.dumps(out,ensure_ascii=False,indent=2));sys.exit(1 if changes or cp_reasons or mismatch or any(x['effective_status']=='stale' for x in activities.values()) else 0)
except (OSError,ValueError,KeyError,TypeError) as e:
 print(json.dumps({'error':type(e).__name__,'message':str(e)},ensure_ascii=False));sys.exit(2)
''')
textfile(ROOT/'RECOVER.md',f'''# 恢复与权威状态

当前配置、逻辑记录与版本的唯一权威表示为 `records/state.json`。作者笔记或旧handoff不得覆盖较新配置；文件的实际字节如果不同于绑定值，应当报告冲突，而不是悄悄接受。原始初始约束和身份材料保留在 `provenance/initial/`，当前配置以后显式修订后以state.json为准。

只读恢复命令（迁移时将ROOT替换为新项目绝对路径，使用可用的Python 3标准库解释器）：

```sh
{PYTHON} -I -B ROOT/scripts/project_status.py --root ROOT
```

脚本完全自包含，不需要外部工具包或本阶段OUTPUT_DIR。退出0表示登记的身份/依赖与检查点一致；退出1表示有漂移/陈旧活动；退出2为读取/格式错误。它不重算、不写项目、不自动接受变化、不认证科学正确性。跟踪9个材料路径，未登记scratch和无本地绑定的来源不在自动文件检查中。

## 当前具体下一步

将已核对的2011第四季度冻结模型指标与摘要交作者讨论；不重新训练，不外推2012。本阶段未发送、未提交，也未获得人类专家批准。材料若变化，先定位具体改变，沿依赖复核D-CALC及D-SYNTH；D-SOURCE-CHECK独立于评价参数，只有其来源、原始数据或来源卡本身变化才需要重做。

## 实际执行和科学边界

`records/validation-A.json`及`records/commands-A.json`保留正常执行与受控无效输入测试。有效计算和预制result/table逐字节相等；summary按其声明的日期、样本量、MAE和降低比例复核。未重训模型，也未核验完整原始hour.csv、ZIP或远端论文/官网内容。8645行2011切片SHA与提供的来源身份一致。原始完整hour.csv 17379行与网站metadata 17389行的差异只按来源卡保留，没有联网核实。

## 版本保留和并发修订

初始参数、result、table、summary的原字节在`snapshots/initial/`，可恢复被覆盖内容；恢复前先保留当前版本，不能无条件覆盖。`scripts/guarded_state_update.py`只提交一个已经准备并审阅的完整新state候选。要求同时提供实际读取的旧state SHA与旧state_version，新state_version须恰增1，修改记录的version须恰增1，并给出reason。旧state完整保留在`snapshots/authority/`，不允许旧handoff覆盖新state。该工具只更新权威元数据；科学文件和活动完成绑定应由执行者在真实复核后显式准备。不要仅刷新checkpoint来掩盖陈旧活动。

四个初始快照完整SHA在`records/initial-snapshots.json`。大型CSV只保留项目内私有缓存一份，原始PDF/CSV禁止随公开仓库分发；可以公开身份和本项目结果。没有新的目标期刊决定，venue保持未定。
''')
textfile(ROOT/'scripts/guarded_state_update.py',r'''from pathlib import Path
import argparse, hashlib, json, os, sys
p=argparse.ArgumentParser(description='Guarded local ledger replacement; never executes research steps')
p.add_argument('--root',type=Path,required=True);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--expected-version',type=int,required=True);p.add_argument('--expected-sha256',required=True);p.add_argument('--reason',required=True);a=p.parse_args()
root=a.root.resolve();state=root/'records/state.json';lock=root/'records/.edit.lock'
try:
 # POSIX flock is standard library on this project's actual macOS environment.
 import fcntl
 with lock.open('a+b') as f:
  fcntl.flock(f.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
  old_bytes=state.read_bytes();old=json.loads(old_bytes);old_sha=hashlib.sha256(old_bytes).hexdigest()
  if old['state_version']!=a.expected_version or old_sha!=a.expected_sha256:raise ValueError('Conflict: authoritative state has changed; reread it before editing')
  new=json.loads(a.candidate.read_text(encoding='utf-8'))
  if new['state_version']!=old['state_version']+1:raise ValueError('state_version must increase exactly by one')
  prior={r['id']:r for r in old['records']}
  for r in new['records']:
   prev=prior.get(r['id'])
   if prev is None and r['version']!=1:raise ValueError('New record version must be 1')
   if prev is not None:
    changed={k:v for k,v in prev.items() if k!='version'}!={k:v for k,v in r.items() if k!='version'}
    if r['version']!=prev['version']+int(changed):raise ValueError('Record version conflict: '+r['id'])
  new.setdefault('history',[]).append({'prior_state_version':old['state_version'],'prior_state_sha256':old_sha,'snapshot':'snapshots/authority/v'+str(old['state_version'])+'-'+old_sha+'.json','reason':a.reason,'executor':'current explicit local update; no implied human scientific approval'})
  snap=root/new['history'][-1]['snapshot'];snap.parent.mkdir(parents=True,exist_ok=True)
  if snap.exists() and snap.read_bytes()!=old_bytes:raise ValueError('Snapshot collision')
  if not snap.exists():snap.write_bytes(old_bytes)
  temp=state.with_name('.state.pending-'+str(os.getpid())+'.json')
  try:
   with temp.open('x',encoding='utf-8') as out:json.dump(new,out,ensure_ascii=False,indent=2,allow_nan=False);out.write('\n');out.flush();os.fsync(out.fileno())
   os.replace(temp,state)
  finally:
   if temp.exists():temp.unlink()
  print(json.dumps({'updated':True,'state_version':new['state_version'],'old_state_snapshot':str(snap)}))
except (OSError,ValueError,KeyError,TypeError) as e:
 print(json.dumps({'updated':False,'error':type(e).__name__,'message':str(e)}));sys.exit(2)
''')
save(ROOT/'records/initial-snapshots.json',{rel:digest(ROOT/'snapshots/initial'/rel) for rel in ['notes/parameters.json','results/result.json','results/table.csv','results/summary.md']})
status=run([PYTHON,'-I','-B',str(ROOT/'scripts/project_status.py'),'--root',str(ROOT)],ROOT)
assert status.returncode==0,status.stdout
status_obj=json.loads(status.stdout);save(OUT/'status.json',status_obj)
# Keep actual persistent read identities and executed commands for subsequent recovery.
for rel in ['scripts/project_status.py','scripts/guarded_state_update.py','records/state.json','RECOVER.md','records/initial-snapshots.json']:
 read(ROOT/rel)
save(ROOT/'records/inputs-A.json',reads)
save(OUT/'execution-data.json',{'commands':commands,'read_files':reads,'written_paths':written,'python_version':sys.version,'platform':platform.platform(),'observed_interpreter':sys.executable,'network_calls':0,'violations':[],'failures':[{'kind':'intentional controlled invalid input','exit_code':invalid.returncode,'stderr':invalid.stderr,'remediation':'None required: canonical tracked files unchanged, rejected output not created'}],'unknown_settings':{'model':None,'temperature':None,'seed':None,'token_budget':None,'system_limits':None}})
print(json.dumps({'project':str(ROOT),'valid_exit':valid.returncode,'invalid_exit':invalid.returncode,'status_exit':status.returncode,'result_equal':result_equal,'table_equal':csv_equal,'tracked_count':len(tracked),'observed_hours':computed['observed_hours']},ensure_ascii=False))
