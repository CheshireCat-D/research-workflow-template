import ast
import collections
import csv
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import random
import subprocess

BASE=Path('STUDY_ROOT')
ROOT=BASE/'numeric-replays'
REFROOT=Path('EVALUATION_ROOT')
RAW=Path('RAW_DATA_DIR')
PLAN=json.loads((BASE/'numeric-audit-plan.json').read_text())
REF=json.loads((REFROOT/'references/data-numbers.json').read_text())
MODEL=json.loads((REFROOT/'references/data-model.json').read_text())
TOL=1e-10
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p): return json.loads(p.read_text())
def rows(p):
    with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')

# Execute the provided reference independently into a new directory as well.
reference_out=ROOT/'reference-replay'
attempt=1
while reference_out.exists():
    attempt+=1
    reference_out=ROOT/f'reference-replay-{attempt}'
reference_argv=[str(BASE/'env/bin/python'),'-I','-B',str(REFROOT/'reference_data.py'),
                '--raw-dir',str(RAW),'--output',str(reference_out)]
with (ROOT/f'reference-{attempt}-stdout.log').open('w') as o,(ROOT/f'reference-{attempt}-stderr.log').open('w') as e:
    reference_exit=subprocess.run(reference_argv,stdout=o,stderr=e).returncode
assert reference_exit==0
assert load(reference_out/'reference_answers.json')==REF
assert load(reference_out/'reference_frozen_model.json')==MODEL

spec=importlib.util.spec_from_file_location('independent_reference',REFROOT/'reference_data.py')
reference=importlib.util.module_from_spec(spec);spec.loader.exec_module(reference)
hours=rows(RAW/'hour.csv');days=rows(RAW/'day.csv')
train=[r for r in hours if '2011-01-01'<=r['dteday']<'2011-10-01']
periods={'phase1':[r for r in hours if '2011-10-01'<=r['dteday']<'2012-01-01'],
         'phase2':[r for r in hours if '2012-01-01'<=r['dteday']<'2013-01-01']}

class Checks:
    def __init__(self):self.items=[]
    def add(self,name,actual,expected):
        if isinstance(expected,(float,int)) and not isinstance(expected,bool):
            error=abs(actual-expected)
            ok=math.isfinite(float(actual)) and error<=TOL
        else:error=0 if actual==expected else None;ok=actual==expected
        self.items.append({'field':name,'actual':actual,'expected':expected,'absolute_error':error,'passed':ok})
    def report(self):
        numeric=[x for x in self.items if x['absolute_error'] is not None]
        max_error=max([x['absolute_error'] for x in numeric],default=0)
        return {'checked_fields':len(self.items),'failures':[x for x in self.items if not x['passed']],
                'max_absolute_error':max_error,
                'max_error_fields':[x for x in numeric if x['absolute_error']==max_error][:10],
                'all_checks':self.items}

def canonical_metric(z,style):
    maps={
      'one':('n_hours','n_dates','MAE','RMSE','bias_prediction_minus_actual','day_equal_MAE',
             'hour_weighted_absolute_improvement','hour_weighted_relative_improvement',
             'day_equal_absolute_improvement','day_equal_relative_improvement'),
      'two':('n_hours','n_dates','hour_weighted_MAE','hour_weighted_RMSE','mean_bias_pred_minus_true','date_equal_mean_intraday_MAE',
             'MAE_difference_C0_minus_C1','relative_MAE_reduction','date_equal_MAE_difference','date_equal_relative_MAE_reduction'),
      'three':('hours','dates','MAE','RMSE','mean_bias_prediction_minus_actual','day_equal_mean_intraday_MAE',
             'MAE_absolute_difference_C0_minus_C1','MAE_relative_reduction','day_equal_absolute_difference_C0_minus_C1','day_equal_relative_reduction')}
    h,d,mae,rmse,bias,de,delta,rel,dedelta,derel=maps[style]
    result={'hours':z[h],'days':z[d],
            'MAE_reduction_absolute':z[delta],'MAE_reduction_fraction':z[rel],
            'day_equal_weight_mean_MAE_difference':z[dedelta],
            'day_equal_weight_MAE_reduction_fraction':z[derel]}
    for m in ('C0','C1'):
        for key,old in [('MAE',mae),('RMSE',rmse),('bias_prediction_minus_actual',bias),('day_equal_weight_MAE',de)]:
            result[m+'_'+key]=z[m][old]
    return result

