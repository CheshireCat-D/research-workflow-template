from pathlib import Path
import hashlib
import json
import subprocess
import sys

ROOT = Path('PROJECT_ROOT')
INPUT = Path('INPUT_DIR')
OUT = Path('OUTPUT_DIR')
PYTHON = 'EVAL_PYTHON'
WORKSPACE = 'TASK_WORKSPACE'

def identity(path):
    data = path.read_bytes()
    return {'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}

def load(path):
    return json.loads(path.read_text(encoding='utf-8'))

def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')

state = load(ROOT / '.research/state.json')
checks = load(OUT / 'validation-checks.json')
initial_execution = load(OUT / 'stage-driver-result.json')
corrected_recovery_line = '本阶段真实核对显示：重算结果 JSON 与原件字节一致，重算 CSV 与原表也字节一致，解析行、数值及摘要 v=10 的十二位小数均一致。以后 CSV 若有换行差异，需把字节差异和数值差异分开检查，不能据 SHA 不同直接判断数值错误。'
original_recovery_line = '外部验证的 CSV 为标准库 csv 默认 CRLF，原表为 LF，解析行和数值完全一致。结果 JSON 字节一致；不能把 CSV SHA 不同误报为数值不同。'
driver_now = (OUT / 'stage_driver.py').read_bytes()
assert driver_now.count(corrected_recovery_line.encode()) == 1
driver_executed = driver_now.replace(corrected_recovery_line.encode(), original_recovery_line.encode())
(OUT / 'stage_driver.executed.py').write_bytes(driver_executed)
historical_recovery = (ROOT / 'RECOVERY.md').read_bytes().replace(corrected_recovery_line.encode(), original_recovery_line.encode())
draft = ROOT / '.research/versions/A-draft/RECOVERY.md'
draft.parent.mkdir(parents=True, exist_ok=True)
draft.write_bytes(historical_recovery)
snapshot_checks = {}
for relative, version in state['versions'].items():
    snapshot_checks[relative] = identity(ROOT / version['content_path']) == identity(ROOT / relative) == {'sha256': version['sha256'], 'bytes': version['bytes']}
assert all(snapshot_checks.values())
before = {p: {'identity': identity(ROOT / p), 'mtime_ns': (ROOT / p).stat().st_mtime_ns} for p in state['tracked_materials']}
argv = [PYTHON, '-I', '-B', str(ROOT / 'scripts/manage.py'), 'status']
status_run = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True)
status = json.loads(status_run.stdout)
after = {p: {'identity': identity(ROOT / p), 'mtime_ns': (ROOT / p).stat().st_mtime_ns} for p in state['tracked_materials']}
assert status_run.returncode == 0 and before == after
assert status['changed_paths'] == status['missing_paths'] == []
assert all(activity['effective_status'] == 'done' for activity in status['activities'].values())
assert '重算 CSV 与原表也字节一致' in (ROOT / 'RECOVERY.md').read_text(encoding='utf-8')
save(OUT / 'final-verification.json', {'snapshot_checks': snapshot_checks, 'read_only_status_preserved_registered_bytes_and_mtimes': before == after, 'status_exit_code': status_run.returncode, 'changed_paths': status['changed_paths'], 'missing_paths': status['missing_paths'], 'note': 'No guarded restoration or revision command was executed.'})

