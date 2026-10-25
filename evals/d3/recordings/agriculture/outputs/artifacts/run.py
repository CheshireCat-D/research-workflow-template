#!/usr/bin/env python3
"""Offline finite-data analysis. Run from PROJECT: python3 artifacts/run.py.
Uses only stdlib; reads inputs, writes artifacts only. All paths are relative to
this script's project root; no original toolkit or case path is consulted.
"""
from pathlib import Path
import csv, hashlib, itertools, json, math, statistics, time
from collections import Counter, defaultdict
ROOT=Path(__file__).resolve().parents[1]
t0=time.perf_counter()
def readcsv(name):
    with (ROOT/'inputs'/name).open(newline='') as f:return list(csv.DictReader(f))
def writecsv(name,rows):
    with (ROOT/'artifacts'/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
plots=readcsv('plots.csv');plants=readcsv('plants.csv')
assert len(plots)==8 and len(plants)==48
assert len({r['plot_id'] for r in plots})==8
pmap={p['plot_id']:p for p in plots}; grouped=defaultdict(list)
for r in plants:
    assert r['plot_id'] in pmap
    y=float(r['dry_seed_g']);assert math.isfinite(y)
    grouped[r['plot_id']].append((int(r['plant_number']),y))
plotrows=[]
for p in plots:
    vals=grouped[p['plot_id']]
    assert sorted(i for i,y in vals)==list(range(1,7))
    ys=[y for i,y in vals]
    plotrows.append(dict(p,n_plants=len(ys),mean_g=statistics.mean(ys),
                         sum_g=sum(ys),within_plot_sd_g=statistics.stdev(ys)))
blockrows=[]
for block in sorted({p['block_id'] for p in plots}):
    ps=[p for p in plotrows if p['block_id']==block]
    assert len(ps)==2 and {p['side'] for p in ps}=={'L','R'}
    assert {p['treatment'] for p in ps}=={'control','mulch'}
    c=next(p for p in ps if p['treatment']=='control')
    m=next(p for p in ps if p['treatment']=='mulch')
    blockrows.append({'block_id':block,'control_plot':c['plot_id'],
                      'mulch_plot':m['plot_id'],'control_mean_g':c['mean_g'],
                      'mulch_mean_g':m['mean_g'],'difference_g':m['mean_g']-c['mean_g'],
                      'supplementary_irrigation':block=='B4'})
ds=[b['difference_g'] for b in blockrows]; n=len(ds)
effect=statistics.mean(ds);sd=statistics.stdev(ds);se=sd/math.sqrt(n)
control=statistics.mean(b['control_mean_g'] for b in blockrows)
mulch=statistics.mean(b['mulch_mean_g'] for b in blockrows)
# Enumerate the actual 2^4 within-block assignments, under sharp no effect.
perms=[]
for signs in itertools.product((-1,1),repeat=n):
    value=sum(s*d for s,d in zip(signs,ds))/n
    perms.append({'assignment_signs':','.join(map(str,signs)),
                  'mean_difference_g':value,'abs_at_least_observed':abs(value)>=abs(effect)-1e-12})
p2=sum(p['abs_at_least_observed'] for p in perms)/len(perms)
p1=sum(p['mean_difference_g']>=effect-1e-12 for p in perms)/len(perms)
# t_3 reference distribution: analytic CDF, deterministic bisection quantile.
def cdf_t3(x):
    u=x/math.sqrt(3)
    return .5+(math.atan(u)+u/(1+u*u))/math.pi
lo,hi=0.,20.
for _ in range(80):
    mid=(lo+hi)/2
    if cdf_t3(mid)<.975:lo=mid
    else:hi=mid
crit=(lo+hi)/2
# A deliberately invalid comparator: treat six matched plant numbers per block
# as six independently randomized pairs. It repeats each block treatment effect
# six times. Those plants were not assigned independently.
pseudo=[d for d in ds for _ in range(6)]
naive_pseudo_se=statistics.stdev(pseudo)/math.sqrt(len(pseudo))
# There are 12 positive pair differences and 12 ties. The hypothetical independent
# sign-flip null puts both extreme sums at probability 2/2^12, but is not the design.
nonzero=sum(abs(d)>1e-12 for d in pseudo)
wrong_p=2/(2**nonzero)
# Ignore blocks entirely: reported only to explain why invalid row-level analyses
# can also become less precise when they discard the strong matching structure.
plant_groups=defaultdict(list)
for r in plants:plant_groups[pmap[r['plot_id']]['treatment']].append(float(r['dry_seed_g']))
naive_se=math.sqrt(sum(statistics.variance(v)/len(v) for v in plant_groups.values()))
first3=ds[:3]
first3_perm=[sum(s*d for s,d in zip(signs,first3))/3 for signs in itertools.product((-1,1),repeat=3)]
first3_effect=statistics.mean(first3)
results={
 'data_origin':'Original synthetic offline task inputs; not field-collected evidence',
 'design':{'site_seasons':1,'blocks':n,'plots':len(plots),'plants':len(plants),
           'assignment':'Independent fair within-block L/R flip; one mulch plot and one control',
           'randomization_unit':'plot','inference_replicates':'4 block contrasts',
           'endpoint':'Mean dry seed mass of six prespecified central plants, g/plant',
           'estimand':'Equal-weight average plot-level treatment effect in these four blocks at this site-season; causal interpretation assumes consistency and no spillover'},
 'data_audit':{'missing':0,'excluded':0,'duplicate_plant_keys':0,'all_plots_have_six_numbered_plants':True},
 'primary':{'control_mean_g':control,'mulch_mean_g':mulch,'difference_g':effect,
            'ratio_of_observed_means_percent':100*effect/control,
            'mean_of_block_percent_changes':statistics.mean(100*b['difference_g']/b['control_mean_g'] for b in blockrows),
            'block_differences_g':ds,'block_difference_sd_g':sd,'block_se_g':se,
            'fisher_sharp_null_two_sided_p':p2,'fisher_one_sided_positive_p':p1,
            'enumerated_assignments':len(perms),
            't3_critical_975':crit,'paired_t_reference_95_interval_g':[effect-crit*se,effect+crit*se],
            'paired_t_reference_two_sided_p':2*(1-cdf_t3(abs(effect/se))),
            'interval_limit':'t reference interval requires extra modeling of block differences; no exact finite-design 95% coverage claim',
            'exact_95_constant_effect_inversion':'All real numbers: with only 16 assignments a nonrandomized two-sided absolute-mean sign-flip p is at least 2/16, so no constant additive effect is rejected at alpha=.05'},
 'invalid_comparators':{
   'plant_number_pseudopairs':{'n':len(pseudo),'effect_g':statistics.mean(pseudo),'se_g':naive_pseudo_se,'hypothetical_signflip_p':wrong_p,'invalid_reason':'Six subsamples share one plot-level assignment; plant-number matching across plots is not a randomized pairing'},
   'all_rows_unblocked':{'n_per_treatment':24,'effect_g':effect,'se_g':naive_se,'invalid_reason':'Ignores plot dependence and block matching; not design-valid despite larger SE here'},
   'draft_p_003':{'reproduced':False,'reason':'No bootstrap algorithm, seed, resampling unit, null construction or code supplied; cannot verify the exact claimed p'}},
 'exploratory_excluding_B4':{'effect_g':first3_effect,'two_sided_signflip_p':sum(abs(x)>=abs(first3_effect)-1e-12 for x in first3_perm)/len(first3_perm),'status':'Sensitivity only; retains B4 in primary analysis; dropping changes finite target'},
 'scope_limits':['One site-season only; blocks are not a national random sample','Crop species, calibration and blinding not supplied; cannot infer measurement traceability','No area yield, economic, pest, or environmental endpoint','B4 supplementary irrigation affected both plots; not an independent irrigation comparison','No external references accessed'],
 'execution':{'command':'python3 artifacts/run.py','working_directory':'PROJECT','python':'stdlib only','random_seed':None,'seed_reason':'No Monte Carlo: complete enumeration and deterministic arithmetic','failures':[]}}
writecsv('plot-means.csv',plotrows);writecsv('block-contrasts.csv',blockrows);writecsv('randomization-distribution.csv',perms)
results['execution']['elapsed_seconds']=time.perf_counter()-t0
assert results['execution']['elapsed_seconds']<10
(ROOT/'artifacts'/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
manifest={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'inputs').iterdir()) if p.is_file()}
(ROOT/'artifacts'/'input-sha256.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(results,ensure_ascii=False,indent=2))
