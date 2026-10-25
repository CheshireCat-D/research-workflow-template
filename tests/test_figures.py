"""Behavior of the read-only SVG structure audit, not scientific validation."""
from pathlib import Path
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/rw-figures"
SCRIPT = SKILL / "scripts/audit_svg_schematic.py"
spec = importlib.util.spec_from_file_location("rw_svg_audit", SCRIPT)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def svg(content="<text id='label' x='2' y='20'>Editable</text>", **canvas):
    attributes = {"width": "100mm", "height": "60mm", "viewBox": "0 0 100 60"}
    attributes.update(canvas)
    return ("<svg xmlns='http://www.w3.org/2000/svg' " +
            " ".join(f"{key}='{value}'" for key, value in attributes.items()) + ">" +
            "<title id='title'>Demo</title><desc id='desc'>Synthetic test</desc>" + content + "</svg>").encode()


class SvgAuditTests(unittest.TestCase):
    def codes(self, report):
        return {item["code"] for item in report["findings"]}

    def test_shipped_example_has_native_text_and_resolved_references(self):
        report = audit.audit_svg((SKILL / "assets/synthetic-workflow.svg").read_bytes())
        self.assertEqual(report["status"], "pass", report)
        self.assertGreaterEqual(report["counts"]["native_text_elements"], 3)
        self.assertGreater(report["counts"]["local_references"], 0)
        figure_spec = json.loads((SKILL / "assets/synthetic-figure-spec.json").read_text())
        self.assertTrue(figure_spec["synthetic"])
        identifiers = {element.get("id") for element in audit.ET.fromstring(
            (SKILL / "assets/synthetic-workflow.svg").read_bytes()).iter()}
        for item in figure_spec["nodes"] + figure_spec["edges"]:
            self.assertIn(item["id"], identifiers)

    def test_bad_xml_and_non_svg_are_not_auditable(self):
        for data in (b"<svg>", b"<html/>", b"\xffnot utf8"):
            with self.subTest(data=data):
                report = audit.audit_svg(data)
                self.assertEqual(audit.exit_code(report), 2)

    def test_dtd_and_entities_are_rejected_before_expansion(self):
        data = b'<!DOCTYPE svg [<!ENTITY word "expanded">]><svg>&word;</svg>'
        report = audit.audit_svg(data)
        self.assertEqual(report["status"], "not-auditable")
        self.assertIn("xml.declaration", self.codes(report))
        utf16 = "<!DOCTYPE svg [<!ENTITY word 'expanded'>]><svg>&word;</svg>".encode("utf-16")
        self.assertEqual(audit.exit_code(audit.audit_svg(utf16)), 2)

    def test_canvas_rejects_zero_negative_nonfinite_and_relative_dimensions(self):
        for changes in ({"width": "0mm"}, {"height": "-1px"}, {"width": "1e999mm"},
                        {"width": "100%"}, {"height": "NaNmm"}, {"width": "10"},
                        {"viewBox": "0 0 0 5"}, {"viewBox": "0 0 5 -2"},
                        {"viewBox": "0 0 inf 5"}, {"viewBox": "0 0 1e999 5"},
                        {"viewBox": "0 0 2"}, {"viewBox": "0 0 1_0 10"}):
            with self.subTest(changes=changes):
                self.assertEqual(audit.exit_code(audit.audit_svg(svg(**changes))), 1)

    def test_absolute_units_and_negative_viewbox_origin_are_supported(self):
        for unit in ("px", "pt", "pc", "mm", "cm", "in"):
            with self.subTest(unit=unit):
                report = audit.audit_svg(svg(width="12.5" + unit, height="2e1" + unit,
                                             viewBox="-5,-2,100,60"))
                self.assertEqual(report["status"], "pass", report)

    def test_duplicate_and_empty_ids_are_findings(self):
        content = "<text id='same'>One</text><text id='same'>Two</text>" + "<g id=''/>"
        report = audit.audit_svg(svg(content))
        self.assertEqual(audit.exit_code(report), 1)
        self.assertIn("id.duplicate", self.codes(report))
        self.assertIn("id.empty", self.codes(report))

    def test_local_references_are_resolved_after_full_tree(self):
        report = audit.audit_svg(svg("<use href='#later'/><path style='marker-end:url(\"#tip\")'/><text aria-labelledby='later'>T</text><g id='later'/><marker id='tip'/>"))
        self.assertEqual(report["status"], "pass", report)
        self.assertEqual(report["counts"]["local_references"], 3)
        for content in ("<use href='#missing'/>", "<g style='clip-path:url(#missing)'/>",
                        "<text aria-describedby='missing'>X</text>", "<use href='#'/>"):
            with self.subTest(content=content):
                report = audit.audit_svg(svg("<text>T</text>" + content))
                self.assertIn("reference.dangling", self.codes(report))
                self.assertEqual(audit.exit_code(report), 1)

    def test_active_content_and_nonlocal_resources_fail_without_execution(self):
        cases = ("<script>throw Error('must not run')</script>", "<foreignObject/>",
                 "<g onload='run()'/>", "<image href='https://example.invalid/image.png'/>",
                 "<use href='other.svg#node'/>", "<g style='fill:url(https://example.invalid/x)'/>",
                 "<style>@import 'https://example.invalid/x.css';</style>",
                 "<image href='data:image/svg+xml,active'/>")
        for content in cases:
            with self.subTest(content=content):
                report = audit.audit_svg(svg("<text>T</text>" + content))
                self.assertEqual(audit.exit_code(report), 1, report)

    def test_paths_or_embedded_images_cannot_replace_native_text(self):
        report = audit.audit_svg(svg("<path d='M0 0L10 10'/><image href='#pixels'/><g id='pixels'/>"))
        self.assertEqual(audit.exit_code(report), 1)
        self.assertIn("text.missing", self.codes(report))
        self.assertIn("content.image", self.codes(report))

    def test_non_svg_text_namespace_does_not_count_as_native_svg_text(self):
        for content in ("<x:text xmlns:x='urn:example:non-svg'>Other text</x:text>",
                        "<text xmlns=''>Text outside the SVG namespace</text>"):
            with self.subTest(content=content):
                report = audit.audit_svg(svg(content))
                self.assertEqual(report["counts"]["native_text_elements"], 0)
                self.assertEqual(audit.exit_code(report), 1)

    def test_static_policy_rejects_xml_base_escaped_css_and_dynamic_mutation(self):
        for content in ("<g xml:base='https://example.invalid/'/>",
                        r"<g style='fill:u\72l(https://example.invalid/x)'/>",
                        "<style>@im/**/port 'https://example.invalid/x.css';</style>",
                        "<set attributeName='href' to='https://example.invalid/x'/>"):
            with self.subTest(content=content):
                self.assertEqual(audit.exit_code(audit.audit_svg(svg("<text>T</text>" + content))), 1)

    def test_cli_is_read_only_and_emits_json_for_success_findings_and_read_error(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "figure.svg"
            for data, expected in ((svg(), 0), (svg(width="0mm"), 1), (b"<svg>", 2)):
                path.write_bytes(data)
                before = path.stat()
                run = subprocess.run([sys.executable, str(SCRIPT), str(path)],
                                     capture_output=True, text=True, check=False)
                self.assertEqual(run.returncode, expected, run.stderr)
                self.assertEqual(path.read_bytes(), data)
                self.assertEqual(path.stat().st_mtime_ns, before.st_mtime_ns)
                self.assertEqual(path.stat().st_mode, before.st_mode)
                self.assertIn("status", json.loads(run.stdout))
                self.assertEqual(sorted(p.name for p in Path(directory).iterdir()), ["figure.svg"])
            run = subprocess.run([sys.executable, str(SCRIPT), str(path.with_name("missing.svg"))],
                                 capture_output=True, text=True, check=False)
            self.assertEqual(run.returncode, 2)
            self.assertEqual(json.loads(run.stdout)["status"], "not-auditable")


if __name__ == "__main__":
    unittest.main()
