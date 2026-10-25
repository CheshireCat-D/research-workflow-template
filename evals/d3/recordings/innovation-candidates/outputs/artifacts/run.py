"""Run from project root: python3 artifacts/run.py. Python standard library only.
Only driver functions inspect x_current; estimators receive a budgeted callable.
"""
import hashlib
import itertools
import json
import math
import platform
import random
import time
from fractions import Fraction as F
from pathlib import Path

class BudgetAccess:
    def __init__(self, values, budget):
        self.__values = tuple(values)
        self.budget = budget
        self.indices = []
    def read(self, i):
        if len(self.indices) >= self.budget:
            raise RuntimeError('current-position access budget exceeded')
        self.indices.append(i)
        return self.__values[i]

def probabilities(scores, alpha):
    n = len(scores)
    total = sum(scores)
    q = [F(s, total) for s in scores] if total else [F(1, n)] * n
    return [(1-alpha)/n + alpha*qi for qi in q]

def strata_allocation(scores, k):
    H = [i for i,s in enumerate(scores) if s > 0]
    L = [i for i,s in enumerate(scores) if s <= 0]
    if not H or not L:
        return [(list(range(len(scores))), k)]
    if k < 2:
        raise ValueError('two nonempty strata require budget >= 2')
    kh = min(len(H), max(1, k//2))
    kl = k-kh
    if kl > len(L):
        kh += kl-len(L)
        kl = len(L)
    if kl < 1:
        kl,kh = 1,k-1
    return [(H,kh),(L,kl)]

def estimate(old, plan, read, kind, probs=None, strata=None):
    # No current vector, complete deltas or truth is supplied to this function.
    total = F(sum(old))
    if kind in ('C_mix','U_wr'):
        return total + sum((F(read(i)-old[i])/probs[i] for i in plan),F())/len(plan)
    if kind == 'A':
        return total + F(len(old),len(plan))*sum((read(i)-old[i] for i in plan),0)
    offset = 0
    for group,kh in strata:
        chosen = plan[offset:offset+kh]
        total += F(len(group),kh)*sum((read(i)-old[i] for i in chosen),0)
        offset += kh
    return total

def make_plan(old,scores,k,kind,rng):
    if kind in ('C_mix','U_wr'):
        probs = probabilities(scores,F(1,2) if kind=='C_mix' else F(0))
        return rng.choices(range(len(old)),weights=[float(p) for p in probs],k=k),probs,None
    if kind=='A':
        return rng.sample(range(len(old)),k),None,None
    strata = strata_allocation(scores,k)
    return [i for group,kh in strata for i in rng.sample(group,kh)],None,strata

def driver_moments(workload,k,kind):
    # Oracle evaluation only: full current vector belongs to the driver.
    old = workload['x_old']; cur = workload['x_current']; scores = workload['history_scores']
    n = len(old); d = [F(x-y) for x,y in zip(cur,old)]; D = sum(d)
    if kind in ('C_mix','U_wr'):
        p = probabilities(scores,F(1,2) if kind=='C_mix' else F(0))
        variance = (sum(di*di/pi for di,pi in zip(d,p))-D*D)/k
        # Independent single-draw enumeration of the actual estimator callable.
        e1 = e2 = F()
        for i,pi in enumerate(p):
            acc = BudgetAccess(cur,1)
            z = estimate(old,[i],acc.read,kind,p)-sum(old)
            assert len(acc.indices)==1
            e1 += pi*z; e2 += pi*z*z
        assert e1 == D and (e2-e1*e1)/k == variance
        return variance,0,{'single_draw_outcomes':n,'joint_factorization':'k independent draws','exact_bias':'0'}
    strata = [(list(range(n)),k)] if kind=='A' else strata_allocation(scores,k)
    variance = F()
    for group,kh in strata:
        nh = len(group); dh = sum(d[i] for i in group)
        if nh > 1:
            s2 = sum((d[i]-dh/nh)**2 for i in group)/(nh-1)
            variance += F(nh*nh,kh)*(1-F(kh,nh))*s2
    plans = (tuple(itertools.chain.from_iterable(groups)) for groups in itertools.product(*(itertools.combinations(group,kh) for group,kh in strata)))
    sumerr=sumerr2=F();count=0
    for plan in plans:
        acc=BudgetAccess(cur,k)
        est=estimate(old,plan,acc.read,kind,strata=strata)
        assert len(acc.indices)==k and len(set(acc.indices))==k
        err=est-sum(cur);sumerr+=err;sumerr2+=err*err;count+=1
    assert sumerr/count==0 and sumerr2/count==variance
    return variance,count,{'joint_sample_sets_enumerated':count,'exact_bias':str(sumerr/count)}

def run():
    start=time.perf_counter()
    config=json.loads(Path('artifacts/config.json').read_text())
    source=Path('inputs/workloads.json'); workloads=json.loads(source.read_text())
    seed=workloads['seed']; rows=[]
    for wi,w in enumerate(workloads['workloads']):
        old=w['x_old'];cur=w['x_current'];scores=w['history_scores'];n=len(old)
        assert len(cur)==len(scores)==n and all(s>=0 for s in scores)
        for k in workloads['budgets']:
            assert 1<=k<=n
            for mi,kind in enumerate(config['methods']):
                mse,enumcount,cross=driver_moments(w,k,kind)
                rng=random.Random(seed+wi*10000+k*100+mi)
                errors=[];calls=[];duplicate_trials=0;example=None
                for rep in range(config['repetitions']):
                    plan,p,strata=make_plan(old,scores,k,kind,rng)
                    acc=BudgetAccess(cur,k)
                    value=estimate(old,plan,acc.read,kind,p,strata)
                    assert len(acc.indices)==k
                    calls.append(len(acc.indices))
                    duplicate_trials += len(set(acc.indices)) < k
                    errors.append(float(value-sum(cur)))
                    if rep==0:
                        example={'indices_0_based':list(acc.indices),'estimate':float(value),'calls':len(acc.indices)}
                row={'workload':w['id'],'N':n,'budget':k,'method':kind,'truth':sum(cur),'exact_mse':str(mse),'mse':float(mse),'exact_bias':'0','moment_crosscheck':cross,'simulation':{'repetitions':len(errors),'seed':seed+wi*10000+k*100+mi,'mean_error':sum(errors)/len(errors),'mse':sum(e*e for e in errors)/len(errors),'purpose':'implementation/audit only; conclusions use exact moments'},'access_audit':{'min_calls':min(calls),'max_calls':max(calls),'trials_with_repeated_indices':duplicate_trials,'repeat_reads_are_charged':True,'first_trace':example}}
                if kind=='C_strata': row['allocation']=[{'indices':g,'sample_size':kh} for g,kh in strata_allocation(scores,k)]
                if kind in ('C_mix','U_wr'):row['p']=[str(p) for p in probabilities(scores,F(1,2) if kind=='C_mix' else F(0))]
                rows.append(row)
    result={'scope':'six provided synthetic fixed vectors; all two budgets; exact randomization MSE; no global guarantee','input_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'config':config,'seed':seed,'environment':{'python':platform.python_version(),'implementation':platform.python_implementation(),'platform':platform.platform()},'rows':rows,'failures':[],'elapsed_seconds':time.perf_counter()-start}
    Path('artifacts/results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'rows':len(rows),'elapsed_seconds':result['elapsed_seconds'],'analytic_crosschecks':'passed','all_access_budgets':'passed','output':'artifacts/results.json'},indent=2))
    for w in workloads['workloads']:
        for k in workloads['budgets']:
            print(w['id'],k,{r['method']:r['exact_mse'] for r in rows if r['workload']==w['id'] and r['budget']==k})

if __name__=='__main__':
    run()
