import hashlib
import json
import pathlib
import shutil
import subprocess
import sys

A=pathlib.Path('STUDY_ROOT/runs/P1/A')
P=A.parent/'project'
O=A/'output'
I=A/'input'
T=pathlib.Path('TOOLKIT_ROOT')
PY='EVAL_PYTHON'
RT=P/'.agents/skills/_rw-runtime'
def save(p,v):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def ident(p):
    b=p.read_bytes()
    return {'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
commands=json.loads((O/'actual-commands.json').read_text())
shutil.copy2(O/'actual-commands.json',O/'actual-commands-before-cwd-correction.json')
# init's logger evaluated P.exists() again after initialization. Its actual
# subprocess cwd was A. Retain the first log and correct this one field.
commands[0]['cwd']=str(A)
commands[0]['recording_correction']='Initial helper recomputed cwd after init created project; actual cwd argument was the stage directory. Original log retained separately.'
def run(args,label,expected=0):
    r=subprocess.run([str(x) for x in args],cwd=P,capture_output=True,text=True)
    v={'label':label,'argv':[str(x) for x in args],'cwd':str(P),'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
    commands.append(v)
    save(O/'actual-commands.json',commands)
    print(json.dumps({'label':label,'exit_code':r.returncode}),flush=True)
    if r.returncode != expected:
        raise RuntimeError(label+': '+r.stdout+r.stderr)
    return json.loads(r.stdout)
def cli(*args,label,expected=0):
    return run([PY,'-I','-B',RT/'tools/research.py',*args],label,expected)

failures={
    'controlled_invalid_input':{'command_label':'controlled-invalid-alpha','exit_code':2,'expected':True,'message':'Require 0<alpha<1, rho>0 and finite nonnegative intrinsic times','scientific_scope':'Intentional input rejection only; canonical four files unchanged.'},
    'unexpected_runtime_path_error':{'command_label':'check-portable-runtime','exit_code':2,'outer_script':'run_stage_a.py','outer_exit_code':1,'message':'Project/_rw-runtime was absent; actual init installed .agents/skills/_rw-runtime.','remediation':'Retained old RECOVERY, corrected runtime paths, read artifact version, replaced using formal interface, successfully checked actual installed runtime.'},
    'intermediate_checkpoint_review':{'command_label':'recheck-after-runtime-path-correction','exit_code':1,'outer_script':'repair_and_finish.py','outer_exit_code':1,'finding':'checkpoint_stale: registered-records and local-files; all three research activities remained effectively done.','explanation':'Expected consequence of replacing RECOVERY artifact after the previous checkpoint; repair helper incorrectly required zero at this intermediate inspection.','remediation':'Reviewed actual findings and activity states, retained the result, then saved a new checkpoint after recording corrections.'},
    'recording_correction':'Init actual cwd was stage A, not project: logger originally evaluated existence after init; uncorrected command log retained.',
    'scientific_impact':'No original PDF, calculator, parameter, canonical JSON/table/summary or source card changed.',
    'actor':'AI execution; no fabricated human review or formal proof.'}
save(O/'failure-and-remediation.json',failures)
save(P/'notes/stage-a-operational-corrections.json',failures)
record={'id':'T-OPERATION-LOG','type':'operational-execution-record','description':'Retained runtime-path error, intermediate stale checkpoint and correction scope; separate from scientific result.','path':'notes/stage-a-operational-corrections.json'}
save(O/'operation-log-record.json',record)
cli('register','--root',P,'--kind','artifact','--file',O/'operation-log-record.json',label='register-operational-corrections')
review=cli('check','--root',P,label='review-checkpoint-drift-before-saving',expected=1)
assert all(x['effective_status']=='done' for x in review['activities'])
assert review['errors']==[] and all(x['code']=='checkpoint_stale' for x in review['findings'])
save(O/'reviewed-intermediate-check.json',review)
next_action=review['cursor']['next_action']
cli('checkpoint','--root',P,'--next-action',next_action,'--activity','T-SYNTH','--note','Reviewed only RECOVERY and operational-note registration changes; research activity inputs and outputs unchanged. Installed runtime checked successfully. Preserve first operational errors.',label='save-final-reviewed-checkpoint')
final=cli('resume','--root',P,label='final-project-local-resume')
assert final['passed'] and final['checkpoint']['status']=='current'
assert len(final['activities'])==3 and all(x['effective_status']=='done' for x in final['activities'])
save(O/'final-recovery.json',final)

constraints=json.loads((P/'provenance/initial/constraints.json').read_text())
proof=json.loads((P/'notes/stage-a-validation.json').read_text())
originals=json.loads((P/'provenance/initial/MANIFEST.json').read_text())['files']
for rel in ['notes/parameters.json','results/result.json','results/table.csv','results/summary.md','scripts/compute.py','notes/source-check.md','sources/howard2021-arxiv-v9.pdf']:
    assert ident(P/rel)==originals['project_payload/'+rel]
for rel,meta in json.loads((P/'history/stage-a-initial/manifest.json').read_text())['files'].items():
    assert ident(P/meta['snapshot_path'])=={'sha256':meta['sha256'],'bytes':meta['bytes']}
save(O/'environment.json',proof['environment'])
state={
    'case_id':'T','stage':'A',
    'active_constraints':constraints,
    'next_action':next_action,
    'changed_or_missing_paths':[],
    'affected_activities':[],
    'unaffected_activities':['T-SOURCE-CHECK','T-CALC','T-SYNTH'],
    'checkpoint_freshness':final['checkpoint'],
    'activity_statuses':final['activities'],
    'scientific_scope':proof['scientific_scope'],
    'scientific_conditions':proof['conditions'],
    'source_tracking_limits':{'T-SRC':proof['source_access']['T-SRC'],'T-REMOTE':proof['source_access']['T-REMOTE'],'unregistered_path':'notes/unregistered-scratch.md','coverage':'Only registered resources and recorded dependencies; URL identity is not live content verification.'},
    'material_paths':{'project_root':str(P),'authoritative_configuration':'project.json','authoritative_registry':'records/registry.json','parameters':'notes/parameters.json','numeric_result':'results/result.json','companion_table':'results/table.csv','summary':'results/summary.md','source_card':'notes/source-check.md','source_identity':'provenance/initial/source-identities.json','obligations':'provenance/initial/obligations.json','initial_content_snapshots':'history/stage-a-initial/','validation':'notes/stage-a-validation.json','portable_runtime':'.agents/skills/_rw-runtime/','recovery':'RECOVERY.md'},
    'numeric_values':proof['numeric_values'],
    'normal_run_exit_code':0,'invalid_run_exit_code':2,'canonical_preserved_after_invalid':True,
    'notes':['Initial project created without replacing any prior directory; no changed/missing tracked paths at final inspection.','All required logical IDs preserved; companion table registered separately.','Initial exact four-file bytes retained, not hashes alone.','Two operational helper exits1 retained and remediated; scientific originals unchanged.','No human expert review, formal verification, full-source scientific review or external submission occurred.'],
    'unresolved_scientific_work':['Author discussion and content review before any submission.','Underlying theorem and coverage proof not independently assessed.'],
    'model':None,'temperature':None,'seed':None,'token_usage':None}
save(O/'state-answer.json',state)
report='''# 阶段 A 交付

项目已在指定新目录建立并保存配置、逻辑登记、依赖和检查点。原材料全部通过给定完整 SHA256/字节数核对；当前三个活动 T-SOURCE-CHECK、T-CALC、T-SYNTH 均为有效完成，最终恢复检查无错误或警告，检查点 current。完成状态只对应各活动声明的工作范围。

实际以当前参数 alpha=0.05、rho=1（观察前固定）、v=[0,1,10,100] 运行 scripts/compute.py，正常退出0，生成 output/validation-normal/。JSON 与预制结果内容及字节相同；table.csv 的全部数值行逐项相同，生成表使用 CRLF、预制表使用 LF。检查了 v=0 特例及等价对数表达式；摘要中的参数和 v=10 舍入值一致。

| v | 边界 |
|---|---|
| 0 | 2.4477468306808166 |
| 1 | 3.6563948713638483 |
| 10 | 9.606401928868575 |
| 100 | 32.73018624234933 |

使用 notes/rejected-parameters.json 的 alpha=1 实际试算退出2，错误为 `Require 0<alpha<1, rho>0 and finite nonnegative intrinsic times`。无效试算未生成输出目录；notes/parameters.json、results/result.json、results/table.csv、results/summary.md 前后完整 SHA 一致。这是受控输入拒绝测试，不表示科研分析失败。

本次仅复现所给计算器并核对四个点的数值与摘要。必要条件是标量 l0=1，S 与 −S 对同一非负内在时间 V 满足相应 sub-Gaussian 控制，alpha 是两侧总预算，rho 预先固定。没有新证明、覆盖模拟、新颖性判断、人类专家批准或投稿。

来源 T-SRC 为所给 Howard 等论文 arXiv:1810.08240v9、DOI 10.1214/20-AOS1991；本地 PDF 完整 SHA 为 eb3efd547349adfbff25514ae0854c142cd29b96b398be38c9000d69a2f64ca8，1494142 字节。本次核对提供的身份、完整文件指纹、PDF头和原始元数据，并读了来源卡；没有读取论文数学页，卡片中的页码与命题内容不是本次独立确认。T-REMOTE 仅有提供的来源元数据，无本地副本或当前远端内容核验。notes/unregistered-scratch.md 明确排除自动覆盖。原PDF只作私有研究缓存，sources/已排除提交，不能再分发原件。

恢复所需内容真实保存在项目：provenance/initial/ 留存原始约束、义务和来源身份；history/stage-a-initial/ 留存上述四个小文件的完整初始字节和清单；notes/stage-a-validation.json、validation/stage-a/ 留存真实正常/无效试算与前后指纹。唯一权威配置和登记分别是 project.json、records/registry.json；笔记和初始约束是历史来源，不能覆盖更晚有效版本。RECOVERY.md 给出项目内工具的恢复命令与变更处理方式。

约束已持久化：截止日期 2026-12-15（任务作者提供），仅离线标准库，不采新数据、不重拟合，中文，目标期刊未定。下一步先读取实际恢复状态、当前参数和表，再把已核对表与摘要交作者讨论；若材料发生变化，先定位、复核相应活动再显式更新登记。未经内容复核不投稿。

执行中第一次运行资源检查误用了目录，真实退出2；路径修正后检查资源成功。修复脚本又因中间检查点已过期的退出1而停下；实际发现仅涉及恢复说明登记变化，三个科研活动始终新鲜，随后完成登记、检查点和项目内恢复检查。两个外层脚本退出1、最初错误及补救都保留在 execution.json、actual-commands.json、failure-and-remediation.json，项目内亦保存操作更正记录。

外部交付：report.md、state-answer.json、execution.json、inputs-and-artifacts.json。全部科学原文件与给定初始版本一致；没有网络、安装、外部投稿或其他项目访问。
'''
(O/'report.md').write_text(report,encoding='utf-8')
assert len(report)<10000
print(json.dumps({'final_checkpoint':final['checkpoint'],'all_activities_done':True,'report_characters':len(report)},ensure_ascii=False))

# Preliminary reads were performed before the command recorder was created.
# Reconstruct their exact tool-request commands, explicitly marking that fact.
preliminary=[
 {'tool_call':1,'argv':['cat',str(A/'REQUEST.md')],'cwd':str(A),'exit_code':0},
 {'tool_call':2,'argv':['cat','input/PROTOCOL.md','input/RECORDING.md','input/STAGE-A.md',str(T/'skills/rw-workflow/SKILL.md'),str(T/'core/skill-bridge.md'),str(T/'core/protocol.md')],'cwd':str(A),'exit_code':0},
 {'tool_call':2,'argv':['rg','--files','input',str(T/'core')],'cwd':str(A),'exit_code':0},
 {'tool_call':3,'argv':[PY,'-I','-B','-c','import pathlib; roots=[pathlib.Path("input/initial")]; files=[p for root in roots for p in root.rglob("*") if p.is_file() and p.suffix != ".pdf"]; files += [pathlib.Path("TOOLKIT_ROOT/core/schemas") / (n+".schema.json") for n in ["source","statement","evidence","artifact","activity","decision","relation"]]; [(print("FILE: "+str(p)),print(p.read_text())) for p in files]'],'cwd':str(A),'exit_code':0},
 {'tool_call':4,'argv':[PY,'-I','-B','-c','import subprocess,json,pathlib,hashlib,re; t=pathlib.Path("TOOLKIT_ROOT"); p="EVAL_PYTHON"; args=[[p,"-I","-B",str(t/"tools/research.py"),x,"--help"] for x in ["init","configure","register-batch","checkpoint"]]; [(print(json.dumps({"argv":a,"cwd":str(pathlib.Path.cwd()),"exit_code":(r:=subprocess.run(a,capture_output=True,text=True)).returncode})),print(r.stdout),print(r.stderr)) for a in args]; b=pathlib.Path("input/initial/project_payload/sources/howard2021-arxiv-v9.pdf").read_bytes(); print(json.dumps({"pdf_sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b),"header":b[:20].decode("latin1"),"metadata_raw":[v.decode("latin1") for v in re.findall(rb"/(?:Title|Author|CreationDate|Subject)\\s*(?:\\([^\\n]*?\\)|<[^>]*>)",b)]},ensure_ascii=False))'],'cwd':str(A),'exit_code':0},
 {'tool_call':5,'argv':[PY,'-I','-B','-c','import pathlib; t=pathlib.Path("TOOLKIT_ROOT"); files=[t/"tools/research.py",t/"tools/connect_skills.py",t/"skills/rw-validation/SKILL.md"]; [(print("FILE: "+str(p)),print(p.read_text())) for p in files]'],'cwd':str(A),'exit_code':0},
 {'tool_call':6,'argv':['cat',str(T/'profiles/methods/computational.md')],'cwd':str(A),'exit_code':0},
 {'tool_call':7,'argv':['rg','-n','-A','65','-B','8','register-batch|def register_batch|expected_version|batch',str(T/'core/cli.py'),str(T/'core/project.py')],'cwd':str(A),'exit_code':0},
 {'tool_call':10,'argv':[PY,'-I','-B','-c','import json,pathlib; o=pathlib.Path("OUTPUT_DIR"); p=pathlib.Path("PROJECT_ROOT"); c=json.loads((o/"actual-commands.json").read_text()); print(c[0]["stdout"]); print((o/"final-recovery.json").read_text()); print("RUNTIME LOCATIONS"); print("\\n".join(str(x.relative_to(p)) for x in p.rglob("research.py"))); print("\\n".join(str(x.relative_to(p)) for x in p.rglob("connect_skills.py")))'],'cwd':str(A),'exit_code':0}
]
for entry in preliminary:
    entry['recorded_after_execution']=True
help_commands=[{'argv':[PY,'-I','-B',str(T/'tools/research.py'),x,'--help'],'cwd':str(A),'exit_code':0,'recorded_after_execution':True} for x in ['init','configure','register-batch','checkpoint']]
script_runs=[{'tool_call':9,'argv':[PY,'-I','-B',str(O/'run_stage_a.py')],'cwd':str(A),'exit_code':1}, {'tool_call':12,'argv':[PY,'-I','-B',str(O/'repair_and_finish.py')],'cwd':str(A),'exit_code':1}, {'tool_call':15,'argv':[PY,'-I','-B',str(O/'finalize.py')],'cwd':str(A),'exit_code':None,'note':'Filled by independent final delivery check only after this script returns.'}]
read_paths=set(p for p in I.rglob('*') if p.is_file()) | {A/'REQUEST.md'}
explicit_tool_paths=['skills/rw-workflow/SKILL.md','core/skill-bridge.md','core/protocol.md','tools/research.py','tools/connect_skills.py','skills/rw-validation/SKILL.md','profiles/methods/computational.md']
read_paths |= {T/x for x in explicit_tool_paths}
read_paths |= {T/'core/schemas'/(x+'.schema.json') for x in ['source','statement','evidence','artifact','activity','decision','relation']}
# Copies were actually read by initialization and the installed-only resource
# check. Hash their corresponding source identities without accessing design/
# or evals/ or scanning any other toolkit/project.
for path in (P/'.agents/skills').rglob('*'):
    if not path.is_file():
        continue
    rel=path.relative_to(P/'.agents/skills')
    if rel.parts[0]=='_rw-runtime':
        src=T/path.relative_to(RT)
    else:
        src=T/'skills'/rel
    if src.is_file() and not any(x in ['design','evals'] for x in src.relative_to(T).parts):
        read_paths.add(src)
read_paths |= {p for p in P.rglob('*') if p.is_file()}
read_paths |= {p for p in O.rglob('*') if p.is_file()}
read_files=[{'path':str(p),'sha256':ident(p)['sha256'],'bytes':ident(p)['bytes'],'read_scope':'Complete bytes for identity; semantic scientific scope separately stated.'} for p in sorted(read_paths)]
execution={
    'case_id':'T','stage':'A','commands':preliminary+help_commands+script_runs+commands,
    'outer_tool_calls':15,'tool_calls':15,'outer_tool_call_types':{'exec_command':11,'apply_patch':4},
    'read_files':read_files,
    'read_manifest_note':'Includes explicit reads, private-source full byte hashing, copied tool resources, actual installed-resource integrity reads, and final artifact hashing; stdlib runtime internals are runtime rather than task materials. Self-referential manifest/execution bookkeeping excluded.',
    'network_calls':0,'install_calls':0,'other_agent_calls':0,'violations':[],
    'failures_and_remediation':failures,
    'written_paths':[str(p) for p in sorted(set(p for p in P.rglob('*') if p.is_file()) | set(p for p in O.rglob('*') if p.is_file()))]+[str(O/'execution.json'),str(O/'inputs-and-artifacts.json')],
    'model':None,'temperature':None,'seed':None,'token_usage':None,'system_token_limit':None,'sampling_settings':'Unknown; no equality assumption.',
    'environment':proof['environment'],'external_report_character_count':len(report),
    'pending_final_delivery_check':True}
save(O/'execution.json',execution)

def inventory():
    entries=[]
    for base,kind in [(I,'input'),(P,'project-artifact'),(O,'external-output')]:
        for path in sorted(base.rglob('*')):
            if path.is_file() and path != O/'inputs-and-artifacts.json':
                entries.append({'kind':kind,'relative_path':str(path.relative_to(base)),'base':str(base),**ident(path)})
    return {'case_id':'T','stage':'A','files':entries,'original_distribution_exclusions':['project:sources/howard2021-arxiv-v9.pdf','input:initial/project_payload/sources/howard2021-arxiv-v9.pdf'],'content_scope':'Original PDF is a private research cache; retain identities/results but do not distribute the original. No original CSV supplied for this case; delivered table.csv is project numerical output.','self_hash_exclusion':'This manifest cannot include its own final hash; all other task input/project/output files have full SHA256 and byte counts.','mtime_note':'Directory mtimes are not scientific content versions.'}
save(O/'inputs-and-artifacts.json',inventory())
