#!/usr/bin/env python3
"""Rebuild site-weighted paired contrasts and exact paired randomization inference.
Run from PROJECT: python3 artifacts/run.py
Standard library only; deterministic complete enumeration, no RNG seed needed.
"""
from pathlib import Path
import csv, hashlib, itertools, json, sys, time
from fractions import Fraction as F

ROOT=Path(__file__).resolve().parents[1]
def mean(v): return sum(v,F(0))/len(v)
def exact_randomization(d):
    observed=mean(d)
    dist=[]
    for signs in itertools.product((-1,1),repeat=len(d)):
        statistic=mean([s*x for s,x in zip(signs,d)])
        dist.append({'pair_signs':list(signs),'statistic':float(statistic),'statistic_exact':str(statistic),
                     'at_least_as_extreme':abs(statistic)>=abs(observed)})
    extreme=sum(x['at_least_as_extreme'] for x in dist)
    return {'null':'sharp null: no program effect at any site/participant',
            'statistic':'equal mean of program minus control site means across four pairs',
            'alternative':'two-sided, absolute statistic, ties included',
            'assignments':len(dist),'extreme_assignments':extreme,'p_value':extreme/len(dist),
            'p_value_exact':str(F(extreme,len(dist))),
            'minimal_attainable_two_sided_p':2/len(dist),
            'distribution':dist,
            'scope':'design-exact test of the sharp null, not a CI or a test of weak zero average effect under arbitrary heterogeneity'}
def main():
    start=time.perf_counter()
    with (ROOT/'inputs/allocation.csv').open(newline='') as f: alloc=list(csv.DictReader(f))
    with (ROOT/'inputs/participants.csv').open(newline='') as f: rows=list(csv.DictReader(f))
    assert len(alloc)==8 and len(rows)==64, 'unexpected analysis set'
    assert len({r['clinic_id'] for r in alloc})==len(alloc), 'duplicate site'
    assert len({r['synthetic_id'] for r in rows})==len(rows), 'duplicate participant'
    by_id={a['clinic_id']:a for a in alloc}
    assert all(r['clinic_id'] in by_id for r in rows), 'unknown site'
    sites=[]; raw_site={}
    for a in alloc:
        rr=[r for r in rows if r['clinic_id']==a['clinic_id']]
        assert len(rr)==int(a['enrolled_n']), 'allocation and participant denominator mismatch'
        assert a['arm'] in ('control','program')
        vals={k:[F(r[k]) for r in rr] for k in ('burden_day30','burden_day7')}
        assert all(0<=x<=20 for vv in vals.values() for x in vv), 'missing or out of range'
        raw_site[a['clinic_id']]={k:mean(vv) for k,vv in vals.items()}
        sites.append(dict(a,observed_n=len(rr),day30_sum=float(sum(vals['burden_day30'])),
                          day7_sum=float(sum(vals['burden_day7'])),day30_mean=float(mean(vals['burden_day30'])),
                          day7_mean=float(mean(vals['burden_day7']))))
    pair_rows=[]; contrasts={k:[] for k in ('burden_day30','burden_day7')}
    for pair in sorted({a['pair_id'] for a in alloc}):
        aa=[a for a in alloc if a['pair_id']==pair]
        assert len(aa)==2 and {a['arm'] for a in aa}=={'program','control'}
        program=next(a['clinic_id'] for a in aa if a['arm']=='program')
        control=next(a['clinic_id'] for a in aa if a['arm']=='control')
        d={k:raw_site[program][k]-raw_site[control][k] for k in contrasts}
        for k in contrasts: contrasts[k].append(d[k])
        pair_rows.append({'pair_id':pair,'program_clinic':program,'control_clinic':control,
                          'day30_difference':float(d['burden_day30']),'day7_difference':float(d['burden_day7'])})
    assert len(pair_rows)==4
    endpoints={}
    for k,d in contrasts.items():
        pooled={arm:mean([F(r[k]) for r in rows if by_id[r['clinic_id']]['arm']==arm])
                for arm in ('control','program')}
        equal={arm:mean([raw_site[a['clinic_id']][k] for a in alloc if a['arm']==arm])
               for arm in ('control','program')}
        endpoints[k]={'prespecified':k=='burden_day30','status':'primary' if k=='burden_day30' else 'post-unblinding exploratory; operational monitoring, not prespecified efficacy endpoint',
                      'pair_differences':[float(x) for x in d],'effect':float(mean(d)), 'effect_exact':str(mean(d)),
                      'site_equal_arm_means':{a:float(v) for a,v in equal.items()},
                      'participant_pooled_arm_means':{a:float(v) for a,v in pooled.items()},
                      'participant_pooled_difference':float(pooled['program']-pooled['control']),
                      'randomization':exact_randomization(d)}
    result={'schema_version':'1','configuration':{'input_paths':['inputs/allocation.csv','inputs/participants.csv'],
          'primary_endpoint':'burden_day30','direction':'program minus control; negative favors program',
          'weighting':'sites equal, four pairs equal','allocation':'four independent fair pair-level coins',
          'seed':'not applicable: complete deterministic enumeration of all 16 assignments',
          'adjustment':'none','exclusion':'none','missing_handling':'assert complete; no imputation'},
          'input_sha256':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted((ROOT/'inputs').iterdir())},
          'flow':{'allocated_sites':8,'analyzed_sites':8,'pairs':4,'listed_participants':64,'analyzed_participants':len(rows),
                  'participants_by_arm':{arm:sum(1 for r in rows if by_id[r['clinic_id']]['arm']==arm) for arm in ('program','control')},
                  'missing_outcomes':0,'crossovers':'not independently observable; protocol states none'},
          'site_results':sites,'pair_results':pair_rows,'endpoints':endpoints,
          'failures':[],'elapsed_seconds':time.perf_counter()-start}
    (ROOT/'artifacts/results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    for name,rr in [('sites',sites),('pairs',pair_rows)]:
        with (ROOT/f'artifacts/{name}.csv').open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(rr[0]));w.writeheader();w.writerows(rr)
    print(json.dumps({'day30_effect':endpoints['burden_day30']['effect'],
                      'day30_exact_two_sided_p':endpoints['burden_day30']['randomization']['p_value'],
                      'pooled_day30_difference':endpoints['burden_day30']['participant_pooled_difference'],
                      'day7_exploratory_effect':endpoints['burden_day7']['effect'],
                      'day7_exploratory_two_sided_p':endpoints['burden_day7']['randomization']['p_value'],
                      'elapsed_seconds':result['elapsed_seconds'],'failure_count':0},ensure_ascii=False))
if __name__=='__main__': main()
