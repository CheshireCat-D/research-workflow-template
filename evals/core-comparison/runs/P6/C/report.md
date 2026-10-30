# 续作结果

已按作者授权，把评价窗口从2011年Q4改为2011-11-01至2011-12-31，实际运行原脚本并修订结果、表格、摘要、参数绑定、主张范围、关系、选择及两个受影响活动。冻结模型和原始数据没有变化。

| 指标 | C0 | C1 |
|---|---:|---:|
| MAE | 56.641274309909 | 41.252622564019 |
| RMSE | 81.700383606317 | 64.158265648678 |
| 预测减实际的平均偏差 | 13.433264561295 | 13.347664992606 |

共1460个观察小时、61日；C1相对C0的MAE降低27.16861853%。原Q4为2203观察小时、92日，降低24.23172448%。两者评价窗口不同，降幅差别不能解释为重训或模型改善。

先保存的漂移状态位于项目`snapshots/stage-C-before-recompute/`，包含当时实际参数、旧Q4成果、权威state及完整SHA清单。随后以原完成绑定保存state版本2的新断点。原始中间检查见本交付目录`intermediate-check.stdout.json`和`intermediate-check.exit.json`：退出1；断点current，参数改变，D-CALC和D-SYNTH仍stale，D-SOURCE-CHECK仍done。保存断点没有重新核验旧工作。

之后真实执行`scripts/compute.py`，退出0；原始新运行文件保留在项目`results-evaluations/C-approved/`。逐项按冻结预测复算计数、MAE、RMSE、偏差和降低比例，结果精确相同；`results/result.json`和`results/table.csv`与新运行文件逐字节相同；已核对更新摘要中的日期、计数、指标、Q4历史比较及解释范围。详细证据在`records/validation-C.json`与本目录`validation-C.json`。

最终权威表示为项目`records/state.json`，state_version=3。D-PARAM、D-CLAIM、D-REL、D-CHOICE、D-RESULT、D-TABLE、D-SUMMARY、D-CALC和D-SYNTH均从版本1升为2。D-CALC和D-SYNTH在实际复核后重新绑定并完成；独立来源活动D-SOURCE-CHECK的记录和完成绑定保持版本1。来源、CSV、冻结模型、三个既有脚本和来源卡SHA不变，因此没有理由因评价窗口调整而使来源分支失败。

最终只读检查原始输出见`final-check.stdout.json`，退出0：无文件漂移、无配置参数冲突、断点current，三个活动有效状态均为done。该检查只核对身份、依赖和恢复状态；数值与摘要复核证据另存，并不构成人类内容认可或科学认证。

初始参数和Q4 result/table/summary的实际原字节保留在项目`snapshots/initial/`，全部与初始指纹一致。每次旧权威state完整保留在`snapshots/authority/`；修订理由和旧state SHA在当前state的history。当前授权和批准参数保留在`provenance/task-C/author-revision/`。项目内`RECOVER.md`和自包含`scripts/project_status.py`可独立恢复，不依赖本交付目录。

实际失败保留：准备续作控制脚本时，嵌套字符串导致一次IndentationError（退出1），发生在解析阶段、没有执行项目写入；随后改用文本行列表修复并成功执行。另有预期的中间状态检查退出1，原始输出没有被最终成功结果覆盖。完整命令、退出码、读取SHA/bytes及补救见`execution.json`；项目保留实际执行命令于`records/commands-C.json`。

研究约束保持：截止2026-12-15，仅本地Python标准库、原有资料和冻结模型，不采集数据或重训，不外推2012，期刊未定。数值为观察小时的描述性时间留出比较，无置信区间或因果保证。当前没有人类专家认可，也没有投稿授权。

来源仅在所提供缓存和身份卡范围内核对：本地2011切片8645行；未联网读取完整ZIP、完整原始hour.csv或论文。D-REMOTE只有DOI身份，未绑定本地全文或检查当前远端内容。来源卡17379与官网元数据17389的差异仍为给定材料中的差异。自动检查覆盖8个登记路径，`notes/unregistered-scratch.md`未登记；本阶段全文件哈希盘点不把它变成科学依赖。原始PDF/CSV为私人研究缓存，不作公开分发；本交付不附原CSV。

下一步：将2011年11月至12月的冻结模型指标与更新摘要交作者内容复核；保留原Q4结果作历史记录。作者内容复核尚未发生。
