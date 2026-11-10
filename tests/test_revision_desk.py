"""Exercise real project registration, portable review, file checks and draft packaging."""
import hashlib
from html.parser import HTMLParser
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from urllib.parse import unquote, urlsplit
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
script = ROOT / "skills/rw-review/scripts/review_desk.py"
spec = importlib.util.spec_from_file_location("review_desk", script)
desk = importlib.util.module_from_spec(spec)
spec.loader.exec_module(desk)


class RevisionDeskTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.base = Path(tmp.name)
        self.root = self.base / "project"
        desk.project.initialize(self.root, "Ozone study")
        self.register("Old", "old.svg", b"<svg>old</svg>")
        self.register("New", "new.svg", b"<svg>new</svg>")
        self.register("Brief", "brief.md", b"Revised brief")
        self.plan = {"id": "D1", "title": "Read <revision>", "candidates": ["artifact:Old", "artifact:New"],
                     "supersedes": {"artifact:New": "artifact:Old"}, "deliverables": ["artifact:Brief"],
                     "checks": [{"label": "Independent reading", "status": "pending"}]}
        self.write_plan()

    def register(self, identifier, path, content, version=None):
        (self.root / path).write_bytes(content)
        desk.project.register(self.root, "artifact", {"id": identifier, "description": identifier,
                              "type": "output", "path": path}, replace=bool(version), expected_version=version)

    def write_plan(self):
        (self.root / "review.json").write_text(json.dumps(self.plan))

    def view(self, root=None):
        return desk.snapshot(root or self.root, "review.json")

    def save(self, token, choice, feedback):
        return desk.save(self.root, "review.json", token, choice, feedback, "test operator")

    def test_native_history_current_choice_and_real_zip(self):
        initial = self.view()
        first = self.save(initial["token"], "request-changes", "Show the observed denominator")
        self.assertTrue(first["checkpoint_saved"])
        self.assertEqual(self.view()["decision_status"], "changes requested")
        with self.assertRaisesRegex(ValueError, "changed"):
            self.save(initial["token"], "artifact:New", "Saw an earlier tab")
        second = self.save(self.view()["token"], "artifact:New", "The revision includes the observed denominator")
        self.assertEqual(second["version"], 2)
        self.assertTrue(self.save(self.view()["token"], "artifact:New",
                                  "The revision includes the observed denominator")["already_saved"])
        relocated = self.base / "relocated"
        shutil.copytree(self.root, relocated)
        view = self.view(relocated)
        self.assertEqual([r["choice"] for r in view["history"]], ["request-changes", "artifact:New"])
        html = desk.html(relocated, view)
        self.assertIn("data:image/svg+xml;base64,", html)
        self.assertIn("Read &lt;revision&gt;", html)
        self.assertNotIn("<form", html)
        output = self.base / "share.zip"
        desk.pack(relocated, "review.json", output)
        with ZipFile(output) as z:
            self.assertEqual(set(z.namelist()), {"index.html", "manifest.json", "files/brief.md", "files/new.svg"})
            manifest = json.loads(z.read("manifest.json"))
            self.assertEqual(manifest["checks"][0]["effective_status"], "pending")
            self.assertEqual(manifest["decision_status"], "selection saved")
            for material in manifest["files"].values():
                self.assertEqual(material["sha256"], hashlib.sha256(z.read(material["member"])).hexdigest())
        with self.assertRaisesRegex(ValueError, "already exists"):
            desk.pack(relocated, "review.json", output)

    def test_unpacked_reader_links_and_optional_feedback(self):
        (self.root / "drafts").mkdir()
        markdown = """# Real results

A **measured difference**. See the [table](../table.csv).

| Group | Value |
| --- | ---: |
| A | 7 |

![Selected](<../图 & %233.svg>)
![Unshipped](unshipped.svg)
![Remote](https://example.org/image.png)

<iframe src="https://example.org/"></iframe>
"""
        self.register("Paper", "drafts/稿件 #2.md", markdown.encode())
        self.register("Note", "plain.txt", b"Two paragraphs.\n\n<em>Literal</em>")
        self.register("Fig3", "图 & #3.svg", b"<svg>selected</svg>")
        self.register("Table", "table.csv", b"x,y")
        self.plan.update(candidates=["artifact:Fig3"], deliverables=["artifact:Table", "artifact:Paper", "artifact:Note"])
        self.write_plan()
        self.save(self.view()["token"], "request-changes", "Private historical remark")
        self.save(self.view()["token"], "artifact:Fig3", "Shareable latest feedback")

        class Links(HTMLParser):
            def __init__(self):
                super().__init__()
                self.hrefs = []
                self.images = []

            def handle_starttag(self, tag, attrs):
                attributes = dict(attrs)
                if tag == "a":
                    self.hrefs.append(attributes["href"])
                elif tag == "img":
                    self.images.append(attributes["src"])

        for publish_feedback in (False, True):
            with self.subTest(include_feedback=publish_feedback):
                target = self.base / f"share-{publish_feedback}.zip"
                folder = self.base / f"reader-{publish_feedback}"
                manifest = desk.pack(self.root, "review.json", target, include_feedback=publish_feedback)
                with ZipFile(target) as archive:
                    archive.extractall(folder)
                index = (folder / manifest["reader"]["member"]).read_bytes()
                self.assertEqual(hashlib.sha256(index).hexdigest(), manifest["reader"]["sha256"])
                ui = Links()
                ui.feed(index.decode())
                self.assertEqual(unquote(ui.hrefs[0]), "files/drafts/稿件 #2.md")
                self.assertEqual([unquote(img) for img in ui.images], ["files/图 & #3.svg"] * 2)
                body = index.decode()
                self.assertIn("<h3>Real results</h3>", body)
                self.assertIn("<strong>measured difference</strong>", body)
                self.assertIn("<td>7</td>", body)
                self.assertIn("Two paragraphs.\n\n&lt;em&gt;Literal&lt;/em&gt;", body)
                self.assertIn("&lt;iframe", body)
                self.assertNotIn("<iframe", body)
                self.assertNotIn("https://example.org/image.png", ui.images)
                self.assertIn("files/table.csv", ui.hrefs)
                for url in ui.hrefs + ui.images:
                    parts = urlsplit(url)
                    self.assertFalse(parts.scheme or parts.netloc or parts.fragment)
                    self.assertTrue((folder / unquote(parts.path)).is_file())
                shareable = index.decode() + (folder / "manifest.json").read_text()
                self.assertNotIn("Private historical remark", shareable)
                self.assertEqual("Shareable latest feedback" in shareable, publish_feedback)
                self.assertEqual("test operator" in shareable, publish_feedback)
                self.assertIn("Independent reading", shareable)

    def test_superseded_candidate_only_previews_and_draft_archive_omits_it(self):
        initial = self.view()
        page = desk.html(self.root, initial, nonce="local")
        self.assertIn("Earlier version", page)
        self.assertNotIn('name="choice" value="artifact:Old"', page)
        with self.assertRaisesRegex(ValueError, "listed candidate"):
            self.save(initial["token"], "artifact:Old", "Restore the old graph")
        share = self.base / "draft.zip"
        desk.pack(self.root, "review.json", share)
        with ZipFile(share) as z:
            self.assertNotIn("files/old.svg", z.namelist())
            self.assertNotIn("files/new.svg", z.namelist())
        self.plan["supersedes"] = {}
        self.write_plan()
        self.save(self.view()["token"], "artifact:Old", "Reinstate this candidate")
        self.plan["supersedes"] = {"artifact:New": "artifact:Old"}
        self.write_plan()
        self.assertNotEqual(self.view()["decision_status"], "selection saved")
        after = self.base / "revised.zip"
        desk.pack(self.root, "review.json", after)
        with ZipFile(after) as z:
            self.assertNotIn("files/old.svg", z.namelist())

    def test_partial_review_check_remains_unverified(self):
        check = {"label": "Inspection", "status": "checked", "evidence": "artifact:Brief"}
        self.plan["checks"] = [check]
        self.write_plan()
        self.assertIn("unverified", self.view()["checks"][0]["effective_status"])
        check["against"] = {"artifact:Brief": hashlib.sha256(b"Revised brief").hexdigest()}
        self.write_plan()
        self.assertIn("unverified", self.view()["checks"][0]["effective_status"])
        check["against"]["artifact:New"] = hashlib.sha256(b"<svg>new</svg>").hexdigest()
        self.write_plan()
        self.assertEqual(self.view()["checks"][0]["effective_status"], "checked (bound files match)")
        self.register("Brief", "brief.md", b"Later edition", version=1)
        self.assertEqual(self.view()["checks"][0]["effective_status"], "needs recheck")

    def test_failed_zip_publish_preserves_destination(self):
        from unittest.mock import patch
        target = self.base / "test.zip"
        with patch.object(desk.os, "link", side_effect=OSError("Volume lacks hard links")):
            with self.assertRaisesRegex(ValueError, "hard-link-capable"):
                desk.pack(self.root, "review.json", target)
        self.assertFalse(target.exists())
        self.assertFalse(list(self.base.glob(".rwt-review-*")))

    def test_changed_file_and_late_qa_revisions(self):
        self.plan["checks"] = [{"label": "Figure inspection", "status": "checked", "evidence": "artifact:Brief",
                                "against": {"artifact:New": hashlib.sha256(b"<svg>new</svg>").hexdigest()}}]
        self.write_plan()
        view = self.view()
        self.save(view["token"], "artifact:New", "Inspected the stated figure")
        (self.root / "new.svg").write_bytes(b"<svg>edited</svg>")
        view = self.view()
        self.assertEqual(view["materials"]["artifact:New"]["state"], "changed")
        self.assertEqual(view["checks"][0]["effective_status"], "needs recheck")
        self.assertIn("changed", view["decision_status"])
        with self.assertRaisesRegex(ValueError, "Changed or missing"):
            self.save(view["token"], "artifact:New", "Cannot accept an unregistered edit")
        with self.assertRaisesRegex(ValueError, "changed or missing"):
            desk.pack(self.root, "review.json", self.base / "stale.zip")
        self.assertFalse((self.base / "stale.zip").exists())
        self.register("New", "new.svg", b"<svg>edited</svg>", version=1)
        self.assertEqual(self.view()["checks"][0]["effective_status"], "needs recheck")
        self.assertEqual(self.view()["materials"]["artifact:New"]["state"], "current")

    def test_old_native_decision_and_bad_plan_cannot_be_overwritten(self):
        desk.project.register(self.root, "decision", {"id": "D1", "choice": "Original", "rationale": "External",
                              "responsible": "investigator", "decided_at": "2026-10-01"})
        with self.assertRaisesRegex(ValueError, "belongs to another record"):
            self.view()
        self.plan["id"] = "D2"
        self.plan["supersedes"]["artifact:Old"] = "artifact:New"
        self.write_plan()
        with self.assertRaisesRegex(ValueError, "Cyclic"):
            self.view()
        self.plan.pop("supersedes")
        self.plan["checks"][0]["status"] = "checked"
        self.write_plan()
        with self.assertRaisesRegex(ValueError, "evidence file"):
            self.view()

    def test_validates_input_again_under_native_lock(self):
        from unittest.mock import patch
        original = desk.project.register

        def intervene(*args, **kwargs):
            (self.root / "old.svg").write_bytes(b"<svg>changed by another process</svg>")
            return original(*args, **kwargs)

        with patch.object(desk.project, "register", side_effect=intervene):
            with self.assertRaisesRegex(ValueError, "Review changed"):
                self.save(self.view()["token"], "artifact:New", "Earlier materials")
        self.assertEqual(self.view()["version"], 0)
