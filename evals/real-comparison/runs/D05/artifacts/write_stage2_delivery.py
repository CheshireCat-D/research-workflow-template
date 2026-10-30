#!/usr/bin/env python3
"""Render the report and handoff from the first, preserved 2012 results."""
import json
from pathlib import Path

w = Path(__file__).resolve().parent
new = w/'results2012'
load = lambda p: json.loads(p.read_text(encoding='utf-8'))
r = load(new/'results.json')
old = load(w/'results/results.json')
annual = load(new/'annual.json')
audits = {year:load(new/f'quality_{year}/audit.json') for year in (2011,2012)}
recovery = load(new/'model_recovery.json')
v = load(new/'verification.json')
fmt = lambda x:f'{x:.6f}'
pct = lambda x:f'{100*x:.6f}%'
parts = ['''# 冻结日历模型的跨年检验

2011留出期的有限结论仍成立；2012新证据支持C1相对C0改善，但本次全部已观测小时的降幅未达到预定10%门槛。7日块区间与28日块区间对10%的覆盖不同，不能挑选块长来加强结论。两个模型的跨年低估也很明显，现有证据不足以部署这个冻结原型。

## 从文件恢复及冻结核验

本次从原交接、代码、模型、首次结果及执行记录恢复，没有使用前次对话。所需证据齐全，无需补造模型或先前结果。原报告、交接、运行说明和执行记录另存于`stage1_snapshot/`；原首次结果继续保存在`results/`，未覆盖。下面的历史数值均能定位到`results/results.json`和该快照原报告。

实际训练范围为2011-01-01至2011-09-30，共273日、6442小时；2011-10-01至12-31的92日、2203小时仍是历史留出，没有加入训练。只读取2011年前九个月核对参数，不用2012重新训练、重估均值、选特征或调参。

对训练集合T，C0(h)=Σ(cnt_i:hr_i=h)/n_h；C1(w,h)=Σ(cnt_i:workingday_i=w,hr_i=h)/n_{w,h}。C1未见组合回退C0；预测不取整。训练覆盖全部24个hr和48个(workingday,hr)组合，两次评估均无回退。除hr与workingday外，其余字段均不作预测输入；日期用于切分、按日汇总与块抽样。workingday必须由预报时可用的周末及节日日历给出。

读取的`results/model.json`格式为calendar-mean-v1，冻结于2011-09-30日终，保存各组sum、n及mean。SHA256=`dba591a44fff2d14514b4b38d00c8985e93f41cf2b1ab684a6abd2f2620d078d`，本次读取前后均相同。独立重算并精确核对72组的和、样本数及均值；训练cnt合计930,102。C0各组n为247至273，C1为75至189。例如8时C0为70327/271=259.509225，C1的非工作日为6299/84=74.988095、工作日为64028/187=342.395722。完整参数仍在原JSON，恢复摘要在`results2012/model_recovery.json`。

用同一模型和原评估代码重播2011留出，结果JSON与首次结果相同；预测、逐日误差、7日与28日bootstrap四个CSV逐字节一致。因此新结果与历史结果对应同一冻结模型、同一算法，而不是替换后的模型。

## 数据身份、质量与年度规模

数据为UCI Bike Sharing的Capital Bikeshare单系统观测。小时表一行是某日某小时的系统总租车数；日表一行是某日系统总数。小时和日表是同一过程的不同聚合，不能当成独立复现样本。随附清单的四份CSV行数及SHA256均核对通过；2011两份输入与原模型来源及原交接哈希一致。2012小时与日表的SHA256分别为`d73ae7f2aba616d775b5bccb3540910a9de49fe88e7f5926f7bf0a3fe840602d`、`75c2dd61bc5f8a3cd6ae5c787c74c0fbc1547201d47c5cba878d29f3083f09b6`。

| 年份 | 小时行/列 | 日行/列 | 日期范围 | 完整24小时日期 | 少于24小时日期 | 缺少日历小时 |
|---|---:|---:|---|---:|---:|---:|
''']
for year in (2011,2012):
    au=audits[year]; h=au['hour'];d=au['day']
    parts.append(f"|{year}|{h['rows']} / {len(h['columns'])}|{d['rows']} / {len(d['columns'])}|{h['dates'][0]}至{h['dates'][1]}|{h['complete_24h_dates']}|{d['rows']-h['complete_24h_dates']}|{h['missing_calendar_hours']}|\n")
