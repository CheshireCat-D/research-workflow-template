import csv, hashlib, json, math, os, shutil, subprocess, sys, zlib
from pathlib import Path

BASE=Path('STUDY_ROOT/runs/P3/A')
INP=BASE/'input'; OUT=BASE/'output'; ROOT=BASE.parent/'project'
PY='EVAL_PYTHON'
TOOLKIT=Path('TOOLKIT_ROOT')
reads={}; commands=[]; writes=[]
def fp(p):
 b=Path(p).read_bytes();return {'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def read(p,scope='full text/content'):
 p=Path(p);b=p.read_bytes();reads[str(p)]={**fp(p),'access':scope};return b
def js(p):return json.loads(read(p).decode())
def dump(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n');writes.append(str(p))
def textfile(p,s):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s);writes.append(str(p))
def run(argv,cwd):
 r=subprocess.run(argv,cwd=cwd,capture_output=True,text=True)
 row={'argv':argv,'cwd':str(cwd),'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr};commands.append(row);return row
def canonical(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()

assert not ROOT.exists(),'Refuse to replace existing project'
OUT.mkdir(parents=True,exist_ok=True)
for p in [BASE/'REQUEST.md',INP/'PROTOCOL.md',INP/'RECORDING.md',INP/'STAGE-A.md',TOOLKIT/'skills/rw-workflow/SKILL.md',TOOLKIT/'core/skill-bridge.md',TOOLKIT/'core/protocol.md']:
 read(p)
manifest=js(INP/'initial/MANIFEST.json');brief=read(INP/'initial/BRIEF.md').decode()
constraints=js(INP/'initial/constraints.json');obligations=js(INP/'initial/obligations.json');sources=js(INP/'initial/source-identities.json')
for rel,expected in manifest['files'].items():
 p=INP/'initial'/rel
 read(p,'full bytes copied and hashed; PDF only partial decoded text identity inspection; scratch content not used' if p.suffix=='.pdf' or p.name=='unregistered-scratch.md' else 'full text/content')
 assert fp(p)==expected,(rel,'manifest mismatch')
ROOT.mkdir()
shutil.copytree(INP/'initial/project_payload',ROOT,dirs_exist_ok=True)
for p in (INP/'initial').iterdir():
 if p.is_file():
  target=ROOT/'provenance/initial'/p.name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target);writes.append(str(target))
for name in ['PROTOCOL.md','RECORDING.md','STAGE-A.md']:
 target=ROOT/'provenance/stage-A'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(INP/name,target);writes.append(str(target))

normal=run([PY,'-I','-B',str(ROOT/'scripts/compute.py'),'--root',str(ROOT),'--output',str(OUT/'verification-normal')],ROOT)
assert normal['exit_code']==0,normal
current=json.loads(read(ROOT/'results/result.json'));actual=json.loads(read(OUT/'verification-normal/result.json'))
assert actual==current
assert read(ROOT/'results/result.json')==read(OUT/'verification-normal/result.json')
assert read(ROOT/'results/table.csv')==read(OUT/'verification-normal/table.csv')
params=json.loads(read(ROOT/'notes/parameters.json'))
rows=list(csv.DictReader((ROOT/'results/table.csv').read_text().splitlines()))
assert len(rows)==len(params['intrinsic_time_grid'])==len(current['values'])
manual=[]
for row,value,v in zip(rows,current['values'],params['intrinsic_time_grid']):
 expected=math.sqrt((v+params['rho'])*(math.log(1+v/params['rho'])-2*math.log(params['alpha'])))
 assert float(row['v'])==v and float(row['boundary'])==value['boundary']
 assert math.isclose(expected,value['boundary'],rel_tol=2e-15,abs_tol=2e-15)
 manual.append({'v':v,'boundary':value['boundary'],'algebraic_formula_check':expected})
summary=read(ROOT/'results/summary.md').decode();assert '9.606401928869' in summary and round(current['values'][2]['boundary'],12)==9.606401928869
protected=['notes/parameters.json','results/result.json','results/table.csv','results/summary.md','scripts/compute.py','sources/howard2021-arxiv-v9.pdf']
before={p:fp(ROOT/p) for p in protected}
before_times={p:(ROOT/p).stat().st_mtime_ns for p in protected}
invalid=run([PY,'-I','-B',str(ROOT/'scripts/compute.py'),'--root',str(ROOT),'--spec',str(ROOT/'notes/rejected-parameters.json'),'--output',str(OUT/'verification-rejected')],ROOT)
assert invalid['exit_code']==2 and 'Require 0<alpha<1' in invalid['stderr']
after={p:fp(ROOT/p) for p in protected};after_times={p:(ROOT/p).stat().st_mtime_ns for p in protected}
assert before==after and before_times==after_times and not (OUT/'verification-rejected').exists()
verification={'normal_command':normal,'rejected_command':invalid,'result_semantic_equal':actual==current,'result_byte_equal':True,'table_byte_equal':True,'summary_numeric_and_scope_review':'matches alpha=.05 rho=1 fixed-before-observation, grid and rounded v=10 value; conditional numerical evaluation only','values':manual,'invalid_input_test':{'purpose':'controlled validation test, not scientific failure','parameter':'alpha=1.0','expected_exit_code':2,'actual_exit_code':invalid['exit_code'],'protected_before':before,'protected_after':after,'protected_mtime_ns_before':before_times,'protected_mtime_ns_after':after_times,'invalid_output_created':False}}
dump(OUT/'verification.json',verification)
dump(ROOT/'validation/stage-A.json',verification)
for filename in ['result.json','table.csv']:
 target=ROOT/'validation/stage-A-normal'/filename;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(OUT/'verification-normal'/filename,target)

snapshot=['notes/parameters.json','results/result.json','results/table.csv','results/summary.md']
snap={}
for rel in snapshot:
 target=ROOT/'.history/A-initial/files'/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/rel,target)
 snap[rel]={'file':str(target.relative_to(ROOT)),**fp(target)}
dump(ROOT/'.history/A-initial/manifest.json',{'stage':'A','reason':'recover initial bytes before any future revision','files':snap,'source':'supplied initial material; numerical outputs independently rerun using supplied calculator'})
tracked=list(obligations['local_tracking_paths'])+['results/table.csv']
records={}
for node in obligations['nodes']:
 rec={'version':1,'data':node.copy()}
 if node['id']=='T-SRC':rec['data'].update(sources['primary']);rec['data']['content_access']='partial: full bytes hashed against supplied manifest and source card read; selected PDF streams inspected for textual identity context, no page/formula/theorem review'
 if node['id']=='T-REMOTE':rec['data'].update(sources['source_only'])
 if node['id']=='T-RESULT':rec['data']['companion_paths']=['results/table.csv']
 if node['id']=='T-CHOICE':rec['data'].update({'responsible':'benchmark material author; not a human approval by executor','rationale':'initial benchmark-specified parameters; alpha .05, rho 1 selected before observation','decided_at':None})
 records[node['id']]=rec
file_bindings={p:fp(ROOT/p) for p in tracked}
bindings={
 'T-SOURCE-CHECK':{'paths':['sources/howard2021-arxiv-v9.pdf','notes/source-check.md'],'records':['T-SRC','T-RAW','T-SOURCE-NOTE']},
 'T-CALC':{'paths':['notes/parameters.json','sources/howard2021-arxiv-v9.pdf','scripts/compute.py','results/result.json','results/table.csv'],'records':['T-PARAM','T-RAW','T-CODE','T-CHOICE','T-RESULT']},
 'T-SYNTH':{'paths':['notes/parameters.json','results/result.json','results/table.csv','results/summary.md'],'records':['T-CLAIM','T-RESULT','T-SUMMARY']}}
activities={}
for aid,binding in bindings.items():
 node=records[aid]['data'];activities[aid]={'declared_status':'done','executor':'AI assistant; no independent human review','scientific_certification':False,'inputs':node['inputs'],'outputs':node['outputs'],'depends_on':node.get('depends_on',[]),'captured_files':{p:file_bindings[p] for p in binding['paths']},'captured_records':{rid:{'version':records[rid]['version'],'content_sha256':canonical(records[rid])} for rid in binding['records']},'evidence':'validation/stage-A.json','scope':node['meaning']}
state={'format':'local-research-state-v1','case_id':'T','metadata_revision':1,'authority':'research/state.json; notes, provenance and checkpoints do not override current configuration or records','configuration':constraints,'records':records,'activities':activities,'tracked_files':file_bindings,'tracking_exclusions':obligations['tracking_exclusions'],'publication_rule':sources['publication_rule'],'scientific_scope':{'formula':'sqrt((v+rho)*(log(1+v/rho)+2*log(1/alpha)))','l0':1,'process_conditions':'S and -S have the required sub-Gaussian exponential control for the same nonnegative intrinsic time V; alpha is the total two-sided error budget','rho_rule':'fixed before observation','assessment':'specified numerical values and summary checked; proof, simulation coverage, novelty and human approval not assessed','formal_verification':'not-started; not required in this numerical task'},'next_action':'将 alpha=0.05、rho=1 的四点边界表和摘要交作者讨论：先确认 intrinsic time V 的含义及过程是否满足给定 sub-Gaussian 控制，rho 在观察前固定；未经内容复核不投稿。','checkpoint':None,'history':[{'revision':1,'basis':'provenance/initial/BRIEF.md and constraints.json; original four small files recoverable from .history/A-initial/files','event':'initial project and completed bounded numerical verification'}]}
state['checkpoint']={'stage':'A','metadata_revision':1,'configuration_sha256':canonical(state['configuration']),'records_sha256':canonical(state['records']),'activities_sha256':canonical(state['activities']),'tracked_files':file_bindings,'next_action':state['next_action'],'note':'checkpoint is a recovery pointer, not scientific review'}
dump(ROOT/'research/state.json',state)
dump(ROOT/'.history/A-initial/state.json',state)

recovery='''#!/usr/bin/env python3
"""Local project recovery: standard library, read-only status, no external resources."""
import argparse,hashlib,json,sys
from pathlib import Path
def digest(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def fingerprint(p):
 if p.is_symlink() or not p.is_file():return {"missing_or_nonregular":True}
 b=p.read_bytes();return {"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def status(root):
 state=json.loads((root/"research/state.json").read_text())
 actual={p:fingerprint(root/p) for p in state["tracked_files"]}
 changed=[p for p,old in state["tracked_files"].items() if actual[p]!=old]
 activities={}
 for aid,a in state["activities"].items():
  reasons=[{"file":p,"expected":old,"actual":fingerprint(root/p)} for p,old in a["captured_files"].items() if fingerprint(root/p)!=old]
  for rid,old in a["captured_records"].items():
   now=state["records"].get(rid)
   if not now or now["version"]!=old["version"] or digest(now)!=old["content_sha256"]:reasons.append({"record":rid,"cause":"version or record content changed"})
  activities[aid]={"declared_status":a["declared_status"],"effective_status":"stale" if reasons else a["declared_status"],"reasons":reasons}
 for iteration in range(len(activities)):
  for aid,a in state["activities"].items():
   for dep in a["depends_on"]:
    if activities[dep]["effective_status"]!="done":
     activities[aid]["effective_status"]="stale"
     reason={"depends_on":dep,"cause":"dependency not currently complete"}
     if reason not in activities[aid]["reasons"]:activities[aid]["reasons"].append(reason)
 cp=state.get("checkpoint") or {};cp_reasons=[]
 for key in ["configuration","records","activities"]:
  if cp.get(key+"_sha256")!=digest(state[key]):cp_reasons.append(key+" changed since checkpoint")
 if cp.get("metadata_revision")!=state.get("metadata_revision"):cp_reasons.append("metadata revision changed")
 if cp.get("tracked_files")!=actual:cp_reasons.append("tracked file bytes changed or missing")
 return {"case_id":state["case_id"],"authority":state["authority"],"metadata_revision":state["metadata_revision"],"active_constraints":state["configuration"],"next_action":state["next_action"],"changed_or_missing_paths":changed,"activities":activities,"checkpoint_freshness":{"fresh":not cp_reasons,"reasons":cp_reasons},"scientific_scope":state["scientific_scope"],"source_tracking_limits":state["tracking_exclusions"],"publication_rule":state["publication_rule"],"resume_is_read_only":True,"no_scientific_certification":True}
def main():
 p=argparse.ArgumentParser();p.add_argument("--root",type=Path,default=Path(__file__).resolve().parent);a=p.parse_args()
 try:
  report=status(a.root.resolve());print(json.dumps(report,ensure_ascii=False,indent=2));return 1 if report["changed_or_missing_paths"] or not report["checkpoint_freshness"]["fresh"] or any(x["effective_status"]!="done" for x in report["activities"].values()) else 0
 except (OSError,ValueError,KeyError,TypeError) as e:
  print(json.dumps({"error":type(e).__name__,"message":str(e)}));return 2
if __name__=="__main__":raise SystemExit(main())
'''
textfile(ROOT/'resume.py',recovery)
textfile(ROOT/'PROJECT.md','''# 固定精度正态混合边界数值核对

权威状态在 `research/state.json`。当前 alpha=0.05、rho=1，rho 在观察前选定；截止日 2026-12-15，目标期刊未定。预算仅限离线 Python 标准库；不采新数据，不重拟合。原始 PDF 是私有研究缓存，不对外分发。

在项目根运行 `python3 -I -B resume.py` 可只读检查已跟踪文件、活动依赖、配置和检查点；退出 0 表示当前登记无漂移，1 表示有漂移或过期活动，2 表示读取错误。项目只依赖 Python 标准库，不依赖原输入目录、外部报告或其他工具包。

实际完成范围和退出码见 `validation/stage-A.json`。正常计算结果与预制 result.json、table.csv 逐字节相同；摘要中的 v=10 数值与条件性表述已核对。受控 alpha=1 试算按预期退出 2，有效参数、结果、表格、摘要、计算器和原 PDF 的字节及文件 mtime 均未改变。这是输入校验测试，不是科学失败。

来源身份来自 `provenance/initial/source-identities.json`，原 PDF 完整 SHA 与清单一致。只读了来源卡、身份元数据和少量解码文本片段，未复核 PDF 公式或证明。远端来源仅有身份，未联网核对；scratch 文件不纳入活动失效覆盖。

下一步：将四点边界表和摘要交作者讨论，确认 V 与过程控制条件以及 rho 的预先固定；未经内容复核不投稿。没有人类专家批准，也没有形式化验证或投稿授权。

初始四个小文件的完整字节位于 `.history/A-initial/files/`，清单给出完整 SHA 和字节数。修改前先保留旧内容与依据；不要把新检查点当作重新验证。更改配置或记录后须更新 `metadata_revision` 和对应记录 `version`，记录旧状态及修订理由；活动只有在实际重新执行或审阅后才可重新绑定，且不能仅用旧笔记覆盖权威 JSON。
''')
resume=run([PY,'-I','-B',str(ROOT/'resume.py')],ROOT);assert resume['exit_code']==0,resume
textfile(OUT/'resume-status.json',resume['stdout'])
dump(OUT/'build-log.json',{'commands':commands,'reads':reads,'writes':writes,'manifest_all_match':True,'bootstrap_argv':sys.argv,'bootstrap_cwd':os.getcwd()})
print(json.dumps({'project':str(ROOT),'normal_exit':normal['exit_code'],'invalid_exit':invalid['exit_code'],'resume_exit':resume['exit_code'],'all_initial_manifest_matches':True},ensure_ascii=False))
