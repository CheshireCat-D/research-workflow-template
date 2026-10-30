# 当前恢复结论

项目的当前工作文件与登记状态发生冲突：`notes/parameters.json` 的 rho 已由初始 1 改为 4；`.research/state.json` revision 1 的有效约束、T-CHOICE 和完成输入指纹仍是 rho=1。没有可见修订依据或作者批准记录。不能把文件较新的 mtime 当作已经接受的新决定，也不能据旧交接自动回滚。

本次只读运行 `scripts/manage.py status`，退出 0；另行逐字节核对登记文件、原始内容副本和结果表。全部登记文件都存在，仅上述参数文件的内容与登记不符。完整读取清单、SHA256、命令及只读前后快照见本目录执行记录；没有修改项目、重新登记、保存断点、恢复文件或运行科学计算。

# 当前问题、约束和权威

唯一权威表示是 `.research/state.json`，不是 `RECOVERY.md`、初始约束副本或 `.research/evidence/A/current-status.json`。现有权威记录的范围为 alpha=0.05、rho=1、观察前固定 rho、v=[0,1,10,100]；实际工作参数除 rho=4 外其余相同。实际参数文件不能继续冒用旧完成指纹。

研究仅对给定条件下的 normal-mixture 边界作数值核对：l0=1，S 与 −S 对同一非负内在时间 V 满足相应 sub-Gaussian 指数控制；alpha 是双侧总预算，rho 须在观察前固定，不能把任意经验方差当成 V。运行资源限离线 Python 标准库，不新增采样或模型重拟合。语言中文；给定截止日为 2026-12-15，属于供给的组织约束。目标期刊未定，无人工专家批准，无外部投稿授权，未经内容复核不投稿。

# 可证实变更与依赖影响

|材料/活动|当前证据和适用性|
|---|---|
|T-PARAM `notes/parameters.json`|161 bytes，rho=4；登记/初始副本为 rho=1，同为 161 bytes。大小相同不能证明内容相同。|
|T-CALC|历史 done；当前 needs_recheck。直接输入 T-PARAM 指纹改变。|
|T-SYNTH|历史 done；当前 needs_recheck。沿 T-CALC → T-SYNTH 传递受影响；摘要仍写 rho=1。|
|T-SOURCE-CHECK|仍为 done，其固定 PDF 和来源卡字节未变，且该分支独立于数值 rho；完成范围仅是来源身份及卡片口径。|

参数登记 SHA256：`230aea31e1afab3553088d8a6ff08e36a9155828c775681f69737c79b7c39b67`。
当前 SHA256：`340d3d94ab2386c9716d3fb134933347adaf630424483a7206abca8074cda117`。
初始完整副本 `.research/versions/A-initial/notes/parameters.json` 仍与登记 SHA 一致，因此 rho 的具体差异可由内容直接核查；不是仅由时间戳猜测。

`results/result.json`、`results/table.csv`、`results/summary.md`、`scripts/compute.py`、固定 PDF 和 `notes/source-check.md` 均与登记字节一致，没有发现登记路径缺失。旧 result 的 alpha=0.05、rho=1，所绑定的参数 SHA 是初始值，明确不绑定当前 rho=4。表与旧 result 数值一致；摘要 v=10 的 9.606401928869 对应旧结果 9.606401928868575。这些历史输出没有被篡改的证据，但也不能作为当前 rho=4 的已验证成果。

这不是定理真假判定。rho=4 本身不违反脚本要求的 rho>0，仍需确认实际选择是否在观察前固定。此次未执行计算、模拟或证明核验，不能宣布 rho=4 的正确数值或覆盖性质，亦不能据文件登记过期宣布原论文或旧数值错误。

# 旧断点和跟踪边界

旧断点 `A-verified-initial` 当前为 `stale_for_registered_bytes`，触发路径为 `notes/parameters.json`。旧状态文件称全部 fresh 的结论只适用于当时登记字节。断点仍保留初始参数、成果的历史依据和确切内容；保存断点本身不构成实质复核，不能凭旧 done 状态继续宣称当前计算完成。

来源 T-SRC 为 Howard 等 *Time-uniform, nonparametric, nonasymptotic confidence sequences*，供给身份 arXiv:1810.08240v9、DOI 10.1214/20-AOS1991。本地 `sources/howard2021-arxiv-v9.pdf` 为 1494142 bytes，SHA256 `eb3efd547349adfbff25514ae0854c142cd29b96b398be38c9000d69a2f64ca8`，与登记一致。本次完整读字节仅为哈希，没有提取正文、检查页面或独立核查 p10 (14)/p28 Proposition 5 (51)；这些定位仍是所给来源卡的陈述。

T-REMOTE 只有 *Time-uniform Chernoff bounds via nonnegative supermartingales*、arXiv:1808.03204v7 等身份元数据，没有本地内容绑定，也没有远程访问，不能判断远端当前内容。`notes/unregistered-scratch.md` 虽存在并被本次清点，不属于声明的自动依赖，不能把一次全树哈希清点说成已跟踪全部科研依赖。自动状态检查覆盖七个登记材料及特定 choice/statement 指纹，不独立保证所有笔记、管理程序、历史证据、来源语义或作者意图。原 PDF 仅限私人研究缓存，本次输出不复制原 PDF；未来公开交付保留来源身份和自行生成成果。

# 应先解决的下一步

先澄清 rho=4 的修改意图和依据，并保留当前编辑内容；不能照旧 next_action 将 rho=1 的成果直接当当前成果交作者讨论。未来获得写入授权的阶段，若 rho=4 是有效修订，应保存修订前内容和依据、更新权威约束/选择及输入登记，再真实重算 T-CALC、核对 result 与 companion table，复核 T-SYNTH 的摘要和范围，最后记录实际完成证据与新断点。若是误改，也须通过明确当前 SHA 的冲突保护和内容保留后再处理，不能以旧笔记静默覆盖。当前阶段已完成只读审查，未实施上述修订或恢复。

本目录 `audit-checks.json` 和 `current-status.json` 提供具体检查结果；`project-before.json` 与 `project-after.json` 对全树文件 SHA/bytes/mtime 和目录 mtime 的比较完全一致。最初四个工具调用仅执行读取；快照比较从独立审查程序开始至其结束，不把目录 mtime 当科研内容版本。
