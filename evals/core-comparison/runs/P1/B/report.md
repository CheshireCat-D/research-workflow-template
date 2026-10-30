# 当前恢复审查

当前工作参数已从 rho=1 改为 rho=4，而结果、配套表和摘要仍为 rho=1。不能继续把这些历史成果称为当前参数的已核对成果。只读恢复发现 T-CALC、T-SYNTH 与最近检查点过期；独立来源身份分支仍有效。本阶段未计算新结果、未登记、未保存检查点、未修复项目。

## 权威状态与约束

`project.json` 是配置权威，`records/registry.json` 是登记、版本、活动依赖及检查点权威；当前 revision=26，T-PARAM/T-CALC/T-SYNTH 均仍为版本1，T-RECOVERY 为版本2。`PROJECT.md` 的初始化句和 `RECOVERY.md` 的历史数值不能覆盖当前文件事实。登记中的 T-CHOICE 仍选择初始 rho=1，没有发现解释 rho=4 的新决定或修订理由，无法判定是谁、何时及为何改变参数。

问题限定为规定 sub-Gaussian 过程、标量 l0=1、S 与 −S 使用同一非负内在时间 V、alpha 为两侧总预算，rho 必须在观察前固定。本项目只核对指定参数的边界数值，不建立新证明。工作文件当前 alpha=0.05、rho=4、rho_selection=fixed-before-observation、v=[0,1,10,100]；登记与历史已核对范围为 rho=1。字段写着“观察前固定”并不独立证明实际选择时间。

配置保存中文、2026-12-15 截止日期（组织者给定约束）、仅离线 Python 标准库、不得新采数据或重拟合、目标期刊未定。没有人类专家批准或外部投稿授权。原 PDF 仅供私有研究缓存，不再分发。原始约束和逻辑义务保存在 `provenance/initial/constraints.json`、`obligations.json`、`BRIEF.md`、`source-identities.json`。

## 可证实的变化与成果不一致

对检查点绑定的15个本地文件逐一计算完整 SHA256，唯一身份变化是 `notes/parameters.json`，未发现其中任何文件缺失。

|对象|现状及证据|
|---|---|
|当前参数|161 bytes；SHA256 `340d3d94ab2386c9716d3fb134933347adaf630424483a7206abca8074cda117`；rho=4|
|绑定及初始参数|161 bytes；SHA256 `230aea31e1afab3553088d8a6ff08e36a9155828c775681f69737c79b7c39b67`；rho=1；完整旧内容在 `history/stage-a-initial/notes/parameters.json`|
|`results/result.json`|与检查点及初始备份完全相同，明确 rho=1，input_sha256.parameters 仍为上述旧参数SHA|
|`results/table.csv`|与检查点完全相同；四行数值对应旧 JSON，不能当作 rho=4 表|
|`results/summary.md`|与检查点完全相同，仍写 rho=1、v=10 时 9.606401928869|

参数的 alpha、选择方式、网格未变。旧 JSON 四个边界值为 2.4477468306808166、3.6563948713638483、9.606401928868575、32.73018624234933。本次只读取并比较这些已存数据，没有重新执行其科学计算。结果、表和摘要彼此保持旧范围的一致性，但与当前参数不一致。

`scripts/compute.py` 身份仍为 `e7b2f754ed7a449ee76a45c80ce3888a36be20f5c783f9a67c630fc7c25c74a1`。主 PDF `sources/howard2021-arxiv-v9.pdf` 仍为1494142 bytes，SHA256 `eb3efd547349adfbff25514ae0854c142cd29b96b398be38c9000d69a2f64ca8`，与给定来源清单一致。源卡及初始备份未变。本次全项目文件身份快照保存在外部 `project-before.json`；它是本次审查的观察记录，不能冒充项目既有自动覆盖。

## 影响传播与检查点

|活动|声明状态 / 当前有效状态|理由|
|---|---|---|
|T-CALC|done / stale|直接输入 T-PARAM 的文件指纹变化，旧结果仍绑定 rho=1|
|T-SYNTH|done / stale|depends_on T-CALC，故传递受影响；完成绑定中也包含旧参数指纹，摘要需重新实质核对|
|T-SOURCE-CHECK|done / done|只依赖 T-SRC、T-RAW，并产生 T-SOURCE-NOTE；PDF与源卡未变，与数值参数选择独立|

T-RESULT、T-TABLE、T-SUMMARY 文件字节未变，并不代表其对当前参数仍适用。T-CLAIM 的旧 supported-in-scope 评估明确只覆盖 alpha=.05、rho=1 的四点重现，不能扩展到当前 rho=4。独立分支的“done”也只表示有限身份/卡片检查曾登记完成。

最近检查点时间为 2026-10-30T01:06:52.542533+00:00；配置哈希未变，登记恢复报告未列登记漂移，检查点仅因 local-files 过期。旧游标的“若身份与活动仍新鲜则把 rho=1 表摘要交作者”条件已不满足；其要求先定位变化和复核的分支仍适用。旧检查点可定位历史，不可用来证明当前成果已核对。

实际运行项目内只读 `resume`，退出1，errors/warnings 均为空，findings 为参数 file_changed、两个 activity_stale、checkpoint_stale；这是待复核状态，不是接口失败。项目内已安装资源完整性检查退出0，检查67个资源文件，未比较工具来源版本（source_version_matches=null），不构成科研结论认证。

## 来源及自动覆盖边界

T-SRC 保存 Howard 等论文 arXiv:1810.08240v9 与 DOI 10.1214/20-AOS1991 身份，并由 T-RAW 绑定本地完整 PDF。此次仅对 PDF 全字节散列，阅读来源元数据及组织者释义卡，没有读取数学页、核对页码/命题或重新证明覆盖结论。卡中的 p10/(14)、p28/Proposition 5/(51) 是材料陈述，本次未独立验证。来源真实身份与公式内容支持须分别判断。

T-REMOTE 仅有 arXiv:1808.03204v7 身份、metadata-only，无本地证据绑定，没有当前远端内容核验。URL 不等于内容指纹。`notes/unregistered-scratch.md` 未登记，不在自动变更覆盖中；此次读到其排除说明且与初始清单哈希一致，也不能据此宣称全部未登记材料/依赖都被系统跟踪。约束、历史日志等实际文件并非全部自动绑定。本次未联网。

已确认的是文件/工作完成登记对当前参数失效；这不证明原定理错误，也不证明 rho=4 科学结论成立。旧活动记录只保存旧范围已执行的核对，并没有人类独立审阅、形式化证明、覆盖模拟或新颖性结论。`scientific_validity` 为 not-assessed。

## 应先解决的下一步

本次可执行动作止于外部只读报告。后续进入获授权的写入阶段时，首先保留 rho=4 当前字节并澄清其选择依据/作者意图，结合已留 rho=1 原始版本核对；不得无依据回滚或把旧表改标为新表。若确认 rho=4 是有效修订，再用现存计算脚本在独立新目录复核新参数，核对 JSON、CSV、摘要及参数指纹，实质重做 T-CALC 后复核 T-SYNTH。读取各当前记录版本，再通过正式替换接口登记证据、决定、成果及活动，最后保存检查点。只重新绑定或保存检查点不能替代复核。独立来源身份分支可沿用其有限范围；远端正文及理论支持仍未检查。未经内容复核不投稿。

本次未执行上述后续计算或写入。项目文件字节、文件mtime和目录mtime的前后核对结果见 `project-readonly-verification.json`；所有答卷和执行证据均在项目外输出目录。

实测前后比较：103个文件及44个目录逐项相同，文件字节和全部所核对mtime未变。
