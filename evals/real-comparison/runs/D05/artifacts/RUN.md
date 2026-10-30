# 可复跑命令

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
