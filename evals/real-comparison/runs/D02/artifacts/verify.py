"""Independent arithmetic and bootstrap audit of saved first results."""
import collections,csv,hashlib,json,math,pathlib,random
ROOT=pathlib.Path(__file__).resolve().parent
INPUT=ROOT.parent/'input'
res=ROOT/'results'
h=list(csv.DictReader((INPUT/'data/hour_2011.csv').open()))
d=list(csv.DictReader((INPUT/'data/day_2011.csv').open()))
model=json.loads((res/'model.json').read_text()); results=json.loads((res/'results.json').read_text()); audit=json.loads((res/'audit.json').read_text())
manifest=json.loads((INPUT/'INPUT_MANIFEST.json').read_text())
checks={}
checks['input_manifest_sha']=all(hashlib.sha256((INPUT/f).read_bytes()).hexdigest()==v['sha256'] for f,v in manifest.items())
train=[r for r in h if r['dteday']<'2011-10-01']; hold=[r for r in h if r['dteday']>='2011-10-01']
checks['split_disjoint']=not ({r['dteday'] for r in train}&{r['dteday'] for r in hold})
checks['train_rows']=len(train)==model['train_n_hours']
checks['all_parameters_train_only']=True
for label in ('C0','C1'):
    for key,cell in model[label].items():
        subset=[int(r['cnt']) for r in train if (r['hr'] if label=='C0' else r['workingday']+':'+r['hr'])==key]
        checks['all_parameters_train_only'] &= sum(subset)==cell['sum_cnt'] and len(subset)==cell['n'] and sum(subset)/len(subset)==cell['mean']
p=list(csv.DictReader((res/'predictions.csv').open()))
checks['prediction_targets_match']=all(int(r['cnt'])==int(t['cnt']) and r['dteday']==t['dteday'] and int(r['hr'])==int(t['hr']) for r,t in zip(p,hold)) and len(p)==len(hold)
for k in ('0','1'):
    errors=[float(r['C'+k])-int(r['cnt']) for r in p]
    metrics={'hour_weighted_MAE':sum(abs(x) for x in errors)/len(errors),'hour_weighted_RMSE':math.sqrt(sum(x*x for x in errors)/len(errors)),'mean_bias_pred_minus_true':sum(errors)/len(errors)}
    for name,val in metrics.items(): checks['C'+k+'_'+name]=math.isclose(val,results['all']['C'+k][name],abs_tol=1e-10,rel_tol=0)
bydate=collections.defaultdict(list)
for r in p:bydate[r['dteday']].append(r)
dates=sorted(bydate);D=len(dates)
for block in (7,28):
    rng=random.Random(20261029); diff=[]; rel=[]; maxerr=0.0
    saved=list(csv.DictReader((res/('bootstrap_'+str(block)+'.csv')).open()))
    for rep in range(2000):
        sampled=[]
        for j in range(math.ceil(D/block)):
            start=rng.randrange(D)
            sampled.extend(dates[(start+offset)%D] for offset in range(block))
        sampled=sampled[:D]
        n=sum(len(bydate[dt]) for dt in sampled)
        a=sum(sum(abs(float(r['C0'])-int(r['cnt'])) for r in bydate[dt]) for dt in sampled)/n
        b=sum(sum(abs(float(r['C1'])-int(r['cnt'])) for r in bydate[dt]) for dt in sampled)/n
        diff.append(a-b);rel.append(1-b/a)
        maxerr=max(maxerr,abs(a-float(saved[rep]['C0_MAE'])),abs(b-float(saved[rep]['C1_MAE'])))
        assert n==int(saved[rep]['n_hours'])
    def q(v,p):
        v=sorted(v);z=1999*p;i=int(z);return (1-(z-i))*v[i]+(z-i)*v[i+1]
    ci=[q(diff,.025),q(diff,.975)];ri=[q(rel,.025),q(rel,.975)]
    checks['bootstrap_'+str(block)+'_all_replicates']=maxerr<1e-10
    checks['bootstrap_'+str(block)+'_intervals']=all(abs(x-y)<1e-10 for x,y in zip(ci+ri,results['bootstrap'][str(block)]['difference_CI95']+results['bootstrap'][str(block)]['relative_reduction_CI95']))
checks['all_pass']=all(checks.values())
(ROOT/'verification.json').write_text(json.dumps(checks,indent=2)+'\n')
assert checks['all_pass']
print(json.dumps({'checks':checks,'training':{k:model[k] for k in ('train_start','train_end','train_n_hours','train_n_dates')},'C0_cells':len(model['C0']),'C1_cells':len(model['C1']),'annual_audit':{k:v for k,v in audit.items() if k!='missing_calendar_hours'},'incomplete_holdout':{k:v for k,v in audit['missing_calendar_hours'].items() if k>='2011-10-01'},'model_sha256':hashlib.sha256((res/'model.json').read_bytes()).hexdigest()},ensure_ascii=False,indent=2))
