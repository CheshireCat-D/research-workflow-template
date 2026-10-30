#!/usr/bin/env python3
"""Audit two supplied years and score the original frozen baselines; never fit."""
import argparse
import collections
import csv
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import runpy
import sys

EXPECTED_MODEL = '84c6c80033718b1c0b7c0333d90ebe66c0978fd305b44d65ffd5ca9fd6f19a47'
READS = []
def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def logread(p, name):
    READS.append({'logical_name':name,'sha256':sha(p)})
    return Path(p)
def jread(p, name):
    return json.loads(logread(p,name).read_text(encoding='utf-8'))
def readcsv(p,name):
    with logread(p,name).open(encoding='utf-8-sig',newline='') as f:
        r=csv.DictReader(f)
        return r.fieldnames,list(r)
def dump(p,x):
    p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def csvout(p,rows,fields):
    with p.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
def audit(year,hours,days,hfields,dfields,out):
    hd=collections.defaultdict(list)
    for r in hours:hd[r['dteday']].append(r)
    daymap={r['dteday']:r for r in days}
    cover=[];mismatches=[];calmismatch=[]
    for date,rs in sorted(hd.items()):
        present={int(r['hr']) for r in rs}
        cover.append({'date':date,'n_rows':len(rs),'n_unique_hours':len(present),'missing_hours':';'.join(map(str,sorted(set(range(24))-present)))})
        if date in daymap:
            for c in ['casual','registered','cnt']:
                total=sum(int(r[c]) for r in rs)
                if total!=int(daymap[date][c]):mismatches.append({'date':date,'column':c,'hour_sum':total,'day_value':int(daymap[date][c])})
        for c in ['workingday','weekday','holiday','yr','mnth']:
            vals={r[c] for r in rs}
            if len(vals)!=1 or (date in daymap and vals!={daymap[date][c]}):calmismatch.append({'date':date,'column':c})
    start=dt.date(year,1,1);end=dt.date(year,12,31)
    dates={(start+dt.timedelta(days=i)).isoformat() for i in range((end-start).days+1)}
    def dup(rs,ks):return len(rs)-len({tuple(r[k] for k in ks) for r in rs})
    def empty(rs):return sum(v is None or v.strip()=='' for r in rs for v in r.values())
    res={'year':year,'hour_rows':len(hours),'day_rows':len(days),'hour_date_count':len(hd),'day_date_count':len(daymap),
         'hour_date_start':min(hd),'hour_date_end':max(hd),'day_date_start':min(daymap),'day_date_end':max(daymap),
         'hour_duplicate_keys':dup(hours,['dteday','hr']),'day_duplicate_keys':dup(days,['dteday']),
         'hour_duplicate_full_rows':dup(hours,hfields),'day_duplicate_full_rows':dup(days,dfields),
         'hour_empty_cells':empty(hours),'day_empty_cells':empty(days),
         'hour_count_identity_failures':sum(int(r['cnt'])!=int(r['casual'])+int(r['registered']) for r in hours),
         'day_count_identity_failures':sum(int(r['cnt'])!=int(r['casual'])+int(r['registered']) for r in days),
         'hour_negative_counts':sum(int(r[c])<0 for r in hours for c in ['casual','registered','cnt']),
         'day_negative_counts':sum(int(r[c])<0 for r in days for c in ['casual','registered','cnt']),
         'hour_out_of_range':sum(int(r['hr']) not in range(24) for r in hours),
         'workingday_out_of_range':sum(int(r['workingday']) not in [0,1] for r in hours),
         'hour_wrong_calendar_year':sum(dt.date.fromisoformat(r['dteday']).year!=year for r in hours),
         'day_wrong_calendar_year':sum(dt.date.fromisoformat(r['dteday']).year!=year for r in days),
         'hour_yr_values':sorted({int(r['yr']) for r in hours}),'day_yr_values':sorted({int(r['yr']) for r in days}),
         'hour_count_distribution':dict(sorted(collections.Counter(len(rs) for rs in hd.values()).items())),
         'complete_24h_dates':sum(len(rs)==24 and {int(r['hr']) for r in rs}==set(range(24)) for rs in hd.values()),
         'missing_calendar_hours':len(dates)*24-len({(r['dteday'],r['hr']) for r in hours}),
         'missing_whole_hour_dates':sorted(dates-set(hd)),'missing_whole_day_dates':sorted(dates-set(daymap)),
         'hour_only_dates':sorted(set(hd)-set(daymap)),'day_only_dates':sorted(set(daymap)-set(hd)),
         'daily_count_mismatches':mismatches,'calendar_field_mismatches':calmismatch,
         'annual_count_hour_sum':sum(int(r['cnt']) for r in hours),'annual_count_day_sum':sum(int(r['cnt']) for r in days),
         'mean_daily_count':sum(int(r['cnt']) for r in days)/len(days)}
    csvout(out/f'date_coverage_{year}.csv',cover,['date','n_rows','n_unique_hours','missing_hours'])
    csvout(out/f'daily_count_mismatches_{year}.csv',mismatches,['date','column','hour_sum','day_value'])
    return res

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input-dir',type=Path,required=True)
    p.add_argument('--prior-dir',type=Path,required=True,help='stage-A snapshot or original stage-A output directory')
    p.add_argument('--model',type=Path,required=True)
    p.add_argument('--output-dir',type=Path,required=True)
    args=p.parse_args();out=args.output_dir;out.mkdir(parents=True,exist_ok=True)
    code=logread(args.prior_dir/'analysis.py','workspace/stage_a_snapshot/analysis.py')
    core=runpy.run_path(str(code),run_name='__frozen_library__')
    assert core['SEED']==20261029 and core['B']==2000
    model=jread(args.model,'workspace/model.json');modelhash=sha(args.model)
    assert modelhash==EXPECTED_MODEL,'Frozen model hash mismatch; no fallback retraining'
    old=jread(args.prior_dir/'results.json','workspace/stage_a_snapshot/results.json')
    manifest=jread(args.input_dir/'INPUT_MANIFEST.json','input/data-b/INPUT_MANIFEST.json')
    dataset={};audits={};manifest_checks={}
    for year in [2011,2012]:
        hname=f'data/hour_{year}.csv';dname=f'data/day_{year}.csv'
        hf,hs=readcsv(args.input_dir/hname,'input/data-b/'+hname)
        df,ds=readcsv(args.input_dir/dname,'input/data-b/'+dname)
        dataset[year]=(hs,ds);audits[str(year)]=audit(year,hs,ds,hf,df,out)
        for n,rs in [(hname,hs),(dname,ds)]:
            manifest_checks[n]={'sha256':sha(args.input_dir/n),'hash_matches':sha(args.input_dir/n)==manifest[n]['sha256'],'rows_match':len(rs)==manifest[n]['data_rows']}
            assert manifest_checks[n]['hash_matches'] and manifest_checks[n]['rows_match']
    train=[r for r in dataset[2011][0] if r['dteday']<'2011-10-01']
    test=[r for r in dataset[2011][0] if '2011-10-01'<=r['dteday']<='2011-12-31']
    assert len(train)==model['train_n_rows']==6442
    assert len({r['dteday'] for r in train})==model['train_n_dates']==273
    assert min(r['dteday'] for r in train)==model['train_start']=='2011-01-01'
    assert max(r['dteday'] for r in train)==model['train_end']=='2011-09-30'
    assert model['training_source_sha256']==sha(args.input_dir/'data/hour_2011.csv')
    cells=0
    for family in ['C0','C1']:
        for key,cell in model[family].items():
            keys=list(map(int,key.split(',')))
            rs=[r for r in train if int(r['hr'])==keys[-1] and (family=='C0' or int(r['workingday'])==keys[0])]
            sm=sum(int(r['cnt']) for r in rs);n=len(rs)
            assert (cell['sum'],cell['n'],cell['mean'])==(sm,n,sm/n)
            cells+=1
    # Recreate the historical scores with frozen parameters; do not fit or change parameters.
    historic=core['metrics'](core['predict'](test,model))
    assert historic==old['overall'],'Historical metric replay mismatch'
    preds=core['predict'](dataset[2012][0],model)
    res=core['evaluate'](preds,out)
    # Independently recompute all hourly predictions and principal metrics.
    for r,q in zip(dataset[2012][0],preds):
        assert q['C0']==model['C0'][r['hr']]['sum']/model['C0'][r['hr']]['n']
        cell=model['C1'][r['workingday']+','+r['hr']]
        assert q['C1']==cell['sum']/cell['n']
    for m in ['C0','C1']:
        errors=[q[m]-int(r['cnt']) for r,q in zip(dataset[2012][0],preds)]
        assert math.isclose(sum(map(abs,errors))/len(errors),res['overall'][m]['MAE'],abs_tol=1e-9)
        assert math.isclose(math.sqrt(sum(x*x for x in errors)/len(errors)),res['overall'][m]['RMSE'],abs_tol=1e-9)
        assert math.isclose(sum(errors)/len(errors),res['overall'][m]['bias_prediction_minus_actual'],abs_tol=1e-9)
    provenance={'trained':False,'model_sha256_before':modelhash,'model_sha256_after':sha(args.model),
        'stage_a_code_sha256':sha(code),'stage_b_code_sha256':sha(Path(__file__)),
        'training_verification':{'rows':len(train),'dates':len({r['dteday'] for r in train}),'exact_sum_n_mean_cells':cells,
        'historical_overall_metrics_exact_replay':historic==old['overall']},
        '2012_prediction_rows_independently_checked':len(preds),'bootstrap_seed':core['SEED'],'bootstrap_B':core['B'],
        'bootstrap_implementation':'unchanged stage-A analysis.py evaluate/block_bootstrap/quantile',
        'python_version':sys.version,'manifest_checks':manifest_checks,'reads':READS}
    assert provenance['model_sha256_before']==provenance['model_sha256_after']
    growth={'total_growth':audits['2012']['annual_count_day_sum']/audits['2011']['annual_count_day_sum']-1,
        'mean_daily_growth':audits['2012']['mean_daily_count']/audits['2011']['mean_daily_count']-1}
    dump(out/'data_audit.json',audits);dump(out/'annual_growth.json',growth);dump(out/'score_provenance.json',provenance)
    rows=[]
    for label,z in [('2011_Q4',old),('2012',res)]:
        for subset,q in [('overall',z['overall']),('complete_24h_dates',z['complete_24h_dates'])]+[('workingday_'+k,v) for k,v in z['by_workingday'].items()]:
            for m in ['C0','C1']:
                rows.append({'period':label,'subset':subset,'model':m,'n_dates':q['n_dates'],'n_hours':q['n_hours'],**q[m],
                'absolute_improvement':q['hour_weighted_absolute_improvement'],'relative_improvement':q['hour_weighted_relative_improvement'],
                'day_equal_absolute_improvement':q['day_equal_absolute_improvement'],'day_equal_relative_improvement':q['day_equal_relative_improvement']})
    csvout(out/'comparison_metrics.csv',rows,list(rows[0]))
    print(json.dumps({'status':'executed','audit':audits,'growth':growth,'results_2012':res,'verification':provenance},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
