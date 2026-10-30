#!/usr/bin/env python3
"""Check lifecycle-study records, file identities and score arithmetic only.

Four stages within a project are dependent observations. Failed execution or
read-only audits remain in the record; closure is not scientific success.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
import stat


STAGES = ("A", "B", "C", "D")
STAGE_POINTS = {"A": 20, "B": 35, "C": 30, "D": 15}
ARMS = {"baseline", "guidance", "core"}
EFFECTIVE_FIELDS = {"model", "reasoning_effort", "temperature", "seed", "output_token_limit"}
SHA = re.compile(r"[0-9a-f]{64}\Z")
IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*\Z")


class RecordError(ValueError):
    pass


def obj(value, label):
    if not isinstance(value, dict):
        raise RecordError(label + " must be an object")
    return value


def array(value, label):
    if not isinstance(value, list):
        raise RecordError(label + " must be an array")
    return value


def text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise RecordError(label + " must be nonempty text")
    return value


def digest(value):
    if not isinstance(value, str) or not SHA.fullmatch(value):
        raise RecordError("sha256 must be 64 lowercase hexadecimal characters")
    return value


def integer(value, minimum=0):
    if type(value) is not int or value < minimum:
        raise RecordError("expected integer >= " + str(minimum))
    return value


def number(value):
    try:
        valid = type(value) in (int, float) and math.isfinite(value) and value >= 0
    except OverflowError:
        valid = False
    if not valid:
        raise RecordError("expected finite nonnegative number")
    return value


def equal(actual, expected, label):
    if not math.isclose(number(actual), expected, rel_tol=0, abs_tol=1e-9):
        raise RecordError(label + " arithmetic mismatch")


def relative(value):
    text(value, "path")
    if ("\\" in value or ":" in value or "\x00" in value
            or any(part in ("", ".", "..") for part in value.split("/"))
            or PurePosixPath(value).is_absolute()
            or PurePosixPath(value).as_posix() != value):
        raise RecordError("unsafe or noncanonical relative path: " + repr(value))
    return value


def strict_json(raw):
    def pairs(entries):
        result = {}
        for key, value in entries:
            if key in result:
                raise RecordError("duplicate JSON key: " + key)
            result[key] = value
        return result

    def constant(value):
        raise RecordError("nonfinite JSON number: " + value)

    def check(value):
        if isinstance(value, float) and not math.isfinite(value):
            raise RecordError("nonfinite JSON number")
        if isinstance(value, dict):
            for child in value.values():
                check(child)
        elif isinstance(value, list):
            for child in value:
                check(child)

    result = json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)
    check(result)
    return result


class Validator:
    def __init__(self, root):
        self.root = Path(root).absolute()
        self.errors, self.missing, self.observations = [], [], []
        self.owners, self.submissions = {}, set()
        self.counts = {"expected_chains": 6, "expected_stages": 24, "recorded": 0,
                       "stages_recorded": 0, "scored": 0, "executed": 0,
                       "failed": 0, "not-run": 0, "readonly_failures": 0}

    def read(self, name, checksum=None, *, as_json=True, byte_count=None):
        name = relative(name)
        current = self.root
        if current.is_symlink():
            raise RecordError("evaluation root must not be a symlink")
        for part in PurePosixPath(name).parts:
            current /= part
            if current.is_symlink():
                raise RecordError("symlink rejected: " + name)
        if checksum is not None:
            digest(checksum)
        if byte_count is not None:
            integer(byte_count)
        if not current.exists():
            self.missing.append("missing file: " + name)
            return None
        if not stat.S_ISREG(current.stat().st_mode):
            raise RecordError("expected regular file: " + name)
        raw = current.read_bytes()
        if checksum is not None and hashlib.sha256(raw).hexdigest() != checksum:
            raise RecordError("hash mismatch: " + name)
        if byte_count is not None and len(raw) != byte_count:
            raise RecordError("byte length mismatch: " + name)
        return strict_json(raw.decode("utf-8")) if as_json else raw

    def ref(self, ref, owner, *, as_json=True):
        ref = obj(ref, owner)
        name = relative(ref.get("path"))
        previous = self.owners.get(name)
        if previous is not None and previous != owner:
            raise RecordError("record reference reused: " + name)
        self.owners[name] = owner
        return self.read(name, digest(ref.get("sha256")), as_json=as_json)

    def plan(self, study):
        entries = array(study.get("expected_chains"), "expected_chains")
        if len(entries) != 6:
            raise RecordError("expected exactly six project chains")
        planned, combinations = {}, set()
        for entry in entries:
            entry = obj(entry, "expected chain")
            identifier = text(entry.get("chain_id"), "chain_id")
            if not IDENTIFIER.fullmatch(identifier) or identifier in planned:
                raise RecordError("invalid or duplicate chain_id")
            pair = entry.get("case_id"), entry.get("arm")
            if pair[0] not in {"T", "D"} or pair[1] not in ARMS or pair in combinations:
                raise RecordError("invalid or duplicate case/arm")
            combinations.add(pair)
            planned[identifier] = entry
        if combinations != {(case, arm) for case in ("T", "D") for arm in ARMS}:
            raise RecordError("plan must cover two cases and three arms")
        self.counts.update(expected_chains=6, expected_stages=24)
        return planned

    def rubric(self):
        value = self.read("rubric.json")
        if value is None:
            return None
        value = obj(value, "rubric")
        stages = obj(value.get("stages"), "rubric.stages")
        if set(stages) != set(STAGES):
            raise RecordError("rubric must cover four stages")
        result = {}
        for stage in STAGES:
            section = obj(stages[stage], "rubric stage")
            equal(section.get("points"), STAGE_POINTS[stage], "stage maximum")
            total = 0
            for item in array(section.get("items"), "rubric items"):
                item = obj(item, "rubric item")
                name = text(item.get("id"), "criterion id")
                points = number(item.get("points"))
                if name in result or points <= 0:
                    raise RecordError("duplicate or nonpositive rubric item")
                result[name] = points
                total += points
            equal(total, STAGE_POINTS[stage], "stage rubric sum")
        equal(value.get("total"), 100, "rubric total")
        return result

    def execution(self, value, status, owner):
        value = obj(value, "execution")
        if value.get("status") != status:
            raise RecordError("execution status does not match stage")
        effective = obj(value.get("effective"), "execution.effective")
        if not EFFECTIVE_FIELDS <= set(effective):
            raise RecordError("effective configuration must retain unknown fields")
        for key in ("model", "reasoning_effort"):
            if effective[key] is not None:
                text(effective[key], key)
        if effective["temperature"] is not None:
            number(effective["temperature"])
        if effective["seed"] is not None and type(effective["seed"]) is not int:
            raise RecordError("seed must be integer or null")
        if effective["output_token_limit"] is not None:
            integer(effective["output_token_limit"], 1)
        for name in ("tool_calls", "network_calls"):
            if name not in value:
                raise RecordError("execution must retain " + name)
            if value[name] is not None:
                integer(value[name])
        if value["network_calls"] not in (0, None):
            raise RecordError("network calls must be zero or unknown")
        violations = array(value.get("violations"), "execution.violations")
        if value.get("scope") != "instruction-only; no OS audit":
            raise RecordError("execution must retain instructed-isolation scope")
        self.observations.append({"stage": owner, "violations": violations,
            "unknown_effective_fields": sorted(k for k in EFFECTIVE_FIELDS if effective[k] is None)})

    def manifest(self, value):
        value = obj(value, "project manifest")
        text(value.get("scope"), "manifest.scope")
        names, public_names = set(), set()
        for item in array(value.get("files"), "manifest.files"):
            item = obj(item, "manifest item")
            name = relative(item.get("path"))
            if name in names:
                raise RecordError("duplicate manifest path")
            names.add(name)
            checksum = digest(item.get("sha256"))
            integer(item.get("bytes"))
            if type(item.get("distributed")) is not bool:
                raise RecordError("distributed must be boolean")
            if not item["distributed"]:
                if any(key in item for key in ("public_path", "public_sha256", "public_bytes")):
                    raise RecordError("undistributed file cannot declare public bytes")
                continue
            public = relative(item.get("public_path"))
            if public in public_names:
                raise RecordError("duplicate public artifact path")
            public_names.add(public)
            self.read(public, digest(item.get("public_sha256", checksum)), as_json=False,
                      byte_count=item.get("public_bytes"))

    def readonly(self, value, owner):
        value = obj(value, "readonly audit")
        if type(value.get("passed")) is not bool:
            raise RecordError("readonly audit passed must be boolean")
        files = array(value.get("file_differences"), "file_differences")
        directories = array(value.get("directory_mtime_differences"), "directory_mtime_differences")
        text(value.get("scope"), "readonly.scope")
        if value["passed"] and (files or directories):
            raise RecordError("passed readonly audit contradicts its differences")
        if not value["passed"]:
            self.counts["readonly_failures"] += 1
        self.observations.append({"stage": owner, "readonly_passed": value["passed"],
                                  "file_differences": files, "directory_mtime_differences": directories})

    def stage(self, value, identifier, phase):
        value = obj(value, "stage")
        status = value.get("status")
        if status not in {"executed", "failed", "not-run"}:
            raise RecordError("unknown stage status")
        self.counts["stages_recorded"] += 1
        self.counts[status] += 1
        owner = identifier + "." + phase
        if status == "not-run":
            self.missing.append("stage not run: " + owner)
        report_sha = None
        for field in ("report", "execution", "project_manifest", "readonly_audit"):
            if field not in value:
                raise RecordError("stage must declare " + field + ", including null")
            ref = value[field]
            if field == "readonly_audit" and phase in {"A", "C"}:
                if ref is not None:
                    raise RecordError("writing stages must declare null readonly audit")
                continue
            if ref is None:
                if (status == "executed" or (field == "execution" and status == "failed")
                        or (field == "readonly_audit" and phase in {"B", "D"})):
                    self.missing.append("missing " + owner + "." + field)
                continue
            result = self.ref(ref, owner + "." + field, as_json=field != "report")
            if field == "report":
                report_sha = digest(ref.get("sha256"))
            if result is None:
                continue
            if field == "execution":
                self.execution(result, status, owner)
            elif field == "project_manifest":
                self.manifest(result)
            elif field == "readonly_audit":
                self.readonly(result, owner)
        return report_sha, status

    def adjudication(self, value, identifier, reports, statuses, rubric):
        value = obj(value, "adjudication")
        if value.get("chain_id") != identifier or type(value.get("scored")) is not bool:
            raise RecordError("adjudication chain/scored mismatch")
        submission = text(value.get("submission_id"), "submission_id")
        if submission in self.submissions:
            raise RecordError("duplicate anonymous submission")
        self.submissions.add(submission)
        if value.get("arm_hidden") is not True:
            raise RecordError("adjudication must declare withheld arm map")
        array(value.get("critical_errors"), "critical_errors")
        array(value.get("notes"), "notes")
        text(value.get("usability"), "usability")
        if value.get("caps_applied", []) != []:
            raise RecordError("this study has no extra score cap")
        criteria = array(value.get("criteria"), "criteria")
        equal(value.get("max_score"), 100, "max_score")
        if not value["scored"]:
            if ("failed" not in statuses or criteria or "raw_score" not in value
                    or "effective_score" not in value or value["raw_score"] is not None
                    or value["effective_score"] is not None):
                raise RecordError("unscored failure requires failed stage and explicit null scores")
            return
        bound = obj(value.get("report_sha256_by_stage"), "report_sha256_by_stage")
        if set(bound) != set(STAGES):
            raise RecordError("adjudication must bind all four report slots")
        for phase in STAGES:
            if reports.get(phase) is None:
                if bound[phase] is not None:
                    raise RecordError("absent report must retain null report identity")
            elif digest(bound[phase]) != reports[phase]:
                raise RecordError("adjudication report binding mismatch")
        seen, total = set(), 0
        for item in criteria:
            item = obj(item, "criterion")
            name = item.get("id")
            if not isinstance(name, str) or not name.strip() or name in seen:
                raise RecordError("unknown or duplicate criterion")
            seen.add(name)
            maximum = number(item.get("max_points"))
            if rubric is not None:
                if name not in rubric:
                    raise RecordError("unknown criterion")
                equal(maximum, rubric[name], "criterion maximum")
            score = number(item.get("score"))
            if score > maximum:
                raise RecordError("criterion exceeds maximum")
            evidence = item.get("evidence")
            if not isinstance(evidence, (str, list)) or not evidence:
                raise RecordError("criterion evidence must be nonempty")
            text(item.get("rationale"), "criterion rationale")
            total += score
        if rubric is not None and seen != set(rubric):
            raise RecordError("adjudication must cover frozen rubric")
        equal(value.get("raw_score"), total, "raw_score")
        equal(value.get("effective_score"), total, "effective_score")
        if rubric is not None:
            self.counts["scored"] += 1

    def chain(self, value, expected, freeze_sha, rubric):
        value = obj(value, "chain")
        identifier = expected["chain_id"]
        if any(value.get(key) != expected[key] for key in ("chain_id", "case_id", "arm")):
            raise RecordError("chain identity differs from plan")
        if digest(value.get("freeze_sha256")) != freeze_sha:
            raise RecordError("chain does not bind frozen design")
        self.counts["recorded"] += 1
        phases = obj(value.get("stages"), "chain.stages")
        if set(phases) - set(STAGES):
            raise RecordError("unexpected stage")
        reports, statuses = {}, []
        for phase in STAGES:
            if phase not in phases:
                self.missing.append("missing stage: " + identifier + "." + phase)
                continue
            reports[phase], status = self.stage(phases[phase], identifier, phase)
            statuses.append(status)
        if "adjudication" not in value or "probes" not in value:
            raise RecordError("chain must declare adjudication and probes, including null")
        if value["adjudication"] is None:
            self.missing.append("unscored chain: " + identifier)
        else:
            result = self.ref(value["adjudication"], identifier + ".adjudication")
            if result is not None:
                self.adjudication(result, identifier, reports, statuses, rubric)
        if value["probes"] is not None:
            self.ref(value["probes"], identifier + ".probes")

    def run(self):
        try:
            study = self.read("study.json")
            raw = self.read("freeze.json", as_json=False)
            if study is not None:
                study = obj(study, "study")
                digest(study.get("freeze_sha256"))
                expected = self.plan(study)
            if raw is not None:
                files = obj(obj(strict_json(raw.decode("utf-8")), "freeze").get("files"), "freeze.files")
                if "rubric.json" not in files:
                    raise RecordError("freeze must bind rubric.json")
                projections = obj(study.get("publication_projections", {}) if study else {},
                                  "publication projections")
                if set(projections) - {"audits/key-audit.json"} or set(projections) - set(files):
                    raise RecordError("scientific frozen files cannot use publication projections")
                for name, checksum in files.items():
                    expected_sha = digest(checksum)
                    if name in projections:
                        projection = obj(projections[name], "administrative audit projection")
                        if (digest(projection.get("original_sha256")) != expected_sha or
                                projection.get("changes") != ["machine-path-redaction"]):
                            raise RecordError("invalid administrative audit projection")
                        expected_sha = digest(projection.get("public_sha256"))
                        self.observations.append({"administrative_audit_projection": name,
                            "original_sha256": checksum, "public_sha256": expected_sha})
                    self.read(name, expected_sha, as_json=False)
            if study is None or raw is None:
                return self.result()
            freeze_sha = hashlib.sha256(raw).hexdigest()
            if digest(study.get("freeze_sha256")) != freeze_sha:
                raise RecordError("study does not bind freeze.json")
            rubric = self.rubric()
            for identifier, planned in expected.items():
                try:
                    value = self.read("chains/" + identifier + ".json")
                    if value is not None:
                        self.chain(value, planned, freeze_sha, rubric)
                except (ValueError, TypeError, OSError, OverflowError, RecursionError) as exc:
                    self.errors.append(identifier + ": " + str(exc))
        except (ValueError, TypeError, OSError, OverflowError, RecursionError) as exc:
            self.errors.append(str(exc))
        return self.result()

    def result(self):
        return {"status": "invalid" if self.errors else "incomplete" if self.missing else "complete",
                "scope": "record closure, file identity and score arithmetic only; scientific validity not assessed",
                "counts": self.counts, "errors": self.errors, "missing": self.missing,
                "observations": self.observations, "effective_model_equality": "not-inferred",
                "independent_replicates": "not-inferred; four dependent stages per project"}


def validate(root):
    return Validator(root).run()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args(argv)
    result = validate(args.root)
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    return 2 if result["status"] == "invalid" else (
        1 if result["status"] == "incomplete" and not args.allow_incomplete else 0)


if __name__ == "__main__":
    raise SystemExit(main())