parts.append('''
两年份所有日历日期都有记录，小时记录按日期/小时排序，hr均在0至23，yr分别为0和1。两表按(dteday,hr)及dteday检查重复键均为0，instant重复、空单元格、多余单元格均为0。所有小时与日记录都满足cnt=casual+registered；每个日期的casual、registered、cnt小时和与日表一致，2011共1095项、2012共1098项差异均为0。每日期内日历字段一致、小时与日表日历字段一致，weekday与真实日期、workingday与非周末且非节日的定义均无冲突。

每日期观察到的小时数分布如下；无空单元格不能推出日历完整。

| 每日期小时数 | 2011日期数 | 2012日期数 |
|---:|---:|---:|
''')
dist = {year:audits[year]['hour']['hours_per_day_distribution'] for year in (2011,2012)}
for n in sorted(set(dist[2011])|set(dist[2012]),key=int):
    parts.append(f"|{n}|{dist[2011].get(n,0)}|{dist[2012].get(n,0)}|\n")
parts.append('''
2012应有366×24=8784个日历小时，实际8734个，少50个；其16个不完整日期仍按实际记录评分，不补零，不把缺行解释为零需求。小时cnt范围为2011的1至651、2012的1至977。逐日期覆盖、全部缺小时键及完整审计分别见`results2012/quality_2011/`和`quality_2012/`。本次不把少小时日期归因于具体事件；一般性的来源说明不能逐条确认缺行原因。

| 年份 | 年度cnt总数（小时和=日和） | 日表日期数 | 每日日计数均值 |
|---|---:|---:|---:|
''')
for row in annual['years']:
    parts.append(f"|{row['year']}|{row['cnt_total']:,}|{row['observed_dates']}|{fmt(row['daily_mean'])}|\n")
parts.append(f"\n年度总数增长{pct(annual['annual_total_growth'])}，每日日计数均值增长{pct(annual['daily_mean_growth'])}。总数比值=均值比值×366/365，所以两个增长率相差{100*(annual['annual_total_growth']-annual['daily_mean_growth']):.6f}个百分点；2012多一天。它们描述所供观察计数，不恢复缺少小时的未知需求。增长与冻结模型发生水平偏移相符，但不能据此识别增长的具体原因。完整精度见`results2012/annual.json`和`annual.csv`。\n")
parts.append('''
两个年份小时行数合计17,379，与原README一致，但随附UCI页面摘录写17,389；明确保留这一差异。season标签、temp与atemp归一化说明的冲突仍存在：README的temp/atemp逆变换为41x与50x，页面小时尺度说明则为47x−8与66x−16；season也分别标为1春/1冬。本次未选择一个公式或改写观测，这些字段均未进入模型。页面“无缺失值”只与本次无空单元格的检查一致，不能消除少小时问题。

## 同一模型在两个时期的误差

主指标为所有已观测小时等权的MAE=Σ|预测−真实|/N，RMSE=√[Σ(预测−真实)²/N]；偏差=Σ(预测−真实)/N，负数表示低估。比较量Δ=MAE0−MAE1，R=1−MAE1/MAE0，预定实务门槛为R≥10%。误差及差值单位为每小时租车次数；R为相对百分比。

| 评估时期 | 日/小时数 | C0 MAE | C1 MAE | C0 RMSE | C1 RMSE | C0偏差 | C1偏差 | Δ | R |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
''')
for name,res in (('2011年10至12月',old),('2012全年',r)):
    a=res['all_observed']
    parts.append(f"|{name}|{a['dates']} / {a['hours']}|{fmt(a['C0']['MAE'])}|{fmt(a['C1']['MAE'])}|{fmt(a['C0']['RMSE'])}|{fmt(a['C1']['RMSE'])}|{fmt(a['C0']['mean_bias_prediction_minus_actual'])}|{fmt(a['C1']['mean_bias_prediction_minus_actual'])}|{fmt(a['MAE_absolute_difference_C0_minus_C1'])}|{pct(a['MAE_relative_reduction'])}|\n")
