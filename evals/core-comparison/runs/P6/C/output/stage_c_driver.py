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


def recompute():
 old=load(ROOT/'records/state.json');assert old['state_version']==2
 approved=load(IN/'author-revision/approved-parameters.json');current=load(ROOT/'notes/parameters.json')
 assert current==approved,'Current parameters must match author authorization'
 frozen=['data/hour_2011.csv','model/frozen.json','scripts/compute.py','scripts/project_status.py','scripts/guarded_state_update.py','notes/source-check.md']
 before={x:fp(ROOT/x) for x in frozen};prior={r['id']:r for r in old['records']}
 for k in ['D-RAW','D-MODEL','D-CODE','D-SOURCE-NOTE']:
  r=prior[k];assert fp(ROOT/r['path'])==r['binding'],'Preserved input changed: '+k
 out=ROOT/'results-evaluations/C-approved'
 v=run([PY,'-I','-B',str(ROOT/'scripts/compute.py'),'--root',str(ROOT),'--spec',str(ROOT/'notes/parameters.json'),'--output',str(out)],'approved-recomputation',[ROOT/'scripts/compute.py',ROOT/'notes/parameters.json',ROOT/'data/hour_2011.csv',ROOT/'model/frozen.json'])
 if v.returncode:raise RuntimeError('Authorized calculator failed; do not mark work complete')
 result=load(out/'result.json');model=load(ROOT/'model/frozen.json')
 rows=list(csv.DictReader(io.StringIO(read(ROOT/'data/hour_2011.csv').decode())))
 selected=[r for r in rows if approved['evaluation_start']<=r['dteday']<=approved['evaluation_end']]
 assert result['observed_hours']==len(selected) and result['observed_days']==len({r['dteday'] for r in selected})
 metrics={}
 for name in ['C0','C1']:
  errors=[]
  for r in selected:
   base=model['C0'][r['hr']];prediction=base if name=='C0' else model['C1'].get(r['workingday']+':'+r['hr'],base)
   errors.append(prediction-int(r['cnt']))
  metrics[name+'_MAE']=math.fsum(abs(e) for e in errors)/len(errors)
  metrics[name+'_RMSE']=math.sqrt(math.fsum(e*e for e in errors)/len(errors))
  metrics[name+'_bias_prediction_minus_actual']=math.fsum(errors)/len(errors)
 metrics['MAE_reduction_fraction']=1-metrics['C1_MAE']/metrics['C0_MAE']
 for k,val in metrics.items():assert result[k]==val,k+' metric mismatch'
 table=list(csv.DictReader(io.StringIO(read(out/'table.csv').decode())))
 for row in table:assert float(row['value'])==result[row['metric']]
 assert result['input_sha256']=={'parameters':fp(ROOT/'notes/parameters.json')['sha256'],'calculator':before['scripts/compute.py']['sha256'],'hour_2011':before['data/hour_2011.csv']['sha256'],'frozen_model':before['model/frozen.json']['sha256']}
 old_result=load(ROOT/'snapshots/initial/results/result.json')
 summary=(f"# 当前研究摘要\n\n冻结2011年1月至9月的C0/C1参数，在2011-11-01至2011-12-31的{result['observed_hours']}个实际观察小时、{result['observed_days']}日上比较。C0 MAE={result['C0_MAE']:.12f}，C1 MAE={result['C1_MAE']:.12f}，相对降低{result['MAE_reduction_fraction']*100:.8f}%。C0 RMSE={result['C0_RMSE']:.12f}，C1 RMSE={result['C1_RMSE']:.12f}；预测减实际的平均偏差分别为{result['C0_bias_prediction_minus_actual']:.12f}和{result['C1_bias_prediction_minus_actual']:.12f}。\n\n作者授权将评价窗口从Q4改为11月至12月。原Q4结果（{old_result['observed_hours']}观察小时、{old_result['observed_days']}日，MAE相对降低{old_result['MAE_reduction_fraction']*100:.8f}%）保留在snapshots/initial/results/；修订前的实际漂移状态另存snapshots/stage-C-before-recompute/。新旧降幅来自不同评价窗口，不能作为重训或模型改善的证据。\n\n数值见results/result.json及results/table.csv。本次为固定模型的观察小时描述性比较，无置信区间，不作因果或2012表现保证。当前成果等待作者内容复核，未有人类专家认可或投稿授权。\n")
 for rel in ['result.json','table.csv']:
  assert fp(ROOT/'results'/rel)==fp(ROOT/'snapshots/stage-C-before-recompute/results'/rel),'Unpreserved result change'
  write(ROOT/'results'/rel,read(out/rel))
 write(ROOT/'results/summary.md',summary)
 for rel in ['result.json','table.csv']:assert read(ROOT/'results'/rel)==read(out/rel)
 for x in frozen:assert fp(ROOT/x)==before[x],'Preserved file unexpectedly modified: '+x
 actual_summary=read(ROOT/'results/summary.md').decode()
 for val in [str(len(selected)),str(result['observed_days']),'2011-11-01','2011-12-31']+[f"{result[k]:.12f}" for k in metrics if k!='MAE_reduction_fraction']+[f"{result['MAE_reduction_fraction']*100:.8f}",f"{old_result['MAE_reduction_fraction']*100:.8f}"]:
  assert val in actual_summary,'Summary mismatch: '+val
 validation={'case_id':'D','stage':'C','executed_calculator_exit':v.returncode,'approved_parameters_match':True,'observed_hours':len(selected),'observed_days':len({r['dteday'] for r in selected}),'independent_metrics':metrics,'independent_metric_comparison':'Exact float agreement using supplied fixed predictions; no refit','companion_table_agrees':True,'canonical_matches_actual_run':True,'summary_dates_counts_metrics_scope_checked':True,'immutable_before':before,'immutable_after':{x:fp(ROOT/x) for x in frozen},'source_branch':'Unchanged identity, inputs, output and completion bindings; no repeat of source activity required','executor':'AI agent and standard-library numerical checks','human_expert_approval':False,'submission_authorized':False}
 save(ROOT/'records/validation-C.json',validation);save(OUT/'validation-C.json',validation)
 s=copy.deepcopy(old);s['state_version']+=1;s['configuration']['current_scope']=approved;rec={r['id']:r for r in s['records']}
 reason='Author-authorized Q4 to November–December window change, unchanged frozen model; actual recomputation and summary review completed by AI executor.'
 for k in ['D-PARAM','D-CLAIM','D-REL','D-CHOICE','D-RESULT','D-TABLE','D-SUMMARY','D-CALC','D-SYNTH']:rec[k]['version']+=1;rec[k]['revision_reason']=reason
 rec['D-PARAM']['binding']=fp(ROOT/'notes/parameters.json');rec['D-PARAM']['specification']=approved
 rec['D-PARAM']['authorization']='provenance/task-C/author-revision/AUTHOR-REVISION.md'
 rec['D-CLAIM']['scope']='2011-11-01 through 2011-12-31; observed-hour weighting; supplied Jan–Sep frozen C0/C1; descriptive time holdout; no model-training-improvement conclusion'
 rec['D-REL']['rationale']='Approved November–December parameters qualify the numerical comparison; source and frozen model unchanged.'
 rec['D-CHOICE']['choice']='Use author-approved November–December 2011 evaluation window with unchanged frozen model'
 rec['D-CHOICE']['rationale']='Explicit authorization in provenance/task-C/author-revision/; original Q4 content remains in snapshots/initial and drift snapshot.'
 rec['D-CHOICE']['responsible']='Benchmark author authorizes; AI executor implemented; no human content approval inferred'
 rec['D-CHOICE']['authorization']='provenance/task-C/author-revision/AUTHOR-REVISION.md'
 for k in ['D-RESULT','D-TABLE','D-SUMMARY']:rec[k]['binding']=fp(ROOT/rec[k]['path'])
 rec['D-CALC']['status']='done';rec['D-CALC']['completion_scope']='Actual supplied-script execution exit 0 on approved November–December window; canonical result/table match actual output; independent fixed-prediction metrics agree; no retraining.'
 rec['D-CALC']['evidence']=['records/validation-C.json','records/commands-C.json']
 rec['D-SYNTH']['status']='done';rec['D-SYNTH']['completion_scope']='AI executor revised and checked dates, counts, MAE/RMSE/bias/reduction, Q4-history comparison and scope against recomputed canonical result; awaiting author content review.'
 rec['D-SYNTH']['evidence']=['records/validation-C.json','results/summary.md']
 for activity in ['D-CALC','D-SYNTH']:
  bindings={}
  for k in prior[activity]['completion_bindings']:
   r=rec[k];b={'version':r['version'],'record_sha256':sig(r)}
   if 'path'in r:b.update({'path':r['path'],'file':fp(ROOT/r['path'])})
   bindings[k]=b
  rec[activity]['completion_bindings']=bindings
 assert rec['D-SOURCE-CHECK']==prior['D-SOURCE-CHECK'],'Do not revise independent source activity'
 next_action='将2011年11月至12月的冻结模型指标与更新摘要交作者内容复核；保留原Q4结果作历史记录。不重训、不外推2012；尚未有人类专家认可，也没有投稿授权。'
 s['checkpoint']=cp(s,next_action);s=commit(s,old,reason,'authorized-state-update')
 recover=['# 恢复与权威状态','',f"唯一当前配置与逻辑记录为records/state.json（state_version={s['state_version']}）。实际材料与绑定冲突时应报告并复核；旧handoff或笔记不能覆盖新显式修订。",'', '只读恢复：用Python 3标准库解释器执行 python -I -B ROOT/scripts/project_status.py --root ROOT。脚本及guarded_state_update.py都在项目内，迁移只需替换ROOT，无需外部输出或指导包。退出0为身份/依赖/配置/断点一致，1为漂移/陈旧，2为读取/格式错误；不认证科学正确性。','', '当前范围：2011-11-01至2011-12-31，observed-hour权重，冻结2011年1至9月模型。其他约束保留：截止2026-12-15，仅本地标准库，不采集新数据、不重新拟合，期刊未定。provenance/initial/保留初始约束和来源；provenance/task-C/保留当前授权。','', '当前具体下一步：'+next_action,'', '先将实际漂移状态和旧完成绑定保存到snapshots/stage-C-before-recompute/，再保存新断点。records/intermediate-check-C.json显示断点current但D-CALC/D-SYNTH仍stale，D-SOURCE-CHECK仍done。之后实际执行原脚本，更新参数/主张/关系/选择/成果与两个受影响活动。records/validation-C.json及records/commands-C.json保留证据，results-evaluations/C-approved/保留实际运行输出。','', '初始参数及Q4 result/table/summary原字节在snapshots/initial/。漂移时实际内容在snapshots/stage-C-before-recompute/，每次权威更新旧state在snapshots/authority/。guarded_state_update.py要求旧state SHA与版本，拒绝旧版本覆盖；不要仅刷新断点以掩盖陈旧活动。','', '跟踪8个材料路径。D-REMOTE只有DOI身份，没有本地全文/当前远端检查；notes/unregistered-scratch.md未登记，不自动检查其内容或依赖。notes/rejected-parameters.json为旧失败试算输入，未用于当前工作。CSV是私人研究缓存，原始PDF/CSV不得公开分发。本次未读取原始完整hour.csv或ZIP、未联网、未重训；来源卡给出的17379与17389行差异保留。没有人类专家认可或投稿授权。']
 write(ROOT/'RECOVER.md','\n'.join(recover)+'\n')
 final=status('final-check')
 if final.returncode:raise RuntimeError('Final check failed; do not declare completion')
 E['remedies'].append({'for':'pre-recomputation stale activities','action':'Actual authorized recomputation, metric/table/summary review, explicit affected-record and completion binding updates; final checkpoint saved','evidence':'final-check.stdout.json'})
 save(ROOT/'records/commands-C.json',E['commands']);save(ROOT/'records/checkpoint-C-final.json',s['checkpoint']);write(ROOT/'records/final-check-C.json',final.stdout)
 save(OUT/'recomputed-result.json',result);flush()
 print(json.dumps({'new_result':result,'final_check_exit':final.returncode,'state_version':s['state_version'],'next_action':next_action},ensure_ascii=False))

if __name__=='__main__':
 E['tool_calls']+=1
 fp(Path(__file__))
 try:
  if sys.argv[1]=='snapshot':snapshot()
  elif sys.argv[1]=='recompute':recompute()
  else:raise ValueError('unknown mode')
 except Exception as e:
  E['failures'].append({'kind':'unexpected execution error','type':type(e).__name__,'message':str(e)});flush();raise
 flush()
