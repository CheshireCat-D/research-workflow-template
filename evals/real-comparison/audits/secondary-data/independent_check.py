from pathlib import Path
import collections, csv, hashlib, json, math, random, subprocess, sys
BASE=Path('STUDY_ROOT/blind')
OUT=Path('DATA_REVIEW_WORK')
PYTHON='STUDY_ROOT/env/bin/python'
CHAINS={'P':('S733011','Sb68670'),'Q':('Sdfb334','S924971'),'R':('S3f44a8','S127718')}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):
 with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def load(p):return json.loads(p.read_text())
# Only the six assigned packages are read. No adjudication, templates or execution logs.
source=BASE/'Sb68670/input/data'
raw={y:{s:read(source/f'{s}_{y}.csv') for s in ('hour','day')} for y in (2011,2012)}
train=[r for r in raw[2011]['hour'] if '2011-01-01'<=r['dteday']<'2011-10-01']
tables={'C0':collections.defaultdict(list),'C1':collections.defaultdict(list)}
for r in train:
 tables['C0'][r['hr']].append(int(r['cnt']))
 tables['C1'][(r['workingday'],r['hr'])].append(int(r['cnt']))
truth={family:{key:{'sum':sum(v),'n':len(v),'mean':sum(v)/len(v)} for key,v in cells.items()} for family,cells in tables.items()}
def predictions(rows):
 result=[]
 for r in rows:
  y=int(r['cnt']); ps=[truth['C0'][r['hr']]['mean'],truth['C1'][(r['workingday'],r['hr'])]['mean']]
  result.append({'date':r['dteday'],'hr':int(r['hr']),'w':int(r['workingday']),'y':y,'p':ps,'e':[p-y for p in ps]})
 return result
def summarize(rs):
 ds=collections.defaultdict(list)
 for r in rs:ds[r['date']].append(r)
 m={}
 for i in (0,1):
  e=[r['e'][i] for r in rs]
  m[f'C{i}']={'MAE':math.fsum(map(abs,e))/len(rs),'RMSE':math.sqrt(math.fsum(x*x for x in e)/len(rs)),'bias':math.fsum(e)/len(rs),'day_MAE':math.fsum(math.fsum(abs(r['e'][i]) for r in day)/len(day) for day in ds.values())/len(ds)}
 m.update(hours=len(rs),days=len(ds),difference=m['C0']['MAE']-m['C1']['MAE'],relative=1-m['C1']['MAE']/m['C0']['MAE'],day_difference=m['C0']['day_MAE']-m['C1']['day_MAE'],day_relative=1-m['C1']['day_MAE']/m['C0']['day_MAE'])
 return m
def boot(rs,L):
 ds=collections.defaultdict(list)
 for r in rs:ds[r['date']].append(r)
 dates=sorted(ds);D=len(dates);daily=[]
 for d in dates:
  day=ds[d];daily.append((len(day),math.fsum(abs(r['e'][0]) for r in day),math.fsum(abs(r['e'][1]) for r in day)))
 rng=random.Random(20261029);rep=[]
 for k in range(2000):
  # Stream each selected date, explicitly truncating the last block.
  selected=[]
  while len(selected)<D:
   start=rng.randrange(D)
   selected.extend(daily[(start+j)%D] for j in range(min(L,D-len(selected))))
  n=sum(v[0] for v in selected); m0=math.fsum(v[1] for v in selected)/n;m1=math.fsum(v[2] for v in selected)/n
  rep.append([n,m0,m1,m0-m1,1-m1/m0])
 def q(i,p):
  v=sorted(r[i] for r in rep);x=1999*p;lo=math.floor(x);return v[lo]+(x-lo)*(v[math.ceil(x)]-v[lo])
 return {'difference_CI':[q(3,.025),q(3,.975)],'relative_CI':[q(4,.025),q(4,.975)]},rep
