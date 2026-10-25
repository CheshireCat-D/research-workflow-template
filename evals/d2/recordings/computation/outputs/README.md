# 隔离计算项目

正文：`manuscript/report.md`。问题与预定计划：`notes/issue.md`。逐目标原始结果：`artifacts/results.json`、`artifacts/summary.csv`。内容自审：`review.md`。

本项目仅用Python标准库。算法源码保存在 `inputs/methods.py`，与给定附件逐字节相同。整个项目迁移后，在项目目录运行以下命令，将复跑结果写到新位置，不修改已登记文件：

```sh
python3 -B artifacts/run.py --output-dir ../fresh-run
python3 -B .agents/skills/_rw-runtime/tools/research.py check --root .
python3 -B .agents/skills/_rw-runtime/tools/research.py resume --root . --format markdown
```

复跑的结果目录不能已含同名结果。若要同时限制完整进程墙钟为10秒，可使用项目旁的 `log-command.py --timeout 10` 包装器；脚本内部另设CPU软/硬限制8/9秒。计时只用于运行约束。

项目旁 `logs/` 保存命令、退出状态和未经改写的stdout/stderr，`check.json`、`resume.json`、`resume.md` 保存最终恢复输出；路径均以外层输出根为基准。正式文件登记后保持不变。迁移复跑和其原始输出位于项目旁 `relocation-check/`，项目内已有核对结果 `artifacts/reproducibility.json`。

下一步为推导一般振荡目标的离散和与混叠条件，再预设独立的扩展预算；本轮不主张算法普遍优越或速度优势。
