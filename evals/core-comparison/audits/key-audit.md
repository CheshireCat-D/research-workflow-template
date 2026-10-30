# 独立材料、答案和 CLI 可实现性审计

审计范围：`design/`、指定的五个当前 core 文件、目标用户 ZIP、前轮私有材料缓存，以及 `evals/real-comparison` 的来源/数值参考。未读取任何组的执行答卷或评分内容，未联网、访问个人 skills/memory、调用其他 agent、修改设计文件或启动正式对照。以下 CLI 操作全部针对独立发明的 toy 材料，不是 T/D 正式生命周期链，也没有给任何组科研分。

**最终追审结论：可冻结。原 F01/F02/F03/F04、P01 与 Q01 均已处理；未发现仍需阻断冻结的问题。数值答案与核心实现结论不变。此结论仅批准按已声明范围冻结方案，不代表已经执行正式对照、达到 OS 级隔离或获得科研/人类专家认证。**

审计工作目录：`KEY_AUDIT_WORK`。目标 ZIP SHA256 为 `1bf658b7895711bf786b3cf415a3c47dc2b214a31bace1d82e5b22ef00849ff2`；ZIP 内五个 core 文件与当前指定源码逐字节一致。审计使用 `EVAL_PYTHON -I -B`。

## 来源与独立数值证据

`numeric-audit.json` 的 83 项检查全部通过：包括全部 initial MANIFEST 条目、原始材料身份、实际命令退出码、预制 JSON/table 字节一致、两次 approved 参数与 B 事件的前后 SHA、完整输入指纹以及计算前后项目文件字节/mtime 保持。最终刷新又核验了设计者后来补充的文本；科学输入、参数和数值答案未变。

- T 的 PDF 与前轮缓存一致，SHA256 为 `eb3efd547349adfbff25514ae0854c142cd29b96b398be38c9000d69a2f64ca8`。缓存原文 p10 (14)、p28 Proposition 5 (51) 支持两侧 normal-mixture 公式。对标量 `l0=1`，独立以 70 位 Decimal 计算 `sqrt((v+rho)*ln((v+rho)/(alpha^2*rho)))`，与给定计算器的最大差为 `8.88e-16`，远小于键中 `1e-10` 容差。
- D 的 2011 CSV 与 data-a/data-b 两个缓存字节一致，共 8645 行；SHA256 为 `294d25e98ef1c9c9cec746e17ba3ff9818627ba5aa14baf1b93db7ae218de115`。冻结模型与数值参考文件逐字节一致，SHA256 为 `9642962f82483eded749138c58ead59c51e1aa2c8a7e99c2185ec33474f11025`。审计另用前 6442 个 Jan–Sep 观察小时的整数和/分组大小，独立核对 C0/C1 均值，全部一致；这只是只读来源核验，没有写回或重训模型。
- D 指标另以 Decimal 累计绝对误差、平方误差和有符号误差，最大差 `1.42e-14`；Q4 结果也与旧数值参考一致。原始数据的公开下载身份来自固定缓存及参考身份，未重新联网下载全文/数据。

|项目/范围|关键复算结果|
|---|---|
|T，rho=1，v=0,1,10,100|2.4477468306808166；3.6563948713638483；9.606401928868575；32.73018624234933|
|T，rho=4，同一 grid|4.895493661361633；5.57431973357386；10.070709270872976；31.015388968276124|
|D，Oct–Dec|2203 小时/92 日；C0 MAE 58.825190494512434；C1 MAE 44.570832407531775；相对降幅 24.2317244826%|
|D，Nov–Dec|1460 小时/61 日；C0 MAE 56.64127430990882；C1 MAE 41.252622564018566；相对降幅 27.1686185266%|

四次给定脚本的正常执行均退出 0；T 的 `alpha=1` 和 D 的起日晚于止日两次无效执行均退出 2，保留真实错误，无效输出目录未创建，源输入/模型/旧成果均不变。27.17% 与 24.23% 的差来自评价窗口变了，不能叫模型经重训变好。最终 D 作者修订文本和答案已正确加入该边界。

## 依赖、历史和实际接口证据

