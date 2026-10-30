# 真实论文对照任务 T-CS-01：经验方差、混合调参与可选停止的定理审查

你是一名概率统计研究合作者。请依据下列两篇真实原始论文，对本次构造的研究备忘录做定理条件核查和文献定位，并交付一篇可直接给研究者阅读的中文短稿。

**真实性边界：下面的“待审备忘录”由本测试设计者专为测试构造，含待核查主张；它不是任何真实论文的摘录，也不是两篇来源论文的错误记录。请勿把构造稿误写为作者已经发表的主张。**

两篇来源论文均需读到相关原文，不能仅依赖摘要或第三方说明：

- S1: Steven R. Howard, Aaditya Ramdas, Jon McAuliffe, Jasjeet Sekhon. *Time-uniform Chernoff bounds via nonnegative supermartingales*. Probability Surveys 17 (2020), 257–317. DOI: https://doi.org/10.1214/18-PS321 。本测试固定作者全文版本 [arXiv:1808.03204v7](https://arxiv.org/abs/1808.03204v7)，PDF: https://arxiv.org/pdf/1808.03204v7 。
- S2: 同四位作者. *Time-uniform, nonparametric, nonasymptotic confidence sequences*. Annals of Statistics 49(2) (2021), 1055–1080. DOI: https://doi.org/10.1214/20-AOS1991 。本测试固定作者全文版本 [arXiv:1810.08240v9](https://arxiv.org/abs/1810.08240v9)，PDF: https://arxiv.org/pdf/1810.08240v9 。

请标明你所使用版本的 PDF 页码以及定理/命题/公式编号，避免把作者版页码当作期刊页码。论文 PDF 和全文提取只可用于本次本机研究缓存；交付物保留来源链接、元数据与必要的小范围公式，不复制全文到项目或输出目录。

## 待审备忘录（本次构造）

令 \((\mathcal F_t)_{t\ge0}\) 为过滤，\((X_t)\) 为适应过程，\(X_t\in[0,1]\) 且 \(\mathbb E[X_t\mid\mathcal F_{t-1}]=\mu\)，其中 \(\mu\in[0,1]\) 为常数。记
\[
S_t=\sum_{i=1}^t(X_i-\mu),\quad \bar X_t=t^{-1}\sum_{i=1}^tX_i,
\quad \widehat X_1=\tfrac12,\quad \widehat X_t=\bar X_{t-1}\ (t\ge2),
\quad \widehat V_t=\sum_{i=1}^t(X_i-\widehat X_i)^2.
\]
对 \(0<\alpha<1,\rho>0,v\ge0\) 定义
\[
b_{\rho,\alpha}(v)=\sqrt{(v+\rho)\log\!\frac{v+\rho}{\alpha^2\rho}}.
\]

**主张 A（基准引理）**：更一般地，如果某个非减可预测过程 \(V_t\) 满足 \(V_0=0\)，且对每个 \(\lambda\in\mathbb R\) 及每个 \(t\ge1\)，
\[
\mathbb E\left[\exp\{\lambda(X_t-\mu)\}\mid\mathcal F_{t-1}\right]
\le \exp\{\lambda^2(V_t-V_{t-1})/2\},\tag{SG}
\]
则对预先固定的 \(\rho>0\)，令 \(F_\rho=N(0,1/\rho)\)，有
\[
M_t^\rho=\int_{\mathbb R}\exp\{\lambda S_t-\lambda^2V_t/2\}\,dF_\rho(\lambda)
=\sqrt{\frac{\rho}{V_t+\rho}}\exp\!\left\{\frac{S_t^2}{2(V_t+\rho)}\right\}.
\]
因此 \(C_t^\rho=[\bar X_t\pm b_{\rho,\alpha}(V_t)/t]\cap[0,1]\) 满足
\(\mathbb P(\forall t\ge1:\mu\in C_t^\rho)\ge1-\alpha\)。

**主张 B（经验方差替换）**：因为 S1 的 sub-\(\psi\) 定义允许内在时间是适应过程，而 \(\widehat V_t\) 也是适应过程，所以仅凭有界性和共同条件均值，就可以在 A 中用 \(\widehat V_t\) 替换 \(V_t\)，仍保留相同的 \(b_{\rho,\alpha}\) 和覆盖概率。

**主张 C（逐时最优调参）**：S2 允许优化混合参数，故每时刻根据当前 \(V_t\) 取 \(\rho_t\in\arg\min_{\rho>0}b_{\rho,\alpha}(V_t)\)，所得 \(C_t^*\) 仍具有上述同时覆盖率。即使用合法的确定性 \(V_t=t/4\)，该结论也无需额外校正。

**主张 D（文献定位）**：“S1 仅给出 iid 观测的固定样本量界；S2 的置信序列要求共同均值和正态误差。因此 B 与 C 是首次得到的自适应、非参数、无限时域置信序列。”

**主张 E（可选停止）**：如果某一构造确实已证明同时覆盖，则对任意取值于 \(\{1,2,\ldots\}\)、几乎处处有限的停止时刻 \(\tau\)，有 \(\mathbb P(\mu\in C_\tau)\ge1-\alpha\)，且无需 \(\mathbb E\tau<\infty\)。

## 你的工作

1. 分别判断 A–E，给出来源和数学理由。用一张简明证据表比较 S1 的 sub-\(\psi\)/主定理、S2 的正态混合结果、S2 的经验 Bernstein 结果：对象、假设、内在时间/方差量、单尾或双尾、概率水平、时间域及可比较的结论。区分定义允许一个量“适应”与特定 \((S,V)\) 确实满足该定义。
2. 独立展示 A 中积分的配方计算与边界反演，解释积分交换/超鞅性质所需的条件，确认双尾概率常数。不能只抄写最终公式。
3. 对 B 如判为不成立，给出一个**有限时间、有明确分布、事件及解析概率**的反例，使错误置信序列的失覆盖概率严格超过标称 \(\alpha\)。反例必须使用上面指定的预测器；模拟图或“无法证明”不算反例。
4. 对 C 推导 \(\inf_{\rho>0}b_{\rho,\alpha}(v)\) 的形状并判断其无限时域行为；解释 S2 中的参数优化究竟允许什么。如需使用经典大数/极限定理，请明确写出用到的命题。可直接使用经典 iid Rademacher LIL：若 \(R_i\) 独立且各以概率 \(1/2\) 取 \(\pm1\)，则 \(\limsup_{t\to\infty}\sum_{i=1}^tR_i/\sqrt{2t\log\log t}=1\) 几乎必然。
5. 写出可替换构造稿的正确版本：至少给出一个使用正态混合边界的有效方案，以及一个确实使用 \(\widehat V_t\) 的经验 Bernstein 方案。对后者写清 \(\psi\) 的形式/参数域、预测器条件、双尾错误预算，并展示一阶条件期望不等式为什么成立。另外给出一个使用多组混合参数、具有明确错误预算的有效方法。
6. 最后写一段可直接放进研究备忘录的修订结论，准确定位已有工作与本次审查得到的内容。不要据有限两篇论文的核查宣称全球首创。

交付 `audit.md`（建议 1500–3000 汉字，公式和证据表不计）及可选的 `checks.py`。所有数值写出计算式；代码只是校验数值，不能替代证明。输出要足够自包含，让读者沿链接和页码复核，但无需做与本任务无关的全面综述。
