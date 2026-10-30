import collections
import csv
import hashlib
import json
import math
from pathlib import Path
import shlex

BASE=Path('STUDY_ROOT');ROOT=BASE/'numeric-replays'
REFROOT=Path('EVALUATION_ROOT')
RAW=Path('RAW_DATA_DIR')
def load(p):return json.loads(p.read_text())
def rows(p):
    with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
audit=load(BASE/'numeric-replay-audit.json');ref=load(REFROOT/'references/data-numbers.json')
rawhour=rows(RAW/'hour.csv');rawday=rows(RAW/'day.csv')

class Checks:
    def __init__(self):self.items=[]
    def add(self,field,a,e):
        numeric=isinstance(e,(int,float)) and not isinstance(e,bool)
        error=abs(a-e) if numeric else 0 if a==e else None
        self.items.append({'field':field,'actual':a,'expected':e,'absolute_error':error,
                           'passed':math.isfinite(float(a)) and error<=1e-10 if numeric else a==e})
    def report(self):
        return {'checked_fields':len(self.items),'failures':[x for x in self.items if not x['passed']],
                'max_absolute_error':max([x['absolute_error'] for x in self.items if x['absolute_error'] is not None],default=0),
                'all_checks':self.items}

def audit_checks(t):
    trial=t['trial_id'];o=ROOT/trial/'output';style=t['style'];phase=t['phase'];c=Checks()
    years=[2011] if phase=='phase1' else [2011,2012]
    for year in years:
        h=[r for r in rawhour if r['dteday'].startswith(str(year)+'-')]
        d=[r for r in rawday if r['dteday'].startswith(str(year)+'-')]
        dist=collections.Counter(r['dteday'] for r in h)
        freqs=dict(sorted(collections.Counter(dist.values()).items()))
        missing={date:[i for i in range(24) if str(i) not in {r['hr'] for r in h if r['dteday']==date}] for date,n in sorted(dist.items()) if n!=24}
        full=sum(v==24 for v in dist.values());cnt=sum(int(r['cnt']) for r in h)
        def test(name,a,e):c.add(str(year)+'/'+name,a,e)
        if style=='one':
            z=load(o/'data_audit.json');z=z if phase=='phase1' else z[str(year)]
            expect={'hour_rows':len(h),'day_rows':len(d),'hour_date_count':len(dist),'day_date_count':len(d),
              'hour_duplicate_keys':0,'day_duplicate_keys':0,'hour_duplicate_full_rows':0,'day_duplicate_full_rows':0,
              'hour_empty_cells':0,'day_empty_cells':0,'hour_count_identity_failures':0,'day_count_identity_failures':0,
              'hour_out_of_range':0,'hour_wrong_calendar_year':0,'day_wrong_calendar_year':0,
              'complete_24h_dates':full,'missing_calendar_hours':24*len(d)-len(h),
              'hour_count_distribution':{str(k):v for k,v in freqs.items()},
              'hour_yr_values':[year-2011],'day_yr_values':[year-2011],
              'daily_count_mismatches':[],'calendar_field_mismatches':[],
              'annual_count_hour_sum':cnt,'annual_count_day_sum':cnt,'mean_daily_count':cnt/len(d),
              'hour_count_negative_values':0,'hour_negative_counts':0,'day_negative_counts':0,'workingday_out_of_range':0}
            for key,e in expect.items():
                if key in z:test(key,z[key],e)
        elif style=='two':
            z=load(o/'audit.json');z=z if phase=='phase1' else z[str(year)]
            expect={'hour_rows':len(h),'day_rows':len(d),'hour_dates':len(dist),'day_dates':len(d),
              'hour_columns':17,'day_columns':16,'duplicate_hour_keys':0,'duplicate_day_keys':0,
              'empty_cells':{'hour':0,'day':0},'duplicate_instant':{'hour':0,'day':0},
              'count_identity_failures':{'hour':0,'day':0},
              'hours_per_date_distribution':{str(k):v for k,v in freqs.items()},
              'missing_calendar_hour_count':24*len(d)-len(h),'missing_calendar_hours':missing,
              'hour_day_count_mismatches':[],'within_date_workingday_conflicts':[] if phase=='phase1' else 0,
              'hour_day_calendar_conflicts':0,'workingday_definition_failures':0,'calendar_conflicts':0,
              'date_calendar_failures':0,'invalid_hour_values':0,'annual_total_cnt':cnt,'mean_daily_cnt':cnt/len(d)}
            for key,e in expect.items():
                if key in z:test(key,z[key],e)
        else:
            z=load(o/('audit.json' if phase=='phase1' else f'quality_{year}/audit.json'))
            for scale,source in [('hour',h),('day',d)]:
                expect={'rows':len(source),'duplicate_keys':0,'blank_cells':0,'duplicate_instant':0,
                        'count_identity_failures':0,'cnt_total':cnt,'cnt_min':min(int(r['cnt']) for r in source),
                        'cnt_max':max(int(r['cnt']) for r in source),'daily_mean':cnt/len(d),
                        'expected_calendar_hours':24*len(d),'missing_calendar_hours':24*len(d)-len(h),
                        'hours_per_day_distribution':{str(k):v for k,v in freqs.items()},'complete_24h_dates':full,'invalid_hours':0}
                for key,e in expect.items():
                    if key in z[scale]:test(scale+'/'+key,z[scale][key],e)
            test('hour_day_discrepancies',z['hour_day_discrepancies'],[])
            test('calendar_field_conflicts',z['calendar_field_conflicts'],[])
            test('hour_day_calendar_conflicts',z['hour_day_calendar_conflicts'],0)
    return c.report()

