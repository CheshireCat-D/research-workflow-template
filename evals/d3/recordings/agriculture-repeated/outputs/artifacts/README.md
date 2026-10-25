# 复算

在PROJECT目录运行：

```text
python3 artifacts/run.py
```

Python标准库，确定性16种分配完全枚举，种子不适用；从inputs/的复制数据重建results.json与四个CSV。单次运行约0.03秒含解释器启动。两次原始实际执行的命令、stdout/stderr、退出码、耗时及原日志SHA-256保存在项目内`artifacts/execution.json`，已登记为运行凭据；原始日志仍在交付工作目录旁保留。原日志未记录精确Python版本与开始UTC，凭据明确标为未记录，本次修订环境另列且不冒充原运行环境。两个运行数值与CSV哈希相同见checks/rerun.json。

plot_season.csv有16个小区季节第90天均值；plot_primary.csv有8个小区两季平均；block_contrasts.csv有4行主要/各季/季差；visit_contrasts.csv为描述性轨迹。results.json内保存16项每个精确零分布、SE与近似区间和错误草稿诊断。冻结后在副本中复算，避免改动已登记文件指纹。
