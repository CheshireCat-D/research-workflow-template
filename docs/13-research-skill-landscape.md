# 科研技能来源与对比

检索日期：2026-11-10。范围：只读 GitHub 仓库元数据、README、LICENSE、选定 SKILL.md；没有安装技能、执行上游脚本、修改个人技能包，也没有实测这些上游工具的科研效果。下列能力是源码/文档所述定位，不等于效果认证。

## PaperSpine5 与 RWT

[PaperSpine5 的原仓库是 WUBING2023/PaperSpine](https://github.com/WUBING2023/PaperSpine)。它以 `paper-spine` 为入口，提供研究、写作、配图、审阅与交付流程，并通过本地网页工作台选择方案、查看产物和反馈修改。[当前 README](https://github.com/WUBING2023/PaperSpine/blob/main/README.md)列出的发行版是 `v0.4.0-alpha.3`，根许可证为 MIT；这些是文档与仓库元数据的核对结果，本轮未安装套件。

| 维度 | PaperSpine5（文档所述） | RWT（当前源码） |
|---|---|---|
| 使用入口 | `paper-spine` 与本地网页工作台 | 九个 `rw-*` 技能与 Python 命令行 |
| 主要组织方式 | 论文任务、方案选择、图文预览与交付 | 主张、来源、证据、产物、活动与检查点 |
| 展示与交付 | 文档强调 Word / LaTeX / PDF 与页面预览 | 可编辑产物由宿主与任务工具生成，项目记录贯穿全过程 |
| 恢复入口 | 文档要求继续已有任务与配置 | `resume` 重新检查已登记文件与保存状态，再返回恢复摘要 |
| 当前判断 | 值得参考图文呈现与论文交付体验 | 保留证据登记和恢复主线，按实际任务补充专项能力 |

这不是同材料、同模型的性能测试，不能据此得出谁的论文质量、正确性或总体能力更高。PaperSpine5 是单独的项目；下面五组是其他候选技能库，不能未经核实称为 PaperSpine5 的内置组成。

## 五组综合技能的对应关系

| 检索名称 | 核验到的原仓库 | 定位及与 RWT 的关系 | 许可与身份限制 |
|---|---|---|---|
| scientific agent | [K-Dense-AI/scientific-agent-skills](https://github.com/K-Dense-AI/scientific-agent-skills) | 领域工具、数据库和分析方法技能库。可以补充 RWT 的领域执行层；文献综述、写作、审稿入口与 RWT 已有功能重叠。 | 根 [LICENSE.md](https://github.com/K-Dense-AI/scientific-agent-skills/blob/main/LICENSE.md) 为 MIT；逐项技能/第三方资源仍需复核。已读 literature-review 与 scientific-slides 的 frontmatter，均明确 MIT。 |
| nature | [Yuan1z0825/nature-skills](https://github.com/Yuan1z0825/nature-skills) | 读文献、论文写作、绘图、审稿、回应、社科选题、检索及 PPT 等。最值得按需参考的是专门的检索/社科/PPT 分支，而非把整套同类入口重复塞入 RWT。 | 根 [LICENSE](https://github.com/Yuan1z0825/nature-skills/blob/main/LICENSE) 为 Apache-2.0。共享依赖 nature-shared 需保留；社区改编材料的来源应单独追踪。 |
| academic research | [Imbad0202/academic-research-skills](https://github.com/Imbad0202/academic-research-skills) | research → write → review → revise → finalize，含 deep-research、academic-paper、reviewer、pipeline、sr-screener 等。整体流程与 RWT 重叠较多。 | 当前 [LICENSE](https://github.com/Imbad0202/academic-research-skills/blob/main/LICENSE) 明确 **CC BY-NC 4.0**。不能把其内容作为 MIT 内容直接混入 RWT。优先保留外链和独立比较。另有作者的 [Codex 版](https://github.com/Imbad0202/academic-research-skills-codex)，本轮未逐文件审核。 |
| codex auto research | **存在歧义**；更贴近“综合 skill”的候选是 [leo-lilinxiao/codex-autoresearch](https://github.com/leo-lilinxiao/codex-autoresearch) | 用可执行指标控制修改、验证、保留/回滚的迭代，适合已有量化评价器的实验/代码优化；并非一般论文全流程。可补充 RWT 实验迭代能力，但引入独立执行/恢复控制器会增加复杂度。 | 该候选根 MIT。README 包含 Full Access / bypass 示例，本轮没有执行；不得将该权限模式当作 RWT 默认。相近仓库还包括 dollarser/codex-auto-research 与 yangtianchangxiao/codex-auto-research，二者根目录未识别公开许可，定位也不同。不能默认为同一项目。 |
| codex class academic skills | 推定是 [zLanqing/codex-claude-academic-skills](https://github.com/zLanqing/codex-claude-academic-skills)，即 class 可能是 claude 的误写 | 三个技能为 research-writing-skill、office-academic-skill、scientific-toolkit-skill；中文写作、学术 DOCX/PPTX、MATLAB/Python 科学计算。Office 交付可补 RWT，写作/绘图明显重叠。 | 根 MIT，README 明确外部引用资源服从原许可。安装示例仍有“你的用户名”占位符，不应照抄。精确同名 [syly0315/codex-class-academic-skills](https://github.com/syly0315/codex-class-academic-skills) 经 API 确认为空仓库；不能作为可用技能包。 |

## thesis-delivery-zh 与专项候选

| 类型 | 直接入口 | 核验到的能力/边界 |
|---|---|---|
| 中文毕业论文交付 | [sanipedro679-gif/thesis-delivery-zh](https://github.com/sanipedro679-gif/thesis-delivery-zh) | 学校要求与材料用途、来源台账、数字引用检查、DOCX 结构/样式检查、可验证经验维护。脚本只读稿件，引用脚本不联网核验，也不替代逐页渲染检查。根目录无 LICENSE，API license=null；当前仅适合作为外部参考入口，不能据此宣称已获再分发许可。 |
| 系统/范围/叙述综述 | [K-Dense literature-review](https://github.com/K-Dense-AI/scientific-agent-skills/tree/main/skills/literature-review) | 记录检索字符串、日期与覆盖范围、筛选及全文取得、records/reports/studies 区分、引用核对。MIT；部分可选流程使用外部 API 或 Pandoc/XeLaTeX，不能说全部无依赖或离线。 |
| 跨源文献检索 | [nature-academic-search](https://github.com/Yuan1z0825/nature-skills/tree/main/skills/nature-academic-search) | 多来源检索、引文核验、MeSH、RIS/BibTeX 管理、他引审计。仓库 Apache-2.0；MCP/部分 provider 有额外依赖或凭据。它本来就在 Nature 包中，不另算一个独立综合包。 |
| 社科选题与论证 | [nature-social-science](https://github.com/Yuan1z0825/nature-skills/tree/main/skills/nature-social-science) | 研究问题、文献版图、证据路线、主张边界、可行性与审稿人攻击。覆盖定量/质性/民族志/档案等；社区改编技能，整合时核对其原始提示词与参考来源。 |
| 社科正文写作候选 | [Norman-bury/research-writing-skill](https://github.com/Norman-bury/research-writing-skill) 的 skills/writing-humanities | 根 MIT，按学科路由、论证/章节/证据组织。README 明确默认产物是 Markdown/TeX，不是可提交的 Word 成品；不能宣传为自动完成 DOCX 排版。 |
| 论文生成 PPTX | [nature-paper2ppt](https://github.com/Yuan1z0825/nature-skills/tree/main/skills/nature-paper2ppt) | 论文/笔记 → 中文学术 PPTX、来源图、演讲备注、实际 PPTX 审计。依赖 nature-shared 及关联资源；该入口并非单一提示词文件。 |
| 科研演示 PPTX/Beamer | [K-Dense scientific-slides](https://github.com/K-Dense-AI/scientific-agent-skills/tree/main/skills/scientific-slides) | 讲稿结构、时间、视觉设计与渲染验证；支持 PowerPoint/Beamer。MIT；可选生成图路径涉及 API，精确公式与结果图应走可编辑格式。 |
| 论文生成离线网页演示 | [O0000-code/paper-deck-reveal](https://github.com/O0000-code/paper-deck-reveal) | 输出 reveal.js 演示文件夹，包含来源图、讲者模式、可交互实验讲解和离线资源。Apache-2.0。输出是 HTML 演示，不应写成 PPTX 生成器。 |

## 只读核验时的 main 引用

这些是检索时读取到的分支指纹；正文内容是同期 main 读取，未执行测试。

- K-Dense-AI/scientific-agent-skills: `2d2065fb4520fa3f3f2bcf61cff26ec8b7eba4b5`
- Yuan1z0825/nature-skills: `a1a8220366e82ecd8584ea3d7f46cb3969f4b018`
- Imbad0202/academic-research-skills: `06a2e6bd9743b68bb0ef2c5d161cf70abc00323e`
- zLanqing/codex-claude-academic-skills: `7ed6377f0efb6a38951b48ef03b19d996e454b1f`
- leo-lilinxiao/codex-autoresearch: `0f54c571707487f59486ba7c50d405edfc746c19`
- sanipedro679-gif/thesis-delivery-zh: `b851a7a0e3400d2cb95366c6a0e02e35e821c734`
- Norman-bury/research-writing-skill: `6f7959554b4614d879d79cb4ece9ed04a7c8a88c`
- O0000-code/paper-deck-reveal: `7a3e807e8e31f7f385abe9c59f8fbd19dfca93a4`

## 给 RWT 的取舍

1. 保留 RWT 的项目登记、检查点、证据状态和恢复机制作为统一主线，避免引入多个并行总控技能。
2. 真正有补充性的优先项是文献检索适配、中文 DOCX/学校模板交付、PPTX 演示与社科方法分支；先选一个实际任务验证，再决定是否引入独立模块。
3. 外链资源指南可以直接收录上述来源并标明用途。任何实际代码/提示词移植都应锁定提交、核对逐文件许可与依赖、保留归属、修改记录，并在同一 RWT 登记/恢复接口下验收。
4. README 图文与多语言呈现可以独立完成，不应把“参考了项目主页样式”写成“已经集成这些技能”或能力排名。

## 文献筛选如何接入 RWT

[Bennu 文献筛选实例](literature-screening/README.md)采用文献综述技能中记录筛选理由的做法，接入 RWT 已有的证据登记与检查点。研究者在英文筛选表里填写检索范围、读到的位置和选择理由，配套脚本生成 `register-batch` 可读的数据。案例把任务团队的原始图像报告登记为一条证据，把重复介绍同一观测的新闻稿记为排除，并将尚待对照样本的后续研究留给下次会话。实现和案例均为 RWT 原创，脚本随源码提供。

## 主页呈现参考

[REA 原仓库](https://github.com/morluto/rea)采用多语言入口、首屏图片、快速开始和案例展示；[PaperSpine5](https://github.com/WUBING2023/PaperSpine)采用产品封面和语言导航。本轮参考这些信息组织方式，RWT 的封面与流程图独立制作，案例图来自 RWT 已有公开企鹅数据分析。没有复制这些项目的商标、截图或技能实现。

[英文互动星图](https://cheshirecat-d.github.io/research-workflow-template/)让访客选择九个科研技能，并查看上述小行星文献实例与企鹅数据分析。

[返回中文主页](i18n/README.zh-CN.md) · [English overview](../README.md)
