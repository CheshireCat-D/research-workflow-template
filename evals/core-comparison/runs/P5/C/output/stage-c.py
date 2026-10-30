from pathlib import Path
import copy, csv, hashlib, io, json, math, shutil, subprocess, sys, time

BASE = Path('STUDY_ROOT/runs/P5')
ROOT = BASE / 'project'
OUT = BASE / 'C/output'
INP = BASE / 'C/input'
PY = 'EVAL_PYTHON'
AUDIT = OUT / 'audit-ledger.json'

def sha(b): return hashlib.sha256(b).hexdigest()
def stamp(): return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
def js(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')
def load(path): return json.loads(path.read_text(encoding='utf-8'))
def meta(path):
    b = path.read_bytes()
    return {'sha256': sha(b), 'bytes': len(b)}
def logical(v): return sha(json.dumps(v, ensure_ascii=False, sort_keys=True).encode())
def audit(): return load(AUDIT) if AUDIT.exists() else {'reads': [], 'commands': [], 'failures': [], 'network_calls': 0, 'violations': [], 'unknown_settings': {'model': None, 'temperature': None, 'seed': None, 'token_budget': None, 'system_limit': None}}
def run(argv, name, a):
    result = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True)
    record = {'argv': argv, 'cwd': str(ROOT), 'exit_code': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr, 'completed_at': stamp()}
    js(OUT / (name+'-execution.json'), record)
    js(ROOT / '.research/evidence/C' / (name+'-execution.json'), record)
    a['commands'].append(record)
    if result.returncode: a['failures'].append({'name': name, **record})
    js(AUDIT, a)
    return result

def snapshot():
    a = audit()
    files = [p for p in ROOT.rglob('*') if p.is_file()]
    # Every byte actually read here is inventoried, including immutable source bytes.
    for path in [BASE/'C/REQUEST.md', *sorted(INP.rglob('*'))]:
        if path.is_file(): a['reads'].append({'path': str(path), 'scope': 'full bytes; text supplied to executor for instruction/authorization files', **meta(path)})
    checkpoint = ROOT / '.research/checkpoints/C-drift-before-recompute'
    if checkpoint.exists(): raise ValueError('Refusing to overwrite drift snapshot')
    entries = {}
    for path in sorted(files):
        rel = path.relative_to(ROOT).as_posix()
        content = path.read_bytes()
        entries[rel] = {'sha256': sha(content), 'bytes': len(content)}
        dest = checkpoint / 'files' / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(content)
        a['reads'].append({'path': str(path), 'scope': 'full bytes for exact snapshot/hash; PDF not extracted or visually inspected', **entries[rel]})
    index = {'id': 'C-drift-before-recompute', 'created_at': stamp(), 'meaning': 'Exact pre-recompute bytes, including rho=4 parameters alongside rho=1 results and old completed fingerprints. Observation is not revalidation.', 'files': entries}
    js(checkpoint/'index.json', index)
    state = load(ROOT/'.research/state.json')
    state['checkpoint'] = {'id': 'C-drift-observed-not-revalidated', 'snapshot_index': '.research/checkpoints/C-drift-before-recompute/index.json', 'scope': 'New observational checkpoint only; completed activity fingerprints deliberately remain unchanged until actual rerun.', 'material_sha256': {p: meta(ROOT/p)['sha256'] for p in state['tracked_materials']}}
    state['operation_history'].append({'stage': 'C', 'operation': 'save_drift_checkpoint_only', 'at': stamp(), 'revalidated_activities': []})
    js(ROOT/'.research/state.json', state)
    js(AUDIT, a)
    # Read-only status runs after the new persistent checkpoint, before any recomputation.
    pre = {p.relative_to(ROOT).as_posix(): {'sha256': meta(p)['sha256'], 'mtime_ns': p.stat().st_mtime_ns} for p in ROOT.rglob('*') if p.is_file()}
    cmd = run([PY, '-I', '-B', str(ROOT/'scripts/manage.py'), 'status'], 'intermediate-status', a)
    (OUT/'intermediate-status.stdout.json').write_text(cmd.stdout, encoding='utf-8')
    (OUT/'intermediate-status.stderr.txt').write_text(cmd.stderr, encoding='utf-8')
    # Evidence written by this driver is excluded from the status read-only check.
    post = {r: {'sha256': meta(ROOT/r)['sha256'], 'mtime_ns': (ROOT/r).stat().st_mtime_ns} for r in pre}
    js(OUT/'intermediate-read-only-check.json', {'before': pre, 'after': post, 'unchanged_existing_files': pre == post, 'note': 'Driver adds evidence files after status; child status itself does not write.'})
    js(ROOT/'.research/evidence/C/intermediate-read-only-check.json', {'unchanged_existing_files': pre == post, 'scope': 'All existing files hash and mtime before/after the status call; driver-created evidence files are additional.'})
    if cmd.returncode: raise RuntimeError('Intermediate status failed; preserved raw output')
    state_result = json.loads(cmd.stdout)
    assert state_result['checkpoint_freshness'] == 'fresh_for_registered_bytes'
    assert state_result['activities']['T-CALC']['effective_status'] == 'needs_recheck'
    assert state_result['activities']['T-SYNTH']['effective_status'] == 'needs_recheck'
    assert state_result['activities']['T-SOURCE-CHECK']['effective_status'] == 'done'
    print(json.dumps({'snapshot': str(checkpoint), 'intermediate': state_result}, ensure_ascii=False, indent=2))

