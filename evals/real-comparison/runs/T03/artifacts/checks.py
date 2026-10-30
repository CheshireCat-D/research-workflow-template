"""Finite, deterministic numerical checks; these do not replace the proofs."""
import argparse
from pathlib import Path
from fractions import Fraction
import itertools
import math
import hashlib
import json

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--input',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args()
    alpha=Fraction(1,16); rho=Fraction(1,4)
    records=[]
    for xs in itertools.product((0,1),repeat=4):
        v=Fraction(0)
        for i,x in enumerate(xs):
            predictor=Fraction(1,2) if i==0 else Fraction(sum(xs[:i]),i)
            v+=(Fraction(x)-predictor)**2
        s=Fraction(sum(xs))-2
        b2=float(v+rho)*math.log(float((v+rho)/(alpha**2*rho)))
        records.append({'path':list(xs),'Vhat4':str(v),'S4':str(s),'boundary_squared':b2,'fails_t4':float(s*s)>b2})
    bad=[r for r in records if r['fails_t4']]
    assert [r['path'] for r in bad]==[[0,0,0,0],[1,1,1,1]]
    failprob=Fraction(len(bad),16)
    assert failprob>alpha
    k=2*math.log(1/float(alpha))
    lo,hi=0.,1.
    while hi-math.log1p(hi)<k: hi*=2
    for _ in range(100):
        mid=(lo+hi)/2
        if mid-math.log1p(mid)<k: lo=mid
        else: hi=mid
    x=(lo+hi)/2
    assert abs(x-math.log1p(x)-k)<1e-12
    v=7.
    rho_star=v/x
    minimized=(v+rho_star)*math.log((v+rho_star)/(float(alpha)**2*rho_star))
    assert abs(minimized-(1+x)*v)<1e-10
    hashes={str(p.relative_to(args.input)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(args.input.rglob('*')) if p.is_file()}
    result={'formula_B':'alpha=1/16; rho=1/4; b^2(1/4)=(1/2)*log(512)',
        'B_boundary_squared':0.5*math.log(512), 'B_boundary':math.sqrt(0.5*math.log(512)),
        'B_failure_probability_t4_exact':str(failprob),'B_nominal_alpha_exact':str(alpha),
        'formula_C':'x-log(1+x)=2*log(1/alpha); rho*=v/x; inf b^2=(1+x)*v',
        'C_alpha':float(alpha),'C_x':x,'C_q':1+x,'C_rho_for_v7':rho_star,
        'C_minimized_b2_v7':minimized,'finite_path_enumeration':records,'input_sha256':hashes,
        'scope':'Exact path enumeration plus floating point arithmetic; no simulation and no proof from numerical agreement.'}
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/'checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['B_boundary_squared','B_failure_probability_t4_exact','C_x','C_q']},ensure_ascii=False))
if __name__=='__main__':main()
