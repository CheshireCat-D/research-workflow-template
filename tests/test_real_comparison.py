"""Synthetic record-integrity checks; no scientific answer is generated or graded."""
from contextlib import redirect_stdout
import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "real_comparison_validate", ROOT / "evals/real-comparison/validate.py")
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


class Fixture:
    def __init__(self, root):
        self.root = root
        self.trials = []
        self.write("common.txt", b"Same scientific request for all arms.\n")
        self.dump("rubrics/theory.json", {
            "items": [{"id": "conditions", "points": 60}, {"id": "scope", "points": 40}],
            "total_points": 100,
            "critical_caps": [{"max_total": 49, "trigger": "Unsupported central certification"}],
        })
        self.dump("rubrics/data.json", {"tasks": {
            task: {"items": [{"id": "analysis", "points": 30}, {"id": "scope", "points": 20}],
                   "total_points": 50}
            for task in ("data-a", "data-b")
        }})
        for arm in ("baseline", "rwt", "external"):
            for repeat in (1, 2):
                self.trials.append({"trial_id": f"theory-{arm}-{repeat}", "task_id": "theory",
                                    "arm": arm, "replicate": repeat, "predecessor": None})
            self.trials.extend([
                {"trial_id": f"data-a-{arm}", "task_id": "data-a", "arm": arm,
                 "replicate": 1, "predecessor": None},
                {"trial_id": f"data-b-{arm}", "task_id": "data-b", "arm": arm,
                 "replicate": 1, "predecessor": f"data-a-{arm}"},
            ])
        self.dump("freeze.json", {"files": {
            name: sha((root / name).read_bytes())
            for name in ("common.txt", "rubrics/theory.json", "rubrics/data.json")
        }})
        self.freeze_sha = sha((root / "freeze.json").read_bytes())
        self.dump("study.json", {"expected_trials": self.trials, "freeze_sha256": self.freeze_sha})
        for planned in self.trials:
            trial_id, task = planned["trial_id"], planned["task_id"]
            prefix = "records/" + trial_id
            report = self.ref(prefix + "/report.md", b"Evidence at source section 2.\n")
            execution = self.ref(prefix + "/execution.json", {
                "status": "executed", "requested": copy.deepcopy(VALIDATOR.REQUESTED),
                "effective": {key: None for key in VALIDATOR.EFFECTIVE_FIELDS},
                "tool_calls": 6, "network_calls": 0, "violations": [],
                "reads": [{"logical_name": "task", "sha256": "a" * 64}],
                "duration_seconds": None, "scope": "instruction-only; no OS audit",
            })
            artifacts = self.ref(prefix + "/artifacts.json", {
                "files": [{"path": "unpublished/input.csv", "sha256": "b" * 64,
                           "bytes": 500, "distributed": False}],
                "scope": "Workspace names only; undistributed raw files are not opened.",
            })
            items = [("conditions", 60), ("scope", 40)] if task == "theory" else [
                ("analysis", 30), ("scope", 20)]
            total = sum(points for _, points in items)
            adjudication = self.ref(prefix + "/adjudication.json", {
                "submission_id": "anonymous-" + trial_id, "task_id": task,
                "report_sha256": report["sha256"],
                "scored": True, "arm_hidden": True,
                "criteria": [{"id": identifier, "score": points, "max_points": points,
                              "evidence": "Report paragraph 1", "rationale": "Supported by supplied source."}
                             for identifier, points in items],
                "raw_score": total, "effective_score": total, "max_score": total,
                "critical_errors": [], "caps_applied": [], "usability": "usable", "notes": [],
            })
            self.dump("trials/" + trial_id + ".json", {
                **planned, "freeze_sha256": self.freeze_sha, "report": report,
                "execution": execution, "artifacts": artifacts, "adjudication": adjudication,
            })

    def write(self, name, raw):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)

    def dump(self, name, value):
        self.write(name, json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False).encode())

    def load(self, name):
        return json.loads((self.root / name).read_text())

    def ref(self, name, value):
        if isinstance(value, bytes):
            self.write(name, value)
        else:
            self.dump(name, value)
        return {"path": name, "sha256": sha((self.root / name).read_bytes())}

    def edit(self, trial_id, field, transform):
        trial_path = "trials/" + trial_id + ".json"
        trial = self.load(trial_path)
        name = trial[field]["path"]
        value = self.load(name)
        transform(value)
        trial[field] = self.ref(name, value)
        self.dump(trial_path, trial)

    def terminal_failure(self, trial_id):
        self.edit(trial_id, "execution", lambda entry: entry.update(
            status="failed", terminal_failure=True))
        self.edit(trial_id, "adjudication", lambda entry: entry.update(
            scored=False, raw_score=None, effective_score=None, criteria=[],
            usability="not-assessable", notes=["Execution failed before scientific work."]))
        name = "trials/" + trial_id + ".json"
        trial = self.load(name)
        trial["report"] = None
        self.dump(name, trial)


