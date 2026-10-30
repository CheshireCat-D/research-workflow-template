# 当前项目恢复入口

权威状态为management/state.json。当前参数为notes/parameters.json，授权原件保存在management/evidence/C/authorization/。当前范围是2011-11-01至2011-12-31，1460观察小时、61日，使用原2011年1月至9月冻结模型与observed-hour权重。结果、表格和摘要分别为results/result.json、results/table.csv、results/summary.md。

迁移后在项目根目录运行（仅Python标准库；将/path/to/python换成可用解释器）：

```sh
/path/to/python -I -B management/status.py --root .
/path/to/python -I -B management/verify_current.py --root .
```

status退出0表示已登记本地文件与版本快照一致，3表示变更/缺失，必须按依赖复核。verify_current退出0表示当前输入与计算器结果散列、各项指标、表格和活动绑定经独立数值检查相符；均不等于科学证明或作者内容认可。脚本不写项目。state.json不能通过自包含散列证明自身未改；以保留的作者授权与版本历史核对，旧handoff不能覆盖较新有效参数。

management/checkpoints/C-pre-recompute/保存参数已变而结果仍为Q4的真实漂移态。新保存断点没有重算：management/evidence/C/intermediate-status.stdout.json原始检查exit=3，D-CALC和D-SYNTH受影响，D-SOURCE-CHECK独立且输入不变。中间检查原结果从未被最终成功结果替换。management/versions/A-initial/保留初始参数、Q4结果、表格及摘要完整字节；C-final保存当前版本。需要修订时保留修订前内容与实际理由，重新复核受影响活动，不要自动覆盖后来修改。

本次按原scripts/compute.py真实重算，命令和独立指标复核见management/evidence/C/。可用新的不存在目录重算：

```sh
/path/to/python -I -B scripts/compute.py --root . --output /new/nonexistent/verification-directory
```

保留失败日志，不覆盖旧运行输出。原始data/hour_2011.csv、scripts/compute.py、model/frozen.json保持字节不变。原Q4 MAE降幅24.23172448%，当前为27.16861853%；窗口改变，不能解释为重训或模型改善。

下一步：将2011年11月至12月的冻结模型指标与更新摘要交作者内容复核；保留原Q4结果作历史记录。尚无人类专家认可、无投稿授权；截止日期2026-12-15，期刊未定。不重训、不作因果或2012/任意未来保证。

来源边界：本地2011切片8645行及完整散列可核验；原完整hour.csv/ZIP、DOI文章与当前网页未读取。完整CSV17379行和metadata17389的差异是来源卡原记录，不擅改。notes/unregistered-scratch.md未登记科学依赖，status不检测它；不能宣称自动覆盖所有文件。原始CSV/PDF仅为私有研究缓存，不对外分发；保留身份和项目结果，本次无网络或发布。
