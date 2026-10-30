#!/usr/bin/env python3
"""Numerical checks only; the report contains the proofs."""
import argparse, hashlib, json, math
from fractions import Fraction
from pathlib import Path

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--input-dir', type=Path, required=True)
    p.add_argument('--output-dir', type=Path, required=True)
    args=p.parse_args()
    names=['TASK.md','draft.tex','sources/howard2020-arxiv-v7.pdf',
           'sources/howard2020-arxiv-v7.txt','sources/howard2021-arxiv-v9.pdf',
           'sources/howard2021-arxiv-v9.txt']
    identity={n: hashlib.sha256((args.input_dir/n).read_bytes()).hexdigest() for n in names}
    alpha=Fraction(1,20); rho=Fraction(1,4); v=Fraction(1,4)
    n=20; mu=Fraction(1,10)
    probability=Fraction(9,10)**n
    b2=float(v+rho)*math.log(float((v+rho)/(alpha*alpha*rho)))
    assert probability>alpha
    assert 20*9**20>10**20
    assert b2<float((n*mu)**2)
    L=math.log(float(1/(alpha*alpha)))
    lo,hi=0.0,16.0
    while hi-math.log1p(hi)<L: hi*=2
    for _ in range(100):
        mid=(lo+hi)/2
        if mid-math.log1p(mid)<L: lo=mid
        else: hi=mid
    x=(lo+hi)/2
    opt_rho=float(v)/x
    min_b2=float(v)*(1+x)
    calc_b2=(float(v)+opt_rho)*math.log((float(v)+opt_rho)/(float(alpha)**2*opt_rho))
    assert abs(calc_b2-min_b2)<1e-12
    result={'scope':'numerical checks, not a proof or simulated coverage estimate',
      'input_sha256':identity,
      'B':{'n':n,'mu':'1/10','alpha':'1/20','rho':'1/4','event':'first 20 observations all zero',
      'probability_exact':str(probability),'probability_float':float(probability),
      'b_squared_formula':'(1/2)*log(800)','b_squared':b2,'b':math.sqrt(b2),
      'interval_upper_on_event':math.sqrt(b2)/n,
      'integer_probability_comparison':20*9**20>10**20},
      'C':{'equation':'x-log(1+x)=log(alpha**-2)', 'x':x,
      'residual':x-math.log1p(x)-L,'sqrt_coefficient':math.sqrt(1+x),
      'v':'1/4','rho_star':opt_rho,'min_b_squared':min_b2,
      'formula_agreement_abs_error':abs(calc_b2-min_b2)},
      'checks_passed':True}
    args.output_dir.mkdir(parents=True,exist_ok=True)
    (args.output_dir/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
