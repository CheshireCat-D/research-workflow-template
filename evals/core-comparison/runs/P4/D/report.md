# 迁移后只读恢复答卷

当前研究问题是：在作者指定的2011年观察小时上，比较所给冻结C0/C1自行车需求模型的MAE、RMSE和偏差。迁移后的项目能够凭自身材料和运行资源恢复；本阶段没有重新计算研究结果、修改项目、登记状态、保存断点或执行下一步。

项目根为 `PROJECT_ROOT`，逻辑项目ID为 `P429d69ff49bc4160bf1b573ea3b3676e`。权威配置是 `project.json`，权威版本、依赖、活动状态与游标是 `records/registry.json`（revision 43）。`context/constraints.json`的Q4窗口是原始约束；较新的 `context/stage-C/AUTHOR-REVISION.md`、`approved-parameters.json`、当前参数和版本2登记共同确定有效窗口，旧笔记或历史断点不能覆盖它。

有效参数是2011-11-01至2011-12-31、observed-hour权重、frozen-2011-Jan-Sep模型；结果覆盖1460观察小时、61日。C0采用训练期小时均值，C1采用工作日状态与小时组合的均值，缺少组合回退C0。训练期及参数来源是项目提供的冻结模型记录，本阶段没有重新拟合或独立重建训练系数。

当前 `results/result.json` 的数值如下；`results/table.csv`各项与其一致，摘要六项指标的舍入文本已核对。

| 指标 | C0 | C1 |
|---|---:|---:|
| MAE | 56.64127430990882 | 41.252622564018566 |
| RMSE | 81.70038360631688 | 64.15826564867794 |
| 偏差（预测减实际） | 13.433264561295244 | 13.347664992606457 |

MAE相对降幅为27.16861852664598%。这是所列观察小时上的描述性时间留出比较，没有置信区间、因果识别或任意未来表现保证。原Q4为2011-10-01至12-31、2203小时、92日、MAE降幅24.231724482575867%，原参数、结果、表和摘要实际字节仍在 `history/stage-A-initial/`。窗口变化不代表模型经重训改善，也不能作为模型改善的证据。

已在迁移目录使用共同Python的 `-I -B` 模式实际执行项目自带的只读 `check` 和 `resume`，两者exit 0。当前19条登记本地路径没有缺失或身份变化，四项活动的声明状态与有效状态均为done，断点为current、changed为空；没有因目录位置变化而判定科学输入变化。完整输出为外部 `check.stdout.json`、`resume.stdout.json`，实际argv与cwd为 `read-only-commands.json`。这些检查涉及身份、版本和工作流一致性，不能替代科学内容认可。

| 工作 | 当前版本及状态 | 证据与注意事项 |
|---|---|---|
| D-SOURCE-CHECK | v1，done且有效 | 数据、来源卡与来源核验文件身份未变；不依赖评价窗口，保持完成有依据。 |
| D-CALC | v2，done且有效 | 项目保存的 `validation/stage-C/verification.json` 记录修订窗口的真实脚本执行exit 0和独立指标、计数、表格、输入身份核对。本阶段只读此证据并核对绑定身份，未重跑计算。 |
| D-SYNTH | v2，done且有效 | `results/summary.md` 已按修订窗口更新，`summary-review.json`记录数值和解释检查；作者内容复核仍待进行。 |
| D-INVALID-TEST | v2，done且有效 | 专用 `invalid-test.json` 记录起点晚于终点的输入被exit 2拒绝、无输出、测试当时规范成果未变；它引用的是替换前Q4成果身份，不应当作本阶段现成果哈希。 |

参数、主张、参数限定关系、作者选择、结果、配套表、摘要均为v2。原始数据、科学计算器和冻结模型仍是原身份。修订前漂移状态和原始检查在 `history/stage-C-before-recalculation/`：当时断点虽然current，D-CALC、D-INVALID-TEST、D-SYNTH仍stale，D-SOURCE-CHECK仍done；这保留了“保存断点不等于旧工作已复核”的实际证据，后来实质复核才恢复当前有效状态。

需保留的失败与缺口：首次自写核验代码对csv.reader切片导致TypeError，原代码和报错在 `history/stage-C-verification-failure/`；项目记录随后仅修复自己的核验代码并在新目录复算，科学计算器未改。第一次计算器stdout/stderr曾被重试同名日志覆盖，首次数值输出仍在 `validation/stage-C/recalculation/`，该原始日志缺口不能补造。本阶段首次格式一致性断言也因要求结果包含所有参数字段而产生false：结果格式未重复metric_weighting键；共享字段一致、参数SHA绑定、摘要和代码均表明按观察小时等权。原断言在 `artifact-consistency.json`保留，解释和修正检查另存 `artifact-consistency-reviewed.json`，项目未改。

约束继续有效：离线、Python标准库、不采新数据、不重训、不外推到2012；中文交付，期刊和交付类型未定，治理适用性unknown；给定截止日为2026-12-15，其依据是提供的作者约束。没有人类专家内容认可或外部投稿授权。作者批准窗口修订与专家认可研究内容是不同事实。

主要来源身份为UCI Bike Sharing数据集，DOI `10.24432/C5W894`。当前本地 `data/hour_2011.csv` 的完整SHA为 `294d25e98ef1c9c9cec746e17ba3ff9818627ba5aa14baf1b93db7ae218de115`（568668字节）。来源核验记录称已解析的2011切片有8645小时行；本阶段仅读取完整字节核验身份，没有重新解析观察值。原完整hour.csv的17379行与网站metadata的17389行差异仅为所给来源信息，本阶段未获取或核验网站、原ZIP或完整CSV。D-REMOTE仅DOI `10.1007/s13748-013-0040-3`身份，无本地文章内容绑定或当前远端内容检查。`notes/unregistered-scratch.md`仍未登记，不是输入、输出或依赖；本阶段为只读审计计算它的SHA不扩展系统自动依赖覆盖。

原CSV/PDF只作私有研究缓存，不外发；本答卷未复制或分发原始数据。项目自带恢复运行资源已可在新位置运行，历史日志中的旧绝对路径仅作执行来源记录，本阶段没有打开那些旧位置，也没有依赖原工具包、缓存、旧聊天或其他项目。没有发现本次恢复必需资源缺失；远端全文、原数据重新获取、训练系数独立重建、人类专家复核仍超出已有证据。

当前具体下一步是：将2011年11月至12月的冻结模型指标与更新摘要交作者内容复核；保留原Q4结果作历史记录。审阅材料为 `results/result.json`、`results/table.csv`、`results/summary.md`，依据为 `context/stage-C/`、`notes/stage-C-revision.md` 与 `validation/stage-C/`。范围限于当前窗口、固定模型、观察小时指标及摘要解释，不包括改窗、重训、外推、补取来源或投稿。本阶段只恢复该下一步，没有发送材料或启动后续工作。

全部实际读取文件的相对路径、完整SHA256、字节数和读取范围见 `read-manifest.json`；执行记录及输入输出清单分别为 `execution.json` 与 `inputs-and-artifacts.json`。`project-unchanged.json`比对了本阶段前后全部项目文件字节身份、文件mtime、目录mtime及路径集合，用于确认只读边界。
