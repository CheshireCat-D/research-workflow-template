from pathlib import Path
import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys

ROOT = Path('PROJECT_ROOT')
INPUT = Path('INPUT_DIR')
OUT = Path('OUTPUT_DIR')
PYTHON = 'EVAL_PYTHON'
REQUEST = INPUT.parent / 'REQUEST.md'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def identity(path):
    return {'sha256': sha(path), 'bytes': path.stat().st_size}

def load(path):
    return json.loads(path.read_text(encoding='utf-8'))

def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')

if ROOT.exists():
    raise SystemExit('Project exists: refused to overwrite')
manifest = load(INPUT / 'initial/MANIFEST.json')
for relative, expected in manifest['files'].items():
    actual = identity(INPUT / 'initial' / relative)
    if actual != expected:
        raise SystemExit('Initial manifest mismatch: ' + relative)
ROOT.mkdir()
shutil.copytree(INPUT / 'initial/project_payload', ROOT, dirs_exist_ok=True)
provenance = ROOT / '.research/provenance/initial'
provenance.mkdir(parents=True)
for name in ('BRIEF.md', 'MANIFEST.json', 'constraints.json', 'obligations.json', 'source-identities.json'):
    shutil.copy2(INPUT / 'initial' / name, provenance / name)
for name in ('PROTOCOL.md', 'RECORDING.md', 'STAGE-A.md'):
    shutil.copy2(INPUT / name, provenance / name)

constraints = load(provenance / 'constraints.json')
obligations = load(provenance / 'obligations.json')
sources = load(provenance / 'source-identities.json')
paths = list(obligations['local_tracking_paths']) + [obligations['companion_deliverable']]
tracked = {p: identity(ROOT / p) for p in paths}
before = {p: {'identity': identity(ROOT / p), 'mtime_ns': (ROOT / p).stat().st_mtime_ns} for p in paths}
normal = OUT / 'validation-normal'
rejected = OUT / 'validation-rejected'
commands = []

def run(label, argv):
    result = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True)
    record = {'label': label, 'argv': argv, 'cwd': str(ROOT), 'exit_code': result.returncode,
              'stdout': result.stdout, 'stderr': result.stderr}
    commands.append(record)
    save(OUT / (label + '-execution.json'), record)
    return result

normal_run = run('normal', [PYTHON, '-I', '-B', str(ROOT / 'scripts/compute.py'), '--root', str(ROOT), '--output', str(normal)])
if normal_run.returncode != 0:
    raise SystemExit('Normal calculator failed; execution retained')
normal_before = {p.name: {'identity': identity(p), 'mtime_ns': p.stat().st_mtime_ns} for p in sorted(normal.iterdir()) if p.is_file()}
invalid_run = run('rejected', [PYTHON, '-I', '-B', str(ROOT / 'scripts/compute.py'), '--root', str(ROOT), '--spec', str(ROOT / 'notes/rejected-parameters.json'), '--output', str(rejected)])
after = {p: {'identity': identity(ROOT / p), 'mtime_ns': (ROOT / p).stat().st_mtime_ns} for p in paths}
normal_after = {p.name: {'identity': identity(p), 'mtime_ns': p.stat().st_mtime_ns} for p in sorted(normal.iterdir()) if p.is_file()}
with (ROOT / 'results/table.csv').open(newline='', encoding='utf-8') as stream:
    initial_rows = list(csv.DictReader(stream))
with (normal / 'table.csv').open(newline='', encoding='utf-8') as stream:
    computed_rows = list(csv.DictReader(stream))
