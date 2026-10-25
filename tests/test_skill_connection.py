"""Real subprocess checks for project-local skill connection and portable use."""
from pathlib import Path
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
CLI = ROOT / 'tools/research.py'
CONNECT = ROOT / 'tools/connect_skills.py'
SKILLS = {'rw-workflow', 'rw-question', 'rw-literature', 'rw-innovation', 'rw-candidates',
          'rw-validation', 'rw-writing', 'rw-review', 'rw-figures'}


def snapshot(root):
    return {p.relative_to(root).as_posix(): (
        hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_size, p.stat().st_mtime_ns)
        for p in root.rglob('*') if p.is_file() and not p.is_symlink()}


class ProjectSkillConnection(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='rw-skill-connection-')
        self.base = Path(self.temporary.name)
        self.project = self.base / '研究 项目'
        self.invoke(CLI, 'init', '--output', self.project, '--title', 'Portable research')

    def tearDown(self):
        self.temporary.cleanup()

    def invoke(self, script, *arguments, expected=0, cwd=None, env=None):
        completed = subprocess.run([sys.executable, '-B', str(script), *map(str, arguments)],
                                   cwd=cwd or ROOT, text=True, capture_output=True, timeout=30,
                                   env=env or dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
        self.assertEqual(completed.returncode, expected, completed.stdout + completed.stderr)
        return json.loads(completed.stdout)

    def install(self):
        return self.invoke(CONNECT, 'install', '--root', self.project)

    def copy_source(self, name):
        source = self.base / name
        source.mkdir()
        for folder in ('core', 'design', 'skills', 'profiles', 'tools'):
            shutil.copytree(ROOT / folder, source / folder,
                            ignore=shutil.ignore_patterns('__pycache__'))
        return source

    def test_missing_shared_guidance_blocks_install_without_mutating_the_project(self):
        from core import bundle
        from core.storage import CoreError

        for name in ('profiles/selection.md', 'profiles/governance.md',
                     'profiles/templates/legal-research.md'):
            with self.subTest(resource=name):
                source = self.copy_source('missing-' + Path(name).stem)
                (source / name).unlink()
                source_before = snapshot(source)
                project_before = snapshot(self.project)
                with mock.patch.object(bundle, 'source_root', return_value=source):
                    with self.assertRaises(CoreError) as raised:
                        bundle.install(self.project)
                self.assertEqual(raised.exception.code, 'bundle_source_missing')
                self.assertIn(name, str(raised.exception))
                self.assertEqual(snapshot(source), source_before)
                self.assertEqual(snapshot(self.project), project_before)
                self.assertFalse((self.project / '.agents').exists())

    def test_install_connects_all_skills_without_touching_existing_project_files(self):
        (self.project / 'AGENTS.md').write_text('Author instructions stay here.\n')
        before = snapshot(self.project)
        result = self.install()
        self.assertTrue(result['installed'])
        self.assertFalse(result['global_installation'])
        self.assertFalse(result['project_records_modified'])
        after = snapshot(self.project)
        self.assertEqual(before, {key: after[key] for key in before})
        folder = self.project / '.agents/skills'
        self.assertEqual({p.name for p in folder.iterdir()}, SKILLS | {'_rw-runtime'})
        self.assertFalse((folder / '_rw-runtime/SKILL.md').exists())
        for skill in SKILLS:
            self.assertTrue((folder / skill / 'SKILL.md').is_file())

    def test_copied_markdown_links_resolve_and_runtime_contains_no_personal_paths(self):
        self.install()
        folder = self.project / '.agents/skills'
        for path in folder.rglob('*'):
            self.assertFalse(path.is_symlink())
            if not path.is_file():
                continue
            content = path.read_text(encoding='utf-8')
            self.assertNotIn('/Users/', content)
            self.assertNotIn('/home/', content)
            if path.suffix == '.md':
                for link in re.findall(r'\]\(([^\s)]+)\)', content):
                    if '://' in link or link.startswith('#'):
                        continue
                    self.assertTrue((path.parent / link.split('#')[0]).exists(), (path, link))

    def test_check_is_read_only_and_does_not_recreate_missing_project_lock(self):
        self.install()
        (self.project / '.research/write.lock').unlink()
        before = snapshot(self.project)
        result = self.invoke(CONNECT, 'check', '--root', self.project)
        self.assertTrue(result['read_only'])
        self.assertTrue(result['installed_integrity'])
        self.assertTrue(result['source_version_matches'])
        self.assertEqual(before, snapshot(self.project))
        self.assertFalse((self.project / '.research/write.lock').exists())

    def test_changed_missing_and_added_resources_are_findings_without_repair(self):
        self.install()
        folder = self.project / '.agents/skills'
        (folder / 'rw-writing/SKILL.md').write_text('A locally edited instruction.\n')
        (folder / 'rw-review/SKILL.md').unlink()
        (folder / 'unmanaged.txt').write_text('Unexpected local material\n')
        before = snapshot(self.project)
        result = self.invoke(CONNECT, 'check', '--root', self.project, expected=1)
        self.assertFalse(result['installed_integrity'])
        self.assertEqual({item['code'] for item in result['findings']}, {
            'bundle_resource_changed', 'bundle_resource_missing', 'unexpected_bundle_resource'})
        self.assertEqual(before, snapshot(self.project))

    def test_existing_skill_directory_even_empty_is_not_overwritten(self):
        target = self.project / '.agents/skills'
        target.mkdir(parents=True)
        before = snapshot(self.project)
        result = self.invoke(CONNECT, 'install', '--root', self.project, expected=2)
        self.assertEqual(result['errors'][0]['code'], 'skill_target_exists')
        self.assertEqual(before, snapshot(self.project))
        self.assertEqual(list(target.iterdir()), [])
        (target / 'keep.txt').write_text('Keep this skill\n')
        before = snapshot(self.project)
        self.invoke(CONNECT, 'install', '--root', self.project, expected=2)
        self.assertEqual(before, snapshot(self.project))

    def test_second_install_refuses_complete_bundle_without_changes(self):
        self.install()
        before = snapshot(self.project)
        self.invoke(CONNECT, 'install', '--root', self.project, expected=2)
        self.assertEqual(before, snapshot(self.project))

    def test_uninitialized_directory_is_rejected_without_creating_locks_or_skills(self):
        target = self.base / 'not-a-project'
        target.mkdir()
        self.invoke(CONNECT, 'install', '--root', target, expected=2)
        self.assertEqual(list(target.iterdir()), [])

    def test_busy_writer_is_reported_without_publishing_any_skill_directory(self):
        import fcntl
        with (self.project / '.research/write.lock').open('r+b') as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            before = snapshot(self.project)
            result = self.invoke(CONNECT, 'install', '--root', self.project, expected=2)
            self.assertEqual(result['errors'][0]['code'], 'project_busy')
            self.assertEqual(before, snapshot(self.project))
            self.assertFalse((self.project / '.agents').exists())
        self.install()

    def test_mid_copy_failure_cleans_staging_and_never_publishes_partial_bundle(self):
        from core.bundle import install
        from core.storage import ProjectFiles
        original = ProjectFiles.write
        writes = []
        def fail_after_two(files, relative, content):
            writes.append(relative)
            if len(writes) == 3:
                raise OSError('simulated interrupted resource copy')
            return original(files, relative, content)
        before = snapshot(self.project)
        with mock.patch.object(ProjectFiles, 'write', new=fail_after_two):
            with self.assertRaisesRegex(OSError, 'simulated interrupted'):
                install(self.project)
        self.assertEqual(before, snapshot(self.project))
        self.assertFalse((self.project / '.agents/skills').exists())
        self.assertEqual(list((self.project / '.agents').iterdir()), [])
        self.install()

    def test_symlinked_agents_target_or_resource_cannot_redirect_reads_or_writes(self):
        outside = self.base / 'outside'
        outside.mkdir()
        sentinel = outside / 'private.txt'
        sentinel.write_text('Untouched outside\n')
        (self.project / '.agents').symlink_to(outside, target_is_directory=True)
        before = snapshot(outside)
        result = self.invoke(CONNECT, 'install', '--root', self.project, expected=2)
        self.assertEqual(result['errors'][0]['code'], 'unsafe_path')
        self.assertEqual(before, snapshot(outside))
        (self.project / '.agents').unlink()
        self.install()
        resource = self.project / '.agents/skills/rw-writing/SKILL.md'
        resource.unlink()
        resource.symlink_to(sentinel)
        before = snapshot(outside)
        result = self.invoke(CONNECT, 'check', '--root', self.project, expected=1)
        self.assertIn('unsafe_bundle_resource', {item['code'] for item in result['findings']})
        self.assertEqual(before, snapshot(outside))

    def test_malformed_manifest_cannot_escape_project(self):
        self.install()
        path = self.project / '.agents/skills/_rw-runtime/bundle-manifest.json'
        manifest = json.loads(path.read_text())
        manifest['files']['../../private.txt'] = '0' * 64
        path.write_text(json.dumps(manifest))
        before = snapshot(self.project)
        result = self.invoke(CONNECT, 'check', '--root', self.project, expected=2)
        self.assertEqual(result['errors'][0]['code'], 'unsafe_path')
        self.assertEqual(before, snapshot(self.project))

    def test_relocated_project_runtime_registers_and_resumes_without_source_repository(self):
        source = self.copy_source('installation-source')
        self.invoke(source / 'tools/connect_skills.py', 'install', '--root', self.project)
        shutil.rmtree(source)
        moved = self.base / 'relocated project'
        self.project.rename(moved)
        empty_home = self.base / 'empty-home'
        empty_home.mkdir()
        environment = dict(os.environ, HOME=str(empty_home), PYTHONDONTWRITEBYTECODE='1', PYTHONPATH='')
        runtime = moved / '.agents/skills/_rw-runtime/tools/research.py'
        record = self.base / 'question.json'
        record.write_text(json.dumps({'id': 'Q1', 'type': 'question', 'text': 'What can the materials establish?',
                                     'scope': 'One portable synthetic project'}))
        self.invoke(runtime, 'register', '--root', moved, '--kind', 'statement', '--file', record,
                    cwd=self.base, env=environment)
        self.invoke(runtime, 'checkpoint', '--root', moved, '--next-action', 'Read the supplied materials',
                    cwd=self.base, env=environment)
        before = snapshot(moved)
        result = self.invoke(runtime, 'resume', '--root', moved, cwd=self.base, env=environment)
        self.assertEqual(result['next_action'], 'Read the supplied materials')
        self.assertEqual(result['scientific_validity'], 'not-assessed')
        self.assertEqual(result['counts']['statements'], 1)
        self.assertEqual(before, snapshot(moved))
        self.assertEqual(list(empty_home.iterdir()), [])

    def test_source_version_drift_is_separate_from_installed_file_integrity(self):
        self.install()
        source = self.copy_source('source-copy')
        (source / 'core/protocol.md').write_text('A later source protocol.\n')
        before = snapshot(self.project)
        result = self.invoke(source / 'tools/connect_skills.py', 'check', '--root', self.project, expected=1)
        self.assertTrue(result['installed_integrity'])
        self.assertFalse(result['source_version_matches'])
        self.assertEqual([item['code'] for item in result['findings']], ['bundle_source_version_differs'])
        self.assertEqual(before, snapshot(self.project))

    def changed_source(self, name='upgrade-source'):
        source = self.copy_source(name)
        protocol = source / 'core/protocol.md'
        protocol.write_text(protocol.read_text() + '\nA reviewed later protocol.\n')
        return source

    def test_upgrade_publishes_complete_new_bundle_and_preserves_research_records(self):
        self.install()
        source = self.changed_source()
        before = snapshot(self.project)
        result = self.invoke(source / 'tools/connect_skills.py', 'upgrade', '--root', self.project)
        self.assertTrue(result['upgraded'])
        self.assertFalse(result['project_records_modified'])
        self.assertNotEqual(result['payload_sha256'], result['previous_payload_sha256'])
        self.assertTrue(self.invoke(source / 'tools/connect_skills.py', 'check', '--root', self.project)['passed'])
        after = snapshot(self.project)
        for path in before:
            if not path.startswith('.agents/'):
                self.assertEqual(before[path], after[path], path)
        self.assertEqual({path.name for path in (self.project / '.agents').iterdir()}, {'skills'})
        self.assertIn('A reviewed later protocol.',
                      (self.project / '.agents/skills/_rw-runtime/core/protocol.md').read_text())

    def test_same_version_upgrade_is_read_only_and_does_not_create_a_missing_lock(self):
        self.install()
        (self.project / '.research/write.lock').unlink()
        before = snapshot(self.project)
        result = self.invoke(CONNECT, 'upgrade', '--root', self.project)
        self.assertFalse(result['upgraded'])
        self.assertEqual(before, snapshot(self.project))
        self.assertFalse((self.project / '.research/write.lock').exists())

    def test_upgrade_requires_an_existing_valid_bundle_before_any_mutation(self):
        (self.project / '.research/write.lock').unlink()
        before = snapshot(self.project)
        result = self.invoke(CONNECT, 'upgrade', '--root', self.project, expected=2)
        self.assertEqual(result['errors'][0]['code'], 'bundle_missing')
        self.assertIn('install', result['errors'][0]['message'])
        self.assertEqual(before, snapshot(self.project))
        empty = self.base / 'not-initialized'
        empty.mkdir()
        self.invoke(CONNECT, 'upgrade', '--root', empty, expected=2)
        self.assertEqual(list(empty.iterdir()), [])

    def test_upgrade_refuses_local_changes_missing_unknown_and_linked_resources(self):
        source = self.changed_source()
        outside = self.base / 'outside-secret'
        outside.write_text('Untouched external material\n')
        for case in ('changed', 'missing', 'unknown-file', 'empty-directory', 'symlink'):
            with self.subTest(case=case):
                if (self.project / '.agents').exists():
                    shutil.rmtree(self.project / '.agents')
                self.install()
                folder = self.project / '.agents/skills'
                target = folder / 'rw-writing/SKILL.md'
                if case == 'changed':
                    target.write_text('Author local edits\n')
                elif case == 'missing':
                    target.unlink()
                elif case == 'unknown-file':
                    (folder / 'my-notes.txt').write_text('Author notes\n')
                elif case == 'empty-directory':
                    (folder / 'my-empty-folder').mkdir()
                else:
                    target.unlink()
                    target.symlink_to(outside)
                before = snapshot(self.project)
                result = self.invoke(source / 'tools/connect_skills.py', 'upgrade', '--root', self.project, expected=2)
                self.assertEqual(result['errors'][0]['code'], 'bundle_modified')
                self.assertEqual(before, snapshot(self.project))
                self.assertEqual(outside.read_text(), 'Untouched external material\n')
                if case == 'empty-directory':
                    self.assertTrue((folder / 'my-empty-folder').is_dir())
                if case == 'symlink':
                    self.assertTrue(target.is_symlink())

    def test_upgrade_refuses_malformed_manifest_without_replacing_files(self):
        self.install()
        path = self.project / '.agents/skills/_rw-runtime/bundle-manifest.json'
        path.write_text('[]\n')
        before = snapshot(self.project)
        result = self.invoke(CONNECT, 'upgrade', '--root', self.project, expected=2)
        self.assertEqual(result['errors'][0]['code'], 'invalid_bundle_manifest')
        self.assertEqual(before, snapshot(self.project))

    def test_upgrade_does_not_follow_linked_agents_or_target_directories(self):
        self.install()
        agents = self.project / '.agents'
        outside = self.base / 'outside-agents'
        agents.rename(outside)
        agents.symlink_to(outside, target_is_directory=True)
        before = snapshot(outside)
        result = self.invoke(CONNECT, 'upgrade', '--root', self.project, expected=2)
        self.assertEqual(result['errors'][0]['code'], 'unsafe_path')
        self.assertEqual(before, snapshot(outside))
        agents.unlink()
        outside.rename(agents)
        target = agents / 'skills'
        outside = self.base / 'outside-skills'
        target.rename(outside)
        target.symlink_to(outside, target_is_directory=True)
        before = snapshot(outside)
        result = self.invoke(CONNECT, 'upgrade', '--root', self.project, expected=2)
        self.assertEqual(result['errors'][0]['code'], 'unsafe_path')
        self.assertEqual(before, snapshot(outside))

    def test_clean_legacy_six_skill_bundle_can_be_explicitly_upgraded(self):
        from core.storage import object_sha
        self.install()
        folder = self.project / '.agents/skills'
        path = folder / '_rw-runtime/bundle-manifest.json'
        manifest = json.loads(path.read_text())
        removed = {'rw-innovation', 'rw-candidates', 'rw-figures'}
        for name in removed:
            shutil.rmtree(folder / name)
        manifest['skills'] = [skill for skill in manifest['skills'] if skill not in removed]
        manifest['files'] = {p:d for p,d in manifest['files'].items() if p.split('/')[0] not in removed}
        manifest['format_version'], manifest['bundle_id'] = '1', 'research-workflow-template-d2'
        manifest['payload_sha256'] = object_sha(manifest['files'])
        path.write_text(json.dumps(manifest))
        result = self.invoke(CONNECT, 'upgrade', '--root', self.project)
        self.assertTrue(result['upgraded'])
        self.assertEqual(set(result['skills']), SKILLS)
        self.assertEqual(json.loads(path.read_text())['format_version'], '2')
        self.assertTrue(self.invoke(CONNECT, 'check', '--root', self.project)['passed'])

    def test_copied_runtime_upgrade_requires_the_full_distribution(self):
        self.install()
        before = snapshot(self.project)
        runtime = self.project / '.agents/skills/_rw-runtime/tools/connect_skills.py'
        result = self.invoke(runtime, 'upgrade', '--root', self.project, expected=2, cwd=self.base)
        self.assertEqual(result['errors'][0]['code'], 'bundle_source_required')
        self.assertEqual(before, snapshot(self.project))

    def test_busy_writer_blocks_upgrade_before_staging(self):
        import fcntl
        self.install()
        source = self.changed_source()
        with (self.project / '.research/write.lock').open('r+b') as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            before = snapshot(self.project)
            result = self.invoke(source / 'tools/connect_skills.py', 'upgrade', '--root', self.project, expected=2)
            self.assertEqual(result['errors'][0]['code'], 'project_busy')
            self.assertEqual(before, snapshot(self.project))
            self.assertEqual({path.name for path in (self.project / '.agents').iterdir()}, {'skills'})

    def test_upgrade_staging_failure_preserves_the_old_bundle(self):
        from core import bundle
        from core.storage import ProjectFiles
        self.install()
        source = self.changed_source()
        original = ProjectFiles.write
        count = 0
        def fail_copy(files, relative, data):
            nonlocal count
            count += 1
            if count == 3:
                raise OSError('simulated copy failure')
            return original(files, relative, data)
        before = snapshot(self.project)
        with mock.patch.object(bundle, 'source_root', return_value=source), mock.patch.object(ProjectFiles, 'write', new=fail_copy):
            with self.assertRaisesRegex(OSError, 'simulated copy failure'):
                bundle.upgrade(self.project)
        self.assertEqual(before, snapshot(self.project))
        self.assertEqual({path.name for path in (self.project / '.agents').iterdir()}, {'skills'})

    def test_generated_directory_name_collisions_do_not_delete_existing_material(self):
        from core import bundle
        from core.storage import CoreError
        agents = self.project / '.agents'
        agents.mkdir()
        install_collision = agents / '.rw-skills-collision'
        install_collision.mkdir()
        (install_collision / 'keep.txt').write_text('Preserve existing directory\n')
        before = snapshot(self.project)
        with mock.patch.object(bundle.uuid, 'uuid4', return_value=mock.Mock(hex='collision')):
            with self.assertRaises(FileExistsError):
                bundle.install(self.project)
        self.assertEqual(before, snapshot(self.project))
        self.install()
        source = self.changed_source()
        for prefix in ('.rw-skills-stage-', '.rw-skills-backup-'):
            with self.subTest(prefix=prefix):
                collision = agents / (prefix + 'collision')
                collision.mkdir()
                (collision / 'keep.txt').write_text('Preserve upgrade collision\n')
                before = snapshot(self.project)
                with mock.patch.object(bundle, 'source_root', return_value=source), mock.patch.object(bundle.uuid, 'uuid4', return_value=mock.Mock(hex='collision')):
                    with self.assertRaises((FileExistsError, CoreError)):
                        bundle.upgrade(self.project)
                self.assertEqual(before, snapshot(self.project))
                self.assertEqual((collision / 'keep.txt').read_text(), 'Preserve upgrade collision\n')
                shutil.rmtree(collision)

    def test_upgrade_publication_failure_restores_the_original_directory(self):
        from core import bundle
        self.install()
        source = self.changed_source()
        original = os.rename
        def fail_publish(src, dst, **kwargs):
            if str(src).startswith('.rw-skills-stage-') and dst == 'skills':
                raise OSError('simulated publish failure')
            return original(src, dst, **kwargs)
        before = snapshot(self.project)
        with mock.patch.object(bundle, 'source_root', return_value=source), mock.patch.object(bundle.os, 'rename', side_effect=fail_publish):
            with self.assertRaisesRegex(OSError, 'simulated publish failure'):
                bundle.upgrade(self.project)
        self.assertEqual(before, snapshot(self.project))
        self.assertTrue(bundle.check(self.project, compare_source=False)['installed_integrity'])
        self.assertEqual({path.name for path in (self.project / '.agents').iterdir()}, {'skills'})

    def test_upgrade_sync_failure_rolls_back_a_published_new_directory(self):
        from core import bundle
        self.install()
        source = self.changed_source()
        original_rename, original_fsync = os.rename, os.fsync
        fail_next_sync = False
        def track_publish(src, dst, **kwargs):
            nonlocal fail_next_sync
            result = original_rename(src, dst, **kwargs)
            if str(src).startswith('.rw-skills-stage-') and dst == 'skills':
                fail_next_sync = True
            return result
        def fail_sync(fd):
            nonlocal fail_next_sync
            if fail_next_sync:
                fail_next_sync = False
                raise OSError('simulated publish sync failure')
            return original_fsync(fd)
        before = snapshot(self.project)
        with mock.patch.object(bundle, 'source_root', return_value=source), mock.patch.object(bundle.os, 'rename', side_effect=track_publish), mock.patch.object(bundle.os, 'fsync', side_effect=fail_sync):
            with self.assertRaisesRegex(OSError, 'simulated publish sync failure'):
                bundle.upgrade(self.project)
        self.assertEqual(before, snapshot(self.project))
        self.assertEqual({path.name for path in (self.project / '.agents').iterdir()}, {'skills'})

    def test_upgrade_preserves_the_backup_if_rollback_itself_fails(self):
        from core import bundle
        from core.storage import CoreError
        self.install()
        source = self.changed_source()
        original = os.rename
        old_protocol = (self.project / '.agents/skills/_rw-runtime/core/protocol.md').read_bytes()
        def fail_publish_and_restore(src, dst, **kwargs):
            if dst == 'skills' and (str(src).startswith('.rw-skills-stage-') or str(src).startswith('.rw-skills-backup-')):
                raise OSError('simulated publication/rollback failure')
            return original(src, dst, **kwargs)
        with mock.patch.object(bundle, 'source_root', return_value=source), mock.patch.object(bundle.os, 'rename', side_effect=fail_publish_and_restore):
            with self.assertRaises(CoreError) as raised:
                bundle.upgrade(self.project)
        self.assertEqual(raised.exception.code, 'upgrade_recovery_required')
        backups = list((self.project / '.agents').glob('.rw-skills-backup-*'))
        self.assertEqual(len(backups), 1)
        self.assertEqual((backups[0] / '_rw-runtime/core/protocol.md').read_bytes(), old_protocol)
        self.assertIn(backups[0].name, raised.exception.message)
        self.assertFalse((self.project / '.agents/skills').exists())
        self.assertEqual(list((self.project / '.agents').glob('.rw-skills-stage-*')), [])

    def test_failed_old_backup_cleanup_reports_that_new_bundle_is_already_installed(self):
        from core import bundle
        from core.storage import CoreError
        self.install()
        source = self.changed_source()
        original = shutil.rmtree
        def fail_old_cleanup(path, *args, **kwargs):
            if str(path).startswith('.rw-skills-backup-'):
                raise OSError('simulated backup cleanup failure')
            return original(path, *args, **kwargs)
        with mock.patch.object(bundle, 'source_root', return_value=source), mock.patch.object(bundle.shutil, 'rmtree', side_effect=fail_old_cleanup):
            with self.assertRaises(CoreError) as raised:
                bundle.upgrade(self.project)
        self.assertEqual(raised.exception.code, 'upgrade_cleanup_required')
        self.assertIn('New bundle installed', raised.exception.message)
        self.assertTrue(bundle.check(self.project, compare_source=False)['installed_integrity'])
        self.assertIn('A reviewed later protocol.',
                      (self.project / '.agents/skills/_rw-runtime/core/protocol.md').read_text())
        self.assertEqual(len(list((self.project / '.agents').glob('.rw-skills-backup-*'))), 1)

    def test_upgrade_rechecks_user_edits_that_appear_during_staging(self):
        from core import bundle
        from core.storage import CoreError
        self.install()
        source = self.changed_source()
        original = bundle._stage_payload
        target = self.project / '.agents/skills/rw-writing/SKILL.md'
        def edit_after_stage(*args, **kwargs):
            result = original(*args, **kwargs)
            target.write_text('A local edit made during staging\n')
            return result
        with mock.patch.object(bundle, 'source_root', return_value=source), mock.patch.object(bundle, '_stage_payload', side_effect=edit_after_stage):
            with self.assertRaises(CoreError) as raised:
                bundle.upgrade(self.project)
        self.assertEqual(raised.exception.code, 'bundle_modified')
        self.assertEqual(target.read_text(), 'A local edit made during staging\n')
        self.assertEqual({path.name for path in (self.project / '.agents').iterdir()}, {'skills'})

    def test_nested_skill_document_links_are_relocated_by_their_actual_depth(self):
        from core.bundle import build_payload
        source = self.copy_source('nested-documents')
        folder = source / 'skills/rw-question/references/details'
        folder.mkdir(parents=True)
        (folder.parent / 'local.md').write_text('Local guide\n')
        (source / 'core/with space.md').write_text('Spaced resource\n')
        document = folder / 'deep.md'
        document.write_text('[Core](../../../../core/protocol.md#scope)\n'
                            '[CLI](../../../../tools/research.py?mode=1#help)\n'
                            '[Space](../../../../core/with%20space.md)\n'
                            '[Local](../local.md)\n'
                            '[Guide]: ../../../../profiles/methods/formal-theory.md "Title"\n'
                            'Literal ../../../../core/protocol.md stays as text.\n'
                            '`[Literal](../../../../core/protocol.md)`\n'
                            '```md\n[Example](../../../../core/protocol.md)\n```\n')
        payload = build_payload(source)
        text = payload['rw-question/references/details/deep.md'].decode()
        self.assertIn('[Core](../../../_rw-runtime/core/protocol.md#scope)', text)
        self.assertIn('[CLI](../../../_rw-runtime/tools/research.py?mode=1#help)', text)
        self.assertIn('[Space](../../../_rw-runtime/core/with%20space.md)', text)
        self.assertIn('[Guide]: ../../../_rw-runtime/profiles/methods/formal-theory.md "Title"', text)
        self.assertIn('[Local](../local.md)', text)
        self.assertIn('Literal ../../../../core/protocol.md stays as text.', text)
        self.assertIn('`[Literal](../../../../core/protocol.md)`', text)
        self.assertIn('```md\n[Example](../../../../core/protocol.md)\n```', text)
        self.invoke(source / 'tools/connect_skills.py', 'install', '--root', self.project)
        installed = self.project / '.agents/skills/rw-question/references/details/deep.md'
        for target in ('../../../_rw-runtime/core/protocol.md#scope',
                       '../../../_rw-runtime/tools/research.py?mode=1#help',
                       '../../../_rw-runtime/core/with%20space.md', '../local.md'):
            self.assertTrue((installed.parent / unquote(urlsplit(target).path)).is_file())

    def test_copied_connector_checks_integrity_without_the_source_repository(self):
        source = self.copy_source('temporary-source')
        self.invoke(source / 'tools/connect_skills.py', 'install', '--root', self.project)
        shutil.rmtree(source)
        moved = self.base / 'standalone research'
        self.project.rename(moved)
        connector = moved / '.agents/skills/_rw-runtime/tools/connect_skills.py'
        before = snapshot(moved)
        result = self.invoke(connector, 'check', '--installed-only', '--root', moved, cwd=self.base)
        self.assertTrue(result['installed_integrity'])
        self.assertFalse(result['source_comparison_performed'])
        self.assertIsNone(result['source_version_matches'])
        default = self.invoke(connector, 'check', '--root', moved, cwd=self.base)
        self.assertTrue(default['installed_integrity'])
        self.assertFalse(default['source_comparison_performed'])
        self.assertIsNone(default['source_version_matches'])
        self.assertEqual(before, snapshot(moved))
        (moved / '.agents/skills/rw-innovation/SKILL.md').write_text('Changed local instruction.\n')
        self.invoke(connector, 'check', '--installed-only', '--root', moved, expected=1)

    def test_legacy_six_skill_manifest_remains_readable_without_silent_upgrade(self):
        from core.storage import object_sha
        self.install()
        folder = self.project / '.agents/skills'
        path = folder / '_rw-runtime/bundle-manifest.json'
        manifest = json.loads(path.read_text())
        removed = {'rw-innovation', 'rw-candidates', 'rw-figures'}
        for name in removed:
            shutil.rmtree(folder / name)
        manifest['skills'] = [s for s in manifest['skills'] if s not in removed]
        manifest['files'] = {p:d for p,d in manifest['files'].items() if p.split('/')[0] not in removed}
        manifest['format_version'] = '1'
        manifest['bundle_id'] = 'research-workflow-template-d2'
        manifest['payload_sha256'] = object_sha(manifest['files'])
        path.write_text(json.dumps(manifest))
        before = snapshot(self.project)
        result = self.invoke(CONNECT, 'check', '--installed-only', '--root', self.project)
        self.assertTrue(result['installed_integrity'])
        self.assertEqual(len(result['skills']), 6)
        self.assertEqual(before, snapshot(self.project))

    def test_malformed_manifest_version_returns_json_error_without_traceback(self):
        self.install()
        path = self.project / '.agents/skills/_rw-runtime/bundle-manifest.json'
        manifest = json.loads(path.read_text())
        manifest['format_version'] = {'not': 'a scalar'}
        path.write_text(json.dumps(manifest))
        before = snapshot(self.project)
        result = self.invoke(CONNECT, 'check', '--installed-only', '--root', self.project, expected=2)
        self.assertEqual(result['errors'][0]['code'], 'invalid_bundle_manifest')
        self.assertEqual(before, snapshot(self.project))

    def test_options_are_available_from_relocated_runtime_without_creating_a_project(self):
        self.install()
        runtime=self.project/'.agents/skills/_rw-runtime/tools/research.py'
        before=snapshot(self.project)
        result=self.invoke(runtime,'options',cwd=self.base)
        self.assertTrue(result['read_only'])
        self.assertEqual({x['id'] for x in result['disciplines']},
                         {'natural-sciences','engineering','medicine-health','agriculture-life','humanities','social-sciences','law'})
        self.assertIn('formal-theory',{x['id'] for x in result['methods']})
        self.assertEqual({x['id'] for x in result['skills'] if x['status']=='implemented'},SKILLS)
        for item in result['skills']:
            if item['status']=='implemented':
                self.assertTrue((runtime.parent.parent/item['entrypoint']).is_file())
        for item in result['methods']:
            self.assertTrue((runtime.parent.parent/item['implementation']['profile']).is_file())
        self.assertEqual(before,snapshot(self.project))

    def test_options_distinguish_distribution_evidence_from_project_runtime_resources(self):
        source_catalog = (ROOT/'design/catalog.json').read_bytes()
        source_options = self.invoke(CLI, 'options')
        source_evidence = {}
        for item in source_options['methods']:
            evidence = item['implementation']['task_evidence']
            source_evidence[item['id']] = evidence
            self.assertEqual(evidence['resource_base'], 'full-distribution-root')
            self.assertEqual(evidence['availability'], 'available')
            for field in ('coverage', 'review'):
                self.assertTrue((ROOT/evidence[field]).is_file())
        self.assertEqual(source_catalog, (ROOT/'design/catalog.json').read_bytes())

        self.install()
        moved = self.base/'moved 项目'
        self.project.rename(moved)
        runtime = moved/'.agents/skills/_rw-runtime'
        before = snapshot(moved)
        copied_options = self.invoke(runtime/'tools/research.py', 'options', cwd=self.base)
        self.assertEqual(copied_options['resource_base'], 'toolkit-root')
        self.assertFalse((runtime/'evals').exists())
        generated_catalog = json.loads((runtime/'design/catalog.json').read_text())
        for collection in (copied_options['methods'], generated_catalog['methods']):
            for item in collection:
                implementation = item['implementation']
                evidence = implementation['task_evidence']
                self.assertEqual(evidence['resource_base'], 'full-distribution-root')
                self.assertEqual(evidence['availability'], 'not-included-in-project-runtime')
                for field in ('coverage', 'review', 'cases'):
                    self.assertEqual(evidence[field], source_evidence[item['id']][field])
                self.assertTrue((runtime/implementation['profile']).is_file())
                self.assertIn('full distribution', implementation['validation_scope'])
        self.assertEqual(before, snapshot(moved))


if __name__ == '__main__':
    unittest.main()
