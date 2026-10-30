"""Small synthetic lifecycle evidence fixtures; no research work is scored here."""
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
SPEC = importlib.util.spec_from_file_location("core_comparison_validate",
                                            ROOT / "evals/core-comparison/validate.py")
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


class Fixture:
    def __init__(self, root):
        self.root = root
        self.planned = [
            {"chain_id": name, "case_id": case, "arm": arm}
            for name, case, arm in [("P1", "T", "core"), ("P2", "D", "baseline"),
                                    ("P3", "T", "guidance"), ("P4", "D", "core"),
                                    ("P5", "T", "baseline"), ("P6", "D", "guidance")]]
        self.write("task.md", b"Four dependent stages; identical substantive obligations.\n")
        self.dump("rubric.json", {"total": 100, "stages": {
            stage: {"points": points, "items": [{"id": stage + "-substance", "points": points}]}
            for stage, points in VALIDATOR.STAGE_POINTS.items()}})
        self.dump("freeze.json", {"files": {name: sha((root / name).read_bytes())
                                             for name in ("task.md", "rubric.json")}})
        self.freeze_sha = sha((root / "freeze.json").read_bytes())
        self.dump("study.json", {"freeze_sha256": self.freeze_sha, "expected_chains": self.planned})
        for expected in self.planned:
            identifier, phases, report_shas = expected["chain_id"], {}, {}
            for phase in VALIDATOR.STAGES:
                prefix = "records/" + identifier + "/" + phase
                report = self.ref(prefix + "/report.md", b"Specific project evidence.\n")
                report_shas[phase] = report["sha256"]
                execution = self.ref(prefix + "/execution.json", {
                    "status": "executed", "effective": {key: None for key in VALIDATOR.EFFECTIVE_FIELDS},
                    "tool_calls": 3, "network_calls": 0, "violations": [],
                    "scope": "instruction-only; no OS audit"})
                manifest = self.ref(prefix + "/manifest.json", {"scope": "Sealed project files.", "files": [
                    {"path": "inputs/not-distributed.csv", "sha256": "b" * 64,
                     "bytes": 10, "distributed": False}]})
                audit = self.ref(prefix + "/readonly.json", {"passed": True, "file_differences": [],
                    "directory_mtime_differences": [], "scope": "File bytes and mtime/dir mtime only."}
                    ) if phase in {"B", "D"} else None
                phases[phase] = {"status": "executed", "report": report, "execution": execution,
                                 "project_manifest": manifest, "readonly_audit": audit}
            grade = self.ref("records/" + identifier + "/grade.json", {
                "chain_id": identifier, "submission_id": "anonymous-" + identifier,
                "scored": True, "arm_hidden": True, "report_sha256_by_stage": report_shas,
                "criteria": [{"id": phase + "-substance", "score": points, "max_points": points,
                    "evidence": "Report and project records", "rationale": "Required evidence is present."}
                    for phase, points in VALIDATOR.STAGE_POINTS.items()],
                "raw_score": 100, "effective_score": 100, "max_score": 100,
                "critical_errors": [], "usability": "usable in stated scope", "notes": []})
            self.dump("chains/" + identifier + ".json", {**expected, "freeze_sha256": self.freeze_sha,
                       "stages": phases, "adjudication": grade, "probes": None})

    def write(self, name, raw):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)

    def dump(self, name, value):
        self.write(name, json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False).encode())

    def load(self, name):
        return json.loads((self.root / name).read_text())

    def ref(self, name, value):
        self.write(name, value) if isinstance(value, bytes) else self.dump(name, value)
        return {"path": name, "sha256": sha((self.root / name).read_bytes())}

    def chain(self, identifier="P1"):
        return self.load("chains/" + identifier + ".json")

    def edit_chain(self, transform, identifier="P1"):
        chain = self.chain(identifier)
        transform(chain)
        self.dump("chains/" + identifier + ".json", chain)

    def edit_ref(self, field, transform, phase=None, identifier="P1"):
        chain = self.chain(identifier)
        owner = chain["stages"][phase] if phase else chain
        name = owner[field]["path"]
        value = self.load(name)
        transform(value)
        owner[field] = self.ref(name, value)
        self.dump("chains/" + identifier + ".json", chain)


