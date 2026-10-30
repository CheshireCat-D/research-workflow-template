# 复核命令

共同解释器：`EVAL_PYTHON`。仅使用标准库与环境已有的 PDF 库读取原文，不安装依赖、不联网。

可自行替换 `--input` 与尚不存在的 `--output` 目录：

```sh
EVAL_PYTHON -I -B WORKSPACE/checks.py --input INPUT_DIR --output WORKSPACE/recheck-new
```

程序复算四步全部 16 条路径、精确事件概率、边界数值与调参方程，并记录输入散列；不生成理论证明或重新审稿。主稿为 `report.md`，按任务名称另存完全相同的 `audit.md`。输入原稿与来源未修改，输出目录不含来源全文。`audit/` 保存分项推导和逐条验证记录。