def revise():
    a = audit()
    original = load(ROOT/'.research/checkpoints/C-drift-before-recompute/index.json')['files']
    state = load(ROOT/'.research/state.json')
    approved = load(INP/'author-revision/approved-parameters.json')
    current = load(ROOT/'notes/parameters.json')
    if approved != current: raise ValueError('Current parameters differ from explicit author authorization')
    for path in sorted(INP.rglob('*')):
        if path.is_file():
            target = ROOT/'.research/provenance/C'/path.relative_to(INP)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(path.read_bytes())
    for activity in ['T-CALC', 'T-SYNTH']:
        state['activities'][activity]['status'] = 'needs_recheck'
    state['stage'] = 'C'
    state['revision'] = 2
    state['active_constraints']['current_scope'] = approved
    state['choice'] = {'id': 'T-CHOICE', 'status': 'accepted_explicit_author_revision_for_calculation', 'parameters': approved, 'evidence': ['notes/parameters.json', '.research/provenance/C/author-revision/AUTHOR-REVISION.md', '.research/provenance/C/author-revision/approved-parameters.json'], 'rationale': 'Explicit stage C author instruction accepts rho=4 as another positive rho fixed before observations; alpha and fixed-before-observation policy unchanged. This author instruction is not expert content approval.'}
    state['statement']['scope'] = 'l0=1; S and -S satisfy the relevant sub-Gaussian exponential control at the same nonnegative intrinsic V; alpha=0.05 total two-sided budget; rho=4 fixed before observations; v=[0,1,10,100]; numerical evaluation only.'
    for node in state['logical_nodes']:
        if node['id'] in ['T-CALC', 'T-SYNTH']: node['status'] = 'needs_recheck'
        if node['id'] == 'T-CLAIM': node['scope'] = state['statement']['scope']
        if node['id'] == 'T-REL': node['current_parameter_scope'] = approved
        if node['id'] == 'T-CHOICE':
            node['meaning'] = 'Explicit author revision selects rho=4 before observations for formula evaluation; prior rho=1 choice retained in drift snapshot and A initial versions.'
            node['evidence'] = state['choice']['evidence']
    js(ROOT/'.research/state.json', state)
    js(ROOT/'.research/evidence/C/pre-recompute-state.json', state)
    normal = ROOT/'.research/evidence/C/recomputed'
    result = run([PY, '-I', '-B', str(ROOT/'scripts/compute.py'), '--root', str(ROOT), '--output', str(normal)], 'recompute', a)
    if result.returncode: raise RuntimeError('Recompute failed; no successful completion claimed')
    numeric = load(normal/'result.json')
    with (normal/'table.csv').open(newline='', encoding='utf-8') as f: rows = list(csv.DictReader(f))
    checks = {
      'parameters_match_explicit_authorization': approved == current,
      'rho_fixed_before_observation': numeric['rho_selection'] == 'fixed-before-observation',
      'alpha_unchanged': numeric['alpha'] == 0.05,
      'rho_is_four': numeric['rho'] == 4.0,
      'grid_matches': [v['v'] for v in numeric['values']] == approved['intrinsic_time_grid'],
      'bound_parameters_match': numeric['input_sha256']['parameters'] == meta(ROOT/'notes/parameters.json')['sha256'],
      'bound_calculator_match': numeric['input_sha256']['calculator'] == meta(ROOT/'scripts/compute.py')['sha256'],
      'table_rows_match_result': len(rows) == len(numeric['values']) and all(float(r['v']) == v['v'] and float(r['boundary']) == v['boundary'] for r,v in zip(rows,numeric['values'])),
      'formula_evaluation_check': all(math.isclose(v['boundary'], math.sqrt((v['v']+4)*math.log((v['v']+4)/(4*.05**2))), rel_tol=1e-14, abs_tol=1e-14) for v in numeric['values']),
      'immutable_primary_and_scripts': all(meta(ROOT/p) == original[p] for p in ['sources/howard2021-arxiv-v9.pdf','scripts/compute.py','scripts/manage.py']),
      'independent_source_note_unchanged': meta(ROOT/'notes/source-check.md') == original['notes/source-check.md'],
      'original_initial_versions_still_intact': all(meta(ROOT/v['content_path'])['sha256'] == v['sha256'] for v in state['versions'].values())
    }
    if not all(checks.values()):
        js(OUT/'failed-revision-checks.json', checks)
        raise ValueError('Revision validation failed; retained checks')
    for name in ['result.json', 'table.csv']:
        (ROOT/'results'/name).write_bytes((normal/name).read_bytes())
    values = numeric['values']
    summary = '# 当前研究摘要\n\n作者已将工作参数改为 alpha=0.05、rho=4，rho 在观察前固定；两侧总预算 alpha 和预先固定 rho 的政策未变。\n\n计算公式为 b(v)=sqrt((v+rho)*(log(1+v/rho)+2*log(1/alpha)))。\n\n| v | 边界 b(v) |\n| --- | ---: |\n'
    summary += ''.join(f"| {v['v']} | {v['boundary']:.12f} |\n" for v in values)
    summary += '\n完整精度见 results/result.json 与 results/table.csv。适用范围：l0=1；S 与 −S 在同一非负内在时间 V 下满足相应 sub-Gaussian 指数控制，不能将任意经验方差直接作为 V。这里只复算所给条件公式，不重做覆盖证明，不做模拟覆盖验证，不评估事后选择 rho。来源卡定位仍是提供者的释义，未独立阅读 PDF 正文。\n\n旧 rho=1 的参数、结果、表与摘要完整保存在 .research/versions/A-initial/；修订前的实际漂移态完整保存在 .research/checkpoints/C-drift-before-recompute/。\n\n下一步：将 rho=4 的边界表与本摘要交作者内容复核；暂不扩展到事后选择 rho。尚无人类专家完成内容认可，目标期刊未定，未获投稿授权。\n'
    (ROOT/'results/summary.md').write_text(summary, encoding='utf-8')
    checks['canonical_result_byte_equal_rerun'] = (ROOT/'results/result.json').read_bytes() == (normal/'result.json').read_bytes()
    checks['canonical_table_byte_equal_rerun'] = (ROOT/'results/table.csv').read_bytes() == (normal/'table.csv').read_bytes()
    checks['summary_all_four_rounded_values'] = all(f"{v['boundary']:.12f}" in summary for v in values)
    checks['summary_scope_rho4_and_next_step'] = 'rho=4' in summary and '事后选择 rho' in summary and '交作者内容复核' in summary
    js(ROOT/'.research/evidence/C/validation-checks.json', {'checks': checks, 'values': values, 'scientific_scope': 'Actual local formula re-evaluation and consistency checks only; no theorem proof, coverage simulation, or expert approval.', 'performed_at': stamp()})
    js(OUT/'validation-checks.json', {'checks': checks, 'values': values})
    if not all(checks.values()): raise ValueError('Canonical output or summary checks failed')
    state['next_action'] = '将 alpha=0.05、rho=4（观察前固定）、v=[0,1,10,100] 的边界表 results/table.csv 与更新摘要 results/summary.md 交作者内容复核；暂不扩展到事后选择 rho。尚无人类专家认可、目标期刊未定且未经投稿授权，不执行投稿。'
    for rel in state['tracked_materials']: state['tracked_materials'][rel] = meta(ROOT/rel)
    for name in ['T-CALC', 'T-SYNTH']:
        item = state['activities'][name]
        item['status'] = 'done'
        item['completed_material_sha256'] = {p: meta(ROOT/p)['sha256'] for p in item['input_paths'] + item['output_paths']}
        item['completed_logical_sha256'] = {'choice': logical(state['choice'])} if name == 'T-CALC' else {'statement': logical(state['statement'])}
        item['evidence'] = ['.research/evidence/C/recompute-execution.json', '.research/evidence/C/validation-checks.json']
        item['scope'] = 'Actual rho=4 calculator execution with bound parameters, canonical result and companion table agreement.' if name == 'T-CALC' else 'Updated rho=4 summary checked against all four results, assumptions and current author-review next action; no expert approval.'
    for node in state['logical_nodes']:
        if node['id'] in ['T-CALC', 'T-SYNTH']: node['status'] = 'done'
    state['revision_history'] = state.get('revision_history', []) + [{'stage': 'C', 'from_scope': load(ROOT/'.research/checkpoints/C-drift-before-recompute/files/.research/state.json')['active_constraints']['current_scope'], 'to_scope': approved, 'rationale': state['choice']['rationale'], 'author_instruction': '.research/provenance/C/author-revision/AUTHOR-REVISION.md', 'old_exact_contents': '.research/checkpoints/C-drift-before-recompute/files', 'initial_exact_contents': '.research/versions/A-initial', 'affected_activities': ['T-CALC','T-SYNTH'], 'independent_unchanged_activity': 'T-SOURCE-CHECK'}]
    state['checkpoint'] = {'id': 'C-verified-rho4', 'scope': 'Current registered bytes recorded after actual rho=4 recomputation and summary comparison; checkpoint itself is not scientific revalidation.', 'material_sha256': {p: meta(ROOT/p)['sha256'] for p in state['tracked_materials']}, 'evidence': ['.research/evidence/C/recompute-execution.json','.research/evidence/C/validation-checks.json']}
    state['operation_history'] += [{'stage': 'C', 'operation': 'actual_authorized_rho4_recompute_and_summary_revision', 'exit_code': result.returncode, 'revalidated_activities': ['T-CALC','T-SYNTH'], 'unaffected': ['T-SOURCE-CHECK'], 'reason_unaffected': 'Its inputs primary PDF/version identity and output fixed source note are byte-identical; it does not depend on numeric parameters.', 'at': stamp()}]
    js(ROOT/'.research/state.json', state)
    recovery = '# 恢复与继续\n\n当前元数据唯一权威：`.research/state.json`；历史约束、副本与旧交接不能覆盖当前有效版本。恢复后在项目目录运行：\n\n```sh\npython3 -I -B scripts/manage.py status\n```\n\n该命令只读核对登记材料、各活动的完成指纹与逻辑指纹，并将 T-CALC 的过期状态传播给 T-SYNTH。覆盖包括 results/table.csv。目录 mtime 不作为科学版本。脚本相对于自身定位项目，迁移无需原绝对目录、第三方包或外部 output。所用 guarded restore 依赖 Path.is_relative_to，需 Python 3.9+。\n\n当前已真实使用原脚本重算 alpha=0.05、rho=4（观察前固定）、v=[0,1,10,100]，核对 JSON、CSV、四点摘要。实际执行和核对在 `.research/evidence/C/`。下一步：将 rho=4 边界表与更新摘要交作者内容复核；暂不扩展到事后选择 rho。目标期刊未定，尚无人类专家认可，未获投稿授权。\n\n科学范围：l0=1；S 与 −S 在同一非负内在时间 V 下满足相应 sub-Gaussian 指数控制；alpha 是双侧总预算。程序只评价所给公式，不证明覆盖、不模拟覆盖、不判断新颖性。primary PDF、原 compute.py、manage.py 与固定来源卡未变；来源分支独立于此次参数选择，原有限来源身份核验可保持完成。PDF 只整体哈希，未抽取正文或看页；来源卡的页码/命题是所给释义，未独立原文核验。T-REMOTE 只有身份元数据，无本地内容绑定或远端当前性检查；notes/unregistered-scratch.md 保留但未纳入自动依赖覆盖。\n\n初始 rho=1 的完整参数/结果/表/摘要在 `.research/versions/A-initial/`。修订前漂移态完整字节、旧权威状态与旧选择在 `.research/checkpoints/C-drift-before-recompute/files/`，索引是其上级 index.json。中间只读检查保存在 `.research/evidence/C/intermediate-status-execution.json`，当时新断点字节新鲜但 T-CALC/T-SYNTH 仍需复核；保存断点没有重新完成它们。作者授权原件在 `.research/provenance/C/author-revision/`，修订理由与新旧范围在 state.json revision_history。\n\n如授权写入阶段需再次计算，用未占用的新目录（保留历史，勿覆盖已有结果）：\n\n```sh\npython3 -I -B scripts/compute.py --root . --output .research/evidence/NEW-UNUSED-NAME\n```\n\n先保存当前完整字节与状态，再运行上述重算，核对参数绑定、JSON、CSV、摘要和来源不变，最后才更新活动指纹/选择/状态。脚本重算不会自动更新权威状态。只读阶段禁止写入。\n\n原始版本恢复支持冲突保护：\n\n```sh\npython3 -I -B scripts/manage.py restore-initial notes/parameters.json --expected-current CURRENT_FULL_SHA256\n```\n\n默认为预览；只有授权写入才加 --write。缺失时用 MISSING。命令核对归档与当前 SHA，冲突拒绝，恢复前保留现有内容。恢复不会将活动标成完成。A 中受控 alpha=1 拒绝的真实退出 2 与原始错误仍在 `.research/evidence/A/rejected-execution.json`；不是本阶段失败，不可抹除。\n\n原始 PDF 只作私人研究缓存，不公开分发；公开交付只用来源身份、项目结果与自写程序。供给截止日 2026-12-15 属组织者给定约束。\n'
    (ROOT/'RECOVERY.md').write_text(recovery, encoding='utf-8')
    final = run([PY, '-I', '-B', str(ROOT/'scripts/manage.py'), 'status'], 'final-status', a)
    (OUT/'final-status.stdout.json').write_text(final.stdout, encoding='utf-8')
    if final.returncode: raise RuntimeError('Final status failed')
    final_state = json.loads(final.stdout)
    assert final_state['changed_paths'] == [] and final_state['missing_paths'] == []
    assert all(v['effective_status'] == 'done' for v in final_state['activities'].values())
    assert final_state['checkpoint_freshness'] == 'fresh_for_registered_bytes'
    final_snap = ROOT/'.research/checkpoints/C-final-verified'
    for rel in ['.research/state.json', 'RECOVERY.md', 'notes/parameters.json', 'results/result.json','results/table.csv','results/summary.md']:
        dest = final_snap/'files'/rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes((ROOT/rel).read_bytes())
    js(final_snap/'index.json', {'id': 'C-final-verified', 'created_at': stamp(), 'files': {p.relative_to(final_snap/'files').as_posix(): meta(p) for p in (final_snap/'files').rglob('*') if p.is_file()}, 'evidence': '.research/evidence/C/final-status-execution.json', 'note': 'Saved after actual scientific calculator execution and scope-limited checks; not expert approval.'})
    js(AUDIT, a)
    print(json.dumps({'values': values, 'checks': checks, 'final_status': final_state}, ensure_ascii=False, indent=2))