class CoreComparisonRecords(unittest.TestCase):
    def test_published_lifecycle_records_close_with_all_planned_stages_retained(self):
        result = VALIDATOR.validate(ROOT / "evals/core-comparison")
        self.assertEqual(result["status"], "complete", result)
        self.assertEqual(result["counts"]["recorded"], 6)
        self.assertEqual(result["counts"]["stages_recorded"], 24)
        self.assertEqual(result["counts"]["scored"], 6)
        self.assertEqual(result["effective_model_equality"], "not-inferred")
        self.assertIn("scientific validity not assessed", result["scope"])

    def audit_projection(self):
        name = "audits/key-audit.json"
        original, public = b'{"fixture":"machine local path"}', b'{"fixture":"logical path"}'
        self.fixture.write(name, public)
        freeze = self.fixture.load("freeze.json")
        freeze["files"][name] = sha(original)
        self.fixture.dump("freeze.json", freeze)
        study = self.fixture.load("study.json")
        study["freeze_sha256"] = sha((self.root / "freeze.json").read_bytes())
        study["publication_projections"] = {name: {"original_sha256": sha(original),
            "public_sha256": sha(public), "changes": ["machine-path-redaction"]}}
        self.fixture.dump("study.json", study)
        for planned in self.fixture.planned:
            self.fixture.edit_chain(lambda value: value.update(
                freeze_sha256=study["freeze_sha256"]), planned["chain_id"])
        return study

    def test_only_administrative_audit_projection_keeps_original_freeze_identity(self):
        self.audit_projection()
        self.check("complete")

    def test_scientific_task_projection_cannot_bypass_freeze(self):
        study = self.audit_projection()
        study["publication_projections"]["task.md"] = dict(
            next(iter(study["publication_projections"].values())))
        self.fixture.dump("study.json", study)
        self.check("invalid")

    def test_audit_projection_must_bind_original_hash_and_path_only_changes(self):
        study = self.audit_projection()
        study["publication_projections"]["audits/key-audit.json"]["original_sha256"] = "0" * 64
        self.fixture.dump("study.json", study)
        self.check("invalid")

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="rwt-lifecycle-records-")
        self.root = Path(self.temporary.name)
        self.fixture = Fixture(self.root)

    def tearDown(self):
        self.temporary.cleanup()

    def check(self, expected):
        result = VALIDATOR.validate(self.root)
        self.assertEqual(result["status"], expected, result)
        return result

    def test_complete_is_readonly_and_retains_unknown_model_and_dependency_scope(self):
        before = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in self.root.rglob("*") if p.is_file()}
        result = self.check("complete")
        self.assertEqual(result["counts"], {"expected_chains": 6, "expected_stages": 24,
            "recorded": 6, "stages_recorded": 24, "scored": 6, "executed": 24,
            "failed": 0, "not-run": 0, "readonly_failures": 0})
        self.assertEqual(result["effective_model_equality"], "not-inferred")
        self.assertIn("scientific validity not assessed", result["scope"])
        self.assertIn("dependent stages", result["independent_replicates"])
        self.assertEqual(before, {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in before})

    def test_missing_chain_keeps_expected_denominator_and_allow_flag_only_handles_missing(self):
        (self.root / "chains/P1.json").unlink()
        result = self.check("incomplete")
        self.assertEqual(result["counts"]["expected_stages"], 24)
        self.assertEqual(result["counts"]["recorded"], 5)
        for allow, code in [(False, 1), (True, 0)]:
            with redirect_stdout(io.StringIO()):
                self.assertEqual(VALIDATOR.main(["--root", str(self.root)] +
                    (["--allow-incomplete"] if allow else [])), code)

    def test_missing_study_retains_known_denominator_and_does_not_hide_bad_freeze(self):
        (self.root / "study.json").unlink()
        result = self.check("incomplete")
        self.assertEqual(result["counts"]["expected_chains"], 6)
        self.fixture.write("freeze.json", b'{"files":[],"files":{}}')
        self.check("invalid")

    def test_missing_freeze_does_not_hide_malformed_present_study(self):
        (self.root / "freeze.json").unlink()
        self.fixture.dump("study.json", [])
        self.check("invalid")

    def test_missing_rubric_does_not_hide_malformed_adjudication(self):
        (self.root / "rubric.json").unlink()
        self.fixture.edit_ref("adjudication", lambda value: value.update(criteria=False))
        self.check("invalid")

    def test_scientific_and_readonly_failures_do_not_invalidate_record_closure(self):
        self.fixture.edit_ref("readonly_audit", lambda value: value.update(passed=False,
            file_differences=[{"path": "notes/written.txt", "change": "added"}]), phase="B")
        self.fixture.edit_ref("adjudication", lambda value: value.update(
            critical_errors=["Unauthorized write during recovery"], usability="unusable"))
        result = self.check("complete")
        self.assertEqual(result["counts"]["readonly_failures"], 1)
        self.assertTrue(any(x.get("readonly_passed") is False for x in result["observations"]))

    def test_failed_execution_can_retain_scored_product(self):
        self.fixture.edit_ref("execution", lambda value: value.update(status="failed"), phase="A")
        self.fixture.edit_chain(lambda value: value["stages"]["A"].update(status="failed"))
        result = self.check("complete")
        self.assertEqual(result["counts"]["failed"], 1)
        self.assertEqual(result["counts"]["scored"], 6)

    def terminal_failure(self):
        self.fixture.edit_ref("execution", lambda value: value.update(status="failed"), phase="A")
        self.fixture.edit_chain(lambda value: value["stages"]["A"].update(
            status="failed", report=None, project_manifest=None))
        self.fixture.edit_ref("adjudication", lambda value: value.update(scored=False,
            raw_score=None, effective_score=None, criteria=[], usability="not-assessable"))

    def test_unassessable_failure_keeps_null_scores_instead_of_zero(self):
        self.terminal_failure()
        result = self.check("complete")
        self.assertEqual(result["counts"]["scored"], 5)
        self.assertEqual(result["counts"]["failed"], 1)
        grade = self.fixture.load(self.fixture.chain()["adjudication"]["path"])
        self.assertIsNone(grade["raw_score"])

    def test_unscored_ordinary_chain_and_zero_imputed_failure_are_invalid(self):
        self.fixture.edit_ref("adjudication", lambda value: value.update(
            scored=False, raw_score=None, effective_score=None, criteria=[]))
        self.check("invalid")
        self.terminal_failure()
        self.fixture.edit_ref("adjudication", lambda value: value.update(raw_score=0))
        self.check("invalid")

    def test_failed_stage_without_execution_evidence_is_incomplete(self):
        self.terminal_failure()
        self.fixture.edit_chain(lambda value: value["stages"]["A"].update(execution=None))
        self.check("incomplete")

    def test_not_run_or_missing_stage_is_incomplete_even_with_old_grade(self):
        self.fixture.edit_ref("execution", lambda value: value.update(status="not-run"), phase="D")
        self.fixture.edit_chain(lambda value: value["stages"]["D"].update(status="not-run"))
        self.check("incomplete")
        self.fixture.edit_chain(lambda value: value["stages"].pop("D"))
        self.fixture.edit_chain(lambda value: value.update(adjudication=None))
        self.check("incomplete")

    def test_executed_stage_needs_report_manifest_and_readonly_evidence(self):
        for field in ("report", "project_manifest", "readonly_audit"):
            with self.subTest(field=field):
                original = self.fixture.chain()
                self.fixture.edit_chain(lambda value: value["stages"]["B"].update({field: None}))
                self.fixture.edit_chain(lambda value: value.update(adjudication=None))
                self.check("incomplete")
                self.fixture.dump("chains/P1.json", original)

    def test_hash_mismatch_remains_invalid_under_allow_incomplete(self):
        report = self.fixture.chain()["stages"]["A"]["report"]["path"]
        self.fixture.write(report, b"changed report")
        self.check("invalid")
        with redirect_stdout(io.StringIO()):
            self.assertEqual(VALIDATOR.main(["--root", str(self.root), "--allow-incomplete"]), 2)

    def test_changed_frozen_task_and_score_rubric_are_invalid(self):
        self.fixture.write("task.md", b"Changed task")
        self.check("invalid")
        self.fixture.write("task.md", b"Four dependent stages; identical substantive obligations.\n")
        rubric = self.fixture.load("rubric.json")
        rubric["stages"]["A"]["items"][0]["points"] = 21
        self.fixture.dump("rubric.json", rubric)
        self.check("invalid")

    def test_study_and_chain_bind_freeze_and_rubric_must_be_frozen(self):
        self.fixture.edit_chain(lambda value: value.update(freeze_sha256="f" * 64))
        self.check("invalid")
        study = self.fixture.load("study.json")
        study["freeze_sha256"] = "a" * 64
        self.fixture.dump("study.json", study)
        self.check("invalid")
        freeze = self.fixture.load("freeze.json")
        freeze["files"].pop("rubric.json")
        self.fixture.dump("freeze.json", freeze)
        study["freeze_sha256"] = sha((self.root / "freeze.json").read_bytes())
        self.fixture.dump("study.json", study)
        self.check("invalid")

    def test_planned_case_arm_balance_and_chain_identity_cannot_be_changed(self):
        self.fixture.edit_chain(lambda value: value.update(arm="baseline"))
        self.check("invalid")
        self.fixture.edit_chain(lambda value: value.update(arm="core"))
        study = self.fixture.load("study.json")
        study["expected_chains"][0]["arm"] = "guidance"
        self.fixture.dump("study.json", study)
        self.check("invalid")

    def test_unknown_stage_or_missing_required_null_declaration_is_invalid(self):
        self.fixture.edit_chain(lambda value: value["stages"].update(E={}))
        self.check("invalid")
        self.fixture.edit_chain(lambda value: value["stages"].pop("E"))
        self.fixture.edit_chain(lambda value: value.pop("probes"))
        self.check("invalid")

    def test_adjudication_binds_all_four_actual_report_hashes(self):
        self.fixture.edit_ref("adjudication", lambda value: value["report_sha256_by_stage"].update(A="0" * 64))
        self.check("invalid")
        report_sha = self.fixture.chain()["stages"]["A"]["report"]["sha256"]
        self.fixture.edit_ref("adjudication", lambda value: value["report_sha256_by_stage"].update(A=report_sha))
        self.fixture.edit_ref("adjudication", lambda value: value["report_sha256_by_stage"].pop("D"))
        self.check("invalid")

    def test_score_coverage_arithmetic_no_extra_cap_and_anonymous_identity(self):
        for mutation in [lambda value: value.update(raw_score=99),
                         lambda value: value["criteria"].pop(),
                         lambda value: value.update(caps_applied=[{"max_total": 49}]),
                         lambda value: value.update(arm_hidden=False),
                         lambda value: value.update(chain_id="P2")]:
            with self.subTest(mutation=mutation):
                chain = self.fixture.chain()
                original = self.fixture.load(chain["adjudication"]["path"])
                self.fixture.edit_ref("adjudication", mutation)
                self.check("invalid")
                self.fixture.edit_ref("adjudication", lambda value: (value.clear(), value.update(original)))

    def test_duplicate_submission_or_shared_record_reference_is_rejected(self):
        self.fixture.edit_ref("adjudication", lambda value: value.update(submission_id="anonymous-P1"),
                              identifier="P2")
        self.check("invalid")
        self.fixture.edit_ref("adjudication", lambda value: value.update(submission_id="anonymous-P2"),
                              identifier="P2")
        ref = self.fixture.chain()["stages"]["A"]["report"]
        self.fixture.edit_chain(lambda value: value["stages"]["B"].update(report=ref))
        self.check("invalid")

    def test_duplicate_json_keys_and_nonfinite_numbers_are_rejected(self):
        for raw in [b'{"expected_chains":[],"expected_chains":[]}', b'{"x":NaN}',
                    b'{"x":Infinity}', b'{"x":1e999}']:
            with self.subTest(raw=raw):
                self.fixture.write("study.json", raw)
                self.check("invalid")

    def test_malformed_values_and_unbounded_scores_are_errors_not_crashes(self):
        self.fixture.edit_ref("adjudication", lambda value: value.update(raw_score=10 ** 500))
        self.check("invalid")
        self.fixture.edit_chain(lambda value: value.update(stages=[]))
        self.check("invalid")

    def test_boolean_counters_nonfinite_values_and_missing_effective_unknowns_rejected(self):
        self.fixture.edit_ref("execution", lambda value: value.update(tool_calls=True), phase="A")
        self.check("invalid")
        self.fixture.edit_ref("execution", lambda value: value.update(tool_calls=3), phase="A")
        self.fixture.edit_ref("execution", lambda value: value["effective"].pop("seed"), phase="A")
        self.check("invalid")

    def test_truthful_violations_and_known_model_do_not_imply_model_equality(self):
        self.fixture.edit_ref("execution", lambda value: value.update(
            violations=["Attempted a disallowed path; no content read"]), phase="A")
        self.fixture.edit_ref("execution", lambda value: value["effective"].update(model="declared-model"), phase="A")
        result = self.check("complete")
        self.assertEqual(result["effective_model_equality"], "not-inferred")
        self.assertTrue(any(x.get("violations") for x in result["observations"]))

    def test_execution_status_and_isolation_scope_must_match_record(self):
        self.fixture.edit_ref("execution", lambda value: value.update(status="failed"), phase="A")
        self.check("invalid")
        self.fixture.edit_ref("execution", lambda value: value.update(status="executed",
            scope="OS-audited"), phase="A")
        self.check("invalid")

    def test_network_call_must_be_zero_or_unknown_not_an_unreported_success(self):
        self.fixture.edit_ref("execution", lambda value: value.update(network_calls=1), phase="A")
        self.check("invalid")

    def test_readonly_pass_cannot_contradict_differences_and_write_stage_cannot_claim_audit(self):
        self.fixture.edit_ref("readonly_audit", lambda value: value.update(
            directory_mtime_differences=["notes"]), phase="B")
        self.check("invalid")
        self.fixture.edit_ref("readonly_audit", lambda value: value.update(passed=False), phase="B")
        audit = self.fixture.chain()["stages"]["B"]["readonly_audit"]
        self.fixture.edit_chain(lambda value: value["stages"]["A"].update(readonly_audit=audit))
        self.check("invalid")

    def test_public_artifacts_bind_public_projection_and_undistributed_files_are_not_opened(self):
        public = b"Logical machine locator\n"
        self.fixture.write("public/project-note.md", public)
        self.fixture.edit_ref("project_manifest", lambda value: value["files"].append({
            "path": "note.md", "sha256": "d" * 64, "bytes": 900, "distributed": True,
            "public_path": "public/project-note.md", "public_sha256": sha(public), "public_bytes": len(public)}),
            phase="A")
        self.check("complete")
        self.fixture.write("public/project-note.md", b"tampered")
        self.check("invalid")

    def test_missing_public_artifact_is_incomplete_not_scientific_failure(self):
        self.fixture.edit_ref("project_manifest", lambda value: value["files"].append({
            "path": "note.md", "sha256": "d" * 64, "bytes": 10, "distributed": True,
            "public_path": "public/missing.md"}), phase="A")
        self.check("incomplete")

    def test_duplicate_manifest_path_and_unsafe_raw_workspace_name_are_rejected(self):
        self.fixture.edit_ref("project_manifest", lambda value: value["files"].append(
            copy.deepcopy(value["files"][0])), phase="A")
        self.check("invalid")
        self.fixture.edit_ref("project_manifest", lambda value: value["files"].pop(), phase="A")
        self.fixture.edit_ref("project_manifest", lambda value: value["files"][0].update(path="../secret"), phase="A")
        self.check("invalid")

    def test_unsafe_reference_paths_are_rejected_before_read(self):
        for path in ["../outside", "/tmp/outside", "a/../b", "a//b", "a\\b", "C:secret", "./report"]:
            with self.subTest(path=path):
                original = self.fixture.chain()
                self.fixture.edit_chain(lambda value: value["stages"]["A"]["report"].update(path=path))
                self.check("invalid")
                self.fixture.dump("chains/P1.json", original)

    def test_symlink_file_and_parent_are_rejected_but_regular_hardlink_is_allowed(self):
        chain = self.fixture.chain()
        name = chain["stages"]["A"]["report"]["path"]
        report = self.root / name
        raw = report.read_bytes()
        target = self.root / "same-report.md"
        target.write_bytes(raw)
        report.unlink()
        report.symlink_to(target)
        self.check("invalid")
        report.unlink()
        os.link(target, report)
        self.check("complete")
        parent = self.root / "linked"
        parent.symlink_to(report.parent, target_is_directory=True)
        self.fixture.edit_chain(lambda value: value["stages"]["A"]["report"].update(path="linked/report.md"))
        self.check("invalid")

    def test_independent_probe_failure_record_never_changes_project_scientific_score(self):
        ref = self.fixture.ref("records/P1/probes.json", {
            "feature": "automatic version guard", "passed": False, "scope": "Separate mechanism probe"})
        self.fixture.edit_chain(lambda value: value.update(probes=ref))
        result = self.check("complete")
        self.assertEqual(result["counts"]["scored"], 6)


if __name__ == "__main__":
    unittest.main()
