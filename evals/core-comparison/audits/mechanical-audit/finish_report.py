#!/usr/bin/env python3
import importlib.util,datetime,zipfile,json,math
from pathlib import Path
sp=importlib.util.spec_from_file_location('audit',Path(__file__).with_name('audit.py'));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
S,A=m.S,m.A
arc=m.load(A/'archive.json');num=m.load(A/'numeric.json');eng=m.load(A/'engineering.json');adapt=m.load(A/'relation-adaptations.json')
dirty_prefix={'P1':'history/stage-c-before-recompute','P2':'management/checkpoints/C-pre-recompute/tree','P3':'.history/C-drift/files','P4':'history/stage-C-before-recalculation','P5':'.research/checkpoints/C-drift-before-recompute/files','P6':'snapshots/stage-C-before-recompute'}
initial_prefix={'P1':'history/stage-a-initial','P2':'management/versions/A-initial','P3':'.history/A-initial/files','P4':'history/stage-A-initial','P5':'.research/versions/A-initial','P6':'snapshots/initial'}
archives=[];unchanged=[];burden=[];coverage=[]
for chain in m.PLAN:
 c=chain['chain_id'];root=S/'runs'/c/'C/sealed-project';case=chain['case_id']
 fields=['notes/parameters.json','results/result.json','results/table.csv','results/summary.md']
 archives.append({'chain':c,'dirty_path':dirty_prefix[c],'dirty_preserved_byte_equal_B':{f:m.sha(root/dirty_prefix[c]/f)==m.sha(S/'runs'/c/'B/sealed-project'/f) for f in fields},'initial_path':initial_prefix[c],'initial_preserved_byte_equal_supplied':{f:m.sha(root/initial_prefix[c]/f)==m.sha(S/'design'/case/'initial/project_payload'/f) for f in fields}})
 for phase in 'ABCD':
  original=S/'runs'/c/phase/'sealed-project'
  if phase=='A':reference=A/c/'numeric-A/project';scope='unmodified numeric copy (compute output was outside project)'
  elif phase=='B':reference=A/c/'readonly-B/project';scope='unmodified read-only audit copy'
  elif phase=='C':reference=A/c/'迁移后 科研项目';scope='unmodified renamed migration copy'
  else:reference=None;scope='organizer project-after.json recorded before this audit'
  expected=m.snap(reference) if reference else m.load(S/'runs'/c/phase/'project-after.json')
  unchanged.append({'chain':c,'phase':phase,'current_sealed_project_equals_reference_bytes_mtime_dirs':m.snap(original)==expected,'reference':str(reference) if reference else str(S/'runs'/c/phase/'project-after.json'),'scope':scope})
 interfaces={'P1':[], 'P2':['management/status.py','management/verify_current.py'],'P3':['resume.py','update-state.py'],'P4':[],'P5':['scripts/manage.py'],'P6':['scripts/project_status.py','scripts/guarded_state_update.py']}[c]
 rfiles=[p for p in (root/'.agents').rglob('*') if p.is_file()] if (root/'.agents').exists() else []
 burden.append({'chain':c,'delivered_custom_interface_files':[{'path':f,'sha256':m.sha(root/f),'bytes':(root/f).stat().st_size,'source_lines':len((root/f).read_text().splitlines())} for f in interfaces],'delivered_custom_interface_lines':sum(len((root/f).read_text().splitlines()) for f in interfaces),'prefabricated_installed_agents_files':len(rfiles),'prefabricated_installed_agents_bytes':sum(f.stat().st_size for f in rfiles),'git_repository_delivered':(root/'.git').exists(),'provided_scientific_compute_lines_excluded':45,'definition':'Only persistent management interfaces; excludes orchestration, validation helpers, copied archives, supplied compute.py and packaged runtime. Not tokens or person-hours.'})
 d=eng[c]['migrated_status'];limits={k:d[k] for k in ['file_tracking','source_tracking_limits','coverage_limits'] if k in d}
 coverage.append({'chain':c,'observed_limits':limits,'remote_content_test':'not-tested: no network or remote modification','source_only_not_claimed_content_monitored':True,'unregistered_dependency_discovery':'not-provided; declared-path coverage only'})

