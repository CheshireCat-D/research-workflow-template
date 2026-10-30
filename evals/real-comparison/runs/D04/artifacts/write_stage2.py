#!/usr/bin/env python3
import json,pathlib
w=pathlib.Path(__file__).resolve().parent
a=json.loads((w/'results_2012/annual_summary.json').read_text());r=json.loads((w/'results_2012/results.json').read_text());p=json.loads((w/'results/results.json').read_text());m=json.loads((w/'results/model.json').read_text())
f=lambda x:f'{x:.6f}'
pct=lambda x:f'{100*x:.6f}%'
z=r['all'];old=p['all'];full=r['complete_24h_dates']
report=f'''# 冻结日历模型的2012年时间外验证

2012年全部8734个已观察小时上，C1的MAE为{f(z['C1']['hour_weighted_MAE'])}，较C0的{f(z['C0']['hour_weighted_MAE'])}降低**{pct(z['relative_MAE_reduction'])}**，仍有改善，但**未达到预设10%门槛**。7日和28日配对块区间都支持改善；对“真实改善是否低于10%”，两种块长的结论敏感，须并列解释。2011第四季度改善24.231724%的历史结论仍保留，不能据此称本模型跨年已足够部署。

## 数据对象、来源与恢复证据

结局是Capital Bikeshare单系统已记录小时的租车次数cnt。小时记录是系统日期×小时的聚合观测，日记录是日期聚合；不是独立用户，也不识别工作日安排的因果效果。来源：Fanaee-T, H. (2013), *Bike Sharing*, UCI Machine Learning Repository，[数据集 DOI](https://doi.org/10.24432/C5W894)，当前页面标注[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)。随附CSV仅按年份切片。原README请求引用Fanaee-T与Gama的“Event labeling combining ensemble detectors and background knowledge”，DOI 10.1007/s13748-013-0040-3；本次未读其论文正文。来源核验限于随附README、2026-10-29官方页离线摘录、SOURCES.md和清单，未联网。

恢复依据为原analyze.py、results/model.json、原报告与交接及实际输出，没有聊天历史。先保存旧报告、交接、RUN、执行记录和清单到stage1_archive/；首次results/和score_check/不覆盖。旧清单内24个原有产物的SHA均一致。原模型完整可读，无需重建；以原2011记录重新核对每组和、样本数、均值，只用于一致性核验，预测仍加载原参数。全部72个单元逐项匹配。没有用2012拟合、调参、重估均值、选择特征，也没有把2011第四季度放入训练。

实际训练范围2011-01-01至09-30：6442小时、273日期；留出2011-10-01至12-31：2203小时、92日期。C0的24个单元是相同hr训练cnt的未舍入算术均值；C1的48个单元是相同(workingday,hr)训练均值。未见C1组合回退C0，未见C0小时报错；2012回退0次。模型只用hr和预测时可知的日历workingday，不用天气、instant、日期数值、casual、registered或yr。日表仅用于数据审查。

冻结模型SHA-256：`f8a758c6c73cf7e0cfcfa0936b594afb8f23b1260610ecae15929f601dc8e5d4`。
原评分代码SHA-256：`9aa68881931fdb685b4c27ea5c5f976b9576e49fac937140b18cc396bad6f32b`。本次直接调用其predict/evaluate/metrics/bootstrap，代码和模型运行前后摘要一致。重新评分2011留出集，完整results.json以及预测、日误差、两份bootstrap逐字节复现原输出，既有证据可定位至results/，不以新报告替换旧数值。

输入摘要均匹配本阶段清单，2011两文件还与原阶段输入逐字节匹配：

| 文件 | SHA-256 |
|---|---|
| hour_2011.csv | 294d25e98ef1c9c9cec746e17ba3ff9818627ba5aa14baf1b93db7ae218de115 |
| day_2011.csv | a15d6536bae4f15ec0b27ccef8b510a9fd7caf46b2f1dbe1ffd00c6a32920d5b |
| hour_2012.csv | d73ae7f2aba616d775b5bccb3540910a9de49fe88e7f5926f7bf0a3fe840602d |
| day_2012.csv | 75c2dd61bc5f8a3cd6ae5c787c74c0fbc1547201d47c5cba878d29f3083f09b6 |

这证明收到的切片身份与清单一致，不独立认证未接触的原始出行日志。

## 数据完整性及年度变化

| 检查 | 2011 | 2012 |
|---|---:|---:|
| 日期范围 | 01-01至12-31 | 01-01至12-31 |
| 小时记录 / 日期数 | 8645 / 365 | 8734 / 366 |
| 日表记录 / 日期数 | 365 / 365 | 366 / 366 |
| 小时列 / 日列 | 17 / 16 | 17 / 16 |
| 空单元格、重复日期小时键、重复日键 | 均0 | 均0 |
| 两表各自重复instant | 均0 | 均0 |
| casual+registered≠cnt的行数 | 0 | 0 |
| 按日汇总三种计数与日表不一致项 | 0 | 0 |
| 缺日期 / 缺日历小时 | 0 / 115 | 0 / 50 |
| 完整24小时日期 / 不完整日期 | 305 / 60 | 350 / 16 |

2011每日期小时数分布为8:1日、12:1、16:1、17:1、18:2、22:6、23:48、24:305；2012为1:1日、11:1、23:14、24:350。2012-10-29只观察到00时一行，10-30观察到13—23时11行；其余14个不完整日期各23行。全部缺小时明细在results_2012/audit.json。2012预期366×24=8784个日历小时，实有8734行；“无空单元格”仍不表示完整小时网格。未补零、未插值、未估计缺小时需求，也未将缺口归因于未经核实的具体事件。

两年小时与日表日期集合相同；日期内workingday一致；workingday/holiday/weekday/mnth/yr在小时与日表一致，星期、月份、年份也与日期相符。workingday符合非周末且非假日取1。

| 年份 | 已记录年度总次数 | 每日计数均值 | 日期分母 |
|---|---:|---:|---:|
| 2011 | 1,243,103 | 3405.761644 | 365 |
| 2012 | 2,049,576 | 5599.934426 | 366 |

年度总数增长**64.875799%**；每日日计数均值增长**64.425318%**。2012为366日而2011为365日，因此日均增长=(1+总数增长)×365/366−1，不能直接用总数增幅代替日均增幅。这些是提供表中已观察计数的年度汇总；日表与小时表相加一致仍不能证明缺小时的真实需求为零。

两年小时行数合计17,379，与README一致，当前UCI摘录的17,389仍有10行差异；这更新了原来仅凭2011无法核对总行数的限制，不擅改任何观测。其他原文冲突仍保留：README season=1/2/3/4标春/夏/秋/冬，当前页标冬/春/夏/秋；README给temp=t/41、atemp=t/50，当前页仅小时尺度给temp=(t+8)/47、atemp=(t+16)/66。模型不用这些变量，本阶段不选择逆变换公式或重贴标签。

## 同口径冻结评分

令e=预测−实际。小时MAE=Σ|e|/N，RMSE=√(Σe²/N)，偏差=Σe/N；绝对差Δ=MAE0−MAE1，相对降幅r=1−MAE1/MAE0。日期等权MAE先计算各日已观察小时的MAE，再对D日等权平均；不是日总计数误差。门槛始终针对总体小时加权r≥10%。表格舍入仅用于展示，计算及CSV保存全精度。

| 指标 | 2011留出C0 | 2011留出C1 | 2012全年C0 | 2012全年C1 |
|---|---:|---:|---:|---:|
| 小时MAE | 58.825190 | 44.570832 | {f(z['C0']['hour_weighted_MAE'])} | {f(z['C1']['hour_weighted_MAE'])} |
| 小时RMSE | 86.080569 | 67.999969 | {f(z['C0']['hour_weighted_RMSE'])} | {f(z['C1']['hour_weighted_RMSE'])} |
| 平均偏差 | 1.078965 | 0.987153 | {f(z['C0']['mean_bias_pred_minus_true'])} | {f(z['C1']['mean_bias_pred_minus_true'])} |
| 日期等权日内MAE | 58.848613 | 44.620154 | {f(z['C0']['date_equal_mean_intraday_MAE'])} | {f(z['C1']['date_equal_mean_intraday_MAE'])} |

2011留出小时Δ=14.254358、r=24.231724%；日等权差14.228459、降幅24.178071%。2012小时Δ=**{f(z['MAE_difference_C0_minus_C1'])}**、r=**{pct(z['relative_MAE_reduction'])}**；日等权差=**{f(z['date_equal_MAE_difference'])}**、降幅=**{pct(z['date_equal_relative_MAE_reduction'])}**。两种权重均未达10%。

2012相较2011留出，C0/C1绝对MAE分别增至约{z['C0']['hour_weighted_MAE']/old['C0']['hour_weighted_MAE']:.3f}/{z['C1']['hour_weighted_MAE']/old['C1']['hour_weighted_MAE']:.3f}倍，绝对改善从14.254358降至9.410155，相对改善从24.231724%降至7.966722%。偏差从约+1变为约−91.5次/小时，两模型都系统性低估。年度已观察需求水平上升与这种方向相容，但无法凭聚合对比确定原因；训练均值固定、比较窗口一为第四季度一为全年，季节构成、日历组成及水平变化均可能参与，不能将全部恶化归因于单一年度效应。

| 2012评价范围 | 日期 / 小时 | C0 MAE | C1 MAE | Δ | 相对降幅 |
|---|---:|---:|---:|---:|---:|
'''
for name,v in [('仅完整24小时日期',full),('workingday=0（周末或假日）',r['workingday']['0']),('workingday=1',r['workingday']['1'])]:
    report+=f"| {name} | {v['n_dates']} / {v['n_hours']} | {f(v['C0']['hour_weighted_MAE'])} | {f(v['C1']['hour_weighted_MAE'])} | {f(v['MAE_difference_C0_minus_C1'])} | {pct(v['relative_MAE_reduction'])} |\n"
