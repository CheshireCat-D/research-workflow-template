#!/usr/bin/env python3
"""Recompute this synthetic corpus; stdlib only, no network, relative inputs.

Run from any working directory: python3 /path/to/PROJECT/artifacts/run.py
Writes artifacts/results.json and artifacts/input-fingerprints.json.
"""
import collections
import datetime
import difflib
import hashlib
import json
import platform
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PARAMETERS = {
    "token_pattern": "[a-z]+", "case_transform": "str.lower",
    "target_exact_token": "liberty", "frequency_multiplier": 100,
    "layers": ["ocr", "corrected"], "periods": [1900, 1910],
    "common_edition_family": "E1", "missing_text_policy": "exclude-from-denominator-and-retain-null",
    "aggregation": "sum-target-count / sum-token-count; not mean document frequency",
    "stemming": False, "synonym_merging": False, "automatic_correction": False,
    "randomness": "none; deterministic analysis", "time_limit_seconds": 10,
}


def fingerprint(path):
    data = path.read_bytes()
    return {"path": path.relative_to(ROOT).as_posix(), "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest()}


def tokenize(text):
    return re.findall(r"[a-z]+", text.lower())


def measure(text):
    if text is None:
        return {"available": False, "tokens": None, "total_tokens": None,
                "liberty_count": None, "per_100_tokens": None}
    tokens = tokenize(text)
    count = tokens.count("liberty")
    return {"available": True, "tokens": tokens, "total_tokens": len(tokens),
            "liberty_count": count,
            "per_100_tokens": 100 * count / len(tokens) if tokens else None}


def aggregate(rows, period, layer, edition=None):
    selected = [r for r in rows if r["period"] == period
                and (edition is None or r["edition_id"] == edition)]
    available = [r for r in selected if r[layer]["available"]]
    n = sum(r[layer]["total_tokens"] for r in available)
    c = sum(r[layer]["liberty_count"] for r in available)
    return {"period": period, "edition_id": edition or "all-available",
            "layer": layer, "catalogued_count": len(selected),
            "available_count": len(available),
            "available_ids": [r["id"] for r in available],
            "missing_ids": [r["id"] for r in selected if not r[layer]["available"]],
            "total_tokens": n, "liberty_count": c,
            "per_100_tokens": 100 * c / n if n else None}


def main():
    start = time.perf_counter()
    result = {"case": "self-authored-fictional-digital-humanities",
              "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "parameters": PARAMETERS,
              "environment": {"python": sys.version, "implementation": platform.python_implementation(),
                              "platform": platform.platform(), "machine": platform.machine(),
                              "dependencies": "Python standard library only"},
              "failures": [], "scientific_scope": "descriptive counts in supplied synthetic excerpts only"}
    code = 0
    try:
        result["input_fingerprints"] = [fingerprint(p) for p in sorted((ROOT / "inputs").iterdir()) if p.is_file()]
        result["code_fingerprint"] = fingerprint(Path(__file__).resolve())
        corpus = json.loads((ROOT / "inputs/corpus.json").read_text(encoding="utf-8"))
        result["corpus_version"] = corpus["version"]
        rows = []
        ids = set()
        for d in corpus["documents"]:
            if d["id"] in ids:
                raise ValueError("duplicate document id: " + d["id"])
            ids.add(d["id"])
            row = {k: d[k] for k in ["id", "period", "edition_id", "edition_year", "title", "genre", "text_access"]}
            for layer in PARAMETERS["layers"]:
                if d[layer] is not None and not isinstance(d[layer], str):
                    raise ValueError("non-string text: " + d["id"])
                row[layer] = measure(d[layer])
            if d["text_access"] == "metadata-only" and any(d[x] is not None for x in PARAMETERS["layers"]):
                raise ValueError("metadata-only entry unexpectedly has text: " + d["id"])
            edits = []
            if d["ocr"] is not None and d["corrected"] is not None:
                old, new = row["ocr"]["tokens"], row["corrected"]["tokens"]
                for tag, i, j, k, l in difflib.SequenceMatcher(a=old, b=new, autojunk=False).get_opcodes():
                    if tag != "equal":
                        edits.append({"operation": tag, "ocr_positions_1based": list(range(i + 1, j + 1)),
                                      "ocr_tokens": old[i:j], "corrected_positions_1based": list(range(k + 1, l + 1)),
                                      "corrected_tokens": new[k:l]})
            row["provided_layer_token_edits"] = edits
            rows.append(row)
        result["documents"] = rows
        result["all_period_totals"] = [aggregate(rows, p, l) for p in PARAMETERS["periods"] for l in PARAMETERS["layers"]]
        result["common_E1_totals"] = [aggregate(rows, p, l, "E1") for p in PARAMETERS["periods"] for l in PARAMETERS["layers"]]
        result["edition_period_totals"] = [aggregate(rows, p, l, e) for e in sorted({r["edition_id"] for r in rows})
                                           for p in PARAMETERS["periods"] for l in PARAMETERS["layers"]]
        result["period_differences_per_100_tokens"] = {}
        for name, totals in [("all_available", result["all_period_totals"]), ("common_E1", result["common_E1_totals"])]:
            result["period_differences_per_100_tokens"][name] = {}
            for layer in PARAMETERS["layers"]:
                values = {r["period"]: r["per_100_tokens"] for r in totals if r["layer"] == layer}
                result["period_differences_per_100_tokens"][name][layer] = values[1910] - values[1900]
        result["coverage"] = {"catalogued_documents": len(rows),
                              "available_excerpt_pairs": sum(r["ocr"]["available"] and r["corrected"]["available"] for r in rows),
                              "metadata_only_ids": [r["id"] for r in rows if r["text_access"] == "metadata-only"],
                              "original_scan_images": 0,
                              "layer_token_totals": {l: sum(r[l]["total_tokens"] or 0 for r in rows) for l in PARAMETERS["layers"]}}
    except Exception as exc:
        result["failures"].append({"type": type(exc).__name__, "message": str(exc)})
        code = 1
    elapsed = time.perf_counter() - start
    result["elapsed_seconds"] = elapsed
    if elapsed >= PARAMETERS["time_limit_seconds"]:
        result["failures"].append({"type": "RuntimeLimit", "message": "analysis elapsed at least 10 seconds"})
        code = 1
    result["exit_code"] = code
    (ROOT / "artifacts/results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ROOT / "artifacts/input-fingerprints.json").write_text(json.dumps(result.get("input_fingerprints", []), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"results": "artifacts/results.json", "exit_code": code,
                      "elapsed_seconds": elapsed, "failures": result["failures"]}, ensure_ascii=False))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
