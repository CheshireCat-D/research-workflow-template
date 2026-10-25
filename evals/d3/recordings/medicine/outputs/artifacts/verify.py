#!/usr/bin/env python3
"""Independent Decimal arithmetic and bit-mask reallocation, then reproducibility check."""
from pathlib import Path
from decimal import Decimal as D
import csv,hashlib,json,subprocess,sys,time
R=Path(__file__).resolve().parents[1]
start=time.perf_counter()
a=list(csv.DictReader((R/'inputs/allocation.csv').open()))
x=list(csv.DictReader((R/'inputs/participants.csv').open()))
old=json.loads((R/'artifacts/results.json').read_text())
checks=[]
for endpoint,expected,pval in [('burden_day30',D('0.5'),D('0.75')),('burden_day7',D('-2'),D('0.125'))]:
    means={s['clinic_id']:sum((D(r[endpoint]) for r in x if r['clinic_id']==s['clinic_id']),D(0))/D(s['enrolled_n']) for s in a}
    ds=[]
    for pair in sorted({s['pair_id'] for s in a}):
        z={s['arm']:means[s['clinic_id']] for s in a if s['pair_id']==pair}
        ds.append(z['program']-z['control'])
    effect=sum(ds)/4
    stats=[sum((1 if mask&(1<<i) else -1)*v for i,v in enumerate(ds))/4 for mask in range(16)]
    pv=D(sum(abs(s)>=abs(effect) for s in stats))/16
    assert effect==expected and pv==pval
    rr=old['endpoints'][endpoint]
    assert D(str(rr['effect']))==effect and D(str(rr['randomization']['p_value']))==pv
    checks.append({'endpoint':endpoint,'decimal_effect':str(effect),'decimal_exact_p':str(pv),'passed':True})
p=subprocess.run([sys.executable,'artifacts/run.py'],cwd=R,capture_output=True,text=True)
assert p.returncode==0,p.stderr
new=json.loads((R/'artifacts/results.json').read_text())
old.pop('elapsed_seconds');new.pop('elapsed_seconds')
assert old==new,'numeric/configuration/input results changed on rerun'
for name,key in [('sites.csv','site_results'),('pairs.csv','pair_results')]:
    rr=list(csv.DictReader((R/'artifacts'/name).open()))
    assert len(rr)==len(new[key])
result={'passed':True,'checks':checks,'deterministic_results_equal_excluding_elapsed':True,'rerun':{'command':[sys.executable,'artifacts/run.py'],'cwd':'.','exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr},'elapsed_seconds':time.perf_counter()-start,'scope':'arithmetic, legal paired allocation enumeration and repeatability only; no clinical validation'}
(R/'checks/analysis-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False))
