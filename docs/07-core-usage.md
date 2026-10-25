# 核心用法

本页说明当前元数据与恢复接口。需要让宿主执行科研技能时，另按 [技能与方法接入](08-skills-and-methods.md) 显式接入项目；本页的示例演示登记与恢复，不认证研究结论。

本页从模板仓库根目录运行命令。需要 Python 3.11+，仅依赖标准库；写入锁使用 `fcntl`，平台目标为 macOS/Linux。当前实际测试平台以验证记录为准。命令中的新项目路径可更换，不需要个人目录、数据库账户或模型密钥。

## 能做什么

| 命令 | 作用 | 是否写入项目 |
|---|---|---|
| `options` | 查看稳定ID、指导范围与显式任务变体记录摘要 | 否 |
| `init` | 创建全新项目；已存在的目标不覆盖 | 是 |
| `register` | 登记一个 JSON 对象，检查字段、引用和本地路径 | 是 |
| `register-batch` | 顺序校验一个记录数组，在一次写锁内整体登记；任一项失败不提交 | 是 |
| `show` | 查看完整记录 envelope 或 ID／版本摘要 | 否 |
| `configure` | 更新支持的项目配置字段；相同配置幂等返回 | 仅有变更时 |
| `check` / `status` | 读取登记、活动依赖和本地文件一致性 | 否 |
| `checkpoint` | 记录当前指纹及下一步文字 | 是 |
| `resume` | 重新检查并显示恢复摘要 | 否 |

默认输出 JSON；只有 `resume --format markdown` 输出便于阅读的摘要。退出码 `0` 表示本次命令范围内成功，`1` 表示记录或文件变更等检查发现，`2` 表示输入、接口、路径或写入占用等错误。若返回 `project_busy`，先等待当前写者结束，再显式重试；命令不会隐藏地循环重试。解析结果时同时查看 `scope`、`errors`、`warnings` 和 `scientific_validity`。`scientific_validity: not-assessed` 不会因为登记检查通过而变为“有效”。

`show`、`check`、`status`、`resume` 不创建锁、不更新文件、不自动修复记录。保存检查报告时将输出重定向至项目外，例如 `check --root ../my-research > ../my-research-check.json`；重定向本身是调用者写文件，不属于只读命令内部行为。

单条和批量登记均可用 `--file -` 从标准输入读取 JSON，例如 `python3 tools/research.py register --root ../demo-formal --kind statement --file - < examples/synthetic/math-statement.json`。文件和标准输入共用严格 UTF-8 JSON 校验及 8 MiB **字节**上限，拒绝重复键、NaN／Infinity及非法编码。输入只是数据，不会被当作命令执行。

`options` 不需要项目。每个方法的 `implementation.variant_evidence` 区分 `guidance_declared`（画像声明）、`explicit_case_bindings`（记录中显式填写变体的任务）、`method_only_cases`（只记录方法的任务）和 `unavailable_cases`（记录缺失或不可读）。有显式记录不等于整个变体已验证；没有变体字段也不等于该工作没有执行。摘要仅查看登记，内容支持与审阅范围另查相应任务证据。复制到研究项目的运行时不携带 `evals/`，其摘要为 `not-included-in-project-runtime`，不能借用完整发行包的记录假装已在项目内核对。

## 数学候选命题：从零到恢复

这是接口教程，材料为新写的有限观察。候选命题为“所有非负整数 n 均使 n²+n+41 为素数”，当前材料只列出五个值。这个教学候选实际上有已知反例：`n=40` 时得到 `1681=41²`。下面刻意保存初始有限观察阶段的未评估登记，用来展示“材料登记通过”不能替代数学检查；它不是实际开放问题或创新结果。真实研究应登记反例并修订原主张。

先创建一个**不存在**的目录，再把材料复制到项目相对路径。不要将模板仓库本身作为研究项目根目录。