report = '''# 固定精度正态混合边界：初始项目交付

已建立可恢复项目 `PROJECT_ROOT`，创建前确认目录不存在，未覆盖已有项目。输入清单 13 项逐一匹配所给完整 SHA256 和字节数。项目保存给定材料、约束、来源身份、逻辑记录、依赖、真实验证证据和四份完整初始内容。

## 当前数值及核对

实际使用给定 `scripts/compute.py`，在独立新目录 `A/output/validation-normal/` 正常运行，退出码 0。alpha=0.05 为双侧总预算，rho=1 在观察前固定，l0=1，内在时间点为 [0,1,10,100]。计算公式为

`b(v)=sqrt((v+rho)*(log(1+v/rho)+2*log(1/alpha)))`。

|v|边界|
|---:|---:|
|0|2.4477468306808166|
|1|3.6563948713638483|
|10|9.606401928868575|
|100|32.73018624234933|

重算 `result.json` 与预制结果 JSON 完整字节及解析内容均一致；`table.csv` 也完整字节一致，解析行与 JSON 的四点值一致。摘要中的 v=10 边界 9.606401928869 与十二位小数舍入一致，alpha、rho、观察前固定及数值评估范围一致。这里验证的是给定预制结果，不声称从零发现或独立证明了研究结论。

真实命令和 stdout/stderr 位于 `normal-execution.json`；逐项结果、全长 SHA 和前后 mtime 位于 `validation-checks.json`，相同小型证据已持久保存在项目 `.research/evidence/A/`。

## 有意无效输入

另以 `notes/rejected-parameters.json` 的 alpha=1 实际运行，退出码 **2**，stderr 为 `ValueError: Require 0<alpha<1, rho>0 and finite nonnegative intrinsic times`。无效输出目录 `validation-rejected` 没有创建。所有已登记的项目输入/有效成果及正常验证输出在无效试算前后，完整 SHA256、字节数及文件 mtime 均未变。

这是受控无效输入拒绝测试；原正常结果保留，没有把它记为科学分析失败，也没有用补跑掩去首次错误。实际 argv、cwd、退出码、错误保存在 `rejected-execution.json` 和项目证据中。

## 持久状态与恢复

当前唯一元数据权威是项目 `.research/state.json`；原始约束和来源依据在 `.research/provenance/initial/`。旧笔记、旧交接和初始副本不覆盖较新有效元数据。逻辑层明确区分来源、材料、声明、关系、选择、成果和活动。

|活动|本次完成范围|当前依赖状态|
|---|---|---|
|T-SOURCE-CHECK|给定固定来源身份/版本、卡片范围检查|当前有效；不依赖数值参数|
|T-CALC|真实正常运行，并核对 JSON 和 companion 表|当前有效|
|T-SYNTH|核对所给摘要的参数、数值和范围|当前有效；依赖 T-CALC|

只读恢复命令（在项目目录，Python 3.9+ 标准库）为 `python3 -I -B scripts/manage.py status`。它比较完成时输入/输出和逻辑指纹，沿 T-CALC → T-SYNTH 传播需复核状态。最终实际执行退出 0，未发现登记材料变更或缺失；三项活动有效，checkpoint 对登记字节当前新鲜。保存断点本身不等于实质复核。

`.research/versions/A-initial/` 保存 parameters.json、result.json、table.csv、summary.md 的完整原字节和索引，四份快照与当前原件逐字节一致。`scripts/manage.py` 提供带完整当前 SHA 冲突保护的恢复预览/显式写入，写入前归档旧字节；本阶段没有实际执行恢复或任何未来修订。恢复说明为 `RECOVERY.md`。脚本以自身位置解析根目录，不依赖本阶段外部答卷或原绝对路径；原大型 PDF 只保存一份私人研究缓存。

## 来源与科学范围

本地主要来源身份来自所给 `source-identities.json`：Howard 等，Time-uniform, nonparametric, nonasymptotic confidence sequences，arXiv:1810.08240v9，DOI 10.1214/20-AOS1991。本地 PDF 1,494,142 字节，完整 SHA256 为 `eb3efd547349adfbff25514ae0854c142cd29b96b398be38c9000d69a2f64ca8`。本阶段整文件仅按字节读取以核对 hash/清单；未提取 PDF 正文、逐页查看或独立审阅定理。来源卡中的 p10 (14)、p28 Proposition 5 (51) 是所给卡片的定位陈述，本阶段未逐页核验。

适用条件仍为：S 与 −S 在同一非负内在时间 V 下满足相应 sub-Gaussian 指数控制；不能把任意经验方差直接代入。只核对给定参数的边界数值；不建立新证明、覆盖率模拟、新颖性、形式化验证或人工专家批准。

T-REMOTE 只有 arXiv:1808.03204v7 身份元数据，无本地副本、内容绑定或当前远端检查；本阶段网络调用为 0。`notes/unregistered-scratch.md` 原样保留但不纳入自动依赖检测，不声称覆盖全部项目文件。原始 PDF 只供私人缓存，公开交付不分发原始资料。

当前截止日为给定的 2026-12-15（组织者约束），只用离线 Python 标准库，不收集新数据、不重拟合，目标期刊未定、语言中文。具体下一步：先运行只读状态检查，向作者讨论当前四点结果、上述条件与未作证明/模拟的范围，等待作者实际决定；未经内容复核不投稿。

主答卷和执行记录分别为本目录 `report.md` 与 `execution.json`；机器可读当前事实见 `state-answer.json`，完整输入/产物身份见 `inputs-and-artifacts.json`。
'''
assert len(report) <= 10000
(OUT / 'report.md').write_text(report, encoding='utf-8')
answer = {'case_id': 'T', 'stage': 'A', 'active_constraints': state['active_constraints'], 'next_action': state['next_action'], 'changed_or_missing_paths': [], 'affected_activities': [], 'unaffected_activities': list(state['activities']), 'checkpoint_freshness': status['checkpoint_freshness'], 'scientific_scope': state['statement'], 'source_tracking_limits': state['coverage_limits'], 'source_access': state['source_access'], 'material_paths': {'project_root': str(ROOT), 'canonical_state': '.research/state.json', 'recovery': 'RECOVERY.md', 'initial_content_versions': '.research/versions/A-initial/index.json', 'durable_evidence': '.research/evidence/A/', 'local_materials': state['material_ids'], 'normal_external_verification': str(OUT / 'validation-normal')}, 'notes': ['No expert approval or external submission.', 'Original supplied initial result independently recalculated using the supplied calculator; no new theorem proof.', 'Normal JSON and CSV are each byte-identical to canonical delivered files.', 'Intentional rejected input exit 2; valid outputs unchanged.', 'Source PDF hash-only access; supplied page references not independently inspected.', 'Restoration code retained but no restoration executed.']}
save(OUT / 'state-answer.json', answer)

