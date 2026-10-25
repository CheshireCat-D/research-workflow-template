#!/usr/bin/env python3
"""Deterministic, stdlib-only fixed-budget quadrature comparison.

Run from any directory; inputs are resolved relative to this source file.
Use --output-dir with a fresh destination for a rerun. Existing output files
are never overwritten. Timing is recorded solely to check the run constraint.
"""
import argparse
import csv
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import platform
import resource
import statistics
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]
TIE_TOLERANCE = 1e-12
BASELINE_TOLERANCE = 1e-13
FUNCTIONS = {
    "quadratic": ("x**2", lambda x: x**2, "1/3", lambda: 1/3),
    "exponential": ("exp(x)", math.exp, "exp(1)-1", lambda: math.exp(1)-1),
    "root": ("sqrt(x)", math.sqrt, "2/3", lambda: 2/3),
    "oscillation": ("cos(18*pi*x)", lambda x: math.cos(18*math.pi*x), "0", lambda: 0.0),
    "kink": ("abs(x-0.37)", lambda x: abs(x-0.37), "(0.37**2+0.63**2)/2", lambda: (0.37**2+0.63**2)/2),
    "rational": ("1/(1+25*x**2)", lambda x: 1/(1+25*x**2), "atan(5)/5", lambda: math.atan(5)/5),
}


class Counted:
    def __init__(self, function):
        self.function, self.calls = function, 0

    def __call__(self, x):
        self.calls += 1
        return self.function(x)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def invoke(method, function, n):
    counted = Counted(function)
    start = time.perf_counter()
    try:
        value = method(counted, n)
        failure = None if math.isfinite(value) else "non-finite estimate: " + repr(value)
        value = value if math.isfinite(value) else None
    except Exception:
        value, failure = None, traceback.format_exc()
    return value, counted.calls, time.perf_counter()-start, failure


