from pathlib import Path
import hashlib,json,re
P=Path(__file__).resolve().parents[1]
summary='年满18岁且为本地居民者，在无正在执行的禁止令且（完成培训或处于获准监督之下）时，得申请许可。'
report=(P/'manuscript/report.md').read_text(encoding='utf-8')
content={'summary':summary,'summary_unicode_characters_including_punctuation_and_digits':len(summary),'summary_within_80':len(summary)<=80,'summary_present_in_report':summary in report,'report_cjk_characters':len(re.findall(r'[\u4e00-\u9fff]',report)),'report_nonspace_characters':len(re.sub(r'\s','',report)),'report_nonspace_within_600':len(re.sub(r'\s','',report))<=600,'scope':'Only length and presence; legal content manually reviewed against input clauses.'}
(P/'checks/content-check.json').write_text(json.dumps(content,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
a=(P/'artifacts/results.json').read_bytes()
b=(P.parent/'replay-output/results.json').read_bytes()
replay={'delivered_result_sha256':hashlib.sha256(a).hexdigest(),'replay_result_sha256':hashlib.sha256(b).hexdigest(),'byte_identical':a==b,'scope':'Actual second invocation, same designated input copies and fresh output directory.'}
(P/'checks/replay-check.json').write_text(json.dumps(replay,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
if not all([content['summary_within_80'],content['summary_present_in_report'],content['report_nonspace_within_600'],replay['byte_identical']]):raise SystemExit(1)
print(json.dumps({'content':content,'replay':replay},ensure_ascii=False))