parts.append('''
C1在2012仍有较低绝对误差，但两个模型的MAE和RMSE都大幅增加；绝对MAE优势从14.254358降到9.410155，相对优势从24.231724%降到7.966722%。平均偏差从接近0转为约−92，C1分工作日的结构没有解决跨年总体低估，而且C1总体偏差略更负。偏差与MAE量纲一致，但不能用偏差代替MAE，因为正负误差会抵消。

这里比较的是2011年第四季度与2012全年，季节和日期组成并不相同；它说明历史留出结论未自动迁移到新评估期，不能把全部差异识别为纯年份效应。年度计数增长是另一项全年对全年描述，两者的比较窗口不能混用。

日期等权指标先计算每个日期内MAE，再对D个日期取算术平均；它是日内小时误差的均值，不是日总数预测误差。其结果为：

| 评估时期 | C0日期等权MAE | C1日期等权MAE | 差 | 相对降幅 |
|---|---:|---:|---:|---:|
''')
for name,res in (('2011留出',old),('2012全年',r)):
    a=res['all_observed']
    parts.append(f"|{name}|{fmt(a['C0']['day_equal_mean_intraday_MAE'])}|{fmt(a['C1']['day_equal_mean_intraday_MAE'])}|{fmt(a['day_equal_absolute_difference_C0_minus_C1'])}|{pct(a['day_equal_relative_reduction'])}|\n")
parts.append('''
2012日期等权降幅同样低于10%，因此小时数较少的日期权重不足并未改变门槛结论。

## 分组与完整日期敏感性

下表按原workingday分别统计已观测小时；0为周末或节日，1为工作日。仍然使用全体训练期冻结的参数。

| 时期/workingday | 日/小时数 | C0 MAE | C1 MAE | Δ | R |
|---|---:|---:|---:|---:|---:|
''')
for name,res in (('2011留出',old),('2012',r)):
    for group,a in res['workingday'].items():
        parts.append(f"|{name} / {group}|{a['dates']} / {a['hours']}|{fmt(a['C0']['MAE'])}|{fmt(a['C1']['MAE'])}|{fmt(a['MAE_absolute_difference_C0_minus_C1'])}|{pct(a['MAE_relative_reduction'])}|\n")
parts.append('''
2012非工作日点估计仍超过10%，工作日仅3.007152%；总体R不能用两个分组R的简单平均代替。本次未另构造分组置信区间，不能把分组点估计当成已确定的未来组别保证，更不能解释为改变工作日安排的因果效果。

只保留每日期24个不同小时，其他全部不变：

| 时期 | 日/小时数 | C0 MAE | C1 MAE | C0 RMSE | C1 RMSE | C0偏差 | C1偏差 | Δ | R |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
''')
for name,res in (('2011留出',old),('2012',r)):
    a=res['complete_24h_dates']
    parts.append(f"|{name}|{a['dates']} / {a['hours']}|{fmt(a['C0']['MAE'])}|{fmt(a['C1']['MAE'])}|{fmt(a['C0']['RMSE'])}|{fmt(a['C1']['RMSE'])}|{fmt(a['C0']['mean_bias_prediction_minus_actual'])}|{fmt(a['C1']['mean_bias_prediction_minus_actual'])}|{fmt(a['MAE_absolute_difference_C0_minus_C1'])}|{pct(a['MAE_relative_reduction'])}|\n")
