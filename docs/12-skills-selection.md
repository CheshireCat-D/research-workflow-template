# 技能检索与取舍

本次以提供的技能名称及相关科研库为线索，查阅原作者仓库、实际技能文件、支撑资料与可见许可。该检索有明确范围，并非全网穷尽，也未验证上游宣传的性能或截图中的排名、下载量与星数。名称重合不表示是同一个项目。

## 已整合的增量

| 实际缺口 | 本模板的实现 | 边界 |
|---|---|---|
| 科研图件缺少独立入口 | 激活已有设计中的 `rw-figures`，区分数据图、可编辑示意图、定量面板和AI概念草稿 | 标准库SVG助手只审结构；绘图后端、实际渲染及科学含义分别验证 |
| 代码维护决策未明确 | `rw-workflow` 的按需代码分支 | 复用接口和风格、限制关联改动；保留探索、必要校验和已授权重构 |
| 跨库批量检索不易复查 | `rw-literature` 的检索记录参考 | 记录实际查询、取回范围与导出限制，不强制固定篇数或综述框架 |
| 长期资料反复查阅 | 项目本地索引与来源变化重核 | 按相关章节或片段读取；索引不是全文已读证据，不复制整书成全局技能 |
| 跨学科同名术语 | `rw-question` 的按需术语核对 | 只澄清影响当前选择的歧义，在已有笔记保存必要取舍 |
| 多份材料中的共享事实难以集中核对 | `rw-review` 的按需跨材料参考与报告附表 | 先确认事实身份，保留合理例外；复用原审阅产物与登记，不自动改源数据或提升主张状态 |

现有选题、创新、证据核对、写作、审阅和交接边界继续适用。没有新增同义写作或提问入口，也没有自动下载全文、注册定时任务、推送消息或后台无限循环。

旧法学案例的内容审阅仍绑定当时实际读取的规则。已更新的共享技能在[当时规则证据](../evals/legal/reviewed-guidance.json)中保留从公开提交恢复的原文；源指纹及重建执行文本的指纹须逐项匹配原有记录和独立审阅，法学专用规则仍与当前源码核对。该文件是旧案例的证据材料，不是可运行旧版，也不表示本次共享规则获得了新的法学内容审阅。当前软件回归与本轮独立实际任务另行报告。

## 绘图来源比较

