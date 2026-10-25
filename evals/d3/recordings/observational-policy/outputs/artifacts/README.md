# 重跑

在完整项目的任意副本根运行：

```sh
python3 artifacts/run.py
python3 .agents/skills/_rw-runtime/tools/research.py check --root .
python3 .agents/skills/_rw-runtime/tools/research.py resume --root . --format markdown
```

仅Python 3.11+标准库，无网络和依赖安装。输入与输出均以run.py确定的项目根为基准；参数和输入SHA-256在results中。运行时间与环境字段可随重跑变化，medical、policy及arithmetic_anchors应相同。重写已登记结果会使指纹失效；要在隔离副本中复核，或先比较后按CLI显式更新记录。单次科学运行预算10秒，无随机种子。

结果不构成因果识别、真实建议、真实政策评价或原创性证据。项目旁logs保存真实命令、stdout、stderr、退出码和耗时；复制检查报告同样保留在项目旁。
