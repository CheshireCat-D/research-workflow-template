# 固定精度正态混合边界：初始项目交付

已建立可恢复项目 `PROJECT_ROOT`，创建前确认目录不存在，未覆盖已有项目。输入清单 13 项逐一匹配所给完整 SHA256 和字节数。项目保存给定材料、约束、来源身份、逻辑记录、依赖、真实验证证据和四份完整初始内容。

## 当前数值及核对

实际使用给定 `scripts/compute.py`，在独立新目录 `A/output/validation-normal/` 正常运行，退出码 0。alpha=0.05 为双侧总预算，rho=1 在观察前固定，l0=1，内在时间点为 [0,1,10,100]。计算公式为

`b(v)=sqrt((v+rho)*(log(1+v/rho)+2*log(1/alpha)))`。

|v|边界|
|---:|---:|
|0|2.4477468306808166|
|1|3.6563948713638483|
|10|9.606401928868575|
|100|32.73018624234933|

重算 `result.json` 与预制结果 JSON 完整字节及解析内容均一致；`table.csv` 也完整字节一致，解析行与 JSON 的四点值一致。摘要中的 v=10 边界 9.606401928869 与十二位小数舍入一致，alpha、rho、观察前固定及数值评估范围一致。这里验证的是给定预制结果，不声称从零发现或独立证明了研究结论。

真实命令和 stdout/stderr 位于 `normal-execution.json`；逐项结果、全长 SHA 和前后 mtime 位于 `validation-checks.json`，相同小型证据已持久保存在项目 `.research/evidence/A/`。

## 有意无效输入

另以 `notes/rejected-parameters.json` 的 alpha=1 实际运行，退出码 **2**，stderr 为 `ValueError: Require 0<alpha<1, rho>0 and finite nonnegative intrinsic times`。无效输出目录 `validation-rejected` 没有创建。所有已登记的项目输入/有效成果及正常验证输出在无效试算前后，完整 SHA256、字节数及文件 mtime 均未变。

这是受控无效输入拒绝测试；原正常结果保留，没有把它记为科学分析失败，也没有用补跑掩去首次错误。实际 argv、cwd、退出码、错误保存在 `rejected-execution.json` 和项目证据中。

## 持久状态与恢复

当前唯一元数据权威是项目 `.research/state.json`；原始约束和来源依据在 `.research/provenance/initial/`。旧笔记、旧交接和初始副本不覆盖较新有效元数据。逻辑层明确区分来源、材料、声明、关系、选择、成果和活动。

|活动|本次完成范围|当前依赖状态|
|---|---|---|
|T-SOURCE-CHECK|给定固定来源身份/版本、卡片范围检查|当前有效；不依赖数值参数|
|T-CALC|真实正常运行，并核对 JSON 和 companion 表|当前有效|
|T-SYNTH|核对所给摘要的参数、数值和范围|当前有效；依赖 T-CALC|

只读恢复命令（在项目目录，Python 3.9+ 标准库）为 `python3 -I -B scripts/manage.py status`。它比较完成时输入/输出和逻辑指纹，沿 T-CALC → T-SYNTH 传播需复核状态。最终实际执行退出 0，未发现登记材料变更或缺失；三项活动有效，checkpoint 对登记字节当前新鲜。保存断点本身不等于实质复核。

`.research/versions/A-initial/` 保存 parameters.json、result.json、table.csv、summary.md 的完整原字节和索引，四份快照与当前原件逐字节一致。`scripts/manage.py` 提供带完整当前 SHA 冲突保护的恢复预览/显式写入，写入前归档旧字节；本阶段没有实际执行恢复或任何未来修订。恢复说明为 `RECOVERY.md`。脚本以自身位置解析根目录，不依赖本阶段外部答卷或原绝对路径；原大型 PDF 只保存一份私人研究缓存。

## 来源与科学范围

本地主要来源身份来自所给 `source-identities.json`：Howard 等，Time-uniform, nonparametric, nonasymptotic confidence sequences，arXiv:1810.08240v9，DOI 10.1214/20-AOS1991。本地 PDF 1,494,142 字节，完整 SHA256 为 `eb3efd547349adfbff25514ae0854c142cd29b96b398be38c9000d69a2f64ca8`。本阶段整文件仅按字节读取以核对 hash/清单；未提取 PDF 正文、逐页查看或独立审阅定理。来源卡中的 p10 (14)、p28 Proposition 5 (51) 是所给卡片的定位陈述，本阶段未逐页核验。

适用条件仍为：S 与 −S 在同一非负内在时间 V 下满足相应 sub-Gaussian 指数控制；不能把任意经验方差直接代入。只核对给定参数的边界数值；不建立新证明、覆盖率模拟、新颖性、形式化验证或人工专家批准。

T-REMOTE 只有 arXiv:1808.03204v7 身份元数据，无本地副本、内容绑定或当前远端检查；本阶段网络调用为 0。`notes/unregistered-scratch.md` 原样保留但不纳入自动依赖检测，不声称覆盖全部项目文件。原始 PDF 只供私人缓存，公开交付不分发原始资料。

当前截止日为给定的 2026-12-15（组织者约束），只用离线 Python 标准库，不收集新数据、不重拟合，目标期刊未定、语言中文。具体下一步：先运行只读状态检查，向作者讨论当前四点结果、上述条件与未作证明/模拟的范围，等待作者实际决定；未经内容复核不投稿。

主答卷和执行记录分别为本目录 `report.md` 与 `execution.json`；机器可读当前事实见 `state-answer.json`，完整输入/产物身份见 `inputs-and-artifacts.json`。
