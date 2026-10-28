#!/usr/bin/env python3
"""Compute stratified binary survey ratios and missing-outcome bounds.

Standard library only. Re-reads the supplied case inputs; never overwrites an
existing output directory. Results are exact rational calculations serialized
with decimal summaries. No toolkit or original-directory import is required.
"""

import argparse
import csv
from fractions import Fraction
import hashlib
import io
import json
from pathlib import Path
import sys


def quantity(value):
    value = Fraction(value)
    return {"fraction": str(value), "decimal": float(value),
            "percent": float(100 * value)}


def analyze(input_dir):
    names = ("strata.csv", "sampling.md", "draft.md", "task.md")
    raw = {name: (input_dir / name).read_bytes() for name in names}
    reader = csv.DictReader(io.StringIO(raw["strata.csv"].decode("utf-8-sig")))
    expected = ["stratum", "population", "sampled", "respondents", "yes"]
    if reader.fieldnames != expected:
        raise ValueError(f"CSV columns must be {expected!r}")
    rows, identifiers = [], set()
    for row in reader:
        sid = row["stratum"]
        if not sid or sid in identifiers:
            raise ValueError("Stratum identifiers must be nonempty and unique")
        identifiers.add(sid)
        N, n, r, y = (int(row[key]) for key in expected[1:])
        if not (0 <= y <= r <= n <= N and N > 0 and n > 0 and r > 0):
            raise ValueError(f"Invalid counts or undefined response weight: {sid}")
        rows.append({"stratum": sid, "N": N, "n": n, "r": r, "y": y,
                     "missing": n-r, "w": Fraction(N, n),
                     "adjustment": Fraction(n, r)})
    if not rows:
        raise ValueError("CSV must contain at least one stratum")
    N = sum(a["N"] for a in rows)
    n = sum(a["n"] for a in rows)
    r = sum(a["r"] for a in rows)
    y = sum(a["y"] for a in rows)
    missing = n-r
    weighted_yes = sum(a["w"] * a["y"] for a in rows)
    weighted_response = sum(a["w"] * a["r"] for a in rows)
    weighted_sample = sum(a["w"] * a["n"] for a in rows)
    weighted_missing = sum(a["w"] * a["missing"] for a in rows)
    adjusted_yes = sum(a["w"] * a["adjustment"] * a["y"] for a in rows)
    adjusted_response = sum(a["w"] * a["adjustment"] * a["r"] for a in rows)
    if adjusted_response != N or weighted_sample != N:
        raise AssertionError("Weight denominator identities failed")
    details = []
    for a in rows:
        details.append({"stratum": a["stratum"], "population": a["N"],
                        "sampled": a["n"], "respondents": a["r"], "yes": a["y"],
                        "no_observed": a["r"]-a["y"], "missing": a["missing"],
                        "sampling_probability": quantity(Fraction(a["n"], a["N"])),
                        "response_rate": quantity(Fraction(a["r"], a["n"])),
                        "respondent_yes_rate": quantity(Fraction(a["y"], a["r"])),
                        "design_weight": str(a["w"]),
                        "nonresponse_factor": str(a["adjustment"]),
                        "adjusted_weight": str(a["w"]*a["adjustment"])})
    return {
        "scope": "Offline synthetic stratified binary survey; missingness ranges, not confidence intervals",
        "inputs_sha256": {name: hashlib.sha256(data).hexdigest() for name, data in raw.items()},
        "totals": {"population": N, "sampled": n, "respondents": r,
                   "yes_observed": y, "no_observed": r-y, "missing_sampled": missing,
                   "response_rate": quantity(Fraction(r, n))},
        "strata": details,
        "estimators": {
            "unweighted_respondents": {"formula": "sum(y_h)/sum(r_h)", "numerator": str(y), "denominator": str(r), "value": quantity(Fraction(y, r))},
            "design_weighted_respondents": {"formula": "sum((N_h/n_h)*y_h)/sum((N_h/n_h)*r_h)", "numerator": str(weighted_yes), "denominator": str(weighted_response), "value": quantity(weighted_yes/weighted_response)},
            "nonresponse_adjusted": {"formula": "sum((N_h/n_h)*(n_h/r_h)*y_h)/sum((N_h/n_h)*(n_h/r_h)*r_h)", "numerator": str(adjusted_yes), "denominator": str(adjusted_response), "value": quantity(adjusted_yes/adjusted_response)}},
        "missing_outcome_bounds": {
            "sampled_raw": {"formula": "[sum(y_h)/sum(n_h), sum(y_h+n_h-r_h)/sum(n_h)]", "lower": quantity(Fraction(y, n)), "upper": quantity(Fraction(y+missing, n)), "scope": "Deterministic complete-outcome proportion bounds for all sampled people"},
            "design_weighted": {"formula": "[sum(w_h*y_h)/sum(w_h*n_h), sum(w_h*(y_h+n_h-r_h))/sum(w_h*n_h)]", "lower": quantity(weighted_yes/weighted_sample), "upper": quantity((weighted_yes+weighted_missing)/weighted_sample), "scope": "Extreme-fill range of design-weighted complete-sample population proportion estimator; not deterministic true-population bounds"}},
        "sensitivity": {"formula": "P_w(q)=sum_h w_h*(y_h+(n_h-r_h)*q_h)/sum_h N_h; each q_h in [0,1]", "intercept": quantity(weighted_yes/weighted_sample), "stratum_missing_coefficients": {a["stratum"]: quantity(a["w"]*a["missing"]/weighted_sample) for a in rows}, "nonresponse_assumption_q_h": {a["stratum"]: quantity(Fraction(a["y"], a["r"])) for a in rows if a["missing"]}},
        "assumptions": ["Mutually exclusive exhaustive strata with given N_h; SRS without replacement within each stratum, hence inclusion probability n_h/N_h.", "Binary responses and counts are correctly recorded; no further measurement or frame correction is supplied.", "n_h/r_h adjustment requires respondents to represent nonrespondents within strata for the outcome; supplied materials do not verify it.", "Bounds vary sampled missing binary outcomes only; sampling error and unsampled resident outcomes remain unresolved."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    if args.output_dir.exists():
        parser.error("--output-dir must not already exist")
    result = analyze(args.input_dir)
    args.output_dir.mkdir(parents=True, exist_ok=False)
    (args.output_dir / "results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    print(json.dumps({"written": "results.json", "strata": len(result["strata"]), "status": "completed"}))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, csv.Error) as exc:
        print(f"analysis failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
