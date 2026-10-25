# 复现

仅需 Python 3.11+ 标准库。可在任意工作目录执行 python3 /path/to/PROJECT/artifacts/run.py；路径以脚本所在项目为根，重建 artifacts/results.json。冻结交付后重跑请先复制项目，以保留本次登记指纹。

从项目根执行原型对照：python3 artifacts/run.py --implementation inputs/gate.py --results artifacts/prototype-results.json。原型应退出1；修复应退出0。所有正式运行均为确定性，无种子、网络、休眠或第三方依赖。全进程命令/退出/耗时见artifacts/logs，项目登记结构检查见checks；工具包runtime已随项目复制。