parts.append('''
每日期恰有24条，所以两模型的日期等权MAE、差及降幅分别与本表对应小时等权值相同（数值舍入误差除外）。2012完整日期的R=7.776923%，也未达门槛。该筛选改变日期组成，不能恢复未知小时，也不能视为消除了缺失机制。

## 配对块bootstrap及门槛

完全沿用原实现：日期排序；每次用random.Random(20261029)的randrange(D)等概率取起点，取连续L个日期，末尾循环；连续抽块至至少D日后截断至D日。抽中日期保留全部小时，两个模型共享日期样本，以合并绝对误差和除以合并小时数重算各自MAE，然后计算Δ及R。D在2011为92、2012为366；B=2000，L=7与28分别重置同一seed。95%百分位区间用排序后(B−1)p位置线性插值，p=0.025与0.975。

| 时期 | 块长 | Δ的95%区间 | R的95%区间 |
|---|---:|---|---|
''')
for name,res in (('2011留出',old),('2012',r)):
    for b in res['bootstrap']:
        parts.append(f"|{name}|{b['block_days']}日|[{fmt(b['absolute_difference_CI95'][0])}, {fmt(b['absolute_difference_CI95'][1])}]|[{pct(b['relative_reduction_CI95'][0])}, {pct(b['relative_reduction_CI95'][1])}]|\n")
