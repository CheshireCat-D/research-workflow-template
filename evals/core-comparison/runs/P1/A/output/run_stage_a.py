import csv
import hashlib
import json
import math
import pathlib
import platform
import shutil
import subprocess
import sys

A = pathlib.Path('STUDY_ROOT/runs/P1/A')
I = A / 'input'
O = A / 'output'
P = A.parent / 'project'
T = pathlib.Path('TOOLKIT_ROOT')
PY = 'EVAL_PYTHON'
commands = []
O.mkdir(exist_ok=True)

def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')

def identity(path):
    b = path.read_bytes()
    return {'sha256': hashlib.sha256(b).hexdigest(), 'bytes': len(b)}

def run(argv, label, expected=0):
    r = subprocess.run([str(x) for x in argv], cwd=P if P.exists() else A, capture_output=True, text=True)
    v = {'label': label, 'argv': [str(x) for x in argv], 'cwd': str(P if P.exists() else A), 'exit_code': r.returncode, 'stdout': r.stdout, 'stderr': r.stderr}
    commands.append(v)
    save(O / 'actual-commands.json', commands)
    print(json.dumps({'label': label, 'exit_code': r.returncode}, ensure_ascii=False), flush=True)
    if r.returncode != expected:
        print(r.stdout, r.stderr, flush=True)
        raise RuntimeError('Unexpected exit in '+label)
    return v

def cli(*args, label, expected=0):
    return run([PY, '-I', '-B', T/'tools/research.py', *args], label, expected)

assert not P.exists(), 'Do not overwrite existing project'
constraints = json.loads((I/'initial/constraints.json').read_text())
manifest = json.loads((I/'initial/MANIFEST.json').read_text())
source_ids = json.loads((I/'initial/source-identities.json').read_text())
input_check = {name: {'actual': identity(I/'initial'/name), 'expected': value} for name,value in manifest['files'].items()}
assert all(x['actual'] == x['expected'] for x in input_check.values())
save(O/'input-manifest-verification.json', input_check)

cli('init', '--output', P, '--title', '固定精度正态混合边界的可恢复数值核对', '--interest', constraints['interest'], '--language', 'zh', '--connect-skills', label='initialize-and-connect')
argv = ['configure', '--root', P, '--interest', constraints['interest'], '--deadline', constraints['deadline'], '--budget', constraints['budget'], '--venue', constraints['venue']]
for cap in constraints['available_capabilities']:
    argv += ['--add-capability', cap]
cli(*argv, label='persist-configuration')

for child in (I/'initial/project_payload').iterdir():
    if child.is_dir():
        shutil.copytree(child, P/child.name, dirs_exist_ok=True)
    else:
        shutil.copy2(child, P/child.name)
for name in ['BRIEF.md','constraints.json','obligations.json','source-identities.json','MANIFEST.json']:
    dest = P/'provenance/initial'/name
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(I/'initial'/name,dest)
for name in ['PROTOCOL.md','RECORDING.md','STAGE-A.md']:
    shutil.copy2(I/name, P/'provenance/initial'/name)

snap_paths = ['notes/parameters.json','results/result.json','results/table.csv','results/summary.md']
snapshot = {}
for rel in snap_paths:
    dst = P/'history/stage-a-initial'/rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(P/rel,dst)
    snapshot[rel] = {'snapshot_path': str(dst.relative_to(P)), **identity(dst)}
save(P/'history/stage-a-initial/manifest.json', {'purpose':'Exact recoverable initial bytes; retain before future revision', 'files':snapshot})

with (P/'.gitignore').open('a',encoding='utf-8') as f:
    f.write('\n# Supplied original source is a private research cache only.\nsources/\n')

canonical_before = {x: identity(P/x) for x in snap_paths}
normal = run([PY,'-I','-B',P/'scripts/compute.py','--root',P,'--output',O/'validation-normal'], 'valid-current-parameters')
actual = json.loads((O/'validation-normal/result.json').read_text())
canonical = json.loads((P/'results/result.json').read_text())
assert actual == canonical
def rows(path):
    with path.open(newline='',encoding='utf-8') as f:
        return [{'v':int(r['v']),'boundary':float(r['boundary'])} for r in csv.DictReader(f)]