code2 = 'from pathlib import Path; import hashlib; p=Path("INPUT_DIR"); print("INPUT FILES"); [print(str(x.relative_to(p)),x.stat().st_size) for x in sorted(p.rglob("*")) if x.is_file()]; [(print("\\nFILE",str(p/n)),print((p/n).read_text())) for n in ("PROTOCOL.md","RECORDING.md","STAGE-A.md")]; q=Path("STUDY_ROOT/runs/P5/A/REQUEST.md"); print("REQUEST_HASH",hashlib.sha256(q.read_bytes()).hexdigest(),q.stat().st_size)'
code3 = 'from pathlib import Path; import hashlib; p=Path("INPUT_DIR"); fs=[x for x in sorted((p/"initial").rglob("*")) if x.is_file()]; [(print("\\nFILE",str(x.relative_to(p)),"SHA256",hashlib.sha256(x.read_bytes()).hexdigest(),"BYTES",x.stat().st_size),print(x.read_text()) if x.suffix!=".pdf" else print("PDF content not inspected; identity hash only")) for x in fs]; q=Path("PROJECT_ROOT"); o=Path("OUTPUT_DIR"); print("PROJECT_EXISTS",q.exists(),"OUTPUT_EXISTS",o.exists()); print("OUTPUT_NAMES",[x.name for x in o.iterdir()] if o.exists() else [])'
# The command strings above are the literal -c source, with one backslash before n.
code2 = code2.replace('\\\\nFILE', '\\nFILE')
code3 = code3.replace('\\\\nFILE', '\\nFILE')
outer = [
    {'call': 1, 'tool': 'exec_command', 'argv': ['cat', str(INPUT.parent / 'REQUEST.md')], 'cwd': WORKSPACE, 'exit_code': 0, 'output_summary': 'Printed the full REQUEST.md; SHA256 and bytes included in read_files.'},
    {'call': 2, 'tool': 'exec_command', 'argv': [PYTHON, '-I', '-B', '-c', code2], 'cwd': WORKSPACE, 'exit_code': 0, 'output_summary': 'Listed input paths/sizes; printed PROTOCOL, RECORDING, STAGE-A and full REQUEST hash.'},
    {'call': 3, 'tool': 'exec_command', 'argv': [PYTHON, '-I', '-B', '-c', code3], 'cwd': WORKSPACE, 'exit_code': 0, 'output_summary': 'Printed all initial text and all initial-file SHA256/bytes; PDF hash only. Confirmed project absent and output empty.'},
    {'call': 4, 'tool': 'apply_patch', 'argv': None, 'cwd': WORKSPACE, 'exit_code': None, 'success': True, 'output_summary': 'Created output/stage_driver.py.'},
    {'call': 5, 'tool': 'exec_command', 'argv': [PYTHON, '-I', '-B', str(OUT / 'stage_driver.py')], 'cwd': str(OUT), 'exit_code': 0, 'output_summary': 'Created project; normal exit 0; controlled rejected input exit 2; JSON/CSV bytes equal; registered content unchanged; three activities done.'},
    {'call': 6, 'tool': 'apply_patch', 'argv': None, 'cwd': WORKSPACE, 'exit_code': None, 'success': True, 'output_summary': 'Corrected an unverified CSV newline assumption in generated recovery prose and generator, preserving the correction record; created finalize.py.'},
    {'call': 7, 'tool': 'apply_patch', 'argv': None, 'cwd': WORKSPACE, 'exit_code': None, 'success': True, 'output_summary': 'Extended final audit to preserve exact executed driver and original recovery draft by reversing the sole documented prose correction; corrected actual tool-call count.'},
    {'call': 8, 'tool': 'exec_command', 'argv': [PYTHON, '-I', '-B', str(OUT / 'finalize.py')], 'cwd': str(OUT), 'exit_code': 0, 'output_summary': 'Verified snapshots and read-only status; wrote report, state answer, full execution and manifest.'},
]
input_files = [INPUT.parent / 'REQUEST.md'] + [p for p in sorted(INPUT.rglob('*')) if p.is_file()]
project_files = [p for p in sorted(ROOT.rglob('*')) if p.is_file()]
output_files = [p for p in sorted(OUT.rglob('*')) if p.is_file() and p.name not in ('execution.json', 'inputs-and-artifacts.json')]
reads = []
for path in input_files + project_files + output_files:
    if path.is_relative_to(INPUT):
        relative, scope = str(path.relative_to(INPUT)), 'input'
    elif path.is_relative_to(ROOT):
        relative, scope = str(path.relative_to(ROOT)), 'project'
    else:
        relative, scope = str(path.relative_to(INPUT.parent)) if path == INPUT.parent / 'REQUEST.md' else str(path.relative_to(OUT)), 'request' if path == INPUT.parent / 'REQUEST.md' else 'output'
    reads.append({'path': str(path), 'relative_path': relative, 'scope': scope, **identity(path), 'read_scope': 'whole file for SHA256 inventory; content interpreted only for text/code/JSON/CSV as described' if path.suffix == '.pdf' else 'whole file, textual/scientific content or audit/hash inspection'})
