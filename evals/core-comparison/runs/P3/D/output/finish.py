from pathlib import Path
import os,json,hashlib
p=Path('PROJECT_ROOT')
i=Path('INPUT_DIR')
o=Path('OUTPUT_DIR')
request=Path('STUDY_ROOT/runs/P3/D/REQUEST.md')
py='EVAL_PYTHON'
cwd='TASK_WORKSPACE'
def scan(root):
 result=[]
 for base,dirs,files in os.walk(root,followlinks=False):
  for name in sorted(dirs+files):
   f=Path(base)/name;s=f.lstat();row={'path':str(f.relative_to(root)),'bytes':s.st_size,'mtime_ns':s.st_mtime_ns,'type':'symlink' if f.is_symlink() else ('dir' if f.is_dir() else 'file')}
   if row['type']=='file':row['sha256']=hashlib.sha256(f.read_bytes()).hexdigest()
   if row['type']=='symlink':row['target']=os.readlink(f)
   result.append(row)
 s=root.stat();result.append({'path':'.','type':'dir','bytes':s.st_size,'mtime_ns':s.st_mtime_ns})
 return result
def save(name,x):(o/name).write_text(json.dumps(x,ensure_ascii=False,indent=2))
before=json.loads((o/'initial-snapshot.json').read_text());after={'project':scan(p),'input':scan(i)}
save('final-snapshot.json',after)
b={x['path']:x for x in before['project']};a={x['path']:x for x in after['project']}
changes=[{'path':k,'before':b.get(k),'after':a.get(k)} for k in sorted(set(b)|set(a)) if b.get(k)!=a.get(k)]
audit={'project_file_bytes_hashes_and_mtimes_unchanged':not changes,'project_directory_mtimes_unchanged':not any((x['before'] or x['after'])['type']=='dir' for x in changes),'changes':changes,'atime_excluded':'Read access can affect atime; byte hashes and file/directory mtimes are protected.','no_project_writes_executed':True}
save('read-only-audit.json',audit)
reqb=request.read_bytes()
reads=[{'root':'request','path':'REQUEST.md','absolute_path':str(request),'sha256':hashlib.sha256(reqb).hexdigest(),'bytes':len(reqb),'access':'text read'}]
text_read={'PROJECT.md','resume.py','research/state.json','research/checkpoints/C-final.json','provenance/initial/BRIEF.md','provenance/initial/constraints.json','provenance/initial/obligations.json','provenance/initial/source-identities.json','provenance/stage-C/AUTHOR-REVISION.md','notes/parameters.json','notes/rejected-parameters.json','notes/source-check.md','notes/unregistered-scratch.md','results/result.json','results/table.csv','results/summary.md','scripts/compute.py','validation/stage-C.json','validation/stage-C-intermediate-interpretation.json','validation/stage-C-recompute-verification.json','.history/A-initial/files/notes/parameters.json','.history/A-initial/files/results/result.json','.history/A-initial/files/results/summary.md','.history/C-drift/checkpoint.json','update-state.py','validation/stage-C-intermediate-resume.stdout','validation/stage-C-final-resume.stdout','validation/stage-A.json','.history/metadata/revision-1.json','.history/metadata/revision-2.json','.history/metadata/revision-3.json','provenance/stage-C/approved-parameters.json'}
for kind,root in [('project',p),('input',i)]:
 for x in after[kind]:
  if x['type']=='file':reads.append({'root':kind,'path':x['path'],'absolute_path':str(root/x['path']),'sha256':x['sha256'],'bytes':x['bytes'],'access':'full-byte hash plus text or structured inspection' if kind=='input' or x['path'] in text_read else 'full-byte hash only'})
