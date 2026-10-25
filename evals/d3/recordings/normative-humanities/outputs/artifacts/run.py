#!/usr/bin/env python3
"""Deterministic arithmetic audit of the copied synthetic facts; no causal model."""
from pathlib import Path
import csv, hashlib, itertools, json, re
root = Path(__file__).resolve().parents[1]
facts_path = root / "inputs/facts.csv"
with facts_path.open(encoding="utf-8", newline="") as stream:
    facts = {row["fact_id"]: row for row in csv.DictReader(stream)}
def numbers(fid):
    return [int(x) for x in re.findall(r"[0-9]+", facts[fid]["observation"])]
previous, pilot = numbers("F1")
surveyed, prefer = numbers("F2")
budget, extended, system, phone = numbers("F3")
conflicts, emergency = numbers("F4")
seats, suggested_limit = numbers("F5")
costs = {"paid_extended_hours": extended, "reservation_system": system, "telephone_assistance": phone}
combinations = []
for size in range(4):
    for names in itertools.combinations(costs, size):
        total = sum(costs[name] for name in names)
        combinations.append({"items": list(names), "cost": total, "within_budget": total <= budget, "unallocated_or_shortfall": budget-total})
result = {
    "input": "inputs/facts.csv",
    "input_sha256": hashlib.sha256(facts_path.read_bytes()).hexdigest(),
    "mode": "deterministic arithmetic only",
    "configuration": {"seed": None, "seed_reason": "No random operations; no statistical experiment", "dependencies": "Python standard library", "scope": "Point estimates copied from F1-F5; no uncertainty model"},
    "visits": {"before": previous, "pilot": pilot, "difference": pilot-previous, "percent_change": 100*(pilot-previous)/previous, "unit": "entries, not independent residents", "causal_identification": False},
    "preference": {"surveyed_existing_users": surveyed, "prefer_phone": prefer, "percent_in_this_sample": 100*prefer/surveyed, "population_or_mandatory_identity_support": "not identified"},
    "budget": {"available": budget, "estimates": costs, "combinations": combinations, "anonymous_count_increment": "reported already covered by existing duty; other new work not priced", "normative_weights": "not assigned", "optimal_allocation": "not inferred"},
    "incidents": {"queue_conflicts": conflicts, "emergencies": emergency, "comparative_effect": "not identified", "zero_risk_claim": "not supported"},
    "capacity": {"seats": seats, "staff_suggested_limit": suggested_limit, "independent_safety_assessment": "not provided"}
}
output = root / "artifacts/results.json"
output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
print(json.dumps({"output": "artifacts/results.json", "status": "arithmetic completed; no policy validation"}, ensure_ascii=False))
