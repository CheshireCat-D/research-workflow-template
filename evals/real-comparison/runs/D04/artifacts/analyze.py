#!/usr/bin/env python3
"""Calendar-only Bike Sharing experiment; standard library, no network."""
import argparse, collections, csv, datetime, hashlib, json, math, pathlib, random, sys, platform
SEED=20261029
B=2000

def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def save(p, data):
    pathlib.Path(p).write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
def read(p):
    with pathlib.Path(p).open(newline='', encoding='utf-8-sig') as f:
        reader=csv.DictReader(f); rows=list(reader); fields=reader.fieldnames
    return rows, fields

def audit(h, d, hp, dp):
    out={'hour_sha256':sha(hp),'day_sha256':sha(dp),'hour_rows':len(h),'day_rows':len(d)}
    out['empty_cells']={name:sum(v is None or v.strip()=='' for row in rows for v in row.values()) for name,rows in [('hour',h),('day',d)]}
    out['duplicate_hour_keys']=len(h)-len({(r['dteday'],r['hr']) for r in h})
    out['duplicate_day_keys']=len(d)-len({r['dteday'] for r in d})
    out['duplicate_instant']={name:len(rows)-len({r['instant'] for r in rows}) for name,rows in [('hour',h),('day',d)]}
    out['count_identity_failures']={name:sum(int(r['cnt'])!=int(r['casual'])+int(r['registered']) for r in rows) for name,rows in [('hour',h),('day',d)]}
    dates=collections.defaultdict(list)
    for r in h: dates[r['dteday']].append(r)
    start=datetime.date(2011,1,1)
    expected=[(start+datetime.timedelta(days=i)).isoformat() for i in range(365)]
    out['hour_date_range']=[min(dates),max(dates)]
    out['day_date_range']=[min(r['dteday'] for r in d),max(r['dteday'] for r in d)]
    out['yr_values']={name:sorted({r['yr'] for r in rows}) for name,rows in [('hour',h),('day',d)]}
    out['missing_dates_hour']=sorted(set(expected)-dates.keys())
    out['missing_dates_day']=sorted(set(expected)-{r['dteday'] for r in d})
    out['hours_per_date_distribution']=dict(sorted(collections.Counter(len(v) for v in dates.values()).items()))
    out['missing_calendar_hours']={dt:[i for i in range(24) if str(i) not in {r['hr'] for r in dates.get(dt,[])}] for dt in expected if len(dates.get(dt,[]))!=24}
    out['missing_calendar_hour_count']=sum(map(len,out['missing_calendar_hours'].values()))
    out['hour_day_date_set_equal']=set(dates)=={r['dteday'] for r in d}
    mismatches=[]
    for r in d:
        for col in ('casual','registered','cnt'):
            val=sum(int(x[col]) for x in dates.get(r['dteday'],[]))
            if val!=int(r[col]): mismatches.append({'date':r['dteday'],'field':col,'hour_sum':val,'day':int(r[col])})
    out['hour_day_count_mismatches']=mismatches
    out['within_date_workingday_conflicts']=[dt for dt,rows in dates.items() if len({r['workingday'] for r in rows})!=1]
    dm={r['dteday']:r for r in d}
    out['hour_day_calendar_conflicts']=sum(any(r[c]!=dm[r['dteday']][c] for c in ('workingday','holiday','weekday','mnth','yr')) for r in h)
    out['workingday_definition_failures']=sum(int(r['workingday'])!=int(int(r['weekday']) not in (0,6) and int(r['holiday'])==0) for r in h)
    return out

def fit(rows, hour_path):
    train=[r for r in rows if r['dteday']<'2011-10-01']
    assert train and all(r['dteday'].startswith('2011-') for r in train)
    a=collections.defaultdict(list); b=collections.defaultdict(list)
    for r in train:
        a[r['hr']].append(int(r['cnt'])); b[r['workingday']+':'+r['hr']].append(int(r['cnt']))
    tab=lambda groups:{k:{'sum_cnt':sum(v),'n':len(v),'mean':sum(v)/len(v)} for k,v in sorted(groups.items())}
    return {'schema_version':1,'frozen_at':'2011-09-30 end of day','train_start':min(r['dteday'] for r in train),'train_end':max(r['dteday'] for r in train),'train_n_hours':len(train),'train_n_dates':len({r['dteday'] for r in train}),'feature_names':{'C0':['hr'],'C1':['workingday','hr']},'prediction_rule':'Unrounded training arithmetic mean; unseen C1 (workingday,hr) uses C0 hour mean; unknown C0 hour is an error.','C0':tab(a),'C1':tab(b),'source_hour_sha256':sha(hour_path),'prohibited_features':['weather','instant','numeric date','casual','registered','yr'],'tuning':'none'}

