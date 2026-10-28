"""Behavioral checks of the standalone read-only revision-plan checker."""

import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "skills/rw-review/scripts/check_revision_plan.py"
# Loading the checker must not create a cache beside its source.
_bytecode_setting = sys.dont_write_bytecode
sys.dont_write_bytecode = True
_spec = importlib.util.spec_from_file_location("revision_plan_checker", SCRIPT)
checker = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(checker)
sys.dont_write_bytecode = _bytecode_setting


def item(item_id="task-a", source_id="review-1", **updates):
    value = {"id": item_id, "source_id": source_id, "severity": "major", "decision": "accept",
             "status": "planned", "depends_on": []}
    value.update(updates)
    return value


def plan(*items, **updates):
    value = {"sources": [{"id": "review-1", "text": "Explain the assumption and revise the example."}],
             "items": list(items or (item(),))}
    value.update(updates)
    return value


class RevisionPlanChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "reply.txt").write_text("We clarified assumption A.\nWe retained the model for reason B.\n", encoding="utf-8")
        (self.root / "draft.txt").write_text("Assumption A now explicitly requires x > 0.\n", encoding="utf-8")
        self.reply = {"path": "reply.txt", "quote": "We clarified assumption A."}
        self.change = {"path": "draft.txt", "quote": "Assumption A now explicitly requires x > 0."}

    def check(self, value, delivery=False):
        return checker.validate_plan(value, self.root, delivery=delivery)

    def assert_code(self, result, code):
        self.assertFalse(result["passed"], result)
        self.assertIn(code, [entry["code"] for entry in result["errors"]], result)

    def run_cli(self, value=None, *arguments, script=SCRIPT, cwd=None):
        path = self.root / "plan.json"
        if value is not None:
            path.write_text(json.dumps(value), encoding="utf-8")
        return subprocess.run([sys.executable, str(script), str(path), *arguments],
                              text=True, capture_output=True, cwd=cwd,
                              env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})

    def test_draft_one_source_multiple_atomic_items_and_dependency_batches(self):
        value = plan(item(effort_hours=1.5), item("task-b", depends_on=["task-a"], effort_hours=2),
                     item("task-c", severity="optional", effort_hours=0), available_hours=4)
        before = copy.deepcopy(value)
        report = self.check(value)
        self.assertTrue(report["passed"], report)
        self.assertEqual(report["batches"], [["task-a", "task-c"], ["task-b"]])
        self.assertTrue(report["dependency_order_complete"])
        self.assertEqual(report["known_effort_hours"], 3.5)
        self.assertEqual(report["budget"], {"status": "within_budget", "available_hours": 4})
        self.assertEqual(len(report["unfinished"]), 3)
        self.assertEqual(value, before)

    def test_delivery_multiple_review_comments_can_share_one_actual_change(self):
        value = plan(item(status="done", reply=self.reply, changes=[self.change]),
                     item("task-b", "review-2", decision="partial", status="done",
                          reply=self.reply, changes=[self.change]),
                     sources=[{"id": "review-1", "text": "Define the assumption."},
                              {"id": "review-2", "text": "Clarify the example's domain."}])
        report = self.check(value, delivery=True)
        self.assertTrue(report["passed"], report)
        self.assertEqual(report["unfinished"], [])

    def test_reasoned_clarification_disagreement_and_deferral_need_no_change(self):
        for decision in ("clarify", "decline", "defer"):
            with self.subTest(decision=decision):
                report = self.check(plan(item(decision=decision, status="done", reason="The stated premise does not apply.",
                                              reply=self.reply)), delivery=True)
                self.assertTrue(report["passed"], report)
                self.assertEqual(len(report["deferred"]), int(decision == "defer"))
                self.assertEqual(len(report["declined"]), int(decision == "decline"))

    def test_completed_item_cannot_skip_an_unfinished_prerequisite(self):
        for delivery in (False, True):
            for status in ("planned", "in_progress", "blocked"):
                with self.subTest(delivery=delivery, prerequisite=status):
                    value = plan(item(status=status, reply=self.reply, changes=[self.change]),
                                 item("task-b", status="done", depends_on=["task-a"],
                                      reply=self.reply, changes=[self.change]))
                    report = self.check(value, delivery=delivery)
                    self.assert_code(report, "incomplete_dependency")
                    value["items"][0]["status"] = "done"
                    self.assertTrue(self.check(value, delivery=delivery)["passed"])

    def test_delivery_unfinished_acceptance_is_reported_without_inventing_readiness(self):
        report = self.check(plan(item(reply=self.reply, status="in_progress")), delivery=True)
        self.assertTrue(report["passed"], report)
        self.assertEqual(report["unfinished"][0]["id"], "task-a")
        self.assertNotIn("submission_ready", report)
        self.assertIn("does not assess scientific correctness", report["scope"])

    def test_delivery_requires_replies_changes_for_done_acceptance_and_decision_reasons(self):
        self.assert_code(self.check(plan(item(status="done")), True), "missing_reply")
        for decision in ("accept", "partial"):
            self.assert_code(self.check(plan(item(status="done", decision=decision, reply=self.reply)), True), "missing_changes")
        for decision in ("clarify", "decline", "defer"):
            self.assert_code(self.check(plan(item(decision=decision, reply=self.reply)), True), "missing_reason")

    def test_cycle_unknown_and_self_dependencies(self):
        cases = [(plan(item(depends_on=["task-b"]), item("task-b", depends_on=["task-a"])), "dependency_cycle"),
                 (plan(item(depends_on=["absent"])), "unknown_dependency"),
                 (plan(item(depends_on=["task-a"])), "self_dependency"),
                 (plan(item(depends_on=["task-b", "task-b"]), item("task-b")), "duplicate_dependency")]
        for value, code in cases:
            with self.subTest(code=code):
                report = self.check(value)
                self.assert_code(report, code)
                self.assertEqual(report["batches"], [])
                self.assertFalse(report["dependency_order_complete"])

    def test_duplicate_empty_and_unknown_ids_and_uncovered_sources(self):
        cases = [(plan(item(), item()), "duplicate_item_id"),
                 (plan(item(), sources=[{"id": "review-1", "text": "a"}, {"id": "review-1", "text": "b"}]), "duplicate_source_id"),
                 (plan(item(" ")), "invalid_item_id"),
                 (plan(item(source_id="missing")), "unknown_source_id"),
                 (plan(item(), sources=[{"id": "review-1", "text": "a"}, {"id": "review-2", "text": "b"}]), "uncovered_source"),
                 (plan(item(), sources=[{"id": "", "text": "a"}]), "invalid_source_id")]
        for value, code in cases:
            with self.subTest(code=code):
                self.assert_code(self.check(value), code)
                delivery_report = self.check(value, delivery=True)
                self.assert_code(delivery_report, code)
                json.dumps(delivery_report, allow_nan=False)

    def test_bad_shapes_enums_and_empty_text_are_readable_errors(self):
        cases = [(None, "invalid_plan"), ([], "invalid_plan"),
                 ({"sources": {}, "items": []}, "invalid_sources"),
                 ({"sources": [], "items": {}}, "invalid_items"),
                 (plan(item(), sources=[{"id": "review-1", "text": " "}]), "invalid_source_text"),
                 (plan(item(severity=[])), "invalid_severity"),
                 (plan(item(decision={})), "invalid_decision"),
                 (plan(item(status="ready")), "invalid_status"),
                 (plan(item(depends_on=None)), "invalid_dependencies"),
                 (plan(item(depends_on=[{}])), "invalid_dependency_id"),
                 (plan(item(changes="draft.txt")), "invalid_changes")]
        for value, code in cases:
            with self.subTest(code=code):
                self.assert_code(self.check(value), code)
                self.assert_code(self.check(value, delivery=True), code)

    def test_empty_sources_or_items_cannot_pass_or_claim_dependency_order(self):
        cases = [(plan(item(reply=self.reply), sources=[]), {"empty_sources"}),
                 (plan(items=[]), {"empty_items"}),
                 ({"sources": [], "items": []}, {"empty_sources", "empty_items"})]
        for delivery in (False, True):
            for value, expected_codes in cases:
                with self.subTest(delivery=delivery, expected_codes=expected_codes):
                    report = self.check(value, delivery=delivery)
                    self.assertFalse(report["passed"], report)
                    self.assertTrue(expected_codes <= {error["code"] for error in report["errors"]}, report)
                    self.assertFalse(report["dependency_order_complete"])
                    self.assertEqual(report["batches"], [])
                    self.assertEqual(report, json.loads(json.dumps(report, allow_nan=False)))

    def test_cli_empty_sources_or_items_return_structured_errors_in_both_modes(self):
        cases = [(plan(item(reply=self.reply), sources=[]), {"empty_sources"}),
                 (plan(items=[]), {"empty_items"}),
                 ({"sources": [], "items": []}, {"empty_sources", "empty_items"})]
        for arguments in ((), ("--delivery",)):
            for value, expected_codes in cases:
                with self.subTest(arguments=arguments, expected_codes=expected_codes):
                    result = self.run_cli(value, *arguments)
                    self.assertEqual(result.returncode, 1)
                    self.assertEqual(result.stderr, "")
                    report = json.loads(result.stdout)
                    self.assertFalse(report["passed"], report)
                    self.assertTrue(expected_codes <= {error["code"] for error in report["errors"]}, report)
                    self.assertFalse(report["dependency_order_complete"])
                    self.assertEqual(report["batches"], [])

    def test_hours_reject_booleans_negative_nonfinite_and_wrong_types(self):
        for hours in (True, False, -1, float("nan"), float("inf"), -float("inf"), "2", None):
            with self.subTest(hours=hours):
                report = self.check(plan(item(effort_hours=hours), available_hours=4))
                self.assert_code(report, "invalid_effort_hours")
                self.assertEqual(report["budget"]["status"], "invalid")
                self.assert_code(self.check(plan(item(), available_hours=hours)), "invalid_available_hours")
                json.dumps(report, allow_nan=False)

    def test_overflowing_total_is_an_error_with_json_safe_null(self):
        report = self.check(plan(item(effort_hours=1e308), item("task-b", effort_hours=1e308), available_hours=1e308))
        self.assert_code(report, "invalid_effort_total")
        self.assertIsNone(report["known_effort_hours"])
        json.dumps(report, allow_nan=False)
        huge = int("9" * 4300)
        result = self.run_cli(plan(item(effort_hours=huge), item("task-b", effort_hours=huge)))
        self.assertEqual(result.returncode, 1)
        self.assert_code(json.loads(result.stdout), "invalid_effort_total")
        self.assertEqual(result.stderr, "")

    def test_decimal_hours_do_not_create_a_spurious_budget_overrun(self):
        report = self.check(plan(item(effort_hours=0.1), item("task-b", effort_hours=0.2), available_hours=0.3))
        self.assertTrue(report["passed"], report)
        self.assertEqual(report["known_effort_hours"], 0.3)

    def test_unknown_effort_cannot_claim_budget_pass_and_known_overrun_is_explicit(self):
        value = plan(item(effort_hours=2), item("task-b"), available_hours=10)
        report = self.check(value)
        self.assert_code(report, "budget_unknown_effort")
        self.assertEqual(report["unknown_effort_items"], ["task-b"])
        self.assertEqual(report["budget"]["status"], "undetermined")
        value["available_hours"] = 1
        report = self.check(value)
        self.assert_code(report, "over_budget")
        self.assertEqual(report["budget"]["status"], "over_budget")
        del value["available_hours"]
        self.assertTrue(self.check(value)["passed"])

    def test_provided_locations_are_checked_even_in_plan_mode(self):
        self.assert_code(self.check(plan(item(reply={"path": "missing.txt", "quote": "anything"}))), "unreadable_location")
        self.assert_code(self.check(plan(item(changes=[{"path": "draft.txt", "quote": "invented evidence"}]))), "quote_not_found")
        self.assert_code(self.check(plan(item(reply={"path": "draft.txt", "quote": " "}))), "invalid_quote")
        self.assert_code(self.check(plan(item(reply=None))), "invalid_locator")
        (self.root / "repeat.txt").write_text("aaaa", encoding="utf-8")
        self.assert_code(self.check(plan(item(reply={"path": "repeat.txt", "quote": "aaa"}))), "ambiguous_quote")
        (self.root / "binary.txt").write_bytes(b"\xff\xfe")
        self.assert_code(self.check(plan(item(reply={"path": "binary.txt", "quote": "text"}))), "unreadable_location")

    def test_quotes_preserve_exact_line_endings(self):
        (self.root / "crlf.txt").write_bytes(b"first\r\nsecond\r\n")
        self.assertTrue(self.check(plan(item(reply={"path": "crlf.txt", "quote": "first\r\nsecond"})))["passed"])
        self.assert_code(self.check(plan(item(reply={"path": "crlf.txt", "quote": "first\nsecond"}))), "quote_not_found")

    def test_absolute_parent_windows_and_symlink_escape_locations_are_rejected(self):
        for name in (str(self.root / "draft.txt"), "../draft.txt", "nested/../../draft.txt", "C:\\draft.txt",
                     "C:draft.txt", "..\\draft.txt", "\\\\server\\share\\draft.txt"):
            with self.subTest(path=name):
                self.assert_code(self.check(plan(item(reply={"path": name, "quote": self.change["quote"]}))), "unsafe_path")
        with tempfile.TemporaryDirectory() as outside:
            target = Path(outside) / "external.txt"
            target.write_text("outside evidence", encoding="utf-8")
            try:
                (self.root / "escape.txt").symlink_to(target)
                (self.root / "escape-dir").symlink_to(outside, target_is_directory=True)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"Symlink creation unavailable: {exc}")
            for name in ("escape.txt", "escape-dir/external.txt"):
                self.assert_code(self.check(plan(item(reply={"path": name, "quote": "outside evidence"}))), "unsafe_path")

    def test_symlink_to_file_within_root_remains_valid(self):
        try:
            (self.root / "alias.txt").symlink_to(self.root / "draft.txt")
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"Symlink creation unavailable: {exc}")
        report = self.check(plan(item(changes=[{"path": "alias.txt", "quote": self.change["quote"]}])))
        self.assertTrue(report["passed"], report)

    def test_cli_json_and_default_root_preserve_all_source_hashes_and_mtimes(self):
        value = plan(item(status="done", reply=self.reply, changes=[self.change], effort_hours=2), available_hours=2)
        (self.root / "plan.json").write_text(json.dumps(value), encoding="utf-8")

        def snapshot():
            return {path.relative_to(self.root).as_posix():
                    (hashlib.sha256(path.read_bytes()).hexdigest(), path.stat().st_mtime_ns)
                    for path in self.root.rglob("*") if path.is_file()}

        before = snapshot()
        result = self.run_cli(None, "--delivery")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)["passed"])
        self.assertEqual(result.stderr, "")
        self.assertEqual(snapshot(), before)
        report = self.check(value, delivery=True)
        self.assertTrue(report["passed"])
        self.assertEqual(snapshot(), before)

    def test_cli_explicit_root_and_script_copied_outside_repository(self):
        value = plan(item(reply=self.reply, changes=[self.change]))
        with tempfile.TemporaryDirectory() as standalone:
            copied_script = Path(standalone) / "checker.py"
            shutil.copyfile(SCRIPT, copied_script)
            result = self.run_cli(value, "--root", str(self.root), script=copied_script, cwd=standalone)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertTrue(report["passed"], report)
            self.assertEqual(set(Path(standalone).iterdir()), {copied_script})

    def test_cli_bad_json_missing_files_and_usage_return_json_without_traceback(self):
        path = self.root / "plan.json"
        for content in ("{bad json", "[]", "[" * 1100 + "]" * 1100):
            path.write_text(content, encoding="utf-8")
            result = self.run_cli()
            self.assertEqual(result.returncode, 1)
            self.assertFalse(json.loads(result.stdout)["passed"])
            self.assertEqual(result.stderr, "")
        path.unlink()
        result = self.run_cli()
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)["errors"][0]["code"], "plan_read_error")
        for arguments in ([], ["--unknown"], ["--root"]):
            result = subprocess.run([sys.executable, str(SCRIPT), *arguments], text=True, capture_output=True)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(json.loads(result.stdout)["errors"][0]["code"], "arguments_error")
            self.assertEqual(result.stderr, "")

    def test_cli_nonfinite_hours_are_rejected_without_nonfinite_json_output(self):
        result = self.run_cli(plan(item(effort_hours=float("nan"))))
        self.assertEqual(result.returncode, 1)
        report = json.loads(result.stdout)
        self.assert_code(report, "invalid_effort_hours")
        self.assertNotIn("NaN", result.stdout)

    def test_cli_invalid_nonfinite_enum_and_escaped_surrogate_do_not_crash(self):
        for value in (plan(item(status=float("nan"))), plan(item("\ud800"))):
            with self.subTest(value=value):
                result = self.run_cli(value)
                self.assertIn(result.returncode, (0, 1), result.stderr)
                json.loads(result.stdout)
                self.assertEqual(result.stderr, "")


if __name__ == "__main__":
    unittest.main()
