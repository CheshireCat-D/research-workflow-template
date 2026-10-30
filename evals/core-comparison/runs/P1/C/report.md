已按作者授权，将当前范围改为 alpha=0.05、观察前固定 rho=4、v=[0,1,10,100]，真实复算并修订结果、表、摘要及登记。当前检查 revision=46，无 errors/warnings/findings；T-CALC、T-SYNTH 和独立的 T-SOURCE-CHECK 均 effective done，最终断点 current。完成状态仅表示所声明数值/摘要工作已执行。

重算前先运行只读恢复（退出1），保存新断点（revision=27，退出0），随后立即只读检查（退出1）。原始输出是 output/resume.json、checkpoint-drift.json、check-drift.json；项目中也保留 validation/stage-c 对应文件。该时刻断点已 current，但 notes/parameters.json 仍 file_changed，T-CALC/T-SYNTH 仍 stale；所以“新保存”没有使旧完成工作重新有效。旧结果和摘要仍使用 rho=1，不能交作 rho=4 成果。

现有 scripts/compute.py 在批准参数下真实执行，退出0；产物保存于 validation/stage-c/rho4，并更新当前 results/result.json、results/table.csv。四个边界值如下：

| v | 边界 |
|---:|---:|
| 0 | 4.895493661361633 |
| 1 | 5.57431973357386 |
| 10 | 10.070709270872976 |
| 100 | 31.015388968276124 |

实际复核包含：批准JSON与工作参数一致；结果的alpha/rho/政策和网格正确；用等价的 log(v+rho)-log(rho)-2log(alpha) 表达式独立核对，绝对及相对容差1e-14；v=0特殊值核对；CSV每行数值与JSON一致；结果中的参数和脚本SHA匹配。results/summary.md 已修订并检查四值12位小数、v=10值及条件范围。执行与逐项结果持久保存在 notes/stage-c-validation.json。

唯一权威仍为 project.json 与 records/registry.json。通过正式版本替换接口更新 T-PARAM、T-CLAIM数值评估、T-REL、T-CHOICE、T-RESULT、T-TABLE、T-SUMMARY、T-CALC/T-SYNTH 和恢复说明；旧登记进入版本历史。T-PARAM当前SHA为 `340d3d94ab2386c9716d3fb134933347adaf630424483a7206abca8074cda117`。作者批准原文及JSON在 provenance/stage-c。

初始rho=1的完整参数、结果、表、摘要及SHA仍在 history/stage-a-initial。history/stage-c-before-recompute 保存本轮重算前真实参数、旧结果/表/摘要、配置、登记与旧恢复说明全文，manifest记录实际SHA/bytes及修订理由。没有用最终成功结果替换中间漂移检查。

不受影响的来源分支保持完成：T-SOURCE-CHECK的整条envelope与重算前完全相同；其来源记录、PDF和来源卡不依赖rho。原PDF完整SHA为 `eb3efd547349adfbff25514ae0854c142cd29b96b398be38c9000d69a2f64ca8`；原计算脚本为 `e7b2f754ed7a449ee76a45c80ce3888a36be20f5c783f9a67c630fc7c25c74a1`。脚本、PDF、来源卡和配置前后字节/长度均一致。本轮只对PDF作完整指纹核对，没有阅读其数学页或重新证明定理。来源身份为 Howard等，Time-uniform, nonparametric, nonasymptotic confidence sequences，arXiv:1810.08240v9，DOI 10.1214/20-AOS1991；来源卡是组织者释义。

保留了实际操作失败及补救：首次将作者修订误读为input直属文件，FileNotFoundError退出1，改读已列出的author-revision子目录；复核脚本误把检查字段写成records，而实际为registered-records，断言退出1，原始检查保留；首次最终断点使用不支持的--activity-id，退出2且未保存，读--help后使用--activity重试，成功输出另存checkpoint-final-retry.json。中间断点曾使用非规范简称，已在持久记录中明确对应实际ID。详见 notes/stage-c-operational-corrections.json、外部execution.json及独立原始输出。计算本身没有失败；阶段A已有alpha=1控制失败也保持原样。

最终 check/resume 使用项目内运行文件，均退出0；本地资源完整性检查通过，但未比较远端或工具源码版本。T-REMOTE仅有来源身份，没有本地内容绑定或当前远端内容核验；notes/unregistered-scratch.md未登记，自动检测不覆盖全部项目文件。URL不是内容新鲜度证明。原PDF仅留私有缓存，本答卷及输出清单不再分发其原件。

当前约束：中文；2026-12-15为任务作者给定期限；仅离线Python标准库和既有资料；不收新数据、不重训或重拟合；目标期刊未定。alpha及预先固定正rho政策未变；数值重算不证明新的覆盖保证，不扩展到事后选择rho。没有人类专家内容认可或投稿授权。

当前可执行下一步已写入最终断点和RECOVERY.md：将rho=4的边界表与更新摘要交作者内容复核；暂不扩展到事后选择rho。如恢复时有新漂移，先定位并实质复核受影响分支再显式登记。
