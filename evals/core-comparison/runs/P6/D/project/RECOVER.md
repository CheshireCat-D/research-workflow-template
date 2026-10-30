# 恢复与权威状态

唯一当前配置与逻辑记录为records/state.json（state_version=3）。实际材料与绑定冲突时应报告并复核；旧handoff或笔记不能覆盖新显式修订。

只读恢复：用Python 3标准库解释器执行 python -I -B ROOT/scripts/project_status.py --root ROOT。脚本及guarded_state_update.py都在项目内，迁移只需替换ROOT，无需外部输出或指导包。退出0为身份/依赖/配置/断点一致，1为漂移/陈旧，2为读取/格式错误；不认证科学正确性。

当前范围：2011-11-01至2011-12-31，observed-hour权重，冻结2011年1至9月模型。其他约束保留：截止2026-12-15，仅本地标准库，不采集新数据、不重新拟合，期刊未定。provenance/initial/保留初始约束和来源；provenance/task-C/保留当前授权。

当前具体下一步：将2011年11月至12月的冻结模型指标与更新摘要交作者内容复核；保留原Q4结果作历史记录。不重训、不外推2012；尚未有人类专家认可，也没有投稿授权。

先将实际漂移状态和旧完成绑定保存到snapshots/stage-C-before-recompute/，再保存新断点。records/intermediate-check-C.json显示断点current但D-CALC/D-SYNTH仍stale，D-SOURCE-CHECK仍done。之后实际执行原脚本，更新参数/主张/关系/选择/成果与两个受影响活动。records/validation-C.json及records/commands-C.json保留证据，results-evaluations/C-approved/保留实际运行输出。

初始参数及Q4 result/table/summary原字节在snapshots/initial/。漂移时实际内容在snapshots/stage-C-before-recompute/，每次权威更新旧state在snapshots/authority/。guarded_state_update.py要求旧state SHA与版本，拒绝旧版本覆盖；不要仅刷新断点以掩盖陈旧活动。

跟踪8个材料路径。D-REMOTE只有DOI身份，没有本地全文/当前远端检查；notes/unregistered-scratch.md未登记，不自动检查其内容或依赖。notes/rejected-parameters.json为旧失败试算输入，未用于当前工作。CSV是私人研究缓存，原始PDF/CSV不得公开分发。本次未读取原始完整hour.csv或ZIP、未联网、未重训；来源卡给出的17379与17389行差异保留。没有人类专家认可或投稿授权。