class RealComparisonRecords(unittest.TestCase):
    def test_published_study_records_close_without_claiming_scientific_validity(self):
        result = VALIDATOR.validate(ROOT / "evals/real-comparison")
        self.assertEqual(result["status"], "complete", result)
        self.assertEqual(result["counts"]["recorded"], 12)
        self.assertEqual(result["counts"]["scored"], 12)
        self.assertEqual(result["effective_model_equality"], "not-inferred")
        self.assertIn("scientific validity not assessed", result["scope"])

    def note_projection(self):
        name = "references/design-provenance.md"
        original, public = b"Organizer local memory locator.\n", b"Organizer logical memory locator.\n"
        self.fixture.write(name, public)
        freeze = self.fixture.load("freeze.json")
        freeze["files"][name] = sha(original)
        self.fixture.dump("freeze.json", freeze)
        study = self.fixture.load("study.json")
        study["freeze_sha256"] = sha((self.root / "freeze.json").read_bytes())
        study["publication_projections"] = {name: {"original_sha256": sha(original),
            "public_sha256": sha(public), "changes": ["machine-path-redaction"]}}
        self.fixture.dump("study.json", study)
        for trial in self.fixture.trials:
            path = "trials/" + trial["trial_id"] + ".json"
            record = self.fixture.load(path)
            record["freeze_sha256"] = study["freeze_sha256"]
            self.fixture.dump(path, record)
        return study

    def test_only_organizer_provenance_can_preserve_raw_freeze_with_path_projection(self):
        self.note_projection()
        result = VALIDATOR.validate(self.root)
        self.assertEqual(result["status"], "complete", result)
        self.assertTrue(any("provenance_publication_projection" in x
                            for x in result["observations"]))

    def test_task_or_rubric_projection_cannot_bypass_scientific_freeze(self):
        study = self.note_projection()
        study["publication_projections"]["common.txt"] = dict(
            next(iter(study["publication_projections"].values())))
        self.fixture.dump("study.json", study)
        self.assertEqual(VALIDATOR.validate(self.root)["status"], "invalid")

    def test_provenance_projection_rejects_wrong_original_identity_or_other_changes(self):
        study = self.note_projection()
        entry = study["publication_projections"]["references/design-provenance.md"]
        entry["original_sha256"] = "0" * 64
        self.fixture.dump("study.json", study)
        self.assertEqual(VALIDATOR.validate(self.root)["status"], "invalid")

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="rw-real-records-")
        self.root = Path(self.temporary.name)
        self.fixture = Fixture(self.root)
        self.theory = "theory-baseline-1"
        self.data = "data-a-baseline"

    def tearDown(self):
        self.temporary.cleanup()

    def result(self):
        return VALIDATOR.validate(self.root)

    def assert_status(self, status):
        result = self.result()
        self.assertEqual(result["status"], status, result)
        return result

    def edit_trial(self, trial_id, transform):
        name = "trials/" + trial_id + ".json"
        value = self.fixture.load(name)
        transform(value)
        self.fixture.dump(name, value)

    def test_complete_records_retain_unknown_settings_and_do_not_claim_scientific_validation(self):
        before = {path: path.read_bytes() for path in self.root.rglob("*") if path.is_file()}
        result = self.assert_status("complete")
        self.assertEqual(result["counts"]["expected"], 12)
        self.assertEqual(result["counts"]["scored"], 12)
        self.assertEqual(result["effective_model_equality"], "not-inferred")
        self.assertIn("scientific validity not assessed", result["scope"])
        self.assertEqual(len(result["observations"][0]["unknown_effective_fields"]), 5)
        self.assertEqual(before, {path: path.read_bytes() for path in before})

    def test_missing_trial_is_incomplete_and_cli_allow_flag_does_not_invent_score(self):
        (self.root / ("trials/" + self.theory + ".json")).unlink()
        result = self.assert_status("incomplete")
        self.assertEqual(result["counts"]["recorded"], 11)
        for allow, expected in ((False, 1), (True, 0)):
            with redirect_stdout(io.StringIO()):
                args = ["--root", str(self.root)] + (["--allow-incomplete"] if allow else [])
                self.assertEqual(VALIDATOR.main(args), expected)

    def test_terminal_failure_closes_record_without_zero_scoring_or_success_count(self):
        self.fixture.terminal_failure(self.theory)
        result = self.assert_status("complete")
        self.assertEqual(result["counts"]["recorded"], 12)
        self.assertEqual(result["counts"]["scored"], 11)
        self.assertEqual(result["counts"]["failed"], 1)
        self.assertEqual(result["counts"]["terminal_failures"], 1)
        self.assertEqual(result["counts"]["executed"], 11)
        trial = self.fixture.load("trials/" + self.theory + ".json")
        self.assertIsNone(self.fixture.load(trial["adjudication"]["path"])["raw_score"])

    def test_failed_with_scored_product_is_record_complete_but_still_failed(self):
        self.fixture.edit(self.theory, "execution", lambda entry: entry.update(status="failed"))
        result = self.assert_status("complete")
        self.assertEqual(result["counts"]["failed"], 1)
        self.assertEqual(result["counts"]["scored"], 12)

    def test_failed_with_no_adjudication_remains_incomplete(self):
        self.fixture.edit(self.theory, "execution", lambda entry: entry.update(status="failed"))
        self.edit_trial(self.theory, lambda trial: trial.update(adjudication=None))
        result = self.assert_status("incomplete")
        self.assertEqual(result["counts"]["failed"], 1)

    def test_terminal_failure_cannot_claim_scored_assessment_without_report(self):
        self.fixture.terminal_failure(self.theory)
        self.fixture.edit(self.theory, "adjudication", lambda entry: entry.update(scored=True))
        self.assert_status("invalid")

    def test_missing_terminal_execution_is_incomplete_instead_of_made_up_failure_state(self):
        self.fixture.terminal_failure(self.theory)
        trial = self.fixture.load("trials/" + self.theory + ".json")
        (self.root / trial["execution"]["path"]).unlink()
        self.assert_status("incomplete")

    def test_not_run_is_incomplete_even_if_an_adjudication_was_attached(self):
        self.fixture.edit(self.theory, "execution", lambda entry: entry.update(status="not-run"))
        self.assert_status("incomplete")

    def test_normal_execution_cannot_claim_terminal_or_null_report(self):
        self.edit_trial(self.theory, lambda trial: trial.update(report=None))
        self.assert_status("invalid")

    def test_unscored_nonterminal_and_terminal_zero_scores_are_rejected(self):
        self.fixture.edit(self.theory, "adjudication", lambda entry: entry.update(
            scored=False, raw_score=None, effective_score=None, criteria=[], usability="not-assessable"))
        self.assert_status("invalid")
        self.fixture.terminal_failure(self.theory)
        self.fixture.edit(self.theory, "adjudication", lambda entry: entry.update(raw_score=0))
        self.assert_status("invalid")

    def test_changed_frozen_input_is_invalid_even_with_allow_incomplete(self):
        self.fixture.write("common.txt", b"Different request")
        self.assert_status("invalid")
        with redirect_stdout(io.StringIO()):
            self.assertEqual(VALIDATOR.main(["--root", str(self.root), "--allow-incomplete"]), 2)

    def test_study_and_trial_must_bind_exact_freeze_bytes(self):
        self.edit_trial(self.theory, lambda trial: trial.update(freeze_sha256="0" * 64))
        self.assert_status("invalid")
        study = self.fixture.load("study.json")
        study["freeze_sha256"] = "f" * 64
        self.fixture.dump("study.json", study)
        self.assert_status("invalid")

    def test_existing_referenced_hash_mismatch_is_not_merely_missing(self):
        trial = self.fixture.load("trials/" + self.theory + ".json")
        self.fixture.write(trial["report"]["path"], b"altered")
        self.assert_status("invalid")

    def test_scored_adjudication_must_bind_the_actual_report(self):
        self.fixture.edit(self.theory, "adjudication", lambda entry: entry.update(
            report_sha256="0" * 64))
        self.assert_status("invalid")

    def test_scored_adjudication_cannot_omit_report_identity(self):
        self.fixture.edit(self.theory, "adjudication", lambda entry: entry.pop("report_sha256"))
        self.assert_status("invalid")

    def test_missing_public_file_is_incomplete_while_undistributed_source_is_not_opened(self):
        self.assert_status("complete")
        self.fixture.edit(self.data, "artifacts", lambda manifest: manifest["files"].append({
            "path": "analysis.py", "sha256": "d" * 64, "bytes": 30,
            "distributed": True, "public_path": "public/missing.py"}))
        self.assert_status("incomplete")

    def test_public_projection_keeps_original_and_public_identity_separate(self):
        public = b"Anonymous path replaces original identity.\n"
        self.fixture.write("public/projection.txt", public)
        self.fixture.edit(self.data, "artifacts", lambda manifest: manifest["files"].append({
            "path": "outputs/original.txt", "sha256": "e" * 64, "bytes": 999,
            "distributed": True, "public_path": "public/projection.txt",
            "public_sha256": sha(public), "public_bytes": len(public)}))
        self.assert_status("complete")
        self.fixture.edit(self.data, "artifacts", lambda manifest: manifest["files"][-1].update(
            public_bytes=len(public) + 1))
        self.assert_status("invalid")

    def test_paths_reject_escape_absolute_and_noncanonical_aliases(self):
        name = "trials/" + self.theory + ".json"
        original = self.fixture.load(name)
        for bad in ("../outside", "/tmp/outside", "records/../outside", "./records/x",
                    "records//x", "records\\x", "C:/outside", "records/./x"):
            with self.subTest(path=bad):
                modified = copy.deepcopy(original)
                modified["report"]["path"] = bad
                self.fixture.dump(name, modified)
                self.assert_status("invalid")
        self.fixture.dump(name, original)

    def test_symlink_file_and_symlink_parent_are_rejected(self):
        trial = self.fixture.load("trials/" + self.theory + ".json")
        report = self.root / trial["report"]["path"]
        original = report.read_bytes()
        target = self.root / "other.md"
        target.write_bytes(original)
        report.unlink()
        report.symlink_to(target)
        self.assert_status("invalid")
        report.unlink()
        report.write_bytes(original)
        linked = self.root / "linked"
        linked.symlink_to(report.parent, target_is_directory=True)
        self.edit_trial(self.theory, lambda entry: entry["report"].update(path="linked/report.md"))
        self.assert_status("invalid")

    def test_regular_hardlink_is_not_misclassified_as_symlink(self):
        trial = self.fixture.load("trials/" + self.theory + ".json")
        os.link(self.root / trial["report"]["path"], self.root / "same-bytes.md")
        self.assert_status("complete")

    def test_raw_workspace_path_escape_is_rejected_without_opening_workspace(self):
        self.fixture.edit(self.data, "artifacts", lambda manifest: manifest["files"][0].update(
            path="../private.csv"))
        self.assert_status("invalid")

    def test_duplicate_artifact_and_read_identifiers_are_rejected(self):
        self.fixture.edit(self.data, "artifacts", lambda manifest: manifest["files"].append(
            copy.deepcopy(manifest["files"][0])))
        self.assert_status("invalid")
        self.fixture.edit(self.theory, "execution", lambda entry: entry["reads"].append(
            copy.deepcopy(entry["reads"][0])))
        self.assert_status("invalid")

    def test_mutable_workspace_reads_keep_distinct_historical_versions(self):
        self.fixture.edit(self.data, "execution", lambda entry: entry["reads"].extend([
            {"logical_name": "workspace/report.md", "sha256": "b" * 64, "version": "stage-a"},
            {"logical_name": "workspace/report.md", "sha256": "c" * 64, "version": "stage-b"},
        ]))
        result = self.assert_status("complete")
        observation = next(x for x in result["observations"] if x["trial_id"] == self.data)
        self.assertEqual(observation["mutable_workspace_paths_with_multiple_versions"],
                         ["workspace/report.md"])

    def test_frozen_read_name_cannot_claim_two_different_identities(self):
        self.fixture.edit(self.data, "execution", lambda entry: entry["reads"].append(
            {"logical_name": "task", "sha256": "c" * 64}))
        self.assert_status("invalid")

    def test_duplicate_json_keys_and_nonfinite_numbers_are_rejected(self):
        for raw in (b'{"expected_trials":[],"expected_trials":[]}',
                    b'{"unexpected":NaN}', b'{"unexpected":Infinity}', b'{"unexpected":1e999}'):
            with self.subTest(raw=raw):
                self.fixture.write("study.json", raw)
                self.assert_status("invalid")

    def test_unexpected_and_duplicate_trial_records_are_rejected(self):
        original = (self.root / ("trials/" + self.theory + ".json")).read_bytes()
        self.fixture.write("trials/unplanned.json", original)
        self.assert_status("invalid")
        (self.root / "trials/unplanned.json").unlink()
        study = self.fixture.load("study.json")
        study["expected_trials"][1] = copy.deepcopy(study["expected_trials"][0])
        self.fixture.dump("study.json", study)
        self.assert_status("invalid")

    def test_predecessor_cannot_cross_arms(self):
        study = self.fixture.load("study.json")
        for trial in study["expected_trials"]:
            if trial["trial_id"] == "data-b-baseline":
                trial["predecessor"] = "data-a-external"
        self.fixture.dump("study.json", study)
        self.assert_status("invalid")

    def test_reused_report_reference_and_submission_id_are_rejected(self):
        first = self.fixture.load("trials/" + self.theory + ".json")
        self.edit_trial("theory-baseline-2", lambda trial: trial.update(report=first["report"]))
        self.assert_status("invalid")

    def test_duplicate_anonymous_submission_id_is_rejected(self):
        first = self.fixture.load("trials/" + self.theory + ".json")
        submission = self.fixture.load(first["adjudication"]["path"])["submission_id"]
        self.fixture.edit("theory-baseline-2", "adjudication", lambda entry: entry.update(
            submission_id=submission))
        self.assert_status("invalid")

    def test_wrong_common_configuration_and_boolean_numbers_are_rejected(self):
        self.fixture.edit(self.theory, "execution", lambda entry: entry["requested"].update(
            fork_turns="all"))
        self.assert_status("invalid")
        self.fixture.edit(self.theory, "execution", lambda entry: entry.update(
            requested=copy.deepcopy(VALIDATOR.REQUESTED), tool_calls=True))
        self.assert_status("invalid")

    def test_soft_budget_excess_and_truthful_violations_are_observed_not_silently_deleted(self):
        self.fixture.edit(self.theory, "execution", lambda entry: entry.update(
            tool_calls=19, violations=["Exceeded requested tool budget"]))
        result = self.assert_status("complete")
        observation = next(item for item in result["observations"] if item["trial_id"] == self.theory)
        self.assertTrue(observation["requested_tool_budget_exceeded"])
        self.assertEqual(len(observation["violations"]), 1)

    def test_theory_cap_arithmetic_and_usable_gate(self):
        self.fixture.edit(self.theory, "adjudication", lambda entry: entry.update(
            critical_errors=["Source theorem does not apply to the central claim."],
            caps_applied=[{"max_total": 49, "reason": "Report paragraph 2 certifies an unsupported claim."}],
            effective_score=49, usability="unusable"))
        self.assert_status("complete")
        self.fixture.edit(self.theory, "adjudication", lambda entry: entry.update(effective_score=50))
        self.assert_status("invalid")
        self.fixture.edit(self.theory, "adjudication", lambda entry: entry.update(
            effective_score=49, usability="usable"))
        self.assert_status("invalid")

    def test_literal_usable_review_labels_are_preserved(self):
        for label in VALIDATOR.USABLE_LABELS:
            self.fixture.edit(self.theory, "adjudication", lambda entry: entry.update(usability=label))
            self.assert_status("complete")

    def test_usable_label_aliases_cannot_hide_critical_errors(self):
        for label in VALIDATOR.USABLE_LABELS:
            self.fixture.edit(self.theory, "adjudication", lambda entry: entry.update(
                usability=label, critical_errors=["Unsupported central certification"]))
            self.assert_status("invalid")

    def test_data_cannot_apply_extra_cap(self):
        self.fixture.edit(self.data, "adjudication", lambda entry: entry.update(
            critical_errors=["Wrong independent unit"], usability="unusable",
            caps_applied=[{"max_total": 49, "reason": "An extra penalty"}], effective_score=49))
        self.assert_status("invalid")

    def test_criterion_arithmetic_coverage_and_rubric_identity_are_checked(self):
        self.fixture.edit(self.theory, "adjudication", lambda entry: entry.update(raw_score=99))
        self.assert_status("invalid")
        self.fixture.edit(self.theory, "adjudication", lambda entry: entry.update(raw_score=100))
        self.fixture.edit(self.theory, "adjudication", lambda entry: entry["criteria"].pop())
        self.assert_status("invalid")

    def test_malformed_adjudication_container_and_unbounded_score_do_not_crash(self):
        name = "trials/" + self.theory + ".json"
        trial = self.fixture.load(name)
        original = copy.deepcopy(trial)
        trial["adjudication"] = self.fixture.ref("records/malformed.json", [])
        self.fixture.dump(name, trial)
        self.assert_status("invalid")
        self.fixture.dump(name, original)
        self.fixture.edit(self.theory, "adjudication", lambda entry: entry.update(raw_score=10 ** 500))
        self.assert_status("invalid")


if __name__ == "__main__":
    unittest.main()
