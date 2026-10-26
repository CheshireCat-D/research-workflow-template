"""Portable Windows path rules and real Win32 filesystem/lock checks on Windows."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.storage import CoreError, ProjectFiles, read_input
from core.windows_storage import validate_windows_parts


class WindowsPathRules(unittest.TestCase):
    def test_device_names_and_aliases_are_rejected(self):
        for name in ('CON', 'nul.json', 'AUX.txt', 'PRN', 'COM1.log', 'LPT9',
                     'com¹.dat', 'LPT².txt', 'CONIN$', 'CONOUT$.txt', 'CLOCK$',
                     'notes.', 'notes ', 'CON .json', 'file:stream', 'a\\b',
                     '//server/share', 'C:/project/file', 'a/../file',
                     'a//file', 'a/*', 'a/quest?', 'a/line\nfeed'):
            with self.subTest(name=name), self.assertRaises(CoreError) as caught:
                validate_windows_parts(name)
            self.assertEqual(caught.exception.code, 'unsafe_path')

    def test_regular_unicode_paths_keep_portable_separator(self):
        self.assertEqual(validate_windows_parts('研究 with spaces/数据.json'),
                         ['研究 with spaces', '数据.json'])
        self.assertEqual(validate_windows_parts('.agents/skills/SKILL.md'),
                         ['.agents', 'skills', 'SKILL.md'])
        self.assertEqual(validate_windows_parts('computer.txt/com10.json'),
                         ['computer.txt', 'com10.json'])

    def test_explicit_json_input_is_binary_and_utf8(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / '输入.json'
            path.write_bytes('{"text":"第一行\\r\\n第二行\\u001a"}\r\n'.encode())
            self.assertEqual(read_input(path), {'text': '第一行\r\n第二行\x1a'})


@unittest.skipUnless(os.name == 'nt', 'requires real Windows handles and NTFS')
class NativeWindowsStorage(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='rw-win32-')
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.root = self.base / '研究项目 with spaces'
        self.root.mkdir()

    def junction(self, name, target):
        link = self.root / name
        result = subprocess.run(['cmd', '/d', '/c', 'mklink', '/J', str(link), str(target)],
                                capture_output=True, text=True, errors='replace')
        self.assertEqual(result.returncode, 0, (result.stdout, result.stderr))
        self.addCleanup(lambda: link.rmdir() if os.path.lexists(link) else None)
        return link

    def test_binary_read_write_fingerprint_and_atomic_replace(self):
        data = b'line\r\n\x1a\x00' + '数学'.encode()
        with ProjectFiles(self.root) as files, files.lock():
            self.assertTrue(files.is_windows)
            files.write('notes/数据.bin', data)
            self.assertEqual(files.read('notes/数据.bin'), data)
            self.assertEqual(files.fingerprint('notes/数据.bin'), hashlib.sha256(data).hexdigest())
            identity = files.identity('notes/数据.bin')
            files.write('notes/数据.bin', b'replaced')
            self.assertEqual(files.read('notes/数据.bin'), b'replaced')
            self.assertNotEqual(files.identity('notes/数据.bin'), identity)
        self.assertEqual(list(self.root.rglob('.rw-*')), [])

    def test_checked_directory_blocks_rename_until_guard_closes(self):
        (self.root / 'notes').mkdir()
        with ProjectFiles(self.root) as files:
            with files.checked_directory('notes'):
                with self.assertRaises(OSError):
                    (self.root / 'notes').rename(self.root / 'renamed')
            (self.root / 'notes').rename(self.root / 'renamed')
        self.assertTrue((self.root / 'renamed').is_dir())

    def test_junction_cannot_redirect_read_write_or_directory_identity(self):
        outside = self.base / 'outside'
        outside.mkdir()
        sentinel = outside / 'keep.txt'
        sentinel.write_bytes(b'keep')
        self.junction('linked', outside)
        with ProjectFiles(self.root) as files:
            for operation in (lambda: files.read('linked/keep.txt'),
                              lambda: files.write('linked/keep.txt', b'changed'),
                              lambda: files.directory_identity('linked')):
                with self.assertRaises(CoreError) as caught:
                    operation()
                self.assertEqual(caught.exception.code, 'unsafe_path')
        self.assertEqual(sentinel.read_bytes(), b'keep')

    def test_junction_root_is_rejected_before_resolve(self):
        target = self.base / 'target'
        target.mkdir()
        link = self.junction('root-alias', target)
        with self.assertRaises(CoreError) as caught:
            ProjectFiles(link)
        self.assertEqual(caught.exception.code, 'unsafe_path')

    def test_hardlink_identity_matches_metadata_alias(self):
        (self.root / 'project.json').write_bytes(b'{}')
        (self.root / 'records').mkdir()
        (self.root / 'records/registry.json').write_bytes(b'{}')
        os.link(self.root / 'project.json', self.root / 'alias.json')
        with ProjectFiles(self.root) as files:
            identities, _ = files.internal_identities()
            self.assertIn(files.identity('alias.json'), identities)

    def test_writer_lock_is_nonblocking_and_released_after_context(self):
        code = '''from core.storage import CoreError, ProjectFiles
import sys
try:
    with ProjectFiles(sys.argv[1]) as files, files.lock():
        print('acquired')
except CoreError as error:
    print(error.code)
'''
        environment = dict(os.environ, PYTHONPATH=str(ROOT), PYTHONDONTWRITEBYTECODE='1')
        def other_process():
            return subprocess.run([sys.executable, '-B', '-c', code, str(self.root)],
                                  cwd=ROOT, env=environment, capture_output=True,
                                  text=True, encoding='utf-8', timeout=15)
        with ProjectFiles(self.root) as files, files.lock():
            result = other_process()
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), 'project_busy')
        result = other_process()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), 'acquired')


if __name__ == '__main__':
    unittest.main()