z=S/'target-user-runtime.zip'
with zipfile.ZipFile(z) as f:zipinfo={'path':str(z),'sha256':m.sha(z),'zip_bytes':z.stat().st_size,'files':sum(not x.is_dir() for x in f.infolist()),'uncompressed_bytes':sum(x.file_size for x in f.infolist())}
maxerr=max(max(r['max_absolute_independent_result_error'],r['max_absolute_independent_table_error']) for r in num)
numeric_ok=all(r['compute_exit']==0 and r['parameter_semantics_match_key'] and r['canonical_equals_rerun_semantically'] and r['canonical_result_bytes_equal_rerun'] and r['canonical_table_bytes_equal_rerun'] and r['table_shape_matches'] and r['summary_tokens_present'] and r['input_sha256_matches_result'] and all(v['equal'] for v in r['protected'].values()) for r in num)
summary_rounding=[]
for case in ['T','D']:
 key=m.load(S/'design'/case/'reference/answer.json')
 for phase in ['initial','revised']:
  d=key[phase+'_result'];values=[x['boundary'] for x in d['values']] if case=='T' else [d[k] for k in ['C0_MAE','C1_MAE','C0_RMSE','C1_RMSE','C0_bias_prediction_minus_actual','C1_bias_prediction_minus_actual']]
  summary_rounding.extend(abs(v-float(f'{v:.12f}')) for v in values)
percent_rounding=[abs((k:=m.load(S/'design/D/reference/answer.json'))[p+'_result']['MAE_reduction_fraction']*100-float(f"{k[p+'_result']['MAE_reduction_fraction']*100:.8f}")) for p in ['initial','revised']]
diff=(k['revised_result']['MAE_reduction_fraction']-k['initial_result']['MAE_reduction_fraction'])*100;percent_rounding.append(abs(diff-2.93689404))
features=[
 {'chain':'P1','old_write':'pass: logical record version 2→3; stale v2 rejected exit2','dangling_target':'pass: statement_id missing target rejected exit2','batch_invalid_version':'covered by native expected_version; dedicated later-invalid-reference batch tested','batch_dangling_target':'pass: exit2, exact authority unchanged, valid prefix absent','dirty_checkpoint':'pass: automatic checkpoint current, CALC/SYNTH remain stale','readonly_and_migration':'pass: all snapshots unchanged; migration execution exit0'},
 {'chain':'P2','old_write':'not-provided/not-comparable','dangling_target':'not-provided/not-comparable','batch_invalid_version':'not-provided/not-comparable','batch_dangling_target':'not-provided/not-comparable','dirty_checkpoint':'manual preserved checkpoint tree; status exit3 still affects CALC/SYNTH; no auto checkpoint API','readonly_and_migration':'pass: status and independent numerical verify_current exit0 after migration'},
 {'chain':'P3','old_write':'pass: global revision 4→5 and record v2→3; both stale requests exit2','dangling_target':'accepted: existing to field changed to missing ID, exit0','batch_invalid_version':'pass: later wrong version exit2; exact authority unchanged; first valid update absent','batch_dangling_target':'accepted: valid first and dangling second both committed exit0','dirty_checkpoint':'pass on replay: checkpoint fresh, CALC/SYNTH stale; no auto checkpoint API','readonly_and_migration':'pass: unchanged snapshots, migration execution exit0'},
 {'chain':'P4','old_write':'pass: logical record version 2→3; stale v2 rejected exit2','dangling_target':'pass: statement_id missing target rejected exit2','batch_invalid_version':'covered by native expected_version; dedicated later-invalid-reference batch tested','batch_dangling_target':'pass: exit2, exact authority unchanged, valid prefix absent','dirty_checkpoint':'pass: automatic checkpoint current, CALC/SYNTH remain stale (also genuine extra INVALID-TEST dependency stale)','readonly_and_migration':'pass: unchanged snapshots, migration execution exit0'},
 {'chain':'P5','old_write':'pass: guarded file restoration with expected-current SHA; stale SHA rejected exit2; no logical record CAS','dangling_target':'not-provided/not-comparable','batch_invalid_version':'not-provided/not-comparable','batch_dangling_target':'not-provided/not-comparable','dirty_checkpoint':'pass on checkpoint-only replay: fresh fingerprints but CALC/SYNTH needs_recheck; status exit0 even when stale','readonly_and_migration':'pass: unchanged snapshots, migration execution exit0'},
 {'chain':'P6','old_write':'pass: global state_version/hash 3→4 and record v2→3; stale state/hash and missing record increment exit2','dangling_target':'accepted: existing to_id field changed to missing ID, exit0','batch_invalid_version':'pass: later bad increment exit2; exact authority unchanged; first valid update absent','batch_dangling_target':'accepted: valid first and dangling second both committed exit0','dirty_checkpoint':'pass on replay: checkpoint current, CALC/SYNTH stale; no auto checkpoint API','readonly_and_migration':'pass: unchanged snapshots, migration execution exit0'}]