def scopes(z,style):
    if style=='one':return {'overall':z['overall'],'full24_dates_sensitivity':z['complete_24h_dates'],
                            **{'workingday='+k:v for k,v in z['by_workingday'].items()}}
    return {'overall':z['all' if style=='two' else 'all_observed'],
            'full24_dates_sensitivity':z['complete_24h_dates'],
            **{'workingday='+k:v for k,v in z['workingday'].items()}}

def compare_metrics(z,style,phase):
    c=Checks()
    for scope,value in scopes(z,style).items():
        target=REF[phase]['subgroups'][scope] if scope.startswith('workingday=') else REF[phase][scope]
        for k,v in canonical_metric(value,style).items():c.add(scope+'/'+k,v,target[k])
    bs={str(x['block_days']):x for x in z['bootstrap']} if style=='three' else z['bootstrap']
    for length,item in bs.items():
        target=REF[phase]['bootstrap'+length]
        abskey={'one':'absolute_improvement_95ci','two':'difference_CI95','three':'absolute_difference_CI95'}[style]
        relkey='relative_improvement_95ci' if style=='one' else 'relative_reduction_CI95'
        for k in ('B','seed'):c.add('bootstrap'+length+'/'+k,item[k],target[k])
        c.add('bootstrap'+length+'/block_days',item['block_days' if style=='three' else 'block_length_days'],int(length))
        c.add('bootstrap'+length+'/dates',item[{'one':'D','two':'n_dates','three':'dates'}[style]],REF[phase]['audit']['unique_dates_hour'])
        for key,refkey in [(abskey,'absolute_difference_percentile95'),(relkey,'relative_reduction_percentile95')]:
            for i,v in enumerate(item[key]):c.add('bootstrap'+length+'/'+refkey+'/'+str(i),v,target[refkey][i])
    return c.report()

# Reconstruct every bootstrap draw with actual hourly error arrays, separately
# from the delivered aggregate implementation. Each block length resets RNG.
def independent_bootstrap(phase,length):
    grouped=collections.defaultdict(list)
    for r in periods[phase]:
        p0,p1=reference.predict(MODEL,r);y=int(r['cnt'])
        grouped[r['dteday']].append((abs(p0-y),abs(p1-y)))
    dates=sorted(grouped);D=len(dates);rng=random.Random(20261029);output=[]
    for replicate in range(1,2001):
        starts=[rng.randrange(D) for _ in range(math.ceil(D/length))]
        indexes=[(start+j)%D for start in starts for j in range(length)][:D]
        sample=[e for i in indexes for e in grouped[dates[i]]]
        n=len(sample);m0=math.fsum(x[0] for x in sample)/n;m1=math.fsum(x[1] for x in sample)/n
        output.append({'replicate':replicate,'n_dates':D,'hours':n,'MAE0':m0,'MAE1':m1,
                       'absolute_difference':m0-m1,'relative_reduction':1-m1/m0})
    p=ROOT/f'independent-{phase}-bootstrap-{length}.csv'
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(output[0]));w.writeheader();w.writerows(output)
    return output
boot_expected={(phase,length):independent_bootstrap(phase,length) for phase in periods for length in (7,28)}

def compare_predictions(path,phase):
    supplied=rows(path);expected=periods[phase];c=Checks()
    c.add('prediction_rows',len(supplied),len(expected))
    for i,(actual,r) in enumerate(zip(supplied,expected)):
        for k,v in [('date',r['dteday']),('hr',int(r['hr'])),('workingday',int(r['workingday'])),('actual',int(r['cnt']))]:
            sourcekey=({'date':'date','actual':'actual'}.get(k,k) if 'date' in actual else {'date':'dteday','actual':'cnt'}.get(k,k))
            c.add(str(i)+'/'+k,actual[sourcekey] if k=='date' else int(actual[sourcekey]),v)
        p0,p1=reference.predict(MODEL,r)
        for m,pred in [('C0',p0),('C1',p1)]:c.add(str(i)+'/'+m,float(actual[m]),pred)
        c.add(str(i)+'/fallback',int(actual['C1_fallback' if 'C1_fallback' in actual else 'fallback']),0)
        for k,v in actual.items():
            if k.startswith(('abs_error_','error_')):
                model=k.split('_')[-1];pred=float(actual[model]);target=pred-int(r['cnt'])
                if k.startswith('abs_'):target=abs(target)
                c.add(str(i)+'/'+k,float(v),target)
            elif k in ('abs0','abs1','sq0','sq1','bias0','bias1'):
                err=float(actual['C'+k[-1]])-int(r['cnt'])
                c.add(str(i)+'/'+k,float(v),abs(err) if k.startswith('abs') else err*err if k.startswith('sq') else err)
    return c.report()

