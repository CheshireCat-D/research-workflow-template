"""The machine-readable CLI must not depend on a Windows pipe's code page."""
import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]


class CLIEncodingTests(unittest.TestCase):
    def test_catalog_json_is_utf8_even_when_stdout_starts_as_ascii(self):
        script = '''
import io, sys
sys.path.insert(0, sys.argv[1])
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='ascii')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='ascii')
from core.cli import main
raise SystemExit(main(['options']))
'''
        result = subprocess.run(
            [sys.executable, '-X', 'utf8', '-I', '-B', '-c', script, str(ROOT)],
            capture_output=True, check=True,
        )
        value = json.loads(result.stdout.decode('utf-8'))
        self.assertTrue(value['passed'])
        self.assertIn('理学', [item['label'] for item in value['disciplines']])
        self.assertIn('理学'.encode('utf-8'), result.stdout)


if __name__ == '__main__':
    unittest.main()
