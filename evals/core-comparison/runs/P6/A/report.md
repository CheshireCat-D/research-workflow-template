# 冻结自行车需求模型：初始状态与核对结果

项目已在新目录建立；`records/state.json`为当前配置、记录版本与依赖的权威表示。原始约束、义务、来源卡及任务规则已留在项目`provenance/`。`scripts/project_status.py`可脱离外部工具包只读恢复。当前8个登记材料路径均与绑定SHA一致，三个活动的声明状态和有效状态均为done，检查点为current。

本次实际运行提供的计算器，评价期2011-10-01至2011-12-31，使用2011年1月至9月的冻结C0/C1参数，按实际观察小时等权计算。正常命令退出0；新结果位于本答卷同目录的`validation-valid/`，其中result.json和table.csv与项目内预制成果逐字节一致。预制成果来自提供材料；本次完成的是重运行核对。

| 指标 | C0 | C1 |
|---|---:|---:|
| MAE | 58.825190494512 | 44.570832407532 |
| RMSE | 86.080568956338 | 67.999969060898 |
| 偏差（预测减实际） | 1.078965171773 | 0.987153115515 |

观察样本为2203小时、92日；C1的MAE相对降低24.23172448%。`results/summary.md`已按日期、样本量、两项MAE、降低比例与范围核对。此结论是指定2011留出范围的描述性比较；未重训，无置信区间，不作因果或2012表现保证。

已实际使用`notes/rejected-parameters.json`运行受控无效试算，其起点2012-01-01晚于终点2011-12-31，退出2并给出`ValueError: evaluation_start must be no later than evaluation_end`。未创建无效输出目录。试算前后8个登记文件的完整SHA和字节数全部一致，包括有效result、table及summary；原有效成果未受影响。这是输入校验测试，不是实际科学分析失败。命令、stdout/stderr及前后摘要保留在`validation.json`，项目内亦保存`records/validation-A.json`和`records/commands-A.json`。

本地`data/hour_2011.csv`共8645行，实际全表解析，均为2011/yr=0；完整SHA为`294d25e98ef1c9c9cec746e17ba3ff9818627ba5aa14baf1b93db7ae218de115`，568668字节，与给定来源身份及清单一致。来源卡中的官方完整hour.csv 17379行与网站metadata 17389行差异予以保留；原始ZIP、完整hour.csv、论文和当前远端页面均未取得或独立检查。冻结模型训练来源只按提供的元数据记录，本次不重新拟合验证。

来源DOI/URL是身份信息；D-REMOTE仅登记DOI，未绑定或检查原文内容。`notes/unregistered-scratch.md`虽随材料保留并有读取清单，但不属于自动计算依赖或检查覆盖。自动状态检查只涉及显式登记的8个科学材料，不能声称全部项目文件均受覆盖。原始CSV保留为私有本地缓存，已写`.gitignore`排除项；禁止随公开仓库分发原始PDF/CSV。

参数、result、table、summary四项初始原字节分别保存在`snapshots/initial/`对应路径，SHA与字节数见`records/initial-snapshots.json`；这些副本可恢复实际内容，不只是摘要。记录均为版本1；以后修订应保存旧内容和依据，依赖变化需要显式复核。`guarded_state_update.py`在答卷目录的隔离副本上完成有效更新/JSON回读及旧版本冲突拒绝测试，冲突退出2且未改当前字节；主项目state保持不变。该测试只验证元数据保护。

恢复时用可用Python标准库解释器运行`python -I -B ROOT/scripts/project_status.py --root ROOT`，具体说明见`RECOVER.md`。目前没有需重做的活动；若评价参数改变，D-CALC及其下游D-SYNTH需重新核对，D-SOURCE-CHECK不因评价起点单独改变而失效。保存新检查点不能代替该复核。

下一步：将已核对的2011第四季度冻结模型指标与摘要交作者讨论；不重训、不外推2012。截止日期2026-12-15是提供的项目约束，预算为离线Python标准库、不采集新数据，期刊未定。未发生人类专家审批或外部投稿。执行记录与输入/产物SHA分别见`execution.json`、`inputs-and-artifacts.json`。
