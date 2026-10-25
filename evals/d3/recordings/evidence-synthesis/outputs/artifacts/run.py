"""Rebuild scoped extraction and numbers from copied raw inputs; Python stdlib only."""
from pathlib import Path
import csv, hashlib, json, math, re, time

ROOT = Path(__file__).resolve().parents[1]
Z = 1.959963984540054

def section(text, rid):
    match = re.search(r'^## '+rid+r'[^\n]*\n(.*?)(?=^## |\Z)',text,re.M|re.S)
    if not match: raise ValueError('Missing section '+rid)
    return match.group(1).strip()

def take(pattern,text):
    m=re.search(pattern,text)
    if not m: raise ValueError('Expected raw-input wording not found: '+pattern)
    return tuple(map(int,m.groups()))

def wilson(a,n):
    p=a/n; den=1+Z*Z/n
    mid=(p+Z*Z/(2*n))/den
    half=Z*math.sqrt(p*(1-p)/n+Z*Z/(4*n*n))/den
    return mid-half,mid+half

def effect(a,n,c,m):
    pt,pc=a/n,c/m; lt,ut=wilson(a,n);lc,uc=wilson(c,m)
    rd=pt-pc
    se=math.sqrt(1/a-1/n+1/c-1/m)
    logrr=math.log(pt/pc)
    return {'events_sms':a,'n_sms':n,'events_control':c,'n_control':m,
            'p_sms':pt,'p_control':pc,'risk_difference':rd,
            'rd_95_ci':[rd-math.sqrt((pt-lt)**2+(uc-pc)**2),rd+math.sqrt((ut-pt)**2+(pc-lc)**2)],
            'risk_ratio':pt/pc,'rr_95_ci':[math.exp(logrr-Z*se),math.exp(logrr+Z*se)],
            'log_rr':logrr,'var_log_rr':se*se}

def pool(es):
    ws=[1/e['var_log_rr'] for e in es]; total=sum(ws)
    mu=sum(w*e['log_rr'] for w,e in zip(ws,es))/total
    q=sum(w*(e['log_rr']-mu)**2 for w,e in zip(ws,es))
    return {'k':len(es),'rr':math.exp(mu),'rr_95_ci':[math.exp(mu-Z/math.sqrt(total)),math.exp(mu+Z/math.sqrt(total))],
            'Q':q,'df':len(es)-1,'I2_percent':max(0,(q-len(es)+1)/q)*100 if q else 0,
            'model':'exploratory inverse-variance fixed common-effect log risk ratio; no missingness adjustment'}

