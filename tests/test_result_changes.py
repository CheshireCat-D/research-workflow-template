"""Exercise the user-facing estimate comparison on independent versioned CSVs."""
import csv
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "skills/rw-validation/scripts/compare_results.py"
HEADER = ("estimate_id", "value", "unit", "scope", "artifact")


class ResultChangesTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.old = Path(temp.name) / "v1.csv"
        self.new = Path(temp.name) / "v2.csv"

    def write(self, path, rows, header=HEADER):
        with path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(header)
            writer.writerows(rows)

    def cli(self, *options):
        return subprocess.run([sys.executable, "-B", str(SCRIPT), str(self.old), str(self.new), *options],
                              capture_output=True, text=True, encoding="utf-8",
                              env={**os.environ, "PYTHONIOENCODING": "ascii"})

    def report(self, *options):
        process = self.cli("--format", "json", *options)
        self.assertEqual(process.returncode, 0, process.stderr)
        return json.loads(process.stdout)

    def test_alignment_and_declared_precision(self):
        old = [
            ("monthly", "1.000000000000000000001", "ppb", "June", "figure 1"),
            ("pooled", "5.0100", "ppb", "May–Sep", "figure 2"),
            ("v1-only", "4", "ppb", "August", ""),
        ]
        new = [
            ("pooled", "501e-2", "ppb", "May–Sep", "figure 3"),
            ("new", "4", "ppb", "September", ""),
            ("monthly", "1.000000000000000000002", "ppb", "June", "figure 2"),
        ]
        self.write(self.old, old)
        self.write(self.new, new)
        report = self.report()
        self.assertEqual(report["inputs"]["old"]["sha256"], hashlib.sha256(self.old.read_bytes()).hexdigest())
        self.assertEqual(report["counts"], {"changed": 1, "unchanged": 1, "not_comparable": 0,
                                            "added": 1, "removed": 1})
        indexed = {row["estimate_id"]: row for row in report["rows"]}
        self.assertEqual(indexed["monthly"]["new"]["value"], new[-1][1])
        self.assertEqual(indexed["pooled"]["status"], "unchanged")
        self.assertEqual(indexed["pooled"]["new"]["artifact"], "figure 3")
        self.assertIsNone(indexed["new"]["old"])
        self.assertIsNone(indexed["v1-only"]["new"])

    def test_unit_scope_and_absent_values_require_review(self):
        self.write(self.old, [("gap", "", "ppb", "May–Sep", ""),
                              ("secondary", "1", "", "", "")])
        self.write(self.new, [("gap", "NA", "ppm", "Jun–Sep", ""),
                              ("secondary", "10", "", "", "")])
        rows = self.report()["rows"]
        self.assertTrue(all(row["status"] == "not_comparable" for row in rows))
        self.assertEqual(set(rows[0]["reasons"]), {"unit_changed", "scope_changed:scope", "missing_value"})
        self.assertIsNone(rows[0]["old"]["value"])
        self.assertEqual(set(rows[1]["reasons"]), {"missing_unit", "missing_scope:scope"})

    def test_existing_tables_and_fixed_unit(self):
        header = ("key", "effect", "months", "weight")
        self.write(self.old, [("暑期|差值", "5", "Jun, Jul", "days")], header)
        self.write(self.new, [("暑期|差值", "5.0", "Jun, Jul", "months")], header)
        options = ("--id-column", "key", "--value-column", "effect", "--unit", "ppb",
                   "--scope-column", "months", "--scope-column", "weight")
        row = self.report(*options)["rows"][0]
        self.assertEqual(row["reasons"], ["scope_changed:weight"])
        self.assertEqual(row["old"]["unit"], "ppb")
        markdown = self.cli(*options).stdout
        self.assertIn("暑期\\|差值", markdown)
        self.assertIn("weight=months", markdown)

    def test_bad_input_never_emits_a_partial_report(self):
        row = ["gap", "1", "ppb", "all", ""]
        self.write(self.old, [row])
        for rows, header in [([row, row], HEADER), ([["", *row[1:]]], HEADER),
                             ([["NA", *row[1:]]], HEADER), ([row[:3]], HEADER),
                             ([["gap", "Infinity", *row[2:]]], HEADER),
                             ([row], ("estimate_id", "value", "unit", "unit", "artifact"))]:
            with self.subTest(rows=rows, header=header):
                self.write(self.new, rows, header)
                cmd = self.cli("--format", "json")
                self.assertEqual(cmd.returncode, 2)
                self.assertEqual(cmd.stdout, "")

    def test_cannot_mask_unit_change_with_constant_argument(self):
        self.write(self.old, [("gap", "1", "ppb", "all", "")])
        self.write(self.new, [("gap", "1", "ppm", "all", "")])
        self.assertEqual(self.cli("--unit", "ppb").returncode, 2)
