#!/usr/bin/env python3
from pathlib import Path
import csv,json,hashlib,shutil,subprocess,sys,time
from decimal import Decimal as D
start=time.perf_counter(); P=Path(__file__).resolve().parents[1]
base=P.parent; scratch=P/'revision-work/v2-recompute'; scratch.mkdir(parents=True,exist_ok=False)
(scratch/'inputs').mkdir();(scratch/'artifacts').mkdir()
for f in (P/'inputs').iterdir(): shutil.copy2(f,scratch/'inputs'/f.name)
shutil.copy2(P/'artifacts/run.py',scratch/'artifacts/run.py')
before=json.loads((P/'artifacts/results.json').read_text())
a={r['clinic_id']:r for r in csv.DictReader((P/'inputs/allocation.csv').open())}
x=list(csv.DictReader((P/'inputs/participants.csv').open()))
sums={arm:sum((D(r['burden_day7']) for r in x if a[r['clinic_id']]['arm']==arm),D(0)) for arm in ('program','control')}
ns={arm:sum(a[r['clinic_id']]['arm']==arm for r in x) for arm in sums}
means={arm:sums[arm]/ns[arm] for arm in sums};diff=means['program']-means['control']
assert sums=={'program':D('120.0'),'control':D('200.0')}
assert means=={'program':D('3.75'),'control':D('6.25')} and diff==D('-2.50')
recorded=before['endpoints']['burden_day7']
assert all(D(str(recorded['participant_pooled_arm_means'][arm]))==means[arm] for arm in means)
assert D(str(recorded['participant_pooled_difference']))==diff
cmd=[sys.executable,'revision-work/v2-recompute/artifacts/run.py']
p=subprocess.run(cmd,cwd=P,capture_output=True,text=True)
assert p.returncode==0,p.stderr
rerun=json.loads((scratch/'artifacts/results.json').read_text())
old_seconds=before.pop('elapsed_seconds');new_seconds=rerun.pop('elapsed_seconds')
assert before==rerun, 'full original computation differs beyond elapsed time'
active_paths=['notes/analysis.md','manuscript/report.md','review.md']
assert all('3.875' not in (P/f).read_text() and '2.375' not in (P/f).read_text() for f in active_paths)
prior=json.loads((base/'revisions/v1/run-summary.json').read_text())['snapshot_sha256_excluding_this_marker']
unchanged=['artifacts/run.py','artifacts/results.json','artifacts/sites.csv','artifacts/pairs.csv','artifacts/verify.py','checks/analysis-verification.json','manuscript/report.md','notes/issue.md']+[str(f.relative_to(P)) for f in (P/'inputs').iterdir()]
for name in unchanged: assert hashlib.sha256((P/name).read_bytes()).hexdigest()==prior['PROJECT/'+name],name
result={'passed':True,'issue':'v1 notes/analysis.md line25 day7 pooled program mean and contrast transcription inconsistent with already-correct original results.json',
 'day7_pooled_decimal':{'sums':{a:str(v) for a,v in sums.items()},'n':ns,'means':{a:str(v) for a,v in means.items()},'difference':str(diff)},
 'original_results_json_already_correct':True,'isolated_full_script_rerun':{'command':cmd,'cwd':'.','exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'elapsed_seconds':new_seconds,'all_results_equal_excluding_elapsed':True},
 'active_prose_old_values_absent':active_paths,'unchanged_paths_verified_against_v1_marker':unchanged,'elapsed_seconds':time.perf_counter()-start,
 'scope':'transcription correction plus independent raw-record Decimal verification and complete original computation rerun in isolated copy; primary analysis files remain byte-identical'}
(P/'checks/revision-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False))
