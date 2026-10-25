# 技能与方法接入

当前实现九个 `rw-*` 技能、十类方法指导和七类学科画像，维护源分别在仓库 `skills/` 与 `profiles/`。它们由宿主代理根据任务读取并执行。共享登记规则位于[接入协议](../core/skill-bridge.md)，统一处理记录版本、检查点和只读命令。软件只维护当前一份；研究记录版本仍按兼容契约保留。

## 在新研究项目中使用

从模板仓库根目录运行，替换标题及尚不存在的项目目录：

```sh
python3 tools/research.py init --output ../my-research --title "我的研究问题"
python3 tools/connect_skills.py install --root ../my-research
python3 tools/connect_skills.py check --root ../my-research
```

接入会在该项目内生成 `.agents/skills/`：九个技能目录及一个不作为技能发现的 `_rw-runtime/` 共用资源目录。代码、登记模式和方法／学科画像随项目复制，不依赖开发者的个人包、Python 虚拟环境或原仓库路径。已有 `AGENTS.md` 保持原样；已有 `.agents/skills` 时拒绝覆盖，包括空目录。

然后在 Codex 中打开研究项目，以自然语言说明任务，例如：

> 从这些研究兴趣开始，先形成一个有范围的问题，说明最值得做的下一项检查。

> 阅读 inputs 中提供的材料，核对现有主张，完成适用的验证，写出修订稿并审阅，最后保存下一步。

