# 复跑自查

使用指定解释器，输入目录指向包含 `TASK.md`、`draft.tex` 和 `sources/` 的本题输入。输出指定新目录，避免覆盖首结果：

```sh
EVAL_PYTHON -I -B WORKSPACE/checks.py --input INPUT_DIR --output WORKSPACE/recheck
```

仅写入指定输出目录的 `checks.json`；不修改输入，不联网，不复制来源全文。代码使用 Python 标准库，精确有理数比较和数值积分不能替代报告中的证明。
