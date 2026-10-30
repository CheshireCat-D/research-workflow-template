#!/usr/bin/env python3
"""Numerical self-checks for the accompanying analytic audit; no simulation/proof claim."""
import argparse, hashlib, json, math
from fractions import Fraction
from pathlib import Path

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--input',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    hashes={str(f.relative_to(a.input)):hashlib.sha256(f.read_bytes()).hexdigest()
            for f in sorted(a.input.rglob('*')) if f.is_file()}
    alpha=Fraction(1,20); probability=Fraction(9,10)**20
    e8_lower=sum((Fraction(8)**k)/math.factorial(k) for k in range(7))
    b=math.sqrt(math.log(800)/2)
    assert e8_lower>800 and probability>alpha and b<2
    lo,hi=0.,32.
    target=math.log(400)
    for _ in range(120):
        mid=(lo+hi)/2
        if mid-math.log1p(mid)<target:lo=mid
        else:hi=mid
    q=(lo+hi)/2; v=.25; rho=v/q
    def boundary(v,r):return math.sqrt((v+r)*math.log((v+r)/(float(alpha)**2*r)))
    envelope=math.sqrt((1+q)*v)
    assert abs(boundary(v,rho)-envelope)<1e-12
    grid_min=min(boundary(v,rho*math.exp(k/100)) for k in range(-1000,1001))
    assert grid_min>=envelope-1e-12
    max_log_excess=-math.inf
    for lam in [.0,.01,.1,.25,.5,.9,.99]:
        psi=-math.log1p(-lam)-lam
        for k in range(2001):
            xi=-1+k/1000
            max_log_excess=max(max_log_excess,lam*xi-psi*xi*xi-math.log1p(lam*xi))
    assert max_log_excess<1e-12
    result={'input_sha256':hashes,'B':{
        'alpha':'1/20','rho':'1/4','n':20,'mu':'1/10',
        'event':'X_1=...=X_20=0 with iid Bernoulli(1/10)',
        'probability_formula':'(9/10)^20','probability_exact':str(probability),
        'probability_decimal':float(probability),'boundary_formula':'sqrt(log(800)/2)',
        'boundary':b,'endpoint':b/20,'e8_rational_lower_bound':str(e8_lower),
        'analytic_strict_inequalities':True},
        'C':{'q_equation':'q-log(1+q)=log(400)','q':q,'K':1+q,
        'v':v,'rho_opt':rho,'minimum_formula':'sqrt((1+q)*v)',
        'minimum':envelope,'finite_grid_minimum':grid_min},
        'EB':{'finite_grid_only':True,'max_log_inequality_excess':max_log_excess,
        'tail_budget':'alpha/[2*k*(k+1)] for each sign, k>=1'},
        'scope':'Exact rational arithmetic and numerical consistency checks; analytic proofs are in report.md.'}
    out=a.output/'checks_results.json';out.write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print(json.dumps({'result':str(out),'B_probability':float(probability),'B_boundary':b,
        'C_q':q,'C_K':1+q,'report_proof_required':True},ensure_ascii=False))
if __name__=='__main__':main()
