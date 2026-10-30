# 复跑与冻结评分

所有分析只需Python标准库。指定解释器：`EVAL_PYTHON`；使用`-I -B`保持隔离、不生成pyc。不安装包。

原分析可指定输入目录与新的输出目录，避免覆盖交接时保存的结果：

```sh
EVAL_PYTHON -I -B \
  WORKSPACE/analysis.py \
  --input-dir PRIOR_INPUT_DIR \
  --output-dir /absolute/path/to/new-output
```

默认train-score只读2011输入，训练date<2011-10-01，评价2011-10-01至12-31，输出模型、指标、bootstrap明细、预测、数据检查及主报告。再次执行是同样的固定程序，不调参。路径应指向有写权限的新普通目录。

下一阶段只对随后合法提供的新观测打分，替换下面的新输入路径和文件名。此命令不重新训练、不覆盖原模型：

```sh
EVAL_PYTHON -I -B \
  WORKSPACE/analysis.py \
  --mode score \
  --input-dir /absolute/path/to/new-input \
  --hour-file future_hour.csv \
  --model WORKSPACE/model.json \
  --output-dir /absolute/path/to/new-scoring-output
```

该输入小时文件位置是`new-input/data/future_hour.csv`，至少包含dteday（ISO日期）、hr（0–23）、workingday（0/1）、cnt（非负整数）；原始完整CSV列也兼容。若只有未来日历尚无目标值，可直接按model.json查均值预报，待真实cnt提供再评价。脚本score路径输出预测、指标、日期误差、两种bootstrap、模型/输入SHA及`trained:false`的score_provenance.json；新数据的身份和完整性另审，不复用2011检查。

独立数值核验本交接目录保存的原结果：

```sh
EVAL_PYTHON -I -B \
  WORKSPACE/verify.py \
  PRIOR_INPUT_DIR
```

核验模型均值、全留出预测、主指标、4000次按小时展开的bootstrap及分位数。`verification.json`成功标识为`"status": "passed"`。`verify.py`默认核验其自身所在目录中的原结果，不是任意新输出目录。

主报告在`report.md`，下一阶段务必先读`handoff.md`并确认model.json SHA-256为`84c6c80033718b1c0b7c0333d90ebe66c0978fd305b44d65ffd5ca9fd6f19a47`。
