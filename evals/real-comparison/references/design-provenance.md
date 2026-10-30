# 设计阶段来源与额外上下文披露

2026-10-29。本文件给评测组织者，不交执行者作为任务说明。

设计者使用 UCI 官方落地页、该页链接的官方 ZIP 及其 README，独立运行 Python 标准库计算。没有修改仓库文件或个人技能包。原始数据、年份切片及参考解析全部保存在 DATA_DESIGN/。

在父代理补充“设计阶段也不读取个人技能包”边界之前，设计者已经只读访问了：

- personal-skills/mathematical-academic-writing/SKILL.md：全文。
- personal-skills/mathematical-academic-writing/references/statistical_analysis_workflows.md：全文。
- personal-memory/MEMORY.md：先以 RWT|reliable|workbench|科研任务 做 rg 查询，随后读取45–76行。内容仅为历史RWT比较与技能路由记录，没有本任务数据或结果。

收到补充边界后立即向父代理披露以上路径和范围，后续不再读取或应用个人技能包正文。任务的全部来源事实、可评分数值均可由下述公开原件和独立计算复核。上述读取意味着本设计者不能声称“设计阶段完全没有接触个人技能”；它不应混入执行者已读指导的归因。执行者只应拿到 public 下对应阶段材料与本方冻结指导，不能拿到本文件、private 目录或完整 raw 目录。

使用的联网途径：web 工具打开官方 UCI 页面和 Creative Commons 官网，使用 curl 从 UCI 官方链接下载 ZIP 和页面快照。网页工具不能解码 ZIP，转用 curl；普通网络沙箱不能解析域名，使用已获自动审查准许的只读公开下载。没有发送消息给第三人。

未取得原论文正文：DOI 10.1007/s13748-013-0040-3 的出版商跳转未能通过网页工具打开。任务不考查该论文的科学结论，也不会把构造草稿归为原论文错误。原论文书目信息仅按原始 README 保留；本次核对的数据身份以 UCI DOI 10.24432/C5W894 为锚。

记忆披露（给父代理引用需要）：MEMORY.md:45-60，对应历史 rollout id 01a17559-0123-7370-a131-625398355924。记忆只用于确定既有RWT比较不能冒充当前科学证据；不用于新数据数值。

Independent review issues were resolved before execution: data-b includes original 2011 CSVs; theory page locators, positive index of tau and explicit multi-rho delivery were clarified. No numerical data, rubric weights or principal answers were changed.