assert rows(O/'validation-normal/table.csv') == rows(P/'results/table.csv') == actual['values']
summary = (P/'results/summary.md').read_text()
assert all(s in summary for s in ['alpha=0.05','rho=1','观察前固定','9.606401928869','不是新证明'])
assert math.isclose(actual['values'][0]['boundary'], math.sqrt(2*math.log(20)), rel_tol=1e-15)
independent_form = [{'v': x['v'], 'boundary': math.sqrt((x['v']+1)*math.log((x['v']+1)/(0.05**2)))} for x in actual['values']]
assert all(math.isclose(x['boundary'], y['boundary'], rel_tol=1e-14, abs_tol=1e-14) for x,y in zip(actual['values'],independent_form))
rejected = run([PY,'-I','-B',P/'scripts/compute.py','--root',P,'--spec',P/'notes/rejected-parameters.json','--output',O/'validation-rejected'], 'controlled-invalid-alpha', expected=2)
assert json.loads(rejected['stderr'])['message'] == 'Require 0<alpha<1, rho>0 and finite nonnegative intrinsic times'
assert not (O/'validation-rejected').exists()
canonical_after = {x: identity(P/x) for x in snap_paths}
assert canonical_after == canonical_before
save(O/'valid-output-preservation.json',{'before':canonical_before,'after':canonical_after,'unchanged':True,'rejected_output_exists':False})

proof = {
    'case_id':'T','stage':'A','operator':'AI agent in this execution; no human review',
    'parameters':json.loads((P/'notes/parameters.json').read_text()),
    'formula':'sqrt((v+rho)*(log(1+v/rho)+2*log(1/alpha)))',
    'conditions':'scalar l0=1; S and -S controlled for the same nonnegative intrinsic time V; alpha is total two-sided budget; rho fixed before observation',
    'normal_execution':normal,'invalid_execution':rejected,
    'numeric_values':actual['values'],
    'comparisons':{'result_json_semantic_equal':True,'result_json_bytes_equal':identity(P/'results/result.json')==identity(O/'validation-normal/result.json'),'csv_numeric_rows_equal':True,'csv_bytes_equal':identity(P/'results/table.csv')==identity(O/'validation-normal/table.csv'),'csv_byte_difference':'Supplied table uses LF; csv module generated CRLF. Rows and floating point values exactly match.','summary_parameters_and_rounded_v10_checked':True,'v0_special_case_checked':True,'equivalent_log_formula_checked_tolerance':{'relative':1e-14,'absolute':1e-14}},
    'canonical_before':canonical_before,'canonical_after_invalid':canonical_after,'canonical_unchanged':True,
    'controlled_failure_scope':'Intentionally invalid alpha=1 input. Not a failure of scientific analysis and not evidence about coverage.',
    'source_access':{'T-SRC':'metadata-only: complete local bytes hashed; PDF header and raw metadata inspected; supplied version identity matched by full SHA; no mathematical pages or theorem proof read','T-REMOTE':'metadata-only supplied identity, no local copy or live content check'},
    'source_identity':source_ids,
    'source_hash':identity(P/'sources/howard2021-arxiv-v9.pdf'),
    'scientific_scope':'Reproduction of supplied deterministic calculator and bounded arithmetic checks for the four initial parameters only. No new proof, coverage simulation, novelty assessment, human expert approval, or submission.',
    'environment':{'python':sys.version,'platform':platform.platform(),'stdlib_only':True,'network_calls':0,'randomness':'deterministic; no random generator used','model':None,'temperature':None,'model_seed':None,'token_usage':None}
}
save(P/'notes/stage-a-validation.json', proof)
shutil.copytree(O/'validation-normal',P/'validation/stage-a/normal')
save(P/'validation/stage-a/commands.json', [normal,rejected])
save(P/'validation/stage-a/preservation.json',json.loads((O/'valid-output-preservation.json').read_text()))
save(P/'provenance/initial/access-manifest.json',{'input_manifest_verified':input_check,'actual_read_scope':proof['source_access'],'private_originals_do_not_redistribute':['sources/howard2021-arxiv-v9.pdf']})

