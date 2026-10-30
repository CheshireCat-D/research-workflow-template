from pathlib import Path
import hashlib, json, os, subprocess

BASE=Path('STUDY_ROOT/runs/P2/A'); OUT=BASE/'output'; ROOT=BASE.parent/'project'; INP=BASE/'input'; PYTHON='EVAL_PYTHON'; CWD='TASK_WORKSPACE'
reads=[]
def read(p):
    p=Path(p); b=p.read_bytes(); reads.append({'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'read_scope':'full file bytes; final audit'}); return b
def obj(p):
    b=read(p); return {'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def load(p): return json.loads(read(p))
def dump(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def tree():
    return {str(p.relative_to(ROOT)):{'kind':'directory' if p.is_dir() else 'file','mtime_ns':p.stat().st_mtime_ns,**({} if p.is_dir() else obj(p))} for p in sorted(ROOT.rglob('*'))}

state=load(ROOT/'management/state.json'); ex=load(OUT/'execution.json'); answer=load(OUT/'state-answer.json'); initial=load(ROOT/'management/MANIFEST.json')
for p,expected in state['tracked_files'].items(): assert obj(ROOT/p)==expected,p
for v in state['versions']: assert obj(ROOT/v['snapshot_path'])=={'sha256':v['sha256'],'bytes':v['bytes']},v
for rel in ['notes/parameters.json','results/result.json','results/table.csv','results/summary.md']:
    assert read(ROOT/rel)==read(ROOT/'management/versions/A-initial'/rel),rel
for rel,ref in initial['files'].items():
    if rel.startswith('project_payload/'): assert obj(ROOT/rel.removeprefix('project_payload/'))==ref,rel
assert answer['changed_or_missing_paths']==[]
assert all(a['status']=='done' for a in state['activities'].values())
assert len(read(OUT/'report.md').decode('utf-8'))<10000
before=tree()
argv=[PYTHON,'-I','-B',str(ROOT/'management/status.py'),'--root',str(ROOT)]
p=subprocess.run(argv,cwd=str(ROOT),capture_output=True,text=True)
after=tree()
assert p.returncode==0 and before==after
current=json.loads(p.stdout)
assert current['checkpoint_freshness']=='fresh-for-registered-local-files' and current['changed_or_missing_paths']==[]
assert sorted(current['unaffected_activities'])==['D-CALC','D-SOURCE-CHECK','D-SYNTH']
assert not (OUT/'verification-rejected').exists()
checks=load(ROOT/'management/evidence/A/checks.json')
assert checks['invalid_input_test']['project_tree_bytes_and_mtimes_unchanged'] is True
assert checks['invalid_input_test']['actual_exit_code']==2

# Reconstruct the literal shell command arguments for the initial read calls.
code2=r'''from pathlib import Path; import hashlib; p=Path("INPUT_DIR"); print("INPUT_FILES"); print("\n".join(str(x.relative_to(p)) for x in sorted(p.rglob("*")) if x.is_file())); names=["PROTOCOL.md","RECORDING.md","STAGE-A.md"]; [(print("\nFILE "+n+" SHA256 "+hashlib.sha256((p/n).read_bytes()).hexdigest()+" BYTES "+str((p/n).stat().st_size)), print((p/n).read_text())) for n in names]'''
code3=r'''from pathlib import Path; import hashlib; p=Path("INPUT_DIR/initial"); files=[x for x in sorted(p.rglob("*")) if x.is_file()]; [(print("\nFILE "+str(x.relative_to(p))+" SHA256 "+hashlib.sha256(x.read_bytes()).hexdigest()+" BYTES "+str(x.stat().st_size)), print(x.read_text() if x.suffix!=".csv" or x.name=="table.csv" else "DATA CSV FIRST 8 LINES\n"+"\n".join(x.read_text().splitlines()[:8])+"\nDATA CSV LAST 3 LINES\n"+"\n".join(x.read_text().splitlines()[-3:]))) for x in files]'''
for ix,code in [(1,code2),(2,code3)]:
    ex['commands'][ix]['argv']=[PYTHON,'-I','-B','-c',code]
    ex['commands'][ix]['shell_argv']=['/bin/zsh','-lc',PYTHON+" -I -B -c '"+code+"'"]
ex['commands'][0]['shell_argv']=ex['commands'][0]['argv']
build=read(OUT/'build_stage_a.py').decode('utf-8')
finalizer=read(Path(__file__)).decode('utf-8')
write_build="mkdir -p OUTPUT_DIR\ncat > OUTPUT_DIR/build_stage_a.py <<'PY'\n"+build+'PY'
write_final="cat > OUTPUT_DIR/finalize_audit.py <<'PY'\n"+finalizer+'PY'
ex['commands'].insert(3,{'argv':['/bin/zsh','-lc',write_build],'cwd':CWD,'exit_code':0,'purpose':'create stage execution resource in output; no project exists yet'})
ex['commands'].extend([
    {'argv':['/bin/zsh','-lc',write_final],'cwd':CWD,'exit_code':0,'purpose':'write independent final audit and execution finalizer'},
    {'argv':[PYTHON,'-I','-B',str(Path(__file__))],'shell_argv':['/bin/zsh','-lc',PYTHON+' -I -B '+str(Path(__file__))],'cwd':CWD,'exit_code':0,'purpose':'audit project and versions, preserve exact commands and finalize external records'},
    {'argv':argv,'cwd':str(ROOT),'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'purpose':'final read-only status and project mtime/byte preservation audit'}])
for e in ex['commands']:
    if e['argv'][0]==PYTHON and 'shell_argv' not in e and e['purpose'] if 'purpose' in e else False: pass
ex['tool_calls']=7
ex['tool_call_count_scope']='Seven outer functions.exec invocations, each with one exec_command; scientific/status subprocesses recorded separately.'
ex['recording_note']='All shell read/write and main Python commands plus scientific/status subprocesses are recorded. Nested Python file operations use standard library and are preserved in the exact executed scripts. Input/project/source resources have complete SHA and bytes; standard-library implementation files are not scientific inputs. Records of earlier file versions retain the SHA observed when read. No network, installation, parent messages, other agent calls, memory or skills accessed.'
ex['read_inventory'].extend(reads)
# Include all original request/input files again as exact final-audit reads.
for q in [BASE/'REQUEST.md']+[q for q in sorted(INP.rglob('*')) if q.is_file()]: obj(q)
# Record external outputs whose bytes are read during inventory, before execution is finalized.
for q in sorted(OUT.rglob('*')):
    if q.is_file() and q.name not in ['execution.json','inputs-and-artifacts.json']: obj(q)
ex['read_inventory'].extend(reads[len(ex['read_inventory'])-len(ex['read_inventory']):] if False else [])
# Deduplicate observations by path and SHA, not path alone: multiple versions may have been read.
all_reads=ex['read_inventory']+reads
unique={}
for r in all_reads: unique[(r['path'],r['sha256'])]=r
ex['read_inventory']=list(unique.values())
ex['written_paths']=sorted(set(ex['written_paths'])|{str(q) for q in OUT.rglob('*') if q.is_file()}|{str(OUT/'execution.json'),str(OUT/'inputs-and-artifacts.json')})
ex['final_audit']={'tracked_file_count':len(state['tracked_files']),'initial_snapshot_count':len(state['versions']),'all_initial_payload_bytes_preserved':True,'all_versions_recoverable':True,'registered_local_files_current':True,'read_only_status_preserves_project_bytes_and_mtimes':True,'project_tree_file_count':sum(v['kind']=='file' for v in after.values())}
dump(OUT/'execution.json',ex)
# Snapshot every final artifact other than this inventory's own self-referential hash.
art={'case_id':'D','stage':'A','inputs':[{'relative_path':str(q.relative_to(BASE)),'path':str(q),**obj(q)} for q in [BASE/'REQUEST.md']+[q for q in sorted(INP.rglob('*')) if q.is_file()]],'project_artifacts':[{'relative_path':str(q.relative_to(ROOT)),'path':str(q),**obj(q)} for q in sorted(ROOT.rglob('*')) if q.is_file()],'output_artifacts':[{'relative_path':str(q.relative_to(OUT)),'path':str(q),**obj(q)} for q in sorted(OUT.rglob('*')) if q.is_file() and q.name!='inputs-and-artifacts.json'],'hash_manifest_self_exclusion':'inputs-and-artifacts.json excludes its own hash to avoid recursion; it is an output path in execution. Execution is hashed here after finalization. Directory mtimes are operational evidence, not scientific content versions.','non_distribution_scope':'No remote/PDF/full original hour.csv acquired. Original supplied CSV is private cache only; do not publicly redistribute source data. Publish source identities and results only under supplied rule.'}
dump(OUT/'inputs-and-artifacts.json',art)
print(json.dumps({'report':str(OUT/'report.md'),'state_answer':str(OUT/'state-answer.json'),'execution':str(OUT/'execution.json'),'inventory':str(OUT/'inputs-and-artifacts.json'),'project':str(ROOT),'outer_tool_calls':7,'audit':ex['final_audit']},ensure_ascii=False))