| 原始来源 | 可确认的开放边界 | 取舍 |
|---|---|---|
| [SciPilot Figure](https://github.com/Haojae/scipilot-figure-skill) | MIT；数据图工作流与检查脚本可见 | 参考数据先于选图、字体和分层检查；不复制另一套整包 |
| [TingxiYu academic-figure-skill](https://github.com/TingxiYu/academic-figure-skill) | Apache-2.0 | 参考模板与数据含义匹配；固定刊物尺寸、轮数和确认流程不成为通用要求 |
| [HututuWorks academic-figure](https://github.com/HututuWorks/academic-figure) | Apache-2.0；案例资产另有边界，部分实现未公开 | 区分精确、结构、风格复用；不把案例缩略图当成开放实现或原始数据 |
| [Azhi-ss academic-figure-skills](https://github.com/Azhi-ss/academic-figure-skills) | MIT；分析、生图、PPTX模块可见 | 借鉴语义规格与结构修订保真；重绘或插入图片不等于原生编辑 |
| [Nature Skills](https://github.com/Yuan1z0825/nature-skills) | 根LICENSE为Apache-2.0，具体文件和第三方资产需分别核对 | 参考原生SVG路线和结构／目视／科学检查分离；不整包覆盖现有实现 |
| [CCF-Figure](https://github.com/Deepshare-Official/CCF-Figure) | MIT；核心为提示词工作流 | 可参考论文类型与图示结构；不当作定量绘图或原生矢量执行器 |
| [codex-visio-paper-figure-skill](https://github.com/pengjunchi0/codex-visio-paper-figure-skill) | MIT；依赖Windows与Visio COM | 参考局部坐标与原生图元；不作为跨平台必需后端 |
| [diagram-design](https://github.com/cathrynlavery/diagram-design) | MIT | 参考语义、可访问SVG和保真；不用固定品牌字体／颜色作为期刊规范 |
| [FigGenie](https://github.com/Sleepy-Avacado/FigGenie-paper-diagram-skill) | 代码／文档MIT，论文图、零件和字体另计 | 参考稳定元素与最终尺寸检查；不捆绑第三方论文素材 |

当前图件实现和SVG审计器为本项目原创，未复制上述脚本、模板或图件。选定刊物后直接核对该刊当前官方规范；技能名称不表示出版社认可或接收标准。

## 其他条目的取舍

| 原始来源 | 判断 |
|---|---|
| [karpathy-guidelines](https://github.com/multica-ai/andrej-karpathy-skills) | 只整合代码改动层面的真实缺口；已有提问、证据和停止条件不重抄 |
| [ponytail](https://github.com/DietrichGebert/ponytail) | 调用链与现有实现复用由代码维护分支覆盖 |
| [graphify](https://github.com/Graphify-Labs/graphify) | 来源陈述与推断关系分开；图用于导航，不自动变成支持证据 |
| [archify](https://github.com/tt-a1i/archify) | 结构检查与实际视觉审查分离，融入图件分支 |
| [impeccable](https://github.com/pbakaus/impeccable)、[ui-ux-pro-max](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) | 前端设计专项；本次不加入科研核心 |
| [i-have-adhd（ayghri版本）](https://github.com/ayghri/i-have-adhd) | 表达偏好非研究方法；不引入强制时间估计或固定段落数 |
| [humanizer](https://github.com/blader/humanizer) | 自然表达与事实保真已有覆盖；不新增同义入口或检测器保证 |
| [book-to-skill](https://github.com/virgiliojr94/book-to-skill) | 只取项目资料索引，不安装每本书或照搬效果保证 |
| [find-skills](https://github.com/vercel-labs/skills) | 发现工具，不因榜单命中而安装 |
| [Matt Pocock skills](https://github.com/mattpocock/skills) | 检查grill-with-docs、架构、TDD、handoff、triage及setup条目；术语核对按需吸收，其余已有覆盖或为工程专项 |
| [agent-browser](https://github.com/vercel-labs/agent-browser) | 浏览器工具适配；使用宿主已有可用工具，不增加第二套浏览器运行环境 |
| [PaperPilot（DGU）](https://github.com/DGU-stallion/PaperPilot)、[PaperPilot（LiPu）](https://github.com/LiPu-jpg/PaperPilot) | 两个不同MIT项目；与现有流程多有重合，来源追踪可参考；不移植非开放获取下载链 |
| [PaperPilot（SuperJayLiu）](https://github.com/SuperJayLiu/PaperPilot-Human-Guided-AI-Research-Workflow) | 同名但定位不同；本次未确认明确许可，不复制 |
| paper-novelty-design | 索引所指LaVineLeo原仓库本次未取得；未核验，不列为已采用源码 |
| [arxiv-digest](https://github.com/Yilgrimage/arxiv-digest) | 本次未确认明确许可；不复制cron或群聊推送 |
| [humanities-thesis](https://github.com/ganzhi-black/humanities-thesis-skill) | MIT；细读、史境和理论适用性已有相应方法指导 |
| [literature-review-workflow](https://github.com/xxy985/agent-skills/tree/main/literature-review-workflow) | MIT；筛选排除与阅读范围可参考，不采用固定篇数／DOI-only限制 |
| [Academic Research Skills](https://github.com/Imbad0202/academic-research-skills) | 当前CC BY-NC 4.0；未复制入MIT模板；系统综述和监控只按实际任务选择 |
| [Orchestra Research](https://github.com/Orchestra-Research/AI-Research-SKILLs)、[K-Dense](https://github.com/K-Dense-AI/scientific-agent-skills) | 参考原表／派生材料区分和检索记录；不引入全部数据库、依赖或持续自治循环 |
| [awesome-ai-research-writing](https://github.com/Leey21/awesome-ai-research-writing) | 提示词索引；不把目录条目当作已实现能力 |
| [Anthropic skills](https://github.com/anthropics/skills)、[knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins) | 分别核对技能内容与许可；不将所有公开文件视为同一自由许可 |

来源记录见 [profiles/sources.json](../profiles/sources.json)，发行文件身份见 [来源清单](../provenance/file-origins.json)。上游后续变化不自动进入本模板，后续仍按缺口、适用性、许可和实际任务检查决定。