```sh
python3 tools/research.py init --output ../demo-formal --title "有限观察与候选命题" --interest "区分算例与全称命题" --discipline natural-sciences --method formal-theory --mode light
mkdir ../demo-formal/notes
cp examples/synthetic/finite-observations.txt ../demo-formal/notes/finite-observations.txt
python3 tools/research.py register --root ../demo-formal --kind statement --file examples/synthetic/math-statement.json
python3 tools/research.py register --root ../demo-formal --kind evidence --file examples/synthetic/math-evidence.json
python3 tools/research.py register --root ../demo-formal --kind relation --file examples/synthetic/math-relation.json
python3 tools/research.py register --root ../demo-formal --kind activity --file examples/synthetic/math-activity.json
python3 tools/research.py check --root ../demo-formal
python3 tools/research.py checkpoint --root ../demo-formal --activity A1 --next-action "登记已知反例 n=40 并修订原候选；若另拟较窄命题则重新列出证明义务" --note "整理已完成；候选命题未证明。"
python3 tools/research.py resume --root ../demo-formal --format markdown
```

`statement` 保存候选表述，`evidence` 保存实际材料，`relation` 说明两者的有界关系，`activity` 记录整理工作的进度。示例 `A1` 的 `done` 只指整理完成；`S1` 的证据评估仍是 `not-assessed`。登记 `formal-theory` 只是记录方法选择，核心不会因此运行证明器；证明工作由宿主依据相应技能与画像开展。

`location.path` 相对于研究项目根目录，不能使用 `..`、绝对路径或符号链接。登记本地证据时记录文件指纹；后续检查可发现其内容改变。核心只为最大 256 MiB 的普通本地文件计算完整指纹，不截断大文件冒充校验。超出范围或受限材料应使用 `controlled` / `external` 定位并说明未核验的内容；这些定位不会被读取或联网访问。

## 史料解释：保留两条竞争路线

[fictional-excerpts.txt](../examples/synthetic/fictional-excerpts.txt) 是完全虚构、为本模板新写的可共享材料，不含真实档案或个人资料。两个节录分别提及经费与轮值组织，允许并列登记两种解释；支持关系数量不决定唯一原因。

为减少样例小文件，[history-records.json](../examples/synthetic/history-records.json) 收集了来源、两个主张、证据、两个关系和一个整理活动。使用原生 `register-batch` 顺序导入这个数组；各项使用 `{"kind": "类型", "record": {记录对象}}`，替换时另加 `"replace": true` 和该记录的 `"expected_version"`。被引用项必须在此前已有或位于批次前面。

```sh
python3 tools/research.py init --output ../demo-history --title "虚构材料的竞争解释" --discipline humanities --method historical-interpretive --mode structured
mkdir ../demo-history/notes
cp examples/synthetic/fictional-excerpts.txt ../demo-history/notes/fictional-excerpts.txt
python3 tools/research.py register-batch --root ../demo-history --file examples/synthetic/history-records.json
python3 tools/research.py checkpoint --root ../demo-history --activity HA1 --next-action "比较两种解释各自仍需的上下文与时间顺序材料" --note "两条解释并存，未判定唯一原因。"
python3 tools/research.py resume --root ../demo-history
python3 tools/research.py check --root ../demo-history
```

检查器验证记录与引用，不能判断史料是否可靠、解释是否充分或因果是否成立。该样例不表示已完成历史研究适配器或学科专家复核。

批次沿用单条登记的版本、依赖和本地文件规则，每项各增加一次 registry revision 和历史条目，但只在全部校验成功后原子替换一次 `records/registry.json`。任何一项失败均不写回整个候选登记；不会留下只导入前半段的主张。批次不接受空数组、未知选项或以字符串代替布尔值的 `replace`。同一批次中，按实际版本顺序替换同一 ID 也必须逐项提供准确版本。

## 法学：法域、时点与法源台账

从完整工具包根运行：