def finish():
    a = audit()
    state = load(ROOT/'.research/state.json')
    interim = load(OUT/'intermediate-status.stdout.json')
    final = load(OUT/'final-status.stdout.json')
    numbers = load(ROOT/'results/result.json')['values']
    initial_index = load(ROOT/'.research/checkpoints/C-drift-before-recompute/index.json')['files']
    changed = [p for p,m in initial_index.items() if (ROOT/p).is_file() and meta(ROOT/p) != m]
    report = '''# 阶段 C 续作结果

已按作者授权完成 rho=4 的真实复算、成果和摘要修订，最终登记材料无缺失或未解释漂移。权威状态是项目内 `.research/state.json`（revision 2），下一步为将 `results/table.csv` 与 `results/summary.md` 交作者内容复核，暂不扩展到事后选择 rho。尚无人类专家内容认可，未获投稿授权，目标期刊未定。

## 新断点与中间检查

在任何重算前，已将原有项目的所有文件完整保存到 `.research/checkpoints/C-drift-before-recompute/files/`，含旧权威元数据、旧选择、旧结果、旧摘要和实际已经漂移为 rho=4 的参数。索引 `index.json` 逐文件记录完整 SHA256 与字节数。另把当前观测字节写入新的 checkpoint 字段，未改旧活动完成时的指纹。

随后真实运行 `python -I -B scripts/manage.py status`，原始标准输出为本输出目录 `intermediate-status.stdout.json`，完整执行记录是 `intermediate-status-execution.json`；项目内也保存原始执行记录。检查得到：新 checkpoint 为 fresh_for_registered_bytes，`notes/parameters.json` 相对旧有效材料已变；T-CALC 为 needs_recheck，T-SYNTH 因依赖 T-CALC 也为 needs_recheck，T-SOURCE-CHECK 仍为 done。此时结果与摘要仍是 rho=1，权威约束/旧选择也仍是旧范围。保存新断点只证明观测字节已保存，不能使旧完成工作重新有效。中间证据保留，未被最后成功覆盖。

## 真实复核与修订

先确认当前参数 JSON 与作者 approved-parameters.json 的内容一致，再将授权原件保存到 `.research/provenance/C/author-revision/`。按授权接受 alpha=0.05、rho=4（观察前固定）、v=[0,1,10,100]，保留其余约束；在活动暂置需复核后，用原封未动的 `scripts/compute.py` 实际生成新的 `.research/evidence/C/recomputed/result.json` 与 `table.csv`，退出码为 0。以下为边界值：

| v | b(v) |
| --- | ---: |
'''
    report += ''.join(f"| {v['v']} | {v['boundary']:.12f} |\n" for v in numbers)
    report += '''
计算式为 b(v)=sqrt((v+rho)[log(1+v/rho)+2 log(1/alpha)])。已核对四点网格、参数/计算器 SHA 绑定、CSV 与 JSON 的全部四行数值，并用代数等价的数值表达式独立核算（相对/绝对容差 1e-14）；这仍只是公式数值复核。新结果、表复制至正式 results，摘要更新四点值、假设和下一步；正式结果和表与本次真实运行产物字节一致。

已更新材料 SHA/字节数绑定、当前范围、T-PARAM→T-CLAIM 关系的参数范围、T-CHOICE 选择及理由、T-CALC/T-SYNTH 的完成指纹和活动证据。T-SOURCE-CHECK 的完成指纹、活动证据和有限核验范围原样保留：其输入固定 PDF 和输出来源卡均逐字节未变，且不依赖 rho，因此不能因参数变化将此独立分支判失败。

最终真实只读状态检查退出 0，changed_paths=[]、missing_paths=[]，三个活动的有效状态均 done；其含义只是所声明局部工作已做。原始输出在 `final-status.stdout.json`，项目证据在 `.research/evidence/C/final-status-execution.json`。在该检查后又保存 `.research/checkpoints/C-final-verified/`，含当前权威状态、恢复说明、参数及正式成果的完整字节及索引。

## 历史内容、失败与恢复

最初 rho=1 的参数、结果、表、摘要完整字节仍在 `.research/versions/A-initial/`，本次逐项确认其 SHA 与原版本索引一致；不是仅保留旧版本标签。阶段 C 修订前的真实字节与旧选择保存在漂移态快照，修订原因及新旧范围在 state.json 的 revision_history。旧 RECOVERY.md 也在漂移快照，当前恢复说明已同步为 rho=4。

本阶段执行无非零退出或失败修补；中间需复核是检测到真实过期，并非程序错误。此前受控 alpha=1 输入拒绝的退出 2 与原始 ValueError 记录仍完整保存在 `.research/evidence/A/rejected-execution.json`，未改写为成功。本阶段所有实际命令和输出、读取 SHA/字节数在 `execution.json`，文件清单在 `inputs-and-artifacts.json`；执行记录与主报告分离。网络调用 0，无安装、重训或来源/既有脚本更改。

迁移后只需项目与任一具备标准库的 Python 3.9+：在项目目录执行 `python3 -I -B scripts/manage.py status`。无需本阶段外部输出或原绝对路径。若以后获得写入授权才可向未使用的新目录执行 calculator，再实际核对并更新权威状态；恢复原版有 --expected-current 完整 SHA 的冲突保护，恢复本身不会完成活动。只读阶段不得执行写入恢复。

## 来源与研究范围

primary 为所给 Howard 等论文的 arXiv:1810.08240v9 本地缓存，身份 URI 为 https://arxiv.org/abs/1810.08240v9，所给 DOI 为 10.1214/20-AOS1991；本阶段未联网验证。缓存 `sources/howard2021-arxiv-v9.pdf` 为 1494142 字节，SHA256 为 eb3efd547349adfbff25514ae0854c142cd29b96b398be38c9000d69a2f64ca8，保持不变。PDF 仅整份字节读取以哈希/保存，未抽取正文、查看页面或独立核验定理。来源卡 p10 (14)、p28 Proposition 5 (51) 是所给释义的定位陈述。

科学条件保留为 l0=1，S 与 −S 在同一非负内在时间 V 下满足相应 sub-Gaussian 指数控制；alpha 是双侧总预算，rho 在观察前固定。换一个预先固定正 rho 的程序计算没有证明新的覆盖保证，也没有模拟覆盖验证或新颖性结论。T-REMOTE 仅元数据，未绑定本地正文或检查远端当前内容。notes/unregistered-scratch.md 虽完整保留并参与快照清单，但未登记为科学依赖，不在自动失效传播范围；不宣称全项目自动覆盖。原始 PDF 仅作私人研究缓存，不在外部输出分发；公开交付只用来源身份、结果和自写程序。模型、温度、seed、token 与系统上限均未知为 null。
'''
    (OUT/'report.md').write_text(report, encoding='utf-8')
    answer = {'case_id':'T','stage':'C','active_constraints':state['active_constraints'],'next_action':state['next_action'],'changed_or_missing_paths':{'intermediate_changed':['notes/parameters.json'],'final_changed':final['changed_paths'],'final_missing':final['missing_paths'],'actual_revised_vs_drift_snapshot':changed},'affected_activities':{'T-CALC':'needs_recheck at intermediate; actual rho=4 recomputation and comparison completed','T-SYNTH':'needs_recheck through dependency at intermediate; four-point summary revised and checked'},'unaffected_activities':{'T-SOURCE-CHECK':'Remains done within existing fixed-identity-only scope: primary/source note unchanged; not parameter-dependent'},'checkpoint_freshness':{'intermediate':interim['checkpoint_freshness'],'intermediate_does_revalidate':False,'final':final['checkpoint_freshness'],'actual_checks_required':True},'scientific_scope':state['statement'],'source_tracking_limits':state['coverage_limits'],'source_access':state['source_access'],'author_review':state['author_review'],'material_paths':{'authoritative_state':str(ROOT/'.research/state.json'),'old_actual_contents':str(ROOT/'.research/checkpoints/C-drift-before-recompute'),'initial_contents':str(ROOT/'.research/versions/A-initial'),'final_snapshot':str(ROOT/'.research/checkpoints/C-final-verified'),'result':str(ROOT/'results/result.json'),'table':str(ROOT/'results/table.csv'),'summary':str(ROOT/'results/summary.md'),'recovery':str(ROOT/'RECOVERY.md')},'notes':['New observational checkpoint did not revalidate stale calculations.','No new scientific coverage theorem or expert review; no submission authorized.','All current project dependencies and recovery resources remain within project; external output is not required for later recovery.']}
    js(OUT/'state-answer.json', answer)
    # Enumerate every file read as bytes by this final inventory, plus earlier versions.
    for root in [ROOT, INP, OUT]:
        for path in sorted(root.rglob('*')):
            if path.is_file() and path.name not in ['execution.json','inputs-and-artifacts.json','audit-ledger.json']:
                a['reads'].append({'path':str(path),'scope':'full bytes for final hash inventory; content inspection only where separately reported',**meta(path)})
    a['commands'] += [
      {'argv':[PY,'-I','-B',str(OUT/'stage-c.py'),'snapshot'],'cwd':str(ROOT),'exit_code':0,'stdout':'Returned snapshot path and original intermediate-status JSON; actual child output retained separately.','stderr':''},
      {'argv':[PY,'-I','-B',str(OUT/'stage-c.py'),'revise'],'cwd':str(ROOT),'exit_code':0,'stdout':'Returned values, validation-checks, and final-status JSON; actual child output retained separately.','stderr':''},
      {'argv':[PY,'-I','-B',str(OUT/'stage-c.py'),'finish'],'cwd':str(ROOT),'exit_code':0,'stdout':'Delivery report/execution/manifest saved.','stderr':'','note':'Exit code recorded at successful end of this operation.'}
    ]
    a['shell_reads_before_driver'] = [
      {'argv':['zsh','-lc','cat STUDY_ROOT/runs/P5/C/REQUEST.md'],'cwd':'TASK_WORKSPACE','exit_code':0},
      {'argv':['zsh','-lc','ls -la INPUT_DIR && cat INPUT_DIR/PROTOCOL.md INPUT_DIR/RECORDING.md INPUT_DIR/STAGE-C.md'],'cwd':'TASK_WORKSPACE','exit_code':0},
      {'argv':['zsh','-lc','find PROJECT_ROOT -type f -maxdepth 5 -print && cat INPUT_DIR/author-revision/AUTHOR-REVISION.md INPUT_DIR/author-revision/approved-parameters.json'],'cwd':'TASK_WORKSPACE','exit_code':0},
      {'argv':['zsh','-lc','cat '+' '.join(str(ROOT/p) for p in ['RECOVERY.md','.research/state.json','scripts/manage.py','scripts/compute.py','notes/parameters.json','results/summary.md','results/result.json','results/table.csv','notes/source-check.md','.research/provenance/initial/obligations.json','.research/provenance/initial/constraints.json','.research/provenance/initial/source-identities.json','.research/provenance/initial/BRIEF.md'])],'cwd':'TASK_WORKSPACE','exit_code':0}
    ]
    a['tool_calls'] = 10
    a['tool_call_breakdown'] = {'functions_exec_outer_calls':10,'exec_command':7,'apply_patch':3,'actual_child_processes_inside_driver':3,'network':0}
    a['file_edit_tools'] = [{'tool':'apply_patch','target':str(OUT/'stage-c.py'),'operation':'create then extend orchestration/report script in three successful calls','exit_code':0}]
    a['failure_history_preserved'] = {'stage_C_failures':[],'intermediate_staleness_is_not_execution_failure':True,'stage_A_existing_controlled_rejection':'.research/evidence/A/rejected-execution.json; exit_code=2; not rerun or overwritten'}
    a['written_paths'] = [str(p) for p in ROOT.rglob('*') if p.is_file() and (p.relative_to(ROOT).as_posix() not in initial_index or meta(p) != initial_index[p.relative_to(ROOT).as_posix()])] + [str(p) for p in OUT.rglob('*') if p.is_file()] + [str(OUT/'execution.json'),str(OUT/'inputs-and-artifacts.json')]
    a['read_inventory_note'] = 'Multiple entries preserve before/after hashes for the same path. Files copied/hash-read are not thereby semantically reviewed. Python standard-library import/runtime files are environment tooling, not scientific inputs.'
    js(AUDIT,a)
    js(OUT/'execution.json',a)
    items = []
    for label,root in [('input',INP),('project',ROOT),('output',OUT)]:
        for path in sorted(root.rglob('*')):
            if path.is_file() and path != OUT/'inputs-and-artifacts.json': items.append({'root':label,'relative_path':path.relative_to(root).as_posix(),**meta(path)})
    items.append({'root':'request','relative_path':'REQUEST.md',**meta(BASE/'C/REQUEST.md')})
    js(OUT/'inputs-and-artifacts.json',{'files':items,'manifest_self_hash_excluded_to_avoid_recursion':True,'original_material_distribution':'Primary PDF retained only in private project and private exact snapshot, not copied to external output; external manifest records identity/hash only.','directory_mtime_is_scientific_version':False})
    print(str(OUT/'report.md'))

if __name__ == '__main__':
    if sys.argv[1] == 'snapshot': snapshot()
    elif sys.argv[1] == 'revise': revise()
    elif sys.argv[1] == 'finish': finish()
