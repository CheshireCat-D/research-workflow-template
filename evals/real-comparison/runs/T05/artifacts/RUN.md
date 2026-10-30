# 复跑

使用共同解释器；`--input` 指向含 TASK.md、draft.tex、source-manifest.json 和 sources/ 的本题输入，`--output` 可指向新的输出目录。脚本只生成数值复核和输入哈希，不复制论文全文，不修改输入。

```sh
EVAL_PYTHON -I -B WORKSPACE/checks.py --input INPUT_DIR --output WORKSPACE/recheck
```

正文的反例、积分、LIL 反证和条件期望不等式是解析论证；数值脚本不是这些结论的证明器。`report.md` 是主报告，`audit.md` 为相同内容的任务约定名称。