independent={};prediction_sets={};bootstrap_reps={};audit={}
for y in (2011,2012):
 h=raw[y]['hour'];d=raw[y]['day'];ds=collections.defaultdict(list)
 for r in h:ds[r['dteday']].append(r)
 dm={r['dteday']:r for r in d};year_days=365 if y==2011 else 366
 audit[y]={'hour_rows':len(h),'day_rows':len(d),'hour_dates':len(ds),'missing_hours':24*year_days-len(h),'hours_per_date':dict(sorted(collections.Counter(map(len,ds.values())).items())),'duplicate_hour_keys':len(h)-len({(r['dteday'],r['hr']) for r in h}),'duplicate_day_keys':len(d)-len(dm),'blank_cells':sum(v is None or v=='' for r in h+d for v in r.values()),'identity_failures':sum(int(r['cnt'])!=int(r['casual'])+int(r['registered']) for r in h+d),'hour_day_mismatches':sum(sum(int(r[c]) for r in rs)!=int(dm[day][c]) for day,rs in ds.items() for c in ('cnt','casual','registered')),'total':sum(int(r['cnt']) for r in d),'daily_mean':sum(int(r['cnt']) for r in d)/year_days,'rare_partial_dates':[{'date':day,'hours':len(rs),'count':sum(int(r['cnt']) for r in rs)} for day,rs in ds.items() if len(rs)<12]}
 rows=h if y==2012 else [r for r in h if r['dteday']>='2011-10-01']
 ps=predictions(rows);prediction_sets[y]=ps;counts=collections.Counter(r['date'] for r in ps)
 result={'all':summarize(ps),'complete':summarize([r for r in ps if counts[r['date']]==24]),'workingday':{str(w):summarize([r for r in ps if r['w']==w]) for w in (0,1)},'bootstrap':{}}
 for L in (7,28):result['bootstrap'][str(L)],bootstrap_reps[y,L]=boot(ps,L)
 independent[y]=result

def normalize_metrics(m,chain):
 if chain=='P':
  keys=['MAE','RMSE','bias_prediction_minus_actual','day_equal_MAE'];nums=['n_hours','n_dates','hour_weighted_absolute_improvement','hour_weighted_relative_improvement','day_equal_absolute_improvement','day_equal_relative_improvement']
 elif chain=='Q':
  keys=['hour_weighted_MAE','hour_weighted_RMSE','mean_bias_pred_minus_true','date_equal_mean_intraday_MAE'];nums=['n_hours','n_dates','MAE_difference_C0_minus_C1','relative_MAE_reduction','date_equal_MAE_difference','date_equal_relative_MAE_reduction']
 else:
  keys=['MAE','RMSE','mean_bias_prediction_minus_actual','day_equal_mean_intraday_MAE'];nums=['hours','dates','MAE_absolute_difference_C0_minus_C1','MAE_relative_reduction','day_equal_absolute_difference_C0_minus_C1','day_equal_relative_reduction']
 out={model:dict(zip(['MAE','RMSE','bias','day_MAE'],[m[model][k] for k in keys])) for model in ('C0','C1')}
 out.update(zip(['hours','days','difference','relative','day_difference','day_relative'],[m[k] for k in nums]));return out

def distances(x,y):
 if isinstance(x,dict):return [z for k in x for z in distances(x[k],y[k])]
 if isinstance(x,list):return [z for a,b in zip(x,y) for z in distances(a,b)]
 return [abs(x-y)]
