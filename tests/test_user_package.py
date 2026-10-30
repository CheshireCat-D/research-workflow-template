"""Current user delivery: actual archives, isolated runtime and rejected damage."""
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from platform_support import symlink_or_skip
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('package_user', ROOT / 'tools/package_user.py')
package = importlib.util.module_from_spec(spec)
spec.loader.exec_module(package)


def snapshot(root):
    return {path.relative_to(root).as_posix():
            (hashlib.sha256(path.read_bytes()).hexdigest(), path.stat().st_mtime_ns)
            for path in root.rglob('*') if path.is_file() and not path.is_symlink()}


class UserPackage(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='rw-user-package-unit-')
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.source = self.base / 'source'
        self.source.mkdir()
        for name in ('core', 'skills', 'profiles'):
            shutil.copytree(ROOT / name, self.source / name,
                            ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        for name in ('LICENSE', 'SECURITY.md', 'design/catalog.json',
                     'tools/research.py', 'tools/connect_skills.py',
                     *package.EXAMPLE_FILES, *package.GUIDES):
            target = self.source / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)

    def build(self, name='research-workflow-template.zip'):
        archive = self.base / name
        package.build(archive, self.source)
        return archive

    def test_new_setup_search_and_complete_example_run_from_user_zip(self):
        archive = self.build()
        with zipfile.ZipFile(archive) as source:
            source.extractall(self.base / 'download')
        toolkit = self.base / 'download' / package.ARCHIVE_ROOT
        project = self.base / 'new project'
        setup = subprocess.run(
            [sys.executable, '-I', '-B', str(toolkit / 'tools/research.py'),
             'init', '--output', str(project), '--title', 'Question', '--connect-skills'],
            capture_output=True, text=True, encoding='utf-8', timeout=30)
        self.assertEqual(setup.returncode, 0, setup.stdout + setup.stderr)
        self.assertTrue(json.loads(setup.stdout)['skill_connection']['installed'])
        search = project / '.agents/skills/rw-literature/scripts/search_crossref.py'
        help_result = subprocess.run([sys.executable, '-I', '-B', str(search), '--help'],
                                     capture_output=True, text=True, encoding='utf-8', timeout=30)
        self.assertEqual(help_result.returncode, 0, help_result.stderr)
        self.assertIn('--query', help_result.stdout)
        demo = subprocess.run(
            [sys.executable, '-I', '-B', str(toolkit / 'examples/public-penguins/run_project.py'),
             '--input', str(ROOT / 'examples/public-penguins/synthetic.csv'),
             '--output', str(self.base / 'offline demonstration')],
            capture_output=True, text=True, encoding='utf-8', timeout=60)
        self.assertEqual(demo.returncode, 0, demo.stdout + demo.stderr)
        receipt = json.loads(demo.stdout)
        self.assertFalse(receipt['matches_pinned_public_input'])
        self.assertEqual(receipt['checkpoint_status'], 'current')
        self.assertTrue(Path(receipt['first_deliverable']).is_file())

    def rewrite(self, original, target, changes):
        """Simulate edits that also update the outer list of file hashes."""
        with zipfile.ZipFile(original) as source:
            prefix = package.ARCHIVE_ROOT + '/'
            entries = {name.removeprefix(prefix): source.read(name) for name in source.namelist()}
        manifest = json.loads(entries.pop(package.MANIFEST))
        for name, data in changes.items():
            if data is None:
                entries.pop(name, None)
            else:
                entries[name] = data
        manifest['files'] = {name: package.digest(data) for name, data in entries.items()}
        entries[package.MANIFEST] = package.encoded(manifest)
        with zipfile.ZipFile(target, 'w') as output:
            for name, data in entries.items():
                output.writestr(prefix + name, data)

    def test_current_profile_is_read_only_and_excludes_development_and_private_state(self):
        for name in ('evals/current/old.json', 'tests/old.py', '.git/history',
                     'build/video.mp4', 'dist/old.zip', '.agents/private/SKILL.md'):
            path = self.source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('Excluded local fixture.\n', encoding='utf-8')
        before = snapshot(self.source)
        entries = package.inventory(self.source)
        self.assertTrue(package.check(self.source)['passed'])
        self.assertEqual(snapshot(self.source), before)
        self.assertFalse(any(name.startswith(('evals/', 'tests/', '.git/', 'build/',
                                              'dist/', '.agents/')) for name in entries))
        self.assertNotIn('tools/check_core.py', entries)
        self.assertNotIn('tools/package_user.py', entries)
        self.assertNotIn('provenance/file-origins.json', entries)
        self.assertEqual(entries['skills/rw-review/SKILL.md'],
                         (self.source / 'skills/rw-review/SKILL.md').read_bytes())
        self.assertIn('skills/rw-review/references/cross-material-consistency.md', entries)
        for name in ('review-modes.md', 'review-response.md', 'submission-delivery.md',
                     'theory-review.md'):
            self.assertIn('skills/rw-review/references/' + name, entries)
        self.assertFalse(package.payload_link_errors(entries))
        catalog = json.loads(entries['design/catalog.json'])
        for method in catalog['methods']:
            evidence = method.get('implementation', {}).get('task_evidence')
            if evidence:
                self.assertEqual(evidence['availability'], 'not-included-in-project-runtime')

    def test_real_archive_is_deterministic_and_keeps_guides_and_source_attribution(self):
        before = snapshot(self.source)
        first = self.build('first.zip')
        for path in self.source.rglob('*'):
            if path.is_file():
                os.utime(path, (1700000000, 1700000000))
        second = self.build('second.zip')
        self.assertEqual(first.read_bytes(), second.read_bytes())
        before_verify = snapshot(self.base)
        report = package.verify(first)
        self.assertTrue(report['passed'])
        self.assertEqual(snapshot(self.base), before_verify)
        self.assertEqual(report['profile'], 'user-runtime')
        with zipfile.ZipFile(first) as archive:
            prefix = package.ARCHIVE_ROOT + '/'
            self.assertEqual({name.split('/')[0] for name in archive.namelist()},
                             {package.ARCHIVE_ROOT})
            self.assertEqual(archive.read(prefix + 'USER_GUIDE.en.md'),
                             (self.source / 'docs/user-package-guide.en.md').read_bytes())
            self.assertIn(b'profiles/sources.json', archive.read(prefix + 'provenance/ORIGIN.md'))
        self.assertEqual({name: value[0] for name, value in snapshot(self.source).items()},
                         {name: value[0] for name, value in before.items()})

    def test_nested_development_or_unreviewed_runtime_resources_block_collection(self):
        for name in ('skills/rw-review/tests/test_old_revision.py',
                     'skills/rw-review/evals/old.json',
                     'skills/rw-review/references/history.md',
                     'profiles/methods/revisions/old.md',
                     'core/old_revision.py'):
            with self.subTest(name=name):
                entries = package.inventory(self.source)
                entries[name] = b'# An unrelated development record.\n'
                report = package._check_entries(entries)
                self.assertFalse(report['passed'])
                self.assertIn({'code': 'outside_user_profile', 'path': name}, report['errors'])
                path = self.source / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(entries[name])
                target = self.base / 'blocked-development.zip'
                with self.assertRaises(package.ReleaseError):
                    package.build(target, self.source)
                self.assertFalse(target.exists())
                path.unlink()

    def test_revision_checker_runs_from_user_archive_without_its_source_tree(self):
        archive = self.build()
        extracted = self.base / 'checker-runtime'
        with zipfile.ZipFile(archive) as source:
            source.extractall(extracted)
        runtime = extracted / package.ARCHIVE_ROOT
        self.source.rename(self.base / 'source-moved-away')
        project = self.base / 'revision'
        project.mkdir()
        (project / 'manuscript.md').write_text('We compare the four paired plot means.\n', encoding='utf-8')
        (project / 'response.md').write_text('R1: The analysis unit is now explicit.\n', encoding='utf-8')
        plan = {
            'sources': [{'id': 'R1', 'text': 'State the analysis unit.'}],
            'items': [{'id': 'R1.a', 'source_id': 'R1', 'severity': 'major',
                       'decision': 'accept', 'status': 'done', 'depends_on': [],
                       'reply': {'path': 'response.md', 'quote': 'R1: The analysis unit is now explicit.'},
                       'changes': [{'path': 'manuscript.md', 'quote': 'We compare the four paired plot means.'}]}],
        }
        input_file = project / 'revision-plan.json'
        input_file.write_text(json.dumps(plan), encoding='utf-8')
        before = snapshot(extracted), snapshot(project)
        command = [sys.executable, '-X', 'utf8', '-I', '-B',
                   str(runtime / 'skills/rw-review/scripts/check_revision_plan.py'),
                   str(input_file), '--root', str(project), '--delivery']
        result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(json.loads(result.stdout)['passed'])
        self.assertEqual((snapshot(extracted), snapshot(project)), before)
        plan['items'][0]['reply']['quote'] = 'This response does not exist.'
        input_file.write_text(json.dumps(plan), encoding='utf-8')
        result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', timeout=30)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('quote_not_found', {e['code'] for e in json.loads(result.stdout)['errors']})

    def test_extracted_user_options_preserve_portable_scope_and_source_keeps_evidence(self):
        archive = self.build()
        extracted = self.base / 'extracted'
        with zipfile.ZipFile(archive) as source:
            source.extractall(extracted)
        runtime = extracted / package.ARCHIVE_ROOT
        before = snapshot(runtime)
        for toolkit, expected in ((ROOT, 'available'),
                                  (runtime, 'not-included-in-project-runtime')):
            result = subprocess.run([sys.executable, '-X', 'utf8', '-I', '-B',
                                     str(toolkit / 'tools/research.py'), 'options'],
                                    capture_output=True, text=True, encoding='utf-8', timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            options = json.loads(result.stdout)
            methods = [item['implementation'] for item in options['methods']
                       if item.get('implementation', {}).get('task_evidence')]
            self.assertTrue(methods)
            for implementation in methods:
                self.assertEqual(implementation['task_evidence']['availability'], expected)
                self.assertEqual(implementation['variant_evidence']['availability'], expected)
        self.assertEqual(snapshot(runtime), before)

    def test_missing_runtime_or_linked_reference_blocks_output(self):
        for name in ('core/storage.py', 'profiles/templates/legal-research.md',
                     'skills/rw-review/references/cross-material-consistency.md',
                     'skills/rw-review/references/theory-review.md',
                     'skills/rw-review/scripts/check_revision_plan.py',
                     'docs/user-package-guide.en.md'):
            with self.subTest(name=name):
                path = self.source / name
                content = path.read_bytes()
                path.unlink()
                target = self.base / 'blocked.zip'
                with self.assertRaises((package.ReleaseError, package.CoreError, FileNotFoundError)):
                    package.build(target, self.source)
                self.assertFalse(target.exists())
                path.write_bytes(content)

    def test_existing_output_or_link_is_never_overwritten(self):
        archive = self.base / 'keep.zip'
        archive.write_bytes(b'Keep existing delivery')
        before = snapshot(self.base)
        with self.assertRaises(FileExistsError):
            package.build(archive, self.source)
        link = self.base / 'link.zip'
        symlink_or_skip(self, link, archive)
        with self.assertRaises(FileExistsError):
            package.build(link, self.source)
        self.assertEqual(archive.read_bytes(), b'Keep existing delivery')
        self.assertEqual(snapshot(self.base), before)

    def test_payload_tampering_is_rejected_without_extraction(self):
        original = self.build()
        changed = self.base / 'changed.zip'
        with zipfile.ZipFile(original) as source, zipfile.ZipFile(changed, 'w') as output:
            for info in source.infolist():
                data = source.read(info)
                if info.filename.endswith('/core/cli.py'):
                    data += b'\n# Unlisted edit\n'
                output.writestr(info, data)
        before = snapshot(self.base)
        with self.assertRaises(package.ReleaseError):
            package.verify(changed)
        self.assertEqual(snapshot(self.base), before)

    def test_rehashed_missing_resources_or_development_files_are_rejected(self):
        original = self.build()
        cases = (
            {'core/storage.py': None},
            {'USER_GUIDE.en.md': None},
            {'profiles/methods/legal-analysis.md': None},
            {'skills/rw-review/references/cross-material-consistency.md': None},
            {'skills/rw-review/references/review-modes.md': None},
            {'skills/rw-review/references/review-response.md': None},
            {'skills/rw-review/references/submission-delivery.md': None},
            {'skills/rw-review/references/theory-review.md': None},
            {'evals/current/history.json': b'{}\n'},
            {'skills/rw-review/tests/test_old_revision.py': b'# Development only.\n'},
            {'profiles/methods/revisions/old.md': b'# Earlier guidance.\n'},
            {'README.md': b'[Missing local document](missing.md)\n'},
        )
        for index, changes in enumerate(cases):
            with self.subTest(changes=changes):
                target = self.base / ('rehashed-' + str(index) + '.zip')
                self.rewrite(original, target, changes)
                before = snapshot(self.base)
                with self.assertRaises(package.ReleaseError):
                    package.verify(target)
                self.assertEqual(snapshot(self.base), before)

    def test_private_source_or_symbolic_link_is_rejected(self):
        path = self.source / 'skills/rw-review/.env'
        path.write_text('Excluded secret fixture.\n', encoding='utf-8')
        with self.assertRaises(package.ReleaseError):
            package.build(self.base / 'private.zip', self.source)
        path.unlink()
        path = self.source / 'skills/rw-review/linked.md'
        symlink_or_skip(self, path, self.source / 'LICENSE')
        with self.assertRaises(package.CoreError):
            package.build(self.base / 'linked.zip', self.source)

    def test_unsafe_or_unlisted_archive_entries_are_rejected(self):
        original = self.build()
        for kind in ('parent', 'link', 'extra'):
            with self.subTest(kind=kind):
                target = self.base / (kind + '.zip')
                with zipfile.ZipFile(original) as source, zipfile.ZipFile(target, 'w') as output:
                    for info in source.infolist():
                        output.writestr(info, source.read(info))
                    name = '../escaped.txt' if kind == 'parent' else package.ARCHIVE_ROOT + '/extra.txt'
                    info = zipfile.ZipInfo(name)
                    if kind == 'link':
                        info.create_system = 3
                        info.external_attr = (stat.S_IFLNK | 0o777) << 16
                    output.writestr(info, 'Unlisted payload')
                with self.assertRaises(package.ReleaseError):
                    package.verify(target)
        self.assertFalse((self.base.parent / 'escaped.txt').exists())

    def test_clean_archive_runs_and_moved_project_recovers_without_source(self):
        archive = self.build()
        before = snapshot(self.base)
        report = package.smoke(archive)
        self.assertTrue(report['passed'])
        self.assertEqual(report['commands_executed'], 12)
        self.assertTrue(report['empty_home_and_tmp'])
        self.assertTrue(report['extracted_user_runtime_evaluation_scope_preserved'])
        self.assertTrue(report['moved_runtime_without_source_dependency'])
        self.assertTrue(report['source_bytes_and_mtime_unchanged'])
        self.assertTrue(report['read_only_project_bytes_and_mtime_unchanged'])
        self.assertEqual(snapshot(self.base), before)


if __name__ == '__main__':
    unittest.main()
