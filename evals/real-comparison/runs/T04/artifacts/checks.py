"""Deterministic numerical corroboration; the report contains the analytic proofs."""
from pathlib import Path
import argparse, json, math
from fractions import Fraction

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input-dir", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    a = p.parse_args()
    if not (a.input_dir / "draft.tex").is_file():
        p.error("input-dir must contain draft.tex")
    a.output_dir.mkdir(parents=True, exist_ok=True)
    alpha, rho, v, n = 1/20, 1/4, 1/4, 200
    b2 = (v + rho) * math.log((v + rho)/(alpha**2*rho))
    exact_prob = Fraction(99, 100)**n
    assert 20*99**200 > 100**200
    assert b2 < 4
    assert -200/99 > -math.log(20)
    lo, hi = 0.0, 100.0
    for _ in range(100):
        x = (lo + hi)/2
        if x - math.log1p(x) - 2*math.log(1/alpha) < 0:
            lo = x
        else:
            hi = x
    x = (lo+hi)/2
    assert abs(x-math.log((1+x)/alpha**2)) < 1e-12
    def b_at_rho(r):
        return math.sqrt((v+r)*math.log((v+r)/(alpha**2*r)))
    rstar = v/x
    assert b_at_rho(rstar) <= min(b_at_rho(rstar*q) for q in [0.5, 0.9, 1.1, 2])
    results = {
        "B": {
            "alpha_formula": "1/20", "rho_formula": "1/4", "mu_formula": "1/100",
            "event": "X_1=...=X_200=0 for iid Bernoulli(1/100)",
            "variance_formula": "(0-1/2)^2+199*(0-0)^2=1/4",
            "s_abs_formula": "200/100=2", "boundary_squared_formula": "log(800)/2",
            "boundary": math.sqrt(b2),
            "event_probability_formula": "(99/100)^200", "event_probability": float(exact_prob),
            "exact_comparison": "20*99^200 > 100^200", "exact_comparison_passed": True,
            "probability_lower_bound_formula": "exp(-200/99)",
            "probability_lower_bound": math.exp(-200/99)
        },
        "C_at_alpha_1_over_20": {
            "root_equation": "x-log(1+x)=2*log(20)", "x_star": x,
            "optimized_constant_formula": "sqrt(1+x_star)", "optimized_constant": math.sqrt(1+x),
            "rho_at_v_1_over_4_formula": "(1/4)/x_star", "rho_at_v_1_over_4": rstar
        },
        "scope": "Exact arithmetic for the finite event comparison and scalar numerical checks; no simulation, theorem proving, compilation or citation-wide audit."
    }
    (a.output_dir/"checks.json").write_text(json.dumps(results, ensure_ascii=False, indent=2)+"\n")
    print(json.dumps(results, ensure_ascii=False, indent=2))
if __name__ == "__main__":
    main()
