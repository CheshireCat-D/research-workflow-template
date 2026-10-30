import hashlib,json,pathlib
W=pathlib.Path(__file__).resolve().parent
I=W.parent/'input'
G=pathlib.Path('GUIDANCE_ROOT')
base=W.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
execution=json.loads((base/'execution.template.json').read_text())
reads=[]
def add(logical,p): reads.append({'logical_name':logical,'sha256':sha(p)})
add('common/executor.md',base/'EXECUTOR.md')
add('common/execution.template.json',base/'execution.template.json')
for rel in ('TASK.md','INPUT_MANIFEST.json','SOURCES.md','ORIGINAL_README.txt','UCI_PAGE_EXCERPT.txt','data/hour_2011.csv','data/day_2011.csv'):
    add('input/data-a/'+rel,I/rel)
for rel in ('skills/rw-workflow/SKILL.md','skills/rw-validation/SKILL.md','core/skill-bridge.md','core/protocol.md','profiles/methods/computational.md','profiles/methods/empirical-quantitative.md','profiles/governance.md','skills/rw-writing/SKILL.md'):
    add('guidance/rwt/'+rel,G/rel)
for rel in ('analyze.py','verify.py','write_delivery.py','results/model.json','results/audit.json','results/results.json','results/predictions.csv','results/daily_errors.csv','results/bootstrap_7.csv','results/bootstrap_28.csv','score_check/results.json','score_check/predictions.csv','score_check/daily_errors.csv','score_check/bootstrap_7.csv','score_check/bootstrap_28.csv'):
    add('workspace/'+rel,W/rel)
P='EVAL_PYTHON'
commands=[
 {'tool_call':1,'command':['cat',str(base/'EXECUTOR.md'),str(base/'execution.template.json')],'exit_code':0},
 {'tool_call':2,'command':['cat',str(I/'TASK.md')]+[str(G/r) for r in ('skills/rw-workflow/SKILL.md','skills/rw-validation/SKILL.md','core/skill-bridge.md','core/protocol.md','profiles/methods/computational.md','profiles/methods/empirical-quantitative.md')],'exit_code':0},
 {'tool_call':3,'command':['find',str(I),'-type','f','-maxdepth','4','-print'],'exit_code':0},
 {'tool_call':4,'command':['cat']+[str(I/r) for r in ('INPUT_MANIFEST.json','SOURCES.md','ORIGINAL_README.txt','UCI_PAGE_EXCERPT.txt')]+[str(G/r) for r in ('profiles/governance.md','skills/rw-writing/SKILL.md')],'exit_code':0},
 {'tool_call':5,'command':[P,'-I','-B',str(W/'analyze.py'),'train','--input-dir',str(I),'--output-dir',str(W/'results')],'exit_code':0,'preceding_writes':['workspace directory via mkdir','analyze.py via shell heredoc']},
 {'tool_call':6,'command':[P,'-I','-B',str(W/'verify.py')],'exit_code':0,'preceding_writes':['verify.py via shell heredoc']},
 {'tool_call':6,'command':[P,'-I','-B',str(W/'analyze.py'),'score','--hour-file',str(I/'data/hour_2011.csv'),'--model',str(W/'results/model.json'),'--start','2011-10-01','--end','2011-12-31','--output-dir',str(W/'score_check')],'exit_code':0},
 {'tool_call':7,'command':[P,'-I','-B',str(W/'write_delivery.py')],'exit_code':0,'preceding_writes':['write_delivery.py via shell heredoc']},
 {'tool_call':8,'command':[P,'-I','-B',str(W/'finalize.py')],'exit_code':0,'preceding_writes':['finalize.py via shell heredoc']}
]
execution.update({'status':'executed','tool_calls':9,'network_calls':0,'violations':[],'reads':reads,'commands':commands,'duration_seconds':None,'failure':None,'scope':'instruction-only; no OS audit','record_notes':['Tool calls count outer orchestration calls, including file creation, calculations and final review.','Requested model/effort overrides absent; effective host configuration not reported, retained null.','Algorithmic random.Random seed 20261029 is distinct from unknown model sampling seed.','No network, installation, 2012 observations, memory, personal skills or other trials accessed.','Plain research directory chosen; no template CLI initialization or registry validity claim.','Last tool call performs final read-only artifact validation.','Exact source for code-writing heredocs is preserved in the corresponding saved script; commands log records calculation argv and write summaries.']})
(W/'execution.json').write_text(json.dumps(execution,ensure_ascii=False,indent=2)+'\n')
artifacts={}
for p in sorted(W.rglob('*')):
    if p.is_file() and p.name not in ('artifact_manifest.json',):
        artifacts[str(p.relative_to(W))]={'sha256':sha(p),'bytes':p.stat().st_size}
(W/'artifact_manifest.json').write_text(json.dumps(artifacts,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'status':execution['status'],'tool_calls':execution['tool_calls'],'recorded_reads':len(reads),'artifacts':len(artifacts),'failures':execution['failure']},ensure_ascii=False))