report={'audit_kind':'independent mechanical/numerical/engineering audit; no scientific-content score or winner','generated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':{'evidence':'sealed A/B/C/D project/output and allowed receipts; initial materials, answer keys, common protocol and frozen engineering probes; target runtime ZIP','network':False,'install':False,'personal_skills_or_memory':False,'route_or_grade_content':False,'original_project_mutations':False,'common_python':m.PY,'isolation':'Instruction boundary, not OS access or syscall audit','not_tested':['Actual public-cache OS deny enforcement','Live remote source content','Concurrent process race stress, power loss, or adversarial filesystem attack','Interfaces not delivered; no interfaces/programs were added to any arm','Scientific truth, proof validity, provenance of remote contents, or novelty']},'attempt_notes':m.load(A/'attempt_notes.json'),'summary':{'sealed_stages':24,'all_seal_counts_and_output_hashes_match':all(r['count_equal'] and not r['sealed_output_hash_mismatches'] and r['assignment_matches'] for r in arc['seals']),'uniform_parameter_events':6,'all_only_parameter_events':all(r['only_parameter_changed'] and r['uniform_parameters'] for r in arc['events']),'readonly_stages':12,'all_recorded_readonly_manifests_identical':all(r['before_after_equal'] for r in arc['readonly']),'all_postaudit_sealed_originals_unchanged_against_untouched_copies_or_original_manifest':all(r['current_sealed_project_equals_reference_bytes_mtime_dirs'] for r in unchanged),'scientific_compute_reruns':12,'all_canonical_numeric_identity_table_summary_checks_pass':numeric_ok,'max_absolute_independent_unrounded_numeric_error':maxerr,'max_12_decimal_rounding_error':max(summary_rounding),'max_8_decimal_percentage_or_difference_rounding_error_percentage_points':max(percent_rounding),'all_initial_and_dirty_required_four_files_preserved':all(all(r['dirty_preserved_byte_equal_B'].values()) and all(r['initial_preserved_byte_equal_supplied'].values()) for r in archives)},'engineering_features_separate_no_added_scientific_score':features,'archives_and_readonly':arc,'numerical':num,'dirty_and_initial_preservation':archives,'originals_postaudit':unchanged,'engineering':eng,'relation_adaptation_evidence':adapt,'coverage':coverage,'burden':burden,'prefabricated_target_runtime':zipinfo,'limitations':['Core does not automatically preserve overwritten research-file original bytes: all six chains explicitly copied old results/parameters and real dirty-state materials. Registry history and checkpoint fingerprints alone do not reconstruct overwritten scientific files.','No arm automatically discovers undeclared dependencies, reads source-only remote content, or certifies scientific truth.','P3/P6 demonstrate real conflict prevention and atomic rejection of invalid versions; lacking referential validation does not erase those observed safeguards.','P2/P5 have narrower interfaces; absent record/batch/checkpoint APIs are not scientific failures. P5 supports real guarded file restoration; no delivered Git repository was found.','Instruction-level migration isolation is not operating-system access enforcement.']}
m.dump(S/'mechanical-audit.json',report)
lines=[
 '# 独立机械、数值与工程能力审计',
 '',
 '本报告只审计真实档案、数值复算和冻结工程探针，不作科研内容评分，不增加共同科研分，不评总冠军。所有无效写入仅发生在 mechanical-audit/ 独立副本，原封存项目与主链未改。',
 '',
 '24个阶段的封存项目计数、分配信息和封存输出SHA全部相符。6次统一事件从A到B重新比较，均仅改变 notes/parameters.json，参数语义与相应T/D新范围一致。12份B/D前后清单逐项相同，覆盖完整文件字节、大小、mtime和目录mtime；当前封存副本也与原清单完全一致。6次D的旧项目和旧toolkit路径当前均不存在；baseline原本不依赖toolkit。迁移收据及本次执行只证明实际入口运行和路径不可达，隔离为指令边界，没有OS访问审计或公共缓存读取拒绝的系统调用证据。',
 '',
 f'12次A/C均在新副本运行原compute.py，全部exit0；result.json及table.csv与canonical逐字节相同。独立从T公式、D的CSV及冻结模型复算，未舍入结果/表格的最大绝对误差为 {maxerr:.17g}。原source/model/code/source-card身份、实际参数SHA与结果绑定全部相符。摘要当前必需数字均按显示精度相符；12位小数舍入最大误差{max(summary_rounding):.17g}，8位百分比（含新旧差）最大舍入误差{max(percent_rounding):.17g}个百分点。该核对不验证原理论或科学真伪。',
 '',
 '所有C都保留了真实漂移态的参数、旧result/table/summary，逐字节匹配对应B；初始四文件也全部匹配供给原字节。保存checkpoint没有冒充重验：P1/P4实际checkpoint接口、P3/P5/P6保留中间态的checkpoint-only重放均显示快照current/fresh时CALC与SYNTH仍stale/needs_recheck。P2保存独立checkpoint树，其status仍按旧绑定返回exit3并报告两个受影响活动；未提供自动checkpoint接口，不虚构该功能。',
 '',
 '| 链 | 旧版本写入 | 悬空目标 | 合法前项+非法后项事务 | dirty checkpoint | 只读/迁移入口 |',
 '|---|---|---|---|---|---|',
 '| P1 | 逻辑record版本拒写，exit2 | statement_id未知目标拒绝 | exit2，authority原字节保留，前项未提交 | 自动保存后current但工作stale | 均无写入；迁移exit0 |',
 '| P2 | 未提供写API/不可比 | 未提供/不可比 | 未提供/不可比 | 手工checkpoint树；status仍报受影响 | status与独立numeric verifier均通过 |',
 '| P3 | global revision和record version均拒写，exit2 | 实际to字段未知目标被exit0接受 | 错版本后项整批拒绝；悬空目标后项与前项均提交 | 重放fresh但工作stale；无自动保存API | 均无写入；迁移exit0 |',
 '| P4 | 逻辑record版本拒写，exit2 | statement_id未知目标拒绝 | exit2，authority原字节保留，前项未提交 | 自动保存后current但工作stale | 均无写入；迁移exit0 |',
 '| P5 | expected-current文件SHA恢复拒绝旧SHA，exit2 | 未提供record写API/不可比 | 未提供batch/不可比 | checkpoint-only重放fresh但needs_recheck；status仍exit0 | 均无写入；迁移exit0 |',
 '| P6 | state版本+SHA与record增量版本拒写，exit2 | 实际to_id字段未知目标被exit0接受 | 错版本后项整批拒绝；悬空目标后项与前项均提交 | 重放current但工作stale；无自动保存API | 均无写入；迁移exit0 |',
 '',
 '四组关系探针均修改原来就存在的关系目标字段：P1/P4的statement_id、P3的to、P6的to_id；AUDIT-MISSING在各自原权威记录中确实不存在。原关系、候选关系、写后实际值和authority前后SHA见 mechanical-audit/relation-adaptations.json 与engineering.json。P1/P4此前的evidence_id未知端点测试也保留，结果同为拒绝。每组批次合法前项都在额外新副本独立执行成功（exit0并核对实际保存值），所以不以无效前项冒充回滚。P3/P6对无效版本后项的全批拒绝是真实保障；接受悬空关系是另一项观测，不能据此称其没有版本/事务能力。',
 '',
 'P2的verify_current.py还真实独立复算D指标、输入SHA、CSV表、活动绑定和摘要，并在迁移副本exit0且不写文件。P5实际交付manage.py，支持只读status和有SHA冲突保护、旧内容归档的restore-initial；A/C/D均无.git，不归因为Git CAS。P5 status即使遇到漂移也exit0，自动调用者必须解析effective_status及changed_paths。',
 '',
 '6组恢复输出都明确区分source-only身份和本地内容绑定；没有假造远端变更或把source locator当内容监测。未登记scratch及未知依赖不在自动覆盖范围。原字节历史均由执行者显式复制；core的metadata历史/checkpoint不会自动归档后来覆盖的研究文件原字节。',
 '',
 '| 链 | 交付的自写管理接口 | 代码行数 | 随项目预制runtime |',
 '|---|---|---:|---|']
