#!/usr/bin/env python3
"""Deterministic arithmetic checks; the analytic proofs are in report.md."""
import argparse
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path


def run(input_dir, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    mu = Fraction(1, 10)
    samples = [Fraction(0)] * 20
    predictions = [Fraction(1, 2)] + [sum(samples[:i]) / i for i in range(1, 20)]
    variance = sum((x - pred)**2 for x, pred in zip(samples, predictions))
    s = sum(samples) - 20 * mu
    probability = Fraction(9, 10)**20
    bound_squared = (float(variance) + .25) * math.log((float(variance) + .25) / (.1**2 * .25))
    assert variance == Fraction(1, 4)
    assert s == -2
    assert bound_squared < float(s*s)
    assert probability > mu
    alpha = .1
    low, high = 0., 20.
    for _ in range(100):
        mid = (low+high)/2
        if mid-math.log1p(mid) < -2*math.log(alpha):
            low = mid
        else:
            high = mid
    r = (low+high)/2
    v = .25
    rho = v/r
    optimum = (v+rho)*math.log((v+rho)/(alpha**2*rho))
    assert abs(optimum-(1+r)*v) < 1e-12
    for scale in (.1, .5, 2., 10.):
        candidate = rho*scale
        assert (v+candidate)*math.log((v+candidate)/(alpha**2*candidate)) >= optimum-1e-12
    # Independent numerical quadrature of the Gaussian kernel, with finite cutoff.
    # Numerical agreement only, not justification for Tonelli or the analytic integral.
    S, V, precision = .7, 2., 1.3
    n, cutoff = 20000, 12.
    h = 2*cutoff/n
    def integrand(lam):
        return math.sqrt(precision/(2*math.pi))*math.exp(lam*S-(V+precision)*lam*lam/2)
    quadrature = h/3*(integrand(-cutoff)+integrand(cutoff)+sum((4 if i%2 else 2)*integrand(-cutoff+i*h) for i in range(1,n)))
    closed = math.sqrt(precision/(V+precision))*math.exp(S*S/(2*(V+precision)))
    assert abs(quadrature-closed) < 1e-10
    max_excess = -1.
    for lam in (.01, .1, .5, .9, .99):
        psi = -math.log1p(-lam)-lam
        for i in range(2001):
            xi = -1+i/1000
            excess = math.exp(lam*xi-psi*xi*xi)-(1+lam*xi)
            max_excess = max(max_excess, excess)
    assert max_excess < 1e-12
    source_hashes = {str(p.relative_to(input_dir)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(input_dir.rglob('*')) if p.is_file()}
    result = {
      'kind':'numerical checks only, not proof', 'status':'passed',
      'B':{'probability_formula':'(9/10)^20','probability_exact':str(probability),'probability':float(probability),'variance_exact':str(variance),'S_exact':str(s),'boundary_formula':'sqrt(log(200)/2)','boundary':math.sqrt(bound_squared)},
      'C':{'alpha':alpha,'r_equation':'r-log(1+r)=log(alpha^-2)','r':r,'rho_at_v_quarter':rho,'minimum_squared':optimum},
      'A':{'S':S,'V':V,'rho':precision,'quadrature':quadrature,'closed_form':closed,'absolute_difference':abs(quadrature-closed),'quadrature_cutoff':cutoff,'simpson_intervals':n},
      'EB':{'grid_only':True,'max_scalar_inequality_excess':max_excess},
      'input_sha256':source_hashes,
    }
    (output_dir/'checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--input',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    run(args.input,args.output)