def table_checks(t):
    trial=t['trial_id'];o=ROOT/trial/'output';style=t['style'];c=Checks()
    file='metric_comparison.csv' if style=='three' else 'comparison_metrics.csv'
    aa=rows(o/file);c.add('row_count',len(aa),16 if style=='one' else 8)
    for i,row in enumerate(aa):
        label=row.get('evaluation',row.get('period'))
        phase='phase1' if label.startswith('2011') else 'phase2'
        scope=row.get('scope',row.get('subset'))
        scope=({'all':'overall','all_observed':'overall','complete_24h_dates':'full24_dates_sensitivity',
                'workingday_0':'workingday=0','workingday_1':'workingday=1'}.get(scope,scope))
        z=ref[phase]['subgroups'][scope] if scope.startswith('workingday=') else ref[phase][scope]
        aliases={'n_hours':'hours','n_dates':'days','hours':'hours','dates':'days',
            'MAE_difference_C0_minus_C1':'MAE_reduction_absolute','relative_MAE_reduction':'MAE_reduction_fraction',
            'date_equal_MAE_difference':'day_equal_weight_mean_MAE_difference','date_equal_relative_MAE_reduction':'day_equal_weight_MAE_reduction_fraction',
            'MAE_absolute_difference_C0_minus_C1':'MAE_reduction_absolute','MAE_relative_reduction':'MAE_reduction_fraction',
            'day_equal_absolute_difference_C0_minus_C1':'day_equal_weight_mean_MAE_difference','day_equal_relative_reduction':'day_equal_weight_MAE_reduction_fraction',
            'absolute_improvement':'MAE_reduction_absolute','relative_improvement':'MAE_reduction_fraction',
            'day_equal_absolute_improvement':'day_equal_weight_mean_MAE_difference','day_equal_relative_improvement':'day_equal_weight_MAE_reduction_fraction'}
        for m in ('C0','C1'):
            for name,target in [('hour_weighted_MAE','MAE'),('hour_weighted_RMSE','RMSE'),('MAE','MAE'),('RMSE','RMSE'),
                    ('mean_bias_pred_minus_true','bias_prediction_minus_actual'),('mean_bias_prediction_minus_actual','bias_prediction_minus_actual'),
                    ('date_equal_mean_intraday_MAE','day_equal_weight_MAE'),('day_equal_mean_intraday_MAE','day_equal_weight_MAE')]:
                aliases[m+'_'+name]=m+'_'+target
        if style=='one':
            aliases.update({k:row['model']+'_'+target for k,target in [('MAE','MAE'),('RMSE','RMSE'),
                            ('bias_prediction_minus_actual','bias_prediction_minus_actual'),('day_equal_MAE','day_equal_weight_MAE')]})
        for key,value in row.items():
            if key in ('evaluation','period','scope','subset','model'):continue
            if key not in aliases:raise ValueError('Unmapped comparison CSV field '+key)
            c.add(str(i)+'/'+key,float(value),z[aliases[key]])
    return c.report()

