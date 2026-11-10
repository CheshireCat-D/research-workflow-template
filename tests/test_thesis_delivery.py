import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile

SCRIPT = Path(__file__).resolve().parents[1] / "skills/rw-writing/scripts/check_thesis_delivery.py"
spec = importlib.util.spec_from_file_location("thesis_delivery", SCRIPT)
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)


class ThesisDeliveryTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name).resolve()
        self.manifest = self.root / "thesis.json"
        self.docx = self.root / "thesis.docx"
        self.pdf = self.root / "thesis.pdf"
        self.pdf.write_bytes(b"%PDF-1.7\nTest PDF placeholder; text extraction is stubbed")
        (self.root / "rules.txt").write_text("Synthetic requirement: both abstracts", encoding="utf-8")
        (self.root / "page-review.md").write_text("Pages 1 and 2 inspected", encoding="utf-8")
        self.cn = "本例的差值为四。"
        self.en = "The difference was four."
        with ZipFile(self.docx, "w") as archive:
            archive.writestr("[Content_Types].xml", f'<Types xmlns="{tool.CONTENT_TYPES[1:-1]}"><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>')
            archive.writestr("word/document.xml", f'<w:document xmlns:w="{tool.WORD[1:-1]}"><w:body><w:p><w:pPr><w:pStyle w:val="Abstract"/></w:pPr><w:r><w:t>{self.cn}</w:t></w:r></w:p><w:p><w:r><w:t>{self.en}</w:t></w:r></w:p></w:body></w:document>')
        self.config = {
            "institution": "Test", "degree": "Test master's programme",
            "basis": {"file": "rules.txt", "locator": "Section 2"},
            "docx": self.docx.name, "pdf": self.pdf.name,
            "anchors": [{"label": "摘要", "text": self.cn, "style": "Abstract"},
                        {"label": "Abstract", "text": self.en}],
            "materials": [{"file": "optional.pdf", "use": "supplement", "applies": False, "basis": "Section 3"}],
            "visual_review": {"note": "page-review.md", "renderer": "Test fixture",
                              "docx_sha256": tool.sha(self.docx), "pdf_sha256": tool.sha(self.pdf),
                              "pages": "1-2", "outcome": "clear"},
        }

    def run_check(self, pages):
        self.manifest.write_text(json.dumps(self.config), encoding="utf-8")
        with patch.object(tool, "pdf_pages", return_value=(pages, "test extractor")):
            return tool.check(self.manifest)

    def test_configured_parity_and_style(self):
        report, code = self.run_check([self.cn, self.en])
        self.assertEqual(code, 0)
        checks = {check["name"]: check for check in report["checks"]}
        self.assertEqual(checks["Abstract/pdf"]["detail"]["matched_pages"], [2])
        self.assertEqual(checks["optional.pdf"]["status"], "not_applicable")

    def test_real_content_mismatch_and_required_attachment(self):
        self.config["materials"][0]["applies"] = True
        report, code = self.run_check([self.cn, "The difference was five."])
        self.assertEqual(code, 1)
        self.assertEqual({c["name"] for c in report["checks"] if c["status"] == "mismatch"},
                         {"Abstract/pdf", "optional.pdf"})

    def test_pending_for_new_version_partial_record_and_unknown_condition(self):
        for change in ({"docx_sha256": "old"}, {"pages": "1"}):
            with self.subTest(change=change):
                initial = self.config["visual_review"].copy()
                self.config["visual_review"].update(change)
                self.assertEqual(self.run_check([self.cn, self.en])[1], 2)
                self.config["visual_review"] = initial
        self.config["materials"][0]["applies"] = None
        self.assertEqual(self.run_check([self.cn, self.en])[1], 2)
        self.config["materials"][0]["applies"] = False
        self.assertEqual(self.run_check(None)[1], 2)

    def test_roles_and_project_paths(self):
        self.config["anchors"][1]["label"] = self.config["anchors"][0]["label"]
        with self.assertRaisesRegex(ValueError, "Duplicate anchor"):
            self.run_check([self.cn, self.en])
        self.config["docx"] = "../foreign.docx"
        with self.assertRaisesRegex(ValueError, "project-relative"):
            self.run_check(None)

    def test_school_outline_order(self):
        self.config["section_order"] = [self.en, self.cn]
        self.assertEqual(self.run_check([self.cn, self.en])[1], 1)
        self.config["section_order"].reverse()
        self.assertEqual(self.run_check([self.cn, self.en])[1], 0)

    def test_numeric_repeats_ranges_and_source_states(self):
        config = {"body_heading": "Intro", "reference_heading": "Works",
                  "sources": [{"number": 1, "origin": "Paper A", "location": "p. 3",
                               "status": "metadata_only"}]}
        body = [(p, None) for p in ("Intro", "Result [1–2]. Again [1].", "Works",
                                    "[1] Paper A", "[2] Paper B")]
        entries = {}
        tool.check_numbered(config, body, lambda k, s, d: entries.update({k: (s, d)}))
        self.assertEqual(entries["citations/body"][0], "pass")
        self.assertEqual(entries["source/1"][0], "pending")
        self.assertEqual(entries["citations/ledger"][1]["unmapped_entries"], [2])
        body[1] = ("Uses [2] then [1] and [3].", None)
        tool.check_numbered(config, body, lambda k, s, d: entries.update({k: (s, d)}))
        self.assertEqual(entries["citations/body"], ("mismatch", {
            "first_use": [2, 1, 3], "missing_references": [3], "unseen_in_body": [],
            "invalid_tokens": []}))
        body.append(("Works", None))
        tool.check_numbered(config, body, lambda k, s, d: entries.update({k: (s, d)}))
        self.assertEqual(entries["citations/scope"][0], "pending")

    def test_invalid_review_page_range(self):
        self.config["visual_review"]["pages"] = "1-300"
        with self.assertRaisesRegex(ValueError, "outside the current PDF"):
            self.run_check([self.cn, self.en])