next_action = '先运行项目内恢复检查并读取当前参数、结果和表；若身份与活动仍新鲜，将 alpha=0.05、rho=1（观察前固定）、v=[0,1,10,100] 的已核对表及摘要交作者讨论。若文件或登记变化，先定位并实质复核 T-CALC/T-SYNTH，再显式更新登记；未经内容复核不投稿。'
recovery = '''# 恢复说明

唯一权威配置为 project.json；唯一权威登记、版本和检查点为 records/registry.json。本文和 provenance/initial 中的材料只保留历史及原始约束，不能覆盖更晚有效登记。

从项目根目录执行（Python 3.11+，仅标准库）：

```sh
python3 -I -B _rw-runtime/tools/research.py resume --root .
python3 -I -B _rw-runtime/tools/connect_skills.py check --installed-only --root .
```

恢复命令只读且不执行登记里的命令。先读实际 configuration、activities、checkpoint 和 findings。未完成或过期时先定位变化，再复核；保存新检查点不能消除旧活动的失效。更新同一 ID 前使用 show 读取当前 envelope.version，register --replace --expected-version N，禁止手工改权威 JSON。

原始参数为 alpha=0.05、rho=1（观察前固定）、v=[0,1,10,100]。当前数值为 2.4477468306808166、3.6563948713638483、9.606401928868575、32.73018624234933。来源卡是组织者释义；本次只核对固定材料身份、卡片文字和数值，没有读取论文数学页或证明覆盖。

本阶段实际试算与失败原文：notes/stage-a-validation.json 和 validation/stage-a/。无效 alpha=1 退出2，未生成试算输出目录，原有效四文件完整SHA未变。该试算不代表研究失败。

重新计算时从项目根调用 scripts/compute.py --root . --output 一个尚不存在的新目录，使用 python3 -I -B。比对 JSON 内容、table.csv 数值行及 summary 参数与舍入值；正常输出 CSV 的CRLF与原表LF差别无数值含义。

history/stage-a-initial 下保存 notes/parameters.json、results/result.json、results/table.csv、results/summary.md 的完整初始字节及SHA/长度。任何修订前先保留当前内容和理由；先比较历史再决定恢复，不要盲目覆盖当前工作。大型PDF仅保留工作缓存一次。

完整给定约束和逻辑义务见 provenance/initial/constraints.json、obligations.json、BRIEF.md、source-identities.json。截止日期 2026-12-15 是任务作者提供的约束；离线标准库、禁止新数据和模型重拟合、中文、目标期刊未定；无人类专家批准，无外部投稿授权。原PDF只作私有研究缓存，sources/已排除提交，不得再分发原件。

覆盖范围：T-REMOTE 只有来源身份，无本地内容绑定，也没有当前远端核验。notes/unregistered-scratch.md 明确未登记，不属于自动变更覆盖；来源URL不是内容绑定。工具状态新鲜不等于科学认证。

下一步：'''+next_action+'\n'
(P/'RECOVERY.md').write_text(recovery,encoding='utf-8')

batch=[]
def add(kind, **record):
    batch.append({'kind':kind,'record':record})
