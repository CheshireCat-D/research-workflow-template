#!/usr/bin/env python3
"""Compare two already-computed estimate tables by stable ID and declared scope."""
import argparse
import csv
from decimal import Decimal, InvalidOperation
import hashlib
import html
import io
import json
from pathlib import Path
import re
import sys


MISSING = {"", "na", "n/a"}
STATUSES = ("changed", "unchanged", "not_comparable", "added", "removed")


def read_table(path, args):
    raw = path.read_bytes()
    reader = csv.reader(io.StringIO(raw.decode("utf-8-sig"), newline=""), strict=True)
    header = next(reader, [])
    if not header or any(not column.strip() for column in header) or len(set(header)) != len(header):
        raise ValueError(f"{path}: a unique nonblank header is required")
    unit_column = args.unit_column or "unit"
    artifact_column = args.artifact_column or "artifact"
    fields = [args.id_column, args.value_column, *args.scope_column]
    if args.unit is None or unit_column in header:
        fields.append(unit_column)
    if args.artifact_column or artifact_column in header:
        fields.append(artifact_column)
    if len(fields) != len(set(fields)):
        raise ValueError(f"{path}: ID, value, unit, scope and artifact need distinct columns")
    missing = set(fields) - set(header)
    if missing:
        raise ValueError(f"{path}: missing columns {', '.join(sorted(missing))}")

    rows = {}
    for cells in reader:
        if not cells:
            continue
        where = f"{path}, line {reader.line_num}"
        if len(cells) != len(header):
            raise ValueError(f"{where}: expected {len(header)} fields, got {len(cells)}")
        row = dict(zip(header, (cell.strip() for cell in cells)))
        key = row[args.id_column]
        if key.casefold() in MISSING:
            raise ValueError(f"{where}: missing estimate ID")
        if key in rows:
            raise ValueError(f"{where}: duplicate estimate ID {key!r}")
        value = row[args.value_column]
        if value.casefold() in MISSING:
            value = None
        else:
            try:
                valid_number = Decimal(value).is_finite() and "_" not in value
            except InvalidOperation:
                valid_number = False
            if not valid_number:
                raise ValueError(f"{where}: expected a finite decimal or missing value for {key!r}")
        unit = row.get(unit_column, args.unit)
        if args.unit is not None and unit != args.unit:
            raise ValueError(f"{where}: declared unit differs from --unit for {key!r}")
        rows[key] = {"value": value, "unit": unit,
                     "scope": {field: row[field] for field in args.scope_column}}
        if artifact_column in row and row[artifact_column]:
            rows[key]["artifact"] = row[artifact_column]
    return {"file": str(path), "sha256": hashlib.sha256(raw).hexdigest()}, rows


def compare(old, new):
    if old is None:
        return "added", []
    if new is None:
        return "removed", []
    reasons = []
    if any(side["unit"].casefold() in MISSING for side in (old, new)):
        reasons.append("missing_unit")
    elif old["unit"] != new["unit"]:
        reasons.append("unit_changed")
    for field, old_scope in old["scope"].items():
        new_scope = new["scope"][field]
        if old_scope.casefold() in MISSING or new_scope.casefold() in MISSING:
            reasons.append(f"missing_scope:{field}")
        elif old_scope != new_scope:
            reasons.append(f"scope_changed:{field}")
    if old["value"] is None or new["value"] is None:
        reasons.append("missing_value")
    if reasons:
        return "not_comparable", reasons
    if Decimal(old["value"]) == Decimal(new["value"]):
        return "unchanged", []
    return "changed", []


def table_cell(value):
    value = html.escape(value, quote=False)
    value = re.sub(r"([\\|`*_\[\]~])", r"\\\1", value)
    return " ".join(value.splitlines())


def side_text(side):
    if side is None:
        return "—"
    parts = [side["value"] if side["value"] is not None else "NA", side["unit"]]
    parts.extend(f"{k}={v}" for k, v in side["scope"].items())
    if "artifact" in side:
        parts.append(side["artifact"])
    return table_cell(" · ".join(parts))


def markdown(report):
    lines = ["# Recomputed estimates", "", "| Estimate | Status | Previous | Current | Reason |",
             "|---|---|---|---|---|"]
    for row in report["rows"]:
        fields = [table_cell(row["estimate_id"]), row["status"], side_text(row["old"]),
                  side_text(row["new"]), table_cell(", ".join(row["reasons"]))]
        lines.append("| " + " | ".join(fields) + " |")
    lines.append("")
    for side, source in report["inputs"].items():
        lines.append(f"- {side}: {table_cell(source['file'])} (SHA-256 {source['sha256']})")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("old", type=Path, help="previous UTF-8 CSV")
    parser.add_argument("new", type=Path, help="recomputed UTF-8 CSV")
    parser.add_argument("--id-column", default="estimate_id")
    parser.add_argument("--value-column", default="value")
    units = parser.add_mutually_exclusive_group()
    units.add_argument("--unit-column", help="unit column (default: unit)")
    units.add_argument("--unit", help="explicit unit for both files when fixed by their source")
    parser.add_argument("--scope-column", action="append",
                        help="column defining the estimand or population; repeat for multiple columns (default: scope)")
    parser.add_argument("--artifact-column", help="output or figure reference (auto-detects artifact)")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    args = parser.parse_args()
    args.scope_column = args.scope_column or ["scope"]
    if args.unit is not None:
        args.unit = args.unit.strip()
        if args.unit.casefold() in MISSING:
            parser.error("--unit requires an explicit unit")
    try:
        old_source, old_rows = read_table(args.old, args)
        new_source, new_rows = read_table(args.new, args)
    except (OSError, UnicodeError, csv.Error, ValueError) as exc:
        parser.exit(2, f"{parser.prog}: {exc}\n")

    rows = []
    counts = dict.fromkeys(STATUSES, 0)
    for key in dict.fromkeys([*old_rows, *new_rows]):
        old, new = old_rows.get(key), new_rows.get(key)
        status, reasons = compare(old, new)
        rows.append({"estimate_id": key, "status": status, "old": old, "new": new, "reasons": reasons})
        counts[status] += 1
    report = {"inputs": {"old": old_source, "new": new_source}, "counts": counts, "rows": rows}
    print(json.dumps(report, ensure_ascii=False, indent=2) if args.format == "json" else markdown(report))


if __name__ == "__main__":
    # Persist readable reports even on hosts with legacy pipe encodings.
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    main()
