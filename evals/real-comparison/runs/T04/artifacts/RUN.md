# 复核命令

解释器：`EVAL_PYTHON`。脚本仅使用 Python 标准库；无需安装、网络或随机种子。

```sh
EVAL_PYTHON -I -B WORKSPACE/checks.py --input-dir INPUT_DIR --output-dir WORKSPACE/results
```

可把 `--input-dir` 改为含有 `draft.tex` 的输入目录，把 `--output-dir` 改为新的输出目录。输入参数用于确认审查对象存在；计算核验报告中明确给定的有限分布及标量公式，不会自动审查任意新稿。

解析证明在 `report.md`（亦保存为任务要求的 `audit.md`）。`audit/` 保存逐项依赖、原构造稿片段与验证步骤。代码不替代证明，不复制来源论文全文。