packages={}
for chain,(sa,sb) in CHAINS.items():
 for stage,sid,y in [('A',sa,2011),('B',sb,2012)]:
  p=BASE/sid;work=p/'work';modelpath=work/'model.json' if chain=='P' else work/'results/model.json'
  resultdir=work if chain=='P' and stage=='A' else work/'stage_b_results' if chain=='P' else work/'results' if stage=='A' else work/'results_2012' if chain=='Q' else work/'results2012'
  model=load(modelpath);stored=load(resultdir/'results.json');max_model_error=0
  for family in ('C0','C1'):
   assert len(model[family])==len(truth[family])
   for key,cell in model[family].items():
    normalized=tuple(key.replace(':',',').split(',')) if family=='C1' else key
    t=truth[family][normalized]
    assert cell.get('sum',cell.get('sum_cnt'))==t['sum'] and cell['n']==t['n']
    max_model_error=max(max_model_error,abs(cell['mean']-t['mean']))
  main_key={'P':'overall','Q':'all','R':'all_observed'}[chain]
  wd_key='by_workingday' if chain=='P' else 'workingday'
  all_norm={'all':normalize_metrics(stored[main_key],chain),'complete':normalize_metrics(stored['complete_24h_dates'],chain),'workingday':{w:normalize_metrics(stored[wd_key][w],chain) for w in ('0','1')},'bootstrap':{}}
  for L in (7,28):
   z=stored['bootstrap'][str(L)] if chain!='R' else next(z for z in stored['bootstrap'] if z['block_days']==L)
   abskey={'P':'absolute_improvement_95ci','Q':'difference_CI95','R':'absolute_difference_CI95'}[chain]
   relkey='relative_improvement_95ci' if chain=='P' else 'relative_reduction_CI95'
   all_norm['bootstrap'][str(L)]={'difference_CI':z[abskey],'relative_CI':z[relkey]}
  max_result_error=max(distances(independent[y],all_norm));assert max_result_error<1e-9
  pred=read(resultdir/'predictions.csv');expected=prediction_sets[y];assert len(pred)==len(expected)
  pred_error=0
  for r,t in zip(pred,expected):
   assert r.get('date',r.get('dteday'))==t['date'] and int(r['hr'])==t['hr'] and int(r['workingday'])==t['w'] and int(r.get('actual',r.get('cnt')))==t['y']
   pred_error=max(pred_error,abs(float(r['C0'])-t['p'][0]),abs(float(r['C1'])-t['p'][1]))
  boot_error=0
  for L in (7,28):
   filename=f'bootstrap_L{L}.csv' if chain=='P' else f'bootstrap_{L}.csv' if chain=='Q' else f'bootstrap_{L}d.csv'
   rows=read(resultdir/filename);assert len(rows)==2000
   keys={'P':['n_sampled_hours','MAE_C0','MAE_C1','absolute_improvement','relative_improvement'],'Q':['n_hours','C0_MAE','C1_MAE','difference','relative_reduction'],'R':['hours','MAE0','MAE1','absolute_difference','relative_reduction']}[chain]
   for row,expectedrow in zip(rows,bootstrap_reps[y,L]):
    boot_error=max(boot_error,*[abs(float(row[k])-v) for k,v in zip(keys,expectedrow)])
  assert pred_error==0 and boot_error<1e-9
  input_checks={}
  for file in (p/'input/data').glob('*.csv'):
   year=int(file.stem.split('_')[1]);scale=file.stem.split('_')[0]
   input_checks[file.name]=sha(file)==sha(source/file.name)
  assert all(input_checks.values())
  item={'chain':chain,'stage':stage,'report_sha256':sha(p/'report.md'),'report_characters':len((p/'report.md').read_text()),'handoff_sha256':sha(work/'handoff.md'),'model_sha256':sha(modelpath),'model_cells':72,'max_model_parameter_error':max_model_error,'max_result_error':max_result_error,'prediction_rows_checked':len(pred),'max_prediction_error':pred_error,'bootstrap_replicates_checked':4000,'max_bootstrap_error':boot_error,'input_hashes_match_common_data':input_checks,'result_directory':str(resultdir.relative_to(p))}
  if stage=='B':
   original=BASE/sa;original_model=original/'work/model.json' if chain=='P' else original/'work/results/model.json'
   item['A_B_model_bytes_equal']=sha(modelpath)==sha(original_model)
   item['previous_report_matches_A']=sha(p/'previous-report.md')==sha(original/'report.md')
   item['previous_handoff_matches_A']=sha(p/'previous-handoff.md')==sha(original/'work/handoff.md')
   assert item['A_B_model_bytes_equal'] and item['previous_report_matches_A'] and item['previous_handoff_matches_A']
  packages[sid]=item
