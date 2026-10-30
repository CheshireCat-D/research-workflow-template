# 独立数值与代码复跑核验

六份交付脚本均已按各自 RUN.md 在全新副本实际执行，全部 exit 0。未修改交付代码、模型、阈值、seed、B 或 bootstrap；未访问分组映射、个人记忆/skills、运行中的 workspace，未联网安装。只核查代码执行与数值，不评价文字质量或推断实验组别。

封存产物及原输入前后 SHA-256 全部不变；六个副本中的代码、模型和原结果前后也不变。输入副本逐行与公开原始 hour.csv/day.csv 对应年度切片完全相同。指定参考程序另行运行成功，其模型语义及答案 JSON 与给定独立参考完全相同。

|产物|任务|exit|参数均值最大误差|逐小时预测均值最大误差|摘要指标最大误差|4000次bootstrap最大误差|新科学输出与封存|
|---|---|---:|---:|---:|---:|---:|---|
|D01|data-a|0|0|0|1.42e-14|2.13e-14|全部逐字节相同|
|D02|data-a|0|0|0|1.42e-14|2.13e-14|全部逐字节相同|
|D03|data-a|0|0|0|1.42e-14|2.13e-14|全部逐字节相同|
|D04|data-b|0|0|0|2.84e-14|2.84e-14|全部逐字节相同|
|D05|data-b|0|0|0|2.84e-14|2.84e-14|全部逐字节相同|
|D06|data-b|0|0|0|2.84e-14|2.84e-14|全部逐字节相同|

每份摘要对照72个数值：总体、完整24小时日期、workingday=0/1四个范围各14项，以及两种块长各8项（B、seed、块长、日期数、两类95%区间四端点）。14项包括日期/小时数、C0/C1的MAE、RMSE、prediction-minus-actual偏差及按日等权MAE、两种加权下的绝对和相对改善。所有数值通过预先固定的绝对容差1e-10。

逐小时核验还检查日期、小时、workingday、实际cnt、fallback和所有交付误差列；每日误差表检查全部已交付数值。均值、计数、每日误差和参数sum/n完全一致。D02–D05部分逐小时平方误差列有浮点运算顺序造成的末位差，2011最大2.27e-13、2012最大1.46e-11；这是辅助平方误差列的差，预测值没有差异。主指标和bootstrap最大差为2.84e-14。

bootstrap由独立审计器重新生成每个抽样日期索引，并真正展开所抽日期的小时误差后重算；每个块长2000次，seed=20261029，循环日期块，截断为原日期数，保留所抽日期的全部实际小时。比较每次重复的样本小时数、两模型MAE、绝对改善、相对改善和重复序号；D01/D06另比较样本日期数。未用运行成功替代数值核验。

## 字段语义映射

|参考字段|D01/D06|D02/D04|D03/D05|
|---|---|---|---|
|overall|overall|all|all_observed|
|full24_dates_sensitivity|complete_24h_dates|complete_24h_dates|complete_24h_dates|
|subgroups.workingday=w|by_workingday.w|workingday.w|workingday.w|
|hours / days|n_hours / n_dates|n_hours / n_dates|hours / dates|
|Cx_MAE / Cx_RMSE|Cx.MAE / Cx.RMSE|Cx.hour_weighted_MAE / Cx.hour_weighted_RMSE|Cx.MAE / Cx.RMSE|
|Cx_bias_prediction_minus_actual|Cx.bias_prediction_minus_actual|Cx.mean_bias_pred_minus_true|Cx.mean_bias_prediction_minus_actual|
|Cx_day_equal_weight_MAE|Cx.day_equal_MAE|Cx.date_equal_mean_intraday_MAE|Cx.day_equal_mean_intraday_MAE|
|MAE_reduction_absolute|hour_weighted_absolute_improvement|MAE_difference_C0_minus_C1|MAE_absolute_difference_C0_minus_C1|
|MAE_reduction_fraction|hour_weighted_relative_improvement|relative_MAE_reduction|MAE_relative_reduction|
|day_equal_weight_mean_MAE_difference|day_equal_absolute_improvement|date_equal_MAE_difference|day_equal_absolute_difference_C0_minus_C1|
|day_equal_weight_MAE_reduction_fraction|day_equal_relative_improvement|date_equal_relative_MAE_reduction|day_equal_relative_reduction|
|bootstrapN.absolute_difference_percentile95|bootstrap.N.absolute_improvement_95ci|bootstrap.N.difference_CI95|bootstrap列表中block_days=N的absolute_difference_CI95|
|bootstrapN.relative_reduction_percentile95|bootstrap.N.relative_improvement_95ci|bootstrap.N.relative_reduction_CI95|bootstrap列表中block_days=N的relative_reduction_CI95|

