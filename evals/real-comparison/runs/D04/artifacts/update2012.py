#!/usr/bin/env python3
"""Frozen calendar models: audit annual slices and evaluate a new year; never fit."""
import argparse, collections, csv, datetime as dt, hashlib, importlib.util, json, math, pathlib, platform, shutil, sys, time
EXPECTED_MODEL='f8a758c6c73cf7e0cfcfa0936b594afb8f23b1260610ecae15929f601dc8e5d4'
EXPECTED_CODE='9aa68881931fdb685b4c27ea5c5f976b9576e49fac937140b18cc396bad6f32b'
READS=[]
def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def touch(p,logical,mode='full'):
    READS.append({'logical_name':logical,'sha256':sha(p),'access':mode});return pathlib.Path(p)
def load(p,logical): return json.loads(touch(p,logical).read_text(encoding='utf-8'))
def save(p,x): pathlib.Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def readcsv(p,logical):
    with touch(p,logical).open(newline='',encoding='utf-8-sig') as f:
        r=csv.DictReader(f); return list(r),r.fieldnames

def audit_year(h,d,year):
    dates=collections.defaultdict(list)
    for r in h: dates[r['dteday']].append(r)
    start=dt.date(year,1,1); D=(dt.date(year+1,1,1)-start).days
    expected={(start+dt.timedelta(days=i)).isoformat() for i in range(D)}
    dm={r['dteday']:r for r in d}
    a={'year':year,'hour_rows':len(h),'day_rows':len(d),'hour_dates':len(dates),'day_dates':len(dm),'hour_range':[min(dates),max(dates)],'day_range':[min(dm),max(dm)],'hour_columns':len(h[0]),'day_columns':len(d[0]),'empty_cells':{name:sum(v is None or v.strip()=='' for r in rows for v in r.values()) for name,rows in [('hour',h),('day',d)]},'duplicate_hour_keys':len(h)-len({(r['dteday'],int(r['hr'])) for r in h}),'duplicate_day_keys':len(d)-len(dm),'duplicate_instant':{name:len(rows)-len({r['instant'] for r in rows}) for name,rows in [('hour',h),('day',d)]},'count_identity_failures':{name:sum(int(r['cnt'])!=int(r['casual'])+int(r['registered']) for r in rows) for name,rows in [('hour',h),('day',d)]},'missing_dates_hour':sorted(expected-set(dates)),'missing_dates_day':sorted(expected-set(dm)),'unexpected_dates_hour':sorted(set(dates)-expected),'unexpected_dates_day':sorted(set(dm)-expected),'hours_per_date_distribution':dict(sorted(collections.Counter(map(len,dates.values())).items())),'missing_calendar_hours':{date:[hr for hr in range(24) if hr not in {int(r['hr']) for r in dates[date]}] for date in sorted(dates) if len(dates[date])!=24},'invalid_hour_values':sum(int(r['hr']) not in range(24) for r in h),'yr_values':{name:sorted({r['yr'] for r in rows}) for name,rows in [('hour',h),('day',d)]}}
    a['missing_calendar_hour_count']=sum(map(len,a['missing_calendar_hours'].values()))
    a['hour_day_count_mismatches']=[{'date':date,'column':col,'hours':sum(int(r[col]) for r in dates.get(date,[])),'day':int(row[col])} for date,row in dm.items() for col in ('casual','registered','cnt') if sum(int(r[col]) for r in dates.get(date,[]))!=int(row[col])]
    a['calendar_conflicts']=sum(any(r[c]!=dm[r['dteday']][c] for c in ('workingday','holiday','weekday','mnth','yr')) for r in h)
    a['within_date_workingday_conflicts']=sum(len({r['workingday'] for r in rows})!=1 for rows in dates.values())
    a['workingday_definition_failures']=sum(int(r['workingday'])!=int(int(r['weekday']) not in (0,6) and int(r['holiday'])==0) for r in h+d)
    a['date_calendar_failures']=sum(int(r['weekday'])!=(dt.date.fromisoformat(r['dteday']).weekday()+1)%7 or int(r['mnth'])!=dt.date.fromisoformat(r['dteday']).month or int(r['yr'])!=year-2011 for r in h+d)
    assert not any(a['empty_cells'].values()) and not any(a['count_identity_failures'].values())
    assert not a['duplicate_hour_keys'] and not a['duplicate_day_keys'] and not a['invalid_hour_values']
    assert not any(a[k] for k in ('missing_dates_hour','missing_dates_day','unexpected_dates_hour','unexpected_dates_day','hour_day_count_mismatches','calendar_conflicts','within_date_workingday_conflicts','workingday_definition_failures','date_calendar_failures'))
    a['annual_total_cnt']=sum(int(r['cnt']) for r in d)
    assert a['annual_total_cnt']==sum(int(r['cnt']) for r in h)
    a['mean_daily_cnt']=a['annual_total_cnt']/len(d)
    return a

