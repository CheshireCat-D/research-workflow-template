"""Behavioral CLI checks, using synthetic projects and separate processes.

These tests assess registration, persistence and recovery, not research validity.
Run with: python3 -B -m unittest discover -s tests -v
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import contextmanager
from unittest import mock
from platform_support import symlink_or_skip


REPOSITORY = Path(__file__).resolve().parents[1]
CLI = REPOSITORY / "tools" / "research.py"
sys.path.insert(0, str(REPOSITORY))


def snapshot(root):
    """Include files, directories, symlinks, content and modification times."""
    result = {}
    for path in [root, *sorted(root.rglob("*"))]:
        rel = "." if path == root else path.relative_to(root).as_posix()
        stat = path.lstat()
        if path.is_symlink():
            content = ("symlink", os.readlink(path))
        elif path.is_file():
            content = ("file", hashlib.sha256(path.read_bytes()).hexdigest())
        else:
            content = ("directory",)
        result[rel] = (*content, stat.st_mtime_ns, stat.st_mode)
    return result


class CoreCLITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="rw-core-tests-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.project = self.base / "研究项目 with spaces"
        self.inputs = self.base / "record inputs"
        self.inputs.mkdir()
        self.sequence = 0
        self.invoke("init", "--output", self.project, "--title", "合成研究问题",
                    "--discipline", "natural-sciences", "--method", "formal-theory")

    def invoke(self, *args, expected=0, cli=CLI, env=None, input_text=None):
        proc = subprocess.run([sys.executable, "-X", "utf8", "-I", "-B", str(cli), *map(str, args)],
                              cwd=self.base, capture_output=True, text=True,
                              encoding="utf-8", timeout=20, env=env, input=input_text)
        self.assertEqual(proc.returncode, expected, (proc.args, proc.stdout, proc.stderr))
        self.assertEqual(proc.stderr, "", proc.stderr)
        try:
            payload = json.loads(proc.stdout)
        except json.JSONDecodeError as exc:
            self.fail(f"CLI did not emit one JSON document: {proc.stdout!r}; {exc}")
        self.assertIsInstance(payload, dict)
        return payload

    def register(self, kind, data, *, expected=0, replace=False, version=None):
        self.sequence += 1
        path = self.inputs / f"input-{self.sequence}.json"
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        args = ["register", "--root", self.project, "--kind", kind, "--file", path]
        if replace:
            args.append("--replace")
        if version is not None:
            args.extend(["--expected-version", str(version)])
        return self.invoke(*args, expected=expected)

    def registry(self):
        return json.loads((self.project / "records/registry.json").read_text(encoding="utf-8"))

    def statement(self, identifier="S1", **updates):
        return {"id": identifier, "text": "有限范围观察需要保留其范围。", "type": "empirical",
                "scope": "合成材料，仅用于接口验证", **updates}

    def source(self, identifier="SRC1", **updates):
        return {"id": identifier, "title": "合成馆藏材料", "locator": "catalog:synthetic-1",
                "version": "edition-1", "content_access": "metadata-only", **updates}

    def local(self, identifier="E1", filename="notes/data.txt"):
        path = self.project / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("synthetic observation 1\n", encoding="utf-8")
        return {"id": identifier, "type": "synthetic-observation", "description": "自建测试材料",
                "provenance": "生成于本测试，不来自任何个人稿件", "location": {"kind": "local", "path": filename}}

    def activity(self, identifier="A1", **updates):
        return {"id": identifier, "title": "比较合成材料", "status": "pending", **updates}

    def no_mutation(self, kind, data, **kwargs):
        before = snapshot(self.project)
        result = self.register(kind, data, expected=2, **kwargs)
        self.assertEqual(snapshot(self.project), before)
        self.assertFalse(result["passed"])
        self.assertTrue(result["errors"])
        return result

    def check(self, expected=0):
        return self.invoke("check", "--root", self.project, expected=expected)

    def assert_stale(self, report, *ids):
        states = {row["id"]: row for row in report["activities"]}
        for identifier in ids:
            self.assertEqual(states[identifier]["declared_status"], "done")
            self.assertEqual(states[identifier]["effective_status"], "stale")
            self.assertTrue(states[identifier]["stale_reasons"])

    def test_initialize_unicode_neutral_and_new_project_files(self):
        for path in ("project.json", "PROJECT.md", "records/registry.json", ".research/write.lock", ".gitignore"):
            self.assertTrue((self.project / path).is_file(), path)
        config = json.loads((self.project / "project.json").read_text(encoding='utf-8'))
        self.assertEqual(config["title"], "合成研究问题")
        self.assertIsNone(config["deliverable"]["venue"])
        self.assertEqual(config["deliverable"]["contribution_benchmarks"], [])
        self.assertEqual(config["governance"]["applicability"], "unknown")
        self.assertEqual(self.check()["scientific_validity"], "not-assessed")

    def test_all_disciplines_accept_different_methods_and_modes(self):
        combinations = [
            ("natural-sciences", "formal-theory", "light"),
            ("engineering", "engineering-design", "structured"),
            ("medicine-health", "empirical-quantitative", "reproducible"),
            ("agriculture-life", "measurement-experiment", "structured"),
            ("humanities", "historical-interpretive", "light"),
            ("social-sciences", "qualitative", "reproducible"),
            ("law", "legal-analysis", "structured"),
        ]
        for discipline, method, mode in combinations:
            with self.subTest(discipline=discipline):
                target = self.base / discipline
                self.invoke("init", "--output", target, "--title", "Synthetic question", "--discipline", discipline,
                            "--method", method, "--mode", mode, "--language", "en")
                config = json.loads((target / "project.json").read_text(encoding='utf-8'))
                self.assertEqual(config["disciplines"], [discipline])
                self.assertEqual(config["methods"], [method])
                self.assertEqual(config["workflow_mode"], mode)
                self.assertTrue(self.invoke("check", "--root", target)["passed"])

    def test_initialization_never_overwrites_existing_or_empty_path(self):
        empty = self.base / "empty"
        empty.mkdir()
        file = self.base / "keep.txt"
        file.write_text("keep", encoding="utf-8")
        for target in (self.project, empty, file):
            with self.subTest(target=target.name):
                before = snapshot(target) if target.is_dir() else target.read_bytes()
                self.invoke("init", "--output", target, "--title", "Replacement", expected=2)
                after = snapshot(target) if target.is_dir() else target.read_bytes()
                self.assertEqual(after, before)

    def test_initialization_refuses_dangling_symlink(self):
        target = self.base / "missing-target"
        link = self.base / "dangling"
        symlink_or_skip(self, link, target, target_is_directory=True)
        self.invoke("init", "--output", link, "--title", "No overwrite", expected=2)
        self.assertTrue(link.is_symlink())
        self.assertFalse(target.exists())

    def test_invalid_configuration_does_not_create_output(self):
        for options in (("--discipline", "unknown"), ("--method", "unknown"), ("--entry", "unknown")):
            target = self.base / ("invalid-" + str(len(list(self.base.iterdir()))))
            self.invoke("init", "--output", target, "--title", "No create", *options, expected=2)
            self.assertFalse(target.exists())

    def test_registration_persists_all_eight_kinds_across_processes(self):
        self.register("source", self.source())
        self.register("statement", self.statement())
        evidence = self.local()
        evidence["source_ids"] = ["SRC1"]
        self.register("evidence", evidence)
        self.register("relation", {"id": "R1", "statement_id": "S1", "evidence_id": "E1", "relation": "qualifies",
                                   "rationale": "材料仅覆盖有限范围", "scope": "测试范围"})
        self.register("activity", self.activity(inputs=["statement:S1", "evidence:E1"]))
        self.register("decision", {"id": "D1", "choice": "补充对照", "rationale": "范围不足", "responsible": "test-researcher",
                                   "decided_at": "2026-01-01", "evidence_refs": ["E1"]})
        self.register("artifact", {"id": "F1", "type": "note", "description": "合成笔记", "path": "notes/data.txt"})
        self.register("method-binding", {"id": "M1", "method_id": "formal-theory", "profile_version": "0.1",
                                         "reason": "明确证明义务", "applies_to": ["statement:S1"], "variant": "proof"})
        report = self.invoke("resume", "--root", self.project)
        self.assertEqual(sum(report["counts"].values()), 8)
        self.assertTrue(all(count == 1 for count in report["counts"].values()))
        self.assertEqual(report["scientific_validity"], "not-assessed")

    def test_duplicate_requires_explicit_version_and_preserves_history(self):
        original = self.statement()
        created = self.register("statement", original)
        replacement = self.statement(text="明确保留新的适用范围。")
        self.no_mutation("statement", replacement)
        self.no_mutation("statement", replacement, replace=True)
        self.no_mutation("statement", replacement, replace=True, version=created["version"] + 1)
        updated = self.register("statement", replacement, replace=True, version=created["version"])
        self.assertEqual(updated["version"], created["version"] + 1)
        registry = self.registry()
        self.assertEqual(registry["records"]["statements"]["S1"]["data"], replacement)
        self.assertEqual(registry["history"][-1]["previous"]["data"], original)

    def test_replace_unknown_record_never_creates_it(self):
        self.no_mutation("statement", self.statement(), replace=True, version=1)

    def test_missing_fields_unknown_fields_and_bad_types_do_not_write(self):
        for data in ({"id": "S1"}, self.statement(type="proved"), self.statement(depends_on="S1"), self.statement(unexpected=True)):
            with self.subTest(data=data):
                self.no_mutation("statement", data)

    def test_missing_cross_record_references_do_not_write(self):
        records = [
            ("statement", self.statement(depends_on=["missing"])),
            ("evidence", {**self.local(), "source_ids": ["missing"]}),
            ("relation", {"id": "R1", "statement_id": "missing", "evidence_id": "missing", "relation": "supports", "rationale": "test", "scope": "test"}),
            ("activity", self.activity(inputs=["source:missing"])),
            ("method-binding", {"id": "M1", "method_id": "qualitative", "profile_version": "0.1", "reason": "test", "applies_to": ["statement:missing"]}),
        ]
        for kind, data in records:
            with self.subTest(kind=kind):
                self.no_mutation(kind, data)

    def test_statement_cycle_and_self_activity_cycle_rejected_atomically(self):
        self.register("statement", self.statement())
        self.register("statement", self.statement("S2", depends_on=["S1"]))
        self.no_mutation("statement", self.statement(depends_on=["S2"]), replace=True, version=1)
        self.no_mutation("activity", self.activity(depends_on=["A1"]))

    def test_method_variants_are_bound_to_their_own_method(self):
        self.register("statement", self.statement())
        for updates in ({"method_id": "unknown"}, {"variant": "interview"}, {"applies_to": []}):
            self.no_mutation("method-binding", {"id": "M1", "method_id": "formal-theory", "profile_version": "0.1",
                                              "reason": "测试范围", "applies_to": ["statement:S1"], **updates})

    def test_unsafe_local_paths_and_symlinks_cannot_escape(self):
        outside = self.base / "outside.txt"
        outside.write_text("protected", encoding="utf-8")
        symlink_or_skip(self, self.project / "linked.txt", outside)
        for path in (str(outside), "../outside.txt", "linked.txt"):
            with self.subTest(path=path):
                data = self.local()
                data["location"]["path"] = path
                self.no_mutation("evidence", data)
        symlink_or_skip(self, self.project / "linked-directory", self.base, target_is_directory=True)
        data["location"]["path"] = "linked-directory/outside.txt"
        self.no_mutation("evidence", data)
        self.assertEqual(outside.read_text(encoding='utf-8'), "protected")

    def test_internal_metadata_cannot_be_its_own_evidence_or_artifact(self):
        for path in ("project.json", "records/registry.json", ".research/write.lock"):
            data = {"id": "E1", "type": "test", "description": "test", "provenance": "test",
                    "location": {"kind": "local", "path": path}}
            self.no_mutation("evidence", data)
            self.no_mutation("artifact", {"id": "F1", "type": "test", "description": "test", "path": path})

    def test_missing_local_resource_is_not_registered(self):
        self.no_mutation("evidence", {"id": "E1", "type": "test", "description": "test", "provenance": "test",
                                     "location": {"kind": "local", "path": "missing.csv"}})

    def test_internal_file_hardlinks_cannot_be_registered_as_research(self):
        (self.project / '.research/nested').mkdir()
        (self.project / '.research/nested/state.json').write_text('{}\n', encoding='utf-8')
        for number, protected in enumerate(('project.json', 'records/registry.json',
                                             '.research/write.lock', '.research/nested/state.json')):
            alias = f'notes/internal-alias-{number}.txt'
            (self.project / alias).parent.mkdir(exist_ok=True)
            os.link(self.project / protected, self.project / alias)
            with self.subTest(protected=protected):
                self.no_mutation('evidence', {'id': 'E1', 'type': 'test', 'description': 'test',
                    'provenance': 'test', 'location': {'kind': 'local', 'path': alias}})
                self.no_mutation('artifact', {'id': 'F1', 'type': 'test',
                    'description': 'test', 'path': alias})

    def test_case_aliases_are_rejected_only_when_the_filesystem_aliases_metadata(self):
        for number, (protected, alias) in enumerate((('project.json', 'PROJECT.JSON'),
                ('records/registry.json', 'records/REGISTRY.json'),
                ('.research/write.lock', '.RESEARCH/write.lock'))):
            target = self.project / alias
            if target.exists() and target.samefile(self.project / protected):
                self.no_mutation('artifact', {'id': 'F1', 'type': 'test',
                    'description': 'test', 'path': alias})
            else:
                target.parent.mkdir(exist_ok=True)
                target.write_text('A distinct file on a case-sensitive filesystem.\n', encoding='utf-8')
                self.register('artifact', {'id': 'F' + str(number), 'type': 'test',
                    'description': 'distinct research file', 'path': alias})
        self.assertTrue(self.check()['passed'])

    def test_read_commands_reject_tampered_internal_alias_without_repair(self):
        self.register('evidence', self.local())
        alias = 'notes/metadata-hardlink.json'
        os.link(self.project / 'project.json', self.project / alias)
        registry = self.registry()
        registry['records']['evidence']['E1']['data']['location']['path'] = alias
        (self.project / 'records/registry.json').write_text(json.dumps(registry), encoding='utf-8')
        before = snapshot(self.project)
        for command in ('check', 'resume'):
            report = self.invoke(command, '--root', self.project, expected=2)
            self.assertFalse(report['passed'])
            self.assertEqual(snapshot(self.project), before)

    @unittest.skipUnless(os.name == 'posix', 'POSIX RLIMIT_NOFILE; native Windows handle traversal is tested separately')
    def test_wide_internal_state_is_read_only_under_a_small_descriptor_limit(self):
        import resource
        hard = resource.getrlimit(resource.RLIMIT_NOFILE)[1]
        if hard != resource.RLIM_INFINITY and hard < 64:
            self.skipTest('The process hard descriptor limit is below the test budget')
        for number in range(150):
            (self.project / '.research' / f'check-{number}').mkdir()
        before = snapshot(self.project)
        wrapper = ('import resource,runpy,sys; '
                   'resource.setrlimit(resource.RLIMIT_NOFILE, '
                   '(64, resource.getrlimit(resource.RLIMIT_NOFILE)[1])); '
                   'sys.argv=sys.argv[1:]; runpy.run_path(sys.argv[0],run_name="__main__")')
        result = subprocess.run([sys.executable, '-X', 'utf8', '-I', '-B', '-c', wrapper,
                                 str(CLI), 'check', '--root', str(self.project)],
                                cwd=self.base, text=True, encoding='utf-8', capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stderr, '')
        report = json.loads(result.stdout)
        self.assertTrue(report['passed'])
        self.assertTrue(report['read_only'])
        self.assertEqual(snapshot(self.project), before)

    def test_local_content_changes_propagate_stale_without_rewriting_declared_status(self):
        evidence = self.local()
        self.register("evidence", evidence)
        self.register("activity", self.activity(status="done", inputs=["evidence:E1"]))
        self.register("activity", self.activity("A2", status="done", depends_on=["A1"]))
        (self.project / "notes/data.txt").write_text("synthetic observation 2\n", encoding='utf-8')
        report = self.check(expected=1)
        self.assert_stale(report, "A1", "A2")
        self.assertIn("file_changed", {row["code"] for row in report["findings"]})
        self.assertEqual(self.registry()["records"]["activities"]["A1"]["data"]["status"], "done")

    def test_record_changes_propagate_stale_transitively(self):
        self.register("statement", self.statement())
        self.register("activity", self.activity(status="done", inputs=["statement:S1"]))
        self.register("activity", self.activity("A2", status="done", depends_on=["A1"]))
        self.register("statement", self.statement(scope="新的合成范围"), replace=True, version=1)
        self.assert_stale(self.check(expected=1), "A1", "A2")

    def test_new_evidence_relation_invalidates_prior_statement_review(self):
        self.register("statement", self.statement())
        self.register("activity", self.activity(status="done", inputs=["statement:S1"]))
        self.register("evidence", self.local())
        self.register("relation", {"id": "R1", "statement_id": "S1", "evidence_id": "E1", "relation": "challenges",
                                   "rationale": "后续材料需要重审", "scope": "合成范围"})
        self.assert_stale(self.check(expected=1), "A1")

    def test_missing_registered_file_reports_loss_and_stale_activity(self):
        self.register("evidence", self.local())
        self.register("activity", self.activity(status="done", inputs=["evidence:E1"]))
        (self.project / "notes/data.txt").unlink()
        report = self.check(expected=1)
        self.assertIn("file_missing", {row["code"] for row in report["findings"]})
        self.assert_stale(report, "A1")

    def test_controlled_and_external_evidence_do_not_require_private_original(self):
        for identifier, location in (("E1", {"kind": "controlled", "reference": "safe-index-01", "access_note": "受限原件由保管者控制；此处未访问"}),
                                     ("E2", {"kind": "external", "locator": "https://example.invalid/material", "access_note": "离线测试，没有执行网络请求"})):
            self.register("evidence", {"id": identifier, "type": "restricted-index", "description": "安全合成索引",
                                       "provenance": "合成测试，不含个人身份", "location": location})
        report = self.check()
        self.assertTrue(report["passed"])
        self.assertEqual({row["record"] for row in report["warnings"]}, {"evidence:E1", "evidence:E2"})
        self.assertEqual(report["governance_approval"], "not-assessed")

    def test_support_and_challenge_preserved_without_automatic_truth_assessment(self):
        self.register("statement", self.statement(type="interpretive"))
        self.register("evidence", self.local())
        for identifier, relation in (("R1", "supports"), ("R2", "challenges")):
            self.register("relation", {"id": identifier, "statement_id": "S1", "evidence_id": "E1", "relation": relation,
                                       "rationale": "同一材料容许不同解释", "scope": "限定语境"})
        before = snapshot(self.project)
        report = self.check()
        self.assertEqual(report["scientific_validity"], "not-assessed")
        self.assertEqual(self.registry()["records"]["statements"]["S1"]["data"], self.statement(type="interpretive"))
        self.assertEqual({r["data"]["relation"] for r in self.registry()["records"]["relations"].values()}, {"supports", "challenges"})
        self.assertEqual(snapshot(self.project), before)

    def test_open_question_does_not_require_proof_or_evidence(self):
        question = self.statement(type="question", text="下一步应比较哪种解释？")
        self.register("statement", question)
        self.assertTrue(self.check()["passed"])
        self.assertEqual(self.registry()["records"]["statements"]["S1"]["data"], question)

    def test_read_commands_do_not_touch_hashes_mtimes_or_create_lock(self):
        self.register("statement", self.statement(type="question"))
        lock = self.project / ".research/write.lock"
        lock.unlink()
        before = snapshot(self.project)
        for command in ("check", "status", "resume"):
            report = self.invoke(command, "--root", self.project)
            self.assertTrue(report["read_only"])
            self.assertEqual(snapshot(self.project), before)
        proc = subprocess.run([sys.executable, "-X", "utf8", "-I", "-B", str(CLI), "resume", "--root", str(self.project), "--format", "markdown"],
                              capture_output=True, text=True, encoding='utf-8', timeout=20)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(proc.stdout.startswith("# Research recovery"))
        self.assertEqual(snapshot(self.project), before)

    def test_failed_and_skipped_are_preserved_with_reasons(self):
        for identifier, status in (("A1", "failed"), ("A2", "skipped")):
            self.no_mutation("activity", self.activity(identifier, status=status))
            self.register("activity", self.activity(identifier, status=status, note="保留失败或跳过的实际理由"))
        report = self.invoke("resume", "--root", self.project)
        self.assertEqual({row["effective_status"] for row in report["activities"]}, {"failed", "skipped"})
        self.assertEqual(self.registry()["records"]["activities"]["A1"]["data"]["note"], "保留失败或跳过的实际理由")

    def test_done_activity_cannot_skip_incomplete_dependency(self):
        self.register("activity", self.activity())
        self.no_mutation("activity", self.activity("A2", status="done", depends_on=["A1"]))

    def test_checkpoint_recovers_exact_next_action_in_new_process(self):
        self.register("activity", self.activity())
        action = "比较版本甲与乙的范围，再登记反例；不声称已完成。"
        self.invoke("checkpoint", "--root", self.project, "--next-action", action, "--activity", "A1", "--note", "合成任务中断位置")
        before = snapshot(self.project)
        resumed = self.invoke("resume", "--root", self.project)
        self.assertEqual(resumed["next_action"], action)
        self.assertEqual(resumed["cursor"]["activity_id"], "A1")
        self.assertFalse(resumed["needs_review"])
        self.assertEqual(resumed["checkpoint"]["status"], "current")
        self.assertEqual(snapshot(self.project), before)

    def test_checkpoint_detects_configuration_records_and_files_changes(self):
        self.register("statement", self.statement())
        self.register("evidence", self.local())
        self.invoke("checkpoint", "--root", self.project, "--next-action", "检查变化")
        config_path = self.project / "project.json"
        config = json.loads(config_path.read_text(encoding='utf-8'))
        config["title"] = "修订后的合成问题"
        config_path.write_text(json.dumps(config, ensure_ascii=False), encoding="utf-8")
        self.register("statement", self.statement("S2"))
        (self.project / "notes/data.txt").write_text("different synthetic data", encoding='utf-8')
        before = snapshot(self.project)
        report = self.invoke("resume", "--root", self.project, expected=1)
        self.assertTrue(report["needs_review"])
        self.assertEqual(set(report["checkpoint"]["changed"]), {"project-config", "registered-records", "local-files"})
        self.assertEqual(snapshot(self.project), before)

    def test_checkpoint_invalid_activity_and_blank_action_do_not_write(self):
        before = snapshot(self.project)
        for arguments in (("--next-action", " "), ("--next-action", "继续", "--activity", "missing")):
            self.invoke("checkpoint", "--root", self.project, *arguments, expected=2)
            self.assertEqual(snapshot(self.project), before)

    def test_strict_json_duplicate_keys_nonfinite_values_and_malformed_input(self):
        payloads = ['{"id":"S1","id":"S2"}',
                    '{"id":"S1","text":"test","type":"question","scope":"test","extensions":{"n":NaN}}',
                    '{"id":']
        for text in payloads:
            path = self.inputs / "invalid.json"
            path.write_text(text, encoding='utf-8')
            before = snapshot(self.project)
            self.invoke("register", "--root", self.project, "--kind", "statement", "--file", path, expected=2)
            self.assertEqual(snapshot(self.project), before)

    def test_unknown_schema_and_corrupt_state_fail_without_repairing_or_overwriting(self):
        original = (self.project / "records/registry.json").read_bytes()
        for target_name in ("project.json", "records/registry.json"):
            path = self.project / target_name
            good = path.read_bytes()
            data = json.loads(good)
            data["schema_version"] = "999.0"
            for malformed in (json.dumps(data).encode(), b'{"schema_version":"0.1","schema_version":"999.0"}', b'{"x": NaN}', b'{'):
                path.write_bytes(malformed)
                before = snapshot(self.project)
                for command in ("check", "status", "resume"):
                    self.invoke(command, "--root", self.project, expected=2)
                    self.assertEqual(snapshot(self.project), before)
                self.register("statement", self.statement(), expected=2)
                self.assertEqual(snapshot(self.project), before)
            path.write_bytes(good)
        self.assertEqual((self.project / "records/registry.json").read_bytes(), original)

    def test_artifact_changes_are_fingerprinted_and_bound(self):
        self.local(filename="artifacts/output.txt")
        self.register("artifact", {"id": "F1", "type": "note", "description": "合成产物", "path": "artifacts/output.txt"})
        self.register("activity", self.activity(status="done", outputs=["artifact:F1"]))
        (self.project / "artifacts/output.txt").write_text("changed artifact", encoding='utf-8')
        report = self.check(expected=1)
        self.assert_stale(report, "A1")
        self.assertTrue(any(row.get("record") == "artifact:F1" and row["code"] == "file_changed" for row in report["findings"]))

    def test_two_writers_do_not_lose_successful_registrations(self):
        commands = []
        for identifier in ("S1", "S2"):
            path = self.inputs / (identifier + ".json")
            path.write_text(json.dumps(self.statement(identifier)), encoding='utf-8')
            commands.append([sys.executable, "-X", "utf8", "-I", "-B", str(CLI), "register", "--root", str(self.project), "--kind", "statement", "--file", str(path)])
        procs = [subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8') for command in commands]
        retry = []
        successful = set()
        for identifier, command, proc in zip(("S1", "S2"), commands, procs):
            stdout, stderr = proc.communicate(timeout=20)
            self.assertEqual(stderr, "")
            result = json.loads(stdout)
            if proc.returncode == 0:
                self.assertTrue(result["registered"])
                successful.add(identifier)
            else:
                self.assertEqual(proc.returncode, 2, (stdout, stderr))
                self.assertEqual([error["code"] for error in result["errors"]], ["project_busy"])
                retry.append(command)
        self.assertTrue(successful)
        self.assertEqual(set(self.registry()["records"]["statements"]), successful)
        for command in retry:
            result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', timeout=20)
            self.assertEqual(result.returncode, 0, (result.stdout, result.stderr))
            self.assertTrue(json.loads(result.stdout)["registered"])
        self.assertEqual(set(self.registry()["records"]["statements"]), {"S1", "S2"})
        self.assertEqual(self.registry()["revision"], 2)

    def test_relocated_repository_and_project_run_without_personal_environment(self):
        self.register("evidence", self.local())
        self.register("activity", self.activity(status="done", inputs=["evidence:E1"]))
        self.invoke("checkpoint", "--root", self.project, "--next-action", "继续合成验证")
        moved_repository = self.base / "independent distribution"
        moved_repository.mkdir()
        for directory in ("core", "tools", "design"):
            shutil.copytree(REPOSITORY / directory, moved_repository / directory, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        moved_project = self.base / "relocated 项目"
        shutil.move(str(self.project), moved_project)
        empty_home = self.base / "empty-home"
        empty_home.mkdir()
        env = {key: value for key, value in os.environ.items() if key.upper() in ("PATH", "SYSTEMROOT", "WINDIR", "LANG", "LC_ALL", "TMPDIR", "TMP", "TEMP")}
        env["HOME"] = env["USERPROFILE"] = str(empty_home)
        before = snapshot(moved_project)
        report = self.invoke("resume", "--root", moved_project, cli=moved_repository / "tools/research.py", env=env)
        self.assertEqual(report["checkpoint"]["status"], "current")
        self.assertEqual(report["next_action"], "继续合成验证")
        self.assertEqual(snapshot(moved_project), before)
        self.assertFalse(any(empty_home.iterdir()))

    def test_show_full_envelope_and_version_summaries_without_lock_or_mutation(self):
        self.register("statement", self.statement())
        self.register("evidence", self.local())
        (self.project / ".research/write.lock").unlink()
        (self.project / ".research").rmdir()
        before = snapshot(self.project)
        report = self.invoke("show", "--root", self.project, "--kind", "evidence", "--id", "E1")
        expected = self.registry()["records"]["evidence"]["E1"]
        self.assertEqual(report["envelope"], expected)
        self.assertEqual(set(report["envelope"]), {"version", "registered_at", "bindings", "data"})
        self.assertTrue(report["read_only"])
        self.assertEqual(report["scientific_validity"], "not-assessed")
        summary = self.invoke("show", "--root", self.project, "--kind", "statement")
        self.assertEqual(summary["records"], [{"id": "S1", "version": 1}])
        all_records = self.invoke("show", "--root", self.project)["records"]
        self.assertEqual(len(all_records), 8)
        self.assertEqual(all_records["source"], [])
        self.assertEqual(snapshot(self.project), before)

    def test_show_missing_reference_and_id_without_kind_fail_read_only(self):
        before = snapshot(self.project)
        missing = self.invoke("show", "--root", self.project, "--kind", "statement", "--id", "S-missing", expected=2)
        self.assertEqual(missing["errors"][0]["code"], "missing_reference")
        invalid = self.invoke("show", "--root", self.project, "--id", "S1", expected=2)
        self.assertEqual(invalid["errors"][0]["code"], "arguments")
        self.assertEqual(snapshot(self.project), before)

    def test_show_rejects_a_metadata_snapshot_that_changes_during_query(self):
        from core.project import show
        from core.storage import CoreError, ProjectFiles
        original = ProjectFiles.read
        calls = 0
        def changing_read(files, relative):
            nonlocal calls
            result = original(files, relative)
            if relative == "records/registry.json":
                calls += 1
                if calls == 2:
                    return result + b" "
            return result
        before = snapshot(self.project)
        with mock.patch.object(ProjectFiles, "read", changing_read):
            with self.assertRaises(CoreError) as raised:
                show(self.project)
        self.assertEqual(raised.exception.code, "concurrent_change")
        self.assertEqual(snapshot(self.project), before)

    def test_register_stdin_supports_versioned_replacement(self):
        first = self.invoke("register", "--root", self.project, "--kind", "statement", "--file", "-",
                            input_text=json.dumps(self.statement(), ensure_ascii=False))
        self.assertEqual(first["version"], 1)
        changed = self.statement(text="已人工修订的有界表述")
        second = self.invoke("register", "--root", self.project, "--kind", "statement", "--file", "-",
                             "--replace", "--expected-version", "1",
                             input_text=json.dumps(changed, ensure_ascii=False))
        self.assertEqual(second["version"], 2)
        self.assertEqual(self.registry()["records"]["statements"]["S1"]["data"], changed)

    def test_stdin_rejects_duplicate_keys_nonfinite_and_invalid_utf8_without_writes(self):
        before = snapshot(self.project)
        for raw in (b'{"id":"S1","id":"S2"}', b'{"id":NaN}', b'\xff'):
            result = subprocess.run([sys.executable, "-X", "utf8", "-I", "-B", str(CLI), "register",
                                     "--root", str(self.project), "--kind", "statement", "--file", "-"],
                                    input=raw, capture_output=True, timeout=20)
            self.assertEqual(result.returncode, 2, result.stdout)
            self.assertEqual(result.stderr, b"")
            self.assertEqual(json.loads(result.stdout)["errors"][0]["code"], "invalid_json")
            self.assertEqual(snapshot(self.project), before)

    def test_stdin_enforces_the_exact_eight_mib_byte_limit(self):
        from core.storage import JSON_LIMIT
        raw = json.dumps(self.statement(), ensure_ascii=False)
        padded = raw + " " * (JSON_LIMIT - len(raw.encode("utf-8")))
        self.invoke("register", "--root", self.project, "--kind", "statement", "--file", "-", input_text=padded)
        before = snapshot(self.project)
        too_large = self.invoke("register", "--root", self.project, "--kind", "statement", "--file", "-",
                                input_text=padded + " ", expected=2)
        self.assertEqual(too_large["errors"][0]["code"], "json_too_large")
        self.assertEqual(snapshot(self.project), before)

    def test_ordered_batch_binds_prior_entries_and_commits_each_record_version(self):
        evidence = self.local()
        evidence["source_ids"] = ["SRC1"]
        operations = [
            {"kind": "source", "record": self.source()},
            {"kind": "statement", "record": self.statement()},
            {"kind": "evidence", "record": evidence},
            {"kind": "relation", "record": {"id": "R1", "statement_id": "S1", "evidence_id": "E1",
                                              "relation": "qualifies", "rationale": "有限观察", "scope": "合成材料"}},
            {"kind": "activity", "record": self.activity(status="done", inputs=["statement:S1", "evidence:E1"])},
        ]
        path = self.inputs / "batch.json"
        path.write_text(json.dumps(operations, ensure_ascii=False), encoding='utf-8')
        result = self.invoke("register-batch", "--root", self.project, "--file", path)
        self.assertEqual(result["registered_count"], 5)
        self.assertEqual([entry["revision"] for entry in result["records"]], [1, 2, 3, 4, 5])
        self.assertEqual(self.registry()["revision"], 5)
        self.assertEqual(len(self.registry()["history"]), 5)
        self.assertEqual(self.check()["activities"][0]["effective_status"], "done")

    def test_batch_uses_one_real_lock_and_one_atomic_registry_write(self):
        from core.project import register_batch
        from core.storage import ProjectFiles
        original_lock, original_write = ProjectFiles.lock, ProjectFiles.write
        events = []
        @contextmanager
        def counted_lock(files):
            events.append("lock")
            with original_lock(files):
                yield
        def counted_write(files, relative, data):
            events.append(relative)
            return original_write(files, relative, data)
        with mock.patch.object(ProjectFiles, "lock", counted_lock), mock.patch.object(ProjectFiles, "write", counted_write):
            register_batch(self.project, [{"kind": "statement", "record": self.statement("S1")},
                                         {"kind": "statement", "record": self.statement("S2", depends_on=["S1"])}])
        self.assertEqual(events, ["lock", "records/registry.json"])
        self.assertEqual(set(self.registry()["records"]["statements"]), {"S1", "S2"})

    def test_batch_late_failures_roll_back_all_earlier_registry_changes(self):
        self.register("statement", self.statement("EXISTING"))
        failing_operations = [
            ({"kind": "statement", "record": self.statement("S2", depends_on=["MISSING"])}, "invalid_registration"),
            ({"kind": "evidence", "record": {"id": "E1", "type": "test", "description": "missing",
              "provenance": "synthetic", "location": {"kind": "local", "path": "absent.txt"}}}, "file_missing"),
            ({"kind": "statement", "record": self.statement("EXISTING"), "replace": True, "expected_version": 99}, "version_conflict"),
        ]
        for operation, error in failing_operations:
            operations = [{"kind": "statement", "record": self.statement("S1")}, operation]
            before = snapshot(self.project)
            result = self.invoke("register-batch", "--root", self.project, "--file", "-",
                                 input_text=json.dumps(operations), expected=2)
            self.assertEqual(result["errors"][0]["code"], error)
            self.assertEqual(snapshot(self.project), before)

    def test_batch_can_replace_sequential_versions_and_preserves_previous_envelopes(self):
        first, second, third = self.statement(), self.statement(text="第二版"), self.statement(text="第三版")
        operations = [{"kind": "statement", "record": first},
                      {"kind": "statement", "record": second, "replace": True, "expected_version": 1},
                      {"kind": "statement", "record": third, "replace": True, "expected_version": 2}]
        self.invoke("register-batch", "--root", self.project, "--file", "-", input_text=json.dumps(operations))
        registry = self.registry()
        self.assertEqual(registry["records"]["statements"]["S1"]["version"], 3)
        self.assertEqual(registry["history"][1]["previous"]["data"], first)
        self.assertEqual(registry["history"][2]["previous"]["data"], second)

    def test_batch_rejects_malformed_operations_and_duplicate_stdin_keys(self):
        good = {"kind": "statement", "record": self.statement()}
        invalid = [[], {}, [1], [{**good, "unknown": True}], [{**good, "kind": ["statement"]}],
                   [{**good, "replace": "false"}], [{**good, "expected_version": True}],
                   [{**good, "expected_version": -1}]]
        for operations in invalid:
            before = snapshot(self.project)
            self.invoke("register-batch", "--root", self.project, "--file", "-",
                        input_text=json.dumps(operations), expected=2)
            self.assertEqual(snapshot(self.project), before)
        before = snapshot(self.project)
        report = self.invoke("register-batch", "--root", self.project, "--file", "-",
                             input_text='[{"kind":"source","kind":"statement","record":{}}]', expected=2)
        self.assertEqual(report["errors"][0]["code"], "invalid_json")
        self.assertEqual(snapshot(self.project), before)

    def test_configure_updates_supported_fields_and_stales_only_configuration_checkpoint(self):
        self.invoke("checkpoint", "--root", self.project, "--next-action", "人工复核方法选择")
        registry_bytes = (self.project / "records/registry.json").read_bytes()
        initial = json.loads((self.project / "project.json").read_text(encoding='utf-8'))
        report = self.invoke("configure", "--root", self.project, "--add-discipline", "engineering",
                             "--add-method", "computational", "--mode", "reproducible",
                             "--venue", "Example journal, policy not assessed",
                             "--governance-applicability", "applicable",
                             "--add-governance-requirement", "Verify permission before accessing restricted material")
        self.assertTrue(report["configured"])
        config = json.loads((self.project / "project.json").read_text(encoding='utf-8'))
        self.assertEqual(config["project_id"], initial["project_id"])
        self.assertEqual(config["title"], initial["title"])
        self.assertEqual(config["workflow_mode"], "reproducible")
        self.assertIn("engineering", config["disciplines"])
        self.assertIn("computational", config["methods"])
        self.assertEqual(config["governance"]["applicability"], "applicable")
        self.assertEqual(report["governance_approval"], "not-assessed")
        self.assertEqual(report["venue_compliance"], "not-assessed")
        self.assertEqual((self.project / "records/registry.json").read_bytes(), registry_bytes)
        stale = self.invoke("resume", "--root", self.project, expected=1)
        self.assertEqual(stale["checkpoint"]["changed"], ["project-config"])
        self.assertEqual(stale["revision"], report["registry_revision"])

    def test_configure_rejects_invalid_changes_without_mutating_configuration_or_registry(self):
        for options in (("--add-discipline", "not-a-discipline"), ("--add-method", "unknown"),
                        ("--venue", " "), ("--add-governance-requirement", " "),
                        ("--governance-applicability", "approved")):
            before = snapshot(self.project)
            self.invoke("configure", "--root", self.project, *options, expected=2)
            self.assertEqual(snapshot(self.project), before)

    def test_configure_noop_is_idempotent_and_preserves_all_project_mtimes(self):
        (self.project / ".research/write.lock").unlink()
        (self.project / ".research").rmdir()
        before = snapshot(self.project)
        for options in ((), ("--add-method", "formal-theory", "--add-discipline", "natural-sciences", "--mode", "light")):
            report = self.invoke("configure", "--root", self.project, *options)
            self.assertFalse(report["configured"])
            self.assertEqual(snapshot(self.project), before)

    def test_configure_respects_the_existing_writer_lock(self):
        from core.storage import ProjectFiles
        with ProjectFiles(self.project) as files, files.lock():
            before = snapshot(self.project)
            report = self.invoke("configure", "--root", self.project, "--mode", "structured", expected=2)
            self.assertEqual(report["errors"][0]["code"], "project_busy")
            self.assertEqual(snapshot(self.project), before)

    def test_markdown_recovery_includes_revision_checkpoint_and_active_activity_title(self):
        self.register("activity", self.activity(status="in-progress"))
        def markdown(expected):
            before = snapshot(self.project)
            result = subprocess.run([sys.executable, "-X", "utf8", "-I", "-B", str(CLI), "resume", "--root", str(self.project),
                                     "--format", "markdown"], text=True, encoding='utf-8', capture_output=True, timeout=20)
            self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
            self.assertEqual(result.stderr, "")
            self.assertEqual(snapshot(self.project), before)
            return result.stdout
        output = markdown(0)
        self.assertIn("Revision: 1", output)
        self.assertIn("Checkpoint status: not-recorded", output)
        self.assertIn("A1", output)
        self.assertIn("比较合成材料", output)
        self.assertIn("in-progress", output)
        self.invoke("checkpoint", "--root", self.project, "--next-action", "继续人工核对")
        output = markdown(0)
        self.assertIn("Revision: 2", output)
        self.assertIn("Checkpoint status: current", output)

    def test_markdown_recovery_lists_drift_missing_files_and_stale_reasons(self):
        self.register("evidence", self.local())
        self.register("activity", self.activity(status="done", inputs=["evidence:E1"]))
        self.invoke("checkpoint", "--root", self.project, "--next-action", "审查受影响输入")
        material = self.project / "notes/data.txt"
        for missing, code in ((False, "file_changed"), (True, "file_missing")):
            if missing:
                material.unlink()
            else:
                material.write_text("intentionally changed synthetic material", encoding='utf-8')
            before = snapshot(self.project)
            result = subprocess.run([sys.executable, "-X", "utf8", "-I", "-B", str(CLI), "resume", "--root", str(self.project),
                                     "--format", "markdown"], text=True, encoding='utf-8', capture_output=True, timeout=20)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            for expected in (code, "evidence:E1", "notes/data.txt", "activity_stale", "checkpoint_stale", "A1", "比较合成材料", "stale", "Needs review: true"):
                self.assertIn(expected, result.stdout)
            self.assertIn("Bound records or local files changed" if not missing else "A bound local file is missing", result.stdout)
            self.assertEqual(snapshot(self.project), before)


if __name__ == "__main__":
    unittest.main()