report+=f'''
完整日C0/C1 RMSE={f(full['C0']['hour_weighted_RMSE'])}/{f(full['C1']['hour_weighted_RMSE'])}，偏差={f(full['C0']['mean_bias_pred_minus_true'])}/{f(full['C1']['mean_bias_pred_minus_true'])}；日期等权MAE与小时MAE相同（末位浮点差异除外），日等权差9.311430、降幅7.776923%，仍未达10%。筛选完整日改变了评价日期集合，不代表填补未观测小时。2011完整日降幅25.549971%、workingday=0/1降幅37.618609%/12.611713%，原值保留于results/results.json及comparison_metrics.csv。2012非工作日点估计17.408898%高于10%，工作日仅3.007152%；不能改用更有利子组替代总体预设门槛。未对子组另造区间；其余分组RMSE、偏差和日期等权指标完整保存在results_2012/results.json与comparison_metrics.csv。

## 配对块区间与门槛

完全沿用原算法：按日期排序，同次给两个模型相同抽样日期；random.Random(20261029)，每次用randrange(D)抽起点，取连续L日并循环，反复抽至至少D日后截断到D。抽中日保留全部已观察小时，重复日期重复计数，以合并绝对误差除以合并小时数重算MAE，再求Δ和r。B=2000，7日与28日块各自从同seed重新开始；95%百分位区间以排序后(B−1)p位置线性插值，p=.025/.975。2011 D=92；2012 D=366。没有把小时视为独立抽样单位。

| 时期 | 块长 | Δ的95%区间 | r的95%区间 |
|---|---:|---:|---:|
| 2011留出 | 7日 | [10.800923, 17.578082] | [17.071941%, 31.483288%] |
| 2011留出 | 28日 | [9.815820, 18.334213] | [15.571346%, 32.544908%] |
'''
for L in ('7','28'):
    b=r['bootstrap'][L];report+=f"| 2012全年 | {L}日 | [{f(b['difference_CI95'][0])}, {f(b['difference_CI95'][1])}] | [{pct(b['relative_reduction_CI95'][0])}, {pct(b['relative_reduction_CI95'][1])}] |\n"
