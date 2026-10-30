#!/usr/bin/env python3
"""Independent scoring arithmetic and prefix-sum bootstrap cross-check."""
import argparse,collections,csv,hashlib,json,math,pathlib,random

def read(p):
    with p.open(newline='') as f:return list(csv.DictReader(f))
def close(a,b):return math.isclose(a,b,rel_tol=1e-11,abs_tol=1e-9)
def q(x,p):
    x=sorted(x);t=(len(x)-1)*p;l=int(t);return x[l]+(t-l)*(x[math.ceil(t)]-x[l])
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output-dir',type=pathlib.Path,required=True);parser.add_argument('--model',type=pathlib.Path,required=True);a=parser.parse_args();o=a.output_dir
    m=json.loads(a.model.read_text());r=json.loads((o/'results.json').read_text());p=read(o/'predictions.csv');v={}
    for x in p:
        for k in ('cnt','hr','workingday','fallback'):x[k]=int(x[k])
        for k in ('C0','C1','abs0','abs1','sq0','sq1','bias0','bias1'):x[k]=float(x[k])
        assert x['C0']==m['C0'][str(x['hr'])]['mean'] and x['C1']==m['C1'][str(x['workingday'])+':'+str(x['hr'])]['mean']
    v['all_predictions_equal_frozen_lookup']=True
    bydate=collections.defaultdict(list)
    for x in p:bydate[x['dteday']].append(x)
    scopes={'all':p,'complete_24h_dates':[x for x in p if len(bydate[x['dteday']])==24],'workingday_0':[x for x in p if x['workingday']==0],'workingday_1':[x for x in p if x['workingday']==1]}
    for name,xs in scopes.items():
        target=r['workingday'][name[-1]] if name.startswith('workingday') else r[name]
        err={k:[x['C'+str(k)]-x['cnt'] for x in xs] for k in (0,1)}
        group=collections.defaultdict(list)
        for x in xs:group[x['dteday']].append(x)
        assert target['n_hours']==len(xs) and target['n_dates']==len(group)
        ms={};ds={}
        for k in (0,1):
            ms[k]=sum(map(abs,err[k]))/len(xs);ds[k]=sum(sum(abs(x['C'+str(k)]-x['cnt']) for x in group[d])/len(group[d]) for d in group)/len(group)
            expected={'hour_weighted_MAE':ms[k],'hour_weighted_RMSE':math.sqrt(sum(e*e for e in err[k])/len(xs)),'mean_bias_pred_minus_true':sum(err[k])/len(xs),'date_equal_mean_intraday_MAE':ds[k]}
            for key,value in expected.items():assert close(value,target['C'+str(k)][key]),(name,k,key)
        for key,value in {'MAE_difference_C0_minus_C1':ms[0]-ms[1],'relative_MAE_reduction':1-ms[1]/ms[0],'date_equal_MAE_difference':ds[0]-ds[1],'date_equal_relative_MAE_reduction':1-ds[1]/ds[0]}.items():assert close(value,target[key]),(name,key)
        v[name+'_all_metrics']=True
    dates=sorted(bydate);D=len(dates)
    vals=[(len(bydate[d]),sum(abs(x['C0']-x['cnt']) for x in bydate[d]),sum(abs(x['C1']-x['cnt']) for x in bydate[d])) for d in dates]
    for L in (7,28):
        pref=[[0.] for k in range(3)]
        for t in vals+vals:
            for k in range(3):pref[k].append(pref[k][-1]+t[k])
        rng=random.Random(20261029);draws=read(o/f'bootstrap_{L}.csv');diff=[];rel=[]
        for row in draws:
            totals=[0.,0.,0.];taken=0
            while taken<D:
                start=rng.randrange(D);n=min(L,D-taken)
                for k in range(3):totals[k]+=pref[k][start+n]-pref[k][start]
                taken+=n
            b0=totals[1]/totals[0];b1=totals[2]/totals[0];dd=b0-b1;rr=1-b1/b0
            for key,value in {'n_hours':totals[0],'C0_MAE':b0,'C1_MAE':b1,'difference':dd,'relative_reduction':rr}.items():assert close(float(row[key]),value),(L,row['replicate'],key)
            diff.append(dd);rel.append(rr)
        assert len(draws)==2000
        for key,series in [('difference_CI95',diff),('relative_reduction_CI95',rel)]:
            assert all(close(t,q(series,p)) for t,p in zip(r['bootstrap'][str(L)][key],(.025,.975)))
        v[f'bootstrap_{L}_all_2000_replicates_and_intervals']=True
    v['all_pass']=all(v.values());(o/'independent_verification.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v,indent=2))
if __name__=='__main__':main()
