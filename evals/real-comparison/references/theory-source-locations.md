# 固定版本原文定位（设计前核验）

这些定位均指 source-manifest.json 的固定 PDF；页码是 PDF 的一基页序数。2020 v7 的印刷页码与 PDF 序数一致；2021 v9 的印刷页码也与 PDF 序数一致。不要把它们直接换成期刊页码。

| 来源 | 精确位置 | 任务所需支持 | 不能据此推断 |
|---|---|---|---|
| S1 arXiv:1808.03204v7 | PDF p9, Definition1, (2.1)–(2.2) | sub-ψ 约束的是(S,V)一对；V适应、V≥0；需要逐λ由超鞅支配 | 任意适应经验方差都可代入ψ_N |
| S1 | PDF p10–11, Definition1 后说明 | V可以适应而非可预测；条件对称性等特定条件可得经验平方变差控制 | 适应性独自意味着指数控制 |
| S1 | PDF p12–13, Theorem1(a), (2.7) | 任意过滤下 sub-ψ 过程，P(∃t:S_t≥a+bV_t) 的无限时域线性 crossing；不是iid固定n定理 | 此定理本身就是S2 normal-mixture曲线 |
| S1 | PDF p15, (2.12)–(2.15) | Ville+固定λ指数过程的 crossing 推理 | 逐时极值/事后λ或ρ无需校正 |
| S1 | PDF p26 Table3; p28 Lemma3(c),(d),(e) | 有界增量的ψ_N方差代理；条件对称性用[S]；有下界的增量用ψ_E | 未满足条件时把所有自归一化量视作等价 |
| S2 arXiv:1810.08240v9 | PDF p2, (2); p4, (3)及μ_t定义; p5, Definition1, (4)–(5), Definition2, (6) | μ_t为平均条件期望；相同的pair-based sub-ψ与统一boundary定义 | Theorem4需要共同μ或正态误差 |
| S2 | PDF p9, Lemma2, (13); p27–28 proof, (49)–(50) | 固定混合、乘积可测性、混合超鞅与阈值 | 以观测选择混合分布仍自动是超鞅 |
| S2 | PDF p10, (14); p28 Proposition5, (51) | 两侧normal-mixture边界，ρ固定，双尾同时失覆盖≤α | 需要再拆α/2；数据一定正态；任意经验V适用 |
| S2 | PDF p12, Proposition3, (21) | 固定ρ的最紧相对内在时间m；固定m的最优ρ | 每时刻把m取成当前V并且无校正 |
| S2 | PDF p14, Theorem4, (23) | X与预测在[a,b]，预测可预测，scale c=b−a的sub-exponential单尾α，双尾2α；目标μ_t不必共同 | ψ_N normal-mixture可无条件插入Vhat |
| S2 | PDF p35, AppendixA.8, (89)–(90) | ψ_E一步指数不等式和预测误差平方和的合法构造 | 概率控制只靠经验方差一致性 |
| S2 | PDF p17 Figure7 caption; p18 §5 item5 and讨论 | 原文已明确讨论naive self-normalized normal-mixture代入失败，含Ber(.01)情形 | 本任务的有限t=280严格反例是原文已经给出的证明；图中模拟本身是解析反例证明 |

版本与许可证据：S1固定版本摘要页链接CC BY4.0；S2固定版本摘要页链接arXiv non-exclusive distribution license。后者只记录作者给arXiv的分发许可，不是授予本仓库重分发全文的开放内容许可。原文PDF/TXT均留临时目录，仓库只收任务、链接、哈希、独立编写的答案/评分表。