primary=source_ids['primary']; remote=source_ids['source_only']
add('source',id='T-SRC',title=primary['title'],locator=primary['uri'],version=primary['version'],content_access='metadata-only',rights='restricted',limitations='No live remote check or mathematical page reading; identity checked against supplied full local hash.',notes='DOI '+primary['doi']+'; private cache, do not redistribute original PDF.')
add('source',id='T-REMOTE',title=remote['title'],locator=remote['uri'],version=remote['version'],content_access='metadata-only',limitations=remote['tracking_limit'])
add('evidence',id='T-RAW',type='immutable-source-cache',description='Supplied fixed primary PDF; exact bytes matched initial manifest.',provenance='Supplied source-identities.json and MANIFEST.json, not fetched remotely.',location={'kind':'local','path':'sources/howard2021-arxiv-v9.pdf'},source_ids=['T-SRC'],limitations='Only file identity, header/raw metadata; no theorem-content audit.')
add('evidence',id='T-PARAM',type='author-parameters',description='Current alpha=0.05 rho=1 and intrinsic time grid [0,1,10,100]; rho fixed before observation.',provenance='Benchmark author initial working parameters, separate from original paper.',location={'kind':'local','path':'notes/parameters.json'})
add('statement',id='T-CLAIM',text=constraints['interest'],type='interpretive',scope='Current declared parameters and supplied sources only; scalar l0=1; two-sided alpha total; same V for S and -S.',assessment={'status':'supported-in-scope','scope':'Only supplied calculator numerical reproduction on v=[0,1,10,100], alpha=.05 rho=1.','rationale':'Fresh run exactly matches canonical JSON and numeric CSV; equivalent-form and v=0 arithmetic checks; underlying coverage theorem not assessed.','reviewer':'AI agent in stage A'},formal_verification={'status':'not-started','scope':'No formal or new manual theorem proof performed.','tool':'none'})
add('relation',id='T-REL',statement_id='T-CLAIM',evidence_id='T-PARAM',relation='qualifies',rationale='Author parameters restrict the numerical claim; file registration is not a mathematical proof.',scope='Current fixed alpha, rho selection and four intrinsic-time points.')
add('decision',id='T-CHOICE',choice='Use the supplied initial alpha=.05 rho=1 fixed before observation, grid [0,1,10,100].',rationale='Initial benchmark-author choice; task authorizes reproducing these supplied parameters.',responsible='Benchmark author, as identified in supplied initial material; recorded by AI agent.',decided_at='Original decision timestamp not supplied',evidence_refs=['T-PARAM'],revisit_when='Explicit author parameter revision; preserve previous content and rationale.',notes='No invented human expert approval.')
add('artifact',id='T-CODE',type='scientific-calculator',description='Unmodified supplied standard-library calculator; SHA preserved.',path='scripts/compute.py')
add('artifact',id='T-RESULT',type='numeric-result',description='Canonical provided result, verified by fresh normal execution.',path='results/result.json',derived_from=['evidence:T-PARAM','evidence:T-RAW','artifact:T-CODE','decision:T-CHOICE'])
add('artifact',id='T-TABLE',type='numeric-table',description='Companion delivered table; all numeric rows match fresh result.',path='results/table.csv',derived_from=['artifact:T-RESULT'])
add('artifact',id='T-SUMMARY',type='summary',description='Provided summary reviewed for current parameters, rounding and bounded conclusion.',path='results/summary.md',derived_from=['statement:T-CLAIM','artifact:T-RESULT'])
add('artifact',id='T-SOURCE-NOTE',type='source-identity-note',description='Fixed provided source card; full text read, independent of numerical parameter.',path='notes/source-check.md',derived_from=['source:T-SRC','evidence:T-RAW'],notes='Card is author-supplied paraphrase; no independent page/theorem confirmation claimed.')
add('artifact',id='T-A-VALIDATION',type='execution-evidence',description='Actual commands/exits, values, identity scope, before/after hashes and bounded scientific audit.',path='notes/stage-a-validation.json')
add('artifact',id='T-INITIAL-SNAPSHOT',type='version-manifest',description='Manifest locating exact recoverable contents of four initial small files.',path='history/stage-a-initial/manifest.json')
for n, rel in enumerate(snap_paths,1):
    add('artifact',id='T-INITIAL-'+str(n),type='initial-version-content',description='Exact initial bytes retained for '+rel,path='history/stage-a-initial/'+rel)
add('artifact',id='T-RECOVERY',type='recovery-guide',description='Portable local recovery, authority, limits and concrete next action.',path='RECOVERY.md')
add('activity',id='T-SOURCE-CHECK',title='Verify supplied fixed source identity and card scope',status='done',inputs=['source:T-SRC','evidence:T-RAW'],outputs=['artifact:T-SOURCE-NOTE'],note='AI agent verified full supplied SHA/bytes and metadata, read card; mathematical pages not examined. Source-only remote not current-content checked.')
add('activity',id='T-CALC',title='Evaluate supplied calculator and verify current result and companion table',status='done',inputs=['evidence:T-PARAM','evidence:T-RAW','artifact:T-CODE','decision:T-CHOICE'],outputs=['artifact:T-RESULT','artifact:T-TABLE','artifact:T-A-VALIDATION'],note='AI execution, normal exit0; exact JSON/numeric CSV comparison and special-case arithmetic checked. Controlled alpha=1 exit2 preserved; effective originals unchanged.')
add('activity',id='T-SYNTH',title='Review supplied summary within current claim and verified numeric result',status='done',inputs=['statement:T-CLAIM','artifact:T-RESULT','artifact:T-TABLE'],outputs=['artifact:T-SUMMARY'],depends_on=['T-CALC'],note='AI read provided summary and checked parameters, pre-observation rho, v10 rounding and no new-proof scope. Not human expert approval.')
save(O/'registration-batch.json',batch)
cli('register-batch','--root',P,'--file',O/'registration-batch.json',label='register-logical-records-and-dependencies')
cli('check','--root',P,label='check-before-checkpoint')
cli('checkpoint','--root',P,'--next-action',next_action,'--activity','T-SYNTH','--note','Actual normal/controlled-invalid computations and bounded content checks performed; registration is not scientific certification.',label='save-concrete-checkpoint')
final=cli('resume','--root',P,label='read-final-recovery-state')
save(O/'final-recovery.json',json.loads(final['stdout']))
run([PY,'-I','-B',P/'_rw-runtime/tools/connect_skills.py','check','--installed-only','--root',P], 'check-portable-runtime')
save(O/'environment.json',proof['environment'])
print(json.dumps({'project':str(P),'output':str(O),'commands':len(commands),'finished':True},ensure_ascii=False))
