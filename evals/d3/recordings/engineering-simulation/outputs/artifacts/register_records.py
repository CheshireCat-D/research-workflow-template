"""Register this completed project's evidence with its copied CLI (first registration only)."""
from pathlib import Path
import json
import subprocess
import time
ROOT=Path(__file__).resolve().parents[1]
CLI='.agents/skills/_rw-runtime/tools/research.py'
records=[]
def add(kind,**value): records.append((kind,value))
for id,name,title in [('SRC_task','task.md','委托与离线合成边界'),('SRC_req','requirements.md','原创合成加热箱需求v1'),('SRC_config','scenarios.json','固定模型与四场景v1'),('SRC_original','simulator.py','原始标称原型')]:
    add('source',id=id,title=title,locator='inputs/'+name,version='1',content_access='full',rights='unknown',limitations='Task-original synthetic material; no physical observations or external source verification.')
statements=[('S_R1','给定模型标称场景在120至240秒内满足24.5至25.5°C。','supported-in-scope','五步长及无延迟解析解一致；不代表实物。'),('S_R2','0–80W纯加热设备可在5至35°C、延迟不超过15秒满足同一温带。','challenged','cold、hot失败；任意允许功率的有限时间比较界反驳此声明。'),('S_R3','补充仿真区分请求与实际功率，实际功率在0至80W。','supported-in-scope','20次实际计算及默认轨迹算术回读合规。'),('S_R4','全场景全程温度不超过28°C且可宣布实物安全。','challenged','hot模型越过28°C；没有独立保护与故障硬件资料。'),('S_R5','本轮数值判断检查时间步长影响。','supported-in-scope','五步长验收标签相同；最细相邻最大差0.000781°C以内；非连续误差认证。'),('S_release','标称仿真可支持5至35°C全域安全并立即宣布实物通过。','challenged','原型漏延迟和钳位；R2/R4被模型反例挑战，实物材料缺失。')]
for id,text,status,reason in statements:
    add('statement',id=id,text=text,type='design',scope='Only supplied synthetic lumped model, four mandatory scenarios, 240s; no physical validation.',work_status='reviewed',assessment={'status':status,'scope':'Agent self-review of stated model/implementation only','rationale':reason,'reviewer':'Codex agent'},formal_verification={'status':'not-applicable','scope':'No formal proof assistant used; ODE comparison manually derived','tool':'none'})
for id,path,type,desc,src in [('E_req','inputs/requirements.md','synthetic-specification','额定值、R1–R5与无实物资料声明',['SRC_req']),('E_results','artifacts/results.json','numerical-simulation','20次完整配置/逐场景指标、步长及解析核对',['SRC_config','SRC_original']),('E_bounds','notes/analytic.md','analytic-derivation','任意0–80W控制的冷热有限时间比较界',['SRC_req','SRC_config']),('E_baseline','logs/baseline.json','execution-log','原标称代码实际运行与退出0',['SRC_original']),('E_readback','checks/trace-readback.json','arithmetic-readback','默认轨迹独立算术回读',['SRC_config']),('E_replay','checks/replay.json','replay-check','两次正式结果去除耗时后完全一致',['SRC_config'])]:
    add('evidence',id=id,type=type,description=desc,provenance='Codex agent executed offline with Python standard library; raw source synthetic.',location={'kind':'local','path':path},source_ids=src,limitations='No hardware performance, safety, external novelty or certification evidence.')
for id,s,e,relation,reason in [('L_R1','S_R1','E_results','supports','所测标称全部步长后120秒达标。'),('L_R2','S_R2','E_results','challenges','cold/hot均不达标。'),('L_R2_bound','S_R2','E_bounds','challenges','有限时间界说明当前额定设备根本不可满足。'),('L_R3','S_R3','E_results','supports','全部实际功率钳位0至80W。'),('L_R3_check','S_R3','E_readback','supports','回读确认延迟/请求/钳位/更新算术。'),('L_R4','S_R4','E_results','challenges','hot最高34.003300°C超过28°C。'),('L_R4_missing','S_R4','E_req','qualifies','没有真实温度保护/故障/断电资料；无法物理安全认证。'),('L_R5','S_R5','E_results','supports','实际运行五步长且标签一致。'),('L_R5_scope','S_R5','E_bounds','qualifies','延迟场景未给连续误差界；必要条件非全域充分保证。'),('L_release','S_release','E_bounds','challenges','原全域声明与额定能力矛盾。'),('L_release_scope','S_release','E_req','qualifies','输入明确无实物证据。')]:
    add('relation',id=id,statement_id=s,evidence_id=e,relation=relation,rationale=reason,scope='Finite supplied synthetic evidence only')
