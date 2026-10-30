"""Numerical diagnostics only; the report contains the mathematical arguments."""
import json
import math


def run_checks():
    alpha = 1 / 20
    rho = 1 / 4
    v = 1 / 4
    n = 20
    p = 1 / 10
    boundary2 = (v + rho) * math.log((v + rho) / (alpha**2 * rho))
    lo, hi = 0.0, 100.0
    for _ in range(100):
        q = (lo + hi) / 2
        if q - math.log1p(q) < 2 * math.log(1 / alpha):
            lo = q
        else:
            hi = q
    q = (lo + hi) / 2
    rho_star = v / q
    minimum2 = (1 + q) * v
    direct_minimum2 = (v + rho_star) * math.log((v + rho_star) / (alpha**2 * rho_star))
    max_excess = -math.inf
    for lam in [0.01, 0.1, 0.25, 0.5, 0.75, 0.9, 0.99]:
        psi = -math.log1p(-lam) - lam
        for j in range(201):
            z = -1 + j / 100
            max_excess = max(max_excess, math.exp(lam * z - psi * z * z) - (1 + lam * z))
    return {
        'scope': 'finite deterministic numerical checks; no simulation or formal proof',
        'B': {
            'alpha': alpha, 'rho': rho, 'v_on_event': v, 'n': n, 'p': p,
            'boundary_squared_formula': 'log(800)/2',
            'boundary_squared': boundary2,
            'boundary': math.sqrt(boundary2),
            'absolute_S_on_event': n * p,
            'event_probability_formula': '(9/10)**20',
            'event_probability': (1 - p)**n,
            'exact_integer_probability_check': 20 * 9**20 > 10**20,
            'left_integer': 20 * 9**20,
            'right_integer': 10**20,
            'analytic_log_bound_integer_check': 8**8 > 800 * 3**8,
        },
        'C': {
            'q_equation': 'q-log(1+q)=2*log(1/alpha)',
            'q': q, 'rho_star': rho_star,
            'minimum_squared_formula': '(1+q)*v',
            'minimum_squared': minimum2,
            'direct_minimum_squared': direct_minimum2,
            'absolute_difference': abs(minimum2 - direct_minimum2),
        },
        'EB': {
            'lambdas': [0.01, 0.1, 0.25, 0.5, 0.75, 0.9, 0.99],
            'z_grid': '-1+j/100, j=0,...,200',
            'max_numerical_excess_exp_over_linear': max_excess,
            'does_not_establish_universal_inequality': True,
        },
    }


if __name__ == '__main__':
    print(json.dumps(run_checks(), ensure_ascii=False, indent=2))
