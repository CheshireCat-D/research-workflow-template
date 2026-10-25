#!/usr/bin/env python3
"""Offline deterministic estimands for two independent synthetic examples (stdlib)."""
from pathlib import Path
from fractions import Fraction
import argparse,csv,hashlib,json,platform,sys,time,traceback

ROOT=Path(__file__).resolve().parents[1]
PARAMETERS={'medical_endpoint':'30-day recorded recovery','contrast':'treated minus usual','standard_population':'pooled severity distribution across the 240 synthetic subjects','policy_baseline_year':2023,'policy_endpoint_years':[2024,2025],'policy_pretrend_years':[2022,2023],'policy_contrast':'(A endpoint - A baseline) - (B endpoint - B baseline)','randomness':'none','inference':'descriptive exact arithmetic; no sampling or causal uncertainty model'}

def number(q):
 q=Fraction(q)
 return {'exact':str(q),'value':float(q)}

def proportion(q):
 return {**number(q),'percent':float(100*q),'unit':'proportion (percent also supplied)'}

def risk_difference(q):
 return {**number(q),'percentage_points':float(100*q),'unit':'proportion difference (percentage points also supplied)'}

def rows(name):
 with (ROOT/'inputs'/name).open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))

def calculate():
 raw=rows('medical-strata.csv');cells={}
 for r in raw:
  key=(r['stratum'],r['treatment']);n=int(r['n']);events=int(r['event_count'])
  if key in cells or n<=0 or not 0<=events<=n:raise ValueError('Duplicate or invalid medical cell')
  cells[key]=(n,events)
 if set(cells)!={(s,t) for s in ('mild','severe') for t in ('treated','usual')}:raise ValueError('Incomplete medical 2x2 cells')
 groups={}
 for treatment in ('treated','usual'):
  n=sum(v[0] for k,v in cells.items() if k[1]==treatment);events=sum(v[1] for k,v in cells.items() if k[1]==treatment)
  groups[treatment]={'n':n,'event_count':events,'recovery':proportion(Fraction(events,n))}
 total=sum(x[0] for x in cells.values());weights={s:Fraction(sum(v[0] for k,v in cells.items() if k[0]==s),total) for s in ('mild','severe')}
 strata={}
 for s in ('mild','severe'):
  rates={t:Fraction(cells[s,t][1],cells[s,t][0]) for t in ('treated','usual')}
  strata[s]={'cells':{t:{'n':cells[s,t][0],'event_count':cells[s,t][1],'recovery':proportion(rates[t])} for t in ('treated','usual')},'risk_difference':risk_difference(rates['treated']-rates['usual']),'pooled_n':sum(cells[s,t][0] for t in ('treated','usual')),'pooled_weight':number(weights[s])}
 standardized={t:sum(weights[s]*Fraction(cells[s,t][1],cells[s,t][0]) for s in weights) for t in ('treated','usual')}
 medical={'target':'Observed synthetic table subjects; standardized values use pooled severity composition, not all patients','endpoint':'30-day recovery','total_n':total,'groups':groups,'crude_risk_difference':risk_difference(Fraction(groups['treated']['event_count'],groups['treated']['n'])-Fraction(groups['usual']['event_count'],groups['usual']['n'])),'strata':strata,'standardized_recovery':{t:proportion(q) for t,q in standardized.items()},'standardized_risk_difference':risk_difference(standardized['treated']-standardized['usual'])}
 policy={}
 for r in rows('policy-periods.csv'):
  key=(r['town'],int(r['year']))
  if key in policy:raise ValueError('Duplicate policy town-year')
  active=int(r['program_active']);y=Fraction(r['outcome_index_points'])
  if active!=int(key[0]=='A' and key[1]>=2024):raise ValueError('Unexpected program timing')
  policy[key]=y
 if set(policy)!={(town,year) for town in ('A','B') for year in range(2022,2026)}:raise ValueError('Incomplete policy town-year cells')
 def changes(start,end):
  delta={t:policy[t,end]-policy[t,start] for t in ('A','B')}
  return {'baseline_year':start,'endpoint_year':end,'unit':'index points','A_change':number(delta['A']),'B_change':number(delta['B']),'difference_in_changes_A_minus_B':number(delta['A']-delta['B'])}
 policy_result={'target':'Two synthetic town-level annual opportunity indices; not individual outcomes','unit':'index points','values':{t:{str(y):number(policy[t,y]) for y in range(2022,2026)} for t in ('A','B')},'primary_2023_to_2024':changes(2023,2024),'pretrend_2022_to_2023':changes(2022,2023),'alternative_endpoint_2023_to_2025':changes(2023,2025),'post_increment_2024_to_2025':changes(2024,2025)}
 # Hand-calculated independent arithmetic anchors, fixed before this run.
 anchors={'medical_treated_total':groups['treated']['event_count']==84 and groups['treated']['n']==120,'medical_usual_total':groups['usual']['event_count']==48 and groups['usual']['n']==120,'standardization':standardized['treated']==Fraction(1,2) and standardized['usual']==Fraction(3,5),'policy_primary':policy_result['primary_2023_to_2024']['difference_in_changes_A_minus_B']['exact']=='1','policy_pretrend':policy_result['pretrend_2022_to_2023']['difference_in_changes_A_minus_B']['exact']=='-3','policy_alternative':policy_result['alternative_endpoint_2023_to_2025']['difference_in_changes_A_minus_B']['exact']=='-1'}
 if not all(anchors.values()):raise AssertionError(anchors)
 return {'medical':medical,'policy':policy_result,'arithmetic_anchors':anchors}

def main():
 p=argparse.ArgumentParser();p.add_argument('--output',default='artifacts/results.json');a=p.parse_args()
 output=Path(a.output)
 if output.is_absolute() or '..' in output.parts:raise ValueError('Output must be project relative')
 start=time.perf_counter();result={'schema_version':'1','synthetic':True,'parameters':PARAMETERS,'environment':{'python':platform.python_version(),'implementation':platform.python_implementation(),'platform':platform.platform(),'machine':platform.machine(),'dependencies':'Python standard library only','network_used':False},'input_fingerprints':{}}
 for name in ('task.md','design-note.md','medical-strata.csv','policy-periods.csv'):
  data=(ROOT/'inputs'/name).read_bytes();result['input_fingerprints']['inputs/'+name]={'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}
 try:
  result.update(calculate());result['status']='success';result['failures']=[];code=0
 except Exception as e:
  result.update(status='failed',failures=[{'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()}]);code=1
 result['elapsed_seconds']=time.perf_counter()-start
 if result['elapsed_seconds']>=10:result['failures'].append({'type':'BudgetExceeded','message':'Run reached 10 seconds'});result['status']='failed';code=1
 (ROOT/output).parent.mkdir(parents=True,exist_ok=True);(ROOT/output).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'status':result['status'],'output':output.as_posix(),'elapsed_seconds':result['elapsed_seconds'],'failures':result['failures']},ensure_ascii=False))
 return code
if __name__=='__main__':sys.exit(main())