commands=[{'tool_call':1,'argv':['cat',str(request)],'cwd':cwd,'exit_code':0,'purpose':'Read only current stage request'}, {'tool_call':2,'argv':['cat',str(i/'PROTOCOL.md'),str(i/'RECORDING.md'),str(i/'STAGE-D.md')],'cwd':cwd,'exit_code':0,'purpose':'Read current allowed protocols'}]
purposes={3:'Stdin Python: inventory and hash all migrated project/input files, save initial snapshot outside project',4:'Stdin Python: read current state, local scripts, sources identity card, constraints and results; outer output was truncated',5:'Stdin Python: run inspected read-only resume.py, save stdout/stderr and command; inspect prior evidence and historical values',6:'Stdin Python: inspect local guarded writer and historical validation; compare existing result/CSV and checkpoint without recalculation',7:'Stdin Python: write report, state answer and this finalizer to external output',8:'Run external finalizer: final hash/mtime comparison and execution/artifact manifests'}
for n in range(3,9):commands.append({'tool_call':n,'argv':[py,'-I','-B',str(o/'finish.py') if n==8 else '-'],'cwd':cwd,'exit_code':0,'purpose':purposes[n]})
commands.append({'parent_tool_call':5,'argv':[py,'-I','-B','resume.py'],'cwd':str(p),'exit_code':0,'stdout_path':'resume.stdout.json','stderr_path':'resume.stderr.txt'})
outputs=sorted([str(x) for x in o.iterdir() if x.is_file()]+[str(o/'execution.json'),str(o/'inputs-and-artifacts.json')])
execution={'case_id':'T','stage':'D','commands':commands,'tool_calls':8,'tool_call_count_convention':'Eight functions.exec calls, each containing one exec_command; nested read-only resume is separately recorded.','network_calls':0,'agent_calls':0,'violations':[],'failures':[{'tool_call':4,'kind':'tool output truncation','exit_code':0,'remedy':'Tool calls 5 and 6 printed selected omitted state sections and retained structured resume output; original truncation is disclosed.'}],'historical_nonzero_results_not_executed_this_stage':[{'path':'validation/stage-A.json','exit_code':2,'meaning':'Controlled rejection of alpha=1 invalid input, not a scientific failure'},{'path':'validation/stage-C.json','exit_code':1,'meaning':'Intermediate new checkpoint did not revalidate stale calculation/synthesis'}],'read_files':reads,'python_runtime_file_access':'The allowed common Python executable and standard-library runtime were used. OS/interpreter-internal runtime file opens were not traced; input/project full-byte reads are inventoried.','written_paths':sorted(set(outputs)),'read_only_audit':audit,'scientific_calculator_executed':False,'state_or_checkpoint_written':False,'next_action_executed':False,'model':None,'temperature':None,'seed':None,'token_count':None,'token_limit':None,'system_limit':None,'notes':['Command argv/cwd/exit_code are actual; stdin payload purpose is recorded, not represented as a saved script.','All project resources are migrated project files; no original project, toolkit, cache, source tree, personal skills, memory, other phase external answers, network or agent was accessed.','Prior absolute command paths appear solely inside project historical evidence and were not opened.']}
save('execution.json',execution)
artifacts=[]
for f in sorted(o.iterdir()):
 if f.is_file() and f.name!='inputs-and-artifacts.json':
  raw=f.read_bytes();artifacts.append({'path':f.name,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)})
save('inputs-and-artifacts.json',{'case_id':'T','stage':'D','roots':{'project':str(p),'input':str(i),'output':str(o)},'inputs':reads,'outputs':artifacts,'self_manifest_note':'This manifest excludes its own hash to avoid a circular self-reference.','nonredistribution_scope':'Original source PDF bytes remain only inside the migrated private project; no original PDF or other raw source bytes copied into output. Only identity metadata and derived project values are reported.','scientific_access_scope':'PDF full-byte identity hashing only in this stage; no theorem/page audit. All other hash-only records are marked.','project_changed':bool(changes)})
report=(o/'report.md').read_text()
assert len(report)<=10000
assert not changes
assert json.loads((o/'resume.stdout.json').read_text())['checkpoint_freshness']['fresh']
print(json.dumps({'report_characters':len(report),'project_changes':len(changes),'input_project_reads':len(reads),'output_files':len(artifacts)+1,'report':str(o/'report.md')},ensure_ascii=False))