宿主可以根据技能 description 选择技能；也可明确指定 `$rw-workflow` 等名字。项目目录属于 Codex 的本地技能发现位置，匹配与加载机制见 [OpenAI 官方说明](https://learn.chatgpt.com/docs/build-skills)。接入工具检验文件与布局，不声称已经通过真实界面的自动触发测试；技能没有出现时，先确认打开的是目标项目及其加载状态。

## 选择当前任务

| 请求 | 入口 | 交付重点 |
|---|---|---|
| 从零组织、继续研究、恢复项目 | `rw-workflow` | 读取当前记录与变化，协调本轮必要工作 |
| 研究兴趣、选题、问题范围与少量候选取舍 | `rw-question` | 有范围的问题、已有依据、未知与最小下一项检查 |
| 文献查阅、来源支持、相关工作 | `rw-literature` | 实际访问状态、原文定位、支持与限制；离线材料同样可用 |
| 机制、构造、概念或设计创新 | `rw-innovation` | 明确假设与机制、便宜反驳检查、修订或停止依据 |
| 多个候选方向的对抗与取舍 | `rw-candidates` | 最强支持、证据反驳、未知及决定性下一项检查 |
| 证明、计算、实证、解释或设计检查 | `rw-validation` | 按所需方法读取画像，交付实际推导、分析或运行依据 |
| 起草、润色、翻译、压缩 | `rw-writing` | 按请求选择模式，保留论证身份与作者声音 |
| 自审、返修、审稿回复、交付核对 | `rw-review` | 可定位发现、实际检查、已完成修改与仍存缺口 |
| 科研数据图、可编辑示意图与图件审查 | `rw-figures` | 原始依据、绘图源、最终尺寸预览及实际完成的结构／目视检查 |

不要为了走流程逐一调用所有技能，也不对单条已定方向强制做候选比赛。图表格式扩展仍在后续计划中；当前路由只调用实际存在的入口。

## 方法与学科适配

- [形式与理论](../profiles/methods/formal-theory.md)：明确对象、假设与量词，处理证明义务、反例和修正版；手工证明与形式化证明分别报告。
- [计算研究](../profiles/methods/computational.md)：保存输入、参数、代码、运行条件、结果和失败；先独立核对基准，再解释有限实验范围。
- [历史与阐释](../profiles/methods/historical-interpretive.md)：确认材料身份和生成语境，区分直接记载与推论，处理同源材料及竞争解释。
- [测量与实验](../profiles/methods/measurement-experiment.md)：处理分配与实验单位、测量校准、区组、重复及环境范围。
- [量化实证](../profiles/methods/empirical-quantitative.md)：区别描述、随机干预、观察因果、预测与调查，保留目标量和分析版本。
- [工程设计](../profiles/methods/engineering-design.md)：需求、工况、验收、失效与实际用途的对应。
- [定性研究](../profiles/methods/qualitative.md)：材料到解释的路径、反身性、反向案例及引用范围。
- [概念与规范论证](../profiles/methods/conceptual-normative.md)：概念、经验前提、价值桥梁、异议与条件性结论。
- [法律解释与法源分析](../profiles/methods/legal-analysis.md)：法域、相关时间、效力依据、裁判理由与后续处理、可定位引证；[项目与台账模板](../profiles/templates/legal-research.md)随运行副本复制。
- [证据综合](../profiles/methods/evidence-synthesis.md)：综述类型、实际检索范围、研究级去重、分母及综合适用性。

按研究对象选择 [学科画像](../profiles/disciplines/)，再按证据义务组合方法；跨学科结果可能一致、互补或冲突，整合结论需另行给理由。[治理说明](../profiles/governance.md) 按具体行动处理材料与参与者权限，[来源记录](../profiles/sources.json) 区分已读范围和适用性。画像是工作的指导；选择方法 ID 或登记 `done` 都不能代替实际工作，代表性任务通过也不覆盖所有变体或取代专业责任。

## 修改与核验

研究代码与工具的实现或维护按 `rw-workflow` 的[对应分支](../skills/rw-workflow/SKILL.md#研究代码与工具维护)执行；仅补充代码改动范围、结构复用和风险相称验证，其他任务继续沿用各自技能。

修改仓库里的维护源，再运行 `python3 tools/check_core.py`。项目内副本是生成产物；不要同时维护两套指令。源码中的 `connect_skills.py check` 只读区分“已安装文件改变／丢失”和“源版本不同”。复制的连接检查器默认只核对已安装资源，也可显式加 `--installed-only`；`source_version_matches=null` 表示未比较来源。旧六技能格式1副本仍可读取，升级仍需显式执行。

## 升级已有项目的技能副本

从当前完整模板目录运行：

```sh
python3 tools/connect_skills.py check --root ../my-research
python3 tools/connect_skills.py upgrade --root ../my-research
python3 tools/connect_skills.py check --root ../my-research
```

首次 `check` 若只发现 `bundle_source_version_differs`，表示项目内副本完整，但与当前模板不同。`upgrade` 仅接受完整副本：文件被修改、缺失，或出现未登记文件、空目录、链接时均拒绝覆盖，先保存并审阅本地改动。没有副本时使用 `install`；项目中复制的 `_rw-runtime/tools/connect_skills.py` 可只读检查，但不能作为升级来源，升级需从完整模板目录执行。同一来源内容返回 `upgraded: false`，不会为此创建写锁。

升级持有项目写锁，在 `.agents/` 下写好完整临时副本后再次核对原副本，将原目录暂存为备份，再将新目录发布到 `skills`；成功后删除旧备份。研究登记、配置、作者笔记及全局技能不随升级修改。源文件中指向 `core/`、`profiles/`、`tools/` 的Markdown链接按文档实际目录深度映射到共享运行目录，技能内部的相对链接保留。

POSIX通用接口不能用一次 `rename` 交换两个非空目录。这里每次目录改名都是原子的，整次升级采用两次改名；两者之间路径可能短暂不存在，同时读取的代理应重试。执行前暂停正在读取该项目技能的宿主。捕获到发布失败时会尝试恢复旧目录；若返回 `upgrade_recovery_required`，先按错误中保留的 `.agents/.rw-skills-backup-*` 位置审阅并恢复，再重试。若返回 `upgrade_cleanup_required`，新副本已发布，仅旧备份清理失败。进程强制终止、断电和绕过写锁的外部目录替换没有完整事务保证。

三项基础回归任务保存在[基础素材](../evals/d2/README.md)，跨学科任务及场景映射在[覆盖记录](../evals/d3/coverage.json)，法学新增场景在[法学覆盖](../evals/legal/coverage.json)。这些是当前测试依赖的不同材料组，不是旧软件副本。执行者只获得任务、原始材料和技能；内容复核与自动回归分开。旧任务的冻结材料与审阅指纹保持原样，新增方法用新任务核验，不继承旧任务的执行结论。自动测试重跑代码和登记流程，不能重新产生一次独立模型评估。

本轮外部技能检索、未采用条目与整合边界见[技能检索与取舍](12-skills-selection.md)。
