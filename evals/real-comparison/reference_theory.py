#!/usr/bin/env python3
"""Recompute reference numbers; certify finite witness using rational arithmetic.

No simulation. The analytic proof and scope are in independent-derivation.md.
"""
from fractions import Fraction as Q
import json
import math


def log_rational_interval(x, terms):
    """For rational x >= 1, rigorous rational interval for log(x)."""
    assert x >= 1
    z = (x - 1) / (x + 1)
    partial = 2 * sum((z ** (2*k + 1)) / (2*k + 1)
                      for k in range(terms))
    remainder_upper = 2 * z ** (2*terms + 1) / ((2*terms + 1) * (1-z*z))
    return partial, partial + remainder_upper


def main():
    l2, u2 = log_rational_interval(Q(2), 45)
    lr, ur = log_rational_interval(Q(128, 125), 12)
    l500, u500 = 9*l2 - ur, 9*u2 - lr
    assert l500 < u500
    b2_upper = Q(5, 4) * u500
    signal2 = Q(14, 5) ** 2
    event_probability = Q(99, 100) ** 280
    alpha = Q(1, 20)
    assert b2_upper < signal2
    assert event_probability > alpha
    lo, hi = 0.0, 100.0
    for _ in range(100):
        r = (lo+hi)/2
        if r-math.log((1+r)/float(alpha*alpha)) > 0:
            hi = r
        else:
            lo = r
    r = (lo+hi)/2
    out = {
        "finite_witness_rational_comparisons_passed": True,
        "log500_interval_width_upper": float(u500-l500),
        "event_probability": float(event_probability),
        "alpha": float(alpha),
        "Vhat_on_zero_event": 0.25,
        "boundary": math.sqrt(1.25*math.log(500)),
        "abs_S": 2.8,
        "one_step_wrong_mgf_lambda_minus2": .99*math.exp(.02)+.01*math.exp(-3.98),
        "optimizer_r": r,
        "envelope_C": math.sqrt(1+r),
        "rho_over_v": 1/r,
        "note": "Finite counterexample strict inequalities certified with Fraction; optimizer numeric values are checks of the separate analytic derivation."
    }
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
