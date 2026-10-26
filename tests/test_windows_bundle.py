"""Portable archive names and native Windows bundle operations.

The Windows cases run on a real Windows runner; their skips on POSIX do not
claim Windows execution. Junctions require neither symlink privileges nor a
developer-mode setting.
"""
from pathlib import Path
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from core import bundle
from core.project import initialize
from core.storage import CoreError, ProjectFiles
from tools import release_package


def snapshot(root):
    return {p.relative_to(root).as_posix():
            (hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_mtime_ns)
            for p in root.rglob('*') if p.is_file() and not p.is_symlink()}


class PortableArchiveNames(unittest.TestCase):
    def test_windows_aliases_and_device_paths_are_rejected_before_packaging(self):
        for name in ('core/CON.py', 'AUX.txt', 'skills/rw-review/NUL',
                     'profiles/COM1.md', 'LPT9.log', 'COM¹.txt', 'core/name.',
                     'core/name ', 'core/bad?.md', 'core/CON .json',
                     'core/file:stream', 'core/control\x01.md'):
            with self.subTest(name=name), self.assertRaises(release_package.ReleaseError):
                release_package.safe_name(name)
        self.assertEqual(release_package.safe_name('profiles/中文说明.md'),
                         'profiles/中文说明.md')

    def test_case_collisions_are_findings_even_on_a_case_sensitive_host(self):
        report = release_package._check_entries({'core/name.py': b'',
                                                'core/NAME.py': b''})
        self.assertIn({'code': 'portable_path_collision'}, report['errors'])

    def test_binary_archive_output_does_not_replace_an_existing_resource(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / 'existing.zip'
            target.write_bytes(b'Existing author bytes.\r\n')
            with self.assertRaises(FileExistsError):
                release_package.exclusive_output(target)
            self.assertEqual(target.read_bytes(), b'Existing author bytes.\r\n')


@unittest.skipUnless(os.name == 'nt', 'Requires native Windows filesystem and handles')
class NativeWindowsBundle(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='rw-windows-bundle-')
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.project = self.base / '研究 项目'
        initialize(self.project, 'Windows 中文 research')

    def changed_source(self):
        source = self.base / 'new source'
        for name in ('core', 'design', 'skills', 'profiles', 'tools'):
            shutil.copytree(ROOT / name, source / name,
                            ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        path = source / 'skills/rw-question/SKILL.md'
        path.write_text(path.read_text(encoding='utf-8') + '\nSynthetic upgrade fixture.\n',
                        encoding='utf-8')
        return source

    def junction(self, link, destination):
        result = subprocess.run(['cmd', '/c', 'mklink', '/J', str(link), str(destination)],
                                capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0, repr(result.stdout + result.stderr))
        self.addCleanup(lambda: os.rmdir(link) if os.path.lexists(link) else None)

    def test_install_check_and_moved_project_runtime_with_unicode_paths(self):
        original = snapshot(self.project)
        installed = bundle.install(self.project)
        self.assertTrue(installed['installed'])
        self.assertFalse(installed['global_installation'])
        self.assertEqual(original, {name: snapshot(self.project)[name] for name in original})
        before = snapshot(self.project)
        self.assertTrue(bundle.check(self.project)['passed'])
        self.assertEqual(snapshot(self.project), before)
        moved = self.base / '搬迁后的 project'
        self.project.rename(moved)
        runtime = moved / '.agents/skills/_rw-runtime'
        for script, arguments in (
                ('tools/research.py', ('resume', '--root', str(moved))),
                ('tools/connect_skills.py', ('check', '--installed-only', '--root', str(moved)))):
            result = subprocess.run([sys.executable, '-X', 'utf8', '-I', '-B',
                                     str(runtime / script), *arguments],
                                    capture_output=True, text=True, encoding='utf-8', timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(snapshot(moved), before)

    def test_writer_lock_prevents_a_second_bundle_install(self):
        with ProjectFiles(self.project) as files, files.lock():
            with self.assertRaises(CoreError) as raised:
                bundle.install(self.project)
        self.assertEqual(raised.exception.code, 'project_busy')
        self.assertFalse((self.project / '.agents').exists())

    def test_real_upgrade_changes_only_the_managed_bundle(self):
        bundle.install(self.project)
        metadata = snapshot(self.project / 'records')
        source = self.changed_source()
        with mock.patch.object(bundle, 'source_root', return_value=source):
            self.assertTrue(bundle.upgrade(self.project)['upgraded'])
            self.assertTrue(bundle.check(self.project)['passed'])
        self.assertEqual(snapshot(self.project / 'records'), metadata)
        self.assertFalse(any((self.project / '.agents').glob('.rw-skills-*')))

    def test_publication_failure_rolls_back_complete_original_bundle(self):
        bundle.install(self.project)
        before = snapshot(self.project / '.agents/skills')
        source = self.changed_source()
        rename = bundle._rename

        def fail_publication(parent, old, new):
            if old.startswith('.rw-skills-stage-') and new == 'skills':
                raise OSError('Injected Windows publication failure')
            return rename(parent, old, new)

        with mock.patch.object(bundle, 'source_root', return_value=source):
            with mock.patch.object(bundle, '_rename', side_effect=fail_publication):
                with self.assertRaises(OSError):
                    bundle.upgrade(self.project)
        self.assertEqual(snapshot(self.project / '.agents/skills'), before)
        self.assertTrue(bundle.check(self.project, compare_source=False)['passed'])
        self.assertFalse(any((self.project / '.agents').glob('.rw-skills-*')))

    def test_cleanup_failure_preserves_backup_and_reports_the_published_bundle(self):
        bundle.install(self.project)
        source = self.changed_source()
        remove_tree = bundle._remove_tree

        def fail_backup_cleanup(parent, name):
            if name.startswith('.rw-skills-backup-'):
                raise OSError('Injected Windows backup cleanup failure')
            return remove_tree(parent, name)

        with mock.patch.object(bundle, 'source_root', return_value=source):
            with mock.patch.object(bundle, '_remove_tree', side_effect=fail_backup_cleanup):
                with self.assertRaises(CoreError) as raised:
                    bundle.upgrade(self.project)
            self.assertEqual(raised.exception.code, 'upgrade_cleanup_required')
            self.assertTrue(bundle.check(self.project)['passed'])
        self.assertEqual(len(list((self.project / '.agents').glob('.rw-skills-backup-*'))), 1)

    def test_junction_agents_cannot_redirect_installation_outside_the_project(self):
        outside = self.base / 'outside'
        outside.mkdir()
        sentinel = outside / 'author.txt'
        sentinel.write_text('Keep this author file.', encoding='utf-8')
        before = snapshot(outside)
        self.junction(self.project / '.agents', outside)
        with self.assertRaises(CoreError) as raised:
            bundle.install(self.project)
        self.assertEqual(raised.exception.code, 'unsafe_path')
        self.assertEqual(snapshot(outside), before)

    def test_unknown_junction_is_a_finding_and_its_target_is_never_cleaned(self):
        bundle.install(self.project)
        outside = self.base / 'outside'
        outside.mkdir()
        (outside / 'author.txt').write_text('Preserve external data.', encoding='utf-8')
        before = snapshot(outside)
        self.junction(self.project / '.agents/skills/unknown-link', outside)
        report = bundle.check(self.project, compare_source=False)
        self.assertFalse(report['passed'])
        self.assertTrue(any(x['code'] == 'unexpected_bundle_resource' for x in report['findings']))
        with ProjectFiles(self.project) as files:
            with files.parent('.agents/skills') as (parent, name):
                with self.assertRaises(CoreError):
                    bundle._remove_tree(parent, name)
        self.assertEqual(snapshot(outside), before)


if __name__ == '__main__':
    unittest.main()
