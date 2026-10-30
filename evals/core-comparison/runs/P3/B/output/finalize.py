from pathlib import Path
import os,json,hashlib,sys
ROOT=Path('PROJECT_ROOT')
OUT=Path('OUTPUT_DIR')
BASE=Path('STUDY_ROOT/runs/P3/B')
GUIDE=Path('TOOLKIT_ROOT')
PYTHON='EVAL_PYTHON'
def save(name,obj):
 (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def fp(p):
 b=p.read_bytes();return {'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def snap():
 d={}
 for base,dirs,files in os.walk(ROOT):
  for p in [Path(base)]+[Path(base)/f for f in files]:
   s=p.lstat();x={'mtime_ns':s.st_mtime_ns,'bytes':s.st_size,'kind':'directory' if p.is_dir() else 'file'}
   if p.is_file():x.update(fp(p))
   d[str(p.relative_to(ROOT))]=x
 return d
before=json.loads((OUT/'project-before.json').read_text())
state=json.loads((ROOT/'research/state.json').read_text())
resume=json.loads((OUT/'resume.stdout.json').read_text())
params=json.loads((ROOT/'notes/parameters.json').read_text())
original=json.loads((ROOT/'.history/A-initial/files/notes/parameters.json').read_text())
result=json.loads((ROOT/'results/result.json').read_text())
assert params['rho']==4.0 and original['rho']==1.0 and result['rho']==1.0
assert resume['changed_or_missing_paths']==['notes/parameters.json']
assert resume['activities']['T-CALC']['effective_status']=='stale'
assert resume['activities']['T-SYNTH']['effective_status']=='stale'
assert resume['activities']['T-SOURCE-CHECK']['effective_status']=='done'
changed=[]
for p,old in state['tracked_files'].items():
 now=fp(ROOT/p) if (ROOT/p).is_file() else None
 if now!=old:changed.append({'path':p,'status':'changed' if now else 'missing','expected':old,'actual':now})
missing=[p for p in state['tracked_files'] if not (ROOT/p).is_file()]
answer={
 'case_id':'T','stage':'B','authority':{'path':'research/state.json','metadata_revision':1,'record_versions':{k:v['version'] for k,v in state['records'].items()},'configuration_scope':state['configuration']['current_scope'],'working_file_scope':params,'conflict':'Authority still declares rho=1.0; current unregistered working-parameter bytes say rho=4.0. No durable authorized revision or rationale establishes a new active rho.'},
 'active_constraints':state['configuration'],
 'next_action':{'first':'先由作者确认 notes/parameters.json 中 rho 从1到4的意图和变更依据，决定维持权威 rho=1 还是明确采用 rho=4；本阶段只报告，不改文件或登记。','after_authorized_resolution':'在可写阶段保留旧字节和依据，以预期元数据/记录版本防冲突更新相关配置与选择；按获准参数在独立新目录重算并核对 result.json、table.csv，复核摘要，再逐项重绑 T-CALC、T-SYNTH 并更新检查点。','then':state['next_action'],'old_action_executed':False},
 'changed_or_missing_paths':changed,'missing_tracked_paths':missing,
 'affected_activities':[{'id':'T-CALC','declared_status':'done','effective_status':'stale','direct_cause':'T-PARAM working file fingerprint changed; output retains rho=1 and old parameter SHA.'},{'id':'T-SYNTH','declared_status':'done','effective_status':'stale','transitive_cause':'depends_on T-CALC; its captured parameter fingerprint also differs.','affected_artifacts':['T-RESULT','results/table.csv','T-SUMMARY']}],
 'unaffected_activities':[{'id':'T-SOURCE-CHECK','declared_status':'done','effective_status':'done','evidence':'Primary PDF and notes/source-check.md byte hashes match captured files; captured source/record versions also match.','scope':'Local fixed identity and limited source card access only; not full scientific certification.'}],
 'checkpoint_freshness':{**resume['checkpoint_freshness'],'stage':'A','configuration_records_and_activities_digests_match':True,'metadata_revision_matches':True,'usable_as':'Historical recovery pointer for rho=1; cannot certify currently changed working inputs.','saved_or_rebound_in_B':False},
 'scientific_scope':{**state['scientific_scope'],'current_B_review':'Read-only identity and dependency audit. No new numerical run, theorem review, simulation, novelty assessment, human approval, or submission.','staleness_meaning':'File/registration consistency failure; does not establish the theorem or the historical rho=1 numbers are false.','conditions':'l0=1; S and -S satisfy required sub-Gaussian exponential control for the same nonnegative intrinsic time V; alpha is total two-sided error; rho fixed before observation. No replacement of V by arbitrary empirical variance.'},
 'source_tracking_limits':{**state['tracking_exclusions'],'local_file_binding_count':7,'remote':'T-REMOTE has metadata-only source identity, no local copy or live remote verification.','scratch':'notes/unregistered-scratch.md was manually hashed/read here but is outside registered activity invalidation coverage.','primary_pdf_access_this_stage':'Full bytes hashed only; no PDF page, formula, proof or remote-content review.','historical_source_access':'State reports prior partial stream/source-card access; no independent full review claimed.','program_coverage':'resume.py checks seven registered local paths plus captured record/configuration digests and declared dependencies; it does not infer all unregistered files or unmodeled dependencies.'},
 'publication_rule':state['publication_rule'],
 'material_paths':{'authoritative_state':'research/state.json','current_parameters':'notes/parameters.json','retained_initial_parameters':'.history/A-initial/files/notes/parameters.json','retained_history_manifest':'.history/A-initial/manifest.json','canonical_result':'results/result.json','companion_table':'results/table.csv','summary':'results/summary.md','source_identity_card':'notes/source-check.md','source_identities':'provenance/initial/source-identities.json','obligations':'provenance/initial/obligations.json','constraints':'provenance/initial/constraints.json','prior_validation':'validation/stage-A.json','recovery_program':'resume.py'},
 'notes':['All registered files present; only notes/parameters.json differs from captured bytes.','Original parameter bytes are retained and verified against history manifest.','Old results and summary still match initial bytes and rho=1. They have not been recomputed for rho=4.','Project update-state.py has not been executed; source recovery script exited1 for actual drift.']}
save('state-answer.json',answer)
report='''# 项目只读恢复审查

当前参数工作副本与权威状态冲突。`research/state.json` 是明确的权威表示，`metadata_revision=1`，全部14条记录仍为版本1：alpha=0.05、rho=1、rho在观察前固定，内在时间网格为0、1、10、100。实际 `notes/parameters.json` 已是 rho=4，其余参数相同；未见说明采用rho=4的登记修订、选择依据或修订历史。本阶段不能据工作副本擅自认定作者已批准新参数，也不能按旧笔记继续执行旧下一步。

研究目标仍是核对给定 normal-mixture 边界的指定参数数值，不重做理论证明。截止日2026-12-15；仅离线Python标准库及固定来源缓存，不采新数据、不重拟合；目标期刊未定，无独立人类专家批准或对外投稿授权。原始PDF/CSV限私有缓存，不对外分发。

## 已证实的变更与旧产物

7个登记文件均存在；唯一指纹变化是 `notes/parameters.json`，字节数仍为161，因此单看文件大小会漏检。

- 登记/历史SHA256：`230aea31e1afab3553088d8a6ff08e36a9155828c775681f69737c79b7c39b67`，rho=1。
- 当前SHA256：`340d3d94ab2386c9716d3fb134933347adaf630424483a7206abca8074cda117`，rho=4。
- 初始原字节真实保留在 `.history/A-initial/files/notes/parameters.json`，与历史清单一致，不依赖外部聊天或原输入目录恢复。

`results/result.json`、`results/table.csv`、`results/summary.md` 都保持原指纹。结果文件明确记录rho=1，并保存旧参数SHA；摘要仍写rho=1、v=10时9.606401928869，表中对应9.606401928868575。它们是历史rho=1成果，不能当作当前rho=4工作副本已完成数值核对。科学计算脚本、原PDF和固定来源卡指纹均未变。全部实际读取文件的完整SHA及字节数见 `execution.json` 和 `inputs-and-artifacts.json`。

## 活动依赖与检查点

实际执行项目自带的只读 `resume.py --root ...`，使用指定Python的 `-I -B`，退出1、stderr为空，报告实际漂移；没有重新计算、重新绑定、登记或保存检查点。

| 活动 | 原声明 | 当前适用性 | 原因及范围 |
|---|---|---|---|
| T-CALC | done | stale，直接受影响 | 输入T-PARAM已变；旧结果和表尚未对应新工作参数。 |
| T-SYNTH | done | stale，传递受影响 | 依赖T-CALC；它自己捕获的参数指纹也已变化；旧摘要需要随获准结果复核。 |
| T-SOURCE-CHECK | done | 在原有身份核验范围内仍有效 | 原PDF与来源卡、捕获的来源/材料记录版本均一致；这一独立分支不依赖rho。 |

检查点A已经过期：配置、记录、活动摘要和元数据版本仍与检查点一致，但实际跟踪文件不一致。旧检查点可恢复rho=1时的历史范围与下一步，不能证明新工作副本已经完成。即使以后保存新检查点，也不能替代对T-CALC和T-SYNTH的实质复核。

## 科学与跟踪范围

公式登记为 `sqrt((v+rho)*(log(1+v/rho)+2*log(1/alpha)))`，l0=1；适用需S及−S对同一个非负内在时间V满足相应sub-Gaussian指数控制，alpha是两侧总误差预算，rho在观察前固定。不能未经论证把任意经验方差代入V。

本次失效是文件身份、参数与登记依赖的不一致，不证明该定理为假，也不证明历史rho=1数值有误。本次未重算rho=4，未复核原PDF的公式/证明、模拟覆盖率、新颖性或投稿条件。项目内旧验证记录仅证明它所声明的旧执行范围；其原先alpha=1被拒绝是输入校验测试，不是科学失败。

本次对原PDF仅做全字节hash；PDF为1494142字节，SHA256为 `eb3efd547349adfbff25514ae0854c142cd29b96b398be38c9000d69a2f64ca8`，与固定身份卡一致。权威记录的历史访问范围是来源卡及少量解码文本片段，不能扩写为独立全文审阅。来源URL不代表远端当前内容已检查。

T-REMOTE仅登记 `arXiv:1808.03204v7` 的来源身份，没有本地内容绑定，本次未联网。`notes/unregistered-scratch.md` 是未登记草稿；本次虽人工读取/散列，它仍不在活动自动失效覆盖内。项目恢复程序只覆盖7个登记本地文件、所捕获的记录和声明依赖，不能据此声称全部项目文件或未建模依赖自动有效。本次额外的全项目快照用于审计只读性，不替代研究登记。

## 应先解决的下一步

先确认rho从1到4的变更意图和依据，明确保留权威rho=1还是批准rho=4。待进入获授权的可写阶段，保留旧内容与依据，用预期元数据/记录版本防冲突地更新相关配置和选择；在独立新目录按确定参数重算并核对JSON结果与CSV表，再复核摘要，逐项更新受影响活动，最后更新检查点。独立的来源身份核验无需只因rho变化就全部重做。

原来的“交作者讨论并确认V、过程控制条件和rho预先固定，未经内容复核不投稿”仍是参数冲突解决后的方向，本阶段没有执行它。本次只写项目外答卷及执行证据；项目全部文件字节、文件mtime和目录mtime复核结果见 `project-readonly-check.json`。
'''
assert len(report)<=10000
(OUT/'report.md').write_text(report,encoding='utf-8')
after=snap();save('project-after.json',after)
diffs=[p for p in sorted(set(before)|set(after)) if before.get(p)!=after.get(p)]
save('project-readonly-check.json',{'unchanged':not diffs,'changed_paths':diffs,'file_count':sum(x['kind']=='file' for x in after.values()),'directory_count':sum(x['kind']=='directory' for x in after.values()),'checked':['whole file SHA256','file bytes','file mtime_ns','directory mtime_ns','path set'],'baseline':'project-before.json','after':'project-after.json','baseline_note':'Baseline captured before executing any project program; preceding operations only read/listed project.','project_files_written':[]})
assert not diffs
semantic={'PROJECT.md','research/state.json','resume.py','provenance/initial/constraints.json','provenance/initial/obligations.json','provenance/initial/BRIEF.md','provenance/initial/source-identities.json','notes/parameters.json','.history/A-initial/files/notes/parameters.json','.history/A-initial/manifest.json','results/result.json','results/table.csv','results/summary.md','notes/source-check.md','notes/unregistered-scratch.md','validation/stage-A.json','scripts/compute.py','provenance/initial/MANIFEST.json'}
reads=[]
for rel,x in before.items():
 if x['kind']=='file':reads.append({'base':'PROJECT_ROOT','relative_path':rel,'absolute_path':str(ROOT/rel),'sha256':x['sha256'],'bytes':x['bytes'],'scope':'content inspected and whole bytes hashed' if rel in semantic else 'whole-byte hash only; contents not semantically inspected'})
for p,scope in [(BASE/'REQUEST.md','instructions'),*[(BASE/'input'/n,'instructions') for n in ['PROTOCOL.md','RECORDING.md','STAGE-B.md']],*[(GUIDE/n,'guidance only; no engine source accessed') for n in ['skills/rw-workflow/SKILL.md','core/skill-bridge.md','core/protocol.md']]]:
 base=GUIDE if p.is_relative_to(GUIDE) else BASE
 reads.append({'base':'GUIDANCE_ROOT' if base==GUIDE else 'STAGE_ROOT','relative_path':str(p.relative_to(base)),'absolute_path':str(p),**fp(p),'scope':scope})
cat1=['cat',str(BASE/'REQUEST.md')]
cat2=['cat',*[str(BASE/'input'/n) for n in ['PROTOCOL.md','RECORDING.md','STAGE-B.md']],*[str(GUIDE/n) for n in ['skills/rw-workflow/SKILL.md','core/skill-bridge.md','core/protocol.md']]]
cat4=['cat',*[str(ROOT/n) for n in ['PROJECT.md','research/state.json','resume.py','provenance/initial/constraints.json','provenance/initial/obligations.json','provenance/initial/BRIEF.md','provenance/initial/source-identities.json']]]
commands=[{'tool_call':1,'argv':cat1,'cwd':'TASK_WORKSPACE','exit_code':0},
 {'tool_call':2,'argv':cat2,'cwd':'TASK_WORKSPACE','exit_code':0},
 {'tool_call':3,'argv':[PYTHON,'-I','-B','-'],'cwd':'/private/tmp','exit_code':0,'stdin_purpose':'Inventory stage input and project file paths, byte sizes, mtimes and symlink flags; no project writes.'},
 {'tool_call':4,'argv':cat4,'cwd':'/private/tmp','exit_code':0},
 {'tool_call':5,'argv':[PYTHON,'-I','-B','-'],'cwd':'/private/tmp','exit_code':0,'stdin_purpose':'Capture whole-project hash and mtime baseline, inspect selected project material, then subprocess-run reviewed local resume.py; write only stage output.'},
 {**json.loads((OUT/'resume-command.json').read_text()),'parent_tool_call':5,'meaning':'Exit1 is actual drift/stale finding; no recovery mutation or scientific execution.'},
 {'tool_call':6,'argv':['cat'],'cwd':'/private/tmp','exit_code':0,'stdin_purpose':'Write external finalize.py via shell heredoc redirection','stdout_redirection':str(OUT/'finalize.py')},
 {'tool_call':7,'argv':[PYTHON,'-I','-B','-'],'cwd':'/private/tmp','exit_code':0,'stdin_purpose':'Correct draft record-count wording from15 to14 and update external execution accounting before finalization.'},
 {'tool_call':8,'argv':[PYTHON,'-I','-B',str(OUT/'finalize.py')],'cwd':'/private/tmp','exit_code':0,'purpose':'Generate final answer and logs, validate local findings and project immutability; self command recorded at successful completion.'}]
written=sorted([p.name for p in OUT.iterdir() if p.is_file()]+['execution.json','inputs-and-artifacts.json'])
written=sorted(set(written))
execution={'case_id':'T','stage':'B','commands':commands,'tool_calls':8,'tool_call_scope':'Eight outer functions.exec invocations each containing one exec_command; child subprocess counted in commands, not as outer tool call.','reads':reads,'generated_artifacts_read':[{'base':'OUTPUT_DIR','relative_path':p,**fp(OUT/p)} for p in ['project-before.json','resume.stdout.json','resume-command.json','finalize.py']], 'network_calls':0,'agent_calls':0,'violations':[],'failures':[],'remediation':[],'nonzero_expected_or_diagnostic_exits':[{'command':'resume.py','exit_code':1,'meaning':'Tracked parameter drift and stale dependent activities detected; not repaired.'}],'written_paths':[str(OUT/n) for n in written],'project_readonly_verified':not diffs,'unknown_settings':{'effective_model':None,'temperature':None,'seed':None,'token_budget':None,'tokens_used':None,'system_limit':None},'note':'No stage-A external execution records or chat were read. validation/stage-A.json was read only as an actually retained project record; any external paths inside it were not followed. No toolkit Python engine was read, imported, copied or executed.'}
save('execution.json',execution)
artifacts=[{'base':'OUTPUT_DIR','relative_path':p.name,**fp(p)} for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='inputs-and-artifacts.json']
save('inputs-and-artifacts.json',{'case_id':'T','stage':'B','inputs':reads,'outputs':artifacts,'self_hash_excluded':'inputs-and-artifacts.json is excluded from its own manifest to avoid recursive self-hashing.','redistribution':{'original_source_pdf_copied_to_output':False,'raw_source_policy':state['publication_rule'],'outputs_contain':'Paths, identities, hashes, local audit results, bounded quoted working material and self-written audit script; no original PDF binary.'},'source_tracking_limits':answer['source_tracking_limits']})
for n in ['state-answer.json','execution.json','inputs-and-artifacts.json','project-readonly-check.json']:
 json.loads((OUT/n).read_text())
print(json.dumps({'output_dir':str(OUT),'report_unicode_characters':len(report),'project_unchanged':not diffs,'commands_recorded':len(commands),'tool_calls':8,'read_files':len(reads),'tracked_missing':missing},ensure_ascii=False))
