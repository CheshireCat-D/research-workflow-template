# 阶段 A 交付

项目已在指定新目录建立并保存配置、逻辑登记、依赖和检查点。原材料全部通过给定完整 SHA256/字节数核对；当前三个活动 T-SOURCE-CHECK、T-CALC、T-SYNTH 均为有效完成，最终恢复检查无错误或警告，检查点 current。完成状态只对应各活动声明的工作范围。

实际以当前参数 alpha=0.05、rho=1（观察前固定）、v=[0,1,10,100] 运行 scripts/compute.py，正常退出0，生成 output/validation-normal/。JSON 与预制结果内容及字节相同；table.csv 的全部数值行逐项相同，生成表使用 CRLF、预制表使用 LF。检查了 v=0 特例及等价对数表达式；摘要中的参数和 v=10 舍入值一致。

| v | 边界 |
|---|---|
| 0 | 2.4477468306808166 |
| 1 | 3.6563948713638483 |
| 10 | 9.606401928868575 |
| 100 | 32.73018624234933 |

使用 notes/rejected-parameters.json 的 alpha=1 实际试算退出2，错误为 `Require 0<alpha<1, rho>0 and finite nonnegative intrinsic times`。无效试算未生成输出目录；notes/parameters.json、results/result.json、results/table.csv、results/summary.md 前后完整 SHA 一致。这是受控输入拒绝测试，不表示科研分析失败。

本次仅复现所给计算器并核对四个点的数值与摘要。必要条件是标量 l0=1，S 与 −S 对同一非负内在时间 V 满足相应 sub-Gaussian 控制，alpha 是两侧总预算，rho 预先固定。没有新证明、覆盖模拟、新颖性判断、人类专家批准或投稿。

来源 T-SRC 为所给 Howard 等论文 arXiv:1810.08240v9、DOI 10.1214/20-AOS1991；本地 PDF 完整 SHA 为 eb3efd547349adfbff25514ae0854c142cd29b96b398be38c9000d69a2f64ca8，1494142 字节。本次核对提供的身份、完整文件指纹、PDF头和原始元数据，并读了来源卡；没有读取论文数学页，卡片中的页码与命题内容不是本次独立确认。T-REMOTE 仅有提供的来源元数据，无本地副本或当前远端内容核验。notes/unregistered-scratch.md 明确排除自动覆盖。原PDF只作私有研究缓存，sources/已排除提交，不能再分发原件。

恢复所需内容真实保存在项目：provenance/initial/ 留存原始约束、义务和来源身份；history/stage-a-initial/ 留存上述四个小文件的完整初始字节和清单；notes/stage-a-validation.json、validation/stage-a/ 留存真实正常/无效试算与前后指纹。唯一权威配置和登记分别是 project.json、records/registry.json；笔记和初始约束是历史来源，不能覆盖更晚有效版本。RECOVERY.md 给出项目内工具的恢复命令与变更处理方式。

约束已持久化：截止日期 2026-12-15（任务作者提供），仅离线标准库，不采新数据、不重拟合，中文，目标期刊未定。下一步先读取实际恢复状态、当前参数和表，再把已核对表与摘要交作者讨论；若材料发生变化，先定位、复核相应活动再显式更新登记。未经内容复核不投稿。

执行中第一次运行资源检查误用了目录，真实退出2；路径修正后检查资源成功。修复脚本又因中间检查点已过期的退出1而停下；实际发现仅涉及恢复说明登记变化，三个科研活动始终新鲜，随后完成登记、检查点和项目内恢复检查。两个外层脚本退出1、最初错误及补救都保留在 execution.json、actual-commands.json、failure-and-remediation.json，项目内亦保存操作更正记录。

外部交付：report.md、state-answer.json、execution.json、inputs-and-artifacts.json。全部科学原文件与给定初始版本一致；没有网络、安装、外部投稿或其他项目访问。