```sh
python3 tools/research.py init --output ../demo-law --title '有时点边界的法律解释问题' --discipline law --method legal-analysis
python3 tools/connect_skills.py install --root ../demo-law
python3 tools/connect_skills.py check --root ../demo-law
```

再使用[法学项目模板](../profiles/templates/legal-research.md)和[source样例](../profiles/templates/legal-source.json)，按实际材料记录法域、相关事实时点、公布／施行／修废与过渡、效力地位依据、裁判理由及后续检索范围。示例的 `not-read`、`null` 和未知状态应在实际核对后才显式更新。`source.extensions.legal` 可保存这些元数据，CLI只验证通用结构并原样保存，不判断法律含义。具体条款、段落或页码与实际访问程度一起保留。

`legal-analysis` 的变体 `doctrinal`、`case-analysis`、`comparative-law` 用在具体 method-binding 中。法律解释可登记为 `interpretive` 主张；规范建议与经验效果按实际性质分别登记。画像版本字符串不是自动新旧判断；若需检测正文或指导变化，把实际使用的本地文件登记为 evidence 并作为活动输入，恢复时再复核漂移，而不自动改写法律结论。两项实际离线合成任务见[法学素材](../evals/legal/README.md)。

## 更新记录与输入变更

每次 `register` 都登记单个对象；类型与最小字段见 [正式模式目录](../core/schemas/)。常用引用写为 `statement:S1`、`evidence:E1`、`activity:A1`，包含类型以区分重名 ID。关系引用、活动输入输出及依赖必须能在当前登记中解析，因此先登记被引用对象。活动的 `depends_on` 只填活动 ID；方法绑定的 `applies_to` 使用带类型引用。

重复 ID 默认拒绝。修改前先用 `show --kind 类型 --id ID` 查看完整 `envelope`，其中包含 `version`、`registered_at`、`bindings` 和 `data`；不存在的记录返回退出码 2、错误码 `missing_reference`。仅给 `--kind` 时返回该类的 ID／当前版本列表，两个参数均省略则按八类汇总；`--id` 必须搭配 `--kind`。

新的输入 JSON 保留相同 ID，再同时传 `--replace --expected-version N`。`N` 是**该记录版本**，不是整个登记的 `revision`；版本不匹配会拒绝写入，原版本保留在历史中。`register` 只接收 `envelope.data` 对应的记录对象，不接收整个 `show` 响应或 envelope。不要直接改写 `records/registry.json`。

本地文件发生变化或记录被替换时，检查会比较指纹，并把受影响活动及其依赖后续列为过期。声明的 `done` 不会被静默改写为新的科学结论。`resume` 仍展示已保存的下一步，同时要求先审阅变化。如果本地证据是有意更改的，先用原证据对象和显式版本替换重新登记新指纹；再按依赖顺序复核活动，上游先于下游。完成审阅后，按实际情况重新登记活动：已经重做的工作才可再次标为 `done`，尚未重做则使用 `pending` / `in-progress`，失败则使用 `failed`，跳过则在 `note` 中说明理由。最后再保存新的检查点。

新的 `checkpoint` 只承认当时的记录和文件基线，不执行活动，也不能把过期活动自动恢复为有效。不要通过不断覆盖检查点来替代复核输入。`resume` 是从持久记录恢复上下文，不是从旧聊天推测执行状态，也没有定时或后台继续功能。

下面用原生只读查询查看数学教程的 `E1` / `A1` 及各自版本。后面的复制命令仅为**刚完成上述教程**的项目准备编辑起点；真实项目应从查询结果的 `envelope.data` 保存当前记录对象。更新输入放在项目外，查询和复制本身都不完成材料复核。

```sh
python3 tools/research.py show --root ../demo-formal --kind evidence --id E1
python3 tools/research.py show --root ../demo-formal --kind activity --id A1
python3 tools/research.py show --root ../demo-formal --kind activity
cp examples/synthetic/math-evidence.json ../E1-reviewed.json
cp examples/synthetic/math-activity.json ../A1-reviewed.json
```

