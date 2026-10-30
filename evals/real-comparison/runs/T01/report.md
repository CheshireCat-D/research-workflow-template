# 经验方差、混合调参与可选停止：构造稿审查

本稿审查的是所给原创 `draft.tex` 中尚未核实的 A–E，不把它们归于来源论文。结论是：**A、E 成立；B、C、D 不成立。** 下文页码全部指指定作者版 PDF 的一基页序，不是期刊页码。仅核查这两篇原始材料及相应推导，不据此作全球首创判断。

来源为 Howard、Ramdas、McAuliffe、Sekhon：S1，*Time-uniform Chernoff bounds via nonnegative supermartingales*，Probability Surveys 17 (2020), 257–317，[DOI](https://doi.org/10.1214/18-PS321)，固定 [arXiv:1808.03204v7 PDF](https://arxiv.org/pdf/1808.03204v7)；S2，*Time-uniform, nonparametric, nonasymptotic confidence sequences*，Annals of Statistics 49(2) (2021), 1055–1080，[DOI](https://doi.org/10.1214/20-AOS1991)，固定 [arXiv:1810.08240v9 PDF](https://arxiv.org/pdf/1810.08240v9)。S2 所用作者版首页日期为 2022 年 8 月，不能将其误称为 2021 年期刊版的同一排页。已核对本地 PDF 哈希与输入 manifest 一致；未重新联网核验元数据。全文保留在输入缓存，输出不复制论文全文。

## 原文证据与可比较范围

| 来源、对象及定位 | 假设与内在时间 | 尾、概率与时间域 | 可比较结论 |
|---|---|---|---|
| S1 定义 1，PDF p.9，(2.1)–(2.2)；主定理 1，pp.12–13，(2.7)–(2.10) | 适应的实值对 \((S,V)\)，\(S_0=V_0=0,V_t\ge0\)；对每个 \(0\le\lambda<\lambda_{\max}\)，指数过程须由初值不超过 \(l_0\) 的超鞅支配。允许适应的 \(V\)，但适应性本身不提供该支配关系 | 原表述为上尾；(2.7) 给 \(\Pr(\exists t:S_t\ge a+bV_t\mid\mathcal F_0)\le l_0e^{-aD(b)}\)。\(t\in\mathbb N\) 或连续时间 \((0,\infty)\)；连续情形有通常条件和 càdlàg 条件 | 一般的无限时域线性穿越界；不要求 iid。其余等价形式另需 CGF-like 条件。下尾另对 \(-S\) 验证 |
| S2 正态混合，PDF p.10 (14)、p.28 命题 5 (51)；混合引理 2，p.9 (13)，证明 pp.27–28 | \(S\) 与 \(-S\) 对同一 \(V\) 均 sub-Gaussian，\(\psi_N(\lambda)=\lambda^2/2\)；混合参数 \(\rho>0\) 固定；混合须有乘积可测性 | 直接双尾，\(\Pr(\forall t\ge1:|S_t|<\sqrt{(V_t+\rho)\log[l_0^2(V_t+\rho)/(\alpha^2\rho)]})\ge1-\alpha\) | \(l_0=1\) 时正是 A 的边界；“正态”描述混合核和 CGF 上界，不要求观测服从正态分布 |
| S2 经验 Bernstein，PDF p.14 定理 4 (23)；p.6 的 \(\psi_{E,c}\)；p.35 证明 (89)–(90) | 适应的 \(X_t\in[a,b]\)，任意取值于 \([a,b]\) 的可预测 \(\widehat X_t\)；\(\widehat V_t=\sum(X_i-\widehat X_i)^2\)，使用尺度 \(c=b-a\) 的 sub-exponential 边界 \(u\) | 若单尾预算为 \(\delta\)，双尾同时覆盖至少 \(1-2\delta\)，对所有整数 \(t\ge1\) | 覆盖 \(\mu_t=t^{-1}\sum\mathbb E_{i-1}X_i\)，半径 \(u(\widehat V_t)/t\)；不要求共同均值、iid 或正态误差，不能把 \(u\) 无条件换成正态边界 |

S1 p.10 明说 sub-\(\psi\) 条件属于配对 \((S,V)\)；p.11 在允许适应方差量后给出的是附加条件下的自归一化例子。S2 pp.4–5 的一般目标是平均条件均值。因此 D 关于两篇论文适用范围的描述均错误；B、C 也不能支撑其首创性结论。

## A：固定混合的独立推导与双尾常数

设 \(S_0=0\)，\(V_t\) 为有限实值过程，并采用题设 (SG)。固定 \(\lambda\in\mathbb R\)，令
\[
L_t(\lambda)=e^{\lambda S_t-\lambda^2V_t/2}.
\]
由于 \(\Delta V_t\) 是 \(\mathcal F_{t-1}\)-可测的，
\[
\mathbb E_{t-1}L_t(\lambda)
=L_{t-1}(\lambda)e^{-\lambda^2\Delta V_t/2}
 \mathbb E_{t-1}e^{\lambda(X_t-\mu)}\le L_{t-1}(\lambda).
\]
其非负且从 1 出发，归纳得 \(\mathbb E L_t(\lambda)\le1\)。这里指数核对 \((\omega,\lambda)\) 联合可测：\(S_t,V_t\) 可测且关于 \(\lambda\) 连续。因此非负的条件 Tonelli 可交换混合与条件期望，得到 \(M_t=\int L_t\,dF_\rho\) 为可积非负超鞅、\(M_0=1\)。对每个固定 \(\lambda\) 的几乎处处不等式足以在此积分，无需预先假定一个覆盖所有实数 \(\lambda\) 的共同零测集。混合分布须预先固定，不能在积分后按当前数据重新选择。

写 \(A_t=V_t+\rho>0\)。代入正态密度并配方：
\[
\begin{aligned}
M_t^\rho
&=\sqrt{\frac\rho{2\pi}}\int_{\mathbb R}
 \exp\!\left\{\lambda S_t-\frac{A_t\lambda^2}{2}\right\}\,d\lambda\\
&=\sqrt{\frac\rho{2\pi}}e^{S_t^2/(2A_t)}
 \int_{\mathbb R}\exp\!\left\{-\frac{A_t}{2}
      (\lambda-S_t/A_t)^2\right\}\,d\lambda\\
&=\sqrt{\frac\rho{A_t}}e^{S_t^2/(2A_t)}.
\end{aligned}
\]
故
\[
M_t^\rho\ge\alpha^{-1}
\iff S_t^2\ge A_t\left(2\log\alpha^{-1}+\log\frac{A_t}{\rho}\right)
\iff |S_t|\ge b_{\rho,\alpha}(V_t).
\]
Ville 不等式（S1 PDF p.13，引理 1，(2.11)）给出该双尾穿越事件的概率不超过 \(\alpha\)。这是一次对全实轴混合的最大不等式，**无须再乘 2 或把 \(\alpha\) 减半**。失覆盖事件 \(\{|S_t|>b(V_t)\}\) 包含于上述穿越事件，闭区间端点无碍结论。因为真值在 \([0,1]\)，截断亦不损覆盖。

## B：指定预测器下的有限、解析反例

取 \(X_i\) iid Bernoulli\((1/100)\)，\(\mu=1/100\)，并预先固定
\[
\alpha=1/20,\qquad\rho=1/4,\qquad n=200.
\]
事件 \(E=\{X_1=\cdots=X_{200}=0\}\) 上，题设预测器恰有 \(\widehat X_1=1/2\)、其后 \(\widehat X_i=0\)，所以
\[
\bar X_{200}=0,\quad\widehat V_{200}=1/4,\quad |S_{200}|=2,
\quad b_{1/4,1/20}(1/4)=\sqrt{\tfrac12\log800}<2.
\]
最后一不等式由 \(e^8>\sum_{k=0}^{6}8^k/k!>800\) 得到。错误区间上端严格小于 \(2/200=\mu\)，故在 \(E\) 上失覆盖。其解析概率为
\[
\Pr(E)=(99/100)^{200}
> (9/10)^{20}>1/9>1/20=\alpha.
\]
第一步用严格 Bernoulli 不等式 \((99/100)^{10}>9/10\)，第二步用 \(3\cdot9^{10}>10^{10}\)。数值仅供核对：\(b=\sqrt{\log800/2}\approx1.82820\)，\(\Pr(E)=(99/100)^{200}\approx0.133980\)。因此仅在一个有限时刻就已违反要求，完全不依赖模拟或渐近论证。\(\widehat V\) 是适应过程，并不保证它可作为 \(\psi_N\) 的内在时间；B 混淆了定义的可测性入口与指数超鞅义务。

## C：逐时最优化把边界降到不可行的平方根阶

令 \(L=\log\alpha^{-2}>0\)。当 \(v>0\) 时设 \(r=v/\rho\)，则
\[
\frac{b_{\rho,\alpha}^2(v)}v
=f(r)=(1+r^{-1})[L+\log(1+r)],\qquad
f'(r)=\frac{r-L-\log(1+r)}{r^2}.
\]
函数 \(r-\log(1+r)\) 从 0 严格增加到无穷大，故唯一最优点 \(r_\alpha>0\) 满足
\[
r_\alpha=L+\log(1+r_\alpha),\quad
\rho^*(v)=v/r_\alpha,\quad
\inf_{\rho>0}b_{\rho,\alpha}(v)
=\sqrt{1+r_\alpha}\sqrt v=:\kappa_\alpha\sqrt v.
\]
等价地 \(1+r_\alpha=-W_{-1}(-\alpha^2/e)\)。当 \(v=0\)，\(b^2=\rho L\)，下确界为 0，但正的 \(\rho\) 上不取到，原稿此时的 argmin 还可能为空。

现在用完全合法的 \(V_t=t/4\)：取 iid Bernoulli\((1/2)\)，令 \(R_i=2X_i-1\)，则 \(S_t=\tfrac12\sum R_i\)，并由有界变量的条件 Hoeffding 引理满足 (SG)。逐时最优边界成为 \(\tfrac12\kappa_\alpha\sqrt t\)。使用题目允许的经典 Rademacher LIL：
\[
\limsup_{t\to\infty}\frac{\sum_{i=1}^tR_i}{\sqrt{2t\log\log t}}=1
\quad\text{a.s.}
\]
故 \(\sum R_i>\kappa_\alpha\sqrt t\) 无穷多次几乎必然成立。失覆盖概率是 1，同时覆盖概率是 0。这甚至是确定性的逐时调参，说明“可预测地选择 \(\rho_t\)”本身也救不了该构造。

S2 PDF pp.11–12 §3.5、命题 3 (21) 允许选定目标内在时间 \(m>0\)，按 \(m/\rho=r_\alpha\) **选一次 \(\rho\)**，所得整条边界仍同时有效；不是允许无代价地取各条边界的逐点下包络。固定 \(\rho\) 的边界在大 \(v\) 时为 \(\sqrt{v\log v}\) 阶，逐点优化则抹去了保证无限时域覆盖所需的增长因子。

## 可替换的有效构造

**正态混合方案。** 对题设全部有界适应过程，条件 Hoeffding 引理给
\[
\mathbb E_{t-1}e^{\lambda(X_t-\mu)}\le e^{\lambda^2/8}
\quad(\lambda\in\mathbb R).
\]
因此取 \(V_t=t/4\)，固定任意 \(\rho>0\)，使用 A 的 \(C_t^\rho\) 即有双尾总错误不超过 \(\alpha\) 的置信序列；不需 iid。这也对应 S1 PDF p.10 对条件有界增量的 sub-Gaussian 说明。

**真正使用 \(\widehat V_t\) 的经验 Bernstein 方案。** 本题预测器属于 \([0,1]\) 且可预测。采用
\[
\psi_E(\lambda)=-\log(1-\lambda)-\lambda,
\qquad0\le\lambda<1,
\]
即 S2 的尺度 \(c=1\)，不能用 \(\lambda^2/2\) 替代。给定总预算 \(\alpha\)，置 \(\delta=\alpha/2\)。例如预先固定 \((0,1)\) 上均匀混合，定义 \(u_\delta(v)\) 为方程
\[
\int_0^1e^{\lambda u_\delta(v)-\psi_E(\lambda)v}\,d\lambda
=\int_0^1e^{\lambda(u_\delta(v)+v)}(1-\lambda)^v\,d\lambda
=\delta^{-1}
\]
的唯一非负解。被积函数给出的积分关于 \(s\) 连续严格递增，在 \(s=0\) 时不超过 1，并随 \(s\to\infty\) 发散，故该定义成立。此方案是 S2 引理 2 与定理 4 的直接应用；也可采用该文 PDF p.30 命题 9 (64)–(66) 的 gamma-exponential 混合边界。

为直接验证一阶条件，记 \(Y_t=X_t-\mu\)、\(d_t=\widehat X_t-\mu\)、\(\xi_t=Y_t-d_t=X_t-\widehat X_t\in[-1,1]\)。对 \(\xi\ge-1\)、\(0\le\lambda<1\)，有
\[
e^{\lambda\xi-\psi_E(\lambda)\xi^2}\le1+\lambda\xi.
\]
可独立看出该标量不等式：对 \(z>-1\)，
\[
\frac{z-\log(1+z)}{z^2}=\int_0^1\frac{u}{1+uz}\,du
\]
（\(z=0\) 按连续延拓），右侧随 \(z\) 递减；代 \(z=\lambda\xi\ge-\lambda\) 并比较 \(z=-\lambda\) 即得。于是
\[
\mathbb E_{t-1}e^{\lambda Y_t-\psi_E(\lambda)\xi_t^2}
\le e^{\lambda d_t}\bigl(1+\lambda\mathbb E_{t-1}\xi_t\bigr)
=e^{\lambda d_t}(1-\lambda d_t)\le1.
\]
最后用 \(1-x\le e^{-x}\)，且 \(d_t\) 可预测。对 \(-X_t\) 和预测器 \(-\widehat X_t\) 重复论证，平方残差相同。因此 \(e^{\pm\lambda S_t-\psi_E(\lambda)\widehat V_t}\) 各为从 1 出发的非负超鞅。固定混合后分别用 Ville，每尾错误不超过 \(\delta\)；联合界给出
\[
C_t^{\rm EB}=\left[\bar X_t\pm\frac{u_{\alpha/2}(\widehat V_t)}t\right]\cap[0,1],
\qquad\Pr(\forall t\ge1:\mu\in C_t^{\rm EB})\ge1-\alpha.
\]
这正解释了 S2 p.35 (89)–(90) 如何使适应的经验量成为合法的 sub-exponential 内在时间；共同条件均值只用于把该文的 \(\mu_t\) 专门化为常数 \(\mu\)。

**多个混合参数与明确预算。** 对同一个已经合法的 sub-Gaussian 配对 \((S,V)\)，预先固定 \(\rho_0>0\)，令
\[
\rho_k=2^{k-1}\rho_0,\quad\alpha_k=\alpha2^{-k}\quad(k=1,2,\ldots),
\qquad \sum_{k\ge1}\alpha_k=\alpha.
\]
每一 \(\rho_k\) 使用双尾正态混合预算 \(\alpha_k\)。取所有相应置信区间的交集，即半径
\[
\frac1t\inf_{k\ge1}b_{\rho_k,\alpha_k}(V_t),
\]
则由可数联合界同时覆盖至少 \(1-\alpha\)。因为已有对全部 \(k,t\) 的共同好事件，事后按数据选择某个 \(k_t\) 也有效。这里的 \(\alpha_k\) 校正正是 C 所遗漏的选择代价。

## E 与可直接采用的修订结论

若 \(G=\{\forall t\ge1:\mu\in C_t\}\) 且 \(\Pr(G)\ge1-\alpha\)，那么在 \(\{\tau<\infty\}\) 上 \(G\subseteq\{\mu\in C_\tau\}\)。故任何几乎处处有限的停止时刻都有 \(\Pr(\mu\in C_\tau)\ge1-\alpha\)，无须 \(\mathbb E\tau<\infty\)。这是路径上的事件包含，无需对 \(\tau\) 使用可选抽样定理；事实上任意有限随机索引均享有这一推论。E 的前提不可由 B、C 的错误构造自动获得。

可替换原稿结论为：

> 在共同条件均值和有界观测下，固定精度的正态混合结合确定性内在时间 \(t/4\) 给出有效的非参数无限时域置信序列。使用在线平方预测残差时，应采用经条件期望验证的 sub-exponential 过程及相应经验 Bernstein 边界，并分配双尾错误预算。精度参数可针对预先选定的内在时间优化；若需同时使用多组精度，则须通过联合错误预算或固定的更高层混合加以校正。Howard 等人的两篇论文已提供这些一般框架与经验 Bernstein 置信序列。本次审查澄清了构造稿的条件与常数，并给出了直接经验替换的有限反例、逐时无校正调参的 LIL 反证及有效修复；这些内容不构成对全球首创性的判断。真正的同时覆盖保证可直接推出几乎处处有限停止时刻的覆盖率。

`checks.py` 的确定性积分、解析概率数值及精确有理数比较只作自查；反例、优化、LIL 与条件期望证明均已在正文给出。
