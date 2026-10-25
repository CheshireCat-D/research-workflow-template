# 实际来源与解释工作笔记

执行者：Codex 代理；离线读取输入并自行分析，未作独立人类或史学专家复核。读取对象为本项目保存的四个输入，不检索外部史实。

来源身份：`corpus.json` 顶层 provenance/version=1 明示内容和元数据为新写虚构；`editorial-note.md` 第1段区分 period（原文被编目的时期）与 edition_year（辑本出版年）。E1=1915 基础辑本，E2=1935 增订辑本，均为虚构。作者/编者姓名、原始形成日期、保存机构、原件页码、选择机制均未提供，不作补写。

|ID及 JSON 定位|时期|辑本|文类|实际访问|
|---|---:|---|---|---|
|documents[id=D01]|1900|E1/1915|meeting-note|supplied-excerpt，仅提供节录，两层均读|
|documents[id=D02]|1900|E1/1915|letter|supplied-excerpt，仅提供节录，两层均读|
|documents[id=D03]|1900|E2/1935|catalogue-only|metadata-only，两层均 null，无文本可核|
|documents[id=D04]|1910|E1/1915|speech|supplied-excerpt，仅提供节录，两层均读|
|documents[id=D05]|1910|E2/1935|editorial|supplied-excerpt，仅提供节录，两层均读|
|documents[id=D06]|1910|E2/1935|letter|supplied-excerpt，仅提供节录，两层均读|

原扫描数量=0。`editorial-note.md` 第2段明确给定 corrected 为编辑修订层，不能据此声称独立核过原件。来源登记中节录条目为 partial，D03 为 metadata-only；本地 JSON 文件完整读取与完整原文访问分开。

实际层间核对：D02 OCR token 1=`liberiy`、4=`libcrty`，给定修订均为 `liberty`；其余四件可读节录两层 token 完全相同。D06 token 2=`liberal` 是另一个词形，按说明第3段不计为 liberty。没有自行纠字。无扫描，故这些只是两份给定文本的差别，未裁定修订的原件准确性。

材料关系：D01、D02、D04 同属 E1，不能因有三个条目即当成三个独立史学佐证；E1 内仍是1900两件/9token，对1910一件/5token，文类不同。E2 在1900没有可读文本，无法作 E2 对称时期比较。全可用1910多纳 D05、D06，共8token，其中 liberty=5；它们对1910合并频率的影响属于材料构成，不是估计出的“1935版次效应”。

草稿逐项核对：`draft.md` 第1段的“同等完整的一手原文”与访问说明冲突；“缺字或未取得页面没有影响”既被 D02 修订影响反驳，也不能由缺失的 D03 证成。“1905改革”在草稿第2段已标为无独立事件资料的作者解释；没有改革记录、机制链、可比控制或足够时间序列。时间先后及词频差不能识别因果。短 token 串缺乏句法和讨论语境，甚至不能验证 liberty 在此是否具有某种稳定政治含义。

竞争解释的证据不对称：提供文本的修订确切解释1900目标词多计2次；版本收文、文类和节录选择能改变可比性，现有输入不允许量化其独立贡献；真实语义/观念变化和改革因果在本包不可检验。修订稿保留计数发现并撤回历史因果断语。
