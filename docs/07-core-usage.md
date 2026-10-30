# 核心用法

本页说明当前元数据与恢复接口。需要让宿主执行科研技能时，另按 [技能与方法接入](08-skills-and-methods.md) 显式接入项目；本页的示例演示登记与恢复，不认证研究结论。

本页示例从模板仓库根目录运行，因此显式给出 `--root`。项目命令省略该参数时只使用当前目录，不向上查找，也不自动初始化；在研究项目根目录可使用项目内的 `.agents/skills/_rw-runtime/tools/research.py`。需要 Python 3.11+，仅依赖标准库；本地项目支持 Windows、macOS 和 Linux。macOS/Linux 使用 POSIX 目录句柄与 `fcntl` 写锁，Windows 使用原生文件句柄与非阻塞范围锁。当前实际测试平台以验证记录为准。命令中的新项目路径可更换，不需要个人目录、数据库账户或模型密钥。

## 能做什么

| 命令 | 作用 | 是否写入项目 |
|---|---|---|
| `options` | 查看稳定ID、指导范围与显式任务变体记录摘要 | 否 |
| `init` | 创建全新项目；已存在的目标不覆盖 | 是 |
| `register` | 登记一个 JSON 对象；可同时保存下一步并返回恢复摘要 | 是 |
| `register-batch` | 顺序校验记录数组；可在同一写锁内连同检查点一次提交 | 是 |
| `show` | 查看记录；`--edit KIND:ID ...` 一次导出带版本的可编辑批次 | 否 |
| `configure` | 更新支持的项目配置字段；相同配置幂等返回 | 仅有变更时 |
| `check` / `status` | 读取登记、活动依赖和本地文件一致性 | 否 |
| `checkpoint` | 仅保存当前断点；`--report` 同时返回恢复摘要 | 是 |
| `resume` | 重新检查并显示恢复摘要 | 否 |

默认输出 JSON；只有 `resume --format markdown` 输出便于阅读的摘要。退出码 `0` 表示本次命令范围内成功，`1` 表示检查发现，`2` 表示输入、接口、路径、写入占用或 I/O 等错误。组合保存和 `checkpoint --report` 可在成功写入后因恢复检查仍有发现而返回 1；必须同时看 `registered` / `checkpoint_saved` 和 `recovery`，不能把退出 1 当作“未保存”而盲目重试。提交前校验失败不会写回；写入后的 I/O 异常可能发生在文件替换后，先用只读恢复确认当前状态，不承诺所有 I/O 失败均回滚。若返回 `project_busy`，先等待当前写者结束，再显式重试；命令不会隐藏地循环重试。解析检查时同时查看 `scope`、`errors`、`warnings` 和 `scientific_validity`。`scientific_validity: not-assessed` 不会因为登记检查通过而变为“有效”。

`show`、`check`、`status`、`resume` 不创建锁、不更新文件、不自动修复记录。保存检查报告时将输出重定向至项目外，例如 `check --root ../my-research > ../my-research-check.json`；重定向本身是调用者写文件，不属于只读命令内部行为。

单条和批量登记均可用 `--file -` 从标准输入读取 JSON，例如 `python3 tools/research.py register --root ../demo-formal --kind statement --file - < examples/synthetic/math-statement.json`。文件和标准输入共用严格 UTF-8 JSON 校验及 8 MiB **字节**上限，拒绝重复键、NaN／Infinity及非法编码。输入只是数据，不会被当作命令执行。

`options` 不需要项目。每个方法的 `implementation.variant_evidence` 区分 `guidance_declared`（画像声明）、`explicit_case_bindings`（记录中显式填写变体的任务）、`method_only_cases`（只记录方法的任务）和 `unavailable_cases`（记录缺失或不可读）。有显式记录不等于整个变体已验证；没有变体字段也不等于该工作没有执行。摘要仅查看登记，内容支持与审阅范围另查相应任务证据。复制到研究项目的运行时不携带 `evals/`，其摘要为 `not-included-in-project-runtime`；任务材料位于源码仓库或 GitHub 的 `Source code` 源码归档，需要按原任务记录核对。

## 日常只需恢复一次、保存一次

在已接入技能的研究项目根目录开始一轮工作：

```sh
python3 .agents/skills/_rw-runtime/tools/research.py resume --format markdown
```

这一次只读检查已包含配置、下一步、文件变化、检查点及过期活动，无须连跑 `status`、`check`、`show`。需要修改已有记录时才导出本轮实际要改的记录，真实复核后编辑，再一次保存：

```sh
python3 .agents/skills/_rw-runtime/tools/research.py show --edit evidence:E1 activity:A1 > ../reviewed-batch.json
# 复核输入和活动，按真实结果编辑 reviewed-batch.json；保留 expected_version。
python3 .agents/skills/_rw-runtime/tools/research.py register-batch --file ../reviewed-batch.json --next-action "继续已复核范围内的下一项工作" --activity A1
```

