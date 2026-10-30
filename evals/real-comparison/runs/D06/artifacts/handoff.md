# 跨年更新交接

首先读report.md。原2011证据保存在stage_a_snapshot/；stage_b_results/是2012实际执行结果。root results.json等旧结果仍为2011文件，请勿误当新年份。原model.json是两阶段共同冻结模型，SHA-256 `84c6c80033718b1c0b7c0333d90ebe66c0978fd305b44d65ffd5ca9fd6f19a47`，前后未变。

## 模型与恢复核验

训练2011-01-01至09-30，共6442小时、273天，未加入2011Q4，也未用2012重训。C0同小时均值，C1同(workingday,hr)均值，72个sum/n/mean单元全部核验一致。预测不取整；C1未见组合回退C0，未知小时报错；2012回退0次。种子20261029，B=2000，7及28天循环日期配对块，分别重置seed；按总小时误差求MAE，分位数使用(B−1)p线性插值。stage_b.py直接载入stage_a_snapshot/analysis.py的原评价函数，不调用fit。

## 更新后的结论

2011Q4 MAE0/1=58.825190/44.570832，改善24.2317%，原结论保留。2012 MAE0/1=118.118276/108.708122，改善7.9667%，未达到10%点估计门槛；日等权改善7.9941%。两块长区间均支持正改善；7天相对区间[6.4764%,9.9674%]，28天[5.7098%,11.5896%]，对是否能排除10%有敏感性，必须同时呈现。偏差−91.533694/−91.613465，不足以部署。完整日改善7.7769%，非工作日17.4089%，工作日3.0072%。

2011/2012年度计数1243103/2049576，日均3405.761644/5599.934426，总数增长64.8758%，日均增长64.4253%；365/366天造成二者差异。2012有8734小时、366日，350日完整、14日23小时、1日11小时、1日1小时，共少50小时键。没有空单元格、重复键、恒等式或小时/日计数差异；少行原因未确定，绝不补零。

## 复现与文件

- stage_b.py：可指定input-dir、prior-dir、model、output-dir的冻结评价和双年度审查。
- verify_b.py：独立展开4000次bootstrap验证，stage_b_results/verification.json标记passed。
- publish_b.py：从已执行结果渲染report.md、handoff.md；不计算新模型。
- stage_b_results/results.json、comparison_metrics.csv：全精度总体、日期等权、完整日和workingday结果及区间。
- data_audit.json、annual_growth.json、date_coverage_2011.csv、date_coverage_2012.csv：审查和年度汇总。
- predictions.csv、daily_errors.csv、bootstrap_L7.csv、bootstrap_L28.csv：全部预测和重采样结果。
- score_provenance.json：trained:false、模型前后hash、72单元核验及输入SHA。
- stage_b_run.log、stage_b_verify.log：实际执行日志。execution.json是本阶段记录；旧执行记录在stage_a_snapshot/execution.json。

后续的新模型可以研究近期水平/季节更新，但应另编号，开发中用过2012后，新的效果主张需未观察过的后续数据。不可把该候选替换成此次测试过的冻结C1。原数据来自Fanaee-T (2013), Bike Sharing, UCI, DOI 10.24432/C5W894，CC BY 4.0；切片保留原始行，随附来源冲突没有靠猜测改值。