report+='''
2012两种区间下限均大于0，支持C1有正向改善。样本点估计7.966722%明确未达实务门槛；7日区间上限9.967439%略低于10%，而28日区间包含10%。因此“低于10%的统计证据”对块长敏感：7日设定下区间全部低于门槛，28日设定下不能排除达到10%；两种设定均不支持把“至少10%”当作已获证实。不能择取任一块长宣称稳定越过门槛，也不能将区间包含10%解释为达到10%。

区间描述给定冻结模型、以本期误差日期序列经验重采样时差异的波动，未纳入训练参数不确定性或未观察小时误差。作为时间总体推断近似，需要该时期误差过程足够稳定、块内依赖代表目标时间、较长相关衰减等条件。全年季节变化与需求变化可能破坏近似平稳性，循环拼接年末年初也是近似；28日块不会自动消除这些问题。区间不是未来年份表现保证。

## 更新后的判断与下一项研究

1. **保留历史结论**：原2011第四季度、指定冻结模型与评价口径下，C1改善24.231724%，两种块区间均高于10%。新数据不抹去这项有限结论。
2. **更新跨年主张**：2012仍支持C1改善，但绝对误差明显上升，平均偏差大幅负移；2011改善幅度不能直接推广到2012。新数据推翻“2011表现即可保证下一年达到门槛”的外推。
3. **区分门槛和部署**：2012总体点估计未达到10%，区间也未稳健确立达到门槛。即使改善为正，也尚不足部署：两个模型都严重低估，且没有针对运营损失、校准容忍度或实际运营收益的验证。单系统历史审查也不能推断个体或因果作用。
4. **具体后续研究**：另立“适应需求水平漂移”的新模型比较：在获得后续年份前，预先规定一个仅用过去28个完整日期、估计总体水平乘数的滚动校准C1，与原冻结C1比较，禁止使用待预测日标签；在2012内部严格滚动起点开发，随后用未用于开发的后续年份作最终时间验证，同时预设MAE、偏差容忍度与运营成本判据。该校准只是一项待测试方案，本次没有拟合、挑选窗口或报告其性能；本次结果只属于原冻结C0/C1。

## 可复现交付

update2012.py参数化接收本阶段输入、原2011输入、冻结模型、原评分代码、原结果与新输出目录；不调用fit。RUN.md有完整命令。results_2012/保存首次2012实际输出、逐小时预测、逐日误差、4000个块抽样复本、年度表、数据审查及参数恢复证据；recovery_2011/记录冻结加载后的历史复算。comparison_metrics.csv并列新旧所有范围。

verify2012.py用独立算术重算总体、完整日、工作日两组所有指标，并用循环序列前缀和方法复核4000次配对块复本及区间，全部通过。另以新输出目录复跑，9个科学结果文件逐字节相同，首次结果保留。此核对支持计算一致性，不替代时间稳定性假设。原结果在results/；原文字与执行记录在stage1_archive/；handoff.md列出冻结规则、最新判断及下一步；execution.json保留实际读取摘要与命令。
'''
assert len(report)<=12000,len(report)
(w/'report.md').write_text(report,encoding='utf-8')
handoff=f'''# 2012阶段交接

本阶段已执行。先读report.md、RUN.md；无需聊天历史。唯一冻结模型仍是results/model.json，SHA-256 f8a758c6c73cf7e0cfcfa0936b594afb8f23b1260610ecae15929f601dc8e5d4。原评分代码analyze.py SHA 9aa68881931fdb685b4c27ea5c5f976b9576e49fac937140b18cc396bad6f32b。不要覆盖这两文件或首次results/、results_2012/。

训练2011-01-01至09-30（6442小时、273日）；原留出10-01至12-31（2203小时、92日）。C0=hr训练算术均值，C1=(workingday,hr)训练均值；未见C1回退C0，未见C0小时报错。24/48个单元完整，均未舍入。只用hr、预测时已知日历workingday。没有2012重训或2011留出回流。本阶段逐单元核对原训练记录的sum/n/mean全部一致，原2011预测/指标/抽样复本逐字节复现，无恢复缺项。

输入在D04/input；2011 SHA与D02/input原件一致。2012小时8734行/366日，日366行；均无空单元格、重复键、恒等式或小时-日计数不一致。2012少50日历小时，350日完整，14日23小时，10-29只有00时，10-30只有13—23时。未补零或归因。2011少115小时、60日不完整。年度总数1243103→2049576，增长64.875799%；日均3405.761644→5599.934426，增长64.425318%，分母365→366。数据与模型SHA汇总见report.md、results_2012/provenance.json、audit.json、model_recovery.json。README与官方页行数/季节/温度公式冲突按报告保留；模型未使用冲突变量。

2012全部观察小时C0/C1：MAE118.118276/108.708122，RMSE174.111341/157.211075，偏差（预测减真值）−91.533694/−91.613465。差9.410155，降幅7.966722%；日等权MAE117.775867/108.360746，差9.415121，降幅7.994100%。完整日350日/8400小时MAE119.731538/110.420108，降幅7.776923%；workingday0/1降幅17.408898%/3.007152%。分组完整指标见results_2012/results.json和comparison_metrics.csv。

块bootstrap与阶段1完全一致：B2000，random.Random(20261029)，randrange(D)起点、循环连续L日抽至D并截断、保留日内全部小时且小时合并加权；L7/28分别重置seed；排序(B−1)p线性插值95%区间。2012 D366，L7差区间[8.083961,10.825503]、降幅[6.476413%,9.967439%]；L28差[7.667940,11.466771]、降幅[5.709841%,11.589625%]。

当前结论：两块长均支持改善；2012点估计未达10%，对是否真实低于10%存在块长敏感性（7日区间全低于，28日包含）；不可选择更有利块长。2011留出24.231724%及其两块区间高于10%的有限结论仍成立。总体绝对误差和负偏差显著变差，尚不足部署。区间不含训练不确定性/未观测小时，也依赖稳定性；不能保证未来。

产物：report.md当前主报告；stage1_archive/保存旧报告/交接/RUN/执行记录与旧清单，24个旧产物原摘要均匹配。results/保留原结果模型；results_2012/为首次新结果与独立验证，recovery_2011/为历史加载复算；reproduction_2012/为新目录复跑，9个科学文件摘要一致。analyze.py原评分；update2012.py完整年度更新入口（不调用fit）；verify2012.py独立指标与4000复本验证；write_stage2.py只从结果写文字。命令见RUN.md，输出须为空或不存在。

下一步：将“用过去28个完整日期滚动估计水平乘数校准C1”另立研究，不改变本次模型；预先规定滚动起点、指标/偏差容忍度/成本判据，用2012作开发后必须留后续年份最终测试。本次未实现或验证该候选性能。若仅获取新的授权年份评价原模型，可用analyze.py score并指定冻结model.json与新输出目录，先做对应年份完整性审查。update2012.py专用于本次2011/2012核对，不要误当任意年份训练器。
'''
(w/'handoff.md').write_text(handoff,encoding='utf-8')
run='''# 冻结模型与2012更新复跑

使用共同Python标准库，无需安装。所有参数可以改为同内容文件的新位置；输出目录必须为空或不存在。以下不训练模型，必须保留原冻结model.json与analyze.py。

```sh
PY=EVAL_PYTHON
WS=WORKSPACE
INPUT=INPUT_DIR
PRIOR_INPUT=PRIOR_INPUT_DIR
OUT=WORKSPACE/another_reproduction_2012
"$PY" -I -B "$WS/update2012.py" --input-dir "$INPUT" --prior-input "$PRIOR_INPUT" --model "$WS/results/model.json" --prior-results "$WS/results/results.json" --original-code "$WS/analyze.py" --output-dir "$OUT"
"$PY" -I -B "$WS/verify2012.py" --output-dir "$OUT" --model "$WS/results/model.json"
```

update2012.py校验四个CSV与INPUT_MANIFEST，核对2011原件、原训练和/n/mean、原模型/代码SHA；加载冻结模型复算2011留出并与旧结果比较，再评分2012。没有调用fit。其audit按年份生成完整日历，未调用原2011专用audit函数检查2012。目录中results.json为所有指标与区间；audit.json为两年核验和缺小时；annual_summary.json为年度总数/日均/增长；model_recovery.json为训练恢复核验；comparison_metrics.csv并列两个时期所有范围。predictions.csv、daily_errors.csv及bootstrap_7/28.csv保留全精度首次数据。

本阶段实际执行上述入口写results_2012，再执行verify2012.py，全部通过；另复跑至reproduction_2012，9个科学结果文件逐字节相同，见results_2012/reproduction_check.json。provenance.json因命令和耗时差异而不同。第一次结果未替换。验证使用独立指标算术及前缀和块和校验，不据运行成功宣称统计稳定性。

只评分其他获授权新年份时，可用原接口（先核验数据，不改均值）：

```sh
"$PY" -I -B "$WS/analyze.py" score --hour-file /path/to/authorized/hour_new.csv --model "$WS/results/model.json" --output-dir /path/to/new_score_directory --start YYYY-01-01 --end YYYY-12-31
```

score必需字段dteday、hr、workingday、cnt；模型均值只由hr/workingday检索，cnt仅用于评价。无需train。原2011复跑说明保存在stage1_archive/RUN.md；仅用于历史复现，不用于本阶段或未来评分重训。
'''
(w/'RUN.md').write_text(run,encoding='utf-8')
print(json.dumps({'report_characters':len(report),'handoff_characters':len(handoff),'report':str(w/'report.md')},ensure_ascii=False))
