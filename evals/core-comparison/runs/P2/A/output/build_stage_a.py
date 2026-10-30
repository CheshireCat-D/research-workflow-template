from pathlib import Path
import csv, datetime, hashlib, io, json, math, os, re, shutil, subprocess, sys

BASE=Path('STUDY_ROOT/runs/P2/A')
INP=BASE/'input'; OUT=BASE/'output'; ROOT=BASE.parent/'project'
PYTHON='EVAL_PYTHON'
CWD=str(Path.cwd())
reads={}; commands=[]; writes=[]
def digest_bytes(b): return hashlib.sha256(b).hexdigest()
def read(p,scope='full file bytes'):
    p=Path(p); b=p.read_bytes(); reads[str(p)]={'path':str(p),'sha256':digest_bytes(b),'bytes':len(b),'read_scope':scope}; return b
def load(p): return json.loads(read(p))
def obj(p):
    b=read(p); return {'sha256':digest_bytes(b),'bytes':len(b)}
def dump(p,v):
    p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8'); writes.append(str(p))
def textfile(p,v):
    p.parent.mkdir(parents=True,exist_ok=True); p.write_text(v,encoding='utf-8'); writes.append(str(p))
def run(argv):
    p=subprocess.run(argv,cwd=str(ROOT),capture_output=True,text=True)
    r={'argv':argv,'cwd':str(ROOT),'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr}; commands.append(r); return r

def tree_snapshot(root):
    return {str(p.relative_to(root)):{'kind':'directory' if p.is_dir() else 'file','mtime_ns':p.stat().st_mtime_ns,**({} if p.is_dir() else obj(p))} for p in sorted(root.rglob('*'))}

request=BASE/'REQUEST.md'; read(request)
for p in sorted(INP.rglob('*')):
    if p.is_file(): read(p)
constraints=load(INP/'initial/constraints.json'); obligations=load(INP/'initial/obligations.json'); identities=load(INP/'initial/source-identities.json'); supplied=load(INP/'initial/MANIFEST.json')
manifest_checks=[]
for rel,expected in supplied['files'].items():
    actual=obj(INP/'initial'/rel); manifest_checks.append({'path':rel,'expected':expected,'actual':actual,'match':expected==actual})
assert all(x['match'] for x in manifest_checks),'Initial manifest mismatch'
if ROOT.exists(): raise RuntimeError('Project already exists; refusing to overwrite')
ROOT.mkdir()
for p in sorted((INP/'initial/project_payload').rglob('*')):
    rel=p.relative_to(INP/'initial/project_payload'); q=ROOT/rel
    if p.is_dir(): q.mkdir(parents=True,exist_ok=True)
    else: q.parent.mkdir(parents=True,exist_ok=True); q.write_bytes(read(p)); writes.append(str(q))
MG=ROOT/'management'; MG.mkdir()
for name in ['BRIEF.md','constraints.json','obligations.json','source-identities.json','MANIFEST.json']:
    q=MG/name; q.write_bytes(read(INP/'initial'/name)); writes.append(str(q))
for name in ['PROTOCOL.md','RECORDING.md','STAGE-A.md']:
    q=MG/'protocol'/name; q.parent.mkdir(exist_ok=True); q.write_bytes(read(INP/name)); writes.append(str(q))
q=MG/'protocol/REQUEST.md'; q.write_bytes(read(request)); writes.append(str(q))
version_paths=['notes/parameters.json','results/result.json','results/table.csv','results/summary.md']
versions=[]
for rel in version_paths:
    p=ROOT/rel; q=MG/'versions/A-initial'/rel; q.parent.mkdir(parents=True,exist_ok=True); q.write_bytes(read(p)); writes.append(str(q))
    versions.append({'logical_path':rel,'version':'A-initial','snapshot_path':str(q.relative_to(ROOT)),**obj(q),'rationale':'本阶段收到的初始版本；任何后续修订须保留该原字节和修订依据。'})

normal_out=OUT/'verification-normal'
normal_argv=[PYTHON,'-I','-B',str(ROOT/'scripts/compute.py'),'--root',str(ROOT),'--output',str(normal_out)]
normal=run(normal_argv)
assert normal['exit_code']==0,normal
result=load(ROOT/'results/result.json'); verified=load(normal_out/'result.json')
normal_equal={rel:read(ROOT/'results'/rel)==read(normal_out/rel) for rel in ['result.json','table.csv']}
assert all(normal_equal.values()),normal_equal
rows=list(csv.DictReader(io.StringIO(read(ROOT/'data/hour_2011.csv').decode('utf-8'))))
params=load(ROOT/'notes/parameters.json'); model=load(ROOT/'model/frozen.json')
selected=[r for r in rows if params['evaluation_start']<=r['dteday']<=params['evaluation_end']]
source_observations={'row_count':len(rows),'yr_values':sorted(set(r['yr'] for r in rows)),'date_min':min(r['dteday'] for r in rows),'date_max':max(r['dteday'] for r in rows),'evaluation_observed_hours':len(selected),'evaluation_observed_days':len({r['dteday'] for r in selected}),'local_sha_matches_identity':obj(ROOT/'data/hour_2011.csv')['sha256']==identities['primary']['sha256'],'full_original_hour_csv_available':False,'remote_access_performed':False}
assert len(rows)==8645 and source_observations['yr_values']==['0'] and len(selected)==2203
assert result['observed_hours']==len(selected) and result['observed_days']==92
numeric={}
for label in ['C0','C1']:
    errors=[]
    for row in selected:
        a=model['C0'][row['hr']]; prediction=a if label=='C0' else model['C1'].get(row['workingday']+':'+row['hr'],a)
        errors.append(prediction-int(row['cnt']))
    numeric[label+'_MAE']=math.fsum(abs(e) for e in errors)/len(errors)
    numeric[label+'_RMSE']=math.sqrt(math.fsum(e*e for e in errors)/len(errors))
    numeric[label+'_bias_prediction_minus_actual']=math.fsum(errors)/len(errors)
numeric['MAE_reduction_fraction']=1-numeric['C1_MAE']/numeric['C0_MAE']
assert all(math.isclose(v,result[k],rel_tol=1e-14,abs_tol=1e-14) for k,v in numeric.items())
table=list(csv.DictReader(io.StringIO(read(ROOT/'results/table.csv').decode('utf-8'))))
assert all(math.isclose(float(r['value']),result[r['metric']],rel_tol=1e-14,abs_tol=1e-14) for r in table)
summary=read(ROOT/'results/summary.md').decode('utf-8')
summary_checks={'dates_and_counts':all(t in summary for t in ['2011-10-01','12-31','2203','92']),'rounded_MAE':all(format(result[k],'.12f') in summary for k in ['C0_MAE','C1_MAE']),'reduction_percent':format(100*result['MAE_reduction_fraction'],'.8f')+'%' in summary,'bounded_scope':all(t in summary for t in ['不重训','因果','2012','无置信区间'])}
assert all(summary_checks.values()),summary_checks
before_invalid=tree_snapshot(ROOT)
bad_out=OUT/'verification-rejected'
bad_argv=[PYTHON,'-I','-B',str(ROOT/'scripts/compute.py'),'--root',str(ROOT),'--spec',str(ROOT/'notes/rejected-parameters.json'),'--output',str(bad_out)]
bad=run(bad_argv)
after_invalid=tree_snapshot(ROOT)
bad_check={'expected_exit_code':2,'actual_exit_code':bad['exit_code'],'error':json.loads(bad['stderr']),'output_directory_exists':bad_out.exists(),'project_tree_bytes_and_mtimes_unchanged':before_invalid==after_invalid,'canonical_results_before':{p:before_invalid[p] for p in ['results/result.json','results/table.csv','results/summary.md']},'canonical_results_after':{p:after_invalid[p] for p in ['results/result.json','results/table.csv','results/summary.md']},'meaning':'有意提交起点晚于终点的无效评价期；这是受控输入拒绝测试，不是实际科学研究分析失败。'}
assert bad['exit_code']==2 and not bad_out.exists() and before_invalid==after_invalid
E=MG/'evidence/A'; E.mkdir(parents=True)
for rel in ['result.json','table.csv']:
    q=E/'normal-run'/rel; q.parent.mkdir(exist_ok=True); q.write_bytes(read(normal_out/rel)); writes.append(str(q))
evidence={'normal_command':normal,'rejected_command':bad,'initial_manifest_checks':manifest_checks,'normal_equals_canonical_bytes':normal_equal,'independent_metric_recalculation':numeric,'table_agrees_with_result':True,'summary_checks':summary_checks,'source_observations':source_observations,'invalid_input_test':bad_check}
dump(E/'checks.json',evidence)
# Keep the pre/post evidence itself in the project, independent of external execution files.
dump(E/'invalid-before.json',before_invalid); dump(E/'invalid-after.json',after_invalid)

status_source=r'''from pathlib import Path
import argparse, hashlib, json, sys

def main():
    a=argparse.ArgumentParser(description='Read-only project identity and dependency recovery; no scientific certification')
    a.add_argument('--root',type=Path,default=Path(__file__).resolve().parent.parent)
    args=a.parse_args(); root=args.root.resolve()
    state=json.loads((root/'management/state.json').read_text(encoding='utf-8'))
    changes=[]; current={}
    for rel,ref in state['tracked_files'].items():
        p=root/rel
        if not p.is_file(): changes.append({'path':rel,'state':'missing','expected_sha256':ref['sha256']}); continue
        b=p.read_bytes(); h=hashlib.sha256(b).hexdigest(); current[rel]={'sha256':h,'bytes':len(b)}
        if h!=ref['sha256'] or len(b)!=ref['bytes']: changes.append({'path':rel,'state':'changed','expected_sha256':ref['sha256'],'current_sha256':h,'current_bytes':len(b)})
    changed_paths={c['path'] for c in changes}
    directly_changed=set()
    for node in state['logical_nodes']:
        if set(node.get('material_paths',[])) & changed_paths: directly_changed.add(node['id'])
    affected=set(directly_changed)
    while True:
        nxt=affected|{n['id'] for n in state['logical_nodes'] if set(n.get('dependencies',[])) & affected}
        if nxt==affected: break
        affected=nxt
    activities=state['activities']
    affected_activities=sorted(a for a in activities if a in affected)
    unaffected=sorted(a for a in activities if a not in affected)
    constraint_changes=changed_paths & {'management/constraints.json','management/obligations.json','management/source-identities.json','management/state.json'}
    if constraint_changes:
        affected_activities=sorted(activities); unaffected=[]
    snapshots=[]
    for version in state['versions']:
        p=root/version['snapshot_path']
        h=hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
        snapshots.append({'logical_path':version['logical_path'],'snapshot_path':version['snapshot_path'],'intact':h==version['sha256']})
    actual_parameters=None
    try: actual_parameters=json.loads((root/'notes/parameters.json').read_text(encoding='utf-8'))
    except (ValueError,OSError) as e: actual_parameters={'read_error':str(e)}
    answer={'case_id':state['case_id'],'state_authority':'management/state.json with supplied governance; current bytes take precedence over old recorded completion','active_parameters_observed':actual_parameters,'authoritative_constraints_at_checkpoint':state['active_constraints'],'changed_or_missing_paths':changes,'affected_activities':affected_activities,'unaffected_activities':unaffected,'checkpoint_freshness':'fresh-for-registered-local-files' if not changes else 'stale-requires-reconciliation','scientific_scope':state['scientific_scope'],'source_tracking_limits':state['source_tracking_limits'],'versions':snapshots,'next_action':state['next_action'] if not changes else '先按changed_or_missing_paths核对当前作者依据，保留旧内容；对受影响活动重新核验并更新权威状态。旧done/checkpoint不代表当前结果仍有效。','writes_project':False}
    print(json.dumps(answer,ensure_ascii=False,indent=2)); return 0 if not changes and all(v['intact'] for v in snapshots) else 3
if __name__=='__main__': raise SystemExit(main())
'''
textfile(MG/'status.py',status_source)
source_limits={'D-SRC':'已绑定本地2011切片全字节与8645行；来源标题、DOI、许可证和原hour.csv散列来自提供的身份文件。本阶段离线，未重取官方ZIP、全文或原完整CSV，不能独立确认远端版本及完整CSV行数。','D-REMOTE':'仅DOI身份，无本地文章副本，未读取文章内容或检查当前远端内容；不纳入本地依赖自动检查。','notes/unregistered-scratch.md':'已按原字节复制，但不登记为科学输入/输出/依赖，不纳入status自动变化检测。','source_card_discrepancy':'卡片称完整CSV17379行、官网metadata17389；该原始差异保留。当前仅可直接验证2011切片8645行。','publication_rule':identities['publication_rule']}
scope='2011-10-01至2011-12-31、2203实际观察小时/92日；固定2011年1至9月C0/C1模型；observed-hour MAE、RMSE、预测减实际偏差；描述性时间留出比较，无重训、置信区间、因果或2012/任意未来保证。'
next_action='当前指标、表格、摘要已核对；下一步由作者讨论2011第四季度冻结模型比较及其研究表述。尚无作者审阅决定；不发送、不投稿、不重训、不外推2012。继续前运行 management/status.py 检查依赖新鲜度。'
node_files={'D-SRC':['management/source-identities.json'],'D-REMOTE':[],'D-RAW':['data/hour_2011.csv'],'D-PARAM':['notes/parameters.json'],'D-CLAIM':['management/constraints.json'],'D-REL':[],'D-CHOICE':['notes/parameters.json'],'D-CODE':['scripts/compute.py'],'D-MODEL':['model/frozen.json'],'D-RESULT':['results/result.json','results/table.csv'],'D-SUMMARY':['results/summary.md'],'D-SOURCE-NOTE':['notes/source-check.md'],'D-SOURCE-CHECK':[],'D-CALC':[],'D-SYNTH':[]}
nodes=[]
for old in obligations['nodes']:
    n=dict(old); deps=[]
    deps.extend(old.get('derived_from',[])); deps.extend(old.get('inputs',[])); deps.extend(old.get('depends_on',[]))
    if old['id']=='D-SOURCE-CHECK': deps+=['D-SOURCE-NOTE']
    if old['id']=='D-CALC': deps+=['D-RESULT']
    if old['id']=='D-SYNTH': deps+=['D-SUMMARY']
    if old['id']=='D-SOURCE-NOTE': deps+=['D-SRC','D-RAW']
    if old['id']=='D-CHOICE': deps+=['D-PARAM']
    if old['id']=='D-REL': deps+=['D-PARAM','D-CLAIM']
    # Frozen model provenance is recorded separately: evaluation never refits the model.
    n['dependencies']=list(dict.fromkeys(deps)); n['material_paths']=node_files[old['id']]; nodes.append(n)
tracked_paths=set(obligations['local_tracking_paths']+[obligations['companion_deliverable'],'management/constraints.json','management/obligations.json','management/source-identities.json','management/BRIEF.md','management/status.py'])
# Evidence and snapshots are checked too; they never expand scratch or remote scientific coverage.
tracked_paths.update(str(p.relative_to(ROOT)) for p in sorted((MG/'versions').rglob('*')) if p.is_file())
tracked_paths.update(str(p.relative_to(ROOT)) for p in sorted(E.rglob('*')) if p.is_file())
tracked={rel:obj(ROOT/rel) for rel in sorted(tracked_paths)}
activities={}
for aid in obligations['required_completed_activities']:
    node=next(n for n in nodes if n['id']==aid)
    bind_ids=node.get('inputs',[])+node.get('outputs',[])
    paths=sorted({p for n in nodes if n['id'] in bind_ids for p in n['material_paths']})
    activities[aid]={'status':'done','status_meaning':'本阶段限定工作已实际完成；不等于专家科学认证、形式化证明或未来版本有效。','evidence':'management/evidence/A/checks.json','bound_materials':{p:obj(ROOT/p) for p in paths},'verification':{'D-SOURCE-CHECK':'验证所给本地身份、完整散列、2011行数及来源卡口径；原完整数据和远端信息仍为提供方陈述。','D-CALC':'实际运行供给计算器，和预制JSON/表格逐字节相符，并另用标准库按定义重算全部指标。','D-SYNTH':'核对预制摘要评价范围、观察数、MAE和降低比例及边界表述；未冒称从零创作。'}[aid]}
state={'schema_version':1,'case_id':'D','stage':'A','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'authority':'management/state.json 是项目生命周期记录唯一权威；management/constraints.json保存所给约束，notes/parameters.json为实际运行参数。新字节/经授权新决定优先于旧done，需显式保留版本后更新此记录。','active_constraints':constraints,'research_question':constraints['interest'],'logical_nodes':nodes,'activities':activities,'decision':{'id':'D-CHOICE','choice':'使用所给初始2011第四季度评价参数和现有冻结模型','author':'material provider','authorization':'initial supplied request; no human approval invented','evidence':['management/constraints.json','notes/parameters.json'],'no_revisions_in_A':True},'tracked_files':tracked,'versions':versions,'checkpoint':{'id':'A-verified-initial','status':'fresh-for-bound-local-files','bound_paths':list(tracked),'evidence':'management/evidence/A/checks.json','not_scientific_certification':True},'scientific_scope':scope,'source_tracking_limits':source_limits,'next_action':next_action,'unknowns':{'human_expert_approval':None,'author_discussion_decision':None,'target_journal':None,'model':None,'temperature':None,'seed':None,'token_budget':None},'history':[{'stage':'A','event':'保留初始字节，验证正常运行与摘要，有意无效参数被拒，原有效结果不变。','before_version':'A-initial','evidence':'management/evidence/A/checks.json','next_action':next_action}]}
dump(MG/'state.json',state)
readme='''# 项目恢复入口

权威状态是 `management/state.json`；给定的研究约束、逻辑义务、来源身份原件分别保存在同目录对应JSON，活动历史在state.history。预制结果仍为 `results/result.json`，`results/table.csv` 必须一致，摘要为 `results/summary.md`。本阶段未改写预制科研材料。

从任何迁移后的项目目录运行：

```sh
/path/to/python -I -B management/status.py --root .
```

只需Python标准库，无第三方包。解释器路径由接续者指向实际可用Python；脚本依据自身路径或显式root运行，不依赖原绝对地址。退出0代表已登记本地身份与快照一致；3代表存在变更、缺失或快照损坏，须读JSON并复核。该程序只读，不写缓存，也不把文件身份检查说成科学认证。不要靠旧handoff或旧done覆盖当前有效字节。状态脚本不能自证 `management/state.json` 从未被篡改，应由授权修订记录与后续给定事件核对其权威内容。

`management/versions/A-initial/` 保存 parameters、result、table、summary 四个原始版本的完整字节和SHA对应记录，可恢复旧成果；不要用旧快照自动覆盖后来经授权修订的文件。需要修订时先保存修订前原字节、修订理由与提供方依据，再更新当前参数、依赖、结果、摘要、活动状态和版本记录。若只改变评价期，D-CALC及D-SYNTH需复核；来源/数据/卡片不变时D-SOURCE-CHECK不因评价期变化而自动失效。任何输入或输出变化均按state中的依赖传播；新保存checkpoint不能替代重新计算和摘要核对。

正常重算须指定新的外部目录，且重新检查当前参数范围：

```sh
/path/to/python -I -B scripts/compute.py --root . --output /new/nonexistent/verification-directory
```

脚本拒绝已存在输出目录；若验证失败，保留原错误与退出码，不覆盖有效results。A的真实运行证据、成功结果副本、失败前后字节/mtime快照均在 `management/evidence/A/`，可独立于外部答卷恢复核验记录。无效输入演练exit=2，未生成其输出目录，整个项目当时字节与目录/文件mtime不变；这是受控无效输入测试。

下一步：当前季度指标、表格与预制摘要已核对，由作者讨论研究表述；作者决定仍未知。禁止重训、2012外推或未经授权外部投稿。截止日期2026-12-15来自所给任务，目标期刊未定。主范围是观察小时加权的描述性留出比较，不包含因果或未来表现保证。

来源覆盖边界：2011切片已实际读取并绑定完整SHA，原完整hour.csv/ZIP、DOI文章和当前网页均未读取。来源卡的17379/17389行差异作为提供方记录保留。`notes/unregistered-scratch.md`虽保留但不登记科学依赖，status不检测该随手草稿变化。不能据此宣称覆盖整个项目所有文件。

本地原始CSV仅供私有研究缓存。发布/迁移前区分私有缓存与公开仓库，遵守所给source-identities.json的“不分发原始PDF/CSV，保留身份与项目结果”规则；本次未联网、未发布。
'''
textfile(ROOT/'RECOVERY.md',readme)
status_before=tree_snapshot(ROOT)
status_run=run([PYTHON,'-I','-B',str(MG/'status.py'),'--root',str(ROOT)])
status_after=tree_snapshot(ROOT)
assert status_run['exit_code']==0 and status_before==status_after,status_run
status_answer=json.loads(status_run['stdout'])
# Do not persist status self-check evidence into the tracked set after it was frozen.
dump(OUT/'status-check.json',{'command':status_run,'project_tree_unchanged':status_before==status_after})
answer={'case_id':'D','stage':'A','active_constraints':constraints,'next_action':next_action,'changed_or_missing_paths':[],'affected_activities':[],'unaffected_activities':obligations['required_completed_activities'],'checkpoint_freshness':'fresh-for-bound-local-files; no scientific certification','scientific_scope':scope,'source_tracking_limits':source_limits,'material_paths':{'project_root':str(ROOT),'authority':'management/state.json','recovery':'RECOVERY.md','calculator':'scripts/compute.py','parameters':'notes/parameters.json','canonical_result':'results/result.json','table':'results/table.csv','summary':'results/summary.md','initial_versions':'management/versions/A-initial/','checks':'management/evidence/A/checks.json','normal_verification':str(normal_out)},'verified_metrics':{k:result[k] for k in ['observed_hours','observed_days',*numeric.keys()]},'controlled_invalid_input':bad_check,'notes':['预制数值和摘要来自所给材料；本阶段已实际独立运行与范围核对。','未发生任何人类专家审阅、形式化证明、作者讨论决定或外部提交。','A未修改初始参数或规范科研成果，后续修订须保留旧字节与依据。']}
dump(OUT/'state-answer.json',answer)
report=f'''# 阶段交付

项目已建立在 `{ROOT}`。权威生命周期记录为 `management/state.json`；约束、来源身份、逻辑义务、版本字节、计算证据和恢复程序均已实际保存在项目内，恢复不依赖本外部答卷。

正常输入实际运行退出0，输出 `{normal_out}`。生成的 result.json 与 table.csv 均和预制规范成果逐字节一致。另以标准库从实际观察记录重算全部指标，按定义核对；摘要评价范围、观察数、舍入数值和表述边界均相符。

|指标|C0|C1|
|---|---:|---:|
|MAE|{result['C0_MAE']:.12f}|{result['C1_MAE']:.12f}|
|RMSE|{result['C0_RMSE']:.12f}|{result['C1_RMSE']:.12f}|
|偏差（预测减实际）|{result['C0_bias_prediction_minus_actual']:.12f}|{result['C1_bias_prediction_minus_actual']:.12f}|

评价期2011-10-01至2011-12-31，2203观察小时、92日，C1的MAE相对降低{100*result['MAE_reduction_fraction']:.8f}%。这里只核对所给冻结模型在该期观察小时上的描述性留出比较；不重训，无置信区间、因果或2012/任意未来表现保证。预制成果由提供方准备，本阶段是重算与核验。

有意无效输入 `notes/rejected-parameters.json` 的起点2012-01-01晚于终点2011-12-31。真实运行退出2，stderr为 `ValueError: evaluation_start must be no later than evaluation_end`，未创建拒绝测试输出目录。失败前后整个当时项目的文件字节、文件mtime及目录mtime完全相同；原有效 result/table/summary保持不变。原失败、命令、前后快照保存在 `management/evidence/A/`。这是受控无效输入测试。

D-SOURCE-CHECK、D-CALC、D-SYNTH在所绑定的当前本地版本下均已完成限定检查。恢复程序实际只读运行退出0，其执行前后项目字节与mtime相同。checkpoint对登记的本地文件新鲜；它不代表科学认证。参数、计算输入或输出变化须传播至相应活动并复核；若仅评价期改变，计算与综合会受影响，来源身份活动可保持有效。

2011本地切片实际读取8645行，日期2011-01-01至12-31，yr仅0，完整SHA为 `{identities['primary']['sha256']}`。所给初始manifest的全部14项SHA和字节数均一致。UCI来源DOI为10.24432/C5W894；标题、许可证和原完整CSV身份来自提供的来源资料，离线未重取官方ZIP或网页。卡片称完整CSV17379行与官网metadata17389有差异，已原样保留，该阶段仅能直接核验所给8645行切片。D-REMOTE仅DOI身份（10.1007/s13748-013-0040-3），无文章副本或远端内容检查。未登记scratch保留但不在自动科学依赖覆盖内；不能宣称自动检查所有文件。原CSV限私有缓存，不作公开分发。

四个初始小文件的完整字节位于 `management/versions/A-initial/notes/parameters.json` 及同一快照目录中的 `results/result.json`、`results/table.csv`、`results/summary.md`；SHA与版本依据在权威state中。原数据及冻结模型和脚本均保留原字节。

下一步：运行 `python -I -B management/status.py --root .` 复核当前依赖，然后由作者讨论已核对的2011第四季度指标与摘要。作者决定、人类专家审批和目标期刊均未知；不发送或提交任何材料。任务给定截止日为2026-12-15，约束为离线标准库、不采集新数据、不重新拟合。

本目录的 `execution.json` 保存实际argv/cwd/退出码、完整读取清单、失败与补救、工具调用数和未知设置；`inputs-and-artifacts.json` 保存输入/产物完整SHA与字节数。精确科学命令也保存在项目证据，可供迁移后复核。
'''
textfile(OUT/'report.md',report)
# Record these first three read-only shell invocations as issued before this driver.
prior_commands=[
{'argv':['/bin/zsh','-lc','cat STUDY_ROOT/runs/P2/A/REQUEST.md'],'cwd':CWD,'exit_code':0,'purpose':'read current request'},
{'argv':['EVAL_PYTHON','-I','-B','-c','from pathlib import Path; import hashlib; p=Path("INPUT_DIR"); print("INPUT_FILES"); print("\\n".join(str(x.relative_to(p)) for x in sorted(p.rglob("*")) if x.is_file())); names=["PROTOCOL.md","RECORDING.md","STAGE-A.md"]; [(print("\\nFILE "+n+" SHA256 "+hashlib.sha256((p/n).read_bytes()).hexdigest()+" BYTES "+str((p/n).stat().st_size)), print((p/n).read_text())) for n in names]'],'cwd':CWD,'exit_code':0,'purpose':'list input files; read protocol, recording, stage A'},
{'argv':['EVAL_PYTHON','-I','-B','-c','from pathlib import Path; import hashlib; p=Path("INPUT_DIR/initial"); files=[x for x in sorted(p.rglob("*")) if x.is_file()]; [(print("\\nFILE "+str(x.relative_to(p))+" SHA256 "+hashlib.sha256(x.read_bytes()).hexdigest()+" BYTES "+str(x.stat().st_size)), print(x.read_text() if x.suffix!=".csv" or x.name=="table.csv" else "DATA CSV FIRST 8 LINES\\n"+"\\n".join(x.read_text().splitlines()[:8])+"\\nDATA CSV LAST 3 LINES\\n"+"\\n".join(x.read_text().splitlines()[-3:]))) for x in files]'],'cwd':CWD,'exit_code':0,'purpose':'read all initial material bytes; full text except displayed data first8/last3'}]
read(Path(__file__))
execution={'stage':'A','case_id':'D','commands':prior_commands+[{'argv':[PYTHON,'-I','-B',str(Path(__file__))],'cwd':CWD,'exit_code':0,'purpose':'create fresh project, preserve governance and versions, execute and verify calculators, persist state and reports'}]+commands,'recording_note':'Shell output/build creation and final audit commands are appended by the final audit step. Python code and read hashes preserve executed construction. Prior scientific reads loaded complete file bytes; CSV display was sampled. Standard-library imports are runtime resources, not project/source claims.','tool_calls':5,'network_calls':0,'install_calls':0,'agent_calls':0,'violations':[],'failures':[{'intentional':True,**bad}],'remediation':['无意外失败；无效输入按预期被拒，未修复或覆盖原成果。'],'read_inventory':list(reads.values()),'written_paths':sorted(set(writes)),'unknown_runtime_settings':{'effective_model':None,'temperature':None,'seed':None,'token_budget':None,'system_token_limit':None},'project_status_unchanged_by_read_only_check':True}
dump(OUT/'execution.json',execution)
artifacts={'case_id':'D','stage':'A','inputs':[{'relative_path':str(p.relative_to(BASE)) if p.is_relative_to(BASE) else 'REQUEST.md','path':str(p),**obj(p)} for p in [request]+[p for p in sorted(INP.rglob('*')) if p.is_file()]],'project_artifacts':[{'relative_path':str(p.relative_to(ROOT)),'path':str(p),**obj(p)} for p in sorted(ROOT.rglob('*')) if p.is_file()],'output_artifacts':[{'relative_path':str(p.relative_to(OUT)),'path':str(p),**obj(p)} for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='inputs-and-artifacts.json'],'hash_manifest_self_exclusion':'This manifest cannot include its own final SHA without recursion; it is listed as an output path in execution. Directory mtimes are operational evidence, not scientific content versions.','non_distribution_scope':'Original PDF/CSV only private research cache; do not redistribute source data publicly. No article PDF or full original hour.csv supplied; no remote content bound.'}
dump(OUT/'inputs-and-artifacts.json',artifacts)
print(json.dumps({'project':str(ROOT),'report':str(OUT/'report.md'),'normal_exit':normal['exit_code'],'rejected_exit':bad['exit_code'],'status_exit':status_run['exit_code'],'invalid_test_preserved_project':before_invalid==after_invalid,'normal_byte_matches':normal_equal,'source_observations':source_observations,'files':len(artifacts['project_artifacts'])},ensure_ascii=False))
