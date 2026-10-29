"""Synthetic, pen-summary-only descriptive investigation. Standard library only."""
import csv
import hashlib
import json
import math
import sys
from pathlib import Path


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def t3_cdf(t):
    x = t / math.sqrt(3.0)
    return 0.5 + (math.atan(x) + x / (1.0 + x * x)) / math.pi


def main():
    source = Path(sys.argv[1])
    target = Path(sys.argv[2])
    with source.open(newline="") as f:
        rows = list(csv.DictReader(f))
    expected = {"block", "pen", "treatment", "bird_count", "mean_live_weight_kg"}
    assert set(rows[0]) == expected
    assert len(rows) == 8
    assert len({r["pen"] for r in rows}) == 8
    blocks = {}
    for row in rows:
        assert row["treatment"] in {"control", "B"}
        assert int(row["bird_count"]) == 18
        assert math.isfinite(float(row["mean_live_weight_kg"]))
        block = blocks.setdefault(row["block"], {})
        assert row["treatment"] not in block
        block[row["treatment"]] = float(row["mean_live_weight_kg"])
    assert len(blocks) == 4
    assert all(set(v) == {"control", "B"} for v in blocks.values())
    diffs = [{"block": k, "B_minus_control_kg": v["B"] - v["control"]}
             for k, v in sorted(blocks.items())]
    ds = [r["B_minus_control_kg"] for r in diffs]
    n = len(ds)
    mean = math.fsum(ds) / n
    sample_sd = math.sqrt(math.fsum((d - mean) ** 2 for d in ds) / (n - 1))
    se = sample_sd / math.sqrt(n)
    lo, hi = 0.0, 10.0
    for _ in range(100):
        mid = (lo + hi) / 2
        if t3_cdf(mid) < .975:
            lo = mid
        else:
            hi = mid
    critical = (lo + hi) / 2
    interval = [mean - critical * se, mean + critical * se]
    group_means = {t: math.fsum(float(r["mean_live_weight_kg"])
                               for r in rows if r["treatment"] == t) / 4
                   for t in ["control", "B"]}
    assert math.isclose(group_means["B"] - group_means["control"], mean, abs_tol=1e-12)
    leave_one = [{"omitted_block": diffs[i]["block"],
                  "mean_B_minus_control_kg": math.fsum(ds[:i] + ds[i + 1:]) / (n - 1)}
                 for i in range(n)]
    out = {
        "synthetic": True,
        "input_file": source.name,
        "input_sha256": sha256(source),
        "unit": "kg",
        "rows_are": "pen summaries; no individual observations reconstructed",
        "checks": {"rows": len(rows), "distinct_pens": 8, "blocks": 4,
                   "pens_per_treatment": 4, "reported_count_per_pen": 18,
                   "sum_of_reported_counts": sum(int(r["bird_count"]) for r in rows),
                   "missing_fields": 0,
                   "randomization_documented": False,
                   "within_pen_variance_available": False,
                   "woody_breast_available": False},
        "group_mean_of_pen_means_kg": group_means,
        "within_block_differences": diffs,
        "mean_B_minus_control_kg": mean,
        "sample_sd_of_block_differences_kg": sample_sd,
        "conditional_model_standard_error_kg": se,
        "conditional_normal_block_difference_interval": {
            "confidence_level": .95, "degrees_of_freedom": 3,
            "t_critical": critical, "bounds_kg": interval,
            "assumptions": "four independent, identically distributed normal block differences",
            "interpretation": "conditional model illustration, not a documented randomization or causal interval"},
        "leave_one_block_out": leave_one,
        "not_identified": ["bird-level variation", "within-pen variance", "ICC",
                           "effect of measuring 5 versus 10 birds per pen",
                           "power", "woody-breast endpoint", "actual feed efficacy"]}
    target.write_text(json.dumps(out, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"passed": True, "synthetic": True,
                      "mean_difference_g": 1000 * mean,
                      "conditional_95_percent_bounds_g": [1000 * x for x in interval],
                      "output_sha256": sha256(target)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
