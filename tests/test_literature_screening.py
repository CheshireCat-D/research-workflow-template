"""Reproduce a reviewed screening pass through the public RWT CLI."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / "docs/literature-screening"
CLI = ROOT / "tools/research.py"


class ScreeningHandoff(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.base = Path(directory.name)
        self.project = self.base / "Bennu project"
        self.batch = self.base / "batch.json"
        self.call(CLI, "init", "--output", self.project, "--title", "Bennu", "--language", "en")
        self.input = self.project / "bennu.json"
        shutil.copyfile(CASE / "bennu.json", self.input)

    def call(self, *args, expected=0):
        process = subprocess.run([sys.executable, "-I", "-B", *map(str, args)], cwd=self.base,
                                 text=True, encoding="utf-8", capture_output=True, timeout=30)
        self.assertEqual(process.returncode, expected, process.stdout + process.stderr)
        return process.stdout

    def prepare(self, expected=0):
        self.call(CASE / "prepare_batch.py", "--root", self.project, "--sheet", "bennu.json",
                  "--output", self.batch, expected=expected)

    def test_case_survives_move_and_signals_changed_decisions(self):
        self.prepare()
        original_batch = self.batch.read_bytes()
        self.prepare(expected=2)
        self.assertEqual(original_batch, self.batch.read_bytes())
        action = "Cross-check the Chesley trajectories against the January images."
        register = (CASE / "prepare_batch.py", "--root", self.project, "--sheet", "bennu.json",
                    "--register", self.batch, "--next-action", action, "--runtime", CLI)
        saved = json.loads(self.call(*register))
        self.assertEqual(saved["registered_count"], 9)
        self.assertTrue(saved["screening_sheet_verified"])
        registry = self.project / "records/registry.json"
        snapshot = registry.read_bytes()
        self.call(*register, expected=2)
        self.assertEqual(registry.read_bytes(), snapshot)
        records = json.loads(snapshot)["records"]
        self.assertEqual(set(records["relations"]), {"Bennu.Lauretta"})
        self.assertEqual(records["sources"]["Bennu.NASA"]["data"]["extensions"]["screening"]["decision"], "exclude")
        self.assertEqual(records["sources"]["Bennu.Chesley"]["data"]["content_access"], "partial")
        moved = self.project.rename(self.base / "relocated")
        restored = json.loads(self.call(CLI, "resume", "--root", moved))
        self.assertEqual(restored["next_action"], action)
        self.assertEqual(restored["checkpoint"]["status"], "current")
        self.assertEqual(restored["scientific_validity"], "not-assessed")
        sheet = moved / "bennu.json"
        changed = json.loads(sheet.read_bytes())
        changed["reports"][-1]["reason"] += " A later reviewer amended the overlap question."
        sheet.write_text(json.dumps(changed), encoding="utf-8")
        drift = json.loads(self.call(CLI, "resume", "--root", moved, expected=1))
        self.assertEqual(drift["checkpoint"]["status"], "stale")
        self.assertTrue(drift["needs_review"])
        self.assertIn({"code": "file_changed", "record": "evidence:Bennu", "path": "bennu.json"}, drift["findings"])
        self.assertIn({"code": "activity_stale", "record": "activity:Bennu"}, drift["findings"])
        self.assertEqual((moved / "records/registry.json").read_bytes(), snapshot)

    def test_one_bad_decision_cannot_generate_partial_evidence(self):
        original = self.input.read_bytes()
        for index, patch in (
                (0, {"access": "metadata-only"}),
                (1, {"locator": "https://doi.org/10.1126/science.aay3544"}),
                (1, {"key": "Lauretta"}),
                (2, {"relation": {"kind": "supports", "scope": "x", "rationale": "x"}})):
            with self.subTest(patch=patch):
                sheet = json.loads(original)
                sheet["reports"][index].update(patch)
                self.input.write_text(json.dumps(sheet), encoding="utf-8")
                self.prepare(expected=2)
                self.assertFalse(self.batch.exists())

    def test_pre_save_check_detects_drift_in_sheet_or_batch(self):
        self.prepare()
        save = (CASE / "prepare_batch.py", "--root", self.project, "--sheet", "bennu.json",
                "--register", self.batch, "--next-action", "Review deferred sources")
        registry = self.project / "records/registry.json"
        snapshot = registry.read_bytes()
        original = self.input.read_bytes()
        changed = json.loads(original)
        changed["reports"][0]["decision"] = "exclude"
        changed["reports"][0].pop("relation")
        self.input.write_text(json.dumps(changed), encoding="utf-8")
        self.call(*save, expected=2)
        self.assertEqual(registry.read_bytes(), snapshot)
        self.input.write_bytes(original)
        self.batch.write_text("[]", encoding="utf-8")
        self.call(*save, expected=2)
        self.assertEqual(registry.read_bytes(), snapshot)

    def test_change_during_registration_reports_already_saved_mismatch(self):
        self.prepare()
        # Deterministically interleave an edit after the helper's comparison and
        # immediately before RWT binds the local file. Both real CLI calls run.
        runtime = self.base / "interleaved.py"
        runtime.write_text(
            "from pathlib import Path\nimport runpy, sys\n"
            "if sys.argv[1] == 'register-batch':\n"
            "    sheet = Path(sys.argv[sys.argv.index('--root') + 1]) / 'bennu.json'\n"
            "    sheet.write_bytes(sheet.read_bytes() + b'\\n')\n"
            f"runpy.run_path({str(CLI)!r}, run_name='__main__')\n", encoding="utf-8")
        result = json.loads(self.call(CASE / "prepare_batch.py", "--root", self.project, "--sheet",
                                      "bennu.json", "--register", self.batch, "--runtime", runtime,
                                      "--next-action", "Inspect overlap", expected=1))
        self.assertTrue(result["registered"] and result["checkpoint_saved"])
        self.assertFalse(result["passed"] or result["screening_sheet_verified"])
