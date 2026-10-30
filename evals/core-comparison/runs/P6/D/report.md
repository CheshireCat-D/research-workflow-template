# 迁移后的只读恢复结果

项目可凭自身留下的材料恢复。唯一当前逻辑权威是 `records/state.json`，版本3，完整SHA256为 `18acf19e64447854c55c57b369ad4795eade5180d4f268bfbe0c8266a69a42cc`。本阶段实际在迁移位置运行了项目自己的只读状态脚本，退出0：8个登记材料路径全部与绑定一致，未发现缺失或漂移，配置与参数没有冲突，断点为current，3项活动的有效状态均为done。位置变化没有改变科学证据。

## 当前问题与约束

在2011-11-01至2011-12-31实际观察小时上，比较固定C0/C1的MAE、RMSE与预测减实际偏差。C0为训练期按小时均值，C1按(workingday,hr)均值，未见单元回退C0；使用给定2011年1月至9月冻结参数。指标按实际观察小时加权，不补齐缺失小时。这是描述性时间留出比较。

期限2026-12-15（任务作者提供的项目期限）；离线、Python标准库；不采集新数据，不重新拟合，不外推2012；期刊未定。未有人类专家完成内容认可，没有投稿授权。当前范围取自版本3、实际 `notes/parameters.json` 和项目内作者修订授权，不能用初始constraints中的Q4范围或旧handoff覆盖。

## 有效成果与已完成工作

当前 `results/result.json`、`results/table.csv`、`results/summary.md` 对应1460个观察小时、61日。

| 指标 | C0 | C1 |
|---|---:|---:|
| MAE | 56.64127430990882 | 41.252622564018566 |
| RMSE | 81.70038360631688 | 64.15826564867794 |
| 预测减实际平均偏差 | 13.433264561295244 | 13.347664992606457 |

MAE相对降幅为0.2716861852664598，约27.16861853%。本阶段只读取现有成果并检查身份与相互一致性，没有重新计算研究指标。表中7项已交付数值与canonical JSON逐项一致，当前result/table字节分别等同项目内 `results-evaluations/C-approved/` 留下的真实运行成果。摘要中的窗口、样本数、指标和范围与其一致。

- `D-SOURCE-CHECK` 版本1，done：检查提供的来源身份、本地切片与覆盖说明。其输入和输出不依赖评价窗口，窗口变动未使其失效。
- `D-CALC` 版本2，done：项目内历史命令记录显示授权11月至12月窗口实际运行计算脚本，退出0；`records/validation-C.json` 保存当时独立固定预测核对和输出一致证据。
- `D-SYNTH` 版本2，done：当时AI执行者已更新并核对摘要，依赖D-CALC；作者内容复核仍待完成。

“done”表示登记的工作完成且绑定仍有效；本次状态脚本不认证研究正确性。研究结果复算和独立数值验证属于项目内先前证据，不冒充本阶段新执行。

## 修订过程与历史内容

`provenance/task-C/author-revision/AUTHOR-REVISION.md` 授权把Q4评价期改为11月至12月。参数、主张、关系、选择、result/table/summary及两个受影响活动均已更新到版本2，台账版本为3。原始数据、计算脚本、模型和独立来源核验分支保持版本1。

初始参数及Q4成果的实际旧字节在 `snapshots/initial/`：2011-10-01至12-31，2203小时、92日，MAE降幅0.24231724482575867。修订前真实漂移状态在 `snapshots/stage-C-before-recompute/`；版本1、2权威台账实际旧内容在 `snapshots/authority/`，本阶段已核对两份快照完整SHA与history声明一致。

`records/intermediate-check-C.json` 保留关键中间事实：刚保存新断点时，checkpoint虽为current，D-CALC与D-SYNTH仍stale，参数与旧配置也冲突；来源核验仍done。之后才有实际复算和更新记录。最终状态不能抹掉这一过程。新旧降幅属于不同评价窗口，不能解释为重训或模型改善。

`notes/rejected-parameters.json` 为旧失败试算输入，起点2012-01-01晚于终点2011-12-31，未用于当前结果；历史命令保留其退出2。旧状态覆盖保护的测试及中间漂移检查也保留原退出码，均非本阶段新失败。

## 来源与覆盖边界

来源身份为UCI Bike Sharing dataset，DOI `10.24432/C5W894`。本地 `data/hour_2011.csv` 为提供的8645行2011切片；完整SHA256 `294d25e98ef1c9c9cec746e17ba3ff9818627ba5aa14baf1b93db7ae218de115`，568668 bytes。本阶段对该文件读取全字节并核对身份，没有重新解析或评分CSV。提供的“官方未变切片”等来源说明属于项目保存的身份记录，本阶段未独立重新核验远端真实性。

`D-REMOTE` 只留下论文DOI `10.1007/s13748-013-0040-3`，无本地全文、无当前远端内容核验。未读取原始完整hour.csv或ZIP；来源卡保留完整原件17379行与网站metadata17389行的差异，不能抹平。`notes/unregistered-scratch.md` 未登记，不属于自动科学依赖覆盖；本阶段全项目文件哈希清单也不把它升级为科学输入。CSV与原始PDF仅供私人研究缓存，不公开分发。

登记材料为data/hour_2011.csv、notes/parameters.json、scripts/compute.py、model/frozen.json、results/result.json、results/table.csv、results/summary.md、notes/source-check.md。全部实际读取文件的完整SHA256和字节数在外部 `read-manifest.json` 及 `inputs-and-artifacts.json`。没有访问旧项目位置、旧工具包、其他阶段外部答卷或网络；旧日志里的绝对路径仅作历史文本。

## 具体下一步与运行边界

下一步是将2011年11月至12月冻结模型指标与更新摘要交作者内容复核，并保留Q4结果作历史记录。待审材料为当前 `results/result.json`、`results/table.csv`、`results/summary.md` 和项目内修订授权；核对范围是日期、观察小时口径、指标、摘要及新旧窗口解释。此步骤尚未执行，不意味着已经联系作者、得到专家认可或获得投稿授权。

如以后仅需再次读取状态，可在新位置运行：

```sh
'EVAL_PYTHON' -I -B 'PROJECT_ROOT/scripts/project_status.py' --root 'PROJECT_ROOT'
```

本阶段已实际使用该命令。只读运行依赖项目内脚本与共同Python标准库，无需旧工具包。guarded_state_update.py也已保存于项目，其写入功能本阶段没有执行。没有重新初始化、重算、修复、登记、保存新checkpoint或自动执行下一步。项目迁移后的字节及文件/目录mtime复核见 `readonly-verification.json`。