artifacts=[('A_issue','notes/issue.md','method-plan','范围/方法/预先判据'),('A_run','artifacts/run.py','code','实际执行主程序与配置/失败保存'),('A_sim','artifacts/simulator.py','code','补充钳位与延迟模型'),('A_readback','artifacts/readback.py','code','独立算术回读'),('A_results','artifacts/results.json','results','当前完整数值结果'),('A_first','artifacts/results.first-run.json','results','首次正式结果保留'),('A_bounds','notes/analytic.md','derivation','执行器能力与有限时间界'),('A_trace','notes/traceability.md','traceability','逐需求/逐场景追踪'),('A_report','manuscript/report.md','manuscript','776字符中文短技术稿'),('A_review','review.md','review','证据支持/失败/限制与发布修订'),('A_replay','README-replay.md','reproduction-guide','项目相对重放步骤')]
for id,path,type,desc in artifacts:
    add('artifact',id=id,type=type,description=desc,path=path,derived_from=['source:SRC_req','source:SRC_config'],notes='Actual file; no source-toolkit or hardware edits.')
for scene in ['nominal','delayed','cold','hot']:
    add('artifact',id='A_csv_'+scene,type='trajectory',description='Default0.1s full trace '+scene,path='artifacts/traces/'+scene+'.csv',derived_from=['artifact:A_sim','artifact:A_run','source:SRC_config'])
add('method-binding',id='M_engineering',method_id='engineering-design',profile_version='0.1',variant='system',reason='Requirements traceability, rating feasibility and release review',applies_to=['statement:S_R2','statement:S_R4','artifact:A_trace','artifact:A_bounds','artifact:A_review'],notes='Actually read project-local profile; no actual hardware design change/testing.')
add('method-binding',id='M_computational',method_id='computational',profile_version='0.1',variant='numerical-simulation',reason='Baseline plus20 runs, five-step sensitivity and analytic special-case readback',applies_to=['artifact:A_run','artifact:A_sim','artifact:A_results','statement:S_R1','statement:S_R3','statement:S_R5'],notes='Actually read project-local profile; deterministic offline stdlib.')
add('activity',id='X_plan',title='Read copied inputs/profiles and set scope plus acceptance plan',status='done',inputs=['source:SRC_task','source:SRC_req','source:SRC_config','source:SRC_original'],outputs=['artifact:A_issue'],note='Executed by Codex agent; source access full.')
add('activity',id='X_simulate',title='Execute original baseline,20 runs, replay and independent readback',status='done',depends_on=['X_plan'],inputs=['artifact:A_issue','source:SRC_config','source:SRC_original','artifact:A_run','artifact:A_sim','artifact:A_readback'],outputs=['evidence:E_results','evidence:E_baseline','evidence:E_readback','evidence:E_replay','artifact:A_first','artifact:A_bounds','artifact:A_trace'],note='Actual exits0; R2/R4 scientific requirement failures retained; no runtime exceptions.')
add('activity',id='X_write',title='Write bounded Chinese technical manuscript',status='done',depends_on=['X_simulate'],inputs=['evidence:E_results','evidence:E_bounds','artifact:A_trace'],outputs=['artifact:A_report'],note='Drafted by Codex agent, under1000 Chinese characters.')
add('activity',id='X_review',title='Self-review claim support and replace premature release opinion',status='done',depends_on=['X_write'],inputs=['artifact:A_report','evidence:E_results','evidence:E_bounds','source:SRC_req'],outputs=['artifact:A_review','artifact:A_replay'],note='Same-agent self-review; not independent expert/human approval or physical certification.')
logs=[]
for n,(kind,payload) in enumerate(records,1):
    rel=f"records-input/{n:03d}-{kind}-{payload['id']}.json"
    (ROOT/rel).write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
    argv=['python3',CLI,'register','--root','.','--kind',kind,'--file',rel]
    t=time.perf_counter();q=subprocess.run(argv,cwd=ROOT,text=True,capture_output=True)
    log={'argv':argv,'cwd':'.','exit_code':q.returncode,'elapsed_s':time.perf_counter()-t,'stdout':q.stdout,'stderr':q.stderr}
    logs.append(log)
    (ROOT/'logs/registration.json').write_text(json.dumps(logs,ensure_ascii=False,indent=2)+'\n')
    if q.returncode:
        print(json.dumps(log,ensure_ascii=False,indent=2));raise SystemExit(q.returncode)
print(json.dumps({'registered':len(records),'counts':{kind:sum(k==kind for k,v in records) for kind,v in records},'exit_codes':[x['exit_code'] for x in logs]},ensure_ascii=False))
