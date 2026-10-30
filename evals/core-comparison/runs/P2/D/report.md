# 迁移后只读恢复报告

当前可恢复的有效研究范围是2011-11-01至2011-12-31的1460个实际观察小时、61日，固定使用2011年1月至9月获得的C0/C1参数，观察小时等权。研究问题是比较这两个固定预测规则在指定窗口上的MAE、RMSE和预测减实际的平均偏差。当前版本已完成原脚本计算及摘要更新，下一步仍是作者内容复核；没有人类专家内容认可，也没有投稿授权。

## 有效版本和约束

项目现位于 `PROJECT_ROOT`。恢复入口是 `RECOVERY.md`；权威台账为 `management/state.json`。当前 `notes/parameters.json` 与 `management/constraints.json` 的现行范围及 `management/evidence/C/authorization/approved-parameters.json` 完全一致，修订理由原件为同目录下 `AUTHOR-REVISION.md`。当前有效版本是 C-author-revision，断点为 `management/checkpoints/C-final/`。

保留的约束：截止日期2026-12-15（任务提供的日期）；期刊未定；中文；离线Python标准库；不新增采集、不重新拟合、不外推2012。结论仅为描述性时间留出比较，不包含置信区间、因果结论或任意未来保证。参数文件是作者工作材料，评价窗口调整不修改原始来源。

`management/BRIEF.md`、约束中的 `initial_next_action`、`management/MANIFEST.json` 和台账中的旧 `checkpoint.id=A-verified-initial` 保留初始背景；不能据此退回Q4范围。较新的作者授权、当前参数、活动绑定和 `checkpoints.current` 均指向11月至12月。旧字段残留是维护上的歧义，本次只读不修复。

## 本次实际检查及现有结果

迁移后实际运行 `management/status.py --root .`（共同Python带 `-I -B`），退出码0；35个登记文件无变更或缺失，9个版本快照均完整，当前受影响活动为空。另逐一比较了活动的输入输出绑定、当前结果输入散列、参数与授权、表格与已存结果、两个断点清单及其真实文件。初始漂移断点31项、最终断点6项均无散列或字节数差异；最终断点6个文件均与当前对应文件一致。原数据、计算器、冻结模型和独立来源材料均与重算前保留字节一致。项目全文件字节及文件/目录mtime与本次进入后的基线一致。

以下数值读取自 `results/result.json`，`results/table.csv` 与它一致，摘要为 `results/summary.md`：

| 指标 | C0 | C1 |
|---|---:|---:|
| MAE | 56.64127430990882 | 41.252622564018566 |
| RMSE | 81.70038360631688 | 64.15826564867794 |
| 预测减实际平均偏差 | 13.433264561295244 | 13.347664992606457 |

已存MAE相对降幅为27.16861853%。原Q4（2011-10-01至12-31）2203小时、92日的参数、结果、表格、摘要完整保存在 `management/versions/A-initial/`，其降幅为24.23172448%。新旧评价窗口不同、冻结模型字节相同，这个差别不能表述为重训改善或模型改善。

本次没有重算研究指标，没有运行 `scripts/compute.py` 或 `management/verify_current.py`；后者虽然不写项目，仍会重新计算指标，因此本阶段只读其源文并保留未执行状态。项目自己的 `management/evidence/C/compute-run.json` 保留此前真实计算命令及exit=0，`checks-before-promotion.json`、`final-numerical-verification.stdout.json` 与 `summary-review.json` 保留此前数值与摘要复核证据。本次恢复不把这些旧记录写成新执行。

## 工作状态与历史因果关系

- D-SOURCE-CHECK：限定来源身份/本地版本工作已完成，当前绑定未变。评价期修订不影响这一独立分支，范围不扩展到远端内容核验。
- D-CALC：当前授权窗口的实际计算与指标复核已在项目记录完成，当前输入/输出绑定仍匹配。
- D-SYNTH：摘要随窗口、样本数、数值和解释范围更新，当前绑定仍匹配；作者内容认可仍待完成。

`management/checkpoints/C-pre-recompute/` 保存的是参数已变、结果尚为Q4的真实漂移状态。原始 `management/evidence/C/intermediate-check.json` 记载只读status退出3，`intermediate-status.stdout.json` 明确只有D-CALC和D-SYNTH受影响，D-SOURCE-CHECK不受影响。保存新断点并未使旧工作重新有效。其后真实重算与摘要修订才建立当前完成状态；中间失败/失效记录仍被保留，没有被最终成功输出覆盖。

## 来源与覆盖边界

来源卡 `management/source-identities.json` 标识UCI Bike Sharing，DOI `10.24432/C5W894`，私有本地2011切片为 `data/hour_2011.csv`，568668字节，完整SHA256为 `294d25e98ef1c9c9cec746e17ba3ff9818627ba5aa14baf1b93db7ae218de115`。本次逐字节核验其身份，未解析原始数据重新计分；8645行是项目既存来源核验记录。C0按小时、C1按工作日标记和小时的冻结均值预测，C1空单元回退C0。

原完整CSV17379行与官网metadata17389的差异按来源卡保留，本次没有取得完整CSV、官方ZIP或网页来裁定。研究文章DOI `10.1007/s13748-013-0040-3` 仅有身份，无本地文章全文绑定；URL存在不能说明远端内容已经检查。`notes/unregistered-scratch.md` 不属于登记科学依赖，status不自动覆盖其变化。本次读取清单与身份列在 `inputs-and-artifacts.json`，不分发原始CSV/PDF。

## 当前下一步及范围

将2011年11月至12月冻结模型指标、更新摘要、作者窗口授权和保留的Q4对比交作者内容复核，保留旧Q4成果作为历史。复核应确认研究表述和窗口选择的内容含义；不能把本地状态、散列一致或旧数值核验视为科学认可或投稿验收。本次未联系作者、未提交、未执行该下一步。

迁移项目已经保留恢复说明、独立的只读状态脚本、计算器、模型、数据、授权、版本和证据；当前恢复没有必须从原工具包补入的资源缺口。可在新目录用共同Python执行 `-I -B management/status.py --root .` 进行身份检查；若未来另获数值重核授权，再考虑运行数值验证器。本次没有初始化、登记、保存新checkpoint、修改项目或使用旧路径。
