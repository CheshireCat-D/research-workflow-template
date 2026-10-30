# 恢复说明

唯一权威配置为 project.json；唯一权威登记、版本和检查点为 records/registry.json。本文和 provenance/initial 中的材料只保留历史及原始约束，不能覆盖更晚有效登记。

从项目根目录执行（Python 3.11+，仅标准库）：

```sh
python3 -I -B .agents/skills/_rw-runtime/tools/research.py resume --root .
python3 -I -B .agents/skills/_rw-runtime/tools/connect_skills.py check --installed-only --root .
```

恢复命令只读且不执行登记里的命令。先读实际 configuration、activities、checkpoint 和 findings。未完成或过期时先定位变化，再复核；保存新检查点不能消除旧活动的失效。更新同一 ID 前使用 show 读取当前 envelope.version，register --replace --expected-version N，禁止手工改权威 JSON。

原始参数为 alpha=0.05、rho=1（观察前固定）、v=[0,1,10,100]。当前数值为 2.4477468306808166、3.6563948713638483、9.606401928868575、32.73018624234933。来源卡是组织者释义；本次只核对固定材料身份、卡片文字和数值，没有读取论文数学页或证明覆盖。

本阶段实际试算与失败原文：notes/stage-a-validation.json 和 validation/stage-a/。无效 alpha=1 退出2，未生成试算输出目录，原有效四文件完整SHA未变。该试算不代表研究失败。

重新计算时从项目根调用 scripts/compute.py --root . --output 一个尚不存在的新目录，使用 python3 -I -B。比对 JSON 内容、table.csv 数值行及 summary 参数与舍入值；正常输出 CSV 的CRLF与原表LF差别无数值含义。

history/stage-a-initial 下保存 notes/parameters.json、results/result.json、results/table.csv、results/summary.md 的完整初始字节及SHA/长度。任何修订前先保留当前内容和理由；先比较历史再决定恢复，不要盲目覆盖当前工作。大型PDF仅保留工作缓存一次。

完整给定约束和逻辑义务见 provenance/initial/constraints.json、obligations.json、BRIEF.md、source-identities.json。截止日期 2026-12-15 是任务作者提供的约束；离线标准库、禁止新数据和模型重拟合、中文、目标期刊未定；无人类专家批准，无外部投稿授权。原PDF只作私有研究缓存，sources/已排除提交，不得再分发原件。

覆盖范围：T-REMOTE 只有来源身份，无本地内容绑定，也没有当前远端核验。notes/unregistered-scratch.md 明确未登记，不属于自动变更覆盖；来源URL不是内容绑定。工具状态新鲜不等于科学认证。

下一步：先运行项目内恢复检查并读取当前参数、结果和表；若身份与活动仍新鲜，将 alpha=0.05、rho=1（观察前固定）、v=[0,1,10,100] 的已核对表及摘要交作者讨论。若文件或登记变化，先定位并实质复核 T-CALC/T-SYNTH，再显式更新登记；未经内容复核不投稿。