def csv_write(path,rows):
    with (ROOT/path).open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def main():
    t=time.perf_counter()
    raw={name:(ROOT/'inputs'/name).read_text(encoding='utf-8') for name in ['search-export.csv','abstracts.md','full-extracts.md','scope.md']}
    records=list(csv.DictReader(raw['search-export.csv'].splitlines()))
    if [r['record_id'] for r in records]!=['R01','R02','R03','R04','R05','R06','R07']:
        raise ValueError('Unexpected export identity/order; rescreen explicitly')
    ex=raw['full-extracts.md'];ab=raw['abstracts.md']
    s1,s2,s4,s5=[section(ex,r) for r in ['R01','R02','R05','R06']]
    if '同一100位参与者' not in s2 or '没有额外批次或随访终点' not in s2:
        raise ValueError('H1 report-link evidence changed')
    n1,a1,b1,m1,c1,d1=take(r'短信随机(\d+)人，出席(\d+)，未出席(\d+)；对照随机(\d+)人，出席(\d+)，未出席(\d+)',s1)
    if a1+b1!=n1 or c1+d1!=m1: raise ValueError('H1 totals disagree')
    total4,arm4=take(r'(\d+)位成人按随机数字表.*?各(\d+)人',s4)
    n4,a4,m4,c4,miss4,missc4=take(r'短信组(\d+)人取得出席状态，其中出席(\d+)人；对照组(\d+)人取得状态，其中出席(\d+)人。其余(\d+)人和(\d+)人的登记状态无法读取',s4)
    if total4!=2*arm4 or n4+miss4!=arm4 or m4+missc4!=arm4: raise ValueError('H4 denominators disagree')
    total5,arm5=take(r'(\d+)位成人.*?各(\d+)',s5)
    a5,b5,c5,d5=take(r'短信组出席(\d+)、未出席(\d+)；对照组出席(\d+)、未出席(\d+)',s5)
    if total5!=2*arm5 or a5+b5!=arm5 or c5+d5!=arm5: raise ValueError('H5 totals disagree')
    included={'H1':effect(a1,n1,c1,m1),'H4_complete_case':effect(a4,n4,c4,m4),'H5':effect(a5,arm5,c5,arm5)}
    reasons={
      'R01':('include','H1','R01','成人个体随机、一次短信对不提醒；结果完整','inputs/full-extracts.md §R01 M1/T1'),
      'R02':('merge-report','H1','R01','同一100人、站点、招募期；C1明确无新增批次或终点，作为佐证报告不重复计人','inputs/abstracts.md §R02; inputs/full-extracts.md §R02 C1'),
      'R03':('exclude','H2','','6至15岁儿童；未提供成人亚组','inputs/abstracts.md §R03'),
      'R04':('exclude','H3','','非随机前后比较，同时改变收费与挂号流程','inputs/abstracts.md §R04'),
      'R05':('include','H4','R05','成人个体随机；缺失状态进入敏感性，不能默用62/65代表70/70','inputs/full-extracts.md §R05 M1/R1/D1'),
      'R06':('include','H5','R06','成人随机短信对不提醒；80人状态完整','inputs/full-extracts.md §R06 M1/T1'),
      'R07':('exclude','H6','','尚未开始招募的方案，无结果','inputs/abstracts.md §R07')}
    screening=[]
    for rec in records:
      rid=rec['record_id'];decision,study,destination,reason,loc=reasons[rid]
      screening.append(dict(record_id=rid,title=rec['title'],study=study,decision=decision,destination=destination,reason=reason,source_location=loc,access='abstract + marked excerpts only' if rid in ['R01','R02','R05','R06'] else 'abstract only; no further full text supplied'))
    extraction=[
      {'study':'H1','reports':'R01;R02','design':'individual randomized; computer sequence; 1:1','randomized_sms':n1,'randomized_control':m1,'observed_sms':n1,'observed_control':m1,'attended_sms':a1,'attended_control':c1,'missing_sms':0,'missing_control':0,'endpoint':'one first follow-up appointment','location':'inputs/full-extracts.md §R01 M1/T1; §R02 C1','limits':'allocation concealment not described; preregistration text unavailable'},
      {'study':'H4','reports':'R05','design':'individual randomized; random number table','randomized_sms':arm4,'randomized_control':arm4,'observed_sms':n4,'observed_control':m4,'attended_sms':a4,'attended_control':c4,'missing_sms':miss4,'missing_control':missc4,'endpoint':'one appointment','location':'inputs/full-extracts.md §R05 M1/R1/D1','limits':'allocation concealment unspecified; missing outcome reason/analysis plan unavailable'},
      {'study':'H5','reports':'R06','design':'individual randomized; sealed numbered envelopes','randomized_sms':arm5,'randomized_control':arm5,'observed_sms':arm5,'observed_control':arm5,'attended_sms':a5,'attended_control':c5,'missing_sms':0,'missing_control':0,'endpoint':'one appointment round','location':'inputs/full-extracts.md §R06 M1/T1','limits':'opacity/sequential numbering/custody unspecified; preregistration text unavailable'}]
    sensitivity=[]
    for sms in range(miss4+1):
      for control in range(missc4+1):
        e=effect(a4+sms,arm4,c4+control,arm4)
        sensitivity.append({'missing_sms_attend':sms,'missing_control_attend':control,'effect':e,'pooled_with_H1_H5':pool([included['H1'],e,included['H5']])})
    tags={'all_missing_absent':(0,0),'all_missing_attend':(miss4,missc4),'sms_worst_control_best':(0,missc4),'sms_best_control_worst':(miss4,0)}
    scenarios={tag:next(s for s in sensitivity if (s['missing_sms_attend'],s['missing_control_attend'])==val) for tag,val in tags.items()}
    result={'scope':'supplied synthetic offline materials only; not complete systematic review','input_sha256':{k:hashlib.sha256(v.encode()).hexdigest() for k,v in raw.items()},
      'flow':{'export_records':len(records),'unique_reports':7,'exact_export_duplicates':0,'same_study_report_links':1,'unique_studies_all':6,'excluded_reports':3,'included_reports':4,'included_independent_studies':3,'randomized_total':sum(x['randomized_sms']+x['randomized_control'] for x in extraction),'observed_total':sum(x['observed_sms']+x['observed_control'] for x in extraction)},
      'effects':included,'H4_missing_scenarios':scenarios,'H4_all_54_assignments':sensitivity,
      'H4_identification_bounds':{'RD':[min(s['effect']['risk_difference'] for s in sensitivity),max(s['effect']['risk_difference'] for s in sensitivity)],'RR':[min(s['effect']['risk_ratio'] for s in sensitivity),max(s['effect']['risk_ratio'] for s in sensitivity)],'note':'point-identification bounds conditional on observed outcomes; not 95% confidence limits'},
      'exploratory_complete_case_pool':pool(list(included.values())),
      'uncertainty':{'RR':'Katz log risk ratio normal approximation; no zero cells','RD':'Newcombe independent Wilson-score intervals without continuity correction','level':0.95,'Z':Z,'missing':'enumeration of all 54 binary outcome-count assignments; no missing-at-random assumption','pool':'secondary fixed common effect illustrative only; estimate targets differ for complete cases'},
      'seed':'not applicable: deterministic extraction/enumeration; no random simulation','failures':[]}
    csv_write('notes/screening.csv',screening);csv_write('notes/extraction.csv',extraction)
    def fmt(e):
      return f"{e['events_sms']}/{e['n_sms']} 对 {e['events_control']}/{e['n_control']}；RD {100*e['risk_difference']:.2f}百分点（95%区间 {100*e['rd_95_ci'][0]:.2f}至{100*e['rd_95_ci'][1]:.2f}）；RR {e['risk_ratio']:.3f}（{e['rr_95_ci'][0]:.3f}至{e['rr_95_ci'][1]:.3f}）"
    lines=['# 逐项结果（从复制原文重建）','',*[f'- {k}：{fmt(e)}。' for k,e in included.items()],'','H4全部随机分母下的情形：','',*[f'- {k}：{fmt(v["effect"])}。' for k,v in scenarios.items()],'',f'H4点识别边界：RD {result["H4_identification_bounds"]["RD"]}；RR {result["H4_identification_bounds"]["RR"]}。这些边界不包含抽样不确定性，不能称95%区间。','', '次级探索性完整病例固定效应：'+json.dumps(result['exploratory_complete_case_pool'],ensure_ascii=False),'','全部54种指派的效应、区间和次级合成见 artifacts/results.json。所有区间均为近似抽样区间，不覆盖偏倚、缺失机制和文献选择的不确定性。']
    (ROOT/'notes/numerical-results.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    result['elapsed_seconds']=time.perf_counter()-t
    (ROOT/'artifacts/results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':'completed','elapsed_seconds':result['elapsed_seconds'],'flow':result['flow'],'effects':included,'bounds':result['H4_identification_bounds'],'pool':result['exploratory_complete_case_pool']},ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