for t in audit['trials']:
    root=ROOT/t['trial_id'];detail=load(root/'numeric-value-checks.json')
    extra={'input_audit':audit_checks(t)}
    if t['phase']=='phase2':extra['comparison_csv']=table_checks(t)
    save(root/'additional-value-checks.json',extra)
    for k,r in extra.items():t['checks'][k]={key:value for key,value in r.items() if key!='all_checks'}
    pred=detail['predictions']['all_checks']
    means=[x for x in pred if x['field'].endswith(('/C0','/C1'))]
    t['prediction_means_max_absolute_error']=max(x['absolute_error'] for x in means)
    t['primary_metrics_max_absolute_error']=t['checks']['main_metrics']['max_absolute_error']
    t['bootstrap_replicates_max_absolute_error']=max(t['checks']['bootstrap_'+str(length)]['max_absolute_error'] for length in (7,28))
    t['max_absolute_error']=max(x['max_absolute_error'] for x in t['checks'].values())
    t['all_numeric_checks_passed']=all(not x['failures'] for x in t['checks'].values())
    t['all_scientific_outputs_byte_identical']=all(x['byte_identical'] for x in t['scientific_output_byte_checks'])

audit['auditor_files_sha256']={name:sha(ROOT/name) for name in ('launch_replays.py','compare_replays.py','finalize_audit.py')}
audit['reference']['output_sha256']={str(p.relative_to(ROOT)):sha(p) for p in sorted(ROOT.glob('reference-replay*/*')) if p.is_file()}
audit['independent_bootstrap_sha256']={p.name:sha(p) for p in sorted(ROOT.glob('independent-phase*-bootstrap-*.csv'))}
audit['auditor_attempt_notes']=[
 'The six delivered entrypoints were each executed once without author-code changes; all six exited zero.',
 'An early independent comparison attempt stopped on an unmapped daily sum_abs_error_C0 column; the auditor mapping was corrected, no delivered code or result was changed.',
 'A redundant independent auditor process was interrupted after identifying avoidable repeated maximum calculations. Its own implementation was optimized; the final successful auditor results were used.',
 'Three reference command executions used distinct new directories and all produced reference artifacts equal to supplied JSON. No sealed or original output was overwritten.'
]
save(BASE/'numeric-replay-audit.json',audit)

lines=['# 独立数值与代码复跑核验','',
 '六份交付脚本均已按各自 RUN.md 在全新副本实际执行，全部 exit 0。未修改交付代码、模型、阈值、seed、B 或 bootstrap；未访问分组映射、个人记忆/skills、运行中的 workspace，未联网安装。只核查代码执行与数值，不评价文字质量或推断实验组别。','',
 '封存产物及原输入前后 SHA-256 全部不变；六个副本中的代码、模型和原结果前后也不变。输入副本逐行与公开原始 hour.csv/day.csv 对应年度切片完全相同。指定参考程序另行运行成功，其模型语义及答案 JSON 与给定独立参考完全相同。','',
 '|产物|任务|exit|参数均值最大误差|逐小时预测均值最大误差|摘要指标最大误差|4000次bootstrap最大误差|新科学输出与封存|',
 '|---|---|---:|---:|---:|---:|---:|---|']
