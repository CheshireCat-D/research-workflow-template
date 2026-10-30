import copy, csv, fcntl, hashlib, importlib.util, json, math, os, shutil, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path('PROJECT_ROOT')
OUT=Path('OUTPUT_DIR')
INP=OUT.parent/'input'
PYTHON='EVAL_PYTHON'
TOOLKIT=Path('TOOLKIT_ROOT')
LOG=OUT/'execution.json'
def load(p):
 b=p.read_bytes(); track(p,b); return json.loads(b)
def track(p,b):
 q=str(p.resolve()); EXEC['read_files'][q]={'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def read(p):
 b=p.read_bytes(); track(p,b); return b
def fp(p):
 b=read(p); return {'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def dig(v):return hashlib.sha256(json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def write(p,v):
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
 EXEC['written_paths'].append(str(p))
def run(argv,label):
 q=subprocess.run(argv,cwd=ROOT,capture_output=True,text=True)
 (OUT/(label+'.stdout')).write_text(q.stdout)
 (OUT/(label+'.stderr')).write_text(q.stderr)
 EXEC['commands'].append({'argv':argv,'cwd':str(ROOT),'exit_code':q.returncode,'stdout':str(OUT/(label+'.stdout')),'stderr':str(OUT/(label+'.stderr'))})
 EXEC['written_paths'].extend([str(OUT/(label+'.stdout')),str(OUT/(label+'.stderr'))])
 if q.returncode:EXEC['failures_or_nonzero_checks'].append({'label':label,'exit_code':q.returncode,'meaning':'preserved actual result; inspect before proceeding'})
 print(json.dumps({'label':label,'exit_code':q.returncode,'stdout':q.stdout},ensure_ascii=False))
 return q
EXEC=json.loads(LOG.read_text()) if LOG.exists() else {'case_id':'T','stage':'C','commands':[],'tool_calls':None,'read_files':{},'network_calls':0,'violations':[],'failures_or_nonzero_checks':[{'label':'initial-batched-display','meaning':'Tool display truncated; exact complete resume.py and update-state.py reread, state parsed in full by this script.'}],'written_paths':[],'settings':{'model':None,'temperature':None,'seed':None,'token_budget':None,'system_limit':None},'executor':'AI assistant; no human expert approval'}
def save_log():write(LOG,EXEC)
def commit_state(old,new,rationale):
 target=ROOT/'research/state.json'; expected=read(target)
 if json.loads(expected)!=old:raise RuntimeError('State changed before commit')
 with (ROOT/'research/write.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  if read(target)!=expected:raise RuntimeError('Concurrent state conflict')
  new['metadata_revision']=old['metadata_revision']+1
  archive=ROOT/'.history/metadata'/('revision-'+str(old['metadata_revision'])+'.json')
  if archive.exists() and read(archive)!=expected:raise RuntimeError('Archive conflict')
  if not archive.exists():archive.parent.mkdir(parents=True,exist_ok=True);archive.write_bytes(expected);EXEC['written_paths'].append(str(archive))
  new['history'].append({'revision':new['metadata_revision'],'rationale':rationale,'previous_state':str(archive.relative_to(ROOT))})
  if 'checkpoint' in new and new['checkpoint'].get('stage') in ['C-drift','C-final']:
   new['checkpoint']['metadata_revision']=new['metadata_revision']
  fd,tmp=tempfile.mkstemp(prefix='.state-',dir=target.parent)
  try:
   with os.fdopen(fd,'w') as f:json.dump(new,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
   if read(target)!=expected:raise RuntimeError('Concurrent state changed')
   os.replace(tmp,target); EXEC['written_paths'].append(str(target))
  finally:
   if os.path.exists(tmp):os.unlink(tmp)
def checkpoint(state,stage,next_action):
 return {'stage':stage,'metadata_revision':state['metadata_revision'],'configuration_sha256':dig(state['configuration']),'records_sha256':dig(state['records']),'activities_sha256':dig(state['activities']),'tracked_files':{p:fp(ROOT/p) for p in state['tracked_files']},'next_action':next_action,'note':'Recovery snapshot only; does not rebind old activities or establish scientific validity.'}
try:
 if sys.argv[1]=='prepare':
  # Hash complete bytes for every input actually read and every preserved project file.
  for p in [OUT.parent/'REQUEST.md',INP/'PROTOCOL.md',INP/'RECORDING.md',INP/'STAGE-C.md',INP/'author-revision/AUTHOR-REVISION.md',INP/'author-revision/approved-parameters.json',TOOLKIT/'skills/rw-workflow/SKILL.md',TOOLKIT/'core/skill-bridge.md',TOOLKIT/'core/protocol.md']:read(p)
  before={}
  files=list(sorted(p for p in ROOT.rglob('*') if p.is_file()))
  snap=ROOT/'.history/C-drift'
  if snap.exists():raise RuntimeError('Drift snapshot already exists; refuse overwrite')
  for p in files:
   rel=p.relative_to(ROOT); data=read(p);before[str(rel)]={'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'mtime_ns':p.stat().st_mtime_ns}
   dest=snap/'files'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest);EXEC['written_paths'].append(str(dest))
  write(snap/'manifest.json',before)
  state=load(ROOT/'research/state.json');new=copy.deepcopy(state)
  new['next_action']='先只读检查漂移断点；仅随后按作者批准的 rho=4 参数真实复算并修订摘要。'
  new['checkpoint']=checkpoint(new,'C-drift',new['next_action'])
  commit_state(state,new,'保存未重算漂移态：参数文件已为rho=4，但活动仍绑定rho=1旧指纹；本次保存不构成复核。')
  write(snap/'checkpoint.json',new['checkpoint'])
  q=run([PYTHON,'-I','-B',str(ROOT/'resume.py'),'--root',str(ROOT)],'intermediate-resume')
  if q.returncode!=1:raise RuntimeError('Expected recorded stale check, got '+str(q.returncode))
  report=json.loads(q.stdout)
  assert report['checkpoint_freshness']['fresh'] is True
  assert report['activities']['T-CALC']['effective_status']=='stale'
  assert report['activities']['T-SYNTH']['effective_status']=='stale'
  assert report['activities']['T-SOURCE-CHECK']['effective_status']=='done'
  write(OUT/'intermediate-interpretation.json',{'saved_new_checkpoint':True,'checkpoint_fresh':True,'old_work_revalidated':False,'changed_paths':report['changed_or_missing_paths'],'affected':['T-CALC','T-SYNTH'],'unaffected':['T-SOURCE-CHECK'],'reason':'New snapshot captures current drifted files; old completed activities still reference old parameter bytes and therefore remain stale.'})
 elif sys.argv[1]=='compute':
  approval=load(INP/'author-revision/approved-parameters.json');params=load(ROOT/'notes/parameters.json')
  if approval!=params:raise RuntimeError('Current parameters differ from explicit approval')
  state=load(ROOT/'research/state.json')
  baseline=load(ROOT/'.history/C-drift/manifest.json')
  for rel in ['sources/howard2021-arxiv-v9.pdf','scripts/compute.py']:
   now=fp(ROOT/rel)
   assert now=={k:baseline[rel][k] for k in ('sha256','bytes')}
  q=run([PYTHON,'-I','-B',str(ROOT/'scripts/compute.py'),'--root',str(ROOT),'--output',str(ROOT/'validation/stage-C-recompute')],'recompute')
  if q.returncode:raise RuntimeError('Recomputation failed; canonical outputs unchanged')
  result=load(ROOT/'validation/stage-C-recompute/result.json')
  with (ROOT/'validation/stage-C-recompute/table.csv').open(newline='') as f:rows=list(csv.DictReader(f))
  fp(ROOT/'validation/stage-C-recompute/table.csv')
  expected=[math.sqrt((v+params['rho'])*(math.log(1+v/params['rho'])-2*math.log(params['alpha']))) for v in params['intrinsic_time_grid']]
  checks={'approved_parameters_match':True,'alpha_unchanged':params['alpha']==state['configuration']['current_scope']['alpha'],'rho_policy_unchanged':params['rho_selection']==state['configuration']['current_scope']['rho_selection'],'grid_unchanged':params['intrinsic_time_grid']==state['configuration']['current_scope']['intrinsic_time_grid'],'result_parameters_match':all(result[k]==params[k] for k in ['alpha','rho','rho_selection']),'grid_matches':[x['v'] for x in result['values']]==params['intrinsic_time_grid'],'direct_formula_matches':all(math.isclose(x['boundary'],y,rel_tol=2e-15,abs_tol=1e-14) for x,y in zip(result['values'],expected)),'csv_matches_result':all(float(r['v'])==v['v'] and float(r['boundary'])==v['boundary'] for r,v in zip(rows,result['values'])) and len(rows)==len(result['values']),'result_parameters_sha_matches':result['input_sha256']['parameters']==fp(ROOT/'notes/parameters.json')['sha256'],'calculator_unchanged':result['input_sha256']['calculator']==baseline['scripts/compute.py']['sha256']}
  if not all(checks.values()):raise RuntimeError('Validation failed: '+json.dumps(checks))
  write(OUT/'recompute-verification.json',{'checks':checks,'values':result['values'],'scientific_limit':'Only current fixed-parameter arithmetic checked; no proof, simulation coverage, novelty, human approval or submission.'})
  print(json.dumps({'checks':checks,'values':result['values']},ensure_ascii=False))
 elif sys.argv[1]=='revise':
  verification=load(OUT/'recompute-verification.json')
  assert all(verification['checks'].values())
  state=load(ROOT/'research/state.json')
  if state['metadata_revision']!=2:raise RuntimeError('Unexpected revision; refuse overwrite')
  approval=load(INP/'author-revision/approved-parameters.json')
  prov=ROOT/'provenance/stage-C'
  for name in ['AUTHOR-REVISION.md','approved-parameters.json']:
   source=INP/'author-revision'/name; dest=prov/name;dest.parent.mkdir(parents=True,exist_ok=True)
   dest.write_bytes(read(source));EXEC['written_paths'].append(str(dest))
  for name in ['result.json','table.csv']:
   source=ROOT/'validation/stage-C-recompute'/name;dest=ROOT/'results'/name
   dest.write_bytes(read(source));EXEC['written_paths'].append(str(dest))
  summary='# 修订后的研究摘要\n\n当前 alpha=0.05、rho=4，rho 在观察前固定；评估点为 V=0、1、10、100。固定公式为 sqrt((V+rho)*(log(1+V/rho)+2*log(1/alpha)))，标量 l0=1，alpha 是两侧总错误预算。\n\n| V | 边界值 |\n|---:|---:|\n'
  result=load(ROOT/'results/result.json')
  for x in result['values']:summary+='| '+str(x['v'])+' | '+format(x['boundary'],'.12f')+' |\n'
  summary+='\n对应完整精度结果和表格见 results/result.json 与 results/table.csv。V=10 时边界为 10.070709270873。适用前提是 S 与 −S 对同一个非负内在时间 V 满足所需 sub-Gaussian 指数控制；V 不能被任意经验方差替代。来源身份及卡片范围见 notes/source-check.md。\n\n本次仅按作者授权将预先固定的正 rho 从 1 改为 4，alpha 与预先固定政策未变，并真实重算四点数值、核对表格及修订摘要。该程序复算没有建立新的覆盖保证，也没有进行新证明、覆盖模拟、形式化验证或人类专家认可。旧参数和成果保留在 .history/A-initial/files/，未重算漂移态保留在 .history/C-drift/。\n\n下一步：将 rho=4 的边界表与本摘要交作者内容复核，确认过程控制条件和 V 的含义；暂不扩展到事后选择 rho。没有投稿授权。\n'
  (ROOT/'results/summary.md').write_text(summary);EXEC['written_paths'].append(str(ROOT/'results/summary.md'))
  summary_read=read(ROOT/'results/summary.md').decode()
  assert 'rho=4' in summary_read and '10.070709270873' in summary_read and 'rho=1，' not in summary_read
  config=copy.deepcopy(state['configuration']);config['current_scope']=approval
  next_action='将 alpha=0.05、预先固定 rho=4 的四点边界表（results/table.csv）与更新摘要（results/summary.md）交作者内容复核，确认 V 与给定过程控制条件；暂不扩展到事后选择 rho；没有投稿授权。'
  changes={}
  def change(rid,**fields):
   data=copy.deepcopy(state['records'][rid]['data']);data.update(fields)
   changes[rid]={'expected_version':state['records'][rid]['version'],'data':data}
  change('T-PARAM',sha256=fp(ROOT/'notes/parameters.json')['sha256'],bytes=fp(ROOT/'notes/parameters.json')['bytes'],approved_scope=approval,revision_basis='provenance/stage-C/AUTHOR-REVISION.md')
  change('T-CLAIM',scope={'alpha':0.05,'rho':4.0,'rho_selection':'fixed-before-observation','intrinsic_time_grid':[0,1,10,100],'claim_limit':'Only supplied formula arithmetic under stated sub-Gaussian process conditions; no new coverage proof.'})
  change('T-REL',meaning='作者批准的预先固定 rho=4 参数限定当前数值主张；参数更改并非原论文修订，也非覆盖证明。',parameter_version=2,claim_version=2)
  change('T-CHOICE',meaning='Use author-approved rho=4 fixed before observation; retain alpha .05 and other constraints.',rationale='provenance/stage-C/AUTHOR-REVISION.md accepts current parameters; not new theorem or post-observation tuning.',responsible='benchmark material author supplied revision; assistant executed arithmetic and record revision',evidence=['T-PARAM'],approval_path='provenance/stage-C/approved-parameters.json',approval_sha256=fp(prov/'approved-parameters.json')['sha256'],decided_at=None)
  change('T-RESULT',parameter_scope=approval,revision_basis='validation/stage-C.json',sha256=fp(ROOT/'results/result.json')['sha256'],companion_paths=['results/table.csv'])
  change('T-SUMMARY',parameter_scope=approval,revision_basis='validation/stage-C.json',sha256=fp(ROOT/'results/summary.md')['sha256'])
  change('T-CALC',status='done',execution_evidence='validation/stage-C.json',scope='Actual recomputation with approved rho=4; full result/CSV and direct formula comparison; no proof.')
  change('T-SYNTH',status='done',execution_evidence='validation/stage-C.json',scope='Summary revised and read against actual rho=4 values and unchanged conditional scope; awaits author content review.')
  patch={'rationale':'作者明确批准 rho=4；已真实重算并核对数值/CSV、改写和读取摘要；保留旧成果和漂移检查，不重做独立来源身份核验。','configuration':config,'records':changes,'next_action':next_action}
  write(prov/'metadata-patch.json',patch)
  q=run([PYTHON,'-I','-B',str(ROOT/'update-state.py'),'--root',str(ROOT),'--expected-revision','2','--patch',str(prov/'metadata-patch.json')],'metadata-revision')
  if q.returncode:raise RuntimeError('Metadata revision failed; no activity rebinding attempted')
  revised=load(ROOT/'research/state.json');new=copy.deepcopy(revised)
  # Rebind only the two activities actually recalculated/reviewed in this stage.
  for aid in ['T-CALC','T-SYNTH']:
   a=new['activities'][aid]
   a['captured_files']={p:fp(ROOT/p) for p in a['captured_files']}
   a['captured_records']={rid:{'version':new['records'][rid]['version'],'content_sha256':dig(new['records'][rid])} for rid in a['captured_records']}
   a['declared_status']='done';a['executor']='AI assistant; no independent human review';a['evidence']='validation/stage-C.json'
   a['revalidation_reason']='Actual approved-rho recomputation and comparison' if aid=='T-CALC' else 'Actual summary revision and numerical/conditional-scope review after T-CALC'
  assert new['activities']['T-SOURCE-CHECK']==state['activities']['T-SOURCE-CHECK']
  baseline=load(ROOT/'.history/C-drift/manifest.json')
  unchanged={}
  for rel in ['sources/howard2021-arxiv-v9.pdf','scripts/compute.py','notes/source-check.md','notes/parameters.json']:
   current=fp(ROOT/rel)
   unchanged[rel]={'bytes_sha_unchanged':current=={k:baseline[rel][k] for k in ('sha256','bytes')},'mtime_unchanged':(ROOT/rel).stat().st_mtime_ns==baseline[rel]['mtime_ns']}
  assert all(all(v.values()) for v in unchanged.values())
  validation={'case_id':'T','stage':'C','executor':'AI assistant','recomputation':verification,'summary_review':{'read_complete_summary':True,'rho4_and_v10_match':True,'conditions_preserved':True,'awaiting_author_content_review':True},'unchanged_materials':unchanged,'source_activity_rebound':False,'independent_source_reason':'T-SOURCE-CHECK inputs, output, captured records and bytes unchanged; rho is not its dependency.','commands':[c for c in EXEC['commands'] if c['argv'][3:4] != ['resume.py']],'human_expert_approval':False,'formal_verification':'not-started','external_submission_authorized':False,'intermediate_check':{'exit_code':1,'checkpoint_fresh':True,'activities_still_stale':['T-CALC','T-SYNTH'],'raw_output_preserved_in_project':'validation/stage-C-intermediate-resume.stdout'}}
  write(ROOT/'validation/stage-C.json',validation)
  for filename in ['intermediate-resume.stdout','intermediate-resume.stderr','intermediate-interpretation.json']:
   (ROOT/'validation'/('stage-C-'+filename)).write_bytes(read(OUT/filename));EXEC['written_paths'].append(str(ROOT/'validation'/('stage-C-'+filename)))
  new['tracked_files']={p:fp(ROOT/p) for p in new['tracked_files']}
  new['scientific_scope']['assessment']='rho=4 specified numerical values, result/CSV correspondence and revised summary checked by AI assistant; proof, simulation coverage, novelty and human approval not assessed'
  new['checkpoint']=checkpoint(new,'C-final',next_action)
  commit_state(revised,new,'真实完成 rho=4 复算、结果/CSV 对照与摘要内容范围复核后，显式重新绑定 T-CALC/T-SYNTH；独立来源分支原记录保留。')
  write(ROOT/'research/checkpoints/C-final.json',new['checkpoint'])
  project='# 固定精度正态混合边界数值核对\n\n唯一权威状态为 research/state.json，当前元数据修订4，alpha=0.05、rho=4，rho在观察前固定；截止日2026-12-15，期刊未定。预算限离线Python标准库，不采新数据、不重新拟合，原PDF仅作私有缓存，不向仓库分发。\n\n恢复：在本项目根执行 python3 -I -B resume.py，或指定 --root PROJECT。退出0表示已声明的文件/记录/活动/断点未发现漂移；1表示漂移或失效；2表示读取或接口错误。恢复只读，不依赖外部报告、原输入目录或指导工具包。PROJECT.md与历史断点不反向覆盖当前JSON。\n\n阶段C先将未重算漂移态完整保存在.history/C-drift/files/及manifest.json，保存新断点后实际只读检查仍退出1：T-CALC和T-SYNTH失效，T-SOURCE-CHECK仍完成。validation/stage-C-intermediate-resume.stdout保留该原始结果；新断点没有使旧工作恢复有效。随后按provenance/stage-C/中的明确授权真实重算到validation/stage-C-recompute/，核对公式、结果JSON和CSV，更新results/summary.md，并显式重新绑定两项受影响活动。validation/stage-C.json保留执行及范围证据。初始rho=1参数、结果、表格、摘要完整字节仍在.history/A-initial/files/，metadata旧版本在.history/metadata/。\n\n原PDF、计算器、固定来源卡片及当前参数文件字节和mtime保持不变；只有成果和管理状态依授权更新。独立来源核验分支的输入、输出及记录没有改变，因此继续有效；本轮仅核对其身份完整性，未审查PDF公式或证明。远端T-REMOTE只有元数据身份，未联网核对内容。notes/unregistered-scratch.md未进入活动自动失效覆盖；历史快照保存字节不等于科学核验。\n\n下一步：将rho=4的边界表与更新摘要交作者内容复核，确认内在时间V和sub-Gaussian过程条件；暂不扩展到事后选择rho。没有人类专家认可、新覆盖证明、形式化验证或投稿授权。\n\n修改权威配置/记录可用update-state.py --expected-revision N --patch PATCH.json；它要求修订理由及预期版本，保留旧状态并拒绝冲突，不会自动重新绑定活动或更新检查点。活动重绑定只应在实际复核后进行。阶段C已实际运行本地接口完成受授权修订。\n'
  (ROOT/'PROJECT.md').write_text(project);EXEC['written_paths'].append(str(ROOT/'PROJECT.md'))
  q=run([PYTHON,'-I','-B',str(ROOT/'resume.py'),'--root',str(ROOT)],'final-resume')
  if q.returncode:raise RuntimeError('Final state check failed; preserve output and repair explicitly')
  final=json.loads(q.stdout)
  assert final['active_constraints']['current_scope']==approval
  assert all(a['effective_status']=='done' for a in final['activities'].values())
  assert final['checkpoint_freshness']['fresh']
  write(OUT/'state-answer.json',dict(final,stage='C',affected_activities=['T-CALC','T-SYNTH'],unaffected_activities=['T-SOURCE-CHECK'],material_paths={'result':'results/result.json','table':'results/table.csv','summary':'results/summary.md','revision':'provenance/stage-C/AUTHOR-REVISION.md','drift_snapshot':'.history/C-drift/','initial':'.history/A-initial/files/'},notes=['Checkpoint save alone did not validate old completed activities.','Only after actual rerun/review were two affected activities rebound.','All stated done activities mean bounded declared work, not scientific approval.']))
 else:raise ValueError('Unknown mode')
finally:save_log()