模型均值按语义比较：C0共24个hr单元，C1共48个workingday/hr单元。键中的逗号和冒号仅作为分隔形式归一化；比较每个mean、sum或sum_cnt、n，不比较无关JSON格式。共72个均值全部精确相同。参考还包含weather分组，六份交付摘要仅报告workingday分组；没有把参考中额外的weather数值算作交付已报告结果。

## 双年比较与冻结核验

|指标|2011全年|2012全年|
|---|---:|---:|
|实际小时数|8645|8734|
|日期数|365|366|
|完整24小时日期|305|350|
|缺失日历小时|115|50|
|cnt总量|1243103|2049576|
|日均cnt|3405.7616438356163|5599.934426229508|

D04–D06全部年度数值与参考一致：年度总量增长0.6487579870694544，日均增长0.6442531838260952。三份比较CSV逐行、逐数值比较通过，包含两个评价期的四个范围、全部模型及按日等权指标。2012-10-29只有1个实际小时，10-30有11个，原输入未补齐；完整24小时敏感性只含350日/8400小时。

- D04 → 前阶段 D02：原模型和原评分代码均逐字节保留；模型SHA `f8a758c6c73cf7e0cfcfa0936b594afb8f23b1260610ecae15929f601dc8e5d4`。更新入口无fit/train调用，读取2011训练记录仅核对sum/n/mean，2012标签只进入审计和误差评价。
- D05 → 前阶段 D03：原模型和原评分代码均逐字节保留；模型SHA `dba591a44fff2d14514b4b38d00c8985e93f41cf2b1ab684a6abd2f2620d078d`。更新入口无fit/train调用，读取2011训练记录仅核对sum/n/mean，2012标签只进入审计和误差评价。
- D06 → 前阶段 D01：原模型和原评分代码均逐字节保留；模型SHA `84c6c80033718b1c0b7c0333d90ebe66c0978fd305b44d65ffd5ca9fd6f19a47`。更新入口无fit/train调用，读取2011训练记录仅核对sum/n/mean，2012标签只进入审计和误差评价。

D04/D05的新输出还完整重播2011留出集，所有摘要、逐小时预测、每日误差及4000次bootstrap通过，且与封存历史科学结果逐字节一致。D06实际更新入口重播并断言2011总体指标，另外本审计核对其封存阶段A的全部72个摘要值和保留模型/代码；不把它描述为更新入口重播了整个2011bootstrap。

## 实际执行命令与哈希

以下参数只把RUN.md中的入口、模型、旧结果和输入路径映射到新副本，并使用新的output目录。没有发明未声明接口。每条实际argv、解释器版本、入口和全部Python文件SHA、每个输出文件SHA、stdout/stderr SHA、前后源文件清单均保存在主JSON对应execution字段及各副本execution-record.json。

### D01

入口SHA-256：`e22ae01683059c937d53ac0f1342cf8d7ae0b1b0fb8905a680eb35144d3735e6`；exit=0。

```sh
STUDY_ROOT/env/bin/python -I -B STUDY_ROOT/numeric-replays/D01/workspace-copy/analysis.py --input-dir STUDY_ROOT/numeric-replays/D01/input-copy --output-dir STUDY_ROOT/numeric-replays/D01/output
```