def compare_boot_csv(path,style,phase,length):
    actual=rows(path);expected=boot_expected[phase,length];c=Checks()
    c.add('replicate_rows',len(actual),len(expected))
    aliases={'one':{'replicate':'replicate','n_sampled_dates':'n_dates','n_sampled_hours':'hours','MAE_C0':'MAE0','MAE_C1':'MAE1','absolute_improvement':'absolute_difference','relative_improvement':'relative_reduction'},
             'two':{'replicate':'replicate','n_hours':'hours','C0_MAE':'MAE0','C1_MAE':'MAE1','difference':'absolute_difference','relative_reduction':'relative_reduction'},
             'three':{'replicate':'replicate','hours':'hours','MAE0':'MAE0','MAE1':'MAE1','absolute_difference':'absolute_difference','relative_reduction':'relative_reduction'}}[style]
    for i,(a,e) in enumerate(zip(actual,expected)):
        for key,canonical in aliases.items():c.add(str(i+1)+'/'+key,float(a[key]),e[canonical])
    return c.report()

def compare_daily(path,style,phase):
    grouped=collections.defaultdict(list)
    for r in periods[phase]:grouped[r['dteday']].append(r)
    actual=rows(path);c=Checks();c.add('daily_rows',len(actual),len(grouped))
    for a in actual:
        date=a['date' if 'date' in a else 'dteday'];rs=grouped[date]
        aliases=({'n_hours':len(rs),'workingday':int(rs[0]['workingday']),
                  **{f'MAE_{m}':math.fsum(abs(reference.predict(MODEL,r)[i]-int(r['cnt'])) for r in rs)/len(rs) for i,m in enumerate(('C0','C1'))},
                  **{f'abs_error_{m}':math.fsum(abs(reference.predict(MODEL,r)[i]-int(r['cnt'])) for r in rs) for i,m in enumerate(('C0','C1'))}})
        aliases.update({'n':len(rs),'distinct_hours':len({r['hr'] for r in rs}),
                        'abs0_sum':aliases['abs_error_C0'],'abs1_sum':aliases['abs_error_C1'],
                        'abs_error_sum_C0':aliases['abs_error_C0'],'abs_error_sum_C1':aliases['abs_error_C1'],
                        'sum_abs_error_C0':aliases['abs_error_C0'],'sum_abs_error_C1':aliases['abs_error_C1']})
        for key,value in a.items():
            if key in ('date','dteday'):continue
            if key not in aliases:raise ValueError('Unmapped daily field '+key)
            c.add(date+'/'+key,float(value),aliases[key])
    return c.report()

def compare_model(path):
    m=load(path);c=Checks();expectedgroups={'C0':collections.defaultdict(list),'C1':collections.defaultdict(list)}
    for r in train:
        expectedgroups['C0'][r['hr']].append(int(r['cnt']))
        expectedgroups['C1'][r['workingday']+':'+r['hr']].append(int(r['cnt']))
    for family in ('C0','C1'):
        observed={key.replace(',',':'):v for key,v in m[family].items()}
        c.add(family+'/keys',sorted(observed),sorted(MODEL[family]))
        for key,cell in observed.items():
            c.add(family+'/'+key+'/mean',cell['mean'],MODEL[family][key])
            c.add(family+'/'+key+'/n',cell['n'],len(expectedgroups[family][key]))
            c.add(family+'/'+key+'/sum',cell['sum' if 'sum' in cell else 'sum_cnt'],sum(expectedgroups[family][key]))
    return c.report()

