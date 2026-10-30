import ast,hashlib,json,subprocess,sys
from pathlib import Path
BASE=Path('STUDY_ROOT/runs/P3/A');OUT=BASE/'output';ROOT=BASE.parent/'project';INP=BASE/'input'
PY='EVAL_PYTHON';TK=Path('TOOLKIT_ROOT')
DEFAULT_CWD='TASK_WORKSPACE'
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def finger(p):
 b=p.read_bytes();return {'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
log=json.loads((OUT/'build-log.json').read_text());check=json.loads((OUT/'resume-status.json').read_text());v=json.loads((OUT/'verification.json').read_text())
state=json.loads((ROOT/'research/state.json').read_text())
for p in [ROOT/'resume.py',ROOT/'update-state.py',OUT/'build_project.py',Path(__file__)]:ast.parse(p.read_text())
with (ROOT/'PROJECT.md').open('a') as f:
 f.write('\n`update-state.py --expected-revision N --patch PATCH.json` 支持带预期元数据版本及记录版本的显式修订，要求理由，保留旧状态并拒绝冲突；不会自动刷新活动或检查点。该写入接口本阶段仅作语法检查，尚未执行修订测试。\n')
before={str(p.relative_to(ROOT)):{**finger(p),'mtime_ns':p.stat().st_mtime_ns} for p in ROOT.rglob('*') if p.is_file()}
dirbefore={str(p.relative_to(ROOT)):p.stat().st_mtime_ns for p in [ROOT,*ROOT.rglob('*')] if p.is_dir()}
r=subprocess.run([PY,'-I','-B',str(ROOT/'resume.py')],cwd=ROOT,capture_output=True,text=True)
after={str(p.relative_to(ROOT)):{**finger(p),'mtime_ns':p.stat().st_mtime_ns} for p in ROOT.rglob('*') if p.is_file()}
dirafter={str(p.relative_to(ROOT)):p.stat().st_mtime_ns for p in [ROOT,*ROOT.rglob('*')] if p.is_dir()}
assert r.returncode==0 and before==after and dirbefore==dirafter
save(OUT/'readonly-recovery-test.json',{'argv':[PY,'-I','-B',str(ROOT/'resume.py')],'cwd':str(ROOT),'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr,'file_bytes_and_mtime_unchanged':True,'directory_mtime_unchanged':True,'before':before,'after':after,'directory_mtime_ns_before':dirbefore,'directory_mtime_ns_after':dirafter})
answer={'case_id':'T','stage':'A','project_root':str(ROOT),'active_constraints':state['configuration'],'next_action':state['next_action'],'changed_or_missing_paths':[],'affected_activities':[],'unaffected_activities':['T-SOURCE-CHECK','T-CALC','T-SYNTH'],'activity_status':check['activities'],'checkpoint_freshness':check['checkpoint_freshness'],'scientific_scope':state['scientific_scope'],'source_tracking_limits':{'local_primary':'PDF bytes match supplied full SHA; metadata and author card read; selected decoded text only, formulas/proofs not independently inspected','remote_identity_only':state['tracking_exclusions']['source_only'],'unregistered_scratch_not_covered':state['tracking_exclusions']['unregistered_file'],'no_network_or_remote_content_check':True},'material_paths':{'authority':'research/state.json','calculator':'scripts/compute.py','raw_private':'sources/howard2021-arxiv-v9.pdf','parameters':'notes/parameters.json','result':'results/result.json','table':'results/table.csv','summary':'results/summary.md','source_note':'notes/source-check.md','initial_snapshots':'.history/A-initial/files/','constraints':'provenance/initial/constraints.json','source_identity':'provenance/initial/source-identities.json','evidence':'validation/stage-A.json','resume':'resume.py'},'verification':{'normal_exit_code':0,'result_and_table_byte_match':True,'invalid_trial_exit_code':2,'valid_artifacts_unchanged_bytes_and_mtime':True,'read_only_resume_unchanged_bytes_and_mtime_and_directory_mtime':True},'notes':['Initial prepared materials were supplied, then actually recomputed using the supplied calculator; no claim of from-scratch original scientific work.','No human expert approval, new theorem proof, coverage simulation, novelty assessment, target journal, or submission.','Guarded metadata revision helper syntax checked only; conflict and write behavior not yet exercised.','One auxiliary PDF regex inspection did not return a final exit in captured output; a linear partial-inspection retry succeeded. An own-process cleanup attempt using ps was denied by sandbox and left no process information.']}
save(OUT/'state-answer.json',answer)
report=f'''# 阶段 A 交付

项目已建于 `{ROOT}`。给定参数的实际重算成功，`results/result.json` 与 `results/table.csv` 和原有预制文件逐字节一致；当前三项活动在已声明的核验范围内完成，检查点新鲜，没有已登记材料漂移。预制内容来自提供材料，本次是在其基础上重算、核对并建立持久记录。

当前 alpha=0.05、rho=1，rho 在观察前固定；内在时间 v 为 0、1、10、100，边界分别为 2.4477468306808166、3.6563948713638483、9.606401928868575、32.73018624234933。另用等价标量公式与 CSV 数值核对，摘要中的 v=10 舍入值 9.606401928869 正确。

实际正常命令（退出 0）：

```text
{PY} -I -B {ROOT}/scripts/compute.py --root {ROOT} --output {OUT}/verification-normal
```

随后以 `notes/rejected-parameters.json` 的 alpha=1.0 运行同一计算器，指定独立的 `verification-rejected` 输出位置，实际退出 2，错误为 `ValueError: Require 0<alpha<1, rho>0 and finite nonnegative intrinsic times`。无效试算未生成输出目录。对有效参数、result、table、summary、计算器和原 PDF 的前后完整 SHA、字节数及文件 mtime 均相同，见 `verification.json` 和项目内 `validation/stage-A.json`。这是受控输入校验测试，不是科研分析失败。

权威状态在 `research/state.json`，包含约束、问题与主张、来源身份、材料、选择、活动、依赖、完成时指纹和检查点。`PROJECT.md` 是阅读入口，旧笔记不覆盖权威 JSON。T-CALC 绑定参数、原 PDF、计算器、选择和结果/表格；T-SYNTH 依赖 T-CALC 及主张和结果；T-SOURCE-CHECK 只核对固定来源身份和来源卡，不随数值参数自动失效。完成状态不表示科学认证。

初始四个小文件 `notes/parameters.json`、`results/result.json`、`results/table.csv`、`results/summary.md` 的完整原字节保存在 `.history/A-initial/files/`，对应完整 SHA 和字节数在 `.history/A-initial/manifest.json`。初始权威状态也保留在 `.history/A-initial/state.json`。约束、义务、来源身份、简报及阶段协议真实复制在项目的 `provenance/` 中，恢复不依赖本阶段外部答卷。

实际核对了所给原 PDF 的完整身份 SHA `eb3efd547349adfbff25514ae0854c142cd29b96b398be38c9000d69a2f64ca8`，大小 1494142 字节，与本地材料清单及给定来源身份一致。所登记版本为 Howard 等论文 arXiv:1810.08240v9、DOI 10.1214/20-AOS1991；这是所给固定身份与字节绑定，并非联网版本核实。阅读范围为身份元数据、组织者来源卡以及少量解码文本片段，未独立审阅公式 (14)、命题 5 或全文证明。T-REMOTE 仅保存 arXiv:1808.03204v7 的身份，没有本地内容绑定，未联网检查。`notes/unregistered-scratch.md` 虽随材料保留并具有交付清单指纹，但不作为已登记科学依赖，恢复脚本不自动覆盖它。原 PDF 仅作私有研究缓存，不随外部报告重发。

科学范围是 l0=1 且同一非负 V 下 S、−S 满足相应 sub-Gaussian 指数控制时，固定 rho 和两侧总 alpha 的给定 normal-mixture 边界数值。不能把任意经验方差当作 V。本次未完成新证明、覆盖率模拟、新颖性论证、形式化验证或人类专家批准。

在项目内运行 `python3 -I -B resume.py` 可只读查看当前约束、下一步、变化文件、三项活动状态及检查点。已实际执行两次，均退出 0；最后一次前后项目所有普通文件字节、文件 mtime 与目录 mtime 均保持相同，证据在 `readonly-recovery-test.json`。该脚本只检查显式登记范围，不执行后续科学动作。`update-state.py` 提供预期版本、旧状态保存及冲突拒绝，且不会自动刷新活动；本阶段只检查其语法，未声称完成写入/冲突测试。

下一步：将当前四点边界表和摘要交作者讨论，具体确认 V 的定义、过程控制条件和 rho 的预先固定。截止日为材料作者给出的 2026-12-15，目标期刊未定；预算仅离线标准库，不采集新数据或重拟合。未经内容复核不投稿。

辅助操作中，首次 PDF 正则扫描未捕获最终退出，随后改用线性扫描成功；为清理自身迟滞扫描而尝试的 `ps` 操作被沙箱拒绝，没有获得进程信息，也未完成该清理。首次失败和补救保留在 `execution.json`，没有以重试成功覆盖原记录。
'''
(OUT/'report.md').write_text(report)

request=BASE/'REQUEST.md'
def cat(paths):return {'argv':['cat',*[str(p) for p in paths]],'cwd':DEFAULT_CWD,'exit_code':0}
initial_cmds=[cat([request]),cat([INP/'PROTOCOL.md',INP/'RECORDING.md',INP/'STAGE-A.md',TK/'skills/rw-workflow/SKILL.md',TK/'core/skill-bridge.md',TK/'core/protocol.md']),{'argv':['find',str(INP),'-type','f','-print'],'cwd':DEFAULT_CWD,'exit_code':0},cat([INP/'initial'/p for p in ['MANIFEST.json','BRIEF.md','constraints.json','obligations.json','source-identities.json','project_payload/scripts/compute.py','project_payload/notes/parameters.json','project_payload/notes/rejected-parameters.json','project_payload/notes/source-check.md','project_payload/results/result.json','project_payload/results/table.csv','project_payload/results/summary.md']]),{'argv':[PY,'-I','-B','-'],'cwd':DEFAULT_CWD,'exit_code':None,'stdin_description':'Auxiliary PDF full-byte SHA and initial regex stream extraction: re.finditer(rb\'<<(.*?)>>\\s*stream\\r?\\n(.*?)\\r?\\nendstream\',b,re.S); first tool returned empty captured stdout after about 10.2 seconds; the returned process metadata was not preserved. Final exit and termination remain unknown.','failure':'naive regex scan did not finish within initial captured response; no scientific result written'},{'argv':[PY,'-I','-B','-u','-'],'cwd':DEFAULT_CWD,'exit_code':0,'stdin_description':'Bounded linear bytes.find stream extraction using zlib; SHA, PDF header, raw term offsets and two selected decoded stream snippets printed','stdout_summary':'PDF full SHA/size matched; selected generic nonparametric excerpts, no independently established title/version from extracted snippets'},{'argv':[PY,'-I','-B','-'],'cwd':DEFAULT_CWD,'exit_code':1,'stdin_description':'Attempted subprocess.run([ps,-axo,pid=,ppid=,command=]) to identify only own stalled regex scan and SIGTERM it; process launch denied before identification','stderr':'PermissionError: [Errno 1] Operation not permitted: ps','nested_attempt':{'argv':['ps','-axo','pid=,ppid=,command='],'cwd':DEFAULT_CWD,'exit_code':None,'result':'spawn denied; no process output'}}]
commands=initial_cmds+[{'argv':[PY,'-I','-B',str(OUT/'build_project.py')],'cwd':str(OUT),'exit_code':0}]+log['commands']+[cat([OUT/'resume-status.json',ROOT/'validation/stage-A.json']),{'argv':[PY,'-I','-B',str(OUT/'finalize.py')],'cwd':str(OUT),'exit_code':0,'note':'This completion code is assigned only after all assertions and output writes in finalizer have completed'}, {'argv':[PY,'-I','-B',str(ROOT/'resume.py')],'cwd':str(ROOT),'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr}]
readmap=log['reads']
for root,label in [(ROOT,'project'),(OUT,'output')]:
 for p in root.rglob('*'):
  if p.is_file():readmap[str(p)]={**finger(p),'access':'full bytes for final inventory; source PDF content access limited as described, scratch not interpreted'}
artifacts={'case_id':'T','stage':'A','inputs':[{'base':'input','path':str(p.relative_to(INP)),**finger(p)} for p in sorted(INP.rglob('*')) if p.is_file()],'guidance':[{'base':str(TK),'path':str(p.relative_to(TK)),**finger(p)} for p in [TK/'skills/rw-workflow/SKILL.md',TK/'core/skill-bridge.md',TK/'core/protocol.md']],'request':{'path':str(request),**finger(request)},'outputs':[{'base':'project','path':str(p.relative_to(ROOT)),**finger(p)} for p in sorted(ROOT.rglob('*')) if p.is_file()]+[{'base':'output','path':str(p.relative_to(OUT)),**finger(p)} for p in sorted(OUT.rglob('*')) if p.is_file() and p.name not in ['inputs-and-artifacts.json','execution.json']],'self_manifest_exclusions':['inputs-and-artifacts.json','execution.json; avoids self-referential hash cycle'],'original_material_distribution':'Original PDF retained only in private project source cache; no PDF or original scientific CSV copied into the external report/output. Result table is a derived project deliverable, not an original source CSV.'}
execution={'case_id':'T','stage':'A','commands':commands,'tool_calls':13,'tool_call_counting':'13 outer functions.exec invocations, including three apply_patch operations; nested exec/apply_patch calls each counted once with their outer wrapper','file_mutations_without_command':[{'tool':'apply_patch','path':str(OUT/'build_project.py')},{'tool':'apply_patch','path':str(ROOT/'update-state.py')},{'tool':'apply_patch','path':str(OUT/'finalize.py')}],'network_calls':0,'model':None,'temperature':None,'seed':None,'tokens':None,'token_limit':None,'read_files':[{'path':p,**x} for p,x in sorted(readmap.items())],'violations':[{'action':'Attempted ps process inventory solely to clean own stalled PDF inspection','status':'sandbox denied before process data obtained','scope_note':'Process inspection was outside the strictly named input/project file workflow; retained as an attempted scope deviation, not silently omitted.'}],'failures':[{'action':'auxiliary regex PDF extraction','exit_code':None,'remediation':'linear bytes.find/zlib partial inspection succeeded; final exit/cleanup of first scan not verified'},{'action':'ps cleanup helper','exit_code':1,'remediation':'No further process inventory or escalation attempted; scientific work continued without relying on it'},{'action':'controlled rejected parameters trial','exit_code':2,'expected':True,'remediation':'none; invalid alpha rejected, valid artifacts unchanged'}],'written_paths':[str(p) for p in sorted(ROOT.rglob('*')) if p.is_file()]+[str(p) for p in sorted(OUT.rglob('*')) if p.is_file()]+[str(OUT/'execution.json'),str(OUT/'inputs-and-artifacts.json')],'unknown_execution_notes':['Original auxiliary regex scan final exit not observed; do not infer termination.','Transport shell exact launch flags are not exposed; commands list preserves invoked program argv and actual scripted arguments.','No core Python source was read, copied, imported or executed; guidance markdown only.','No memory, personal skill, other project, future material, network, install or other agent was accessed.'],'settings_assumption':'No inferred same-model, temperature, seed or token setting.'}
assert len(report)<10000
assert json.loads(r.stdout)['checkpoint_freshness']['fresh']
save(OUT/'inputs-and-artifacts.json',artifacts)
save(OUT/'execution.json',execution)
print(json.dumps({'report':str(OUT/'report.md'),'report_unicode_chars':len(report),'execution':str(OUT/'execution.json'),'state_answer':str(OUT/'state-answer.json'),'manifest':str(OUT/'inputs-and-artifacts.json'),'tool_calls':13,'last_resume_exit':r.returncode},ensure_ascii=False))
