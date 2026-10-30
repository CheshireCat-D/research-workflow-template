from pathlib import Path
import csv,hashlib,json,math,subprocess,sys
root=Path(__file__).resolve().parents[2]; out=Path(__file__).resolve().parent
reads=[]; commands=[]
def trace(): (out/'run-trace.json').write_text(json.dumps({'reads':reads,'commands':commands},ensure_ascii=False,indent=2)+'\n')
def read(path):
    b=path.read_bytes(); reads.append({'path':str(path),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'scope':'full processing'}); trace(); return b
def sha(path): return hashlib.sha256(read(path)).hexdigest()
def save(name,obj): (out/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def run(args,name):
    a=[sys.executable,'-I','-B',str(root/'scripts/compute.py'),*args]
    r=subprocess.run(a,cwd=str(root),capture_output=True,text=True)
    (out/(name+'.stdout')).write_text(r.stdout); (out/(name+'.stderr')).write_text(r.stderr)
    commands.append({'argv':a,'cwd':str(root),'exit_code':r.returncode,'stdout':name+'.stdout','stderr':name+'.stderr'})
    trace(); return r
spec=json.loads(read(root/'notes/parameters.json')); approved=json.loads(read(root/'context/stage-C/approved-parameters.json'))
assert spec==approved, 'Current parameter object differs from approved scope'
assert spec['metric_weighting']=='observed-hour' and spec['case_id']=='D'
protected=['data/hour_2011.csv','scripts/compute.py','model/frozen.json','notes/source-check.md','validation/stage-A/source-verification.json']
before={rel:sha(root/rel) for rel in protected}
registry=json.loads(read(root/'records/registry.json'))
source_envelope=registry['records']['activities']['D-SOURCE-CHECK']
normal=run(['--root',str(root),'--output',str(out/'recalculation-retry')],'03-normal-recalculation')
assert normal.returncode==0,normal.stderr
fresh=json.loads(read(out/'recalculation-retry/result.json'))
rows=list(csv.DictReader(read(root/'data/hour_2011.csv').decode().splitlines()))
selected=[r for r in rows if spec['evaluation_start']<=r['dteday']<=spec['evaluation_end']]
model=json.loads(read(root/'model/frozen.json'))
metrics={'observed_hours':len(selected),'observed_days':len({r['dteday'] for r in selected})}
for key in ['C0','C1']:
    errors=[]
    for r in selected:
        pred=model['C0'][r['hr']] if key=='C0' else model['C1'].get(r['workingday']+':'+r['hr'],model['C0'][r['hr']])
        errors.append(pred-int(r['cnt']))
    metrics[key+'_MAE']=math.fsum(map(abs,errors))/len(errors)
    metrics[key+'_RMSE']=math.sqrt(math.fsum(e*e for e in errors)/len(errors))
    metrics[key+'_bias_prediction_minus_actual']=math.fsum(errors)/len(errors)
metrics['MAE_reduction_fraction']=1-metrics['C1_MAE']/metrics['C0_MAE']
checks={k:math.isclose(fresh[k],val,rel_tol=1e-14,abs_tol=1e-14) for k,val in metrics.items()}
table=dict(list(csv.reader(read(out/'recalculation-retry/table.csv').decode().splitlines()))[1:])
checks.update({'table:'+k:math.isclose(float(value),fresh[k],rel_tol=1e-14,abs_tol=1e-14) for k,value in table.items()})
checks['interval']=fresh['evaluation_start']==spec['evaluation_start'] and fresh['evaluation_end']==spec['evaluation_end']
checks['input_sha256']=fresh['input_sha256']=={'parameters':sha(root/'notes/parameters.json'),'calculator':before['scripts/compute.py'],'hour_2011':before['data/hour_2011.csv'],'frozen_model':before['model/frozen.json']}
canonical=['results/result.json','results/table.csv','results/summary.md']; canonical_before={r:sha(root/r) for r in canonical}
invalid=run(['--root',str(root),'--output',str(out/'invalid-output'),'--spec',str(root/'notes/rejected-parameters.json')],'04-controlled-invalid-recheck')
canonical_after={r:sha(root/r) for r in canonical}
negative={'expected_exit':2,'actual_exit':invalid.returncode,'output_absent':not (out/'invalid-output').exists(),'canonical_unchanged':canonical_before==canonical_after,'canonical_before_sha256':canonical_before,'canonical_after_sha256':canonical_after,'error':invalid.stderr}
checks['invalid_rejected']=invalid.returncode==2 and negative['output_absent'] and negative['canonical_unchanged']
after={rel:sha(root/rel) for rel in protected}; checks['protected_bytes_unchanged']=before==after
record={'checks':checks,'passed':all(checks.values()),'independent_metrics':metrics,'protected_before':before,'protected_after':after,'source_activity_envelope_before':source_envelope,'negative_test':negative,'commands':commands,'reads':reads,'scope':'Assistant standard-library observed-hour metrics and consistency check; supplied frozen model preserved; no refit or human expert approval.'}
save('verification.json',record)
print(json.dumps({'passed':record['passed'],'metrics':metrics,'commands':commands},ensure_ascii=False,indent=2))
raise SystemExit(0 if record['passed'] else 1)
