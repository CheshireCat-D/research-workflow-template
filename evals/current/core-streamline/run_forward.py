#!/usr/bin/env python3
"""Offline comparison of old/new RWT user archives using a pinned public CSV.

Usage: python3 -B run_forward.py --old-archive OLD.zip --new-archive NEW.zip \
    --input penguins.csv --output NEW_DIRECTORY

All mutations are confined to the new output directory. Analysis/client JSON
assembly is recorded separately and excluded from workflow command counts.
No network access or external Python dependencies are used.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import csv
import hashlib
import json
import math
from pathlib import Path
import shutil
import stat
import statistics
import subprocess
import sys
import zipfile

SOURCE = {
    'source_commit': '8957207b78d6ccd1b4654a9dd9c9041b657478ab',
    'path': 'inst/extdata/penguins.csv',
    'sha256': 'f204db2c753b0937caac3cb35258562c14f073e4bbc76be24b4c51ce22767a93',
    'bytes': 15241, 'rows': 344, 'license': 'CC0-1.0',
    'url': 'https://raw.githubusercontent.com/allisonhorst/palmerpenguins/8957207b78d6ccd1b4654a9dd9c9041b657478ab/inst/extdata/penguins.csv',
    'license_url': 'https://github.com/allisonhorst/palmerpenguins/blob/8957207b78d6ccd1b4654a9dd9c9041b657478ab/LICENSE.md',
}
BOUNDARY = '仅描述该CSV的观测；未核实个体或巢重复、抽样独立性；不作因果、总体或显著性推断。'
SPECIES = ('Adelie', 'Chinstrap', 'Gentoo')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n', encoding='utf-8')


def csv_rows(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise ValueError('Missing or repeated CSV columns')
        if not {'species', 'sex', 'body_mass_g'} <= set(reader.fieldnames):
            raise ValueError('Missing analysis columns')
        rows = list(reader)
        if any(None in row or any(value is None for value in row.values()) for row in rows):
            raise ValueError('Malformed CSV row')
        return list(reader.fieldnames), rows


def complete(row):
    return row['species'] in SPECIES and row['sex'] in ('female', 'male') and row['body_mass_g'] not in ('', 'NA')


def analyze(input_path, output_path):
    data = input_path.read_bytes()
    _, rows = csv_rows(input_path)
    for row in rows:
        if row['species'] not in SPECIES or row['sex'] not in ('female', 'male', '', 'NA'):
            raise ValueError('Unknown species or sex')
        if row['body_mass_g'] not in ('', 'NA'):
            mass = float(row['body_mass_g'])
            if not math.isfinite(mass) or mass <= 0:
                raise ValueError('Non-finite/non-positive mass')
    usable = [row for row in rows if complete(row)]
    groups = []
    for species in SPECIES:
        values = {sex: [float(row['body_mass_g']) for row in usable
                        if row['species'] == species and row['sex'] == sex]
                  for sex in ('female', 'male')}
        means = {sex: statistics.mean(data) if data else None for sex, data in values.items()}
        groups.append({'species': species, 'n_female': len(values['female']), 'n_male': len(values['male']),
                       'mean_female_g': means['female'], 'mean_male_g': means['male'],
                       'male_minus_female_g': (means['male'] - means['female']
                                               if all(value is not None for value in means.values()) else None)})
    result = {'input_sha256': digest(data), 'input_bytes': len(data), 'rows': len(rows),
              'complete_species_sex_mass': len(usable), 'excluded': len(rows) - len(usable),
              'missing_sex': sum(row['sex'] in ('', 'NA') for row in rows),
              'missing_mass': sum(row['body_mass_g'] in ('', 'NA') for row in rows),
              'matches_pinned_public_input': digest(data) == SOURCE['sha256'],
              'species_contrasts': groups, 'scope': BOUNDARY}
    write_json(output_path, result)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


def derive(input_path, output_path):
    fields, rows = csv_rows(input_path)
    index = next(i for i, row in enumerate(rows) if complete(row))
    omitted = rows.pop(index)
    with output_path.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fields, lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({'action': 'omit-first-complete-observation', 'omitted_csv_row': index + 2,
                      'omitted_observation': omitted, 'rows': len(rows),
                      'input_sha256': digest(input_path.read_bytes()),
                      'derived_sha256': digest(output_path.read_bytes()),
                      'scope': 'Deterministic subset sensitivity check; original public CSV is unchanged.'},
                     ensure_ascii=False, sort_keys=True))


def tree_snapshot(root):
    result = {}
    for path in [root, *sorted(root.rglob('*'))]:
        value = path.lstat()
        if path.is_symlink():
            raise ValueError('Unexpected project symlink')
        result[path.relative_to(root).as_posix()] = {
            'kind': 'file' if path.is_file() else 'directory',
            'sha256': digest(path.read_bytes()) if path.is_file() else None,
            'mtime_ns': value.st_mtime_ns, 'mode': value.st_mode,
        }
    return result


def snapshot_sha(value):
    return digest(json.dumps(value, sort_keys=True).encode('utf-8'))


class Recorder:
    def __init__(self, root):
        self.root = root
        self.commands = []
        self.actions = []
        (root / 'logs').mkdir()

    def command(self, arm, stage, category, argv, *, project=None, readonly=False, expected=0):
        number = len(self.commands) + 1
        stem = f'{number:03d}-{arm}-{stage}'
        before = tree_snapshot(project) if readonly else None
        proc = subprocess.run(list(map(str, argv)), cwd=self.root, capture_output=True, text=True,
                              encoding='utf-8', timeout=90)
        stdout_path = self.root / 'logs' / (stem + '.stdout.txt')
        stderr_path = self.root / 'logs' / (stem + '.stderr.txt')
        stdout_path.write_text(proc.stdout, encoding='utf-8')
        stderr_path.write_text(proc.stderr, encoding='utf-8')
        after = tree_snapshot(project) if readonly else None
        entry = {'number': number, 'arm': arm, 'stage': stage, 'category': category,
                 'argv': list(map(str, argv)), 'cwd': str(self.root),
                 'expected_exit': expected, 'exit_code': proc.returncode,
                 'stdout': stdout_path.relative_to(self.root).as_posix(),
                 'stdout_sha256': digest(proc.stdout.encode('utf-8')),
                 'stderr': stderr_path.relative_to(self.root).as_posix(),
                 'stderr_sha256': digest(proc.stderr.encode('utf-8'))}
        if readonly:
            entry.update(read_only_unchanged=(before == after),
                         before_snapshot_sha256=snapshot_sha(before),
                         after_snapshot_sha256=snapshot_sha(after))
        self.commands.append(entry)
        write_json(self.root / 'commands.json', self.commands)
        if proc.returncode != expected or proc.stderr:
            raise AssertionError(f'Unexpected command result: {entry}')
        if readonly and before != after:
            raise AssertionError(f'Read-only command changed project: {entry}')
        return json.loads(proc.stdout)

    def action(self, arm, stage, action, details):
        self.actions.append({'arm': arm, 'stage': stage, 'action': action, **details})
        write_json(self.root / 'client-actions.json', self.actions)


def extract(archive, destination):
    destination.mkdir()
    with zipfile.ZipFile(archive) as package:
        names = package.namelist()
        if len(names) != len(set(names)):
            raise ValueError('Archive has repeated paths')
        for member in package.infolist():
            path = Path(member.filename)
            if path.is_absolute() or '..' in path.parts or stat.S_ISLNK(member.external_attr >> 16):
                raise ValueError('Unsafe archive entry')
        package.extractall(destination)
    cli_paths = list(destination.glob('*/tools/research.py'))
    if len(cli_paths) != 1:
        raise ValueError('Expected one top-level user toolkit')
    return cli_paths[0]


def seed_records(summary):
    return [
        {'kind': 'source', 'record': {'id': 'SRC1', 'title': 'Pinned Palmer penguins public CSV',
         'locator': SOURCE['url'], 'version': SOURCE['source_commit'], 'content_access': 'full',
         'rights': 'public', 'limitations': BOUNDARY}},
        {'kind': 'evidence', 'record': {'id': 'E1', 'type': 'pinned-public-observations',
         'description': '344 public observations; descriptive sex/mass analysis.',
         'provenance': 'Existing cached CC0 CSV verified against the pinned upstream SHA-256.',
         'source_ids': ['SRC1'], 'location': {'kind': 'local', 'path': 'data/penguins.csv'}}},
        {'kind': 'evidence', 'record': {'id': 'E2', 'type': 'analysis-code',
         'description': 'Offline standard-library descriptive calculation.',
         'provenance': 'The exact analysis code used in this temporary comparison.',
         'location': {'kind': 'local', 'path': 'code/analysis.py'}}},
        {'kind': 'activity', 'record': {'id': 'A1', 'title': 'Compute species/sex mass descriptions',
         'status': 'done', 'inputs': ['evidence:E1', 'evidence:E2'],
         'note': json.dumps(summary, ensure_ascii=False, sort_keys=True)}},
    ]


def refreshed_operations(exported, summary):
    result = deepcopy(exported)
    for operation in result:
        if operation['kind'] == 'evidence':
            operation['record']['type'] = 'derived-public-subset'
            operation['record']['description'] = '343-row sensitivity subset; first complete observation omitted.'
            operation['record']['provenance'] = (
                'Deterministic subset of the pinned public CSV; no new observation or measurement is claimed.')
        elif operation['kind'] == 'activity':
            operation['record']['status'] = 'done'
            operation['record']['note'] = json.dumps(summary, ensure_ascii=False, sort_keys=True)
    return result


def validate_recovery(result, summary):
    assert result['passed'] and not result['needs_review'], result
    assert result['checkpoint']['status'] == 'current', result
    assert not result['findings'], result
    assert result['file_tracking']['local_files'] == ['code/analysis.py', 'data/penguins.csv'], result
    assert result['activities'][0]['effective_status'] == 'done', result
    assert result['scientific_validity'] == 'not-assessed', result
    return {'input_sha256': summary['input_sha256'], 'rows': summary['rows'],
            'complete_species_sex_mass': summary['complete_species_sex_mass'],
            'species_contrasts': summary['species_contrasts'],
            'revision': result['revision'], 'next_action': result['next_action'],
            'checkpoint': result['checkpoint'], 'activities': result['activities'],
            'file_tracking': result['file_tracking'], 'counts': result['counts']}


def run(args):
    output = args.output.resolve()
    if output.exists() or not output.parent.is_dir():
        raise ValueError('Output must be a new directory with an existing parent')
    data = args.input.read_bytes()
    if digest(data) != SOURCE['sha256'] or len(data) != SOURCE['bytes']:
        raise ValueError('Input does not match the pinned public CSV')
    if len(csv_rows(args.input)[1]) != SOURCE['rows']:
        raise ValueError('Unexpected pinned input row count')
    output.mkdir()
    recorder = Recorder(output)
    write_json(output / 'invocation.json', {'argv': [sys.executable, *sys.argv]})
    write_json(output / 'source.json', SOURCE)
    inputs = output / 'inputs'
    inputs.mkdir()
    input_copy = inputs / 'penguins.csv'
    input_copy.write_bytes(data)
    archive_identity = {arm: {'sha256': digest(path.read_bytes()), 'bytes': path.stat().st_size}
                        for arm, path in [('old', args.old_archive), ('new', args.new_archive)]}
    write_json(output / 'archive-identity.json', archive_identity)
    arms = {}
    results = {}
    python = [sys.executable, '-X', 'utf8', '-I', '-B']
    action = '核实原始抽样单位和重复测量标识，再决定推断方法。'

    def cli(arm, stage, *arguments, category='workflow', readonly=False, expected=0):
        state = arms[arm]
        return recorder.command(arm, stage, category, [*python, state['cli'], *arguments],
                                project=state['project'], readonly=readonly, expected=expected)

    for arm, archive in [('old', args.old_archive), ('new', args.new_archive)]:
        arm_root = output / arm
        arm_root.mkdir()
        toolkit_cli = extract(archive, arm_root / 'package')
        project = arm_root / 'research-project'
        arms[arm] = {'cli': toolkit_cli, 'project': project}
        cli(arm, 'setup', 'init', '--output', project, '--title', 'Public penguin descriptive comparison',
            '--discipline', 'natural-sciences', '--method', 'empirical-quantitative',
            '--connect-skills', category='setup')
        (project / 'data').mkdir()
        (project / 'code').mkdir()
        (project / 'notes').mkdir()
        (project / 'data/penguins.csv').write_bytes(data)
        shutil.copyfile(Path(__file__), project / 'code/analysis.py')
        recorder.action(arm, 'setup', 'copy-pinned-data-and-exact-analysis-code', {
            'input_sha256': digest(data), 'analysis_sha256': digest((project / 'code/analysis.py').read_bytes())})
        summary = recorder.command(arm, 'initial', 'analysis', [*python, project / 'code/analysis.py',
            '_analyze', '--input', project / 'data/penguins.csv', '--output', project / 'notes/summary.json'])
        batch = arm_root / 'initial-records.json'
        write_json(batch, seed_records(summary))
        recorder.action(arm, 'initial', 'assemble-registration-json', {'path': batch.relative_to(output).as_posix(),
                                                                      'sha256': digest(batch.read_bytes())})
        if arm == 'old':
            cli(arm, 'initial', 'register-batch', '--root', project, '--file', batch)
            cli(arm, 'initial', 'checkpoint', '--root', project, '--activity', 'A1', '--next-action', action)
            recovery = cli(arm, 'initial', 'resume', '--root', project, readonly=True)
        else:
            saved = cli(arm, 'initial', 'register-batch', '--root', project, '--file', batch,
                        '--activity', 'A1', '--next-action', action)
            assert saved['registered'] and saved['checkpoint_saved'] and not saved['read_only'], saved
            recovery = saved['recovery']
        results.setdefault('initial', {})[arm] = validate_recovery(recovery, summary)
        arms[arm]['summary'] = summary

    assert results['initial']['old'] == results['initial']['new'], results['initial']
    probes = output / 'probes'
    probes.mkdir()
    for arm in ('old', 'new'):
        state = arms[arm]
        project = state['project']
        derived = recorder.command(arm, 'refresh', 'analysis', [*python, project / 'code/analysis.py',
            '_derive', '--input', input_copy, '--output', project / 'data/penguins.csv'])
        summary = recorder.command(arm, 'refresh', 'analysis', [*python, project / 'code/analysis.py',
            '_analyze', '--input', project / 'data/penguins.csv', '--output', project / 'notes/summary.json'])
        assert not summary['matches_pinned_public_input'] and summary['rows'] == 343, summary
        state['summary'] = summary
        state['derived'] = derived
        if arm == 'new':
            stale_project = probes / 'stale-checkpoint'
            shutil.copytree(project, stale_project)
            stale_before = json.loads((stale_project / 'records/registry.json').read_text(encoding='utf-8'))
            stale_result = recorder.command('new', 'stale-negative', 'probe', [*python, state['cli'],
                'checkpoint', '--root', stale_project, '--activity', 'A1', '--next-action', action, '--report'],
                project=stale_project, expected=1)
            stale_recovery = stale_result['recovery']
            assert stale_result['checkpoint_saved'] and not stale_result['passed'], stale_result
            assert {'file_changed', 'activity_stale'} <= {row['code'] for row in stale_recovery['findings']}
            stale_after = json.loads((stale_project / 'records/registry.json').read_text(encoding='utf-8'))
            assert stale_before['records'] == stale_after['records']
            results['stale_negative'] = {'exit_code': 1, 'saved': True,
                'checkpoint_status': stale_recovery['checkpoint']['status'],
                'findings': stale_recovery['findings'], 'old_bindings_unchanged': True}
            exported = cli(arm, 'refresh', 'show', '--root', project,
                           '--edit', 'evidence:E1', '--edit', 'activity:A1', readonly=True)
        else:
            exported = []
            for kind, identifier in [('evidence', 'E1'), ('activity', 'A1')]:
                shown = cli(arm, 'refresh', 'show', '--root', project, '--kind', kind, '--id', identifier,
                            readonly=True)
                exported.append({'kind': kind, 'record': deepcopy(shown['envelope']['data']),
                                 'replace': True, 'expected_version': shown['envelope']['version']})
        assert [(entry['kind'], entry['record']['id']) for entry in exported] == [
            ('evidence', 'E1'), ('activity', 'A1')], exported
        batch = output / arm / 'refresh-records.json'
        write_json(batch, refreshed_operations(exported, summary))
        recorder.action(arm, 'refresh', 'edit-exported-records-with-recomputed-summary', {
            'path': batch.relative_to(output).as_posix(), 'sha256': digest(batch.read_bytes()),
            'expected_versions': [entry['expected_version'] for entry in exported]})
        if arm == 'old':
            cli(arm, 'refresh', 'register-batch', '--root', project, '--file', batch)
            cli(arm, 'refresh', 'checkpoint', '--root', project, '--activity', 'A1', '--next-action', action)
            recovery = cli(arm, 'refresh', 'resume', '--root', project, readonly=True)
        else:
            saved = cli(arm, 'refresh', 'register-batch', '--root', project, '--file', batch,
                        '--activity', 'A1', '--next-action', action)
            assert saved['registered'] and saved['checkpoint_saved'], saved
            recovery = saved['recovery']
        results.setdefault('refresh', {})[arm] = validate_recovery(recovery, summary)
    assert results['refresh']['old'] == results['refresh']['new'], results['refresh']

    # A conflict probe runs on a separate copy, leaving both measured arms intact.
    state = arms['new']
    concurrent = probes / 'concurrent-edit'
    shutil.copytree(state['project'], concurrent)
    exported = recorder.command('new', 'version-negative', 'probe', [*python, state['cli'],
        'show', '--root', concurrent, '--edit', 'evidence:E1', '--edit', 'activity:A1'],
        project=concurrent, readonly=True)
    stale_batch = probes / 'old-export.json'
    write_json(stale_batch, exported)
    competitor = deepcopy(exported[0]['record'])
    competitor['description'] += ' Another client revised this description.'
    competing_file = probes / 'competing-record.json'
    write_json(competing_file, competitor)
    recorder.command('new', 'version-negative', 'probe', [*python, state['cli'],
        'register', '--root', concurrent, '--kind', 'evidence', '--file', competing_file,
        '--replace', '--expected-version', str(exported[0]['expected_version'])])
    before_conflict = tree_snapshot(concurrent)
    conflict = recorder.command('new', 'version-negative', 'probe', [*python, state['cli'],
        'register-batch', '--root', concurrent, '--file', stale_batch, '--next-action', action], expected=2)
    assert conflict['errors'][0]['code'] == 'version_conflict', conflict
    assert tree_snapshot(concurrent) == before_conflict
    results['version_negative'] = {'exit_code': 2, 'error': 'version_conflict',
                                   'rejected_export_version': exported[0]['expected_version'],
                                   'failed_project_bytes_and_mtimes_unchanged': True}

    moved = output / 'moved'
    moved.mkdir()
    for arm in ('old', 'new'):
        state = arms[arm]
        destination = moved / (arm + '-project')
        state['project'].rename(destination)
        (output / arm / 'package').rename(output / arm / 'package-unavailable-at-original-location')
        state['project'] = destination
        state['cli'] = destination / '.agents/skills/_rw-runtime/tools/research.py'
        recorder.action(arm, 'moved-resume', 'move-project-and-remove-original-toolkit-path', {
            'project': destination.relative_to(output).as_posix()})
        recovery = cli(arm, 'moved-resume', 'resume', '--root', destination, readonly=True)
        results.setdefault('moved-resume', {})[arm] = validate_recovery(recovery, state['summary'])
        if arm == 'old':
            cli(arm, 'save-report', 'checkpoint', '--root', destination, '--activity', 'A1',
                '--next-action', action)
            recovery = cli(arm, 'save-report', 'resume', '--root', destination, readonly=True)
        else:
            saved = cli(arm, 'save-report', 'checkpoint', '--root', destination, '--activity', 'A1',
                        '--next-action', action, '--report')
            assert saved['checkpoint_saved'] and not saved['read_only'], saved
            recovery = saved['recovery']
        results.setdefault('save-report', {})[arm] = validate_recovery(recovery, state['summary'])
        registry = json.loads((destination / 'records/registry.json').read_text(encoding='utf-8'))
        file_fingerprints = {path: digest((destination / path).read_bytes())
                             for path in registry['checkpoint']['files']}
        assert file_fingerprints == registry['checkpoint']['files']
        activity = registry['records']['activities']['A1']['data']
        assert json.loads(activity['note']) == state['summary']
        results.setdefault('final-fingerprints', {})[arm] = file_fingerprints
    assert results['moved-resume']['old'] == results['moved-resume']['new']
    assert results['save-report']['old'] == results['save-report']['new']
    assert results['final-fingerprints']['old'] == results['final-fingerprints']['new']

    counts = {stage: {arm: sum(item['category'] == 'workflow' and item['stage'] == stage
                              and item['arm'] == arm for item in recorder.commands) for arm in ('old', 'new')}
              for stage in ('initial', 'refresh', 'moved-resume', 'save-report')}
    assert counts == {'initial': {'old': 3, 'new': 1}, 'refresh': {'old': 5, 'new': 2},
                      'moved-resume': {'old': 1, 'new': 1}, 'save-report': {'old': 2, 'new': 1}}, counts
    readonly = [entry for entry in recorder.commands if 'read_only_unchanged' in entry]
    assert all(entry['read_only_unchanged'] for entry in readonly)
    public = {'passed': True, 'experiment': 'Deterministic offline software journey using real public observations.',
              'archives': archive_identity, 'source': SOURCE, 'workflow_cli_counts': counts,
              'edit_export_cli_syntax': 'Repeated --edit options, with one typed reference per option.',
              'workflow_cli_totals': {arm: sum(value[arm] for value in counts.values()) for arm in ('old', 'new')},
              'excluded_commands': dict(Counter(item['category'] for item in recorder.commands if item['category'] != 'workflow')),
              'readonly_checks': len(readonly), 'readonly_bytes_and_mtimes_unchanged': True,
              'results': results, 'commands_json_sha256': digest((output / 'commands.json').read_bytes()),
              'client_actions_json_sha256': digest((output / 'client-actions.json').read_bytes()),
              'runner_sha256': digest(Path(__file__).read_bytes()),
              'limits': ['One fixed dataset and deterministic software journey; no human-user efficiency measurement.',
                         'Command counts exclude common initialization, data analysis, derivation and client JSON edits.',
                         'No measurement of scientific accuracy, novelty, proof correctness or ranking against other skills.',
                         'The derived 343-row input is a sensitivity subset, not newly collected or corrected data.',
                         'No network verification was performed; local cached input matches the recorded upstream identity.']}
    write_json(output / 'summary.json', public)
    report = [
        '# RWT 核心流程离线前向验收', '',
        '两臂均直接解压各自冻结用户 ZIP，使用相同的固定公开企鹅 CSV、相同分析代码与相同登记内容。',
        '初始数据 344 行、完整物种/性别/体质量观测 333 行；变动输入为删除首个完整观测后的 343 行子集，实际重新计算后更新 done。', '',
        '| 同一目标 | 旧流程 CLI | 新流程 CLI |', '|---|---:|---:|',
        '| 初次登记、检查点及恢复摘要 | 3 | 1 |', '| 输入改变后导出、更新并查看恢复摘要 | 5 | 2 |',
        '| 移动整个项目后的新进程恢复 | 1 | 1 |', '| 单独保存检查点并查看恢复摘要 | 2 | 1 |',
        '| 合计 | 11 | 5 |', '',
        '共同初始化、真实数据分析、子集生成与客户端编辑 JSON 均单列，不计入工作流 CLI。旧流程已使用 register-batch，未增加额外 check。',
        '新流程以重复 --edit 参数分别指定 evidence:E1 与 activity:A1，验证同一命令保留全部导出引用。',
        f'只读命令共 {len(readonly)} 次，均验证项目字节、mtime 与目录元数据未改变。',
        '两臂初始/更新/移动恢复/纯保存后的科研摘要、实际文件指纹、有效活动状态与检查点状态一致。',
        '负例在另存项目运行：只保存新检查点仍保留 file_changed、activity_stale；旧版本编辑导出遇到并发更新返回 version_conflict，失败调用不改项目字节或 mtime。', '',
        '这是确定性软件旅程与命令计数，不是人类使用效率或科研准确率的测量，也不构成与其他科研技能包的排名。',
        '完整实际 argv、stdout/stderr 与退出码仅保留在本临时目录 logs/ 和 commands.json；公共 summary.json 只记录相对定位与哈希。', '',
        '## 更新后子集的有界描述性结果', '',
    ]
    for row in arms['old']['summary']['species_contrasts']:
        report.append(f"- 子集 {row['species']}：雌 {row['n_female']}、雄 {row['n_male']}；雄减雌均值差 {row['male_minus_female_g']:.6f} g。")
    report.extend(['', BOUNDARY, '', f"runner SHA256: {public['runner_sha256']}",
                   f"commands.json SHA256: {public['commands_json_sha256']}"])
    (output / 'report.zh.md').write_text('\n'.join(report) + '\n', encoding='utf-8')
    print(json.dumps({'passed': True, 'output': str(output), 'workflow_cli_counts': counts,
                      'readonly_checks': len(readonly), 'summary_sha256': digest((output / 'summary.json').read_bytes())},
                     ensure_ascii=False))


def main():
    if len(sys.argv) > 1 and sys.argv[1] in ('_analyze', '_derive'):
        mode = sys.argv[1]
        parser = argparse.ArgumentParser()
        parser.add_argument('--input', type=Path, required=True)
        parser.add_argument('--output', type=Path, required=True)
        arguments = parser.parse_args(sys.argv[2:])
        (analyze if mode == '_analyze' else derive)(arguments.input, arguments.output)
        return
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--old-archive', type=Path, required=True)
    parser.add_argument('--new-archive', type=Path, required=True)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    run(parser.parse_args())


if __name__ == '__main__':
    main()