共同图可按现有 schema 映射：RAW/PARAM 用 local evidence；参数→CLAIM 用 `qualifies` relation；CHOICE 用 decision 并引用 PARAM；CODE/MODEL/RESULT/SUMMARY 用 artifact；CALC、SYNTH、SOURCE-CHECK 用 activity。参数、选择、原材料和代码进入 CALC；SYNTH 依赖 CALC；SOURCE-CHECK 不引用所改参数。无需新增引擎字段，也无需假造人类审阅。

`cli-retry/cli-probe.json` 记录实际 19 次 CLI 操作、14 项通过检查：

1. 实际目标 ZIP 初始化并安装项目内 runtime；14 个 toy 逻辑记录可用现有 `register-batch` 登记。
2. 只改已绑定参数后，CALC/SYNTH 均为 `stale`，SOURCE-CHECK 仍为 `done`。
3. 再实际保存 checkpoint：checkpoint 为 `current`，CALC/SYNTH 仍 `stale`，整体 `passed=false`。所以 C 的中间断点不洗白旧工作。
4. source-only 身份被列为无本地 evidence；scratch 不在跟踪路径。引擎没有宣称识别未知依赖、检查远端内容或覆盖全部项目文件。
5. 对受影响 evidence/claim/relation/decision/artifact/activity 作带版本的显式替换，按 CALC→SYNTH 更新后可恢复当前状态；旧记录实际内容保留在 history。**这不自动保留曾被覆盖的研究文件原字节。**
6. `check/status/resume/show` 实测不改任何文件字节、文件 mtime 或目录 mtime；迁移恢复也保持只读。
7. 原 toy 项目路径和原提取工具包路径消失后，实际运行迁移项目自己的 `.agents/skills/_rw-runtime/tools/research.py` 成功。此处没有建立 OS 级拒读公共缓存的沙箱；正式试验的强隔离仍需另行落实。
8. 旧版本写入得到 `version_conflict`；非法后项批次拒绝且 registry 字节不变。这些只列为独立机械特性证据，不加共同 100 分。

审计第一版 harness 误把 runtime 猜在 `PROJECT/_rw-runtime`，迁移/冲突调用发生找不到文件的退出 2，随后 harness 抛出 KeyError。错误及第一版脚本保存在 `cli-first-attempt-error.json` / `cli-probe-first-attempt.py`，首次输出未覆盖；新目录按实际 `.agents/skills/_rw-runtime` 路径重做成功。这是审计路径假设错误，不是产品迁移失败。

设计者新增的最终 A 请求已明确要求所有组留存 parameters/result/table/summary 的可恢复初始内容，并说明 SHA 不能恢复原字节、组织者不补档。这修复了最容易造成不公平的历史归档歧义；不能再按“核心自动归档旧科研文件”的假设评阅 C。

## 冻结前需修正或明确的地方

以下保留首次审计时的意见及论据；最终处理状态见末尾“冻结前追审”。首次完整稿另由组织者留存为 initial-key-audit，不用新意见覆盖旧发现。

### F01：标准成功链答案必须增加上游失败时的事实分支

T/D 键的 `B_checkpoint_freshness` 目前都直接写 stale，D 的最终状态/下一步也按 C 已完成复算修订来给。共同协议却明确保留各组真实失败、不由组织者补台账。若某组 A 没有实际留下 checkpoint，B 正确事实可能是 `not-recorded`；若 C 未完成复核，D 正确事实应是尚待复核和相应恢复动作。不能要求恢复者编造一个存在且 stale 的断点，或宣称尚未完成的新数值已经有效。

建议：键明确标为“上游成功时的标准答案”；另加通用条件规则：checkpoint 的存在/新旧、版本、活动完成和下一步必须以该组实际留下的状态为准。A/C 的缺项按预先规则扣分，B/D 是否如实恢复单独判定；不补状态，也不把如实报告缺口本身判错。若研究目标要对上游缺失产生链式损失，也应事先明确该计分口径。**这是评分冻结前的必要澄清，不是已发现任何正式组失败。**

### F02：部分得分和关键错误的计分锚点仍不足以机械复评

