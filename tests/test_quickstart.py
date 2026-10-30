"""One-command setup preserves refusal and reports a real partial failure."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from core import cli
from core.storage import CoreError


class Quickstart(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='rwt-quickstart-')
        self.addCleanup(temporary.cleanup)
        self.project = Path(temporary.name) / 'research with spaces'

    def invoke(self, *extra):
        result = subprocess.run(
            [sys.executable, '-I', '-B', str(ROOT / 'tools/research.py'),
             'init', '--output', str(self.project), '--title', '示例问题', *extra],
            capture_output=True, text=True, encoding='utf-8', timeout=30)
        return result.returncode, json.loads(result.stdout)

    def test_one_command_installs_portable_skills_and_refuses_a_second_setup(self):
        code, result = self.invoke('--connect-skills')
        self.assertEqual(code, 0, result)
        self.assertTrue(result['skill_connection']['installed'])
        self.assertFalse(result['skill_connection']['global_installation'])
        self.assertEqual(len(result['skill_connection']['skills']), 9)
        runtime = self.project / '.agents/skills/_rw-runtime/tools/research.py'
        restored = subprocess.run([sys.executable, '-I', '-B', str(runtime),
                                   'resume', '--root', str(self.project)],
                                  capture_output=True, text=True,
                                  encoding='utf-8', timeout=30)
        self.assertEqual(restored.returncode, 0, restored.stdout)
        before = (self.project / 'project.json').read_bytes()
        code, result = self.invoke('--connect-skills')
        self.assertNotEqual(code, 0)
        self.assertFalse(result['passed'])
        self.assertEqual((self.project / 'project.json').read_bytes(), before)

    def test_missing_toolkit_resource_fails_before_creating_project(self):
        with patch.object(cli, 'build_payload', side_effect=CoreError('bundle_source_missing', 'missing')):
            with redirect_stdout(io.StringIO()) as out:
                code = cli.main(['init', '--output', str(self.project),
                                 '--title', 'Question', '--connect-skills'])
        self.assertEqual(code, 2)
        self.assertFalse(json.loads(out.getvalue())['passed'])
        self.assertFalse(self.project.exists())

    def test_failed_connection_retains_initialization_and_does_not_claim_success(self):
        with patch.object(cli, 'install', side_effect=CoreError('busy', 'writer active')):
            with redirect_stdout(io.StringIO()) as out:
                code = cli.main(['init', '--output', str(self.project),
                                 '--title', 'Question', '--connect-skills'])
        result = json.loads(out.getvalue())
        self.assertEqual(code, 1)
        self.assertTrue(result['initialized'])
        self.assertFalse(result['passed'])
        self.assertFalse(result['skill_connection']['passed'])
        self.assertEqual(result['skill_connection']['errors'][0]['code'], 'busy')
        self.assertTrue((self.project / 'project.json').is_file())
        self.assertFalse((self.project / '.agents/skills').exists())


if __name__ == '__main__':
    unittest.main()
