# 可移位的离线研究项目

从项目根运行 `python3 artifacts/run.py` 重建 `artifacts/results.json`；运行 `python3 artifacts/minimum_check.py` 重建最小反例；`python3 artifacts/verify_relocation.py` 检查移位重跑。仅Python标准库；输入位于inputs/；代码没有固定外部文件路径。

主要文本为notes/issue.md、notes/mechanism.md、notes/candidates.md、notes/results.md、manuscript/report.md、review.md。正式配置artifacts/config.json；原始运行日志位于项目旁logs/，属于执行溯源，不是科学代码的依赖。

持久化使用项目副本 `.agents/skills/_rw-runtime/tools/research.py`。只读结构检查和恢复输出在checks/；它们不判断科学真伪。具体下一步保存在项目checkpoint中，并见review.md。
