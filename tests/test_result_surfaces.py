import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


script = Path(__file__).resolve().parents[1] / "skills/rw-figures/scripts/check_result_surfaces.py"
spec = importlib.util.spec_from_file_location("surface_check", script)
surface = importlib.util.module_from_spec(spec)
spec.loader.exec_module(surface)


class SurfaceTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.plan = self.root / "checks.json"
        self.table = self.root / "data.csv"
        self.table.write_text("id,gap,unit\nmain,40.162,ppb\n", encoding="utf-8")
        self.md = self.root / "brief.md"
        self.md.write_text("Primary: +40.16 ppb\n", encoding="utf-8")

    def inspect(self, filename="brief.md", **kwargs):
        check = dict(row="main", file=filename, after="Primary:", expect="{gap:+.2f} {unit}")
        check.update(kwargs)
        self.plan.write_text(json.dumps({"table":"data.csv","id_column":"id","checks":[check]}))
        return surface.audit(self.plan)["status"]

    def test_anchor_binds_value_and_unit_to_its_own_claim(self):
        self.assertEqual(self.inspect(), "matched")
        for text in ("Primary: +47.90 ppb. Sensitivity: +40.16 ppb", "Primary: -40.16 ppb",
                     "Primary: +40.16 ppm", "Primary: +40.16 ppb\nPrimary: +40.16 ppb"):
            self.md.write_text(text)
            self.assertEqual(self.inspect(), "mismatch")

    def test_svg_text_and_caption_and_unreadable_plot(self):
        (self.root/"plot.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"><text>Primary:</text><text>+40.16 ppb</text><text>Sensitivity</text></svg>')
        self.assertEqual(self.inspect("plot.svg", before="Sensitivity"), "matched")
        (self.root/"chart.png").write_bytes(b"image")
        self.assertEqual(self.inspect("chart.png"), "not_checked")

    def test_missing_field_duplicate_id_and_escape(self):
        with self.assertRaises(ValueError):
            self.inspect(expect="{imaginary}")
        self.table.write_text("id,gap,unit\nmain,1,ppb\nmain,2,ppb")
        with self.assertRaises(ValueError):
            self.inspect()
        with self.assertRaises(ValueError):
            surface.local_file(self.root, "../outside")
        self.assertFalse((self.root/"preview.png").exists())

    def test_missing_pdf_renderer_leaves_todo(self):
        (self.root/"report.pdf").write_bytes(b"%PDF-test")
        with patch.object(surface.shutil, "which", return_value=None):
            result = surface.preview_page(self.root,"report.pdf",1,self.root/"preview.png")
        self.assertEqual((result["status"],result["visual_review"]), ("not_checked","not_performed"))


if __name__ == "__main__":
    unittest.main()