若两条记录仍是刚完成教程时的版本 1，下面展示对应命令；若版本不同，使用刚才读出的实际值。先检查文件为何变化，并据实际情况编辑新证据对象。活动也需实际复核：已重做才能保留 `done`，否则改为真实进度或失败状态；不要把导出的旧状态当作复核完成。

```sh
python3 tools/research.py register --root ../demo-formal --kind evidence --file ../E1-reviewed.json --replace --expected-version 1
# 完成对受影响活动的实际复核，再执行下一条；多层依赖按上游到下游处理。
python3 tools/research.py register --root ../demo-formal --kind activity --file ../A1-reviewed.json --replace --expected-version 1
python3 tools/research.py checkpoint --root ../demo-formal --activity A1 --next-action "继续已复核范围内的下一项工作"
python3 tools/research.py resume --root ../demo-formal
```

证据更新后活动仍可能过期；活动更新后旧检查点仍可能过期。这些中间输出是正常且应保留的复核过程。

`resume --format markdown` 使用同一次只读检查的快照，列出 registry revision、检查点状态（`current`／`stale`／`not-recorded`）、具体 findings 及关联路径／记录。过期或进行中的活动同时显示 ID、标题和过期原因。存在漂移时仍返回退出码 1，不会把已保存的下一步当成当前可直接执行的决定。

## 初始化后调整项目配置

学科、方法及交付要求逐渐明确后，可以显式更新受支持字段，无需手工改 `project.json`：

```sh
python3 tools/research.py configure --root ../demo-history --add-discipline social-sciences --add-method qualitative --mode structured --venue "待核对作者指南的目标期刊" --governance-applicability applicable --add-governance-requirement "访问受限材料前核对授权"
```

可重复使用 `--add-discipline`、`--add-method` 和 `--add-governance-requirement`；已有值不会重复加入。`--mode` 支持 `light`／`structured`／`reproducible`，治理适用性支持 `unknown`／`applicable`／`not-applicable`。未知目录 ID、空白必填值或违反现有引用的配置被拒绝。项目 ID、登记内容、活动状态和检查点不会被配置命令重写。

真正变更在同一次项目写锁内重新读取和校验，并只原子写回 `project.json`；registry revision 仍仅计数登记和 checkpoint 写入。已有检查点因此通过配置指纹显示 `project-config` 过期，需人工审阅影响再保存新检查点。相同配置返回 `configured: false`，不改文件或补建缺失锁。填写期刊和治理要求只记录计划，`venue_compliance` 与 `governance_approval` 仍为 `not-assessed`。

## 项目里哪些是权威记录

```text
my-research/
├── project.json                 init 生成的配置
├── PROJECT.md                   人工笔记，不反向同步
├── records/registry.json         八类记录、版本历史、检查点、恢复游标
├── notes/                       相对路径材料与笔记
├── literature/                  可选来源材料
├── manuscript/                  可选稿件
├── artifacts/                   可选产物
└── .research/write.lock          写入时使用的操作系统锁
```

初始化创建元数据与锁目录；上图的材料、稿件和产物目录按需要创建。`light`、`structured`、`reproducible` 三种模式都会建立一个空登记文件，以保持单一权威与一致接口；`light` 不要求为了启动而填满任何表。模式与方法目前是配置，不会自动生成分析环境、运行实验或增强科学验证。

[design/project.example.json](../design/project.example.json) 保留为中性设计示意，**不是可直接覆盖的运行配置**。运行配置由 `init` 生成，遵守 [project.schema.json](../core/schemas/project.schema.json)；当前 CLI 没有 `--config` 导入参数。移动整个研究项目后，相对材料路径保持可用；外部或受控证据仍需按其原有权限另行访问。
