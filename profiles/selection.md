# 从专业与问题选择入口

专业名称帮助定位语境，具体问题、主张与证据决定方法。下表是现有七类学科与十类方法的选择示例，不新增专业 ID，也不认证某专业已完整实现或验证。稳定 ID 见 [目录](../design/catalog.json)，持续登记见 [接入协议](../core/skill-bridge.md)。

| 专业中的问题 | 可选入口与方法 | 选择时保留的范围 |
|---|---|---|
| 教育：学习成效、课堂经验或教育政策 | `social-sciences`；按问题选 `empirical-quantitative` 或 `qualitative`，制度价值问题另选 `conceptual-normative` | 分清学校、班级、学生与重复观测的层级；现有社会科学任务不等于教育领域专门验证 |
| 经济与管理：形式模型、政策效果或组织实践 | `social-sciences`；效果研究选 `empirical-quantitative`，组织材料可选 `qualitative`；实际模型推导或计算再选 `formal-theory`、`computational` | 模型结论、经验效果与制度建议分别论证；不能由一个政策示例推定所有经管问题已测 |
| 心理：行为测量、体验或干预研究 | 通常从 `social-sciences` 进入；按设计选 `empirical-quantitative`、`measurement-experiment` 或 `qualitative`；确有健康研究语境时再考虑 `medicine-health` | 区分量表得分、拟解释的概念与临床判断；目前没有心理专业专项任务，不能由通用测量指导认证量表或干预 |
| 哲学与思想史：概念、规范理由或文本解释 | `humanities`；按主张选 `conceptual-normative` 或 `historical-interpretive` | 经验前提、价值理由和历史解释分别提供依据；一个规范论证任务不代表所有哲学传统已测 |
| 艺术：作品解释、文化语境或创作实践 | `humanities`；作品材料可按问题选 `historical-interpretive`，参与者材料可选 `qualitative` | 艺术阐释尚未完整验证；创作实践没有专用方法画像或专项任务，先明确作品、过程记录、反思和评价依据，不直接套用工程阈值验收 |

专业未在表中出现时，从研究对象与现有材料找到最接近的入口。允许组合方法，但只加载当前主张所需的资源；不要为填满目录而把整个项目绑上全部方法。无法匹配的研究传统或交付形式应保留为需要项目化说明的方法缺口，不能仅换一个标签宣称已经覆盖。

`catalog.json` 中的 `supported_variants` 是画像声明的指导范围。`options` 的 `implementation.variant_evidence` 另列记录中的显式变体绑定与仅有方法级记录、未注明变体的任务。该摘要不重新核对内容审阅；具体结论和范围仍查任务审阅记录。未注明变体不等于未开展该工作，也不能据任务名自动补绑；列出一项任务不认证整个专业或变体。

项目内运行副本携带本导航与画像，不携带完整 `evals/`。其证据摘要应明确标为未包含；需要追查任务时回到完整发行包，不能把缺少材料当成已经核实，也不能把完整包的证据位置误当项目内文件。
