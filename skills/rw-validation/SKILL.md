---
name: rw-validation
description: Validate research arguments, designs and evidence with the applicable method. Use for 数学证明、计算实验、医学与田间设计、量化实证、定性与规范论证、法源与判例分析、证据综合 or 最小验证; registration integrity alone uses the core check command.
---

# 方法验证

先读 [接入协议](../../core/skill-bridge.md) 与 [核心协议](../../core/protocol.md)。从具体主张和证据义务选择方法；学科或期刊名称本身不决定检查。

按任务只加载所需画像：

| 研究工作 | 方法画像及当前范围 |
|---|---|
| 命题、引理、证明或推导 | [形式与理论](../../profiles/methods/formal-theory.md)：证明义务与手工论证；形式化工具按实际使用另报 |
| 数值或算法实验 | [计算研究](../../profiles/methods/computational.md)：可复查输入、实验与结果；不覆盖全部计算子领域 |
| 实验、观测、田间或动物测量 | [测量与实验](../../profiles/methods/measurement-experiment.md)：分配／抽样单位、测量、对照与执行偏差 |
| 系统、设备或软件设计 | [工程设计](../../profiles/methods/engineering-design.md)：需求、设计取舍与实际使用证据 |
| 描述、调查、观察、因果、随机干预或预测 | [量化实证](../../profiles/methods/empirical-quantitative.md)：按设计检查目标量、数据、分析与外推 |
| 访谈、民族志、案例或参与式材料 | [定性研究](../../profiles/methods/qualitative.md)：语境、反身性、材料到解释及反向案例 |
| 档案、文本与竞争解释 | [历史与阐释](../../profiles/methods/historical-interpretive.md)：材料定位、语境与解释支持；不代表全部人文方法 |
| 概念重构、价值前提或规范建议 | [概念与规范论证](../../profiles/methods/conceptual-normative.md)：定义、前提链、反例与有力异议 |
| 法律解释、裁判或比较法研究 | [法律解释与法源分析](../../profiles/methods/legal-analysis.md)：法域、相关时点、效力依据、裁判地位和精确引证 |
| 系统／范围／叙述／解释性综述 | [证据与文献综合](../../profiles/methods/evidence-synthesis.md)：覆盖范围、研究去重、偏倚与合成依据 |

各类方法均有指导画像，具体变体的实际测试覆盖以核验记录为准，不能将目录完整称为全部学科已验证。学科语境按需读 [画像目录](../../profiles/disciplines/)；涉及招募、干预、受限资料或外发等实际动作时查 [治理](../../profiles/governance.md)。混合研究分别检验各部分，再检查连接结论是否跨越了依据范围。

## 执行与结果

写清本次待查结论、所用材料、必要条件和结果判据。先做能暴露关键错误或区分方案的检查；不要用大量弱检查代替证明义务或研究设计。

在任务授权与实际工具能力内执行。保留输入身份、实际命令或推导步骤、产物及失败信息。没有执行的部分标为计划或未检查；程序无输出、超时或工具缺失都不能填成通过。

给出与依据相称的结论：有效范围内的证明、反例、局部计算结果、混合材料支持或尚缺论证均可成为有用产物。把实际发现交给 `rw-writing` 表达、`rw-review` 审查；不从 CLI 退出码推导科学有效性。

持续项目将材料、验证产物、主张关系及活动登记。若需要更新 statement 的 assessment，明确本次评估者、范围、理由及仍存限制；使用形式化状态时只记录实际工具完成的范围。当前核心不会代替这些实质判断。

## 返修后的估计值对照

已实际复算且有两版结果 CSV 时，运行[结果对照工具](scripts/compare_results.py)。例如在已接入的项目根目录执行：

```sh
python3 .agents/skills/rw-validation/scripts/compare_results.py history/estimates.csv results/estimates.csv
```

默认读取 `estimate_id,value,unit,scope`，可选 `artifact` 列记录关联图表。标识应随估计量跨版保留；“主结果”这样的展示顺序或角色在返修时可能变化。口径列应覆盖人群、时间范围、加权方法及与该估计有关的定义。原表列名不同时可指定 `--id-column`、`--value-column`、`--unit-column` 和一个或多个 `--scope-column`。两表单位由数据说明固定时可用 `--unit ppb`。使用计算结果保留的精度；只有舍入后的表时，对照只到表中精度。

旧版和新版使用不同的列名或行结构时，可从各自原表投影为两张规范表。根据原始方法说明明确两侧行键、取值列、单位和范围，保存来源指纹和未纳入的行。报告“新增”时说明依据的是所给表格还是同时包括旧正文。工具包的 `examples/ozone-revision/adapt_legacy.py` 演示了如何排除单组均值，只对照跨组差值。

报告附两表的 SHA-256、前后值、口径、关联图表及比较状态。空值、`NA`、`N/A` 属于缺测；单位、口径变化或缺失值会列出原因。用 `--format json` 可交给后续审查。成功比较（包括发现变化）退出 0，重复或缺少标识、格式错误等输入问题退出 2。结合实质解释和敏感性分析写明哪些原结论保留、修订或仍有疑问，再按需把对照报告登记为返修证据。
