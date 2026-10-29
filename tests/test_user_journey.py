"""Real packaged CLI journeys for existing materials, corrections and recovery.

These are synthetic software exercises, not human usability or scientific
validation. Each command runs in a separate process from an actual user ZIP.
"""
from pathlib import Path
import csv
import hashlib
import importlib.util
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('journey_package', ROOT / 'tools/package_user.py')
package = importlib.util.module_from_spec(spec)
spec.loader.exec_module(package)


def snapshot(root):
    return {path.relative_to(root).as_posix():
            (hashlib.sha256(path.read_bytes()).hexdigest(), path.stat().st_mtime_ns)
            for path in root.rglob('*') if path.is_file()}


class UserJourney(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.delivery_temp = tempfile.TemporaryDirectory(prefix='rw-journey-delivery-')
        cls.addClassCleanup(cls.delivery_temp.cleanup)
        cls.archive = Path(cls.delivery_temp.name) / 'user.zip'
        assert package.build(cls.archive, ROOT)['passed']
        assert package.verify(cls.archive)['passed']

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='rw-journey-')
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        with zipfile.ZipFile(self.archive) as archive:
            archive.extractall(self.base / 'download')
        self.toolkit = self.base / 'download' / package.ARCHIVE_ROOT
        self.toolkit_before = snapshot(self.toolkit)
        self.project = self.base / '研究项目 with spaces'
        self.cli = self.toolkit / 'tools/research.py'
        home = self.base / 'empty-home'
        scratch = self.base / 'scratch'
        home.mkdir()
        scratch.mkdir()
        self.environment = dict(os.environ, HOME=str(home), USERPROFILE=str(home),
                                TMPDIR=str(scratch), TMP=str(scratch), TEMP=str(scratch),
                                PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1')

    def invoke(self, *arguments, script=None, expected=0, record=None, json_output=True):
        result = subprocess.run(
            [sys.executable, '-X', 'utf8', '-I', '-B', str(script or self.cli),
             *map(str, arguments)], cwd=self.base, env=self.environment,
            input=None if record is None else json.dumps(record, ensure_ascii=False),
            capture_output=True, text=True, encoding='utf-8', timeout=30)
        self.assertEqual(result.returncode, expected, (result.args, result.stdout, result.stderr))
        self.assertEqual(result.stderr, '')
        if not json_output:
            self.assertTrue(result.stdout.strip())
            return result.stdout
        payload = json.loads(result.stdout)
        self.assertIsInstance(payload, dict)
        return payload

    def initialize(self, project=None):
        target = project or self.project
        self.invoke('init', '--output', target, '--title', '既有农学资料的描述问题',
                    '--interest', '比较一份已取得的合成体重资料',
                    '--discipline', 'agriculture-life', '--method', 'empirical-quantitative')
        return target

    def register(self, kind, record, *, version=None, expected=0):
        arguments = ['register', '--root', self.project, '--kind', kind, '--file', '-']
        if version is not None:
            arguments += ['--replace', '--expected-version', version]
        return self.invoke(*arguments, record=record, expected=expected)

    def read_only(self, *arguments, expected=0, json_output=True):
        before = snapshot(self.project)
        result = self.invoke(*arguments, expected=expected, json_output=json_output)
        self.assertEqual(snapshot(self.project), before)
        return result

    def test_existing_materials_first_deliverable_correction_and_new_session(self):
        original = self.base / '原资料 already-in-use'
        original.mkdir()
        (original / 'data.csv').write_bytes(b'bird,weight_g\n1,100\n2,110\n3,130\n')
        (original / 'draft.md').write_text('Original author notes.\n', encoding='utf-8')
        original_before = snapshot(original)
        self.invoke('init', '--output', original, '--title', 'Do not overwrite', expected=2)
        self.assertEqual(snapshot(original), original_before)

        self.initialize()
        self.invoke('install', '--root', self.project,
                    script=self.toolkit / 'tools/connect_skills.py')
        capabilities = ['已有合成 CSV 和作者笔记', '本地 Python 环境']
        interest = '先描述三个合成体重测量的均值，不推断处理效果'
        configured = self.invoke('configure', '--root', self.project, '--interest', interest,
                                 '--deadline', '2026-11-30', '--budget', '仅使用本地资源',
                                 '--venue', '待定', '--add-capability', capabilities[0],
                                 '--add-capability', capabilities[1])
        self.assertTrue(configured['configured'])
        notes = self.project / 'notes'
        notes.mkdir()
        shutil.copyfile(original / 'data.csv', notes / 'data.csv')
        with (notes / 'data.csv').open(encoding='utf-8', newline='') as stream:
            values = [int(row['weight_g']) for row in csv.DictReader(stream)]
        result_path = notes / 'first-result.md'
        result_path.write_text(f'Observed synthetic mean: {sum(values) / len(values):.2f} g.\n',
                               encoding='utf-8')
        source = {'id': 'SRC1', 'title': '合成体重工作副本', 'locator': 'notes/data.csv',
                  'version': 'working-copy-1', 'content_access': 'full'}
        evidence = {'id': 'E1', 'type': 'synthetic-data', 'description': '三个合成观测',
                    'provenance': 'Copied from the preserved synthetic input for this test.',
                    'source_ids': ['SRC1'], 'location': {'kind': 'local', 'path': 'notes/data.csv'}}
        artifact = {'id': 'F1', 'type': 'first-result', 'description': '首份描述统计短稿',
                    'path': 'notes/first-result.md', 'derived_from': ['evidence:E1']}
        activity = {'id': 'A1', 'title': 'Calculate the supplied synthetic mean', 'status': 'done',
                    'inputs': ['evidence:E1'], 'outputs': ['artifact:F1']}
        batch = [{'kind': kind, 'record': record} for kind, record in
                 [('source', source), ('evidence', evidence), ('artifact', artifact),
                  ('activity', activity)]]
        self.invoke('register-batch', '--root', self.project, '--file', '-', record=batch)
        next_action = '核对下一份材料的测量单位，再决定是否扩展描述。'
        self.invoke('checkpoint', '--root', self.project, '--activity', 'A1',
                    '--next-action', next_action)

        # A new process uses only the installed project after the download moves.
        moved_toolkit = self.base / 'moved toolkit'
        self.toolkit.rename(moved_toolkit)
        runtime = self.project / '.agents/skills/_rw-runtime/tools'
        self.cli = runtime / 'research.py'
        resumed = self.read_only('resume', '--root', self.project)
        self.assertTrue(resumed['passed'])
        self.assertEqual(resumed['next_action'], next_action)
        self.assertEqual(resumed['checkpoint']['status'], 'current')
        configuration = resumed['configuration']
        self.assertEqual(configuration['interest'], interest)
        self.assertEqual(configuration['disciplines'], ['agriculture-life'])
        self.assertEqual(configuration['deliverable']['venue'], '待定')
        self.assertEqual(configuration['resources'], {
            'deadline': '2026-11-30', 'budget': '仅使用本地资源',
            'available_capabilities': capabilities})
        self.assertEqual(resumed['file_tracking']['local_files'],
                         ['notes/data.csv', 'notes/first-result.md'])
        self.assertEqual(resumed['file_tracking']['source_ids_without_local_evidence'], [])
        readable = self.read_only('resume', '--root', self.project, '--format', 'markdown',
                                  json_output=False)
        for value in (interest, '2026-11-30', 'notes/first-result.md', next_action):
            self.assertIn(value, readable)
        self.assertEqual(result_path.read_text(encoding='utf-8'),
                         'Observed synthetic mean: 113.33 g.\n')
        for command in ('check', 'status'):
            self.assertTrue(self.read_only(command, '--root', self.project)['passed'])
        before = snapshot(self.project)
        self.invoke('check', '--installed-only', '--root', self.project,
                    script=runtime / 'connect_skills.py')
        self.assertEqual(snapshot(self.project), before)

        shown = self.read_only('show', '--root', self.project, '--kind', 'artifact', '--id', 'F1')
        record = self.read_only('show', '--root', self.project, '--kind', 'artifact',
                                '--id', 'F1', '--data-only')
        self.assertEqual(record, artifact)
        before = snapshot(self.project)
        error = self.register('artifact', shown, version=shown['envelope']['version'], expected=2)
        self.assertIn('--data-only', error['errors'][0]['message'])
        self.assertEqual(snapshot(self.project), before)
        corrected = dict(record, description='更正登记描述；数值与文件未改变')
        self.register('artifact', corrected, version=shown['envelope']['version'])
        stale = self.read_only('resume', '--root', self.project, expected=1)
        self.assertIn('activity_stale', {row['code'] for row in stale['findings']})
        self.register('activity', activity, version=1)
        self.invoke('checkpoint', '--root', self.project, '--activity', 'A1',
                    '--next-action', next_action)
        registry = json.loads((self.project / 'records/registry.json').read_text(encoding='utf-8'))
        replaced = [row for row in registry['history']
                    if row.get('kind') == 'artifact' and row.get('action') == 'replace']
        self.assertEqual(len(replaced), 1)
        self.assertEqual(replaced[0]['previous']['data'], artifact)
        self.assertEqual(registry['records']['artifacts']['F1']['data'], corrected)

        before = snapshot(self.project)
        unchanged = self.invoke('configure', '--root', self.project, '--deadline', '2026-11-30',
                                '--add-capability', capabilities[0])
        self.assertFalse(unchanged['configured'])
        self.assertEqual(snapshot(self.project), before)
        self.invoke('configure', '--root', self.project, '--deadline', '2026-12-15')
        updated = self.read_only('resume', '--root', self.project, expected=1)
        self.assertEqual(updated['configuration']['resources']['deadline'], '2026-12-15')
        self.assertIn('project-config', updated['checkpoint']['changed'])
        self.invoke('checkpoint', '--root', self.project, '--activity', 'A1',
                    '--next-action', next_action)
        self.assertTrue(self.read_only('resume', '--root', self.project)['passed'])
        (notes / 'data.csv').write_bytes(b'bird,weight_g\n1,100\n2,110\n3,140\n')
        changed = self.read_only('resume', '--root', self.project, expected=1)
        self.assertIn({'code': 'file_changed', 'record': 'evidence:E1', 'path': 'notes/data.csv'},
                      changed['findings'])
        self.assertEqual(changed['activities'][0]['effective_status'], 'stale')
        self.assertEqual(snapshot(original), original_before)
        self.assertEqual(snapshot(moved_toolkit), self.toolkit_before)

    def test_source_only_and_external_materials_report_tracking_coverage(self):
        self.initialize()
        local = self.project / 'paper.txt'
        local.write_text('Original local wording.\n', encoding='utf-8')
        outside = self.base / 'outside.txt'
        outside.write_text('External material remains outside the project.\n', encoding='utf-8')
        records = [
            {'kind': 'source', 'record': {
                'id': 'SRC1', 'title': 'Local identity only', 'locator': 'paper.txt',
                'version': 'one', 'content_access': 'full'}},
            {'kind': 'source', 'record': {
                'id': 'SRC2', 'title': 'External identity', 'locator': outside.as_uri(),
                'version': 'one', 'content_access': 'metadata-only'}},
            {'kind': 'evidence', 'record': {
                'id': 'E2', 'type': 'external', 'description': 'External locator only',
                'provenance': 'Synthetic', 'source_ids': ['SRC2'],
                'location': {'kind': 'external', 'locator': outside.as_uri(),
                             'access_note': 'No file access requested.'}}},
            {'kind': 'evidence', 'record': {
                'id': 'E3', 'type': 'controlled', 'description': 'Controlled locator only',
                'provenance': 'Synthetic', 'location': {
                    'kind': 'controlled', 'reference': 'vault:unavailable-item',
                    'access_note': 'No access available or requested.'}}},
        ]
        activity = {'id': 'A1', 'title': 'Record identities and access boundaries', 'status': 'done',
                    'inputs': ['source:SRC1', 'evidence:E2', 'evidence:E3']}
        self.invoke('register-batch', '--root', self.project, '--file', '-',
                    record=records + [{'kind': 'activity', 'record': activity}])
        self.invoke('checkpoint', '--root', self.project, '--next-action', 'Obtain a local working copy.')
        local.write_text('Changed wording outside any file binding.\n', encoding='utf-8')
        outside.unlink()
        report = self.read_only('resume', '--root', self.project)
        self.assertTrue(report['passed'])
        self.assertEqual(report['checkpoint']['status'], 'current')
        self.assertEqual(report['activities'][0]['effective_status'], 'done')
        self.assertEqual(report['file_tracking']['local_file_count'], 0)
        self.assertEqual(report['file_tracking']['source_ids_without_local_evidence'], ['SRC1', 'SRC2'])
        readable = self.read_only('resume', '--root', self.project, '--format', 'markdown',
                                  json_output=False)
        self.assertIn('SRC1', readable)
        self.assertIn('SRC2', readable)
        self.assertEqual({row['record'] for row in report['warnings']
                          if row['code'] == 'evidence_not_inspected'}, {'evidence:E2', 'evidence:E3'})
        bindings = self.read_only('show', '--root', self.project, '--kind', 'activity', '--id', 'A1')
        self.assertEqual(bindings['envelope']['bindings']['files'], {})

        evidence = {'id': 'E1', 'type': 'local-text', 'description': 'Actual working copy',
                    'provenance': 'Synthetic', 'source_ids': ['SRC1'],
                    'location': {'kind': 'local', 'path': 'paper.txt'}}
        self.register('evidence', evidence)
        activity['inputs'][0] = 'evidence:E1'
        self.register('activity', activity, version=1)
        self.invoke('checkpoint', '--root', self.project, '--next-action', 'Review the bound wording.')
        local.write_text('Another update to the bound working copy.\n', encoding='utf-8')
        changed = self.read_only('resume', '--root', self.project, expected=1)
        self.assertEqual(changed['file_tracking']['local_files'], ['paper.txt'])
        self.assertEqual(changed['file_tracking']['source_ids_without_local_evidence'], ['SRC2'])
        self.assertIn({'code': 'file_changed', 'record': 'evidence:E1', 'path': 'paper.txt'},
                      changed['findings'])
        self.assertEqual(changed['activities'][0]['effective_status'], 'stale')
        self.assertEqual(snapshot(self.toolkit), self.toolkit_before)

    def test_bilingual_material_examples_execute_from_the_delivered_guides(self):
        for language, filename in [('zh', '中文介绍与使用说明.md'), ('en', 'USER_GUIDE.en.md')]:
            with self.subTest(language=language):
                text = (self.toolkit / filename).read_text(encoding='utf-8')
                block = next(block for block in re.finditer(
                    r'^```json[^\S\n]*\n(.*?)^```[^\S\n]*$', text, re.MULTILINE | re.DOTALL)
                    if 'material-batch.json' in text[max(0, block.start() - 900):block.start()])
                batch = json.loads(block.group(1))
                following = re.search(r'^```sh[^\S\n]*\n(.*?)^```[^\S\n]*$',
                                      text[block.end():], re.MULTILINE | re.DOTALL)
                self.assertIsNotNone(following)
                documented = [shlex.split(line) for line in following.group(1).splitlines() if line.strip()]
                self.assertEqual([tokens[2] for tokens in documented],
                                 ['register-batch', 'checkpoint', 'resume'])
                project = self.initialize(self.base / ('documented-' + language))
                (project / 'notes').mkdir()
                (project / 'notes/data.csv').write_bytes(b'bird,weight_g\n1,100\n2,110\n')
                input_file = self.base / (language + '-material-batch.json')
                input_file.write_text(block.group(1), encoding='utf-8')
                for tokens in documented:
                    self.assertEqual(tokens[:2], ['python3', 'tools/research.py'])
                    arguments = [str(project) if token == 'PROJECT' else
                                 str(input_file) if token == 'material-batch.json' else token
                                 for token in tokens[2:]]
                    self.invoke(*arguments, json_output='markdown' not in arguments)
                before = snapshot(project)
                resumed = self.invoke('resume', '--root', project)
                self.assertEqual(snapshot(project), before)
                self.assertEqual(resumed['file_tracking']['local_files'], ['notes/data.csv'])
                self.assertEqual(resumed['file_tracking']['source_ids_without_local_evidence'], [])
                for item in batch:
                    shown = self.invoke('show', '--root', project, '--kind', item['kind'],
                                        '--id', item['record']['id'], '--data-only')
                    self.assertEqual(shown, item['record'])
                self.assertEqual(snapshot(project), before)
                self.assertEqual(snapshot(self.toolkit), self.toolkit_before)


if __name__ == '__main__':
    unittest.main()