canonical = load(ROOT / 'results/result.json')
computed = load(normal / 'result.json')
summary = (ROOT / 'results/summary.md').read_text(encoding='utf-8')
checks = {
    'supplied_manifest_all_files_match': True,
    'normal_exit_code': normal_run.returncode,
    'result_json_semantic_equal': canonical == computed,
    'result_json_byte_equal': (ROOT / 'results/result.json').read_bytes() == (normal / 'result.json').read_bytes(),
    'table_csv_rows_equal': initial_rows == computed_rows,
    'table_csv_byte_equal': (ROOT / 'results/table.csv').read_bytes() == (normal / 'table.csv').read_bytes(),
    'table_csv_equal_after_newline_normalization': (ROOT / 'results/table.csv').read_text() == (normal / 'table.csv').read_text(),
    'table_agrees_with_result': [{'v': float(row['v']), 'boundary': float(row['boundary'])} for row in computed_rows] == computed['values'],
    'summary_current_scope_checked': all(token in summary for token in ('alpha=0.05', 'rho=1', '9.606401928869', '不是新证明或模拟覆盖验证')),
    'summary_v10_rounding_equal': format(next(row['boundary'] for row in computed['values'] if row['v'] == 10), '.12f') == '9.606401928869',
    'rejected_exit_code': invalid_run.returncode,
    'rejected_error': json.loads(invalid_run.stderr),
    'rejected_output_directory_exists': rejected.exists(),
    'project_registered_bytes_and_mtimes_unchanged_by_runs': before == after,
    'normal_validation_bytes_and_mtimes_unchanged_by_invalid_run': normal_before == normal_after,
    'registered_before': before,
    'registered_after': after,
    'normal_before_invalid': normal_before,
    'normal_after_invalid': normal_after,
}
assert all(checks[k] for k in ('result_json_semantic_equal', 'result_json_byte_equal', 'table_csv_rows_equal', 'table_csv_equal_after_newline_normalization', 'table_agrees_with_result', 'summary_current_scope_checked', 'summary_v10_rounding_equal', 'project_registered_bytes_and_mtimes_unchanged_by_runs', 'normal_validation_bytes_and_mtimes_unchanged_by_invalid_run'))
assert invalid_run.returncode == 2 and not rejected.exists()
save(OUT / 'validation-checks.json', checks)
evidence = ROOT / '.research/evidence/A'
evidence.mkdir(parents=True)
for name in ('normal-execution.json', 'rejected-execution.json', 'validation-checks.json'):
    shutil.copy2(OUT / name, evidence / name)
shutil.copytree(normal, evidence / 'normal')

versions = {}
for relative in ('notes/parameters.json', 'results/result.json', 'results/table.csv', 'results/summary.md'):
    destination = ROOT / '.research/versions/A-initial' / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / relative, destination)
    versions[relative] = {'version': 'A-initial', 'content_path': str(destination.relative_to(ROOT)), **identity(destination),
                          'rationale': 'Exact supplied initial bytes preserved before any future revision.'}
save(ROOT / '.research/versions/A-initial/index.json', versions)

