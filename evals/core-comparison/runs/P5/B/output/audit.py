from pathlib import Path
import hashlib, json, subprocess, sys
ROOT=Path('PROJECT_ROOT')
OUT=Path('OUTPUT_DIR')
INPUT=Path('INPUT_DIR')
PYTHON='EVAL_PYTHON'
def identity(path):
    b=path.read_bytes();return {'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def save(name,obj):
    (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def snapshot():
    d={'.':{'kind':'directory','mtime_ns':ROOT.stat().st_mtime_ns}}
    for p in sorted(ROOT.rglob('*')):
        r=str(p.relative_to(ROOT));d[r]={'kind':'directory' if p.is_dir() else 'file','mtime_ns':p.stat().st_mtime_ns}
        if p.is_file():d[r].update(identity(p))
    return d
before=snapshot();save('project-before.json',before)
state=json.loads((ROOT/'.research/state.json').read_text())
argv=[PYTHON,'-I','-B',str(ROOT/'scripts/manage.py'),'status']
r=subprocess.run(argv,cwd=ROOT,text=True,capture_output=True)
(OUT/'status.stdout.txt').write_text(r.stdout);(OUT/'status.stderr.txt').write_text(r.stderr)
save('status-execution.json',{'argv':argv,'cwd':str(ROOT),'exit_code':r.returncode,'stdout_path':'status.stdout.txt','stderr_path':'status.stderr.txt'})
if r.returncode:raise RuntimeError('Read-only project status failed')
status=json.loads(r.stdout);save('current-status.json',status)
old=json.loads((ROOT/'.research/versions/A-initial/notes/parameters.json').read_text())
current=json.loads((ROOT/'notes/parameters.json').read_text())
result=json.loads((ROOT/'results/result.json').read_text())
summary=(ROOT/'results/summary.md').read_text()
import csv,io
rows=list(csv.DictReader(io.StringIO((ROOT/'results/table.csv').read_text())))
checks={
 'authoritative_state':'.research/state.json','revision':state['revision'],
 'parameter_diff':{k:{'registered_initial':old.get(k),'working_current':current.get(k)} for k in sorted(set(old)|set(current)) if old.get(k)!=current.get(k)},
 'current_parameter_identity':identity(ROOT/'notes/parameters.json'),
 'registered_parameter_identity':state['tracked_materials']['notes/parameters.json'],
 'old_content_identity_matches_registered':identity(ROOT/'.research/versions/A-initial/notes/parameters.json')==state['tracked_materials']['notes/parameters.json'],
 'result_parameters':{k:result[k] for k in ['alpha','rho','rho_selection']},
 'result_parameter_sha256':result['input_sha256']['parameters'],
 'result_still_binds_initial_parameter':result['input_sha256']['parameters']==state['tracked_materials']['notes/parameters.json']['sha256'],
 'result_binds_current_parameter':result['input_sha256']['parameters']==identity(ROOT/'notes/parameters.json')['sha256'],
 'table_agrees_with_old_result':[(float(x['v']),float(x['boundary'])) for x in rows]==[(float(x['v']),float(x['boundary'])) for x in result['values']],
 'summary_states_initial_rho':'rho=1' in summary,
 'source_sha_matches_registered':identity(ROOT/'sources/howard2021-arxiv-v9.pdf')==state['tracked_materials']['sources/howard2021-arxiv-v9.pdf'],
 'all_registered_present':all((ROOT/p).is_file() for p in state['tracked_materials']),
 'checkpoint_id':state['checkpoint']['id'],
 'status_result':status,
 'scientific_calculator_run_this_stage':False,
 'restoration_or_rebinding_this_stage':False
}
checks['preserved_initial_files_match']={p:identity(ROOT/v['content_path'])=={'sha256':v['sha256'],'bytes':v['bytes']} for p,v in state['versions'].items()}
save('audit-checks.json',checks)
after=snapshot();save('project-after.json',after)
unchanged=before==after
save('readonly-verification.json',{'project_bytes_file_mtimes_directory_mtimes_unchanged':unchanged,'before':'project-before.json','after':'project-after.json','scope':'Full tree before/after read-only status and audit. Earlier inventory commands only read files.'})
if not unchanged:raise RuntimeError('Project changed during read-only audit')
inputs=[]
request=INPUT.parent/'REQUEST.md'
for base,label in [(ROOT,'project'),(INPUT,'input')]:
    for p in sorted(base.rglob('*')):
        if p.is_file():inputs.append({'scope':label,'relative_path':str(p.relative_to(base)),**identity(p),'read_scope':'Full bytes for identity; text files inspected; PDF only hashed, no text/page review.'})
inputs.append({'scope':'request','relative_path':'REQUEST.md',**identity(request),'read_scope':'Full text'})
inputs.append({'scope':'runtime','relative_path':str(Path(__file__)),**identity(Path(__file__)),'read_scope':'Self-authored audit program executed'})
save('read-inputs.json',inputs)
print(json.dumps({'status_exit_code':r.returncode,'changed_paths':status['changed_paths'],'missing_paths':status['missing_paths'],'activities':status['activities'],'checkpoint':status['checkpoint_freshness'],'project_unchanged':unchanged,'parameter_diff':checks['parameter_diff']},ensure_ascii=False,indent=2))
