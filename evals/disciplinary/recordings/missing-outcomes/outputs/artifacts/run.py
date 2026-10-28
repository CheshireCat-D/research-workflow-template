#!/usr/bin/env python3
"""Offline standard-library analysis of the supplied two-arm binary trial.

Python 3.11+. Run with --input-dir DIR --output-dir NEW. NEW must not exist.
Protocol counts and all event counts are read anew; no input-directory path or
precomputed result is embedded in this program.
"""
import argparse
import csv
from fractions import Fraction
import hashlib
import itertools
import json
import math
from pathlib import Path
import re
import sys


def value(x):
    return {"fraction": str(x), "decimal": float(x),
            "percentage_points": float(100 * x)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.output_dir.exists() or args.output_dir.is_symlink():
        parser.error("--output-dir must not already exist")
    names = ["task.md", "protocol.md", "outcomes.csv", "draft.md"]
    raw = {name: (args.input_dir / name).read_bytes() for name in names}
    texts = {name: data.decode("utf-8-sig") for name, data in raw.items()}
    protocol = texts["protocol.md"]
    size = re.search(r"各随机分配\s*(\d+)\s*人", protocol)
    endpoint = re.search(r"第\s*(\d+)\s*天", protocol)
    contrast = re.search(r"比较\s*([A-Za-z]+)\s*减\s*([A-Za-z]+)\s*的风险差", protocol)
    if not (size and endpoint and contrast):
        raise ValueError("Protocol must state equal randomization counts, day and risk contrast")
    expected_n = int(size.group(1))
    if expected_n <= 0:
        raise ValueError("Randomization count must be positive")
    arms = list(contrast.groups())
    if len(set(arms)) != 2:
        raise ValueError("Contrast needs two distinct arms")
    reader = csv.DictReader(texts["outcomes.csv"].splitlines())
    if reader.fieldnames != ["id", "arm", "event"]:
        raise ValueError("CSV must have id,arm,event columns")
    rows = list(reader)
    ids = set()
    groups = {arm: {"events": 0, "observed": 0, "randomized": 0,
                    "missing_ids": []} for arm in arms}
    for row in rows:
        person, arm, event = row["id"], row["arm"], row["event"]
        if not person or person in ids:
            raise ValueError("IDs must be nonempty and unique")
        ids.add(person)
        if arm not in groups or event not in ("", "0", "1"):
            raise ValueError("Unknown arm or event outside 0,1,blank")
        g = groups[arm]
        g["randomized"] += 1
        if event == "":
            g["missing_ids"].append(person)
        else:
            g["observed"] += 1
            g["events"] += int(event)
    for arm, g in groups.items():
        if g["randomized"] != expected_n or g["observed"] == 0:
            raise ValueError("CSV randomized counts disagree with protocol or no observed cases")
        g["missing"] = len(g["missing_ids"])
        g["observed_nonevents"] = g["observed"] - g["events"]
        g["complete_case_risk"] = value(Fraction(g["events"], g["observed"]))
        g["risk_bounds"] = [value(Fraction(g["events"], expected_n)),
                            value(Fraction(g["events"] + g["missing"], expected_n))]
    ga, gb = [groups[a] for a in arms]
    cc_rd = Fraction(ga["events"], ga["observed"]) - Fraction(gb["events"], gb["observed"])
    combinations = []
    for ma, mb in itertools.product(range(ga["missing"] + 1), range(gb["missing"] + 1)):
        pa = Fraction(ga["events"] + ma, ga["randomized"])
        pb = Fraction(gb["events"] + mb, gb["randomized"])
        rd = pa - pb
        combinations.append({"missing_events": dict(zip(arms, (ma, mb))),
                             "risks": dict(zip(arms, (value(pa), value(pb)))),
                             "risk_difference": value(rd),
                             "sign": "negative" if rd < 0 else "positive" if rd > 0 else "zero",
                             "individual_completion_count": math.comb(ga["missing"], ma) * math.comb(gb["missing"], mb),
                             "reverses_complete_case_direction": cc_rd * rd < 0})
    all_rd = [Fraction(x["risk_difference"]["fraction"]) for x in combinations]
    lower, upper = min(all_rd), max(all_rd)
    boundary = lambda ma, mb: next(x for x in combinations if x["missing_events"] == dict(zip(arms, (ma, mb))))
    completions = []
    missing_people = [(arm, person) for arm in arms for person in groups[arm]["missing_ids"]]
    for bits in itertools.product((0, 1), repeat=len(missing_people)):
        extra = {arm: 0 for arm in arms}
        assignments = {}
        for (arm, person), bit in zip(missing_people, bits):
            extra[arm] += bit
            assignments[person] = bit
        rd = Fraction(ga["events"] + extra[arms[0]], ga["randomized"]) - Fraction(gb["events"] + extra[arms[1]], gb["randomized"])
        completions.append({"assigned_missing_outcomes": assignments, "risk_difference": value(rd)})
    assert len(combinations) == (ga["missing"] + 1) * (gb["missing"] + 1)
    assert sum(x["individual_completion_count"] for x in combinations) == 2 ** len(missing_people)
    assert set(Fraction(x["risk_difference"]["fraction"]) for x in completions) == set(all_rd)
    results = {
        "input_sha256": {n: hashlib.sha256(raw[n]).hexdigest() for n in names},
        "design": {"independent_unit": "person", "randomization_level": "person, as specified by synthetic protocol",
                   "endpoint_day": int(endpoint.group(1)), "endpoint": "binary adverse event",
                   "contrast": arms[0] + " minus " + arms[1], "missing_policy": "blank remains missing; no imputation"},
        "groups": groups,
        "complete_case_risk_difference": value(cc_rd),
        "assigned_cohort_risk_difference_bounds": {"lower": value(lower), "upper": value(upper),
            "meaning": "sharp extreme bounds from all missing outcomes; not a confidence interval"},
        "count_combinations": combinations,
        "extreme_scenarios": {
            "A_lower_B_upper": boundary(0, gb["missing"]),
            "A_upper_B_lower": boundary(ga["missing"], 0),
            "all_missing_nonevents": boundary(0, 0),
            "all_missing_events": boundary(ga["missing"], gb["missing"])},
        "individual_completions": completions,
        "conclusions": {"complete_case_direction_robust": all(cc_rd * rd > 0 for rd in all_rd),
            "strict_reversal_combinations": [x["missing_events"] for x in combinations if x["reverses_complete_case_direction"]],
            "equality_combinations": [x["missing_events"] for x in combinations if x["sign"] == "zero"],
            "missingness_mechanism": "not supplied; MCAR, MAR and MNAR not established",
            "interpretation": "Observed-case descriptive comparison; full assigned-cohort contrast not point identified. No clinical recommendation."},
        "validation": {"protocol_csv_counts_agree": True, "ids_unique": True,
                       "count_combinations": len(combinations), "individual_completions": len(completions),
                       "fraction_arithmetic": True, "microstate_and_count_grid_agree": True}}
    args.output_dir.mkdir(parents=True, exist_ok=False)
    (args.output_dir / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "completed", "count_combinations": len(combinations),
                      "individual_completions": len(completions), "bounds": [str(lower), str(upper)]}))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, csv.Error) as error:
        print(f"analysis failed: {error}", file=sys.stderr)
        sys.exit(1)