for t in audit['trials']:
    lines.append(f"|{t['trial_id']}|{t['task_id']}|{t['execution']['exit_code']}|{t['checks']['frozen_model']['max_absolute_error']:.3g}|{t['prediction_means_max_absolute_error']:.3g}|{t['primary_metrics_max_absolute_error']:.3g}|{t['bootstrap_replicates_max_absolute_error']:.3g}|{'全部逐字节相同' if t['all_scientific_outputs_byte_identical'] else '见JSON'}|")
lines += ['',
 '每份摘要对照72个数值：总体、完整24小时日期、workingday=0/1四个范围各14项，以及两种块长各8项（B、seed、块长、日期数、两类95%区间四端点）。14项包括日期/小时数、C0/C1的MAE、RMSE、prediction-minus-actual偏差及按日等权MAE、两种加权下的绝对和相对改善。所有数值通过预先固定的绝对容差1e-10。','',
 '逐小时核验还检查日期、小时、workingday、实际cnt、fallback和所有交付误差列；每日误差表检查全部已交付数值。均值、计数、每日误差和参数sum/n完全一致。D02–D05部分逐小时平方误差列有浮点运算顺序造成的末位差，2011最大2.27e-13、2012最大1.46e-11；这是辅助平方误差列的差，预测值没有差异。主指标和bootstrap最大差为2.84e-14。','',
 'bootstrap由独立审计器重新生成每个抽样日期索引，并真正展开所抽日期的小时误差后重算；每个块长2000次，seed=20261029，循环日期块，截断为原日期数，保留所抽日期的全部实际小时。比较每次重复的样本小时数、两模型MAE、绝对改善、相对改善和重复序号；D01/D06另比较样本日期数。未用运行成功替代数值核验。','',
 '## 字段语义映射','',
 '|参考字段|D01/D06|D02/D04|D03/D05|',
 '|---|---|---|---|',
 '|overall|overall|all|all_observed|',
 '|full24_dates_sensitivity|complete_24h_dates|complete_24h_dates|complete_24h_dates|',
 '|subgroups.workingday=w|by_workingday.w|workingday.w|workingday.w|',
 '|hours / days|n_hours / n_dates|n_hours / n_dates|hours / dates|',
 '|Cx_MAE / Cx_RMSE|Cx.MAE / Cx.RMSE|Cx.hour_weighted_MAE / Cx.hour_weighted_RMSE|Cx.MAE / Cx.RMSE|',
 '|Cx_bias_prediction_minus_actual|Cx.bias_prediction_minus_actual|Cx.mean_bias_pred_minus_true|Cx.mean_bias_prediction_minus_actual|',
 '|Cx_day_equal_weight_MAE|Cx.day_equal_MAE|Cx.date_equal_mean_intraday_MAE|Cx.day_equal_mean_intraday_MAE|',
 '|MAE_reduction_absolute|hour_weighted_absolute_improvement|MAE_difference_C0_minus_C1|MAE_absolute_difference_C0_minus_C1|',
 '|MAE_reduction_fraction|hour_weighted_relative_improvement|relative_MAE_reduction|MAE_relative_reduction|',
 '|day_equal_weight_mean_MAE_difference|day_equal_absolute_improvement|date_equal_MAE_difference|day_equal_absolute_difference_C0_minus_C1|',
 '|day_equal_weight_MAE_reduction_fraction|day_equal_relative_improvement|date_equal_relative_MAE_reduction|day_equal_relative_reduction|',
 '|bootstrapN.absolute_difference_percentile95|bootstrap.N.absolute_improvement_95ci|bootstrap.N.difference_CI95|bootstrap列表中block_days=N的absolute_difference_CI95|',
 '|bootstrapN.relative_reduction_percentile95|bootstrap.N.relative_improvement_95ci|bootstrap.N.relative_reduction_CI95|bootstrap列表中block_days=N的relative_reduction_CI95|','',
 '模型均值按语义比较：C0共24个hr单元，C1共48个workingday/hr单元。键中的逗号和冒号仅作为分隔形式归一化；比较每个mean、sum或sum_cnt、n，不比较无关JSON格式。共72个均值全部精确相同。参考还包含weather分组，六份交付摘要仅报告workingday分组；没有把参考中额外的weather数值算作交付已报告结果。','',
 '## 双年比较与冻结核验','',
 '|指标|2011全年|2012全年|',
 '|---|---:|---:|',
 '|实际小时数|8645|8734|',
 '|日期数|365|366|',
 '|完整24小时日期|305|350|',
 '|缺失日历小时|115|50|',
 '|cnt总量|1243103|2049576|',
 '|日均cnt|3405.7616438356163|5599.934426229508|','',
 'D04–D06全部年度数值与参考一致：年度总量增长0.6487579870694544，日均增长0.6442531838260952。三份比较CSV逐行、逐数值比较通过，包含两个评价期的四个范围、全部模型及按日等权指标。2012-10-29只有1个实际小时，10-30有11个，原输入未补齐；完整24小时敏感性只含350日/8400小时。','']
