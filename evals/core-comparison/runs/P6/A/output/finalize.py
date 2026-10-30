from pathlib import Path
import hashlib,json,subprocess,sys,os,shlex
BASE=Path('STUDY_ROOT/runs/P6');ROOT=BASE/'project';OUT=BASE/'A/output';IN=BASE/'A/input'
PYTHON='EVAL_PYTHON'
def fp(p):
 b=Path(p).read_bytes();return {'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def load(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def save(p,v):Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
base=load(OUT/'execution-data.json');reads=base['read_files'];cmds=base['commands'];repairs=[]
def record_read(p,access='full'):
 p=Path(p);reads.append({'path':str(p),**fp(p),'access':access});return p.read_bytes()
def run(argv,cwd):
 p=subprocess.run(argv,cwd=str(cwd),text=True,capture_output=True);entry={'argv':argv,'cwd':str(cwd),'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr};cmds.append(entry);return p
# Correct an explanatory file count; no scientific material is changed.
p=ROOT/'RECOVER.md';old=record_read(p).decode();new=old.replace('跟踪9个材料路径','跟踪8个材料路径');p.write_text(new,encoding='utf-8');repairs.append({'path':'RECOVER.md','kind':'documentation count correction','from':9,'to':8,'scientific_material_changed':False})
(ROOT/'.gitignore').write_text('# Private source cache: identities and derived results may be shared.\ndata/hour_2011.csv\n',encoding='utf-8')
# Compile syntax in memory, without bytecode files, then test guarded writes only in OUTPUT_DIR.
for rel in ['scripts/project_status.py','scripts/guarded_state_update.py']:
 compile(record_read(ROOT/rel),str(ROOT/rel),'exec')
test=OUT/'guarded-update-test';(test/'records').mkdir(parents=True)
state_bytes=record_read(ROOT/'records/state.json');(test/'records/state.json').write_bytes(state_bytes)
candidate=json.loads(state_bytes);candidate['state_version']=2;save(test/'candidate.json',candidate)
old_sha=hashlib.sha256(state_bytes).hexdigest()
first=run([PYTHON,'-I','-B',str(ROOT/'scripts/guarded_state_update.py'),'--root',str(test),'--candidate',str(test/'candidate.json'),'--expected-version','1','--expected-sha256',old_sha,'--reason','Controlled guard validation on isolated copy; no scientific revision'],ROOT)
assert first.returncode==0,first.stdout+first.stderr
changed_test=load(test/'records/state.json');assert changed_test['state_version']==2
safe_before=fp(test/'records/state.json')
second=run([PYTHON,'-I','-B',str(ROOT/'scripts/guarded_state_update.py'),'--root',str(test),'--candidate',str(test/'candidate.json'),'--expected-version','1','--expected-sh256',old_sha,'--reason','Controlled stale state guard test'],ROOT) if False else run([PYTHON,'-I','-B',str(ROOT/'scripts/guarded_state_update.py'),'--root',str(test),'--candidate',str(test/'candidate.json'),'--expected-version','1','--expected-sha256',old_sha,'--reason','Controlled stale state guard test'],ROOT)
assert second.returncode==2 and 'Conflict:' in second.stdout
assert fp(test/'records/state.json')==safe_before
assert fp(ROOT/'records/state.json')['sha256']==old_sha
save(OUT/'guard-check.json',{'isolated_test_root':str(test),'valid_update_exit':first.returncode,'json_readback_success':True,'conflict_exit':second.returncode,'conflict_preserved_current_bytes':True,'main_state_unchanged':True,'scope':'Metadata conflict guard only, no scientific validation'})
# Final read-only recovery check, retaining command and exact output.
status=run([PYTHON,'-I','-B',str(ROOT/'scripts/project_status.py'),'--root',str(ROOT)],ROOT);assert status.returncode==0,status.stdout
state=load(ROOT/'records/state.json');s=json.loads(status.stdout);save(OUT/'status.json',s)
res=load(ROOT/'results/result.json');validation=load(OUT/'validation.json')
answer={'case_id':'D','stage':'A','active_constraints':state['configuration'],'next_action':state['checkpoint']['next_action'],'changed_or_missing_paths':s['changed_or_missing_paths'],'affected_activities':[],'unaffected_activities':['D-SOURCE-CHECK','D-CALC','D-SYNTH'],'activities':s['activities'],'checkpoint_freshness':s['checkpoint_freshness'],'scientific_scope':{'evaluation_start':res['evaluation_start'],'evaluation_end':res['evaluation_end'],'model_policy':res['model_policy'],'metric_weighting':'observed-hour','observed_hours':res['observed_hours'],'observed_days':res['observed_days'],'numeric_result':res,'result_origin':'Precomputed author-provided artifacts, independently rerun with supplied calculator and matched byte for byte','no_refit':True,'no_confidence_intervals':True,'no_causal_or_future_year_guarantee':True,'human_review':False,'formal_proof':'not-applicable'},'source_tracking_limits':{'primary_local':'8645 yr=0 rows read and complete SHA verified against supplied source identity; remote official origin and full hour.csv not independently re-established','source_only':['D-REMOTE'],'unregistered_file':['notes/unregistered-scratch.md'],'not_auto_checked':'All other project files are outside explicitly bound scientific dependencies','raw_distribution':'Private local cache only; do not redistribute original CSV/PDF'},'material_paths':{'project':str(ROOT),'authority':'records/state.json','recovery':'RECOVER.md','snapshots':['snapshots/initial/notes/parameters.json','snapshots/initial/results/result.json','snapshots/initial/results/table.csv','snapshots/initial/results/summary.md'],'original_constraints':'provenance/initial/constraints.json','original_obligations':'provenance/initial/obligations.json','source_identity':'provenance/initial/source-identities.json'},'notes':['Normal calculator exit 0; result.json and table.csv both byte-equal to supplied canonical files.','Intentional rejected range exit 2: evaluation_start must be no later than evaluation_end; no rejected output directory and eight bound file fingerprints unchanged.','D-SOURCE-CHECK is restricted to supplied identity card and local cache; evaluation-scope revisions alone do not invalidate it.','Current declared and effective activity states are done within their explicit scopes; checkpoint is current.','Checkpoint storage itself adds no scientific evidence.']}
save(OUT/'state-answer.json',answer)
report=f'''# 冻结自行车需求模型：初始状态与核对结果

项目已在新目录建立；`records/state.json`为当前配置、记录版本与依赖的权威表示。原始约束、义务、来源卡及任务规则已留在项目`provenance/`。`scripts/project_status.py`可脱离外部工具包只读恢复。当前8个登记材料路径均与绑定SHA一致，三个活动的声明状态和有效状态均为done，检查点为current。

本次实际运行提供的计算器，评价期2011-10-01至2011-12-31，使用2011年1月至9月的冻结C0/C1参数，按实际观察小时等权计算。正常命令退出0；新结果位于本答卷同目录的`validation-valid/`，其中result.json和table.csv与项目内预制成果逐字节一致。预制成果来自提供材料；本次完成的是重运行核对。

| 指标 | C0 | C1 |
|---|---:|---:|
| MAE | {res['C0_MAE']:.12f} | {res['C1_MAE']:.12f} |
| RMSE | {res['C0_RMSE']:.12f} | {res['C1_RMSE']:.12f} |
| 偏差（预测减实际） | {res['C0_bias_prediction_minus_actual']:.12f} | {res['C1_bias_prediction_minus_actual']:.12f} |

观察样本为2203小时、92日；C1的MAE相对降低24.23172448%。`results/summary.md`已按日期、样本量、两项MAE、降低比例与范围核对。此结论是指定2011留出范围的描述性比较；未重训，无置信区间，不作因果或2012表现保证。

已实际使用`notes/rejected-parameters.json`运行受控无效试算，其起点2012-01-01晚于终点2011-12-31，退出2并给出`ValueError: evaluation_start must be no later than evaluation_end`。未创建无效输出目录。试算前后8个登记文件的完整SHA和字节数全部一致，包括有效result、table及summary；原有效成果未受影响。这是输入校验测试，不是实际科学分析失败。命令、stdout/stderr及前后摘要保留在`validation.json`，项目内亦保存`records/validation-A.json`和`records/commands-A.json`。

本地`data/hour_2011.csv`共8645行，实际全表解析，均为2011/yr=0；完整SHA为`294d25e98ef1c9c9cec746e17ba3ff9818627ba5aa14baf1b93db7ae218de115`，568668字节，与给定来源身份及清单一致。来源卡中的官方完整hour.csv 17379行与网站metadata 17389行差异予以保留；原始ZIP、完整hour.csv、论文和当前远端页面均未取得或独立检查。冻结模型训练来源只按提供的元数据记录，本次不重新拟合验证。

来源DOI/URL是身份信息；D-REMOTE仅登记DOI，未绑定或检查原文内容。`notes/unregistered-scratch.md`虽随材料保留并有读取清单，但不属于自动计算依赖或检查覆盖。自动状态检查只涉及显式登记的8个科学材料，不能声称全部项目文件均受覆盖。原始CSV保留为私有本地缓存，已写`.gitignore`排除项；禁止随公开仓库分发原始PDF/CSV。

参数、result、table、summary四项初始原字节分别保存在`snapshots/initial/`对应路径，SHA与字节数见`records/initial-snapshots.json`；这些副本可恢复实际内容，不只是摘要。记录均为版本1；以后修订应保存旧内容和依据，依赖变化需要显式复核。`guarded_state_update.py`在答卷目录的隔离副本上完成有效更新/JSON回读及旧版本冲突拒绝测试，冲突退出2且未改当前字节；主项目state保持不变。该测试只验证元数据保护。

恢复时用可用Python标准库解释器运行`python -I -B ROOT/scripts/project_status.py --root ROOT`，具体说明见`RECOVER.md`。目前没有需重做的活动；若评价参数改变，D-CALC及其下游D-SYNTH需重新核对，D-SOURCE-CHECK不因评价起点单独改变而失效。保存新检查点不能代替该复核。

下一步：将已核对的2011第四季度冻结模型指标与摘要交作者讨论；不重训、不外推2012。截止日期2026-12-15是提供的项目约束，预算为离线Python标准库、不采集新数据，期刊未定。未发生人类专家审批或外部投稿。执行记录与输入/产物SHA分别见`execution.json`、`inputs-and-artifacts.json`。
'''
assert len(report)<10000
(OUT/'report.md').write_text(report,encoding='utf-8')
# Persistent records are sufficient for recovery without any external answer file.
save(ROOT/'records/commands-A.json',cmds)
save(ROOT/'records/guard-validation-A.json',load(OUT/'guard-check.json'))
for p in sorted(ROOT.rglob('*')):
 if p.is_file():record_read(p,'full-byte inventory; scientific access separately documented')
for p in sorted(OUT.rglob('*')):
 if p.is_file() and p.name not in ['execution.json','inputs-and-artifacts.json']:record_read(p,'full-byte output inventory')
record_read(BASE/'A/REQUEST.md')
# Record all initial outer commands; later shell heredoc wrappers are preserved verbatim by source content.
payload=IN/'initial/project_payload';guides=Path('TOOLKIT_ROOT')
outer=[]
def outer_entry(n,cmd,cwd,stdout):outer.append({'tool_call':n,'tool':'exec_command','command':cmd,'cwd':cwd,'exit_code':0,'stdout_summary':stdout,'stderr':''})
outer_entry(1,'cat '+str(BASE/'A/REQUEST.md'),'TASK_WORKSPACE','REQUEST.md content returned')
outer_entry(2,'ls -la '+str(IN)+'\ncat '+' '.join(str(p) for p in [IN/'PROTOCOL.md',IN/'RECORDING.md',IN/'STAGE-A.md',guides/'skills/rw-workflow/SKILL.md',guides/'core/skill-bridge.md',guides/'core/protocol.md']),'TASK_WORKSPACE','Input directory listing and six requested guidance documents returned')
outer_entry(3,'find '+str(IN/'initial')+' -type f -print','TASK_WORKSPACE','15 initial file paths returned')
initial_paths=[IN/'initial'/n for n in ['BRIEF.md','constraints.json','obligations.json','source-identities.json','MANIFEST.json']]+[payload/n for n in ['notes/parameters.json','notes/rejected-parameters.json','notes/source-check.md','notes/unregistered-scratch.md','results/result.json','results/table.csv','results/summary.md','model/frozen.json','scripts/compute.py']]
outer_entry(4,'cat '+' '.join(map(str,initial_paths)),'TASK_WORKSPACE','All listed scientific and project material contents returned; large raw CSV read by later calculator/inventory')
build=(OUT/'build_project.py').read_text(encoding='utf-8')
outer_entry(5,'mkdir -p '+str(OUT)+'\ncat > '+str(OUT/'build_project.py')+" <<'PY'\n"+build+'PY\n'+PYTHON+' -I -B '+str(OUT/'build_project.py'),str(IN),'Project built; valid exit 0, intentional invalid exit 2, status exit 0, exact result/table matches, 8 tracked paths')
outer_entry(6,'cat '+' '.join(str(p) for p in [ROOT/'scripts/guarded_state_update.py',OUT/'status.json',ROOT/'records/commands-A.json']),str(OUT),'Guard implementation, current status and actual scientific commands returned')
finalizer=Path(__file__).read_text(encoding='utf-8')
outer_entry(7,'cat > '+str(Path(__file__))+" <<'PY'\n"+finalizer+'PY\n'+PYTHON+' -I -B '+str(Path(__file__)),str(OUT),'Reports and manifests finalized; isolated guard update and conflict tests complete; final read-only status exit 0')
# Exact process argument arrays for subprocesses and the actual submitted shell source for outer calls.
for x in outer:x['argv']=['/bin/zsh',('-lc' if x['tool_call']<=4 else '-c'),x['command']];x['argv_note']='Submitted shell-source representation; tool backend wrapper argv is not exposed'
# Deduplicate identical input versions while preserving earlier read identities of changed owned files.
unique={}
for x in reads:unique[(x['path'],x['sha256'])]=x
execution={**base,'commands':cmds,'outer_commands':outer,'tool_calls':7,'tool_call_count_unit':'functions.exec / nested exec_command pairs; 7 of each, no additional tools','read_files':list(unique.values()),'read_scope_note':'Includes explicit task/guidance/input and owned project/output byte reads. Automatically imported Python standard-library/runtime files and shell internals are execution dependencies, not inspected scientific inputs.','network_calls':0,'other_agent_calls':0,'violations':[],'repairs':repairs,'failures':base['failures']+[{'kind':'controlled stale-ledger conflict on isolated copy','exit_code':second.returncode,'stdout':second.stdout,'remediation':'No retry or overwrite; current test ledger and main project authority preserved'}],'written_paths':[str(p) for p in sorted(ROOT.rglob('*')) if p.is_file()]+[str(p) for p in sorted(OUT.rglob('*')) if p.is_file()]+[str(OUT/'execution.json'),str(OUT/'inputs-and-artifacts.json')],'unknown_settings':{'model':None,'temperature':None,'seed':None,'token_budget':None,'system_limits':None},'report_unicode_characters':len(report)}
save(OUT/'execution.json',execution)
# Manifest excludes its own recursive hash. execution.json has a stable final hash here.
items=[]
for category,basepath in [('input',IN),('project',ROOT),('output',OUT)]:
 for p in sorted(basepath.rglob('*')):
  if p.is_file() and p!=OUT/'inputs-and-artifacts.json':items.append({'category':category,'relative_path':p.relative_to(basepath).as_posix(),**fp(p),'distribution':'private original source cache; do not redistribute' if p.name=='hour_2011.csv' else 'project/task artifact'})
save(OUT/'inputs-and-artifacts.json',{'items':items,'self_hash_excluded':'inputs-and-artifacts.json','nonredistribution_scope':['Original PDF/CSV private cache; original raw CSV appears only in supplied input, project private data cache and local controlled test-free computation inputs. No remote fetch, upload or publication.'],'guidance_reads':[x for x in unique.values() if '/toolkits/' in x['path']]})
# Final checks use exact delivered bytes and do not modify the project.
assert all((ROOT/'snapshots/initial'/rel).read_bytes()==(ROOT/rel).read_bytes() for rel in ['notes/parameters.json','results/result.json','results/table.csv','results/summary.md'])
assert (OUT/'validation-valid/result.json').read_bytes()==(ROOT/'results/result.json').read_bytes()
assert (OUT/'validation-valid/table.csv').read_bytes()==(ROOT/'results/table.csv').read_bytes()
assert not (OUT/'validation-rejected').exists()
assert len(load(OUT/'execution.json')['outer_commands'])==7
assert s['changed_or_missing_paths']==[] and s['checkpoint_freshness']=='current'
print(json.dumps({'report':str(OUT/'report.md'),'state_answer':str(OUT/'state-answer.json'),'execution':str(OUT/'execution.json'),'manifest':str(OUT/'inputs-and-artifacts.json'),'project':str(ROOT),'report_characters':len(report),'tool_calls':7,'final_status_exit':status.returncode,'guard_update_exit':first.returncode,'guard_conflict_exit':second.returncode,'snapshots_verified':4,'all_final_checks_passed':True},ensure_ascii=False))
