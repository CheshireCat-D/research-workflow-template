"""Deterministic numeric and exact-arithmetic checks; proofs are in report.md."""
import argparse
import hashlib
import json
import math
from fractions import Fraction
from pathlib import Path


def simpson(f, a, b, n=40000):
    h = (b-a)/n
    return h/3*(f(a)+f(b)+4*sum(f(a+h*k) for k in range(1,n,2))
                +2*sum(f(a+h*k) for k in range(2,n,2)))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    alpha, rho, v, n, p = .05, .25, .25, 200, .01
    b = math.sqrt((v+rho)*math.log((v+rho)/(alpha**2*rho)))
    probability = Fraction(99,100)**200
    assert probability > Fraction(1,20)
    assert sum(Fraction(8)**k/math.factorial(k) for k in range(7)) > 800
    assert b < n*p
    L = math.log(alpha**-2)
    lo, hi = 0., 1.
    while hi-math.log1p(hi) < L:
        hi *= 2
    for _ in range(100):
        r = (lo+hi)/2
        if r-math.log1p(r) < L:
            lo = r
        else:
            hi = r
    r = (lo+hi)/2
    kappa = math.sqrt(1+r)
    s, vg, rg = 1.2, 3., .7
    A = vg+rg
    center = s/A
    f = lambda lam: math.sqrt(rg/(2*math.pi))*math.exp(lam*s-A*lam*lam/2)
    integrated = simpson(f, center-12/math.sqrt(A), center+12/math.sqrt(A))
    closed = math.sqrt(rg/A)*math.exp(s*s/(2*A))
    assert abs(integrated-closed) < 1e-12
    worst = -1.
    for lam in (0.,.1,.5,.9,.99):
        psi = -math.log1p(-lam)-lam
        for j in range(2001):
            xi = -1+j/1000
            worst = max(worst, math.exp(lam*xi-psi*xi*xi)-(1+lam*xi))
    assert worst < 1e-13
    pdf_hashes = {}
    for name in ('howard2020-arxiv-v7.pdf','howard2021-arxiv-v9.pdf'):
        pdf_hashes[name] = hashlib.sha256((args.input/'sources'/name).read_bytes()).hexdigest()
    result = {
        'counterexample': {
            'alpha':'1/20','rho':'1/4','mu':'1/100','t':200,
            'event':'X_1=...=X_200=0', 'Vhat_on_event':'1/4',
            'S_on_event':-2, 'boundary_formula':'sqrt(log(800)/2)',
            'boundary':b, 'event_probability_formula':'(99/100)^200',
            'event_probability':float(probability),
            'exact_probability_above_alpha':True,
            'exp8_lower_Taylor_sum':float(sum(Fraction(8)**k/math.factorial(k) for k in range(7)))
        },
        'optimization':{'alpha':alpha,'r':r,'residual':r-math.log1p(r)-L,
                        'kappa':kappa,'rho_star_formula':'v/r','inf_boundary_formula':'kappa*sqrt(v)'},
        'normal_mixture_numeric_check':{'s':s,'v':vg,'rho':rg,'quadrature':integrated,
                                         'closed_form':closed,'absolute_error':abs(integrated-closed)},
        'empirical_Bernstein_scalar_grid_max_excess':worst,
        'pdf_sha256':pdf_hashes,
        'scope':'Exact finite probability comparison and deterministic numeric checks; no simulation, no proof by grid.'
    }
    (args.output/'checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