for t in audit['trials']:
    if t['phase']=='phase2':
        f=t['freeze'];lines.append(f"- {t['trial_id']} → 前阶段 {f['predecessor']}：原模型和原评分代码均逐字节保留；模型SHA `{f['model_sha256']}`。更新入口无fit/train调用，读取2011训练记录仅核对sum/n/mean，2012标签只进入审计和误差评价。")
lines += ['',
 'D04/D05的新输出还完整重播2011留出集，所有摘要、逐小时预测、每日误差及4000次bootstrap通过，且与封存历史科学结果逐字节一致。D06实际更新入口重播并断言2011总体指标，另外本审计核对其封存阶段A的全部72个摘要值和保留模型/代码；不把它描述为更新入口重播了整个2011bootstrap。','',
 '## 实际执行命令与哈希','',
 '以下参数只把RUN.md中的入口、模型、旧结果和输入路径映射到新副本，并使用新的output目录。没有发明未声明接口。每条实际argv、解释器版本、入口和全部Python文件SHA、每个输出文件SHA、stdout/stderr SHA、前后源文件清单均保存在主JSON对应execution字段及各副本execution-record.json。','']
for t in audit['trials']:
    e=t['execution'];lines += [f"### {t['trial_id']}",'',f"入口SHA-256：`{e['entry_sha256']}`；exit={e['exit_code']}。",'', '```sh',shlex.join(e['argv']),'```','']
lines += ['## 检查范围及失败记录','',
 '作者六份实际复跑没有失败或unavailable。未做内容评分、文献审核、统计稳定性推断或组别比较。作者RUN.md中的独立验证器没有另行运行；结论来自实际分析入口复跑和本审计对原始公开数据、给定参考、封存数值以及新输出的独立检查。','',
 '审计器自身第一次字段映射遇到sum_abs_error_C0未映射而停止，只修正了本审计器的别名；另一个冗余审计进程因重复最大值计算而中止，优化的仍仅为本审计器。六份交付脚本均只实际运行一次，原封存及输出完全未动。参考程序三个实际执行均写不同新目录并得到相同答案。最终审计无未映射数值或未解决失败。','',
 '主结构化报告：`numeric-replay-audit.json`；每个新副本：`numeric-replays/Dxx/`；逐项实际值、参考值、误差和通过标识：各副本`numeric-value-checks.json`与`additional-value-checks.json`。独立小时展开bootstrap CSV与参考重跑也在numeric-replays/。']
(BASE/'numeric-replay-audit.md').write_text('\n'.join(lines)+'\n')
print(json.dumps({'all_six_passed':all(t['all_numeric_checks_passed'] and t['all_scientific_outputs_byte_identical'] for t in audit['trials']),
                  'reports':[str(BASE/'numeric-replay-audit.md'),str(BASE/'numeric-replay-audit.json')],
                  'extra_checks':{t['trial_id']:{k:(r['checked_fields'],r['max_absolute_error'],len(r['failures'])) for k,r in t['checks'].items() if k in ('input_audit','comparison_csv')} for t in audit['trials']}},ensure_ascii=False,indent=2))
