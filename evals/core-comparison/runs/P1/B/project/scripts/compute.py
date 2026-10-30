#!/usr/bin/env python3
"""Tiny supplied scientific calculator; not a registry or state-recovery program."""
import argparse,csv,hashlib,json,math,sys
from pathlib import Path

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def calculate(root,spec):
 case=spec['case_id']
 if case=='T':
  alpha=float(spec['alpha']);rho=float(spec['rho']);grid=spec['intrinsic_time_grid']
  if not 0<alpha<1 or not rho>0 or not all(isinstance(v,(int,float)) and math.isfinite(v) and v>=0 for v in grid):raise ValueError('Require 0<alpha<1, rho>0 and finite nonnegative intrinsic times')
  if spec['rho_selection']!='fixed-before-observation':raise ValueError('This calculator is authorized only for fixed-before-observation rho')
  values=[{'v':v,'boundary':math.sqrt((v+rho)*(math.log1p(v/rho)+2*math.log(1/alpha)))} for v in grid]
  return {'case_id':'T','alpha':alpha,'rho':rho,'rho_selection':spec['rho_selection'],'values':values,'interpretation':'Numerical boundary evaluation under the supplied fixed-parameter theorem; no new proof or coverage simulation.'}
 if case=='D':
  start=spec['evaluation_start'];end=spec['evaluation_end']
  if start>end:raise ValueError('evaluation_start must be no later than evaluation_end')
  if spec['model_policy']!='frozen-2011-Jan-Sep':raise ValueError('This calculator only scores the supplied frozen model')
  model=load(root/'model/frozen.json')
  with (root/'data/hour_2011.csv').open(newline='',encoding='utf-8') as f:rows=[r for r in csv.DictReader(f) if start<=r['dteday']<=end]
  if not rows:raise ValueError('No observed hours in evaluation range')
  abs0=[];abs1=[];sq0=[];sq1=[];bias0=[];bias1=[]
  for r in rows:
   y=int(r['cnt']);a=model['C0'][r['hr']];b=model['C1'].get(r['workingday']+':'+r['hr'],a)
   abs0.append(abs(a-y));abs1.append(abs(b-y));sq0.append((a-y)**2);sq1.append((b-y)**2);bias0.append(a-y);bias1.append(b-y)
  n=len(rows);a=math.fsum(abs0)/n;b=math.fsum(abs1)/n
  return {'case_id':'D','evaluation_start':start,'evaluation_end':end,'model_policy':spec['model_policy'],'observed_hours':n,'observed_days':len({r['dteday'] for r in rows}),'C0_MAE':a,'C1_MAE':b,'C0_RMSE':math.sqrt(math.fsum(sq0)/n),'C1_RMSE':math.sqrt(math.fsum(sq1)/n),'C0_bias_prediction_minus_actual':math.fsum(bias0)/n,'C1_bias_prediction_minus_actual':math.fsum(bias1)/n,'MAE_reduction_fraction':1-b/a,'interpretation':'Observed-hour descriptive comparison under the supplied frozen model; no refit, no confidence interval, causal or future-year guarantee.'}
 raise ValueError('Unknown case_id')
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--output',required=True);p.add_argument('--spec');args=p.parse_args();root=Path(args.root).resolve();out=Path(args.output)
 try:
  sp=Path(args.spec) if args.spec else root/'notes/parameters.json';spec=load(sp);result=calculate(root,spec)
  result['input_sha256']={'parameters':digest(sp),'calculator':digest(Path(__file__))}
  if spec['case_id']=='D':result['input_sha256'].update({'hour_2011':digest(root/'data/hour_2011.csv'),'frozen_model':digest(root/'model/frozen.json')})
  if out.exists():raise ValueError('Output directory must not exist; preserve prior outputs')
  out.mkdir(parents=True);save(out/'result.json',result)
  with (out/'table.csv').open('w',newline='',encoding='utf-8') as f:
   if spec['case_id']=='T':w=csv.DictWriter(f,fieldnames=['v','boundary']);w.writeheader();w.writerows(result['values'])
   else:w=csv.writer(f);w.writerow(['metric','value']);w.writerows((k,result[k]) for k in ['observed_hours','observed_days','C0_MAE','C1_MAE','C0_RMSE','C1_RMSE','MAE_reduction_fraction'])
  print(json.dumps({'passed':True,'result':str(out/'result.json'),'parameters_sha256':result['input_sha256']['parameters']}));return 0
 except (OSError,ValueError,KeyError,TypeError) as e:
  print(json.dumps({'passed':False,'error':type(e).__name__,'message':str(e)}),file=sys.stderr);return 2
if __name__=='__main__':raise SystemExit(main())