for row in burden:
 names=', '.join(x['path'] for x in row['delivered_custom_interface_files']) or '使用已封装native CLI'
 rt=f"{row['prefabricated_installed_agents_files']} files / {row['prefabricated_installed_agents_bytes']} bytes" if row['prefabricated_installed_agents_files'] else '无复制runtime'
 lines.append(f"| {row['chain']} | {names} | {row['delivered_custom_interface_lines']} | {rt} |")
lines += ['',f"该代码行数只算持久管理入口，不含供给的45行compute.py、研究验证脚本、编排脚本或历史副本。完整预制target-user-runtime.zip为{zipinfo['zip_bytes']}字节，{zipinfo['files']}文件，解压{zipinfo['uncompressed_bytes']}字节；P1/P4项目安装副本各68文件、414713字节。不能拿整个runtime与某组作者新增脚本混为同一开发负担，不能由字节推算token或由本次运行时间推算人类工时。",'',
 '实际使用负担：native入口要求正确导出record data、使用kind/expected-version/batch格式并显式重绑活动，checkpoint可自动保存；P3要维护global revision、逐record expected_version及patch并手工保存checkpoint/重绑；P6要构造完整候选ledger、递增state/record版本、供给旧SHA并维护checkpoint；P2需显式文件版本/状态维护，数值核对脚本降低D复核操作负担；P5恢复需获得当前完整SHA，通用元数据修订和checkpoint仍依赖自写文件流程。以上为观察到的接口与维护步骤，不是人类耗时估计。', '',
 '未测或不可比：未提供的更新/批次/自动checkpoint接口、真正OS公共缓存拒读、并发竞争/断电/恶意文件系统压力、远端当前内容、科研证明与新颖性。不同组未提供接口不算科研失败。未发生成功委派：一次数值子任务spawn被平台以agent thread limit拒绝，未收到外部内容，已原样记入attempt_notes.json。初始rg仅列出route文件名，没有打开route执行或评分内容。', '',
 '完整机读结果：mechanical-audit.json。原始stdout/stderr/exit及前后文件SHA/mtime/目录mtime：mechanical-audit/receipts/。审计脚本与详细中间结果均在mechanical-audit/；所有原封存项目在结束时再次与未修改副本/原始清单一致。']
(S/'mechanical-audit.md').write_text('\n'.join(lines)+'\n')
print(json.dumps(report['summary'],ensure_ascii=False,indent=2))
