"""Independent row-expanded verification of frozen scoring and all bootstrap draws."""
import argparse
import collections
import csv
import hashlib
import json
import math
from pathlib import Path
import random
import sys
p=argparse.ArgumentParser();p.add_argument('--result-dir',type=Path,required=True);p.add_argument('--model',type=Path,required=True)
a=p.parse_args();out=a.result_dir
model=json.loads(a.model.read_text());result=json.loads((out/'results.json').read_text())
with (out/'predictions.csv').open(newline='') as f:preds=list(csv.DictReader(f))
assert len(preds)==8734
bydate=collections.defaultdict(list)
for q in preds:
    bydate[q['date']].append(q)
    assert float(q['C0'])==model['C0'][q['hr']]['mean']
    assert float(q['C1'])==model['C1'][q['workingday']+','+q['hr']]['mean']
dates=sorted(bydate);assert len(dates)==366
max_delta=0.;max_relative=0.
for L in [7,28]:
    with (out/f'bootstrap_L{L}.csv').open(newline='') as f:recorded=list(csv.DictReader(f))
    assert len(recorded)==2000
    rng=random.Random(20261029);deltas=[];rels=[]
    for record in recorded:
        indexes=[]
        for _ in range(math.ceil(len(dates)/L)):
            start=rng.randrange(len(dates))
            indexes.extend((start+j)%len(dates) for j in range(L))
        selected=[q for i in indexes[:len(dates)] for q in bydate[dates[i]]]
        n=len(selected);assert n==int(record['n_sampled_hours'])
        m0=sum(abs(float(q['C0'])-int(q['actual'])) for q in selected)/n
        m1=sum(abs(float(q['C1'])-int(q['actual'])) for q in selected)/n
        delta=m0-m1;rel=1-m1/m0
        max_delta=max(max_delta,abs(delta-float(record['absolute_improvement'])))
        max_relative=max(max_relative,abs(rel-float(record['relative_improvement'])))
        assert math.isclose(delta,float(record['absolute_improvement']),abs_tol=1e-9)
        assert math.isclose(rel,float(record['relative_improvement']),abs_tol=1e-11)
        deltas.append(delta);rels.append(rel)
    for values,key in [(deltas,'absolute_improvement_95ci'),(rels,'relative_improvement_95ci')]:
        values.sort()
        for i,pct in enumerate([.025,.975]):
            pos=(len(values)-1)*pct;lo=math.floor(pos);hi=math.ceil(pos)
            q=values[lo]+(pos-lo)*(values[hi]-values[lo])
            assert math.isclose(q,result['bootstrap'][str(L)][key][i],abs_tol=1e-9)
v={'status':'passed','prediction_rows':len(preds),'bootstrap_expanded_hour_replicates_checked':4000,
   'max_absolute_delta_discrepancy':max_delta,'max_relative_discrepancy':max_relative,
   'model_sha256':hashlib.sha256(a.model.read_bytes()).hexdigest(),'python_version':sys.version}
(out/'verification.json').write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(v,ensure_ascii=False,indent=2))
