#!/usr/bin/env python3
"""Validate frozen comparison records, never their scientific correctness.

All public paths are relative to this evaluation directory. Artifact ``path``
values are workspace-relative names only; they are never opened. Unknown model
settings remain unknown. A complete record set may contain failed executions.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
import stat
from typing import Any


SHA256 = re.compile(r"[0-9a-f]{64}\Z")
IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*\Z")
TASKS = {"theory", "data-a", "data-b"}
# Retain the reviewers' literal labels rather than rewriting their records.
USABLE_LABELS = {"usable", "ready-to-use", "usable without substantive mathematical revision"}
REQUESTED = {
    "model_override": None,
    "reasoning_effort_override": None,
    "fork_turns": "none",
    "max_tool_calls": 18,
    "max_report_characters": 12000,
}
EFFECTIVE_FIELDS = {
    "model", "reasoning_effort", "temperature", "seed", "output_token_limit"
}


class RecordError(ValueError):
    pass


def strict_json(raw: str) -> Any:
    """Reject duplicate object keys and all non-finite JSON numbers."""
    def pairs(entries):
        result = {}
        for key, value in entries:
            if key in result:
                raise RecordError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    def constant(value):
        raise RecordError(f"non-finite JSON number: {value}")

    value = json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)

    def finite(item):
        if isinstance(item, float) and not math.isfinite(item):
            raise RecordError("non-finite JSON number")
        if isinstance(item, dict):
            for child in item.values():
                finite(child)
        elif isinstance(item, list):
            for child in item:
                finite(child)

    finite(value)
    return value


def relative_name(value: Any) -> str:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        raise RecordError("path must be a nonempty canonical POSIX relative path")
    path = PurePosixPath(value)
    if (path.is_absolute() or any(part in {"", ".", ".."} for part in value.split("/"))
            or ":" in value or path.as_posix() != value):
        raise RecordError(f"unsafe or noncanonical relative path: {value!r}")
    return value


def digest(value: Any) -> str:
    if not isinstance(value, str) or SHA256.fullmatch(value) is None:
        raise RecordError("sha256 must be 64 lowercase hexadecimal characters")
    return value


def number(value: Any, *, minimum: float = 0) -> float:
    try:
        valid = (not isinstance(value, bool) and isinstance(value, (int, float))
                 and math.isfinite(value) and value >= minimum)
    except OverflowError:
        valid = False
    if not valid:
        raise RecordError(f"expected finite number >= {minimum}")
    return value


def integer(value: Any, *, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        raise RecordError(f"expected integer >= {minimum}")
    return value


def text_field(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RecordError(f"{name} must be a nonempty string")
    return value


def object_field(value: Any, name: str) -> dict:
    if not isinstance(value, dict):
        raise RecordError(f"{name} must be an object")
    return value


def list_field(value: Any, name: str) -> list:
    if not isinstance(value, list):
        raise RecordError(f"{name} must be an array")
    return value


def equal_score(actual: Any, expected: float, name: str) -> None:
    if not math.isclose(number(actual), expected, rel_tol=0, abs_tol=1e-9):
        raise RecordError(f"{name} arithmetic mismatch: expected {expected}")


class Validator:
    def __init__(self, root: Path):
        self.root = Path(root).absolute()
        self.errors: list[str] = []
        self.missing: list[str] = []
        self.observations: list[dict] = []
        self.reference_owners: dict[str, str] = {}
        self.submissions: set[str] = set()
        self.counts = {
            "expected": 0, "recorded": 0, "scored": 0,
            "executed": 0, "failed": 0, "not-run": 0, "terminal_failures": 0,
        }

    def path(self, name: Any) -> Path:
        name = relative_name(name)
        current = self.root
        if self.root.is_symlink():
            raise RecordError("evaluation root must not be a symlink")
        for part in PurePosixPath(name).parts:
            current = current / part
            if current.is_symlink():
                raise RecordError(f"symlink rejected: {name}")
        # Canonical names and an explicit symlink walk keep the target in root.
        if current.exists() and not stat.S_ISREG(current.stat().st_mode):
            raise RecordError(f"expected regular file: {name}")
        return current

    def read(self, name: str, *, expected_sha: str | None = None,
             expected_bytes: int | None = None, as_json: bool = True):
        path = self.path(name)
        if expected_sha is not None:
            digest(expected_sha)
        if expected_bytes is not None:
            integer(expected_bytes)
        if not path.exists():
            self.missing.append(f"missing file: {name}")
            return None
        raw = path.read_bytes()
        if expected_sha is not None and hashlib.sha256(raw).hexdigest() != expected_sha:
            raise RecordError(f"hash mismatch: {name}")
        if expected_bytes is not None and len(raw) != expected_bytes:
            raise RecordError(f"byte length mismatch: {name}")
        if not as_json:
            return raw
        try:
            return strict_json(raw.decode("utf-8"))
        except (UnicodeError, ValueError, RecursionError) as exc:
            raise RecordError(f"invalid JSON in {name}: {exc}") from exc

    def reference(self, ref: Any, owner: str, *, as_json=True):
        ref = object_field(ref, owner)
        name = relative_name(ref.get("path"))
        expected_sha = digest(ref.get("sha256"))
        previous = self.reference_owners.get(name)
        if previous is not None and previous != owner:
            raise RecordError(f"duplicate record reference {name}: {previous}, {owner}")
        self.reference_owners[name] = owner
        return self.read(name, expected_sha=expected_sha, as_json=as_json)

    def expected(self, study: dict) -> dict[str, dict]:
        entries = list_field(study.get("expected_trials"), "study.expected_trials")
        if len(entries) != 12:
            raise RecordError("study must declare exactly 12 expected trials")
        result, combinations = {}, set()
        for entry in entries:
            item = object_field(entry, "expected trial")
            trial_id = text_field(item.get("trial_id"), "trial_id")
            if IDENTIFIER.fullmatch(trial_id) is None or trial_id in result:
                raise RecordError(f"invalid or duplicate expected trial_id: {trial_id}")
            task = item.get("task_id")
            if task not in TASKS:
                raise RecordError(f"unknown task_id: {task}")
            arm = text_field(item.get("arm"), "arm")
            replicate = integer(item.get("replicate"), minimum=1)
            if "predecessor" not in item:
                raise RecordError("expected trial must declare predecessor, including null")
            predecessor = item["predecessor"]
            if predecessor is not None:
                text_field(predecessor, "predecessor")
            combination = task, arm, replicate
            if combination in combinations:
                raise RecordError(f"duplicate task/arm/replicate: {combination}")
            combinations.add(combination)
            result[trial_id] = item
        arms = {item["arm"] for item in result.values()}
        if len(arms) != 3:
            raise RecordError("study must declare three arms")
        theory_replicates = None
        for arm in arms:
            grouped = {task: [item for item in result.values()
                              if item["arm"] == arm and item["task_id"] == task]
                       for task in TASKS}
            if {task: len(items) for task, items in grouped.items()} != {
                    "theory": 2, "data-a": 1, "data-b": 1}:
                raise RecordError("each arm needs two theory repeats and one data chain")
            repetitions = {item["replicate"] for item in grouped["theory"]}
            if theory_replicates is None:
                theory_replicates = repetitions
            elif repetitions != theory_replicates:
                raise RecordError("theory replicate labels must agree across arms")
        for item in result.values():
            predecessor = item["predecessor"]
            if item["task_id"] != "data-b":
                if predecessor is not None:
                    raise RecordError("only data-b can have a predecessor")
                continue
            prior = result.get(predecessor)
            if (prior is None or prior["task_id"] != "data-a"
                    or prior["arm"] != item["arm"]
                    or prior["replicate"] != item["replicate"]):
                raise RecordError("data-b predecessor must be its own arm/replicate data-a")
        self.counts["expected"] = len(result)
        return result

    def execution(self, entry: dict, trial_id: str) -> str:
        entry = object_field(entry, "execution")
        status = entry.get("status")
        if status not in {"executed", "failed", "not-run"}:
            raise RecordError("unknown execution status")
        for field in ("tool_calls", "network_calls", "duration_seconds"):
            if field not in entry:
                raise RecordError(f"execution must retain {field}, including null")
        terminal = entry.get("terminal_failure", False)
        if type(terminal) is not bool or (terminal and status != "failed"):
            raise RecordError("terminal_failure=true requires execution.status=failed")
        self.counts[status] += 1
        if terminal:
            self.counts["terminal_failures"] += 1
        requested = object_field(entry.get("requested"), "execution.requested")
        if requested != REQUESTED:
            raise RecordError("requested configuration differs from frozen common request")
        effective = object_field(entry.get("effective"), "execution.effective")
        if not EFFECTIVE_FIELDS <= set(effective):
            raise RecordError("effective configuration must retain all unknown fields")
        for key in ("model", "reasoning_effort"):
            if effective[key] is not None:
                text_field(effective[key], f"effective.{key}")
        if effective["temperature"] is not None:
            number(effective["temperature"])
        if effective["seed"] is not None:
            integer(effective["seed"])
        if effective["output_token_limit"] is not None:
            integer(effective["output_token_limit"], minimum=1)
        calls = entry.get("tool_calls")
        if calls is not None:
            integer(calls)
        if entry.get("network_calls") is not None:
            if type(entry["network_calls"]) is not int or entry["network_calls"] != 0:
                raise RecordError("network_calls must be 0 or null")
        violations = list_field(entry.get("violations"), "execution.violations")
        reads = list_field(entry.get("reads"), "execution.reads")
        names, identities, versioned = set(), set(), set()
        for read in reads:
            read = object_field(read, "execution read")
            name = text_field(read.get("logical_name"), "read.logical_name")
            checksum = digest(read.get("sha256"))
            identity = name, checksum
            if identity in identities or (name in names and not name.startswith("workspace/")):
                raise RecordError(f"duplicate or conflicting read identity: {name}")
            if name in names:
                versioned.add(name)
            names.add(name)
            identities.add(identity)
        if entry.get("duration_seconds") is not None:
            number(entry["duration_seconds"])
        if entry.get("scope") != "instruction-only; no OS audit":
            raise RecordError("execution scope must retain instruction-only/no-OS-audit limit")
        self.observations.append({
            "trial_id": trial_id, "execution_status": status,
            "tool_calls": calls, "requested_tool_budget_exceeded": calls is not None and calls > 18,
            "unknown_effective_fields": sorted(key for key in EFFECTIVE_FIELDS
                                               if effective[key] is None),
            "violations": violations,
            "mutable_workspace_paths_with_multiple_versions": sorted(versioned),
        })
        if status == "not-run":
            self.missing.append(f"trial not run: {trial_id}")
        return status

    def artifacts(self, manifest: dict) -> None:
        manifest = object_field(manifest, "artifacts manifest")
        text_field(manifest.get("scope"), "artifacts.scope")
        files = list_field(manifest.get("files"), "artifacts.files")
        names, public_names = set(), set()
        for item in files:
            item = object_field(item, "artifact")
            name = relative_name(item.get("path"))
            if name in names:
                raise RecordError(f"duplicate workspace artifact path: {name}")
            names.add(name)
            raw_sha = digest(item.get("sha256"))
            raw_bytes = integer(item.get("bytes"))
            if type(item.get("distributed")) is not bool:
                raise RecordError("artifact distributed must be boolean")
            if not item["distributed"]:
                # Never interpret raw workspace names as public filesystem paths.
                if "public_path" in item or "public_sha256" in item:
                    raise RecordError("undistributed artifact must not declare public location")
                continue
            public = relative_name(item.get("public_path"))
            if public in public_names:
                raise RecordError(f"duplicate public artifact path: {public}")
            public_names.add(public)
            public_sha = digest(item.get("public_sha256", raw_sha))
            public_bytes = item.get("public_bytes", raw_bytes if public_sha == raw_sha else None)
            self.read(public, expected_sha=public_sha, expected_bytes=public_bytes, as_json=False)

    def rubric(self, task: str, theory: dict, data: dict) -> tuple[dict, set]:
        if task == "theory":
            source = theory
            expected_total = 100
        else:
            source = object_field(object_field(data.get("tasks"), "data.tasks").get(task), task)
            expected_total = 50
        items = list_field(source.get("items"), f"{task} rubric items")
        result = {}
        for item in items:
            item = object_field(item, "rubric item")
            name = text_field(item.get("id"), "rubric item id")
            if name in result:
                raise RecordError(f"duplicate rubric criterion: {name}")
            points = number(item.get("points"))
            if points == 0:
                raise RecordError("rubric points must be positive")
            result[name] = points
        equal_score(sum(result.values()), expected_total, "rubric total")
        caps = set()
        if task == "theory":
            declared = list_field(source.get("critical_caps"), "theory critical_caps")
            if not declared:
                raise RecordError("theory rubric must declare its critical caps")
            for item in declared:
                item = object_field(item, "critical cap")
                equal_score(item.get("max_total"), 49, "theory critical cap")
                text_field(item.get("trigger"), "critical cap trigger")
                caps.add(item["max_total"])
        if "total_points" in source:
            equal_score(source["total_points"], expected_total, "rubric total_points")
        if "max_score" in source:
            equal_score(source["max_score"], expected_total, "rubric max_score")
        return result, caps

    def adjudication(self, entry: dict, task: str, rubric: dict, allowed_caps: set,
                     *, terminal_failure: bool | None = False) -> None:
        entry = object_field(entry, "adjudication")
        submission = text_field(entry.get("submission_id"), "submission_id")
        if submission in self.submissions:
            raise RecordError(f"duplicate submission_id: {submission}")
        self.submissions.add(submission)
        if entry.get("task_id") != task or type(entry.get("scored")) is not bool:
            raise RecordError("adjudication task/scored mismatch")
        if entry.get("arm_hidden") is not True:
            raise RecordError("adjudication must declare arm_hidden=true")
        criteria = list_field(entry.get("criteria"), "adjudication.criteria")
        critical = list_field(entry.get("critical_errors"), "critical_errors")
        caps = list_field(entry.get("caps_applied"), "caps_applied")
        if "notes" not in entry:
            raise RecordError("adjudication must retain notes")
        if not entry["scored"]:
            if (terminal_failure is False or criteria or caps or entry.get("raw_score") is not None
                    or entry.get("effective_score") is not None
                    or entry.get("usability") != "not-assessable"):
                raise RecordError("unscored adjudication requires a terminal failure and null scores")
            if "raw_score" not in entry or "effective_score" not in entry:
                raise RecordError("terminal failure must explicitly retain null scores")
            if entry.get("max_score") is not None:
                equal_score(entry["max_score"], sum(rubric.values()), "max_score")
            return
        seen, raw = set(), 0
        for item in criteria:
            item = object_field(item, "criterion")
            identifier = item.get("id")
            if identifier not in rubric or identifier in seen:
                raise RecordError(f"unknown or duplicate adjudication criterion: {identifier}")
            seen.add(identifier)
            equal_score(item.get("max_points"), rubric[identifier], "criterion max_points")
            score = number(item.get("score"))
            if score > rubric[identifier]:
                raise RecordError("criterion score exceeds available points")
            evidence = item.get("evidence")
            if not isinstance(evidence, (str, list)) or not evidence:
                raise RecordError("criterion evidence must be a nonempty string or array")
            text_field(item.get("rationale"), "criterion rationale")
            raw += score
        if seen != set(rubric):
            raise RecordError("scored adjudication does not cover all rubric criteria")
        equal_score(entry.get("raw_score"), raw, "raw_score")
        equal_score(entry.get("max_score"), sum(rubric.values()), "max_score")
        cap_values = []
        for applied in caps:
            applied = object_field(applied, "applied cap")
            value = number(applied.get("max_total"))
            if value not in allowed_caps:
                raise RecordError("applied cap is not allowed by this task rubric")
            text_field(applied.get("reason"), "applied cap reason")
            cap_values.append(value)
        if caps and not critical:
            raise RecordError("applied theory cap needs a recorded critical error")
        equal_score(entry.get("effective_score"), min([raw, *cap_values]), "effective_score")
        usability = entry.get("usability")
        if usability not in USABLE_LABELS | {"partially-usable", "unusable", "not-assessable"}:
            raise RecordError("unknown usability")
        if usability in USABLE_LABELS and critical:
            raise RecordError("usable adjudication cannot contain critical errors")
        self.counts["scored"] += 1

    def run(self) -> dict:
        try:
            study = self.read("study.json")
            freeze_raw = self.read("freeze.json", as_json=False)
            if study is None or freeze_raw is None:
                return self.result()
            study = object_field(study, "study")
            freeze_sha = hashlib.sha256(freeze_raw).hexdigest()
            if digest(study.get("freeze_sha256")) != freeze_sha:
                raise RecordError("study freeze_sha256 does not bind freeze.json")
            freeze = object_field(strict_json(freeze_raw.decode("utf-8")), "freeze")
            files = object_field(freeze.get("files"), "freeze.files")
            projections = object_field(study.get("publication_projections", {}),
                                       "study.publication_projections")
            # Only this organizer-only provenance note may redact a local path.
            # Scientific tasks, source/answer material and grading rules keep
            # their original freeze hashes without any projection escape hatch.
            if set(projections) - {"references/design-provenance.md"}:
                raise RecordError("frozen scientific files cannot use publication projections")
            if set(projections) - set(files):
                raise RecordError("projection is not bound by original freeze")
            for name, sha in files.items():
                relative_name(name)
                if name in {"study.json", "freeze.json"}:
                    raise RecordError("study/freeze must not occur inside freeze.files")
                if name in projections:
                    item = object_field(projections[name], "provenance projection")
                    if (set(item) != {"original_sha256", "public_sha256", "changes"} or
                            digest(item["original_sha256"]) != digest(sha) or
                            item["changes"] != ["machine-path-redaction"]):
                        raise RecordError("invalid organizer provenance projection")
                    self.read(name, expected_sha=digest(item["public_sha256"]), as_json=False)
                    self.observations.append({"provenance_publication_projection": name,
                                              "original_sha256": sha,
                                              "public_sha256": item["public_sha256"]})
                else:
                    self.read(name, expected_sha=digest(sha), as_json=False)
            for name in ("rubrics/theory.json", "rubrics/data.json"):
                if name not in files:
                    raise RecordError(f"rubric is not bound by freeze.files: {name}")
            expected = self.expected(study)
            theory = self.read("rubrics/theory.json")
            data = self.read("rubrics/data.json")
            if theory is None or data is None:
                return self.result()
            theory = object_field(theory, "theory rubric")
            data = object_field(data, "data rubric")
            rubrics = {task: self.rubric(task, theory, data) for task in TASKS}
            trial_dir = self.root / "trials"
            if trial_dir.is_symlink():
                raise RecordError("trials directory must not be a symlink")
            if trial_dir.exists():
                for path in trial_dir.iterdir():
                    if path.suffix == ".json" and path.stem not in expected:
                        raise RecordError(f"unexpected trial record: {path.name}")
            for trial_id, planned in expected.items():
                try:
                    trial = self.read(f"trials/{trial_id}.json")
                    if trial is None:
                        continue
                    trial = object_field(trial, "trial")
                    self.counts["recorded"] += 1
                    for field in ("trial_id", "task_id", "arm", "replicate", "predecessor"):
                        if field not in trial or trial[field] != planned[field]:
                            raise RecordError(f"trial metadata mismatch: {field}")
                    integer(trial["replicate"], minimum=1)
                    if digest(trial.get("freeze_sha256")) != freeze_sha:
                        raise RecordError("trial freeze_sha256 mismatch")
                    execution = self.reference(trial.get("execution"), trial_id + ".execution")
                    terminal_failure = None
                    if execution is not None:
                        self.execution(execution, trial_id)
                        terminal_failure = execution.get("terminal_failure", False)
                    if "report" not in trial:
                        raise RecordError("trial must declare report, including null for terminal failure")
                    if trial["report"] is None:
                        if terminal_failure is False:
                            raise RecordError("null report requires a terminal failure")
                        report = None
                    else:
                        report = self.reference(trial["report"], trial_id + ".report", as_json=False)
                    if report is not None:
                        characters = len(report.decode("utf-8"))
                        if characters > 12000:
                            self.observations.append({"trial_id": trial_id,
                                                      "requested_report_budget_exceeded": True,
                                                      "report_characters": characters})
                    artifacts = self.reference(trial.get("artifacts"), trial_id + ".artifacts")
                    if artifacts is not None:
                        self.artifacts(artifacts)
                    if "adjudication" not in trial:
                        raise RecordError("trial must declare adjudication, including null")
                    if trial["adjudication"] is None:
                        self.missing.append(f"unscored trial: {trial_id}")
                    else:
                        judged = self.reference(trial["adjudication"], trial_id + ".adjudication")
                        if judged is not None:
                            judged = object_field(judged, "adjudication")
                            if trial["report"] is None and judged.get("scored") is True:
                                raise RecordError("scored adjudication requires a scientific report")
                            if judged.get("scored") is True:
                                if digest(judged.get("report_sha256")) != digest(
                                        trial["report"].get("sha256")):
                                    raise RecordError("adjudication does not bind the scored report")
                            rubric, caps = rubrics[planned["task_id"]]
                            self.adjudication(judged, planned["task_id"], rubric, caps,
                                              terminal_failure=terminal_failure)
                except (RecordError, OSError, UnicodeError, ValueError, TypeError,
                        OverflowError, RecursionError) as exc:
                    self.errors.append(f"{trial_id}: {exc}")
        except (RecordError, OSError, UnicodeError, ValueError, TypeError,
                OverflowError, RecursionError) as exc:
            self.errors.append(str(exc))
        return self.result()

    def result(self) -> dict:
        return {
            "status": "invalid" if self.errors else "incomplete" if self.missing else "complete",
            "scope": "record closure, file identity and score arithmetic only; scientific validity not assessed",
            "counts": self.counts,
            "errors": self.errors,
            "missing": self.missing,
            "observations": self.observations,
            "effective_model_equality": "not-inferred",
        }


def validate(root: Path | str) -> dict:
    return Validator(Path(root)).run()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args(argv)
    result = validate(args.root)
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    if result["status"] == "invalid":
        return 2
    if result["status"] == "incomplete" and not args.allow_incomplete:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