def predict(rows, model):
    pred=[]
    for r in rows:
        hr=str(int(r['hr'])); wd=str(int(r['workingday']))
        if hr not in model['C0']: raise ValueError('Unseen C0 hour: '+hr)
        p0=model['C0'][hr]['mean']; cell=model['C1'].get(wd+':'+hr); p1=cell['mean'] if cell else p0
        y=int(r['cnt'])
        pred.append({'dteday':r['dteday'],'hr':int(hr),'workingday':int(wd),'cnt':y,'C0':p0,'C1':p1,'fallback':int(cell is None),'abs0':abs(p0-y),'abs1':abs(p1-y),'sq0':(p0-y)**2,'sq1':(p1-y)**2,'bias0':p0-y,'bias1':p1-y})
    return pred

def metrics(p):
    if not p: return None
    days=collections.defaultdict(list)
    for r in p: days[r['dteday']].append(r)
    n=len(p); D=len(days); out={'n_hours':n,'n_dates':D,'range':[min(days),max(days)],'C1_fallback_hours':sum(r['fallback'] for r in p)}
    for k in (0,1):
        out['C'+str(k)]={'hour_weighted_MAE':math.fsum(r['abs'+str(k)] for r in p)/n,'hour_weighted_RMSE':math.sqrt(math.fsum(r['sq'+str(k)] for r in p)/n),'mean_bias_pred_minus_true':math.fsum(r['bias'+str(k)] for r in p)/n,'date_equal_mean_intraday_MAE':math.fsum(math.fsum(r['abs'+str(k)] for r in v)/len(v) for v in days.values())/D}
    out['MAE_difference_C0_minus_C1']=out['C0']['hour_weighted_MAE']-out['C1']['hour_weighted_MAE']
    out['relative_MAE_reduction']=1-out['C1']['hour_weighted_MAE']/out['C0']['hour_weighted_MAE']
    out['date_equal_MAE_difference']=out['C0']['date_equal_mean_intraday_MAE']-out['C1']['date_equal_mean_intraday_MAE']
    out['date_equal_relative_MAE_reduction']=1-out['C1']['date_equal_mean_intraday_MAE']/out['C0']['date_equal_mean_intraday_MAE']
    return out

def quantile(v,p):
    s=sorted(v); z=(len(s)-1)*p; lo=math.floor(z); hi=math.ceil(z)
    return s[lo]+(z-lo)*(s[hi]-s[lo])

def bootstrap(p, block):
    days=collections.defaultdict(list)
    for r in p: days[r['dteday']].append(r)
    dates=sorted(days); D=len(dates); rng=random.Random(SEED)
    totals=[(len(days[d]),math.fsum(r['abs0'] for r in days[d]),math.fsum(r['abs1'] for r in days[d])) for d in dates]
    samples=[]
    for repeat in range(B):
        idx=[]
        while len(idx)<D:
            start=rng.randrange(D); idx.extend((start+j)%D for j in range(block))
        idx=idx[:D]; n=sum(totals[j][0] for j in idx)
        m0=math.fsum(totals[j][1] for j in idx)/n; m1=math.fsum(totals[j][2] for j in idx)/n
        samples.append({'replicate':repeat+1,'n_hours':n,'C0_MAE':m0,'C1_MAE':m1,'difference':m0-m1,'relative_reduction':1-m1/m0})
    return {'block_length_days':block,'seed':SEED,'B':B,'n_dates':D,'difference_CI95':[quantile([r['difference'] for r in samples],q) for q in (.025,.975)],'relative_reduction_CI95':[quantile([r['relative_reduction'] for r in samples],q) for q in (.025,.975)],'quantile':'sorted (B-1)p linear interpolation','sampling':'paired circular date blocks, truncate to D dates, pool all retained hours'},samples