def compare_annual(output,trial,style):
    c=Checks()
    if trial=='D04':
        a=load(output/'annual_summary.json');yy=a['years'];total=a['total_count_growth'];daily=a['daily_mean_growth']
        nums={y:{'hours':v['hour_rows'],'days':v['day_rows'],'total':v['annual_total_cnt'],'mean':v['mean_daily_cnt']} for y,v in yy.items()}
    elif trial=='D05':
        a=load(output/'annual.json');total=a['annual_total_growth'];daily=a['daily_mean_growth']
        nums={str(v['year']):{'hours':v['observed_hours'],'days':v['observed_dates'],'total':v['cnt_total'],'mean':v['daily_mean']} for v in a['years']}
    else:
        a=load(output/'annual_growth.json');total=a['total_growth'];daily=a['mean_daily_growth']
        yy=load(output/'data_audit.json')
        nums={y:{'hours':v['hour_rows'],'days':v['day_rows'],'total':v['annual_count_day_sum'],'mean':v['mean_daily_count']} for y,v in yy.items()}
    for y,z in nums.items():
        r=REF['year2011' if y=='2011' else 'phase2']['audit'] if y!='2011' else REF['year2011']
        for k,key in [('hours','hour_rows'),('days','day_rows'),('total','cnt_total_day'),('mean','daily_mean_count')]:c.add(y+'/'+k,z[k],r[key])
    c.add('total_growth',total,REF['total_year_growth_fraction']);c.add('daily_mean_growth',daily,REF['daily_mean_year_growth_fraction'])
    return c.report()

def compact(report):
    # Full per-value evidence is retained separately to keep the main audit navigable.
    return {k:v for k,v in report.items() if k not in ('all_checks','max_error_fields')}

