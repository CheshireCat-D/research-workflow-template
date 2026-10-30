import hashlib,json,os,subprocess,sys
from pathlib import Path
ROOT=Path('PROJECT_ROOT');OUT=Path('OUTPUT_DIR');INPUT=OUT.parent/'input';PY='EVAL_PYTHON'
log=json.loads((OUT/'execution.json').read_text())
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def fingerprint(p):
 b=p.read_bytes();return {'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
for name in ['PROTOCOL.md','RECORDING.md','STAGE-C.md']:
 p=ROOT/'provenance/stage-C'/name;p.write_bytes((INPUT/name).read_bytes());log['written_paths'].append(str(p))
for name in ['final-resume.stdout','final-resume.stderr','recompute-verification.json']:
 p=ROOT/'validation'/('stage-C-'+name);p.write_bytes((OUT/name).read_bytes());log['written_paths'].append(str(p))
initial=json.loads((ROOT/'.history/C-drift/manifest.json').read_text());current=json.loads((ROOT/'research/state.json').read_text())
changed=[]
for rel,old in initial.items():
 p=ROOT/rel
 if not p.exists():changed.append({'path':rel,'change':'missing'})
 elif fingerprint(p)!={k:old[k] for k in ('sha256','bytes')}:changed.append({'path':rel,'change':'bytes changed','before':{k:old[k] for k in ('sha256','bytes')},'after':fingerprint(p)})
proof={'snapshot':'.history/C-drift/manifest.json','initial_retained':'.history/A-initial/files/','unchanged_primary_sha256':fingerprint(ROOT/'sources/howard2021-arxiv-v9.pdf'),'unchanged_calculator_sha256':fingerprint(ROOT/'scripts/compute.py'),'changed_original_paths':changed,'final_metadata_revision':current['metadata_revision'],'record_versions':{rid:x['version'] for rid,x in current['records'].items()},'final_check_exit_code':0,'mid_check_exit_code':1}
save(OUT/'revision-audit.json',proof)
report='''# 参数修订与当前恢复状态

已按明确授权使用 alpha=0.05、观察前固定 rho=4、V∈{0,1,10,100} 真实复算，更新结果、表格、摘要、材料绑定、关系、选择和受影响活动。权威状态在 `project/research/state.json`，元数据修订为4；截止日2026-12-15、离线标准库预算、不采新数据/不重拟合、期刊未定等约束未变。

## 先保存漂移，再实际复核

未重算时的全部既存项目文件及完整 SHA/字节/mtime 清单保存在 `project/.history/C-drift/files/`、`manifest.json`；新漂移断点在同目录 `checkpoint.json`。保存后立即运行现有 `resume.py`，真实退出1。原始标准输出保存在本交付目录 `intermediate-resume.stdout`，同时在项目 `validation/stage-C-intermediate-resume.stdout` 保留，未被最终成功输出覆盖。

该中间检查确认：`notes/parameters.json` 已变成rho=4，而权威配置和旧结果仍为rho=1。新断点自身 fresh=true，但 T-CALC 和 T-SYNTH 仍 stale；后者还受到计算依赖失效的影响。因此保存新断点没有重新验证先前完成的工作。独立 T-SOURCE-CHECK 仍 done：原PDF、来源身份记录、固定核验卡及该活动捕获的文件/记录均未变化，rho不是此活动依赖。

## 真实计算与修订

使用未改动的 `scripts/compute.py`，通过离线Python标准库实际计算到独立新目录 `validation/stage-C-recompute/`，退出0。核对批准参数与现有参数、结果记录的输入SHA、四点网格、直接公式数值及JSON/CSV逐项对应，均通过。canonical结果从该实际输出更新至 `results/result.json` 与 `results/table.csv`，摘要已重新写入并完整读取核对。

| V | rho=4边界值 |
|---:|---:|
| 0 | 4.895493661362 |
| 1 | 5.574319733574 |
| 10 | 10.070709270873 |
| 100 | 31.015388968276 |

完整精度与输入SHA见JSON；本表仅显示12位小数。计算式为 sqrt((V+rho)·(log(1+V/rho)+2log(1/alpha)))，l0=1，alpha为两侧总错误预算。固定原始资料要求 S与−S 对同一非负内在时间V满足相应sub-Gaussian指数控制；V不能被任意经验方差替代。本轮改变另一个预先固定的正rho，没有改变alpha或预先固定政策；程序复算没有证明新的覆盖保证。

T-PARAM、T-CLAIM、T-REL、T-CHOICE、T-RESULT、T-SUMMARY、T-CALC、T-SYNTH 均显式升为版本2；来源、原始材料、计算器、固定来源卡及来源核验记录仍为版本1。修订使用当前元数据修订2及各记录预期版本，通过现有带冲突保护的 `update-state.py` 实际提交，退出0。该提交本身仍未重新绑定活动；只有在实际复算/审阅之后才显式更新T-CALC和T-SYNTH的文件SHA及记录版本捕获。T-SOURCE-CHECK未重新绑定。

初始rho=1的参数、结果、表格、摘要完整内容保留在 `.history/A-initial/files/`；C修订前的完整现状在 `.history/C-drift/files/`；每次旧权威状态保留在 `.history/metadata/revision-1.json` 至 `revision-3.json`。明确授权及实际修订patch保留在 `provenance/stage-C/`。实际验证记录在 `validation/stage-C.json`，中间、最终恢复输出分别保存。原PDF、计算器、来源核验卡、现有rho=4参数文件的字节与mtime均未修改；数值成果和状态依授权更新。

## 最终检查与下一步

最后运行现有只读恢复程序，退出0：changed_or_missing_paths为空，三项活动的effective_status均为done，最终断点fresh=true。项目内保存 `research/checkpoints/C-final.json`。这仅说明所声明依赖和登记当前一致；done表示这次有界工作实际完成，不是内容认可或科学认证。

可执行恢复命令：在项目根执行 `python3 -I -B resume.py`；程序及所有必要状态都在项目中，不依赖本交付目录或原输入路径。当前具体下一步已写入权威状态：将rho=4的边界表与更新摘要交作者内容复核，确认V的含义及过程控制条件，暂不扩展到事后选择rho。没有人类专家认可、形式化验证或投稿授权。

## 来源范围与保留的异常

原PDF是 Howard等 (2021), arXiv:1810.08240v9，DOI 10.1214/20-AOS1991；完整SHA为 `eb3efd547349adfbff25514ae0854c142cd29b96b398be38c9000d69a2f64ca8`，1494142字节。此次读取完整字节仅为指纹和私有快照保留，读取来源卡及已存身份记录；没有在本轮阅读PDF页面、验证公式出处或证明。继承的来源活动原范围是身份版本核验，不能将其表述为全文科学审稿。T-REMOTE仅有远端来源身份，无本地内容绑定，也没有联网核查。`notes/unregistered-scratch.md`不进入自动活动失效覆盖；历史快照保存它的字节不扩大此覆盖。

第一次批量显示输出被工具截断，已保留该执行异常说明；随后完整重读两个本地状态脚本，并完整解析权威JSON，未用截断显示代替状态检查。中间检查退出1是实际发现过期活动，已按顺序保存并修复其原因；没有用最终退出0覆盖。计算和修订未出现非零退出。网络调用0，未安装依赖，未知模型/温度/seed/token和系统上限保持null。原始PDF只在本项目私有缓存与历史快照中保留，不对外分发。
'''
(OUT/'report.md').write_text(report);log['written_paths'].append(str(OUT/'report.md'))
# Capture command provenance without pretending that the shell wrapper argv was exposed.
common='STUDY_ROOT/runs/P3/'
log['bootstrap_commands']=[
 {'argv':['cat',common+'C/REQUEST.md'],'cwd':'TASK_WORKSPACE','exit_code':0},
 {'argv':['cat',*[common+'C/input/'+s for s in ['PROTOCOL.md','RECORDING.md','STAGE-C.md']],*[str(Path('TOOLKIT_ROOT')/s) for s in ['skills/rw-workflow/SKILL.md','core/skill-bridge.md','core/protocol.md']]],'cwd':'TASK_WORKSPACE','exit_code':0},
 {'argv':['find',common+'C/input',str(ROOT),'-type','f','-maxdepth','5','-print'],'cwd':'TASK_WORKSPACE','exit_code':0},
 {'argv':['cat',common+'C/input/author-revision/AUTHOR-REVISION.md',common+'C/input/author-revision/approved-parameters.json',*[str(ROOT/s) for s in ['research/state.json','resume.py','update-state.py','PROJECT.md','provenance/initial/obligations.json','provenance/initial/constraints.json','provenance/initial/source-identities.json','provenance/initial/BRIEF.md','scripts/compute.py','notes/parameters.json','notes/rejected-parameters.json','notes/source-check.md','notes/unregistered-scratch.md','results/result.json','results/table.csv','results/summary.md']]],'cwd':'TASK_WORKSPACE','exit_code':0,'output_display_truncated':True},
 {'argv':['cat',str(ROOT/'resume.py'),str(ROOT/'update-state.py')],'cwd':'TASK_WORKSPACE','exit_code':0}
]
log['driver_commands']=[{'argv':[PY,'-I','-B',str(OUT/'stage_c.py'),mode],'cwd':'TASK_WORKSPACE','exit_code':0} for mode in ['prepare','compute','revise']]
log['driver_commands'] += [{'argv':[PY,'-I','-B','-'],'cwd':'TASK_WORKSPACE','exit_code':0,'meaning':'standard-input local file assembly to add revise mode to stage_c.py; source retained in final script'}, {'argv':[PY,'-I','-B',str(OUT/'finalize.py')],'cwd':'TASK_WORKSPACE','exit_code':0,'meaning':'this finalization; record written only after assertions below pass'}]
log['shell_wrapper_argv']=None;log['shell_wrapper_note']='Program argv above is determined by submitted command text; tool-managed shell process argv is not exposed.'
# Complete full SHA inventory of actual byte reads, keeping historical state fingerprints too.
log['read_version_evidence']={}
for rel in ['research/state.json','results/result.json','results/table.csv','results/summary.md']:
 versions=[]
 for p in [ROOT/'.history/C-drift/files'/rel,ROOT/rel]:
  if p.is_file():versions.append(dict(path=str(p),**fingerprint(p)))
 if rel=='research/state.json':
  for p in sorted((ROOT/'.history/metadata').glob('revision-*.json')):versions.append(dict(path=str(p),**fingerprint(p)))
 log['read_version_evidence'][str(ROOT/rel)]=versions
read_paths=set(log['read_files'])
read_paths.update(str(p) for p in ROOT.rglob('*') if p.is_file())
read_paths.update(str(p) for p in OUT.rglob('*') if p.is_file() and p.name not in ['execution.json','inputs-and-artifacts.json'])
for path in sorted(read_paths):
 p=Path(path)
 if p.is_file():log['read_files'][str(p)]=fingerprint(p)
log['read_scope_note']='Whole-byte SHA reads do not mean full content review. Original source PDF hashed/copied only in C; no PDF page/theorem read. Directory inventory alone did not read file contents.'
log['tool_calls']=9
log['failures_or_nonzero_checks'][1]['meaning']='Expected and preserved actual stale result after new drift checkpoint; T-CALC/T-SYNTH required actual recomputation/review; repaired only afterward.'
log['written_paths']=sorted(set(log['written_paths']+[str(OUT/'execution.json'),str(OUT/'inputs-and-artifacts.json'),str(OUT/'revision-audit.json')]))
assert len(report)<10000
assert current['configuration']['current_scope']['rho']==4
assert all(current['records'][r]['version']==1 for r in ['T-SRC','T-RAW','T-CODE','T-SOURCE-NOTE','T-SOURCE-CHECK'])
save(OUT/'execution.json',log)
manifest={'case_id':'T','stage':'C','inputs':[],'project_current_and_history_artifacts':[],'output_artifacts':[],'self_exclusions':['inputs-and-artifacts.json (self fingerprint excluded to avoid recursive hash)'],'distribution_scope':'No original PDF bytes included in external report deliverables; original material is private project cache/history only. Hashing is byte identity, not page/formula/proof review.'}
for p in sorted(INPUT.rglob('*')):
 if p.is_file():manifest['inputs'].append(dict(path=str(p.relative_to(INPUT)),**fingerprint(p)))
for p in sorted(ROOT.rglob('*')):
 if p.is_file():manifest['project_current_and_history_artifacts'].append(dict(path=str(p.relative_to(ROOT)),**fingerprint(p)))
for p in sorted(OUT.rglob('*')):
 if p.is_file() and p.name!='inputs-and-artifacts.json':manifest['output_artifacts'].append(dict(path=str(p.relative_to(OUT)),**fingerprint(p)))
save(OUT/'inputs-and-artifacts.json',manifest)
print(json.dumps({'report_chars':len(report),'project_metadata_revision':current['metadata_revision'],'written':str(OUT/'report.md'),'tool_calls':log['tool_calls'],'original_paths_changed':[x['path'] for x in changed]},ensure_ascii=False))