def csvout(p,rows):
    if not rows: return
    with pathlib.Path(p).open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def evaluate(rows, model, output, start, end):
    use=[r for r in rows if (start is None or r['dteday']>=start) and (end is None or r['dteday']<=end)]
    p=predict(use, model)
    if not p: raise ValueError('No evaluation rows')
    bydate=collections.defaultdict(list)
    for r in p: bydate[r['dteday']].append(r)
    full={dt for dt,v in bydate.items() if len(v)==24 and {r['hr'] for r in v}==set(range(24))}
    out={'all':metrics(p),'complete_24h_dates':metrics([r for r in p if r['dteday'] in full]),'workingday':{str(wd):metrics([r for r in p if r['workingday']==wd]) for wd in (0,1)},'bootstrap':{}}
    for block in (7,28):
        result,samples=bootstrap(p,block); out['bootstrap'][str(block)]=result;csvout(output/('bootstrap_'+str(block)+'.csv'),samples)
    csvout(output/'predictions.csv',p)
    daily=[{'dteday':dt,'n_hours':len(v),'workingday':v[0]['workingday'],'abs_error_C0':math.fsum(r['abs0'] for r in v),'abs_error_C1':math.fsum(r['abs1'] for r in v),'MAE_C0':math.fsum(r['abs0'] for r in v)/len(v),'MAE_C1':math.fsum(r['abs1'] for r in v)/len(v)} for dt,v in sorted(bydate.items())]
    csvout(output/'daily_errors.csv',daily)
    out['threshold_10pct_met']=out['all']['relative_MAE_reduction']>=.10
    save(output/'results.json',out)
    return out

def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
    train=sub.add_parser('train');train.add_argument('--input-dir',type=pathlib.Path,required=True);train.add_argument('--output-dir',type=pathlib.Path,required=True)
    score=sub.add_parser('score');score.add_argument('--hour-file',type=pathlib.Path,required=True);score.add_argument('--model',type=pathlib.Path,required=True);score.add_argument('--output-dir',type=pathlib.Path,required=True);score.add_argument('--start');score.add_argument('--end')
    args=parser.parse_args(); out=args.output_dir
    if out.exists() and any(out.iterdir()): raise FileExistsError('Use an empty or new output directory: '+str(out))
    out.mkdir(parents=True,exist_ok=True)
    if args.command=='train':
        hp=args.input_dir/'data/hour_2011.csv';dp=args.input_dir/'data/day_2011.csv'
        h,hf=read(hp);d,df=read(dp)
        a=audit(h,d,hp,dp);a['hour_fields']=hf;a['day_fields']=df
        assert all(r['dteday'].startswith('2011-') for r in h+d)
        assert a['duplicate_hour_keys']==a['duplicate_day_keys']==0
        assert not any(a['empty_cells'].values()) and not any(a['count_identity_failures'].values())
        assert not a['hour_day_count_mismatches']
        save(out/'audit.json',a)
        model=fit(h,hp);save(out/'model.json',model)
        result=evaluate(h,model,out,'2011-10-01','2011-12-31')
        save(out/'runtime.json',{'python':sys.version,'platform':platform.platform(),'argv':sys.argv,'network':False,'dependencies':'Python standard library only','model_sha256':sha(out/'model.json'),'code_sha256':sha(__file__)})
    else:
        h,_=read(args.hour_file);model=json.loads(args.model.read_text(encoding='utf-8'))
        result=evaluate(h,model,out,args.start,args.end)
        save(out/'score_provenance.json',{'hour_sha256':sha(args.hour_file),'frozen_model_sha256':sha(args.model),'code_sha256':sha(__file__),'argv':sys.argv,'retrained':False})
    print(json.dumps({'all':result['all'],'complete_24h_dates':result['complete_24h_dates'],'workingday':result['workingday'],'bootstrap':result['bootstrap'],'threshold_10pct_met':result['threshold_10pct_met']},ensure_ascii=False,indent=2))
if __name__=='__main__': main()
