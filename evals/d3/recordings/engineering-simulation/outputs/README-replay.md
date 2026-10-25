# 重放

在本PROJECT目录运行（Python3.11+、仅标准库）：

```sh
python3 inputs/simulator.py
python3 artifacts/run.py
python3 .agents/skills/_rw-runtime/tools/research.py check --root .
python3 .agents/skills/_rw-runtime/tools/research.py resume --root .
```

前两条重建标称基线与20次补充仿真。artifacts/run.py读取inputs/，调用artifacts/simulator.py与原始inputs/simulator.py，不需要原案例或源工具包路径。results包含配置、每场景/步长指标、解析与细化对比、需求状态及异常。artifacts/traces保留0.1秒完整轨迹；其余步长可由同一脚本重建，指标已留存。

固定四场景而非随机抽样；无种子。单次正式运行实测约0.2秒；环境/版本与输入SHA-256在结果内。logs/formal-run.json、logs/replay-run.json记录实际命令、stdout、stderr、退出码和耗时。首次结果保存在artifacts/results.first-run.json。命令退出0不代表所有工程需求通过。

登记/指纹在重新运行后可能因results中的耗时变化而报告过期；需要复核实际变化并用CLI显式更新相关记录/活动，而不能只刷新检查点掩盖变化。冻结交付中的checks/check.json与checks/resume.json是当时实际CLI输出。
