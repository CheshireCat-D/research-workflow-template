# 项目恢复入口

权威状态是 `management/state.json`；给定的研究约束、逻辑义务、来源身份原件分别保存在同目录对应JSON，活动历史在state.history。预制结果仍为 `results/result.json`，`results/table.csv` 必须一致，摘要为 `results/summary.md`。本阶段未改写预制科研材料。

从任何迁移后的项目目录运行：

```sh
/path/to/python -I -B management/status.py --root .
```

只需Python标准库，无第三方包。解释器路径由接续者指向实际可用Python；脚本依据自身路径或显式root运行，不依赖原绝对地址。退出0代表已登记本地身份与快照一致；3代表存在变更、缺失或快照损坏，须读JSON并复核。该程序只读，不写缓存，也不把文件身份检查说成科学认证。不要靠旧handoff或旧done覆盖当前有效字节。状态脚本不能自证 `management/state.json` 从未被篡改，应由授权修订记录与后续给定事件核对其权威内容。

`management/versions/A-initial/` 保存 parameters、result、table、summary 四个原始版本的完整字节和SHA对应记录，可恢复旧成果；不要用旧快照自动覆盖后来经授权修订的文件。需要修订时先保存修订前原字节、修订理由与提供方依据，再更新当前参数、依赖、结果、摘要、活动状态和版本记录。若只改变评价期，D-CALC及D-SYNTH需复核；来源/数据/卡片不变时D-SOURCE-CHECK不因评价期变化而自动失效。任何输入或输出变化均按state中的依赖传播；新保存checkpoint不能替代重新计算和摘要核对。

正常重算须指定新的外部目录，且重新检查当前参数范围：

```sh
/path/to/python -I -B scripts/compute.py --root . --output /new/nonexistent/verification-directory
```

脚本拒绝已存在输出目录；若验证失败，保留原错误与退出码，不覆盖有效results。A的真实运行证据、成功结果副本、失败前后字节/mtime快照均在 `management/evidence/A/`，可独立于外部答卷恢复核验记录。无效输入演练exit=2，未生成其输出目录，整个项目当时字节与目录/文件mtime不变；这是受控无效输入测试。

下一步：当前季度指标、表格与预制摘要已核对，由作者讨论研究表述；作者决定仍未知。禁止重训、2012外推或未经授权外部投稿。截止日期2026-12-15来自所给任务，目标期刊未定。主范围是观察小时加权的描述性留出比较，不包含因果或未来表现保证。

来源覆盖边界：2011切片已实际读取并绑定完整SHA，原完整hour.csv/ZIP、DOI文章和当前网页均未读取。来源卡的17379/17389行差异作为提供方记录保留。`notes/unregistered-scratch.md`虽保留但不登记科学依赖，status不检测该随手草稿变化。不能据此宣称覆盖整个项目所有文件。

本地原始CSV仅供私有研究缓存。发布/迁移前区分私有缓存与公开仓库，遵守所给source-identities.json的“不分发原始PDF/CSV，保留身份与项目结果”规则；本次未联网、未发布。