def json_write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+"\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT/"artifacts")
    args = parser.parse_args()
    out = args.output_dir.resolve()
    names = ["results.json", "summary.csv", "summary.md", "run.log", "pilot-audit.json"]
    if any((out/name).exists() for name in names):
        parser.error("Use a fresh output directory; refusing to overwrite retained results")
    out.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    cpu_started = time.process_time()
    events = []
    failures = []
    limits = {"external_wall_timeout_seconds": 10,
              "extra_memory_hard_limit": "not imposed"}
    try:
        resource.setrlimit(resource.RLIMIT_CPU, (8, 9))
        limits["cpu_limit_setting"] = "set soft=8 and hard=9 CPU seconds"
    except (ValueError, OSError) as exc:
        limits["cpu_limit_setting"] = "not applied: " + repr(exc)
    for name in ("RLIMIT_CPU", "RLIMIT_AS", "RLIMIT_DATA", "RLIMIT_NOFILE"):
        kind = getattr(resource, name, None)
        if kind is not None:
            limits[name] = list(resource.getrlimit(kind))

    spec = importlib.util.spec_from_file_location("fixed_methods", ROOT/"inputs/methods.py")
    methods = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(methods)
    functions = {"midpoint": methods.midpoint, "trapezoid": methods.trapezoid}
    target_spec = json.loads((ROOT/"inputs/targets.json").read_text(encoding="utf-8"))
    budgets = target_spec["function_evaluation_budgets"]
    assert target_spec["domain"] == [0.0, 1.0]
    assert budgets == [9, 33, 129]
    assert len(target_spec["targets"]) == len(FUNCTIONS)
    assert {t["id"] for t in target_spec["targets"]} == set(FUNCTIONS)
    for target in target_spec["targets"]:
        formula, _, reference_expression, _ = FUNCTIONS[target["id"]]
        assert target["formula"] == formula and target["integral"] == reference_expression

    baselines = []
    for budget in budgets:
        for method_name, method in functions.items():
            n = budget if method_name == "midpoint" else budget-1
            for label, function, expected in [
                ("constant", lambda x: 1.0, 1.0),
                ("linear", lambda x: x, 0.5),
                ("quadratic_closed_sum", lambda x: x*x,
                 1/3-1/(12*n*n) if method_name == "midpoint" else 1/3+1/(6*n*n)),
            ]:
                estimate, calls, _, failure = invoke(method, function, n)
                passed = failure is None and calls == budget and abs(estimate-expected) <= BASELINE_TOLERANCE
                row = dict(baseline=label, method=method_name, budget=budget,
                           subintervals=n, actual_function_calls=calls,
                           estimate=estimate, independently_expected=expected,
                           tolerance=BASELINE_TOLERANCE, passed=passed, failure=failure)
                baselines.append(row)
                if not passed:
                    failures.append({"stage": "baseline", "row": row})
    events.append(f"Independent baselines: {sum(r['passed'] for r in baselines)}/{len(baselines)} passed")

    pilot = []
    with (ROOT/"inputs/pilot.csv").open(encoding="utf-8", newline="") as handle:
        for supplied in csv.DictReader(handle):
            target_id, method_name = supplied["target_id"], supplied["method"]
            n = int(supplied["subintervals"])
            _, function, _, reference = FUNCTIONS[target_id]
            estimate, calls, _, failure = invoke(functions[method_name], function, n)
            error = abs(estimate-reference()) if estimate is not None else None
            estimate_delta = estimate-float(supplied["estimate"]) if estimate is not None else None
            error_delta = error-float(supplied["absolute_error"]) if error is not None else None
            consistent = (failure is None and calls == int(supplied["function_calls"])
                          and abs(estimate_delta) <= 2e-14 and abs(error_delta) <= 2e-14)
            row = dict(supplied=supplied, actual_function_calls=calls, recomputed_estimate=estimate,
                       recomputed_absolute_error=error, estimate_delta=estimate_delta,
                       absolute_error_delta=error_delta, agreement_tolerance=2e-14,
                       numerically_consistent=consistent, failure=failure)
            pilot.append(row)
            if not consistent:
                failures.append({"stage": "pilot_audit", "row": row})
    json_write(out/"pilot-audit.json", pilot)
    events.append(f"Pilot recomputation: {sum(r['numerically_consistent'] for r in pilot)}/{len(pilot)} rows consistent; budgets unequal")

    rows = []
    if all(row["passed"] for row in baselines):
        for target in target_spec["targets"]:
            target_id = target["id"]
            _, function, reference_expression, reference_function = FUNCTIONS[target_id]
            reference = reference_function()
            for budget in budgets:
                for method_name, method in functions.items():
                    n = budget if method_name == "midpoint" else budget-1
                    estimate, calls, elapsed, failure = invoke(method, function, n)
                    if calls != budget:
                        failure = (failure or "") + f" function-call count {calls} != budget {budget}"
                    error = abs(estimate-reference) if estimate is not None else None
                    row = dict(target_id=target_id, formula=target["formula"], budget=budget,
                               method=method_name, subintervals=n, actual_function_calls=calls,
                               reference_expression=reference_expression, reference_value=reference,
                               reference_float_hex=reference.hex(), estimate=estimate,
                               estimate_float_hex=estimate.hex() if estimate is not None else None,
                               absolute_error=error, diagnostic_elapsed_seconds=elapsed,
                               status="failed" if failure else "ok", failure=failure)
                    rows.append(row)
                    if failure:
                        failures.append({"stage": "formal_comparison", "row": row})
    else:
        events.append("Formal comparison skipped because independent baselines failed")

    comparisons, summary = [], []
    for budget in budgets:
        wins = dict(midpoint=0, trapezoid=0, tie=0, unavailable=0)
        for target in target_spec["targets"]:
            pair = {r["method"]: r for r in rows if r["target_id"] == target["id"] and r["budget"] == budget}
            if len(pair) != 2 or any(r["status"] != "ok" for r in pair.values()):
                winner, strict = "unavailable", "unavailable"
            else:
                m, t = pair["midpoint"]["absolute_error"], pair["trapezoid"]["absolute_error"]
                strict = "midpoint" if m < t else "trapezoid" if t < m else "tie"
                winner = "tie" if abs(m-t) <= TIE_TOLERANCE else strict
            wins[winner] += 1
            comparisons.append(dict(target_id=target["id"], budget=budget,
                                    winner_with_tolerance=winner, strict_float_winner=strict,
                                    tie_absolute_tolerance=TIE_TOLERANCE))
        for method_name in functions:
            selected = [r for r in rows if r["method"] == method_name and r["budget"] == budget and r["status"] == "ok"]
            errors = [r["absolute_error"] for r in selected]
            summary.append(dict(budget=budget, method=method_name, successful_targets=len(errors),
                                mean_absolute_error=statistics.mean(errors) if errors else None,
                                median_absolute_error=statistics.median(errors) if errors else None,
                                max_absolute_error=max(errors) if errors else None,
                                wins_and_ties=wins))

    elapsed = time.perf_counter()-started
    cpu_seconds = time.process_time()-cpu_started
    usage = resource.getrusage(resource.RUSAGE_SELF)
    config = dict(python_version=sys.version, python_implementation=platform.python_implementation(),
                  platform=platform.platform(), machine=platform.machine(),
                  standard_library_only=True, network_used=False, random_seed=None,
                  random_seed_note="Not applicable: no random process",
                  budgets=budgets, budget_unit="one actual call to integrand f",
                  subinterval_policy={"midpoint": "B", "trapezoid": "B-1"},
                  targets_in_supplied_order=[t["id"] for t in target_spec["targets"]],
                  reference_policy="Supplied exact expressions implemented independently with math/binary64; no certified rounding bound",
                  tie_absolute_tolerance=TIE_TOLERANCE,
                  resource_limits=limits,
                  input_sha256={f"inputs/{p.name}": sha256(p) for p in sorted((ROOT/"inputs").iterdir()) if p.is_file()},
                  code_sha256=sha256(Path(__file__).resolve()),
                  rerun_command="python3 -B artifacts/run.py --output-dir ../fresh-run",
                  expected_formal_rows=36,
                  reference_baseline_and_pilot_calls_excluded_from_formal_budget=True)
    result = dict(configuration=config, independent_baselines=baselines,
                  raw_results=rows, per_target_comparisons=comparisons, summary=summary,
                  failures=failures,
                  execution=dict(wall_seconds=elapsed, cpu_seconds=cpu_seconds,
                                 within_10_second_wall_limit=elapsed < 10,
                                 formal_function_calls=sum(r["actual_function_calls"] for r in rows),
                                 baseline_function_calls=sum(r["actual_function_calls"] for r in baselines),
                                 pilot_function_calls=sum(r["actual_function_calls"] for r in pilot),
                                 max_rss=usage.ru_maxrss,
                                 max_rss_unit="bytes on macOS; KiB on Linux",
                                 successful_formal_rows=sum(r["status"] == "ok" for r in rows),
                                 failed_or_nonfinite_formal_rows=sum(r["status"] != "ok" for r in rows)),
                  timing_interpretation="Diagnostics for resource-limit check only; no speed ranking")
    json_write(out/"results.json", result)
    with (out/"summary.csv").open("w", encoding="utf-8", newline="") as handle:
        fieldnames = ["target_id", "budget", "method", "subintervals", "actual_function_calls", "reference_expression", "reference_value", "estimate", "absolute_error", "status", "failure"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    lines = ["# 正式比较汇总", "", "误差为对附件参考数学表达式的双精度实现之绝对误差。目标等权平均仅描述此固定集合。", "", "|预算|方法|平均绝对误差|中位数|最大值|", "|---:|---|---:|---:|---:|"]
    for row in summary:
        lines.append(f"|{row['budget']}|{row['method']}|{row['mean_absolute_error']:.12g}|{row['median_absolute_error']:.12g}|{row['max_absolute_error']:.12g}|")
    lines.extend(["", "|目标|预算|中点法误差|梯形法误差|按预设阈值判别|", "|---|---:|---:|---:|---|"])
    for comparison in comparisons:
        pair = {r["method"]: r for r in rows if r["target_id"] == comparison["target_id"] and r["budget"] == comparison["budget"]}
        if len(pair) == 2 and all(r["absolute_error"] is not None for r in pair.values()):
            lines.append(f"|{comparison['target_id']}|{comparison['budget']}|{pair['midpoint']['absolute_error']:.12g}|{pair['trapezoid']['absolute_error']:.12g}|{comparison['winner_with_tolerance']}|")
    lines.extend(["", f"18 个独立基准；正式结果 {len(rows)}/36 行；失败记录 {len(failures)}。", f"记录墙钟 {elapsed:.9g} 秒；不据此推断相对速度。", "并列阈值：误差差值≤1e-12。严格浮点比较保存在 results.json。", "完整逐项表见 summary.csv；原始配置、参考表达式和十六进制浮点数见 results.json。"])
    (out/"summary.md").write_text("\n".join(lines)+"\n", encoding="utf-8")
    events.extend([f"Formal rows: {len(rows)}/36; successful={result['execution']['successful_formal_rows']}; failures={len(failures)}", f"Actual formal function calls: {result['execution']['formal_function_calls']}", f"Wall seconds: {elapsed:.9g}; CPU seconds: {cpu_seconds:.9g}", "Random seed: not applicable (deterministic)", "No inference about relative speed"])
    log = "\n".join(events)+"\n"
    (out/"run.log").write_text(log, encoding="utf-8")
    print(log, end="")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if not failures and len(rows) == 36 and elapsed < 10 else 1


if __name__ == "__main__":
    raise SystemExit(main())
