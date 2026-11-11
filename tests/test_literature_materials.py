"""Read-only inventories preserve original bytes and report partial access honestly."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile


SCRIPT = Path(__file__).resolve().parents[1] / "skills/rw-literature/scripts/inspect_materials.py"
spec = importlib.util.spec_from_file_location("inspect_materials", SCRIPT)
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)


class LiteratureMaterialsTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def test_unicode_duplicates_and_originals_remain_unchanged(self):
        (self.root / "例文").mkdir()
        (self.root / "例文/论文.pdf").write_bytes(b"%PDF original")
        (self.root / "another.pdf").write_bytes(b"%PDF original")
        (self.root / "references.bib").write_text("@article{kept-key, title={Real title}}")
        before = {str(p): (p.read_bytes(), p.stat().st_mtime_ns) for p in self.root.rglob("*") if p.is_file()}
        report = tool.inspect(self.root)
        self.assertTrue(report["passed"])
        self.assertFalse(report["truncated"])
        self.assertEqual(len(report["files"]), 3)
        self.assertEqual(set(report["duplicates"][0]["paths"]), {"another.pdf", "例文/论文.pdf"})
        self.assertTrue(all(f["reading_status"] == "not-read" and f["citation_support"] == "not-checked" for f in report["files"]))
        self.assertEqual(before, {str(p): (p.read_bytes(), p.stat().st_mtime_ns) for p in self.root.rglob("*") if p.is_file()})

    def test_limits_never_emit_partial_hashes(self):
        (self.root / "large.pdf").write_bytes(b"12345")
        report = tool.inspect(self.root, max_file_bytes=4)
        self.assertTrue(report["truncated"])
        self.assertIsNone(report["files"][0]["sha256"])
        self.assertEqual(report["content_bytes_hashed"], 0)
        (self.root / "second.ris").write_bytes(b"RIS")
        self.assertTrue(tool.inspect(self.root, max_files=1)["truncated"])
        self.assertTrue(tool.inspect(self.root, max_entries=1)["truncated"])
        (self.root / "nested").mkdir()
        (self.root / "nested/deep").mkdir()
        self.assertTrue(tool.inspect(self.root, max_depth=1)["truncated"])

    def test_zip_member_identity_and_unsafe_members_without_extraction(self):
        archive = self.root / "supplied.zip"
        with zipfile.ZipFile(archive, "w") as z:
            z.writestr("例文/paper.pdf", b"source bytes")
            z.writestr("../escape.pdf", b"outside")
            z.writestr("C:/escape.pdf", b"outside")
            link = zipfile.ZipInfo("linked.pdf")
            link.create_system = 3
            link.external_attr = (stat.S_IFLNK | 0o777) << 16
            z.writestr(link, "somewhere.pdf")
        raw = archive.read_bytes()
        report = tool.inspect(archive)
        self.assertEqual(report["input"]["sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual([f["path"] for f in report["files"]], ["例文/paper.pdf"])
        self.assertEqual(report["files"][0]["sha256"], hashlib.sha256(b"source bytes").hexdigest())
        self.assertEqual(len(report["skipped"]), 3)
        self.assertEqual(list(self.root.iterdir()), [archive])
        self.assertEqual(archive.read_bytes(), raw)

    def test_corrupt_zip_and_duplicate_name_are_failures(self):
        archive = self.root / "bad.zip"
        archive.write_bytes(b"not a zip")
        process = subprocess.run([sys.executable, "-B", str(SCRIPT), str(archive)], capture_output=True)
        self.assertEqual(process.returncode, 2)
        self.assertFalse(json.loads(process.stdout)["passed"])
        with zipfile.ZipFile(archive, "w") as z:
            z.writestr("paper.pdf", b"v1")
            with self.assertWarns(UserWarning):
                z.writestr("paper.pdf", b"v2")
        self.assertFalse(tool.inspect(archive)["passed"])

    def test_input_links_are_rejected_and_nested_links_skipped(self):
        from platform_support import symlink_or_skip
        outside = self.root / "outside.pdf"
        outside.write_bytes(b"original")
        folder = self.root / "folder"
        folder.mkdir()
        symlink_or_skip(self, folder / "linked.pdf", outside)
        report = tool.inspect(folder)
        self.assertEqual(report["files"], [])
        self.assertEqual(report["skipped"][0]["reason"], "symbolic-link-or-reparse-point")
        with self.assertRaisesRegex(ValueError, "symbolic link"):
            tool.inspect(folder / "linked.pdf")

    def test_corrupt_member_keeps_its_total_budget_reservation(self):
        archive = self.root / "crc.zip"
        with zipfile.ZipFile(archive, "w") as z:
            z.writestr("first.pdf", b"first-unique-payload")
            z.writestr("second.pdf", b"second-payload")
        original = archive.read_bytes()
        offset = original.index(b"first-unique-payload")
        archive.write_bytes(original[:offset] + b"X" + original[offset+1:])
        budget = archive.stat().st_size + len(b"first-unique-payload") + len(b"second-payload") - 1
        report = tool.inspect(archive, max_total_bytes=budget)
        self.assertFalse(report["passed"])
        self.assertTrue(report["truncated"])
        self.assertEqual([f["status"] for f in report["files"]],
                         ["unreadable-or-changed", "byte-limit"])
        self.assertTrue(all(f["sha256"] is None for f in report["files"]))

    def test_archive_directory_limits_precede_member_allocation(self):
        archive = self.root / "many.zip"
        with zipfile.ZipFile(archive, "w") as z:
            for number in range(3):
                z.writestr(f"{number}.pdf", b"article")
        with patch.object(tool.zipfile, "ZipFile", side_effect=AssertionError("Metadata objects allocated")):
            report = tool.inspect(archive, max_entries=2)
            self.assertTrue(report["passed"])
            self.assertTrue(report["truncated"])
            self.assertEqual(report["input"]["archive_declared_members"], 3)
            self.assertEqual(report["files"], [])
            with patch.object(tool, "ZIP_METADATA_LIMIT", 1):
                self.assertTrue(tool.inspect(archive)["truncated"])

    def test_single_file_cli_utf8_and_budget_validation(self):
        source = self.root / "书目.bib"
        source.write_bytes(b"bibliography")
        report = tool.inspect(source)
        self.assertEqual(report["input"]["kind"], "file")
        self.assertEqual(report["files"][0]["path"], source.name)
        process = subprocess.run([sys.executable, "-B", str(SCRIPT), str(source)], capture_output=True,
                                 env={**os.environ, "PYTHONIOENCODING": "ascii"})
        self.assertEqual(process.returncode, 0)
        self.assertEqual(json.loads(process.stdout.decode("utf-8"))["files"][0]["path"], source.name)
        with self.assertRaises(ValueError):
            tool.inspect(source, max_total_bytes=0)


if __name__ == "__main__":
    unittest.main()
