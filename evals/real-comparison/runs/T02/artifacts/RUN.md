# 复跑

所有数学证明在 report.md；checks.py 只校验具体数值和输入身份。
在共同解释器下指定输入目录与一个新的结果目录：

```sh
EVAL_PYTHON -I -B \
  WORKSPACE/checks.py \
  --input-dir INPUT_DIR \
  --output-dir WORKSPACE/rerun-new
```

输出 results.json。无需联网或安装。原始 PDF 和提取全文继续留在 input/sources，输出目录不复制全文。
