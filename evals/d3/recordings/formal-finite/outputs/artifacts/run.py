#!/usr/bin/env python3
"""Exact finite inspection. Run from PROJECT: python3 artifacts/run.py.
Only standard library; paths are resolved relative to this script's PROJECT.
No claim of a proof about unenumerated n is made by this program.
"""
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import signal
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]
START = time.perf_counter()


def fingerprint(path):
    data = path.read_bytes()
    return {"path": str(path.relative_to(ROOT)), "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest()}


def trial(m):
    if m <= 1:
        return {"value": m, "prime": False, "classification": "neither", "tested_divisors": [],
                "sqrt_floor": None, "factor": None, "cofactor": None}
    tested = []
    bound = math.isqrt(m)
    for d in range(2, bound + 1):
        tested.append(d)
        if m % d == 0:
            return {"value": m, "prime": False, "classification": "composite",
                    "tested_divisors": tested, "sqrt_floor": bound,
                    "factor": d, "cofactor": m // d}
    return {"value": m, "prime": True, "classification": "prime", "tested_divisors": tested,
            "sqrt_floor": bound, "factor": None, "cofactor": None}


def sieve(bound):
    prime = bytearray(b"\x01") * (bound + 1)
    prime[0:2] = b"\x00\x00"
    for p in range(2, math.isqrt(bound) + 1):
        if prime[p]:
            for multiple in range(p * p, bound + 1, p):
                prime[multiple] = 0
    return prime


def alarm_handler(signum, frame):
    raise TimeoutError("10 second hard execution budget exceeded")


def main():
    signal.signal(signal.SIGALRM, alarm_handler)
    signal.alarm(10)
    config = json.loads((ROOT / "artifacts/config.json").read_text())
    environment = {"python": sys.version, "executable": sys.executable,
                   "platform": platform.platform(), "machine": platform.machine(),
                   "implementation": platform.python_implementation(), "cwd": os.getcwd(),
                   "dependencies": "Python standard library only", "clock": "time.perf_counter",
                   "deterministic": True, "random_seed": None}
    input_files = sorted((ROOT / "inputs").iterdir())
    fingerprints = [fingerprint(p) for p in input_files]
    (ROOT / "artifacts/input-fingerprints.json").write_text(
        json.dumps(fingerprints, ensure_ascii=False, indent=2) + "\n")
    failures = []
    benchmarks = []
    for m, expected in [(0, False), (1, False), (2, True), (3, True), (4, False),
                        (17, True), (289, False), (323, False), (437, False)]:
        result = trial(m)
        ok = result["prime"] == expected
        if not ok:
            failures.append(f"benchmark {m}")
        benchmarks.append({"input": m, "expected_prime": expected, "actual": result, "passed": ok})
    rows = []
    with (ROOT / config["input_csv"]).open(newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != ["n", "q_n", "reported_prime"]:
            raise ValueError("unexpected CSV columns")
        for line, row in enumerate(reader, 2):
            n, stored = int(row["n"]), int(row["q_n"])
            if row["reported_prime"] not in ("true", "false"):
                raise ValueError(f"invalid Boolean at line {line}")
            reported = row["reported_prime"] == "true"
            actual = n * n - n + 17
            computed = trial(actual)
            stored_check = trial(stored)
            rows.append({"line": line, "n": n, "stored_q_n": stored,
                         "recomputed_q_n": actual, "value_matches": stored == actual,
                         "reported_prime": reported,
                         "reported_status_matches_polynomial": reported == computed["prime"],
                         "reported_status_matches_stored_value": reported == stored_check["prime"],
                         "polynomial_primality": computed, "stored_value_primality": stored_check})
    csv_shape = {"expected_n": config["expected_csv_n"], "actual_n": [r["n"] for r in rows],
                 "count": len(rows), "duplicates": len(rows) != len({r["n"] for r in rows}),
                 "exact_order_and_range": [r["n"] for r in rows] == config["expected_csv_n"]}
    if not csv_shape["exact_order_and_range"]:
        failures.append("CSV indexes differ from declared 0..16")
    if any(not r["value_matches"] or not r["reported_status_matches_polynomial"] or
           not r["reported_status_matches_stored_value"] for r in rows):
        failures.append("CSV discrepancy found")
    all_rows = []
    for n in range(config["n_min"], config["n_max"] + 1):
        all_rows.append({"n": n, "q_n": n * n - n + 17, **trial(n * n - n + 17)})
    upper = max(r["q_n"] for r in all_rows)
    independently_prime = sieve(upper)
    disagreements = [r["n"] for r in all_rows if r["prime"] != bool(independently_prime[r["q_n"]])]
    if disagreements:
        failures.append("trial/sieve disagreement")
    witnesses_ok = all(1 < r["factor"] < r["q_n"] and r["factor"] * r["cofactor"] == r["q_n"]
                       for r in all_rows if not r["prime"])
    if not witnesses_ok:
        failures.append("invalid composite factor witness")
    composite_rows = [r for r in all_rows if not r["prime"]]
    initial_prime_end = next(r["n"] for r in all_rows if not r["prime"]) - 1
    residue_table = [{"p": p, "minus67_mod_p": (-67) % p,
                      "quadratic_residues": sorted({x * x % p for x in range(p)}),
                      "minus67_is_square": (-67) % p in {x * x % p for x in range(p)}}
                     for p in (3, 5, 7, 11, 13)]
    elapsed = time.perf_counter() - START
    result = {"scope": "Exact finite n=0..200 only; not an all-n proof", "config": config,
              "environment": environment, "input_fingerprints": fingerprints,
              "code_fingerprint": fingerprint(ROOT / "artifacts/run.py"),
              "config_fingerprint": fingerprint(ROOT / "artifacts/config.json"),
              "benchmarks": benchmarks, "csv_shape": csv_shape, "csv_checks": rows,
              "range": {"inclusive_min": config["n_min"], "inclusive_max": config["n_max"],
                        "requested_count": 201, "completed_count": len(all_rows), "skipped_n": []},
              "method": {"primary": config["primary_algorithm"],
                         "independent_check": "Eratosthenes sieve of all integers 0..39817",
                         "integer_only": True, "sieve_upper_bound": upper,
                         "disagreement_n": disagreements, "all_factor_witnesses_valid": witnesses_ok},
              "summary": {"prime_count": sum(r["prime"] for r in all_rows),
                          "composite_count": len(composite_rows),
                          "initial_consecutive_prime_range": [0, initial_prime_end],
                          "first_composite": composite_rows[0],
                          "composite_n": [r["n"] for r in composite_rows],
                          "csv_all_values_match": all(r["value_matches"] for r in rows),
                          "csv_all_reported_statuses_match": all(r["reported_status_matches_polynomial"] for r in rows)},
              "residue_table_crosscheck": residue_table, "finite_checks": all_rows,
              "timing": {"elapsed_seconds": elapsed, "budget_seconds": 10,
                         "within_budget": elapsed < 10},
              "failures": failures, "exit_code": 0 if not failures else 1,
              "limitations": ["finite algorithm output alone does not prove any infinite claim",
                              "no proof assistant or human independent review used",
                              "no external literature, novelty or publication assessment"]}
    (ROOT / "artifacts/environment.json").write_text(json.dumps(environment, ensure_ascii=False, indent=2) + "\n")
    (ROOT / "artifacts/results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    signal.alarm(0)
    print(json.dumps({"completed": len(all_rows), "summary": result["summary"],
                      "elapsed_seconds": elapsed, "failures": failures,
                      "sieve_disagreements": disagreements}, ensure_ascii=False))
    return result["exit_code"]


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        failure = {"exception": type(exc).__name__, "message": str(exc),
                   "elapsed_seconds": time.perf_counter() - START, "exit_code": 2,
                   "traceback": traceback.format_exc()}
        (ROOT / "artifacts/failure.json").write_text(json.dumps(failure, indent=2) + "\n")
        print(json.dumps(failure), file=sys.stderr)
        raise SystemExit(2)