权重加总确为 A20+B35+C30+D15=100，各 item 的语义不依赖产品字段，基线可用 hash/version/recovery 脚本，额外有效依赖也已允许。当前 `Partial credit by actual substance` 尚未给 item 内部可复用的部分得分锚点；critical errors 仅另报，没有明确是否还会触发额外扣分/零分以及如何避免重复扣分。

建议：在看正式答卷前固定共同 codebook，给每个 item 的完整/部分/零分依据及跨阶段继承失败规则；“exact next action”按必要语义与当前条件判定，不按中文逐字匹配。未知依赖、未登记 scratch、未绑定 source-only 不得列为引擎本应自动检测的漏报。该规则对所有臂相同，不因哪组失败再改题。

### F03：事件注入把相同参数的合法 JSON 排版误当设置错误

独立 fixture 中把 T/D 的初始参数仅改为紧凑序列化及排序键，JSON 语义仍相同，但现有 `shared/inject_event.py` 两次均在 `Unexpected current parameter bytes` 处拒绝，没有注入事件。这会让合法采用其他 JSON 格式的组得不到相同干预。共同任务只要求真实身份/范围和原始来源字节保持，并未要求工作参数永远保持最初排版；没有必须按原 SHA 放行的科研理由。具体退出/前后字节见 `event-injection-audit.json`。

建议采用组织者提出的语义检查：先验证真实 regular file、拒绝任一路径分量的链接/逃逸；严格解析 JSON，确认整个对象的键与值等同初始参数；归档实际旧字节，记录实际 before SHA、与原排版的差异及通过依据；再统一写入相同 canonical after_json。语义已变、文件缺失、重复键、非法数值或链接时记录未投放事件和真实 setup 问题，不能悄悄恢复初始值。

这里不要只用默认 `json.loads(...) == initial`：Python 把 `true` 与 `1` 判相等，也会把足够接近的十进制字面量先舍入同一 float。独立示例已验证：严格的重复键拒绝、有限 Decimal 数字解析、布尔/数字类型区分可以同时接受 `1`/`1.0` 与键序/空白变化，拒绝 `true`/`1`、`1.0000000000000001`/`1`、重复键和 NaN。该比较规则应投放前冻结。

同步评分口径：允许排版变化时，A/C 结果里的 `input_sha256.parameters` 必须对应实际输入字节，不能硬要求等于参考答案的标准排版 SHA，也不能为通过而把真实哈希改写成参考哈希。科学数值按键的容差核对；原始 PDF/CSV、脚本和冻结模型仍要求字节不变。事件回执里的“仅改目标文件”应由真实前后快照支持，不能只依赖注入脚本自报。

### P01：执行投放仍未达到冻结状态

README 已诚实标明未冻结：每臂真实预算/环境、具体允许工具与指导及 SHA、顺序、阶段隔离、只读前后快照和工程探针适配均待组织者锁定。正式运行前只投放当阶段可见文件；A 不可看到 events/reference/stage-C 或未来探针答案，B/D 外部输出不能成为暗补状态。D 必须真正拒绝旧根/原 toolkit/公共缓存，且只读检查本身使用 `-I -B`。不能用本次 toy 可执行性检查代替上述执行隔离证据。

## 非阻断的小修建议

T 卡片可显式写“标量 `l0=1`，S 与 −S 对同一 V 满足相应 sub-Gaussian 控制”，使简化公式的必要条件直接可见。现有原文和公式计算在该范围下正确，不需要改数值。D 表虽未列 bias 两行，但 canonical result 已提供且正确；评阅不要因表格只呈部分指标而误称偏差未计算。

最终判断：材料足以进行后续冻结准备，数值无需修正；F01/F02/F03 与 P01 应在正式对照前写清并锁定。本审计没有证明产品提高科研正确率、节省人类工时或优于任何基线。

## 冻结前追审

本次只读取新增澄清和 `study_ops.py` 的相关实现；未读取任何正式阶段执行或评分，也未运行 freeze 或准备真实链。源函数通过 AST 提取到独立 AUDIT fixture 测试，不触及实际组项目。