parts.append('''
2011两种块长的R下限都高于10%，因此原留出期“C1改善且达到门槛”的有限判断保留。2012两种块长Δ和R的下限都大于0，在各自重采样近似下支持改善。2012的7日R区间上限为9.967439%，略低于10%；28日区间为5.709841%至11.589625%，跨过10%。所以“未来或同类时期改善是否达到10%”对块长敏感：没有稳健的超过10%证据，也不能综合两种区间宣称已稳健证明真实改善一定低于10%。这不改变所观察2012全年R=7.966722%、未达到预定门槛的事实。不能把9.967439%粗略四舍五入成10%，也不能因28日区间包含10%就说达到门槛。

这些区间量化固定模型误差比较随相关日期组成变化的不确定性，不包含训练参数估计、未知缺小时、部署成本或未来结构变化的不确定性。其外推仍需时间过程足够稳定、跨块依赖适度衰减；2012全年的季节性及趋势、年底与年初的循环拼接都是近似限制。28日块每次约13.1块，7日约52.3块，不能因数据较多就把日期当独立小时。跨年大幅低估提示可迁移性受限，不能把条件区间当成未来保证。

## 更新结论及后续研究

1. 保留：原2011留出中的MAE、24.231724%降幅及两种块长区间，均由同一模型重新核对，属于该期单系统已观测小时的有限结论。
2. 更新：2012中C1仍改善，但实测降幅7.966722%低于10%，完整日期和日期等权结果同样未达门槛。不能继续把2011门槛结论直接推广至下一年。
3. 部署：现有结果不足以部署；除了门槛未达，两模型均明显低估，且没有面向未来独立时期的稳定性和运营成本验证。该研究不推断个体行为，不提供工作日安排或其他干预的因果效果。
4. 下一项具体研究：把“可随时间更新水平的日历模型”作为新候选，预先固定只用过去56日、每28日更新一次同类均值及不足样本回退的规则，并与原冻结C0/C1作时间顺序比较。若使用2012开发这一方案，应明确2012已成为开发数据，另留之后尚未查看的时间段作最终门槛验证，并预先锁定MAE、两种块长、偏差监测和运营成本标准。这个候选尚未在本次拟合或测试，不能把它的设想成绩归给当前模型。

## 复现、结果及来源

`update_2012.py`加载原`analyze.py`和`results/model.json`，执行双年审计、训练参数核对、历史重播及2012冻结评分，未调用拟合函数。`results2012/results.json`保存完整精度；`metric_comparison.csv`对齐两个时期全部总体、分组及完整日期指标；`predictions.csv`、`daily_errors.csv`与两个`bootstrap_*d.csv`保留可追查的逐小时、逐日和逐次抽样结果。`verification.json`记录历史重播一致、72组参数精确核对、scikit-learn 1.9.1的MAE/RMSE独立核对及模型哈希不变。`provenance.json`保存输入、代码、模型、旧结果的SHA256及实际命令；`RUN.md`给出可指定输入与新输出目录的命令。

数据引用：Fanaee-T, H. (2013), *Bike Sharing*, UCI Machine Learning Repository，[DOI 10.24432/C5W894](https://doi.org/10.24432/C5W894)，[官方页](https://archive.ics.uci.edu/dataset/275/bike+sharing+dataset)，[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)。使用随附保持原观测字节的2011和2012年份切片。原README请求引用Fanaee-T与Gama，*Event labeling combining ensemble detectors and background knowledge*，[DOI 10.1007/s13748-013-0040-3](https://doi.org/10.1007/s13748-013-0040-3)。来源判断基于随附离线材料，未另行联网或核验介绍论文正文；构造草稿也不归于真实作者。
''')
report=''.join(parts)
assert len(report)<=12000
(w/'report.md').write_text(report,encoding='utf-8')
(w/'RUN.md').write_text('''# 可复跑命令

使用预置Python 3.12.14。主体评估沿用标准库；独立指标检查使用预置scikit-learn 1.9.1。所有Python调用带`-I -B`。输入与原结果不改动，输出目录必须尚不存在。

完整复跑双年审计、旧参数核对、2011留出重播、2012冻结评估：

```sh
EVAL_PYTHON -I -B WORKSPACE/update_2012.py --input-dir INPUT_DIR --output-dir WORKSPACE/reproduce_2012 --model WORKSPACE/results/model.json --prior-results WORKSPACE/results
```

`--input-dir`可替换为包含同样清单及`data/hour_2011.csv`、`day_2011.csv`、`hour_2012.csv`、`day_2012.csv`的路径；核对SHA和行数。`--output-dir`改成新的输出目录，不能用已存在的`results2012/`覆盖首次结果。`--prior-results`指向原2011首次结果，`--model`必须是本次核验的原冻结模型。2011训练数据只用于核对72组已存参数，不改变模型；2011最后三个月仍只评分。

单独对新小时文件评分且不重训：

```sh
EVAL_PYTHON -I -B WORKSPACE/analyze.py score --hour-csv /ABSOLUTE/NEW_HOUR.csv --model WORKSPACE/results/model.json --output-dir /ABSOLUTE/NEW_OUTPUT
```

至少需要dteday、hr、workingday、cnt，键不得重复；cnt只用于评分。新年度还应另核验日历覆盖和日表一致性。7/28日块、seed、B和指标定义不得根据评分结果更改。完整阶段1运行说明保存在`stage1_snapshot/RUN.md`，历史重播核验在`results2012/history_replay/`。

由首结果重建本文档及主报告、交接：

```sh
EVAL_PYTHON -I -B WORKSPACE/write_stage2_delivery.py
```

此文档生成命令会更新report.md、RUN.md、handoff.md，不重新评分。正式数值以首次JSON和CSV为准。
''',encoding='utf-8')
(w/'handoff.md').write_text('''# 冻结模型与新年度结论交接

先读本文件、report.md与RUN.md。前阶段原文档保存在`stage1_snapshot/`，原首次`results/`及模型均未覆盖；本阶段首次输出为`results2012/`。不依赖聊天即可恢复。

训练仍为2011-01-01至09-30，273日6442小时，目标cnt总和930102。C0为相同hr的训练算术均值，C1为相同(workingday,hr)的均值，未见组合回退C0；不取整。只用这两个日历变量，不使用日期数值、yr、天气、instant或casual/registered。24+48组都有训练记录，两期回退0。原参数`results/model.json` SHA256=`dba591a44fff2d14514b4b38d00c8985e93f41cf2b1ab684a6abd2f2620d078d`，读取前后不变；72组sum/n/mean由2011前九个月独立精确核对，未用2012恢复参数。

输入四份CSV均通过随附清单SHA256及行数核对。2011小时SHA=`294d25e98ef1c9c9cec746e17ba3ff9818627ba5aa14baf1b93db7ae218de115`；2012小时SHA=`d73ae7f2aba616d775b5bccb3540910a9de49fe88e7f5926f7bf0a3fe840602d`。完整输入摘要见`results2012/provenance.json`及两份quality目录audit.json。2012有8734小时、366日，350完整日，16不完整日，少50日历小时；重复键/空单元格/计数恒等式失败/小时日汇总差异均为0。没有补零，没有将缺行归于具体事件。

年度总数2011=1243103，2012=2049576，增长64.875799%；每日均值3405.761644与5599.934426，增长64.425318%。两种增长不同是因2012有366日而2011有365日。来源元数据与原README关于全量小时数、season和温度逆变换的冲突已保留，不修改观测。

主指标为观察小时等权MAE；Δ=MAE0−MAE1，R=1−MAE1/MAE0，实务门槛R≥10%。偏差定义预测减真实。另报日期等权日内MAE及差/降幅、工作日分组、完整日期敏感性。日期等权不是日总数预测误差。

历史2011留出92日2203小时：C0 MAE=58.825190494512434，C1=44.570832407531775，Δ=14.254358086980659，R=0.24231724482575867。7日R区间[0.17071940679252828,0.3148328823524696]；28日[0.15571346410314052,0.325449081470458]。本次加载同一模型重播，结果JSON相同，四份CSV逐字节相同；原历史有限结论仍保留。

2012全部8734小时：C0 MAE=118.11827620046033，C1=108.70812150008842，Δ=9.410154700371905，R=0.07966722003631166；偏差分别−91.53369361340616和−91.61346537392994。日期等权MAE分别117.77586740335869与108.3607464606273，差9.415120942731392，R=0.07994100277339922；完整日期R=0.07776923135594593。工作日0/1的R为0.17408897566264925/0.030071519252312773。

Bootstrap完全沿用原代码：按日期排序，配对循环移动块，randrange(D)取起点，抽至至少D后截D，保留整日日内小时，合并误差和/小时数；B=2000，每种L重新random.Random(20261029)，95%百分位在(B−1)p线性插值，p=.025/.975。2012 D=366，L=7/28的Δ区间分别[8.083961388811428,10.825502808133045]、[7.667939814729385,11.466770540309213]；R区间分别[0.06476413180843968,0.09967438859012917]、[0.05709841034889167,0.11589625362630877]。均支持改善；7日区间上限略低于10%，28日跨10%，不要挑一个块长。观察期点估计未达门槛，但关于同类时间过程是否低于10%的推断对块长敏感，不能作稳健低于10%或达到10%的保证。

不能部署为已经达标模型；C1结构改善没有解决需求水平低估。两个评估期为2011第四季度及2012全年，不能将差异全归因于纯年份效应。区间固定训练参数，依赖时间稳定性，不含缺小时误差或训练不确定性；单系统观察比较没有个体或因果结论。

`update_2012.py`是本次恢复/审计/评估代码，调用原`analyze.py`的预测及评估函数；它不调用拟合入口。新输入和新输出路径见RUN.md。`results2012/results.json`和`metric_comparison.csv`为完整结果；`predictions.csv`、`daily_errors.csv`、`bootstrap_*d.csv`为底层证据；`model_recovery.json`、`verification.json`、`provenance.json`分别记录模型、核对及运行。`execution.json`记录本次执行，前阶段执行另存`stage1_snapshot/execution.json`。

下一项研究可开发仅用过去56日、每28日更新同类均值的水平更新日历模型，先规定回退及评估规则；若用2012开发，须另留未查看的后续时期作最终时间外验证。它是未在本次训练或测试的新候选，不能替换当前结论或声称已有改善成绩。
''',encoding='utf-8')
print(json.dumps({'report_characters':len(report),'verification':v['status'],'report':str(w/'report.md')},ensure_ascii=False))