def verify_model(h,m):
    tr=[r for r in h if '2011-01-01'<=r['dteday']<'2011-10-01']
    check={'model_sha256':EXPECTED_MODEL,'code_sha256':EXPECTED_CODE,'train_start':min(r['dteday'] for r in tr),'train_end':max(r['dteday'] for r in tr),'train_n_hours':len(tr),'train_n_dates':len({r['dteday'] for r in tr}),'all_parameters_match_original_training_records':True,'training_reperformed_for_prediction':False,'used_2012_labels_to_modify_model':False}
    for k in ('train_start','train_end','train_n_hours','train_n_dates'): assert check[k]==m[k]
    for name,cols in [('C0',('hr',)),('C1',('workingday','hr'))]:
        cells=collections.defaultdict(list)
        for r in tr: cells[':'.join(str(int(r[c])) for c in cols)].append(int(r['cnt']))
        assert set(cells)==set(m[name])
        for key,ys in cells.items():
            got=m[name][key]; assert got['n']==len(ys) and got['sum_cnt']==sum(ys) and got['mean']==sum(ys)/len(ys)
        check[name+'_cells']=len(cells)
    return check

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input-dir',type=pathlib.Path,required=True);p.add_argument('--prior-input',type=pathlib.Path,required=True)
    p.add_argument('--model',type=pathlib.Path,required=True);p.add_argument('--prior-results',type=pathlib.Path,required=True)
    p.add_argument('--original-code',type=pathlib.Path,required=True);p.add_argument('--output-dir',type=pathlib.Path,required=True)
    a=p.parse_args();start=time.time();o=a.output_dir
    if o.exists() and any(o.iterdir()): raise FileExistsError('Use new or empty output: '+str(o))
    o.mkdir(parents=True,exist_ok=True)
    code=touch(a.original_code,'workspace/analyze.py'); assert sha(code)==EXPECTED_CODE
    spec=importlib.util.spec_from_file_location('frozen_analysis',code);old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
    assert old.SEED==20261029 and old.B==2000
    m=load(a.model,'workspace/results/model.json');assert sha(a.model)==EXPECTED_MODEL
    manifest=load(a.input_dir/'INPUT_MANIFEST.json','input/INPUT_MANIFEST.json'); h={};d={};aud={}
    for y in (2011,2012):
        h[y],_=readcsv(a.input_dir/f'data/hour_{y}.csv',f'input/data-b/hour_{y}.csv')
        d[y],_=readcsv(a.input_dir/f'data/day_{y}.csv',f'input/data-b/day_{y}.csv')
        for scale,rows in [('hour',h[y]),('day',d[y])]:
            f=f'data/{scale}_{y}.csv';assert manifest[f]['sha256']==sha(a.input_dir/f) and manifest[f]['data_rows']==len(rows)
            if y==2011:
                original=touch(a.prior_input/f,f'prior-input/data-a/{scale}_{y}.csv','digest-only');assert sha(original)==sha(a.input_dir/f)
        aud[str(y)]=audit_year(h[y],d[y],y)
    assert m['source_hour_sha256']==sha(a.input_dir/'data/hour_2011.csv')
    restored=verify_model(h[2011],m)
    past=load(a.prior_results,'workspace/results/results.json')
    recovered=o/'recovery_2011';recovered.mkdir();r11=old.evaluate(h[2011],m,recovered,'2011-10-01','2011-12-31')
    assert r11==past;restored['2011_holdout_exact_result_match']=True
    for file in ('predictions.csv','daily_errors.csv','bootstrap_7.csv','bootstrap_28.csv'):
        prev=touch(a.prior_results.parent/file,'workspace/results/'+file,'digest-only')
        assert sha(prev)==sha(recovered/file)
    res=old.evaluate(h[2012],m,o,'2012-01-01','2012-12-31')
    assert sha(a.model)==EXPECTED_MODEL and sha(code)==EXPECTED_CODE
    annual={'years':{y:{k:aud[y][k] for k in ('annual_total_cnt','mean_daily_cnt','day_rows','hour_rows')} for y in aud},'total_count_growth':aud['2012']['annual_total_cnt']/aud['2011']['annual_total_cnt']-1,'daily_mean_growth':aud['2012']['mean_daily_cnt']/aud['2011']['mean_daily_cnt']-1,'daily_mean_growth_identity':'(1+total_count_growth)*365/366 - 1'}
    save(o/'audit.json',aud);save(o/'annual_summary.json',annual);save(o/'model_recovery.json',restored)
    rows=[]
    for label,r in [('2011_holdout',past),('2012_all',res)]:
        for scope,z in [('all',r['all']),('complete_24h_dates',r['complete_24h_dates']),('workingday_0',r['workingday']['0']),('workingday_1',r['workingday']['1'])]:
            rows.append({'evaluation':label,'scope':scope,**{k:z[k] for k in ('n_hours','n_dates','MAE_difference_C0_minus_C1','relative_MAE_reduction','date_equal_MAE_difference','date_equal_relative_MAE_reduction')},**{model+'_'+k:v for model in ('C0','C1') for k,v in z[model].items()}})
    old.csvout(o/'comparison_metrics.csv',rows)
    save(o/'provenance.json',{'argv':sys.argv,'reads':READS,'frozen_model_sha256':sha(a.model),'frozen_scoring_code_sha256':sha(code),'update_code_sha256':sha(__file__),'python':sys.version,'platform':platform.platform(),'seed':old.SEED,'B':old.B,'retrained':False,'network':False,'elapsed_seconds':time.time()-start})
    print(json.dumps({'annual':annual,'audit':{y:{k:v for k,v in a.items() if k!='missing_calendar_hours'} for y,a in aud.items()},'recovery':restored,'2012':res},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
