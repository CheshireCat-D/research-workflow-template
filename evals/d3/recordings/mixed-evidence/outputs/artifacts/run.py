#!/usr/bin/env python3
"""Offline stdlib audit of the supplied synthetic aggregates; no fitted model."""
import csv, datetime, hashlib, json, platform, sys, time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
START=time.perf_counter()
FAILURES=[]
def save(path,obj):
    (ROOT/path).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def rate(n,d):
    if d<=0: raise ValueError('nonpositive denominator')
    return {'numerator':n,'denominator':d,'proportion':n/d,'percent':100*n/d}
def require(test,message):
    if not test: raise ValueError(message)

save('artifacts/environment.json',{'python':sys.version,'implementation':platform.python_implementation(),'platform':platform.platform(),'machine':platform.machine(),'packages':'standard library only','started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'command':'python3 PROJECT/artifacts/run.py','network':'not used'})
try:
    config=json.loads((ROOT/'artifacts/config.json').read_text())
    files=['inputs/task.md','inputs/design-and-draft.md','inputs/interviews.md','inputs/quantitative.csv','artifacts/config.json','artifacts/run.py']
    fingerprints={f:{'sha256':hashlib.sha256((ROOT/f).read_bytes()).hexdigest(),'bytes':(ROOT/f).stat().st_size} for f in files}
    save('artifacts/input-fingerprints.json',fingerprints)
    with (ROOT/'inputs/quantitative.csv').open(newline='') as f: rows=list(csv.DictReader(f))
    require(len(rows)==4,'Expected four supplied aggregate rows')
    lookup={}
    for r in rows:
        key=(r['source_id'],r['group'])
        require(key not in lookup,'Duplicate source/group')
        r['n']=int(r['n']);r['event_count']=int(r['event_count'])
        require(0<=r['event_count']<=r['n'],'Invalid count')
        lookup[key]=r
    pos=lookup[('P1','label-positive')];neg=lookup[('P1','label-negative')]
    require(all(r['site']=='A' and r['period']=='2023-retrospective' and r['unit']=='subject' and r['meaning']=='classifier-predicted-positive' for r in [pos,neg]),'P1 identity mismatch')
    tp=pos['event_count'];fn=pos['n']-tp;fp=neg['event_count'];tn=neg['n']-fp
    pre=lookup[('P2','pre')];post=lookup[('P2','post')]
    require(pre['n']==post['n']==config['pilot']['volunteers'],'Same volunteer denominator mismatch')
    require(all(r['site']=='B' and r['period']=='2024-two-week-pilot' and r['unit']=='volunteer' and r['meaning']=='completed-process' for r in [pre,post]),'P2 identity mismatch')
    n=pre['n'];a=pre['event_count'];b=post['event_count']
    # All feasible paired tables; the source does not say which occurred.
    tables=[{'completed_both':x,'pre_only':a-x,'post_only':b-x,'neither':n-a-b+x} for x in range(max(0,a+b-n),min(a,b)+1)]
    result={'scope':'Supplied synthetic aggregates only; classification and process completion are distinct outcomes','prediction':{'source':'inputs/quantitative.csv:2-3; inputs/design-and-draft.md Q1','site':pos['site'],'period':pos['period'],'n':pos['n']+neg['n'],'unit':pos['unit'],'design':'retrospective fixed-classifier agreement with existing labels; training/development independence unknown','matrix_orientation':{'rows':['true positive label','true negative label'],'columns':['predicted positive','predicted negative']},'confusion_matrix':[[tp,fn],[fp,tn]],'counts':{'TP':tp,'FN':fn,'FP':fp,'TN':tn},'sensitivity':rate(tp,tp+fn),'specificity':rate(tn,tn+fp),'positive_predictive_value':rate(tp,tp+fp),'accuracy':rate(tp+tn,tp+fn+fp+tn),'unassessed':['calibration','training/validation separation and leakage','external performance','downstream workflow benefit']},'pilot':{'source':'inputs/quantitative.csv:4-5; inputs/design-and-draft.md Q2','site':pre['site'],'period':pre['period'],'unit':pre['unit'],'design':'same eight volunteers, pre/post aggregate; tool and reminder calls bundled; no randomized or concurrent control','pre':rate(a,n),'post':rate(b,n),'difference':{'numerator_change':b-a,'denominator':n,'proportion_difference':b/n-a/n,'percentage_point_difference':100*(b-a)/n},'uptake':rate(n,config['pilot']['eligible_contactable']),'nonparticipants':{'count':config['pilot']['eligible_contactable']-n,'outcome':'not collected; neither zero nor excluded from recruitment account'},'compatible_paired_tables_not_observed':tables,'paired_transition_status':'not identifiable from marginal counts','causal_effect':'not identified'},'failures':[]}
    elapsed=time.perf_counter()-START
    require(elapsed<config['runtime_limit_seconds'],'Runtime budget exceeded')
    result['elapsed_seconds']=elapsed
    save('artifacts/results.json',result)
    print(json.dumps(result,ensure_ascii=False,indent=2))
except Exception as exc:
    FAILURES.append({'type':type(exc).__name__,'message':str(exc)})
    print(json.dumps({'failures':FAILURES},ensure_ascii=False),file=sys.stderr)
    raise
finally:
    save('artifacts/failures.json',{'failures':FAILURES,'elapsed_seconds':time.perf_counter()-START})