state = {
    'schema': 'durable-research-state-v1', 'case_id': 'T', 'stage': 'A', 'revision': 1,
    'authority': {'path': '.research/state.json', 'rule': 'This file is authoritative for current constraints, choices, next action, and completed fingerprints; provenance and old handoffs are historical. Actual file bytes must still be checked.'},
    'active_constraints': constraints,
    'constraints_provenance': '.research/provenance/initial/constraints.json',
    'next_action': '在交作者讨论前运行只读状态核对，确认当前 alpha=0.05、rho=1（观察前固定）、v=[0,1,10,100] 的结果与摘要仍对应；向作者报告四点数值、sub-Gaussian/V 条件和未作证明/模拟覆盖验证的范围，等待作者实际决定。未经内容复核不投稿。',
    'author_review': {'status': 'not_occurred', 'submission_authorized': False, 'venue': None},
    'sources': sources,
    'source_access': {
        'T-SRC': {'status': 'local_fixed_identity_checked', 'local_path': 'sources/howard2021-arxiv-v9.pdf', **identity(ROOT / 'sources/howard2021-arxiv-v9.pdf'),
                  'actual_read_scope': 'Whole local PDF read as bytes for SHA256 and manifest binding only. No PDF text extraction, page inspection, or independent theorem review. Title/version/DOI and page references are supplied metadata/card assertions.'},
        'T-REMOTE': {'status': 'metadata-only', 'local_copy': None, 'live_access': False, 'content_binding': False}},
    'statement': {'id': 'T-CLAIM', 'text': constraints['interest'], 'scope': 'l0=1; S and -S satisfy the relevant sub-Gaussian exponential control at the same nonnegative intrinsic V; alpha is the total two-sided budget; rho fixed before observations; numerical evaluation only.'},
    'choice': {'id': 'T-CHOICE', 'status': 'accepted_supplied_initial_parameters_for_calculation', 'parameters': load(ROOT / 'notes/parameters.json'), 'evidence': ['notes/parameters.json', '.research/provenance/initial/BRIEF.md'], 'rationale': 'Use supplied author-fixed initial parameters; no invented human approval.'},
    'logical_nodes': obligations['nodes'], 'dependency_edges': obligations['dependency_edges'],
    'tracked_materials': tracked,
    'material_ids': {'T-RAW': ['sources/howard2021-arxiv-v9.pdf'], 'T-PARAM': ['notes/parameters.json'], 'T-CODE': ['scripts/compute.py'], 'T-RESULT': ['results/result.json', 'results/table.csv'], 'T-SUMMARY': ['results/summary.md'], 'T-SOURCE-NOTE': ['notes/source-check.md']},
    'activities': {
        'T-SOURCE-CHECK': {'status': 'done', 'scope': 'Supplied fixed local identity, source metadata and source-card scope checked only; PDF pages not read.', 'input_ids': ['T-SRC', 'T-RAW'], 'output_ids': ['T-SOURCE-NOTE'], 'input_paths': ['sources/howard2021-arxiv-v9.pdf'], 'output_paths': ['notes/source-check.md'], 'depends_on': [], 'evidence': ['.research/evidence/A/validation-checks.json']},
        'T-CALC': {'status': 'done', 'scope': 'Real normal calculator execution and canonical result plus companion table comparison.', 'input_ids': ['T-PARAM', 'T-RAW', 'T-CODE', 'T-CHOICE'], 'output_ids': ['T-RESULT'], 'input_paths': ['notes/parameters.json', 'sources/howard2021-arxiv-v9.pdf', 'scripts/compute.py'], 'output_paths': ['results/result.json', 'results/table.csv'], 'depends_on': [], 'evidence': ['.research/evidence/A/normal-execution.json', '.research/evidence/A/validation-checks.json']},
        'T-SYNTH': {'status': 'done', 'scope': 'Supplied summary checked against current numerical result, fixed-rho scope and v=10 rounding; no new author review.', 'input_ids': ['T-CLAIM', 'T-RESULT'], 'output_ids': ['T-SUMMARY'], 'input_paths': ['results/result.json', 'results/table.csv'], 'output_paths': ['results/summary.md'], 'depends_on': ['T-CALC'], 'evidence': ['.research/evidence/A/validation-checks.json']}
    },
    'versions': versions,
    'coverage_limits': {'source_only': ['T-REMOTE'], 'excluded_unregistered_paths': ['notes/unregistered-scratch.md'], 'all_project_files_covered': False, 'note': 'Scratch is retained but is not a declared scientific dependency. Hash inventory is not scientific review. Remote identity metadata does not monitor content.'},
    'checkpoint': {'id': 'A-verified-initial', 'scope': 'Recorded validated fingerprints and exact initial contents; saving a checkpoint does not independently revalidate science.', 'material_sha256': {p: value['sha256'] for p, value in tracked.items()}},
    'operation_history': [{'stage': 'A', 'operation': 'normal_verification', 'exit_code': 0}, {'stage': 'A', 'operation': 'controlled_invalid_parameters', 'exit_code': 2, 'error': checks['rejected_error'], 'scientific_analysis_failure': False, 'canonical_valid_outputs_unchanged': True}],
}
for activity in state['activities'].values():
    activity['completed_material_sha256'] = {p: tracked[p]['sha256'] for p in activity['input_paths'] + activity['output_paths']}
    activity['completed_logical_sha256'] = {key: hashlib.sha256(json.dumps(state[key], ensure_ascii=False, sort_keys=True).encode()).hexdigest() for key in ('statement', 'choice') if (key == 'statement' and 'T-CLAIM' in activity['input_ids']) or (key == 'choice' and 'T-CHOICE' in activity['input_ids'])}
save(ROOT / '.research/state.json', state)

