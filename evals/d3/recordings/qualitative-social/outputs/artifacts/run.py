"""Rebuild excerpt traceability from copied inputs and explicit AI-agent-performed interpretive coding.
Coding and thematic judgment were performed by the Codex AI agent; no independent human coding or human validation is claimed.
This script performs deterministic document traceability checks only, not interpretation or a numerical experiment.
Run from any directory: python3 PROJECT/artifacts/run.py
"""
from pathlib import Path
import json, hashlib, time, sys
start=time.monotonic()
root=Path(__file__).resolve().parents[1]
source=root/'inputs/interviews.md'
coding=root/'analysis/coding.json'
lines=source.read_text().splitlines()
entries=json.loads(coding.read_text())['entries']
failures=[]
for e in entries:
    actual=lines[e['line']-1] if e['line']<=len(lines) else ''
    expected=e['locator']+'：'+e['quote']
    if actual!=expected:failures.append({'locator':e['locator'],'problem':'quote or line mismatch'})
input_ids=[line.split('：',1)[0] for line in lines if line.startswith(('P1-Q','P2-Q','P3-Q','P4-Q','P5-Q','P6-Q'))]
if sorted(e['locator'] for e in entries)!=sorted(input_ids):failures.append({'problem':'missing or duplicate excerpt coding'})
report=(root/'manuscript/report.md').read_text()
chinese_chars=sum('\u4e00'<=c<='\u9fff' for c in report)
if chinese_chars>1000:failures.append({'problem':'report exceeds 1000 Chinese characters'})
if not failures:
    table=['# 原话位置—代码—主题—解释范围','', '全部18段均保留，原话逐字复制；表中范围栏为本次Codex AI代理解释，未经独立人类验证。所有事实性事件、时长与参与者背景均未独立核验。主题不是互斥分类，出现次数不用于总体比例或饱和度。','', '| 原话位置 | 原话 | 代码 | 主题 | 解释范围 |','|---|---|---|---|---|']
    for e in entries:table.append(f"| inputs/interviews.md:L{e['line']}（{e['locator']}） | {e['quote']} | {'/'.join(e['codes'])} | {e['theme']} | {e['scope']} |")
    (root/'analysis/traceability.md').write_text('\n'.join(table)+'\n')
results={'operation':'exact quotation/location and coverage check; rebuild traceability table from AI-agent-performed interpretive coding','not_a_numerical_experiment':True,'seed':'not-applicable: deterministic document reconstruction','inputs':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [source,coding,root/'manuscript/report.md']},'coded_excerpt_ids':[e['locator'] for e in entries],'all_supplied_excerpt_ids_preserved':not failures,'report_chinese_characters':chinese_chars,'interpretation':'Codex AI agent interpretive coding fixed in analysis/coding.json; no independent human coding or human validation; this script does not infer codes, themes, prevalence or causality','failures':failures,'elapsed_seconds':time.monotonic()-start}
(root/'artifacts/results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(results,ensure_ascii=False,indent=2))
sys.exit(bool(failures))
