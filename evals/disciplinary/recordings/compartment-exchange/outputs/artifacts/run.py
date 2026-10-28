#!/usr/bin/env python3
"""Offline two-compartment calculation; Python 3.11+, standard library only.

Run: python run.py --input-dir DIR --output-dir NEW
NEW must not exist. Model input and all parameter values are read on each run.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import platform
import re
import sys
import time


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def finite_number(value, name: str, positive: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be numeric")
    value = float(value)
    if not math.isfinite(value) or (positive and value <= 0):
        raise ValueError(f"Invalid {name}: {value}")
    return value


def compute(input_dir: Path) -> dict:
    # All supplied originals are read afresh; the model's volume is not hard-coded.
    originals = {name: (input_dir / name).read_text(encoding="utf-8")
                 for name in ("model.md", "parameters.json", "draft.md", "task.md")}
    p = json.loads(originals["parameters.json"])
    match = re.search(r"各为\s*([0-9]+(?:\.[0-9]+)?)\s*升", originals["model.md"])
    if not match or "无外源、无损失" not in originals["model.md"] or "k(a-b)" not in originals["model.md"]:
        raise ValueError("The supplied model is outside the implemented equal-volume closed exchange model")
    volume = finite_number(float(match.group(1)), "volume_litre", True)
    a0 = finite_number(p["a0"], "a0")
    b0 = finite_number(p["b0"], "b0")
    if min(a0, b0) < 0:
        raise ValueError("Initial concentrations must be nonnegative")
    k = finite_number(p["k_per_hour"], "k_per_hour", True)
    times = [finite_number(t, "times_hours") for t in p["times_hours"]]
    if not times or min(times) < 0:
        raise ValueError("At least one nonnegative comparison time is required")
    steps = [finite_number(h, "euler_steps_hours", True) for h in p["euler_steps_hours"]]
    n_steps = p["n_steps"]
    if isinstance(n_steps, bool) or not isinstance(n_steps, int) or not 1 <= n_steps <= 10000:
        raise ValueError("n_steps must be an integer in [1, 10000]")
    mean = (a0 + b0) / 2
    difference = a0 - b0
    mass0 = volume * (a0 + b0)

    def exact(t):
        d = difference * math.exp(-2 * k * t)
        return mean + d / 2, mean - d / 2

    analytic = []
    for t in times:
        a, b = exact(t)
        analytic.append({"t_hours": t, "a": a, "b": b, "sum_concentration": a + b,
                         "total_amount": volume * (a + b), "difference": a - b,
                         "tau": 2 * k * t,
                         "a_over_mean": a / mean if mean else None,
                         "b_over_mean": b / mean if mean else None})

    def euler(h, n):
        q = 1 - 2 * k * h
        a, b = a0, b0
        rows = []
        for index in range(n + 1):
            t = index * h
            ea, eb = exact(t)
            expected_difference = difference * q ** index
            rows.append({"step": index, "t_hours": t, "a": a, "b": b,
                         "sum_concentration": a + b, "total_amount": volume * (a + b),
                         "exact_a": ea, "exact_b": eb,
                         "error_a": a - ea, "error_b": b - eb,
                         "max_abs_concentration_error": max(abs(a - ea), abs(b - eb)),
                         "difference_recurrence_residual": (a - b) - expected_difference,
                         "mass_residual": volume * (a + b) - mass0,
                         "nonnegative": min(a, b) >= 0})
            if index < n:
                transfer = h * k * (a - b)
                a, b = a - transfer, b + transfer
        return {"h_hours": h, "kh": k * h, "delta_tau": 2 * k * h, "q": q,
                "difference_mode_asymptotically_stable": abs(q) < 1,
                "preserves_nonnegativity_for_all_nonnegative_initial_states": k * h <= 1,
                "difference_nonoscillatory": 0 <= q < 1,
                "first_negative_step": next((row["step"] for row in rows if not row["nonnegative"]), None),
                "rows": rows}

    euler_cases = [euler(h, n_steps) for h in steps]
    horizon = max(times)
    refinement = []
    if horizon > 0:
        for subdivisions in (16, 32, 64, 128, 256):
            h = horizon / subdivisions
            last = euler(h, subdivisions)["rows"][-1]
            refinement.append({"h_hours": h, "n_steps": subdivisions, "t_hours": horizon,
                               "max_abs_concentration_error": last["max_abs_concentration_error"]})
        for index, row in enumerate(refinement):
            row["previous_error_ratio"] = (refinement[index - 1]["max_abs_concentration_error"] /
                                            row["max_abs_concentration_error"]) if index and row["max_abs_concentration_error"] else None
    boundary = euler(1 / k, max(4, n_steps))
    all_rows = [row for case in euler_cases + [boundary] for row in case["rows"]]
    max_mass_residual = max(abs(row["mass_residual"]) for row in all_rows)
    max_recurrence_residual = max(abs(row["difference_recurrence_residual"]) for row in all_rows)
    max_ode_residual = 0.0
    for t in times:
        a, b = exact(t)
        da = -k * difference * math.exp(-2 * k * t)
        db = -da
        max_ode_residual = max(max_ode_residual, abs(da + k * (a - b)), abs(db - k * (a - b)))
    tolerances = {"mass_U": 1e-11 * max(1.0, abs(mass0)),
                  "concentration_U_per_litre": 1e-11 * max(1.0, abs(a0), abs(b0)),
                  "ODE_U_per_litre_per_hour": 1e-11 * max(1.0, k * abs(difference))}
    if (max_mass_residual > tolerances["mass_U"] or
            max_recurrence_residual > tolerances["concentration_U_per_litre"] or
            max_ode_residual > tolerances["ODE_U_per_litre_per_hour"]):
        raise ArithmeticError("The conservation/recurrence/ODE numerical checks exceeded tolerance")
    return {"schema_version": "1.0", "model_scope": "Closed, instantaneously mixed, equal constant volumes; k>0; t>=0",
            "parameters": p, "model_volume_litre": volume,
            "units": {"a_b_mean_difference_errors": "U/litre; U is the unspecified solute amount unit",
                      "time_h": "hour", "k": "hour^-1", "mass": "U", "q_kh_delta_tau_tau": "dimensionless",
                      "concentration_rate_k_times_difference": "U/(litre hour)",
                      "amount_transfer_rate_Vk_times_difference": "U/hour"},
            "invariants": {"sum_concentration": a0 + b0, "total_amount": mass0,
                           "equilibrium_concentration": mean, "difference_decay_rate_per_hour": 2 * k,
                           "relaxation_time_hours": 1 / (2 * k)},
            "analytic_comparison": analytic, "euler_cases": euler_cases,
            "positivity_boundary": boundary, "fixed_horizon_refinement": refinement,
            "numerical_checks": {"max_absolute_mass_residual": max_mass_residual,
                                 "max_absolute_difference_recurrence_residual": max_recurrence_residual,
                                 "max_absolute_ODE_residual": max_ode_residual,
                                 "tolerances_by_quantity": tolerances, "passed": True},
            "limits": ["A finite floating-point check supplements the written derivation, not a universal proof.",
                       "Eigenvalue 1 conserves total amount; stability refers to the difference mode on a fixed-mass subspace.",
                       "The existing model's flux is interpreted as a concentration exchange rate; multiply by volume for amount/time.",
                       "No experimental calibration or real-world extrapolation is performed."]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    start = time.perf_counter()
    input_dir = args.input_dir.resolve(strict=True)
    output_dir = args.output_dir.absolute()
    if output_dir.exists() or output_dir.is_symlink():
        parser.error("--output-dir must not already exist")
    result = compute(input_dir)
    output_dir.mkdir(parents=False, exist_ok=False)
    result_path = output_dir / "results.json"
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    input_hashes = {name: sha256(input_dir / name) for name in ("model.md", "parameters.json", "draft.md", "task.md")}
    script = Path(__file__).resolve()
    summary = {"argv": [sys.executable, *sys.argv], "exit_status": 0,
               "input_sha256": input_hashes, "code_sha256": {script.name: sha256(script)},
               "output_sha256": {"results.json": sha256(result_path)},
               "guidance": "The host's actually read guidance paths are recorded in PROJECT/execution.json; no runtime guidance is required by this portable script.",
               "machine_specific": {"elapsed_seconds": time.perf_counter() - start,
                                    "python": sys.version, "platform": platform.platform()}}
    (output_dir / "execution.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output_dir": str(output_dir), "checks_passed": result["numerical_checks"]["passed"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
