from pathlib import Path
import argparse,csv,hashlib,io,json,math,sys

def main():
 p=argparse.ArgumentParser(description='Read-only independent numeric and binding verification, not scientific approval');p.add_argument('--root',type=Path,default=Path(__file__).resolve().parent.parent);a=p.parse_args();r=a.root.resolve()
 def load(n):return json.loads((r/n).read_text(encoding='utf-8'))
 def identity(n):
  b=(r/n).read_bytes();return {'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
 errors=[]
 s=load('management/state.json');q=load('notes/parameters.json');result=load('results/result.json');model=load('model/frozen.json')
 auth=load('management/evidence/C/authorization/approved-parameters.json')
 if q!=auth or s['active_constraints']['current_scope']!=q:errors.append('Parameter/authorization/active scope mismatch')
 if q['model_policy']!='frozen-2011-Jan-Sep' or q['metric_weighting']!='observed-hour':errors.append('Unsupported model policy or weighting')
 rows=list(csv.DictReader(io.StringIO((r/'data/hour_2011.csv').read_text(encoding='utf-8'))));rows=[x for x in rows if q['evaluation_start']<=x['dteday']<=q['evaluation_end']]
 expected={'observed_hours':len(rows),'observed_days':len({x['dteday'] for x in rows})}
 for c in ['C0','C1']:
  errs=[]
  for x in rows:
   y=model[c][x['hr']] if c=='C0' else model[c].get(x['workingday']+':'+x['hr'],model['C0'][x['hr']]);errs.append(y-int(x['cnt']))
  expected[c+'_MAE']=math.fsum(abs(v) for v in errs)/len(errs);expected[c+'_RMSE']=math.sqrt(math.fsum(v*v for v in errs)/len(errs));expected[c+'_bias_prediction_minus_actual']=math.fsum(errs)/len(errs)
 expected['MAE_reduction_fraction']=1-expected['C1_MAE']/expected['C0_MAE']
 for k,v in expected.items():
  if not math.isclose(result[k],v,rel_tol=1e-13,abs_tol=1e-13):errors.append('Numeric mismatch '+k)
 for k in ['evaluation_start','evaluation_end','model_policy','case_id']:
  if result[k]!=q[k]:errors.append('Result parameter mismatch '+k)
 for k,n in {'parameters':'notes/parameters.json','calculator':'scripts/compute.py','hour_2011':'data/hour_2011.csv','frozen_model':'model/frozen.json'}.items():
  if result['input_sha256'][k]!=identity(n)['sha256']:errors.append('Result input hash mismatch '+k)
 table=list(csv.DictReader(io.StringIO((r/'results/table.csv').read_text(encoding='utf-8'))))
 needed={'observed_hours','observed_days','C0_MAE','C1_MAE','C0_RMSE','C1_RMSE','MAE_reduction_fraction'}
 if len(table)!=len(needed) or {x['metric'] for x in table}!=needed:errors.append('Table metric coverage mismatch')
 for x in table:
  if not math.isclose(float(x['value']),result[x['metric']],rel_tol=1e-13,abs_tol=1e-13):errors.append('Table mismatch '+x['metric'])
 for aid,activity in s['activities'].items():
  for n,ref in activity['bound_materials'].items():
   if identity(n)!=ref:errors.append('Activity binding mismatch '+aid+':'+n)
 baseline=load('management/checkpoints/C-pre-recompute/checkpoint.json');before={x['path']:x for x in baseline['manifest']}
 for n in ['data/hour_2011.csv','scripts/compute.py','model/frozen.json','management/source-identities.json','notes/source-check.md']:
  if identity(n)['sha256']!=before[n]['sha256']:errors.append('Protected primary/code/model changed '+n)
 summary=(r/'results/summary.md').read_text(encoding='utf-8')
 for token in ['2011-11-01','2011-12-31',str(result['observed_hours']),str(result['observed_days']),f"{result['C0_MAE']:.12f}",f"{result['C1_MAE']:.12f}",f"{100*result['MAE_reduction_fraction']:.8f}"]:
  if token not in summary:errors.append('Summary missing '+token)
 answer={'passed':not errors,'errors':errors,'independent_metrics':expected,'table_agrees':not any('Table' in e for e in errors),'activities_checked':list(s['activities']),'writes_project':False,'interpretation':'Numeric and local binding verification only; author content review remains pending.'};print(json.dumps(answer,ensure_ascii=False,indent=2));return 0 if not errors else 4
if __name__=='__main__':
 try:raise SystemExit(main())
 except (OSError,ValueError,KeyError,TypeError,ZeroDivisionError) as e:
  print(json.dumps({'passed':False,'error':type(e).__name__,'message':str(e)},ensure_ascii=False));raise SystemExit(4)