manage_source = '''from pathlib import Path
import argparse, hashlib, json, sys

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def logical(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()

def status(root):
    state = json.loads((root / '.research/state.json').read_text(encoding='utf-8'))
    changed, missing, current = [], [], {}
    for relative, expected in state['tracked_materials'].items():
        path = root / relative
        if not path.is_file():
            missing.append(relative)
        else:
            current[relative] = digest(path)
            if current[relative] != expected['sha256']:
                changed.append(relative)
    activities = {}
    for name, activity in state['activities'].items():
        reasons = []
        for relative, expected in activity['completed_material_sha256'].items():
            if current.get(relative) != expected:
                reasons.append('missing or changed material: ' + relative)
        for key, expected in activity.get('completed_logical_sha256', {}).items():
            if logical(state[key]) != expected:
                reasons.append('changed logical state: ' + key)
        activities[name] = {'recorded_status': activity['status'], 'effective_status': 'needs_recheck' if reasons else activity['status'], 'reasons': reasons}
    progress = True
    while progress:
        progress = False
        for name, activity in state['activities'].items():
            for dependency in activity['depends_on']:
                if activities[dependency]['effective_status'] != 'done':
                    reason = 'dependency needs recheck: ' + dependency
                    if reason not in activities[name]['reasons']:
                        activities[name]['reasons'].append(reason)
                        activities[name]['effective_status'] = 'needs_recheck'
                        progress = True
    result = {'case_id': state['case_id'], 'authoritative_state': '.research/state.json', 'revision': state['revision'], 'active_constraints': state['active_constraints'], 'next_action': state['next_action'], 'changed_paths': changed, 'missing_paths': missing, 'activities': activities, 'checkpoint_freshness': 'fresh_for_registered_bytes' if all(current.get(p) == expected for p, expected in state['checkpoint']['material_sha256'].items()) else 'stale_for_registered_bytes', 'coverage_limits': state['coverage_limits'], 'source_access': state['source_access'], 'scientific_scope': state['statement'], 'author_review': state['author_review']}
    return result

def main():
    parser = argparse.ArgumentParser(description='Offline durable project status and guarded exact-byte restoration. Status is read-only.')
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('status')
    restore = sub.add_parser('restore-initial')
    restore.add_argument('relative_path')
    restore.add_argument('--expected-current', required=True, help='Current complete SHA256, or MISSING. Refuses conflicts.')
    restore.add_argument('--write', action='store_true', help='Required to actually restore; default is a preview.')
    args = parser.parse_args()
    root = args.root.resolve()
    if args.command == 'status':
        print(json.dumps(status(root), ensure_ascii=False, indent=2))
        return 0
    state = json.loads((root / '.research/state.json').read_text(encoding='utf-8'))
    if args.relative_path not in state['versions']:
        raise ValueError('No preserved initial content for requested path')
    version = state['versions'][args.relative_path]
    source = root / version['content_path']
    target = root / args.relative_path
    if not target.resolve().is_relative_to(root) or not source.resolve().is_relative_to(root):
        raise ValueError('Path escapes project')
    if digest(source) != version['sha256']:
        raise ValueError('Preserved content hash mismatch')
    current = digest(target) if target.is_file() else 'MISSING'
    if current != args.expected_current:
        raise ValueError('Conflict: current hash differs from explicitly expected current')
    if args.write:
        if target.exists():
            archive = root / '.research/versions/pre-restore' / current / args.relative_path
            if archive.exists() and archive.read_bytes() != target.read_bytes():
                raise ValueError('Archive collision')
            archive.parent.mkdir(parents=True, exist_ok=True)
            if not archive.exists():
                archive.write_bytes(target.read_bytes())
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
    print(json.dumps({'operation': 'restore-initial', 'written': args.write, 'target': args.relative_path, 'previous_sha256': current, 'restored_sha256': version['sha256'], 'note': 'Restoration does not mark activities completed or revise authoritative metadata.'}, ensure_ascii=False))
    return 0

if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError) as error:
        print(json.dumps({'passed': False, 'error': type(error).__name__, 'message': str(error)}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(2)
'''
(ROOT / 'scripts/manage.py').write_text(manage_source, encoding='utf-8')
recovery = '''# 恢复与继续

本项目当前元数据的唯一权威为 `.research/state.json`。初始材料、旧交接、输入约束副本仅是历史依据；不能据旧笔记覆盖实际较新的有效版本。恢复后先核对当前文件，不因活动历史状态为 done 就沿用。

在项目内用任何可用的 Python 3.9+ 标准库环境执行（脚本不依赖原绝对目录、第三方包或本阶段外部 output）：

```sh
python3 -I -B scripts/manage.py status
```

该命令只读，比较当前登记材料与各活动完成时输入/输出及逻辑声明/选择的指纹，再沿 T-CALC → T-SYNTH 传播需复核状态。登记范围含 companion `results/table.csv`。目录 mtime 不作为科研版本。`T-SOURCE-CHECK` 仅核对所给固定本地来源身份和卡片口径；未读 PDF 正文，未联网。`T-REMOTE` 只有身份元数据，未绑定本地内容；`notes/unregistered-scratch.md` 被保留但不在自动依赖范围。

当前条件：l0=1；S 与 −S 在同一非负内在时间 V 下满足相应 sub-Gaussian 指数控制；alpha=0.05 是双侧总预算，rho=1 在观察前固定，v=[0,1,10,100]。这里只计算给定公式，不证明覆盖、不做模拟验证、不声称新颖性。初始摘要已与真实重算和表核对。

具体下一步以 state.json 的 next_action 为准：先运行只读状态检查，再将当前四点边界和条件交作者讨论。尚无人工专家批准，目标期刊未定，未经内容复核不投稿；供给截止日 2026-12-15 是组织者给定约束。

## 完整内容与失败记录

`.research/versions/A-initial/` 保存 parameters、result、table、summary 的原始完整字节和索引，可在未来覆盖/删除后恢复。大型 PDF 只保留项目内原缓存一份。`.research/evidence/A/` 保存正常实际执行、结果、逐项核对、无效参数退出 2 的错误及前后 SHA/mtime 证据。无效 alpha=1 是受控输入拒绝测试，未改变有效成果。

若需恢复初始内容，先检查当前完整 SHA，再运行预览，例如：

```sh
python3 -I -B scripts/manage.py restore-initial notes/parameters.json --expected-current CURRENT_FULL_SHA256
```

明确需要写入的阶段才加 `--write`。缺失文件用 `--expected-current MISSING`。工具先核对已保存内容 SHA 和当前 SHA，冲突即拒绝；写入前归档现有内容。恢复不会更新元数据或把活动标成已完成。之后按真实复核更新 state.json、保留修订前字节与依据，再重算受影响活动，不能靠保存 checkpoint 消除过期。只读阶段禁止任何恢复写入。

外部验证的 CSV 为标准库 csv 默认 CRLF，原表为 LF，解析行和数值完全一致。结果 JSON 字节一致；不能把 CSV SHA 不同误报为数值不同。

## 原始来源分发范围

原 PDF 仅供私人研究缓存，不放进公开仓库；公开交付使用来源身份、项目结果与自行编写程序。URL 是所给身份信息，本阶段未远程访问。来源卡给出的 p10 (14)、p28 Proposition 5 (51) 仅为所给卡片的定位陈述，本阶段未逐页核验。
'''
(ROOT / 'RECOVERY.md').write_text(recovery, encoding='utf-8')

status_run = run('status', [PYTHON, '-I', '-B', str(ROOT / 'scripts/manage.py'), 'status'])
assert status_run.returncode == 0
status = json.loads(status_run.stdout)
assert not status['changed_paths'] and not status['missing_paths']
assert all(value['effective_status'] == 'done' for value in status['activities'].values())
save(OUT / 'current-status.json', status)
shutil.copy2(OUT / 'status-execution.json', evidence / 'status-execution.json')
shutil.copy2(OUT / 'current-status.json', evidence / 'current-status.json')
save(OUT / 'stage-driver-result.json', {'created_project': str(ROOT), 'commands': commands, 'checks': {k:v for k,v in checks.items() if k not in ('registered_before','registered_after','normal_before_invalid','normal_after_invalid')}, 'current_status': status})
print(json.dumps({'project': str(ROOT), 'normal_exit': normal_run.returncode, 'rejected_exit': invalid_run.returncode, 'result_match': checks['result_json_byte_equal'], 'table_rows_match': checks['table_csv_rows_equal'], 'csv_byte_match': checks['table_csv_byte_equal'], 'unchanged': before == after, 'activities': status['activities']}, ensure_ascii=False, indent=2))
