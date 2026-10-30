from pathlib import Path
import csv, hashlib, json, os, platform, shutil, subprocess, sys

BASE=Path('STUDY_ROOT/runs/P4')
P=BASE/'project'; I=BASE/'A/input'; O=BASE/'A/output'
T=Path('TOOLKIT_ROOT')
PY='EVAL_PYTHON'
logs=O/'logs'; logs.mkdir(exist_ok=True)
commands=[]
def save(p,x):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def load(p): return json.loads(p.read_text(encoding='utf-8'))
def ident(p):
    b=p.read_bytes(); return {'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def cmd(name,target,args,expect=0,cwd=None):
    argv=[PY,'-I','-B',str(O/'auditrun.py'),str(logs/(name+'.reads.json')),str(target),*map(str,args)]
    proc=subprocess.run(argv,cwd=cwd or BASE,text=True,capture_output=True)
    (logs/(name+'.stdout')).write_text(proc.stdout)
    (logs/(name+'.stderr')).write_text(proc.stderr)
    rec={'name':name,'argv':argv,'target_argv':[str(target),*map(str,args)],'cwd':str(cwd or BASE),'exit_code':proc.returncode,'stdout':proc.stdout,'stderr':proc.stderr,'expected_exit_code':expect}
    commands.append(rec); save(O/'commands.json',commands)
    print(name,proc.returncode,proc.stdout[:150],proc.stderr[:150],flush=True)
    if proc.returncode != expect: raise RuntimeError('Unexpected command exit: '+name)
    return proc
def tool(name,args,expect=0):return cmd(name,T/'tools/research.py',args,expect)

assert not P.exists(), 'Refuse overwriting a project'
C=load(I/'initial/constraints.json'); IDS=load(I/'initial/source-identities.json')
M=load(I/'initial/MANIFEST.json')
manifest_check=[]
for rel,expected in M['files'].items():
    actual=ident(I/'initial'/rel)
    assert actual==expected, rel
    manifest_check.append({'path':rel,**actual,'matches_supplied_manifest':True})
save(O/'input-manifest-check.json',manifest_check)

tool('01-init',['init','--output',P,'--title','冻结自行车需求模型的评价范围修订','--interest',C['interest'],'--method','computational','--mode','reproducible','--language','zh','--entry','validation','--connect-skills'])
shutil.copytree(I/'initial/project_payload',P,dirs_exist_ok=True)
(P/'context').mkdir()
for rel in ['BRIEF.md','constraints.json','obligations.json','source-identities.json','MANIFEST.json']:
    shutil.copy2(I/'initial'/rel,P/'context'/rel)
for rel in ['PROTOCOL.md','RECORDING.md','STAGE-A.md']:
    shutil.copy2(I/rel,P/'context'/rel)
tool('02-configure',['configure','--root',P,'--deadline',C['deadline'],'--budget',C['budget'],*sum((['--add-capability',v] for v in C['available_capabilities']),[])])

snap=P/'history/stage-A-initial'
snapshot_paths=['notes/parameters.json','results/result.json','results/table.csv','results/summary.md']
for rel in snapshot_paths:
    target=snap/rel; target.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(P/rel,target)
save(snap/'manifest.json',{'reason':'Initial author-provided canonical bytes retained before any later revision. Not a fresh scientific analysis.','files':{rel:ident(snap/rel) for rel in snapshot_paths}})

protected=['notes/parameters.json','notes/rejected-parameters.json','model/frozen.json','scripts/compute.py','data/hour_2011.csv','results/result.json','results/table.csv','results/summary.md']
before={r:ident(P/r) for r in protected}
normal=cmd('03-normal-calculation',P/'scripts/compute.py',['--root',P,'--output',O/'validation-normal'])
result=load(O/'validation-normal/result.json'); canonical=load(P/'results/result.json')
assert result==canonical
assert (O/'validation-normal/result.json').read_bytes()==(P/'results/result.json').read_bytes()
assert (O/'validation-normal/table.csv').read_bytes()==(P/'results/table.csv').read_bytes()
with (O/'validation-normal/table.csv').open(newline='') as f:
    table=list(csv.DictReader(f))
for row in table: assert float(row['value'])==float(result[row['metric']])
summary=(P/'results/summary.md').read_text()
for text in ['2203','92','58.825190494512','44.570832407532','24.23172448%','2011-10-01','12-31']:
    assert text in summary
with (P/'data/hour_2011.csv').open(newline='') as f: raw=list(csv.DictReader(f))
assert len(raw)==8645
assert set(r['yr'] for r in raw)=={'0'}
assert min(r['dteday'] for r in raw)=='2011-01-01'
assert max(r['dteday'] for r in raw)=='2011-12-31'
assert len({(r['dteday'],r['hr']) for r in raw})==8645
eval_rows=[r for r in raw if '2011-10-01'<=r['dteday']<='2011-12-31']
assert len(eval_rows)==2203 and len({r['dteday'] for r in eval_rows})==92
model=load(P/'model/frozen.json')
assert model['train_before']=='2011-10-01'
cmd('04-controlled-invalid-calculation',P/'scripts/compute.py',['--root',P,'--output',O/'validation-invalid','--spec',P/'notes/rejected-parameters.json'],expect=2)
after={r:ident(P/r) for r in protected}
assert before==after
assert not (O/'validation-invalid').exists()

source_verification={
 'performer':'assistant agent plus local deterministic Python checks; no human approval',
 'primary_identity':IDS['primary'],'remote_identity':IDS['source_only'],
 'actual_read_scope':'Full supplied 2011 CSV parsed (8645 rows); supplied frozen model/code/parameter/result/table/summary/source note read. Original full hour.csv, official ZIP, website and research article not supplied or inspected.',
 'checks':{'supplied_manifest_all_match':True,'local_2011_row_count':len(raw),'local_year_values':['0'],'date_min':'2011-01-01','date_max':'2011-12-31','unique_date_hour_count':8645,'frozen_model_train_before':model['train_before']},
 'source_note_limits':'Source note says full CSV has 17379 rows while web metadata says 17389. Both counts are supplied provenance, not freshly verified. Do not alter observations or claim a remote-content check.',
 'publication_rule':IDS['publication_rule'],
 'not_checked':['Full remote article content','Original full CSV byte hash against remote','Independent re-creation of fitted coefficients','Human expert approval']}
save(P/'validation/stage-A/source-verification.json',source_verification)
comparison={'performer':'assistant agent and supplied calculator','preparation':'Prebuilt results were supplied by material builder; this is a rerun and consistency check, not an analysis from scratch.',
 'canonical_result_identical_bytes':True,'canonical_table_identical_bytes':True,'all_table_rows_match_result':True,'summary_rounding_and_scope_match':True,'result':result,
 'normal_command':commands[-2], 'controlled_invalid_command':commands[-1],
 'controlled_invalid_test':{'expected_failure':True,'exit_code':2,'error':'ValueError','message':'evaluation_start must be no later than evaluation_end','is_scientific_analysis_failure':False,'invalid_output_created':False},
 'protected_before':before,'protected_after':after,'all_protected_bytes_unchanged':True,
 'scope':'Actual observed-hour descriptive comparison over 2011 Q4 using supplied Jan-Sep fixed coefficients; no refit, confidence interval, causal conclusion or 2012 extrapolation.'}
save(P/'validation/stage-A/comparison.json',comparison)
for rel in ['result.json','table.csv']:
    shutil.copy2(O/'validation-normal'/rel,P/'validation/stage-A/normal'/rel) if (P/'validation/stage-A/normal').is_dir() else None
(P/'validation/stage-A/normal').mkdir(exist_ok=True)
for rel in ['result.json','table.csv']: shutil.copy2(O/'validation-normal'/rel,P/'validation/stage-A/normal'/rel)
for name in ['03-normal-calculation','04-controlled-invalid-calculation']:
    for ext in ['stdout','stderr']:
        shutil.copy2(logs/(name+'.'+ext),P/'validation/stage-A'/(name+'.'+ext))
save(P/'validation/stage-A/initial-identities.json',{'files':{str(p.relative_to(P)):ident(p) for p in sorted(P.rglob('*')) if p.is_file() and (str(p.relative_to(P)).split('/')[0] in {'data','model','notes','results','scripts','context','history'})},'tracking_exclusion':'notes/unregistered-scratch.md identity preserved here as copy inventory only. It has no registry record or activity dependency and is not automatically monitored.'})
(P/'.gitignore').write_text('.research/\nlocal-config/\nprivate-data/\n.DS_Store\ndata/\n*.pdf\n')
next_action='2011第四季度指标与摘要已逐项核对；下一步由作者讨论该描述性比较的解释与用途。恢复先运行项目内 resume，核对当前 parameters/result/table/summary 及依赖；若有漂移，保留旧字节与原因并复核 D-CALC、D-SYNTH 后显式重登，不重训或外推2012。'
(P/'RECOVERY.md').write_text('''# 项目恢复\n\n权威配置为 project.json；权威登记、版本与游标为 records/registry.json。context/ 保存给定原始约束与义务，只作来源，不覆盖以后显式修订后的当前配置/登记。PROJECT.md 和本文件不反向覆盖登记。\n\n先用可用的 Python 3.11+ 运行：\n\n```text\npython3 -I -B _rw-runtime/tools/research.py resume --root .\npython3 -I -B _rw-runtime/tools/research.py check --root .\n```\n\n指令不自动执行计算。恢复后按实际任务决定下一步；变更登记须使用 register 或 register-batch，替换显式 --replace --expected-version N。历史初始内容可从 history/stage-A-initial/ 的四份原字节恢复，manifest.json 给出SHA；context/ 保存本次来源/约束/逻辑义务。不能只保存新checkpoint来承认旧工作仍有效。\n\n冻结模型为所给2011年1—9月参数；本阶段是2203观察小时、92日的2011第四季度描述性复算，不重新拟合、无置信区间、无因果或2012外推。未有人类专家批准；未授权外部投稿。截止日2026-12-15为给定项目约束，并非观察到的真实截止日；目标期刊未知，project.json保留null。\n\n来源卡记录原完整CSV的17379/官网metadata的17389差异；本次只独立检查给定8645行2011切片及本地SHA，未访问原ZIP/网站/文章。D-REMOTE仅身份元数据，没有本地内容绑定。notes/unregistered-scratch.md不登记，不是计算依赖，不在自动变化检测覆盖内。原始CSV/PDF只留私有研究缓存；data/被gitignore排除，无外发。\n\n验证与两次真实命令、受控无效输入退出2及失败前后SHA在validation/stage-A/。失败是预期输入校验；原有效成果未改变。\n\n具体下一步：'''+next_action+'\n')
(P/'PROJECT.md').write_text('# 冻结自行车需求模型的评价范围修订\n\n当前结果由所给预制材料复算核对；详见results/与validation/stage-A/。当前工作和配置以project.json及records/registry.json为准，恢复操作见RECOVERY.md。\n\n'+next_action+'\n')

batch=[]
def add(kind,**rec):batch.append({'kind':kind,'record':rec})
add('source',id='D-SRC',title=IDS['primary']['title'],locator=IDS['primary']['uri'],version=IDS['primary']['version'],content_access='partial',rights='restricted',limitations='Only supplied 2011 slice inspected; no current remote verification or full dataset/website inspection.',extensions={'doi':IDS['primary']['doi'],'license':IDS['primary']['license'],'access_detail':source_verification['actual_read_scope'],'publication_rule':IDS['publication_rule']})
add('source',id='D-REMOTE',title=IDS['source_only']['title'],locator=IDS['source_only']['uri'],version=IDS['source_only']['version'],content_access='metadata-only',limitations=IDS['source_only']['tracking_limit'])
add('evidence',id='D-RAW',type='observed-data',description='Immutable supplied official-hour.csv 2011 slice, 8645 observed hour rows',provenance='Supplied local cache and source identities; local SHA and row coverage verified',location={'kind':'local','path':'data/hour_2011.csv'},source_ids=['D-SRC'],limitations='Full original CSV/remote origin not independently reacquired')
add('evidence',id='D-PARAM',type='author-parameters',description='Current declared frozen-model evaluation interval and observed-hour weighting',provenance='Benchmark author working parameters, not original dataset content',location={'kind':'local','path':'notes/parameters.json'})
add('statement',id='D-CLAIM',text=C['interest'],type='empirical',scope='Current author parameters: 2011-10-01 to 2011-12-31; supplied frozen C0/C1 and observed hours only',assessment={'status':'supported-in-scope','scope':'Rerun and descriptive consistency only','rationale':'Independent execution of supplied calculator reproduces canonical result/table exactly and summary rounding agrees; no human expert review or inferential guarantee','reviewer':'assistant agent'},formal_verification={'status':'not-applicable','scope':'Descriptive numerical calculation','tool':'none'})
add('relation',id='D-REL',statement_id='D-CLAIM',evidence_id='D-PARAM',relation='qualifies',rationale='Declared period and weighting delimit the current comparison',scope='Current numerical/descriptive claim; registration is not mathematical proof')
add('decision',id='D-CHOICE',choice='Use initial supplied author parameters and Jan-Sep frozen model; do not refit',rationale='Given constraints and author-supplied initial evaluation specification',responsible='benchmark author, as attributed in supplied material',decided_at='Unspecified in supplied materials; no author decision date invented',evidence_refs=['D-PARAM'],revisit_when='Only upon explicit authorized parameter/scope revision; retain prior content and reason',extensions={'decision_date':None,'recorded_by':'assistant agent'})
add('artifact',id='D-CODE',type='scientific-calculator',description='Supplied deterministic calculator, unchanged',path='scripts/compute.py')
add('artifact',id='D-MODEL',type='frozen-model',description='Supplied C0 hour means and C1 workingday/hour means, trained before 2011-10-01; no refit performed',path='model/frozen.json',derived_from=['evidence:D-RAW'],notes='Training provenance is supplied; this activity did not independently refit the model')
add('artifact',id='D-RESULT',type='numeric-result',description='Canonical numeric result verified byte-for-byte against fresh calculation',path='results/result.json',derived_from=['evidence:D-PARAM','evidence:D-RAW','artifact:D-CODE','decision:D-CHOICE','artifact:D-MODEL'])
add('artifact',id='D-TABLE',type='numeric-table',description='Companion table verified byte-for-byte and metric-by-metric',path='results/table.csv',derived_from=['artifact:D-RESULT'])
add('artifact',id='D-SUMMARY',type='summary',description='Supplied current summary checked for numbers, rounding, interval and scope',path='results/summary.md',derived_from=['statement:D-CLAIM','artifact:D-RESULT','artifact:D-TABLE'])
add('artifact',id='D-SOURCE-NOTE',type='source-card',description='Supplied source/version/coverage note; independent of chosen evaluation interval',path='notes/source-check.md')
add('artifact',id='D-SOURCE-VERIFICATION',type='verification-record',description='Actual local source check and declared remote/unread limits',path='validation/stage-A/source-verification.json',derived_from=['source:D-SRC','evidence:D-RAW','source:D-REMOTE'])
add('artifact',id='D-VALIDATION',type='validation-record',description='Real normal/invalid calculator runs, output comparison and unchanged protected hashes',path='validation/stage-A/comparison.json',derived_from=['evidence:D-PARAM','evidence:D-RAW','artifact:D-CODE','artifact:D-MODEL','artifact:D-RESULT','artifact:D-TABLE','artifact:D-SUMMARY'])
add('evidence',id='D-INVALID-PARAM',type='controlled-invalid-input',description='Deliberately invalid start-after-end input; not current parameters',provenance='Supplied controlled invalid input',location={'kind':'local','path':'notes/rejected-parameters.json'})
add('activity',id='D-SOURCE-CHECK',title='Verify supplied source identity, local slice and source card',status='done',inputs=['source:D-SRC','evidence:D-RAW'],outputs=['artifact:D-SOURCE-NOTE','artifact:D-SOURCE-VERIFICATION'],note='Performed by assistant/local standard library checks; no remote reacquisition, article review or human approval')
add('activity',id='D-CALC',title='Rerun supplied calculator and verify canonical numeric result and companion table',status='done',inputs=['evidence:D-PARAM','evidence:D-RAW','artifact:D-CODE','decision:D-CHOICE','artifact:D-MODEL'],outputs=['artifact:D-RESULT','artifact:D-TABLE'],note='Actual command exit 0; result.json/table.csv byte-identical to canonical prebuilt files; read-time files and command evidence preserved')
add('activity',id='D-SYNTH',title='Check supplied summary within current claim and verified result',status='done',inputs=['statement:D-CLAIM','artifact:D-RESULT','artifact:D-TABLE'],outputs=['artifact:D-SUMMARY'],depends_on=['D-CALC'],note='Assistant reviewed interval/counts/rounding and no-refit/no-causal/no-2012 scope; supplied summary kept unchanged')
add('activity',id='D-INVALID-TEST',title='Controlled invalid parameter rejection and canonical preservation check',status='done',inputs=['evidence:D-INVALID-PARAM','artifact:D-CODE'],outputs=['artifact:D-VALIDATION'],note='Expected calculator exit 2 with start-after-end ValueError; no invalid output directory; valid material before/after SHA identical. Successful negative-input test, not scientific-analysis failure.')
add('method-binding',id='D-COMPUTATIONAL',method_id='computational',profile_version='0.1',reason='Rerun deterministic frozen-model observed-hour metrics and preserve actual execution evidence',applies_to=['activity:D-CALC','activity:D-INVALID-TEST'])
save(O/'register-batch.json',batch)
tool('05-register',['register-batch','--root',P,'--file',O/'register-batch.json'])
check=tool('06-check',['check','--root',P])
tool('07-checkpoint',['checkpoint','--root',P,'--activity','D-SYNTH','--next-action',next_action,'--note','Normal/controlled-invalid runs and source/summary checks completed; human discussion pending. Initial four source contents retained in history/stage-A-initial.'])
resume=tool('08-resume',['resume','--root',P])
save(O/'final-status.json',json.loads(resume.stdout))
shutil.copy2(logs/'08-resume.stdout',P/'validation/stage-A/resume-at-handoff.json')
save(O/'workflow-result.json',{'case_id':'D','stage':'A','normal_result':result,'unchanged_protected':True,'next_action':next_action,'commands_count':len(commands),'project':str(P),'checkpoint':json.loads(resume.stdout)['checkpoint']})
print('WORKFLOW_COMPLETE',str(P),flush=True)
