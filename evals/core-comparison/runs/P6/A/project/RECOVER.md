# 恢复与权威状态

当前配置、逻辑记录与版本的唯一权威表示为 `records/state.json`。作者笔记或旧handoff不得覆盖较新配置；文件的实际字节如果不同于绑定值，应当报告冲突，而不是悄悄接受。原始初始约束和身份材料保留在 `provenance/initial/`，当前配置以后显式修订后以state.json为准。

只读恢复命令（迁移时将ROOT替换为新项目绝对路径，使用可用的Python 3标准库解释器）：

```sh
EVAL_PYTHON -I -B ROOT/scripts/project_status.py --root ROOT
```

脚本完全自包含，不需要外部工具包或本阶段OUTPUT_DIR。退出0表示登记的身份/依赖与检查点一致；退出1表示有漂移/陈旧活动；退出2为读取/格式错误。它不重算、不写项目、不自动接受变化、不认证科学正确性。跟踪8个材料路径，未登记scratch和无本地绑定的来源不在自动文件检查中。

## 当前具体下一步

将已核对的2011第四季度冻结模型指标与摘要交作者讨论；不重新训练，不外推2012。本阶段未发送、未提交，也未获得人类专家批准。材料若变化，先定位具体改变，沿依赖复核D-CALC及D-SYNTH；D-SOURCE-CHECK独立于评价参数，只有其来源、原始数据或来源卡本身变化才需要重做。

## 实际执行和科学边界

`records/validation-A.json`及`records/commands-A.json`保留正常执行与受控无效输入测试。有效计算和预制result/table逐字节相等；summary按其声明的日期、样本量、MAE和降低比例复核。未重训模型，也未核验完整原始hour.csv、ZIP或远端论文/官网内容。8645行2011切片SHA与提供的来源身份一致。原始完整hour.csv 17379行与网站metadata 17389行的差异只按来源卡保留，没有联网核实。

## 版本保留和并发修订

初始参数、result、table、summary的原字节在`snapshots/initial/`，可恢复被覆盖内容；恢复前先保留当前版本，不能无条件覆盖。`scripts/guarded_state_update.py`只提交一个已经准备并审阅的完整新state候选。要求同时提供实际读取的旧state SHA与旧state_version，新state_version须恰增1，修改记录的version须恰增1，并给出reason。旧state完整保留在`snapshots/authority/`，不允许旧handoff覆盖新state。该工具只更新权威元数据；科学文件和活动完成绑定应由执行者在真实复核后显式准备。不要仅刷新checkpoint来掩盖陈旧活动。

四个初始快照完整SHA在`records/initial-snapshots.json`。大型CSV只保留项目内私有缓存一份，原始PDF/CSV禁止随公开仓库分发；可以公开身份和本项目结果。没有新的目标期刊决定，venue保持未定。
