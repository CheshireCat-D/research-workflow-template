# 可复跑命令

实际运行时为Python 3.12.14，分析入口只用标准库。必须传新的、尚不存在的输出目录，避免覆盖首次结果。原输入不可修改。

完整复跑2011审查（唯一拟合入口）：

```sh
EVAL_PYTHON -I -B WORKSPACE/analyze.py fit --input-dir INPUT_DIR --output-dir WORKSPACE/new_fit
```

`--input-dir`可替换为含相同`data/hour_2011.csv`、`data/day_2011.csv`结构的输入路径，`--output-dir`可指定新的输出目录。fit拒绝含2011以外观测的数据。模型预测均值未取整，sum/n与mean一并保存。

无重训评分入口（下一阶段提供新小时观测后才运行，当前未读取或获取2012）：

```sh
EVAL_PYTHON -I -B WORKSPACE/analyze.py score --hour-csv /ABSOLUTE/PATH/TO/NEW_HOUR.csv --model WORKSPACE/results/model.json --output-dir WORKSPACE/new_score
```

`--hour-csv`至少含dteday、hr、workingday、cnt，dteday为ISO日期，hr为0..23，workingday为0或1，键不得重复。workingday按已知日历的周末/节日规则提供；预测不使用cnt，cnt只用于实际误差评分。输入中其余列全部忽略。score只加载模型，不调用拟合；缺少C1组合时回退C0。当前24个小时均有C0均值。为生成同样的完整日期及工作日分组敏感性，评分期应包含24小时完整日期及两个workingday类别；分析2012全年满足这些结构前应先核验新输入。不同目标期应各放一个输入文件，避免将2011与未来期混合评分。

已执行的冻结重播：

```sh
EVAL_PYTHON -I -B WORKSPACE/analyze.py score --hour-csv WORKSPACE/results/predictions.csv --model WORKSPACE/results/model.json --output-dir WORKSPACE/replay_check
```

predictions.csv中的旧预测列被忽略，仅取实际目标与日历列重新预测。该目录已存在，重复运行时必须改变输出路径。

独立数值核验（使用共同预置scikit-learn 1.9.1的MAE和RMSE指标，训练与评分不依赖该包）：

```sh
EVAL_PYTHON -I -B WORKSPACE/verify.py WORKSPACE INPUT_DIR
```

该命令只核验已存首结果和重播，并更新verification.json，不改模型或结果。指标单位和解释见report.md；所有计算完整精度在JSON与CSV中，报告只为显示取小数位。
