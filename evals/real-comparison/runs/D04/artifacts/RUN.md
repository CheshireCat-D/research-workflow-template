# 冻结模型与2012更新复跑

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