`E1` / `A1` 换成已有记录。导出数组直接携带类型、记录、替换标志和固定版本，不必先查一遍版本；下游依赖多时也在同一次导出中明确列出，并按上游到下游顺序提交。新记录直接写有序批次即可；单条 `register` 也支持相同的下一步参数。没有记录变化、只保存断点时使用 `checkpoint --next-action "下一步" --report`。这些保存命令返回 `recovery`，无须再补一次 `resume`。

## 接入已有文件夹

已有材料目录不直接初始化为 RWT 项目。先在它旁边创建新项目并接入技能，保留原件，只复制当前要使用的普通材料，确认目标路径不存在。明确后续在哪份工作副本继续修改；否则原目录更新、项目内副本不变时，检查只能报告副本未变。`init` 拒绝覆盖已有目录，不会替你迁移或同步文件。

本地材料使用项目相对路径；不能使用 `..`、绝对材料路径或链接。不能复制或必须在外部更新的材料，用 `external`／`controlled` 保存定位和访问说明，原件变化不会被本地检查检测。[用户指南的完整接入示例](user-package-guide.md)演示把实际文件登记为来源、本地证据和活动；不增加第二套材料台账。

`source.locator` 只保存来源身份。需要绑定本地文件时，另登记 `evidence.location={"kind":"local","path":"notes/data.csv"}`，用 `source_ids` 连接来源，再将该证据放进实际活动的 `inputs`。`artifact.path` 同样绑定本地产物。`file_tracking.local_files` 和 `local_file_count` 显示绑定路径；`source_ids_without_local_evidence` 是没有本地证据关联的来源 ID，不是过期或未读的判断。程序不猜测 locator、不读取外部或受控原件，也不会把覆盖摘要当成错误。

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
python3 tools/research.py register --root ../demo-formal --kind activity --file examples/synthetic/math-activity.json --activity A1 --next-action "登记已知反例 n=40 并修订原候选；若另拟较窄命题则重新列出证明义务" --note "整理已完成；候选命题未证明。"
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
python3 tools/research.py register-batch --root ../demo-history --file examples/synthetic/history-records.json --activity HA1 --next-action "比较两种解释各自仍需的上下文与时间顺序材料" --note "两条解释并存，未判定唯一原因。"
```

检查器验证记录与引用，不能判断史料是否可靠、解释是否充分或因果是否成立。该样例不表示已完成历史研究适配器或学科专家复核。

批次沿用单条登记的版本、依赖和本地文件规则，每项各增加一次 registry revision 和历史条目。给出 `--next-action` 时，同一写锁内顺序校验批次、保存检查点并计算恢复摘要，最后原子替换一次 `records/registry.json`；新增检查点另有一次 revision 和历史条目。任一提交前校验失败（包括检查点的 activity 不存在或下一步空白），整个候选登记均不写回，不留下前半段登记。`--activity` / `--note` 不能脱离 `--next-action` 单独使用。批次不接受空数组、未知选项或以字符串代替布尔值的 `replace`。同一批次中，按实际版本顺序替换同一 ID 也必须逐项提供准确版本。不带下一步时保持仅登记的原有行为。

## 法学：法域、时点与法源台账

从完整工具包根运行：

```sh
python3 tools/research.py init --output ../demo-law --title '有时点边界的法律解释问题' --discipline law --method legal-analysis --connect-skills
```

再使用[法学项目模板](../profiles/templates/legal-research.md)和[source样例](../profiles/templates/legal-source.json)，按实际材料记录法域、相关事实时点、公布／施行／修废与过渡、效力地位依据、裁判理由及后续检索范围。示例的 `not-read`、`null` 和未知状态应在实际核对后才显式更新。`source.extensions.legal` 可保存这些元数据，CLI只验证通用结构并原样保存，不判断法律含义。具体条款、段落或页码与实际访问程度一起保留。

`legal-analysis` 的变体 `doctrinal`、`case-analysis`、`comparative-law` 用在具体 method-binding 中。法律解释可登记为 `interpretive` 主张；规范建议与经验效果按实际性质分别登记。画像版本字符串不是自动新旧判断；若需检测正文或指导变化，把实际使用的本地文件登记为 evidence 并作为活动输入，恢复时再复核漂移，而不自动改写法律结论。两项实际离线合成任务见[法学素材](../evals/legal/README.md)。

## 更新记录与输入变更

每次 `register` 都登记单个对象；类型与最小字段见 [正式模式目录](../core/schemas/)。常用引用写为 `statement:S1`、`evidence:E1`、`activity:A1`，包含类型以区分重名 ID。关系引用、活动输入输出及依赖必须能在当前登记中解析，因此先登记被引用对象。活动的 `depends_on` 只填活动 ID；方法绑定的 `applies_to` 使用带类型引用。

重复 ID 默认拒绝。修改时优先用 `show --edit evidence:E1 activity:A1` 一次导出所选记录。返回值是可直接交给 `register-batch` 的数组，每项携带 `kind`、`record`、`replace:true` 和导出时的 `expected_version`。它不与 `--kind`、`--id` 或 `--data-only` 混用。只选择本轮实际要复核的记录，避免无意义地替换其他 ID。

`expected_version` 是**该记录版本**，不是整个登记的 `revision`；编辑时保留它。导出后若别人更新同一记录，保存会拒绝旧版本；应重新读取、比较并合并真实修改，不能自动换成最新版本号来覆盖。单条旧接口仍可用 `register --replace --expected-version N`；普通 `show --kind KIND --id ID` 返回完整 `envelope`，`--data-only` 仅导出其中的 `data` 对象。仅给 `--kind` 列出该类 ID／版本，两个参数均省略则按八类汇总；`--id` 必须搭配 `--kind`。不存在记录返回退出 2、错误码 `missing_reference`。不要把整个查询响应或 envelope 回灌 `register`，也不要直接改写登记簿。

本地文件发生变化或记录被替换时，检查会比较指纹，并把受影响活动及其依赖后续列为过期。恢复仍展示已保存的下一步，同时要求先审阅变化。先查明输入为何变化，真实复核并更新证据，再按上游到下游顺序重做必要活动；已经重做完成才可再次标为 `done`，尚未重做使用 `pending` / `in-progress`，失败用 `failed`，跳过则在 `note` 中说明。不能照抄导出物中的旧 `done` 冒充完成复核。

下面导出数学教程中的两条记录。POSIX shell 可用重定向；PowerShell 编码安全的方式见[用户指南](user-package-guide.md)。导出与编辑本身都不完成复核：

```sh
python3 tools/research.py show --root ../demo-formal --edit evidence:E1 activity:A1 > ../reviewed-batch.json
# 实际复核后编辑记录，保留 expected_version；证据排在使用它的活动之前。
python3 tools/research.py register-batch --root ../demo-formal --file ../reviewed-batch.json --activity A1 --next-action "继续已复核范围内的下一项工作"
```

一批中的活动声明也必须符合实际完成情况。返回的 `recovery` 若仍有过期状态，按其原因继续复核；已保存的记录不应重复提交。仅更新检查点只承认当时基线，不执行活动、重绑旧证据或使过期活动自动有效；需要单独保存下一步时用 `checkpoint --next-action TEXT --report`，省略 `--report` 保留原来的简短返回结构。`resume` 从持久记录恢复上下文，不从旧聊天猜测执行状态，也没有定时或后台继续功能。

`resume --format markdown` 使用同一次只读检查的快照，列出项目配置、文件绑定覆盖、registry revision、检查点状态（`current`／`stale`／`not-recorded`）、具体 findings 及关联路径／记录。过期或进行中的活动同时显示 ID、标题和过期原因。存在漂移时仍返回退出码 1，不会把已保存的下一步当成当前可直接执行的决定。JSON 的 `configuration` 保留实际启动约束，`file_tracking` 是覆盖摘要；两者与已有记录共用同一次检查，不写回项目。

## 初始化后调整项目配置

学科、方法及交付要求逐渐明确后，可以显式更新受支持字段，无需手工改 `project.json`：

```sh
python3 tools/research.py configure --root ../demo-history --add-discipline social-sciences --add-method qualitative --mode structured --venue "待核对作者指南的目标期刊" --governance-applicability applicable --add-governance-requirement "访问受限材料前核对授权"
python3 tools/research.py configure --root ../demo-history --interest "比较已取得材料中的竞争解释" --deadline "四周内" --budget "使用现有材料，无新增支出" --add-capability "已有可读材料与本地分析环境"
```

`--interest` 更新当前兴趣，`--deadline`、`--budget` 保存期限和预算，`--venue` 保存目标期刊。可重复使用 `--add-discipline`、`--add-method`、`--add-capability` 和 `--add-governance-requirement`；已有值不会重复加入。未知项可以省略，不要求先填满配置。已有知识、文献和材料的细节继续保留在实际笔记或来源记录中，`available_capabilities` 只保存可用资源的简短说明。

`--mode` 支持 `light`／`structured`／`reproducible`，治理适用性支持 `unknown`／`applicable`／`not-applicable`。未知目录 ID、空白必填值或违反现有引用的配置被拒绝。项目 ID、登记内容、活动状态和检查点不会被配置命令重写。

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

运行配置由 `init` 生成，遵守 [project.schema.json](../core/schemas/project.schema.json)；当前 CLI 没有 `--config` 导入参数，不要用设计示意覆盖项目配置。移动整个研究项目后，相对材料路径保持可用；外部或受控证据仍需按其原有权限另行访问。