results=[]
for item in PLAN:
    trial=item['trial_id'];root=ROOT/trial;output=root/'output';workspace=root/'workspace-copy'
    style={'D01':'one','D02':'two','D03':'three','D04':'two','D05':'three','D06':'one'}[trial]
    phase='phase1' if item['task_id']=='data-a' else 'phase2'
    original_result={'D01':'','D02':'results','D03':'results','D04':'results_2012','D05':'results2012','D06':'stage_b_results'}[trial]
    original=Path(item['sealed_workspace'])/original_result
    checks={}
    checks['main_metrics']=compare_metrics(load(output/'results.json'),style,phase)
    checks['predictions']=compare_predictions(output/'predictions.csv',phase)
    checks['daily_errors']=compare_daily(output/'daily_errors.csv',style,phase)
    model=workspace/('model.json' if style=='one' else 'results/model.json')
    checks['frozen_model']=compare_model(output/'model.json' if phase=='phase1' else model)
    if phase=='phase1':assert sha(output/'model.json')==sha(model)
    for length in (7,28):
        filename={'one':f'bootstrap_L{length}.csv','two':f'bootstrap_{length}.csv','three':f'bootstrap_{length}d.csv'}[style]
        checks['bootstrap_'+str(length)]=compare_boot_csv(output/filename,style,phase,length)
    if phase=='phase2':checks['annual']=compare_annual(output,trial,style)
    # Check all delivered numerical artifacts for reproduction identity. Runtime,
    # prose and provenance logs are excluded from byte-identity conclusions.
    ignored={'runtime.json','provenance.json','score_provenance.json','report.md'}
    byte_checks=[]
    for p in sorted(output.rglob('*')):
        if p.is_file() and p.name not in ignored:
            relative=p.relative_to(output);prior=original/relative
            byte_checks.append({'file':str(relative),'new_sha256':sha(p),'sealed_sha256':sha(prior) if prior.exists() else None,
                                'byte_identical':prior.exists() and sha(p)==sha(prior)})
    # Confirm data inputs are the same rows as the raw public source slices.
    input_checks={}
    for y in ([2011] if phase=='phase1' else [2011,2012]):
        for scale,all_rows in [('hour',hours),('day',days)]:
            expected=[r for r in all_rows if r['dteday'].startswith(str(y)+'-')]
            p=root/f'input-copy/data/{scale}_{y}.csv'
            input_checks[f'{scale}_{y}']={'row_content_equals_raw_subset':rows(p)==expected,'rows':len(expected),'sha256':sha(p)}
    freeze={}
    if phase=='phase2':
        pred=next(x for x in PLAN if x['trial_id']==item['predecessor'])
        prior_model=Path(pred['sealed_workspace'])/('model.json' if style=='one' else 'results/model.json')
        prior_code=Path(pred['sealed_workspace'])/('analysis.py' if style=='one' else 'analyze.py')
        code=workspace/('stage_a_snapshot/analysis.py' if style=='one' else 'analyze.py')
        entry=workspace/{'D04':'update2012.py','D05':'update_2012.py','D06':'stage_b.py'}[trial]
        tree=ast.parse(entry.read_text())
        fit_calls=[{'line':n.lineno,'function':ast.unparse(n.func)} for n in ast.walk(tree) if isinstance(n,ast.Call) and
                   ((isinstance(n.func,ast.Name) and n.func.id in ('fit','train')) or (isinstance(n.func,ast.Attribute) and n.func.attr in ('fit','train')))]
        freeze={'predecessor':item['predecessor'],'model_sha256':sha(model),'predecessor_model_sha256':sha(prior_model),
                'original_model_retained_byte_for_byte':sha(model)==sha(prior_model),
                'scoring_code_sha256':sha(code),'predecessor_scoring_code_sha256':sha(prior_code),
                'scoring_code_retained_byte_for_byte':sha(code)==sha(prior_code),
                'fit_or_train_calls_in_update_entry':fit_calls,
                'inspection':'Entry loads model from JSON; training sum/n/mean checks use 2011 pre-October rows. New-year rows are passed only to audit/predict/evaluate; imported analysis main is guarded. No new-year refit or parameter assignment appears in update path.',
                'new_labels_used_for_refit':False}
        history=output/({'D04':'recovery_2011','D05':'history_replay','D06':'unused'}[trial])
        hresults=history/'results.json' if trial!='D06' else workspace/'stage_a_snapshot/results.json'
        checks['historical_metrics']=compare_metrics(load(hresults),style,'phase1')
        if trial!='D06':
            checks['historical_predictions']=compare_predictions(history/'predictions.csv','phase1')
            checks['historical_daily_errors']=compare_daily(history/'daily_errors.csv',style,'phase1')
            for length in (7,28):
                filename=f'bootstrap_{length}.csv' if style=='two' else f'bootstrap_{length}d.csv'
                checks['historical_bootstrap_'+str(length)]=compare_boot_csv(history/filename,style,'phase1',length)
    save(root/'numeric-value-checks.json',checks)
    result={'trial_id':trial,'task_id':item['task_id'],'phase':phase,'style':style,
            'execution':load(root/'execution-record.json'), 'checks':{k:compact(v) for k,v in checks.items()},
            'raw_input_checks':input_checks,'scientific_output_byte_checks':byte_checks,'freeze':freeze,
            'max_absolute_error':max(v['max_absolute_error'] for v in checks.values()),
            'all_numeric_checks_passed':all(not v['failures'] for v in checks.values()),
            'unreported_reference_scopes':['weathersit subgroups'],
            'scope_note':'All delivered numeric summary scopes are compared. Weather subgroup summaries exist only in the independent reference and are not claimed as author-delivered values.'}
    results.append(result)

audit={'protocol':'Blind to arm mapping; no memory, personal skills, network, author-code changes or algorithm/threshold/seed changes.',
       'tolerance_absolute':TOL,'reference':{'argv':reference_argv,'exit_code':reference_exit,
        'script_sha256':sha(REFROOT/'reference_data.py'),'answers_sha256':sha(REFROOT/'references/data-numbers.json'),
        'model_sha256':sha(REFROOT/'references/data-model.json'),
        'new_reference_answers_equal_supplied':True,'new_reference_model_semantically_equal_supplied':True,
        'raw_sha256':{name:sha(RAW/name) for name in REF['raw_sha256']},
        'raw_hashes_match_reference':all(sha(RAW/name)==value for name,value in REF['raw_sha256'].items())},
       'trials':results}
save(BASE/'numeric-replay-audit.json',audit)
print(json.dumps({'reference_exit':reference_exit,'trials':[{k:x[k] for k in ('trial_id','max_absolute_error','all_numeric_checks_passed')} for x in results]},indent=2))