|原意见|当前状态|复核证据|
|---|---|---|
|F01 上游失败条件答案|已处理|T/D key 均有 `standard_success_path` 和相同的 `conditional_grading_rules`，允许 not-recorded/pending/unknown 与安全条件下一步，不虚构成功链|
|F02 子项/部分分/关键错误|已处理|`shared/score-codebook.json` 覆盖全部 criterion；子项逐项和 rubric 相等，总分100；半分条件、无额外 cap、继承缺口与逐字匹配边界已固定|
|F03 合法 JSON 格式|已处理|最新 standalone injector 与 helper 接受同语义格式；严格 Decimal/重复键/类型检查通过；T/D 两个紧凑格式实际注入均退出0并记录 actual before SHA|
|P01 执行设置/隔离范围|设计层已处理|helper 固定6链24阶段、A/C24与B/D16外层调用软预算、10000字符、臂工具范围、目标SHA、同一Python、初次失败保留；D实际旧根/本链toolkit旧路径移走，其他源码/缓存是指令限制，无OS访问审计|
|Q01 T标量条件|已处理|T BRIEF 明写标量 l0=1、S与−S对同一V的控制、alpha两侧总预算；更新的 T/D initial MANIFEST 均有效|

新增追审检查13项全部通过，T/D 数值键与先前独立复算逐字段一致。证据为 `followup-clarification-audit.json` 与 `followup-updated-injector.json`。评估的 helper SHA 为 `1aa86d3a294172ef11e344bd7c7a79d327974708a9b7732c26162c34e777f343`；最新 standalone injector SHA 为 `08b6ede67122d64371eee6e38269345c245323e30bd9bbba4ecb3f6dc41e96e1`。

### F04：拒绝不安全/已变设置后，实际 helper 没有生成可继续的失败链记录

`study_ops.py` 的 B 分支直接调用 snapshot、读取参数并 assert；main 未捕获异常。三个独立 fixture 的实际结果：语义已变抛 AssertionError、参数缺失抛 FileNotFoundError、参数链接抛 RuntimeError。它们都正确地没有修改参数，但都未生成 `injection.json`，也未生成 B 的 `REQUEST.md`。此时 B 文件夹已经创建，直接重跑又会因 `exist_ok=False` 失败。standalone injector 本身拒绝异常输入是合理的；问题在组织者编排层尚未把这种结果转成“未投放且保留失败链”的固定处理。

建议冻结前在编排层捕获这些预期 setup 问题：保存结构化 `event_applied=false`、错误类型/路径/实际可得身份和原始失败；不改项目、不补初始值、不删除首轮目录；继续生成 B 的只读请求，让恢复者如实识别缺口。snapshot 对链接的报错同样需转成不跟随链接的行政状态记录，不能为拿到 snapshot 而修链接。后续总快照调用也应采用同一失败保留策略。若有专门外层 runner 承担这些步骤，应在冻结前把该实现和规则纳入冻结，而不是执行后人工决定。

这是目前唯一必要阻断；不涉及科研答案、核心产品修改或扩大评分要求。修正并在同类独立 fixture 上确认“失败记录存在、未投放、项目未改、B请求仍生成”后，可冻结。其他隔离能力按已声明的指令/自报范围解释，不要求额外引入OS沙箱。


### F04 最终处理结果：已关闭，可冻结

再次只读复核最新 helper：B 在 try/except 中拒绝语义变化、缺失或链接路径；错误进入结构化回执，记录 `event_applied=false`、实际差异和 `no_project_mutation_when_event_rejected`，随后仍生成 project-before 和 B REQUEST。snapshot 只记录链接自身的文本/mtime，不跟随或修改链接。原首次失败目录不删除，原 F04 发现与证据保留。

组织者最新三项独立 preflight（semantic-changed、missing、link）均表明：请求已生成、事件未投放、项目未变且错误已留存。对照实际代码与 `STUDY_ROOT/F04-preflight.json`，与协议要求一致；本次未执行新的 fixture 或正式链。最新 helper SHA256 为 `8b01b1de33e72ca7c498122e6c9d84b860e3b082c702cb981640b44ad34b137d`，preflight SHA256 为 `1856ca8e25f4dd76eaaf5e78fd67e5d8a8a7ed1c855986ac90b53a371ca6453e`。

现在没有必要阻断，建议冻结当前材料、代码、评分 codebook、工具身份和已声明的指令隔离范围；之后不因组别表现修改规则。
