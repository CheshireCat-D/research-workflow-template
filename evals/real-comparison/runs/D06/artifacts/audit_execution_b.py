"""Finalize the execution record and artifact integrity checks for this completed run."""
import csv
import hashlib
import json
from pathlib import Path
import sys
import sysconfig
w=Path('WORKSPACE')
b=Path('STUDY_ROOT/runs/D06')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
readings=[]
def record(p,name):
    assert p.is_file(),p
    readings.append({'logical_name':name,'sha256':sha(p)})
    return p
# The request and template were supplied with this run, outside its input subfolder.
record(b/'EXECUTOR.md','common/EXECUTOR.md')
template=json.loads(record(b/'execution.template.json','common/execution.template.json').read_text())
for p in sorted((b/'input').rglob('*')):
    if p.is_file():record(p,'input/data-b/'+str(p.relative_to(b/'input')))
# Every file archived from the original root was read while preserving its old bytes.
for p in sorted((w/'stage_a_snapshot').iterdir()):
    if p.is_file():record(p,'workspace/stage_a_snapshot/'+p.name)
for name in ['analysis.py','verify.py','model.json','results.json','report.md','handoff.md','RUN.md','stage_b.py','verify_b.py','publish_b.py','audit_execution_b.py','stage_b_run.log','stage_b_verify.log']:
    record(w/name,'workspace/'+name)
for p in sorted((w/'stage_b_results').iterdir()):
    if p.is_file():record(p,'workspace/stage_b_results/'+p.name)
record(Path(sys.executable),'common/python')
# Hash the explicitly imported runtime modules where a backing source or extension exists.
stdlib=Path(sysconfig.get_path('stdlib'))
for rel in ['argparse.py','collections/__init__.py','csv.py','datetime.py','hashlib.py','json/__init__.py','math.cpython-312-darwin.so','pathlib.py','random.py','runpy.py','sysconfig.py','fractions.py']:
    path=stdlib/rel
    if path.is_file():record(path,'common/stdlib/'+rel)
model_sha='84c6c80033718b1c0b7c0333d90ebe66c0978fd305b44d65ffd5ca9fd6f19a47'
assert sha(w/'model.json')==sha(w/'stage_a_snapshot/model.json')==model_sha
assert sha(w/'results.json')==sha(w/'stage_a_snapshot/results.json')
assert sha(w/'analysis.py')==sha(w/'stage_a_snapshot/analysis.py')
report=(w/'report.md').read_text();assert len(report)<=12000
assert '7.9667%' in report and '9.9674%' in report and '11.5896%' in report
assert '2012-10-29有1行' in report and '2012-10-30有11行' in report
result=json.loads((w/'stage_b_results/results.json').read_text())
verification=json.loads((w/'stage_b_results/verification.json').read_text())
prov=json.loads((w/'stage_b_results/score_provenance.json').read_text())
assert verification['status']=='passed' and verification['bootstrap_expanded_hour_replicates_checked']==4000
assert prov['trained'] is False and prov['model_sha256_after']==model_sha
assert result['overall']['n_hours']==8734
with (w/'stage_b_results/comparison_metrics.csv').open(newline='') as f:assert len(list(csv.DictReader(f)))==16
P='EVAL_PYTHON -I -B '
base=str(w)
maincmd=P+base+'/stage_b.py --input-dir '+str(b/'input')+' --prior-dir '+base+'/stage_a_snapshot --model '+base+'/model.json --output-dir '+base+'/stage_b_results > '+base+'/stage_b_run.log'
verifycmd=P+base+'/verify_b.py --result-dir '+base+'/stage_b_results --model '+base+'/model.json > '+base+'/stage_b_verify.log'
publishcmd=P+base+'/publish_b.py --workspace '+base+' --result-dir '+base+'/stage_b_results'
commands=[
 {'call':1,'operation':'read','command':'cat '+str(b/'EXECUTOR.md')+' '+str(b/'execution.template.json')+' '+str(b/'input/TASK.md'),'exit_code':0},
 {'call':2,'operation':'inventory','command':'ls workspace; find INPUT -maxdepth 3 -type f; find WORKSPACE -maxdepth 3 -type f','exit_code':0},
 {'call':3,'operation':'read','command':'cat workspace/{handoff.md,RUN.md,model.json,results.json} input/data-b/{INPUT_MANIFEST.json,SOURCES.md,UCI_PAGE_EXCERPT.txt,ORIGINAL_README.txt}','exit_code':0},
 {'call':4,'operation':'read','command':'cat workspace/{analysis.py,verify.py,report.md}','exit_code':0},
 {'call':5,'operation':'preserve-write-run','command':'mkdir stage_a_snapshot; cp original root artifacts to stage_a_snapshot; write stage_b.py by heredoc; '+maincmd,'exit_code':0},
 {'call':6,'operation':'read','command':'cat workspace/stage_b_results/{data_audit.json,annual_growth.json,results.json,score_provenance.json}','exit_code':0},
 {'call':7,'operation':'write-run','command':'write verify_b.py by heredoc; '+verifycmd,'execution_session':38201,'exit_code':0},
 {'call':8,'operation':'await-completion','command':'write_stdin(session_id=38201, chars="")','exit_code':0},
 {'call':9,'operation':'write-run','command':'write publish_b.py by heredoc; '+publishcmd,'exit_code':0},
 {'call':10,'operation':'write-validate-record','command':'write audit_execution_b.py by heredoc; '+P+base+'/audit_execution_b.py','exit_code':0}
]
template.update({'status':'executed','trial_id':'D06','phase':'B','tool_calls':10,'network_calls':0,
 'violations':[],'reads':readings,'commands':commands,'duration_seconds':None,
 'scope':'instruction-only; no OS audit','failure':None,
 'checks':{'report_characters':len(report),'model_unchanged':True,'original_results_preserved':True,
 'training_verified_sum_n_mean_cells':72,'new_prediction_rows':8734,'bootstrap_expanded_replicates_verified':4000,
 'verification_status':'passed','scientific_seed':20261029,'scientific_bootstrap_B':2000},
 'notes':['No model or reasoning-effort override requested; effective host model/effort not reported, kept null.',
          'duration_seconds unavailable for the full outer-tool run, kept null.',
          'Command descriptions abbreviate heredoc bodies; exact created code is retained and hashed.',
          'No stage-A chats, other trials, organizer design/answers, memory, skills, network, installs or agent messaging were used.']})
(w/'execution.json').write_text(json.dumps(template,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':'executed','report_characters':len(report),'tool_calls':10,'read_hash_records':len(readings),
 'model_sha256':model_sha,'report':str(w/'report.md'),'execution':str(w/'execution.json')},ensure_ascii=False,indent=2))
