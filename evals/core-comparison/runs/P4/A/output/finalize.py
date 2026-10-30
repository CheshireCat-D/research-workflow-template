from pathlib import Path
import hashlib, json, platform, sys

B=Path('STUDY_ROOT/runs/P4')
P=B/'project'; I=B/'A/input'; O=B/'A/output'
T=Path('TOOLKIT_ROOT')
PY='EVAL_PYTHON'
def load(p):return json.loads(p.read_text())
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def fp(p):
    b=p.read_bytes();return {'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
C=load(P/'context/constraints.json'); R=load(P/'results/result.json'); S=load(O/'final-status.json')
commands=load(O/'commands.json')

report='''# 冻结自行车需求模型：初始交付

项目已建立于 `PROJECT_ROOT`。本阶段复算了给定计算器，核对了预制结果、表格和摘要；没有把材料制作者的预制研究记为从零完成的分析。

当前评价期为 **2011-10-01—2011-12-31**，使用给定2011年1—9月冻结模型，按实际观察小时等权。共有 **2203小时、92日**。

| 指标 | C0 | C1 |
|---|---:|---:|
| MAE | 58.825190494512434 | 44.570832407531775 |
| RMSE | 86.08056895633848 | 67.99996906089847 |
| 偏差：预测减实际 | 1.078965171773347 | 0.9871531155146787 |

C1的MAE相对C0降低 **24.23172448%**。正常计算退出0，新输出位于 `A/output/validation-normal/`，`result.json`及`table.csv`与项目内预制文件逐字节一致；表中七项也逐项对应结果。摘要中的区间、样本量、舍入数值与解释范围均一致，保留原字节。这里是给定观察期上的描述性时间留出比较；未重训、未构造置信区间、未作因果判断或2012年外推。

来源为UCI Bike Sharing数据集，DOI `10.24432/C5W894`，所给官方 `hour.csv` 的2011切片。实际解析本地8645行，日期覆盖2011全年、`yr=0`，日期和小时组合无重复，完整SHA256为 `294d25e98ef1c9c9cec746e17ba3ff9818627ba5aa14baf1b93db7ae218de115`。来源卡的“完整CSV为17379行、官网metadata为17389”是所给来源说明，本次未访问远端或原完整CSV重新确认。原文章 `10.1007/s13748-013-0040-3` 仅登记DOI身份，无本地文章内容或当前远端检查。原始CSV/PDF仅留私有缓存，禁止仓库再分发。

另以 `notes/rejected-parameters.json` 真实运行一次受控无效输入：起点2012-01-01晚于终点2011-12-31，退出 **2**，错误为 `ValueError: evaluation_start must be no later than evaluation_end`。未生成无效输出目录；参数、模型、数据、计算器、原结果、表和摘要的完整SHA在失败前后均一致。它证明这个输入被拒绝且有效文件未改，属于负向输入测试，不是科学分析失败。

持久状态在 `project.json`、`records/registry.json`；`context/`保存给定约束、义务、来源和初始清单。来源核验、计算、摘要核对与负向测试均据实登记完成，执行者为助手和本地程序，无人类专家批准或形式化证明。依赖包含参数、原始数据、代码、模型、作者既定选择、结果、表和摘要；计算到摘要有明确活动依赖。最终只读检查无发现，22号登记修订的检查点为current，四个活动均为done，11个本地文件被绑定。此状态检查只确认登记和文件一致性。

`history/stage-A-initial/`保存 `notes/parameters.json`、`results/result.json`、`results/table.csv`、`results/summary.md` 四份可恢复初始内容及清单。`validation/stage-A/`保留两次真实命令、输出、错误和失败前后指纹，后续恢复无须依赖外部答卷。`notes/unregistered-scratch.md`没有登记或工作依赖，不纳入自动变化覆盖；来源URL本身也不绑定或验证远端内容。

截止日2026-12-15、仅离线Python标准库、固定资料、不采新数据或重拟合等约束已保留。截止日来自给定项目设定；期刊未知，保持null；未授权投稿。

下一步由作者讨论这项已核对的2011第四季度比较的解释和用途。恢复时在项目目录执行 `python3 -I -B .agents/skills/_rw-runtime/tools/research.py resume --root .`，再检查当前参数、结果、表、摘要及依赖；若漂移，先保留旧内容和修订理由，复核受影响活动后正式更新登记，再保存新检查点。操作说明见 `RECOVERY.md`。本阶段没有代替作者作出后续研究或投稿决定。
'''
(O/'report.md').write_text(report)
assert len(report)<=10000
state={'case_id':'D','stage':'A','active_constraints':C,'next_action':S['next_action'],
 'changed_or_missing_paths':[],
 'affected_activities':[],
 'unaffected_activities':['D-SOURCE-CHECK','D-CALC','D-SYNTH','D-INVALID-TEST'],
 'checkpoint_freshness':S['checkpoint'],
 'scientific_scope':{'evaluation_start':R['evaluation_start'],'evaluation_end':R['evaluation_end'],'observed_hours':R['observed_hours'],'observed_days':R['observed_days'],'model_policy':R['model_policy'],'metric_weighting':'observed-hour','no_refit':True,'confidence_interval':None,'human_expert_approval':False,'formal_verification':'not-applicable','causal_or_future_year_guarantee':False,'prebuilt_provenance':'Supplied by material builder; rerun and compared in this stage'},
 'source_tracking_limits':{'D-SRC':'Full local 2011 slice parsed; partial coverage of identified original dataset; no remote verification','D-REMOTE':'Metadata-only DOI identity, no supplied local copy or content binding','unregistered_paths':['notes/unregistered-scratch.md'],'original_full_csv_and_web_counts':'Supplied provenance only; 17379 vs 17389 discrepancy retained','publication_rule':load(P/'context/source-identities.json')['publication_rule']},
 'material_paths':{'project_root':str(P),'authoritative_configuration':'project.json','authoritative_registry':'records/registry.json','constraints':'context/constraints.json','source_identities':'context/source-identities.json','obligations':'context/obligations.json','initial_snapshots':'history/stage-A-initial','validation':'validation/stage-A','recovery':'RECOVERY.md','normal_rerun':str(O/'validation-normal')},
 'controlled_invalid_test':{'exit_code':2,'error':'ValueError','message':'evaluation_start must be no later than evaluation_end','protected_valid_artifacts_unchanged':True,'scientific_failure':False,'output_directory_created':False},
 'notes':['Initial stage has no prior checkpoint or revision-induced stale work to compare.','All required activities have actually been checked; author discussion remains next action.','Checkpoint current is not scientific certification.']}
save(O/'state-answer.json',state)

# Record direct earlier reads as well as child-process file-open audit records.
manual=[]
for p in [B/'A/REQUEST.md',*sorted(I.rglob('*'))]:
    if p.is_file():manual.append({'path':str(p),**fp(p),'read_scope':'full bytes; input text inspected, CSV parsed by controller/calculator'})
tool_files=['skills/rw-workflow/SKILL.md','core/skill-bridge.md','core/protocol.md','tools/research.py','core/cli.py','core/bundle.py','tools/connect_skills.py','core/project.py','core/model.py','skills/rw-validation/SKILL.md','profiles/methods/computational.md','profiles/methods/empirical-quantitative.md',*['core/schemas/'+n+'.schema.json' for n in ['source','statement','evidence','relation','artifact','activity','decision','method-binding']]]
for rel in tool_files:
    manual.append({'path':str(T/rel),**fp(T/rel),'read_scope':'earlier direct read or bounded text search; complete fingerprint now retained'})
audited=[]
for f in sorted((O/'logs').glob('*.reads.json')):
    for row in load(f):audited.append({**row,'recorded_by':str(f.relative_to(O))})
read_map={}
for row in manual+audited:
    key=(row['path'],row['sha256'])
    if key not in read_map:read_map[key]=row
save(O/'read-manifest.json',list(read_map.values()))

# Preserve supplied-copy provenance without accessing original design/evaluation contents.
resource_copy_manifest=[]
for directory in [P/'_rw-runtime',P/'.agents/skills']:
    for p in sorted(directory.rglob('*')):
        if p.is_file():resource_copy_manifest.append({'path':str(p.relative_to(P)),**fp(p),'scope':'Automatically installed runtime/guidance copy; content is not scientific evidence'})
save(O/'installed-resources.json',resource_copy_manifest)

execution={'case_id':'D','stage':'A','commands':commands,
 'tool_calls':16,'outer_tool_call_count':16,'tool_calls_basis':'13 setup/inspection calls before this finalizer was written; finalizer creation, execution, and final audit make 16 total outer calls. One outer call contained both an exec and apply_patch.',
 'network_calls':0,'other_agents_called':0,'packages_installed':0,
 'read_manifest':'read-manifest.json','read_files':list(read_map.values()),
 'runtime_read_audit_note':'Child Python processes were launched with -I -B under a runpy audit wrapper. Ordinary filename-open events are recorded with read-time SHA and bytes; descriptor-relative file accesses may not expose an absolute path in audit events. Installed resource copy identities are therefore also recorded separately. No design or eval content was displayed or used as research evidence.',
 'violations':[{'type':'implicit-tool-resource-access','path':str(T/'design/catalog.json'),'reason':'Mandatory init --connect-skills and core validation internally read the stable catalog under design/. This runtime access conflicts with a literal no-design-read interpretation. No manual content inspection, evaluator material or eval directory access occurred. Required official interface was retained; the exception is disclosed rather than hidden.'}],
 'failures':[{'command':'01-init','exit_code':2,'error_code':'invalid_registration','message':'Unknown project entry activity or workflow mode','cause':'Explicit --entry validation was not accepted by the official interface','remedy':'Removed unsupported entry argument and used default; project had not been created. First stdout, command, failed script and read audit retained.'},{'command':'04-controlled-invalid-calculation','exit_code':2,'expected':True,'scientific_failure':False,'message':'evaluation_start must be no later than evaluation_end','remedy':'No retry or parameter repair; test expected rejection; hashes proved no valid input/output bytes changed.'}],
 'first_failed_driver':{'argv':[PY,'-I','-B',str(O/'auditrun.py'),str(O/'logs/controller.reads.json'),str(O/'perform.py')],'cwd':'TASK_WORKSPACE','exit_code':1,'preserved_script':'perform-first-failed.py','preserved_reads':'logs/controller-first-failed.reads.json'},
 'successful_driver':{'argv':[PY,'-I','-B',str(O/'auditrun.py'),str(O/'logs/controller.reads.json'),str(O/'perform.py')],'cwd':'TASK_WORKSPACE','exit_code':0},
 'written_paths':[str(p) for root in [P,O] for p in sorted(root.rglob('*')) if p.is_file()],
 'unknown_settings':{'effective_model':None,'temperature':None,'seed':None,'token_budget':None,'actual_token_usage':None,'system_limits':None},
 'observed_runtime':{'python_executable':sys.executable,'python_version':sys.version,'platform':platform.platform(),'machine':platform.machine()},
 'publication_scope':'No remote publication, upload, submission or messaging. Original supplied CSV stays in private project cache and data/ is gitignored.',
 'report_unicode_characters':len(report),'checks':{'input_supplied_manifest_all_match':True,'normal_result_and_table_byte_identical':True,'controlled_invalid_exit':2,'protected_files_unchanged':True,'initial_four_snapshots_retained':True,'core_final_passed':S['passed'],'checkpoint':S['checkpoint'],'all_activities_done':all(a['effective_status']=='done' for a in S['activities'])}}
save(O/'execution.json',execution)

def inventory():
    return {'case_id':'D','stage':'A','inputs':[{'relative_path':str(p.relative_to(I)),**fp(p)} for p in sorted(I.rglob('*')) if p.is_file()],
      'project_artifacts':[{'relative_path':str(p.relative_to(P)),**fp(p)} for p in sorted(P.rglob('*')) if p.is_file()],
      'output_artifacts':[{'relative_path':str(p.relative_to(O)),**fp(p)} for p in sorted(O.rglob('*')) if p.is_file() and p.name not in ['inputs-and-artifacts.json','finalizer.reads.json']],
      'self_manifest_note':'inputs-and-artifacts.json excludes its own hash to avoid self-reference; finalizer audit is written after this inventory and covered in final-audit.json.',
      'not_for_redistribution':['project/data/hour_2011.csv','Any original PDF/CSV if present in private cache'],
      'original_materials_copy_policy':'Private project copy only; no second large data archive or public repository operation performed.'}
save(O/'inputs-and-artifacts.json',inventory())
print(json.dumps({'report_chars':len(report),'read_file_versions':len(read_map),'installed_resource_files':len(resource_copy_manifest),'commands':len(commands),'outputs_written':True},ensure_ascii=False))