reference=load(BASE/'S733011/numbers.json')
reference_checks={}
for phase,y in [('phase1',2011),('phase2',2012)]:
 r=reference[phase];refm=r['overall'];reference_checks[phase]={'overall':refm,'bootstrap7':r['bootstrap7'],'bootstrap28':r['bootstrap28']}
for y in (2011,2012):print(y,json.dumps(independent[y],ensure_ascii=False))
# Relocation checks invoke delivered programs with fresh output paths, without rewriting source or first outputs.
commands={
 'P_A_score':[str(BASE/'S733011/work/analysis.py'),'--mode','score','--input-dir',str(BASE/'Sb68670/input'),'--hour-file','hour_2012.csv','--model',str(BASE/'S733011/work/model.json'),'--output-dir',str(OUT/'P_A_score')],
 'Q_A_score':[str(BASE/'Sdfb334/work/analyze.py'),'score','--hour-file',str(source/'hour_2012.csv'),'--model',str(BASE/'Sdfb334/work/results/model.json'),'--output-dir',str(OUT/'Q_A_score'),'--start','2012-01-01','--end','2012-12-31'],
 'R_A_score':[str(BASE/'S3f44a8/work/analyze.py'),'score','--hour-csv',str(source/'hour_2012.csv'),'--model',str(BASE/'S3f44a8/work/results/model.json'),'--output-dir',str(OUT/'R_A_score')],
 'P_B_update':[str(BASE/'Sb68670/work/stage_b.py'),'--input-dir',str(BASE/'Sb68670/input'),'--prior-dir',str(BASE/'Sb68670/work/stage_a_snapshot'),'--model',str(BASE/'Sb68670/work/model.json'),'--output-dir',str(OUT/'P_B_update')],
 'Q_B_update':[str(BASE/'S924971/work/update2012.py'),'--input-dir',str(BASE/'S924971/input'),'--prior-input',str(BASE/'Sdfb334/input'),'--model',str(BASE/'S924971/work/results/model.json'),'--prior-results',str(BASE/'S924971/work/results/results.json'),'--original-code',str(BASE/'S924971/work/analyze.py'),'--output-dir',str(OUT/'Q_B_update')],
 'R_B_update':[str(BASE/'S127718/work/update_2012.py'),'--input-dir',str(BASE/'S127718/input'),'--model',str(BASE/'S127718/work/results/model.json'),'--prior-results',str(BASE/'S127718/work/results'),'--output-dir',str(OUT/'R_B_update')]
}
runs={}
for name,args in commands.items():
 completed=subprocess.run([PYTHON,'-I','-B',*args],capture_output=True,text=True,cwd=OUT)
 runs[name]={'returncode':completed.returncode,'arguments':args,'stderr':completed.stderr[:3000]}
 if completed.returncode==0:
  chain=name[0];generated=load(OUT/name/'results.json');sid=CHAINS[chain][1]
  resultdir=BASE/sid/packages[sid]['result_directory']
  runs[name]['results_equal_delivered_2012']=generated==load(resultdir/'results.json')
 print('RELOCATION',name,json.dumps(runs[name],ensure_ascii=False))
 assert completed.returncode==0 and runs[name]['results_equal_delivered_2012']
summary={'method':'Independent standard-library calculation from the assigned CSV inputs, without importing author analysis for the independent calculation. Delivered code separately executed only to fresh reviewer output directories.','train':{'hours':len(train),'dates':len({r['dteday'] for r in train}),'count_total':sum(int(r['cnt']) for r in train)},'audit':audit,'annual_total_growth':audit[2012]['total']/audit[2011]['total']-1,'daily_mean_growth':audit[2012]['daily_mean']/audit[2011]['daily_mean']-1,'independent_results':independent,'packages':packages,'relocation_runs':runs,'reference_checks':reference_checks}
(OUT/'independent_checks.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print('ALL CHECKS PASSED')
