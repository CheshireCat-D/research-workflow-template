from pathlib import Path
import hashlib, json, os, shutil, subprocess, sys
B=Path('STUDY_ROOT/runs/P4'); P=B/'project'; O=B/'A/output'; I=B/'A/input'
PY='EVAL_PYTHON'
def load(p):return json.loads(p.read_text())
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def fp(p):
 b=p.read_bytes();return {'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def snap():
 return {str(p.relative_to(P)):{'mtime_ns':p.stat().st_mtime_ns,'kind':'file',**fp(p)} if p.is_file() else {'mtime_ns':p.stat().st_mtime_ns,'kind':'directory'} for p in [P,*sorted(P.rglob('*'))]}
old_argv=[PY,'-I','-B',str(P/'_rw-runtime/tools/research.py'),'resume','--root',str(P)]
for ext in ['stdout','stderr']:
 old=O/'logs'/('09-portable-resume.'+ext)
 if old.exists():shutil.copy2(old,O/'logs'/('09-portable-resume-failed.'+ext))
before=snap()
argv=[PY,'-I','-B',str(P/'.agents/skills/_rw-runtime/tools/research.py'),'resume','--root',str(P)]
r=subprocess.run(argv,cwd=P,text=True,capture_output=True)
(O/'logs/10-portable-resume.stdout').write_text(r.stdout)
(O/'logs/10-portable-resume.stderr').write_text(r.stderr)
assert r.returncode==0,r.stdout+r.stderr
s=json.loads(r.stdout);after=snap()
assert before==after
assert s['passed'] and s['checkpoint']['status']=='current' and s['revision']==22
assert all(a['effective_status']=='done' for a in s['activities'])
for rel,expected in load(P/'history/stage-A-initial/manifest.json')['files'].items():
 assert fp(P/'history/stage-A-initial'/rel)==expected
 assert fp(P/rel)==expected
for rel in ['result.json','table.csv']:assert fp(P/'results'/rel)==fp(O/'validation-normal'/rel)
assert not (O/'validation-invalid').exists()
ledger=load(O/'execution.json')
ledger['commands'].extend([
 {'name':'09-portable-resume-first-failed','argv':old_argv,'cwd':str(P),'exit_code':2,'stdout':(O/'logs/09-portable-resume-failed.stdout').read_text(),'stderr':(O/'logs/09-portable-resume-failed.stderr').read_text()},
 {'name':'10-portable-resume','argv':argv,'cwd':str(P),'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr},
 {'name':'finalizer-first','argv':[PY,'-I','-B',str(O/'auditrun.py'),str(O/'logs/finalizer.reads.json'),str(O/'finalize.py')],'cwd':'TASK_WORKSPACE','exit_code':0,'old_output_preserved':'failure-preservation/'},
 {'name':'finalizer-corrected','argv':[PY,'-I','-B',str(O/'auditrun.py'),str(O/'logs/finalizer.reads.json'),str(O/'finalize.py')],'cwd':'TASK_WORKSPACE','exit_code':0},
 {'name':'final-check','argv':[PY,'-I','-B',str(O/'auditrun.py'),str(O/'logs/final-check.reads.json'),str(O/'final_check.py')],'cwd':os.getcwd(),'exit_code':0}])
ledger['failures'].extend([
 {'command':'09-portable-resume-first-failed','exit_code':2,'outer_assertion_exit_code':1,'message':'Runtime was incorrectly assumed at project/_rw-runtime/tools/research.py; actual installed path is project/.agents/skills/_rw-runtime/tools/research.py','remedy':'Kept first stderr, corrected RECOVERY.md and report, preserved first report/execution/inventory and reran installed runtime successfully. Canonical research results unchanged.'},
 {'command':'inspect-installed-runtime-layout','argv':[PY,'-I','-B','-c','from pathlib import Path; import json; p=Path("PROJECT_ROOT"); print("\\n".join(str(f.relative_to(p)) for f in sorted(p.rglob("*")) if f.is_file() and (f.name in ["research.py","connect_skills.py","bundle-manifest.json"] or f.parent==p))); print(json.dumps(json.loads((p/"_rw-runtime/bundle-manifest.json").read_text()).keys()))'],'cwd':'TASK_WORKSPACE','exit_code':1,'message':'FileNotFoundError for assumed project/_rw-runtime/bundle-manifest.json after listing actual installed .agents/skills/_rw-runtime paths','remedy':'Used listed actual path; no tool/catalog mutation.'}])
ledger['tool_calls']=22;ledger['outer_tool_call_count']=22
ledger['tool_calls_basis']='22 outer functions.exec calls including final inventory refresh; call 11 contained both one shell execution and one apply_patch. No other agents or network calls.'
ledger['recording_limitations']=['Initial ad hoc read-only inspections were not launched under the later command/audit wrapper. Their actual read paths and full fingerprints are recorded; the full original -c strings of every early inspection were not persisted automatically. Calculator, core-interface and installed-runtime command argv/cwd/exit codes are complete.','Source runtime internally reads design/catalog.json as disclosed under violations; no evaluator materials or remote contents were read.']
ledger['portable_resume']={'passed':True,'source_toolkit_needed':False,'actual_runtime_relative_path':'.agents/skills/_rw-runtime/tools/research.py','project_bytes_and_file_and_directory_mtimes_unchanged':True,'exit_code':0}
reads={(v['path'],v['sha256']):v for v in ledger['read_files']}
for f in [O/'logs/finalizer.reads.json']:
 for row in load(f):reads.setdefault((row['path'],row['sha256']),{**row,'recorded_by':str(f.relative_to(O))})
for root in [P,O]:
 for p in sorted(root.rglob('*')):
  if p.is_file() and p.name!='inputs-and-artifacts.json':
   row={'path':str(p),**fp(p),'read_scope':'Full-byte final verification inventory'}
   reads.setdefault((row['path'],row['sha256']),row)
ledger['read_files']=list(reads.values())
ledger['written_paths']=[str(p) for root in [P,O] for p in sorted(root.rglob('*')) if p.is_file()]
save(O/'read-manifest.json',list(reads.values()))
save(O/'execution.json',ledger)
audit={'case_id':'D','stage':'A','passed':True,'checkpoint':s['checkpoint'],'findings':s['findings'],'all_activities_done':True,'normal_result_and_table_byte_identical':True,'all_four_initial_snapshots_match_initial_current_bytes':True,'invalid_output_absent':True,'portable_resume_read_only_bytes_and_file_and_directory_mtimes':True,'runtime_relative_path':'.agents/skills/_rw-runtime/tools/research.py','report_unicode_characters':len((O/'report.md').read_text()),'execution':fp(O/'execution.json'),'tool_calls':22}
save(O/'final-audit.json',audit)
print(json.dumps(audit,ensure_ascii=False,indent=2))
