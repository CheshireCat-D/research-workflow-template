#!/usr/bin/env python3
"""Fixed calendar-mean prototypes; fit once, or score a saved JSON model.

Standard library only. No weather/category-count predictors; predictions unrounded.
"""
import argparse
import collections
import csv
import datetime as dt
import hashlib
import json
import math
import pathlib
import random
import sys
import time

SEED = 20261029
B = 2000

def digest(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()

def write_json(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')

def read_csv(path):
    with pathlib.Path(path).open(encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fields = reader.fieldnames
    return fields, rows

def write_csv(path, rows, fields):
    with path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

def date_range(start, end):
    first = dt.date.fromisoformat(start)
    last = dt.date.fromisoformat(end)
    return [(first + dt.timedelta(days=i)).isoformat() for i in range((last-first).days+1)]

def schema_audit(fields, rows, key):
    keys = [tuple(r[k] for k in key) for r in rows]
    counter = collections.Counter(keys)
    blanks = [(i+2, f) for i,r in enumerate(rows) for f in fields if r.get(f) in ('', None)]
    extra = [i+2 for i,r in enumerate(rows) if None in r]
    return {'rows':len(rows), 'columns':fields, 'duplicate_keys':sum(n-1 for n in counter.values()),
            'duplicate_key_examples':[list(k) for k,n in counter.items() if n>1][:10],
            'blank_cells':len(blanks), 'blank_examples':blanks[:10], 'extra_cell_rows':extra[:10],
            'duplicate_instant':len(rows)-len({r['instant'] for r in rows}),
            'dates':[min(r['dteday'] for r in rows),max(r['dteday'] for r in rows)],
            'years':sorted({r['yr'] for r in rows}),
            'count_identity_failures':sum(int(r['casual'])+int(r['registered'])!=int(r['cnt']) for r in rows)}

def audit_inputs(hour_path, day_path, output):
    hf, hr = read_csv(hour_path)
    df, dr = read_csv(day_path)
    h = schema_audit(hf,hr,['dteday','hr'])
    d = schema_audit(df,dr,['dteday'])
    if any(not r['dteday'].startswith('2011-') or r['yr']!='0' for r in hr+dr):
        raise ValueError('Fit input must contain 2011 only.')
    byday = collections.defaultdict(list)
    for r in hr:
        byday[r['dteday']].append(r)
    days = date_range('2011-01-01','2011-12-31')
    coverage = []
    missing = []
    for day in days:
        present = {int(r['hr']) for r in byday[day]}
        absent = sorted(set(range(24))-present)
        coverage.append({'dteday':day,'rows':len(byday[day]),'distinct_hours':len(present),'missing_hours':','.join(map(str,absent))})
        missing.extend({'dteday':day,'hr':x} for x in absent)
    write_csv(output/'calendar_coverage.csv',coverage,list(coverage[0]))
    write_csv(output/'missing_calendar_hours.csv',missing,['dteday','hr'])
    h.update({'expected_calendar_hours':len(days)*24,'missing_calendar_hours':len(missing),
              'hours_per_day_distribution':dict(sorted(collections.Counter(len(byday[x]) for x in days).items())),
              'complete_24h_dates':sum(len(byday[x])==24 and len({r['hr'] for r in byday[x]})==24 for x in days),
              'missing_calendar_dates':[x for x in days if not byday[x]],
              'invalid_hours':sum(not 0<=int(r['hr'])<=23 for r in hr),
              'chronological_order':[(r['dteday'],int(r['hr'])) for r in hr]==sorted((r['dteday'],int(r['hr'])) for r in hr),
              'cnt_total':sum(int(r['cnt']) for r in hr),
              'cnt_min':min(int(r['cnt']) for r in hr), 'cnt_max':max(int(r['cnt']) for r in hr)})
    daily = {r['dteday']:r for r in dr}
    discrepancy = []
    for day in sorted(set(byday)|set(daily)):
        for col in ['casual','registered','cnt']:
            total = sum(int(r[col]) for r in byday[day])
            value = int(daily[day][col]) if day in daily else None
            if total!=value:
                discrepancy.append({'dteday':day,'field':col,'hour_sum':total,'day_value':value})
    d['cnt_total']=sum(int(r['cnt']) for r in dr)
    d['missing_calendar_dates']=sorted(set(days)-set(daily))
    calendar_conflicts = []
    for r in hr:
        expected = int(int(r['weekday']) not in (0,6) and int(r['holiday'])==0)
        pyweekday = (dt.date.fromisoformat(r['dteday']).weekday()+1)%7
        if int(r['workingday'])!=expected or int(r['weekday'])!=pyweekday:
            calendar_conflicts.append([r['dteday'],r['hr']])
    result = {'inputs':{'hour':{'sha256':digest(hour_path)},'day':{'sha256':digest(day_path)}},
              'hour':h,'day':d,'hour_day_discrepancies':discrepancy,
              'calendar_field_conflicts':calendar_conflicts,
              'calendar_fields_constant_within_date':all(all(len({r[c] for r in rows})==1 for c in ['workingday','holiday','weekday']) for rows in byday.values()),
              'hour_day_calendar_conflicts':sum(any(r[c]!=daily[day][c] for r in rows for c in ['workingday','holiday','weekday']) for day,rows in byday.items())}
    write_json(output/'audit.json',result)
    return hr,result

def fit_model(rows, source_hash):
    train = [r for r in rows if r['dteday']<'2011-10-01']
    groups0 = collections.defaultdict(lambda:[0,0])
    groups1 = collections.defaultdict(lambda:[0,0])
    for r in train:
        for groups,key in [(groups0,str(int(r['hr']))),(groups1,f"{int(r['workingday'])},{int(r['hr'])}")]:
            groups[key][0]+=int(r['cnt'])
            groups[key][1]+=1
    convert = lambda g:{k:{'sum':v[0],'n':v[1],'mean':v[0]/v[1]} for k,v in sorted(g.items())}
    return {'format':'calendar-mean-v1','frozen_at':'2011-09-30 end of day',
            'training_start':min(r['dteday'] for r in train),'training_end':max(r['dteday'] for r in train),
            'training_rows':len(train),'training_dates':len({r['dteday'] for r in train}),
            'training_input_sha256':source_hash,
            'predictors':{'C0':['hr'],'C1':['workingday','hr']},
            'prediction_rule':'arithmetic training mean; unseen C1 group falls back to C0; no rounding',
            'C0':convert(groups0),'C1':convert(groups1)}

def predict(rows, model):
    out=[]
    for r in rows:
        hr=str(int(r['hr']))
        wd=int(r['workingday'])
        if not 0<=int(hr)<=23 or wd not in (0,1):
            raise ValueError('Invalid calendar predictor')
        p0=model['C0'][hr]['mean']
        key=f'{wd},{hr}'
        p1=model['C1'].get(key,model['C0'][hr])['mean']
        y=int(r['cnt'])
        out.append({'dteday':r['dteday'],'hr':int(hr),'workingday':wd,'cnt':y,'C0':p0,'C1':p1,
                    'fallback':int(key not in model['C1']),
                    'abs0':abs(p0-y),'abs1':abs(p1-y),'sq0':(p0-y)**2,'sq1':(p1-y)**2,
                    'bias0':p0-y,'bias1':p1-y})
    return sorted(out,key=lambda r:(r['dteday'],r['hr']))

def summarize(rows):
    byday=collections.defaultdict(list)
    for r in rows:
        byday[r['dteday']].append(r)
    n=len(rows)
    result={'hours':n,'dates':len(byday)}
    for i in (0,1):
        result[f'C{i}']={'MAE':math.fsum(r[f'abs{i}'] for r in rows)/n,
                        'RMSE':math.sqrt(math.fsum(r[f'sq{i}'] for r in rows)/n),
                        'mean_bias_prediction_minus_actual':math.fsum(r[f'bias{i}'] for r in rows)/n,
                        'day_equal_mean_intraday_MAE':math.fsum(math.fsum(r[f'abs{i}'] for r in day)/len(day) for day in byday.values())/len(byday)}
    m0=result['C0']['MAE']; m1=result['C1']['MAE']
    d0=result['C0']['day_equal_mean_intraday_MAE']; d1=result['C1']['day_equal_mean_intraday_MAE']
    result.update({'MAE_absolute_difference_C0_minus_C1':m0-m1,'MAE_relative_reduction':1-m1/m0,
                   'day_equal_absolute_difference_C0_minus_C1':d0-d1,'day_equal_relative_reduction':1-d1/d0})
    return result

def quantile(values,p):
    values=sorted(values)
    index=(len(values)-1)*p
    low=math.floor(index); high=math.ceil(index)
    return values[low]+(values[high]-values[low])*(index-low)

def bootstrap(daily,block):
    rng=random.Random(SEED)
    dates=sorted(daily)
    D=len(dates)
    reps=[]
    for b in range(B):
        chosen=[]
        while len(chosen)<D:
            start=rng.randrange(D)
            chosen.extend((start+j)%D for j in range(block))
        chosen=chosen[:D]
        sampled=[daily[dates[i]] for i in chosen]
        count=sum(x['n'] for x in sampled)
        m0=math.fsum(x['abs0_sum'] for x in sampled)/count
        m1=math.fsum(x['abs1_sum'] for x in sampled)/count
        reps.append({'replicate':b+1,'hours':count,'MAE0':m0,'MAE1':m1,'absolute_difference':m0-m1,'relative_reduction':1-m1/m0})
    result={'block_days':block,'B':B,'seed':SEED,'dates':D,
            'absolute_difference_CI95':[quantile([r['absolute_difference'] for r in reps],p) for p in (.025,.975)],
            'relative_reduction_CI95':[quantile([r['relative_reduction'] for r in reps],p) for p in (.025,.975)]}
    return result,reps

def evaluate(rows,output):
    daily={}
    for day in sorted({r['dteday'] for r in rows}):
        rs=[r for r in rows if r['dteday']==day]
        daily[day]={'dteday':day,'n':len(rs),'distinct_hours':len({r['hr'] for r in rs}),
                    'workingday':rs[0]['workingday'],
                    'abs0_sum':math.fsum(r['abs0'] for r in rs),'abs1_sum':math.fsum(r['abs1'] for r in rs)}
    complete={day for day,d in daily.items() if d['n']==24 and d['distinct_hours']==24}
    result={'observed_range':[rows[0]['dteday'],rows[-1]['dteday']],
            'all_observed':summarize(rows),
            'complete_24h_dates':summarize([r for r in rows if r['dteday'] in complete]),
            'workingday':{str(wd):summarize([r for r in rows if r['workingday']==wd]) for wd in (0,1)},
            'fallback_hours':sum(r['fallback'] for r in rows),'bootstrap':[]}
    for block in (7,28):
        summary,reps=bootstrap(daily,block)
        result['bootstrap'].append(summary)
        write_csv(output/f'bootstrap_{block}d.csv',reps,list(reps[0]))
    write_csv(output/'predictions.csv',rows,list(rows[0]))
    write_csv(output/'daily_errors.csv',list(daily.values()),list(next(iter(daily.values()))))
    write_json(output/'results.json',result)
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='mode',required=True)
    fit=sub.add_parser('fit')
    fit.add_argument('--input-dir',required=True,type=pathlib.Path)
    fit.add_argument('--output-dir',required=True,type=pathlib.Path)
    score=sub.add_parser('score')
    score.add_argument('--hour-csv',required=True,type=pathlib.Path)
    score.add_argument('--model',required=True,type=pathlib.Path)
    score.add_argument('--output-dir',required=True,type=pathlib.Path)
    args=parser.parse_args()
    started=time.perf_counter()
    args.output_dir.mkdir(parents=True,exist_ok=False)
    if args.mode=='fit':
        hour=args.input_dir/'data/hour_2011.csv'; day=args.input_dir/'data/day_2011.csv'
        rows,audit=audit_inputs(hour,day,args.output_dir)
        model=fit_model(rows,digest(hour))
        write_json(args.output_dir/'model.json',model)
        holdout=[r for r in rows if '2011-10-01'<=r['dteday']<='2011-12-31']
        result=evaluate(predict(holdout,model),args.output_dir)
    else:
        fields,rows=read_csv(args.hour_csv)
        model=json.loads(args.model.read_text(encoding='utf-8'))
        if len({(r['dteday'],int(r['hr'])) for r in rows})!=len(rows):
            raise ValueError('Duplicate date/hour key in score input')
        result=evaluate(predict(rows,model),args.output_dir)
        write_json(args.output_dir/'score_provenance.json',{'input_sha256':digest(args.hour_csv),'model_sha256':digest(args.model),'refit':False})
    write_json(args.output_dir/'runtime.json',{'python':sys.version,'argv':sys.argv,'seconds':time.perf_counter()-started,'libraries':'standard library only'})
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