execution = {'case_id': 'T', 'stage': 'A', 'tool_calls': 8, 'tool_calls_definition': 'Outer functions.exec invocations; nested actual subprocesses recorded separately.', 'outer_calls': outer, 'commands': [entry for entry in outer if entry['argv'] is not None] + initial_execution['commands'] + [{'label': 'final-read-only-status', 'argv': argv, 'cwd': str(ROOT), 'exit_code': status_run.returncode, 'stdout': status_run.stdout, 'stderr': status_run.stderr}], 'network_calls': 0, 'installations': 0, 'agents_called': 0, 'violations': [], 'failures': [{'kind': 'expected_controlled_invalid_input', **load(OUT / 'rejected-execution.json'), 'valid_outputs_preserved': True}], 'unexpected_runtime_failures': [], 'remedies': [{'kind': 'reporting_correction', 'original_statement': 'Recovery prose initially assumed generated CSV CRLF differed from supplied LF.', 'observed_evidence': 'Actual comparison returned table_csv_byte_equal=true.', 'correction': 'Corrected RECOVERY.md and its generator to actual JSON/CSV byte identity; no numerical files were changed.', 'original_recovery_draft': '.research/versions/A-draft/RECOVERY.md', 'executed_driver_copy': 'stage_driver.executed.py', 'preservation_method': 'Reverse the sole explicitly recorded line replacement; no executed command was repeated.'}], 'read_files': reads, 'historical_executed_read_versions': [{'path': str(OUT / 'stage_driver.py'), 'at_outer_call': 5, 'sha256': hashlib.sha256(driver_executed).hexdigest(), 'bytes': len(driver_executed), 'exact_content_preserved_at': str(OUT / 'stage_driver.executed.py')}], 'read_recording_limits': 'Standard-library implementation modules and operating-system process startup are runtime dependencies, not scientific material reads. Audit execution.json and inputs-and-artifacts.json omit self-hashes to avoid recursive checksums; execution is hashed by the separate manifest.', 'written_paths': [str(p) for p in sorted(ROOT.rglob('*')) if p.is_file()] + [str(p) for p in sorted(OUT.rglob('*')) if p.is_file()] + [str(OUT / 'execution.json'), str(OUT / 'inputs-and-artifacts.json')], 'settings': {'effective_model': None, 'temperature': None, 'seed': None, 'token_usage': None, 'token_budget': None, 'system_context_limit': None}, 'report_unicode_characters': len(report), 'project_authority': '.research/state.json', 'raw_material_distribution': 'Private local cache only; original PDF is not authorized for public repository redistribution.'}
execution['written_paths'] = sorted(set(execution['written_paths']))
save(OUT / 'execution.json', execution)
inventory = {'case_id': 'T', 'stage': 'A', 'input_root': str(INPUT), 'project_root': str(ROOT), 'output_root': str(OUT), 'inputs': [{'relative_path': str(p.relative_to(INPUT)) if p.is_relative_to(INPUT) else '../REQUEST.md', **identity(p)} for p in input_files], 'project_artifacts': [{'relative_path': str(p.relative_to(ROOT)), **identity(p)} for p in sorted(ROOT.rglob('*')) if p.is_file()], 'outputs': [{'relative_path': str(p.relative_to(OUT)), **identity(p)} for p in sorted(OUT.rglob('*')) if p.is_file() and p.name != 'inputs-and-artifacts.json'], 'self_hash_exclusion': 'This manifest excludes its own checksum to avoid recursion.', 'non_distribution_scope': 'Original PDF/CSV only for private research cache per supplied source identities. No public repository redistribution; distribute identities and derived project results instead.', 'mtime_policy': 'Directory mtime is not a scientific content version.'}
save(OUT / 'inputs-and-artifacts.json', inventory)
print(json.dumps({'report': str(OUT / 'report.md'), 'state_answer': str(OUT / 'state-answer.json'), 'execution': str(OUT / 'execution.json'), 'inventory': str(OUT / 'inputs-and-artifacts.json'), 'project': str(ROOT), 'tool_calls': 8, 'report_unicode_characters': len(report), 'snapshots_verified': snapshot_checks, 'status_exit': status_run.returncode}, ensure_ascii=False, indent=2))