### D02

入口SHA-256：`9aa68881931fdb685b4c27ea5c5f976b9576e49fac937140b18cc396bad6f32b`；exit=0。

```sh
STUDY_ROOT/env/bin/python -I -B STUDY_ROOT/numeric-replays/D02/workspace-copy/analyze.py train --input-dir STUDY_ROOT/numeric-replays/D02/input-copy --output-dir STUDY_ROOT/numeric-replays/D02/output
```

### D03

入口SHA-256：`ddcfbed9e5fbb64fd336e2df20f04d1550dad77a2ae30bba2634a415d3b16d49`；exit=0。

```sh
STUDY_ROOT/env/bin/python -I -B STUDY_ROOT/numeric-replays/D03/workspace-copy/analyze.py fit --input-dir STUDY_ROOT/numeric-replays/D03/input-copy --output-dir STUDY_ROOT/numeric-replays/D03/output
```

### D04

入口SHA-256：`d83980da17c54f116aa26da88b34ea5e1a1a1b4aae87c17e6427e00542d6a95f`；exit=0。

```sh
STUDY_ROOT/env/bin/python -I -B STUDY_ROOT/numeric-replays/D04/workspace-copy/update2012.py --input-dir STUDY_ROOT/numeric-replays/D04/input-copy --prior-input STUDY_ROOT/numeric-replays/D04/prior-input-copy --model STUDY_ROOT/numeric-replays/D04/workspace-copy/results/model.json --prior-results STUDY_ROOT/numeric-replays/D04/workspace-copy/results/results.json --original-code STUDY_ROOT/numeric-replays/D04/workspace-copy/analyze.py --output-dir STUDY_ROOT/numeric-replays/D04/output
```

### D05

入口SHA-256：`273a6fbf25461a560db3502f91e483d06da20b77cfb5d2f829733e9654d0ba4b`；exit=0。

```sh
STUDY_ROOT/env/bin/python -I -B STUDY_ROOT/numeric-replays/D05/workspace-copy/update_2012.py --input-dir STUDY_ROOT/numeric-replays/D05/input-copy --output-dir STUDY_ROOT/numeric-replays/D05/output --model STUDY_ROOT/numeric-replays/D05/workspace-copy/results/model.json --prior-results STUDY_ROOT/numeric-replays/D05/workspace-copy/results
```

### D06

入口SHA-256：`09d153bcc9f812204adc590adfed0a321ccb4ca9245b81e8aeacce48299addf0`；exit=0。

```sh
STUDY_ROOT/env/bin/python -I -B STUDY_ROOT/numeric-replays/D06/workspace-copy/stage_b.py --input-dir STUDY_ROOT/numeric-replays/D06/input-copy --prior-dir STUDY_ROOT/numeric-replays/D06/workspace-copy/stage_a_snapshot --model STUDY_ROOT/numeric-replays/D06/workspace-copy/model.json --output-dir STUDY_ROOT/numeric-replays/D06/output
```

## 检查范围及失败记录

作者六份实际复跑没有失败或unavailable。未做内容评分、文献审核、统计稳定性推断或组别比较。作者RUN.md中的独立验证器没有另行运行；结论来自实际分析入口复跑和本审计对原始公开数据、给定参考、封存数值以及新输出的独立检查。

审计器自身第一次字段映射遇到sum_abs_error_C0未映射而停止，只修正了本审计器的别名；另一个冗余审计进程因重复最大值计算而中止，优化的仍仅为本审计器。六份交付脚本均只实际运行一次，原封存及输出完全未动。参考程序三个实际执行均写不同新目录并得到相同答案。最终审计无未映射数值或未解决失败。

主结构化报告：`numeric-replay-audit.json`；每个新副本：`numeric-replays/Dxx/`；逐项实际值、参考值、误差和通过标识：各副本`numeric-value-checks.json`与`additional-value-checks.json`。独立小时展开bootstrap CSV与参考重跑也在numeric-replays/。
