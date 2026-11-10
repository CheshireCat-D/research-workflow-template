#!/usr/bin/env python3
"""Project the two documented legacy ozone tables onto comparable study estimates."""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path


VALUE = "hot_minus_other_ppb"
CASES = {
    "Primary": ("equal_month", "Equal supported months", "Jun Jul Aug Sep"),
    "Sensitivity": ("supported_pooled", "Equal measured days within group", "Jun Jul Aug Sep"),
    "Previous primary": ("all_pooled", "Equal measured days within group", "May Jun Jul Aug Sep"),
}


def source_rows(path, label, required):
    raw = path.read_bytes()
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline=""), strict=True)
    columns = reader.fieldnames or []
    if len(set(columns)) != len(columns) or not {label, VALUE, *required}.issubset(columns):
        raise ValueError(f"{path}: unexpected columns for this legacy format")
    rows = {}
    for row in reader:
        if None in row or None in row.values() or not row[label].strip() or row[label] in rows:
            raise ValueError(f"{path}: ambiguous row at line {reader.line_num}")
        rows[row[label]] = row
    return rows, {"file": str(path), "sha256": hashlib.sha256(raw).hexdigest()}


def project(old_path, new_path, output):
    old, old_source = source_rows(old_path, "group", [])
    new, new_source = source_rows(new_path, "role", ["months", "weighting"])
    if set(old) != {"Hot", "Other", "Hot minus other"} or set(new) != set(CASES):
        raise ValueError("Row labels differ from this documented case. Review the mapping before reuse.")
    if any(old[group][VALUE].strip() for group in ("Hot", "Other")):
        raise ValueError("The proposed exclusions contain contrast values.")
    for label, (_, weighting, months) in CASES.items():
        if (new[label]["weighting"], new[label]["months"]) != (weighting, months):
            raise ValueError(f"{label}: weighting or months differ from the documented estimand")

    def normalized(row, definition):
        key, weighting, months = definition
        return (key, row[VALUE], "ppb", f"Temp >= 85 F vs cooler; {weighting}; {months}")

    old_values = [normalized(old["Hot minus other"], CASES["Previous primary"])]
    new_values = [normalized(new[label], definition) for label, definition in CASES.items()]
    output.mkdir(parents=True, exist_ok=False)
    for name, values in (("old.csv", old_values), ("new.csv", new_values)):
        with (output / name).open("x", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(("estimate_id", "value", "unit", "scope"))
            writer.writerows(values)
    receipt = {
        "old": {**old_source, "selected": {"Hot minus other": "all_pooled"},
                "excluded_group_means": ["Hot", "Other"]},
        "new": {**new_source, "selected": {label: row[0] for label, row in CASES.items()}},
        "value_column": VALUE,
        "assumptions": "The first study brief defines the May-Sep pooled contrast; the early CSV omits its scope. Only contrast rows and the supplied precision are compared.",
    }
    (output / "mapping.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("old", type=Path)
    parser.add_argument("new", type=Path)
    parser.add_argument("output", type=Path, help="new directory for the normalized tables and input identities")
    args = parser.parse_args()
    try:
        project(args.old, args.new, args.output)
    except (ValueError, OSError, csv.Error) as error:
        parser.exit(2, f"{parser.prog}: {error}\n")
