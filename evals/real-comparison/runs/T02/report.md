# 经验方差、混合调参与可选停止：定理审查

待审稿是本次构造的备忘录，不是下列论文的摘录。审查结论为：**A、E 成立；B、C、D 不成立。** B 有有限时间的解析反例，C 即使使用合法确定性方差过程，失覆盖概率仍可达到 1。

本文页码均为指定作者版 PDF 从封面起计的页序，**不是期刊页码**。核对材料为本地提供的 PDF 及提取文本，未开展外部检索；期刊题录采用任务给定信息。

- S1：Howard、Ramdas、McAuliffe、Sekhon，*Time-uniform Chernoff bounds via nonnegative supermartingales*，Probability Surveys 17 (2020), 257–317，[DOI](https://doi.org/10.1214/18-PS321)；全文使用 [arXiv:1808.03204v7](https://arxiv.org/pdf/1808.03204v7)，首页标示 2020 年 5 月 12 日。
- S2：同四位作者，*Time-uniform, nonparametric, nonasymptotic confidence sequences*，Annals of Statistics 49(2) (2021), 1055–1080，[DOI](https://doi.org/10.1214/20-AOS1991)；全文使用 [arXiv:1810.08240v9](https://arxiv.org/pdf/1810.08240v9)，首页日期为 2022 年 8 月 9 日。因此不能将这个作者版的编号、页序直接套在期刊版上。

**原文证据对照。** 下表中 (l_0=1) 对应本文标量构造，(mu_t=t^{-1}\sum_{i\le t}\mathbb E_{i-1}X_i)。

| 结果及定位 | 对象与必要假设 | 内在时间／方差量 | 尾部、概率、时间域与可比较结论 |
|---|---|---|---|
| S1 定义 1，PDF p.9，(2.1)–(2.2)；解释 p.10–11 | 适应的实值 ((S,V))，(S_0=V_0=0,V_t\ge0)；对每个 (0\le\lambda<\lambda_{\max})，指数过程须被初值不超过 (l_0) 的超鞅控制 | 可适应；并非任取一个适应过程都符合定义 | 定义本身不是覆盖定理；通常考察上尾；须对具体的 ((S,V,\psi)) 验证 |
| S1 定理 1(a)，PDF p.12，(2.7)；Ville 引理 1，p.13，(2.11) | 上述 sub-(\psi) 条件；无需 iid | 同一个已验证的 (V) | (\Pr(\exists t\in T:S_t\ge a+bV_t\mid\mathcal F_0)\le l_0e^{-aD(b)})，(D(b)=\sup\{\lambda>0:\psi(\lambda)/\lambda\le b\})；单尾，全离散或连续时域；双尾需另合并 |
| S2 正态混合，PDF p.10，(14)；命题 5，p.28，(51) | (S) 与 (-S) 均 sub-Gaussian，(\psi_N(\lambda)=\lambda^2/2)，固定 (\rho>0) | 同一个合法 (V)，不必等于经验方差 | (u(v)=\sqrt{(v+\rho)\log[l_0^2(v+\rho)/(\alpha^2\rho)]})；直接双尾，(\Pr(\forall t\ge1:|S_t|<u(V_t))\ge1-\alpha) |
| S2 经验 Bernstein，定理 4，PDF p.14，(23)；证明 p.35，(89)–(90) | (X_t\in[a,b])，预测器可预测且取值于 ([a,b])；估计一般的 (\mu_t)，无需独立、共同均值或正态误差 | (\sum_{i\le t}(X_i-\widehat X_i)^2)，实际为 sub-exponential，尺度 (c=b-a) | 任意相应单尾统一边界 (u_\delta) 给出 (\Pr(\forall t:|\bar X_t-\mu_t|<u_\delta(\widehat V_t)/t)\ge1-2\delta)；全 (t\ge1)。总误差为 (\alpha) 时取 (\delta=\alpha/2) |

**A：成立，双尾常数无需再乘 2。** 记 (L_t(\lambda)=e^{\lambda S_t-\lambda^2V_t/2})。由于 (\Delta V_t) 可预测，(SG) 给出
\[
\mathbb E_{t-1}L_t(\lambda)
=L_{t-1}(\lambda)e^{-\lambda^2\Delta V_t/2}
 \mathbb E_{t-1}e^{\lambda(X_t-\mu)}\le L_{t-1}(\lambda).
\]
对每个实数 (\lambda)，这是初值为 1 的非负可积超鞅。(S,V) 为有限实值适应过程时，显式指数函数对 ((\omega,\lambda)) 联合可测。固定、与数据无关的概率测度 (F_\rho) 下，非负性允许条件 Tonelli 交换积分与条件期望；即使各 (\lambda) 的零测例外不同，Fubini 也保证积分后的不等式几乎处处成立。因此 (M^\rho=\int L(\lambda)dF_\rho) 是超鞅，且 (M_0=1,\mathbb E M_t\le1)。S2 的引理 2（PDF p.9，(13)；证明 p.27–28，(49)–(50)）也明确要求混合时的乘积可测性。

配方直接给出（此处 (s=S_t,v=V_t)）
\[
\begin{aligned}
M_t^\rho
&=\sqrt{\frac\rho{2\pi}}\int_{\mathbb R}
 \exp\{\lambda s-(v+\rho)\lambda^2/2\}\,d\lambda\\
&=\sqrt{\frac\rho{2\pi}}e^{s^2/[2(v+\rho)]}
 \int_{\mathbb R}\exp\!\left\{-\frac{v+\rho}{2}
 \left(\lambda-\frac{s}{v+\rho}\right)^2\right\}d\lambda\\
&=\sqrt{\frac\rho{v+\rho}}e^{s^2/[2(v+\rho)]}.
\end{aligned}
\]
边界反演为
\[
M_t^\rho\ge\alpha^{-1}
\iff \frac{S_t^2}{2(V_t+\rho)}
\ge\log\alpha^{-1}+\frac12\log\frac{V_t+\rho}{\rho}
\iff |S_t|\ge b_{\rho,\alpha}(V_t).
\]
Ville 不等式控制上述越界事件概率不超过 (\alpha)。正负 (\lambda) 已在同一个概率混合中，故这是总双尾误差 (\alpha)，不是每尾 (\alpha)。闭区间失覆盖对应严格越界，是该事件的子集；与 ([0,1]) 相交不损害对真实 (\mu\in[0,1]) 的覆盖。

**B：不成立，且指定预测器下有有限反例。** 取 iid (X_i\sim\mathrm{Bernoulli}(1/10))，自然过滤，(\mu=1/10,\alpha=1/20,\rho=1/4)。在
\[
E=\{X_1=\cdots=X_{20}=0\}
\]
上，指定预测器依次为 (1/2,0,\ldots,0)，故
\[
\widehat V_{20}=1/4,\quad S_{20}=-2,\quad
b_{1/4,1/20}(1/4)^2=\tfrac12\log800<4.
\]
于是错误区间上端 (b_{1/4,1/20}(1/4)/20<1/10=\mu)，必然失覆盖。而
\[
\Pr(E)=(9/10)^{20}=0.12157665459056928801>1/20,
\]
严格超过标称错误率；精确整数比较是 (20\cdot9^{20}>10^{20})。这已经推翻同时覆盖，也推翻第 20 时刻的边际保证。

错误发生在把“定义允许适应的 (V)”当成“任何适应的 (V) 都有合法超鞅控制”。此外，(\widehat V_t) 一般不具可预测性，不能直接代入 A 的证明。S1 PDF p.10 强调 sub-(\psi) 是一对 ((S,V)) 的属性；p.11 的适应性说明并未免除指数超鞅义务。S2 定理 4 使用的 (\psi_E) 也不是 (\psi_N)。

**C：不成立，逐点下包络在无限时域失效。** 令 (L=\log\alpha^{-2}>0)。对 (v>0)，置 (x=v/\rho)，有
\[
\frac\partial{\partial\rho}b_{\rho,\alpha}(v)^2
=\log\frac{1+x}{\alpha^2}-x.
\]
函数 (x-\log(1+x)) 从 0 严格增至无穷，故存在唯一 (x_\alpha>0) 满足
\[
x_\alpha-\log(1+x_\alpha)=L.
\]
当 (\rho\downarrow0) 或 (\rho\uparrow\infty) 时平方边界均趋无穷，因此唯一全局最优值为
\[
\rho^*(v)=v/x_\alpha,\qquad
\inf_{\rho>0}b_{\rho,\alpha}(v)=\sqrt{(1+x_\alpha)v}.
\]
在 (v=0)，下确界为 0，但不被任何 (\rho>0) 取得，原稿的 argmin 此处为空。

取 iid Rademacher (R_i)，令 (X_i=(1+R_i)/2)，则 (S_t=\tfrac12\sum_{i\le t}R_i)，且 (V_t=t/4) 合法：(\mathbb E e^{\lambda(X_i-1/2)}=\cosh(\lambda/2)\le e^{\lambda^2/8})。题给经典 LIL 为
\[
\limsup_{t\to\infty}\frac{\sum_{i\le t}R_i}{\sqrt{2t\log\log t}}=1
\quad\text{a.s.}
\]
而优化边界仅为 (\sqrt{(1+x_\alpha)t}/2)，其相对 LIL 尺度的比值为
\(\sqrt{(1+x_\alpha)/(2\log\log t)}\to0\)。因此正向越界几乎必然发生，甚至无穷多次，所得同时覆盖概率为 0。

S2 PDF p.12，命题 3、(21)，允许为一个**预先指定的目标内在时间 (m)** 选择固定 (\rho=m/x_\alpha)，并保持这条边界在全部时间有效；没有允许每次重新最小化后免费选取整族边界的下包络。固定参数边界增长为 (\sqrt{v\log v})，逐时重调却删去了维持同时控制所需的增长。

**可替换的有效构造。** 其一，在原有有界、共同条件均值假设下，取确定的 (V_t=t/4) 和预先固定的 (\rho>0)，直接使用 A 的 (C_t^\rho)。条件 Hoeffding 界为
\[
\mathbb E_{t-1}e^{\lambda(X_t-\mu)}\le e^{\lambda^2/8},\qquad\lambda\in\mathbb R.
\]
一个简短证明是：条件对数矩母函数 (g) 满足 (g(0)=g'(0)=0)，其二阶导数是指数倾斜后仍支撑于 ([0,1]) 的变量方差，不超过 (1/4)。故
\(g(\lambda)=\lambda^2\int_0^1(1-r)g''(r\lambda)dr\le\lambda^2/8\)。这不要求正态分布或独立性；也与 S1 PDF p.10 的有界增量例及 p.26 表 3 的 Hoeffding 行相符。

其二，保留原指定预测器与 (\widehat V_t)，改用
\[
\psi_E(\lambda)=-\log(1-\lambda)-\lambda,\quad0\le\lambda<1.
\]
所有预测器均须为 (\mathcal F_{t-1})-可测且落在 ([0,1])；本稿预测器符合。令 (Y_t=X_t-\mu,\delta_t=\widehat X_t-\mu,\xi_t=Y_t-\delta_t\in[-1,1])。下面补足一阶条件期望论证。对 (u=\lambda\xi>-1)，
\[
u-\log(1+u)=u^2\int_0^1\frac{r}{1+ru}\,dr
\le u^2\int_0^1\frac{r}{1-r\lambda}\,dr
=\psi_E(\lambda)\xi^2.
\]
所以 (e^{\lambda\xi-\psi_E(\lambda)\xi^2}\le1+\lambda\xi)，进而
\[
\mathbb E_{t-1}e^{\lambda Y_t-\psi_E(\lambda)(Y_t-\delta_t)^2}
\le e^{\lambda\delta_t}(1-\lambda\delta_t)\le1.
\]
这里使用 (\mathbb E_{t-1}Y_t=0)、(\delta_t) 可预测及 (1-z\le e^{-z})；(\lambda=0) 直接成立。替换 (Y,\delta) 为其相反数得到另一尾，同一 (\widehat V_t) 可用。这正是 S2 PDF p.35，(89)–(90) 的机制。

例如预先在 ((0,1)) 上取均匀混合，对 (\delta\in(0,1)) 定义 (u_\delta(v)) 为下式关于 (s) 的唯一正根：
\[
\int_0^1e^{\lambda s-\psi_E(\lambda)v}\,d\lambda=1/\delta.
\]
该积分对有限 (v\ge0) 连续、严格递增于 (s)，在 (s=0) 不超过 1，且随 (s\to\infty) 趋于无穷，故定义良好。两侧混合分别是初值为 1 的非负超鞅。Ville 加并合界给出
\[
C_t^{EB}=[\bar X_t\pm u_{\alpha/2}(\widehat V_t)/t]\cap[0,1],\qquad
\Pr(\forall t\ge1:\mu\in C_t^{EB})\ge1-\alpha.
\]
这是一条实际使用观测预测误差平方和的经验 Bernstein 方案；上述均匀混合是此处给出的具体选择，不能误称为 S2 的正态混合或其命题 9 的 gamma 混合。数值求根可用于计算，覆盖证明不依赖数值模拟。

其三，若要同时使用多组正态混合参数，预先指定 (\rho_k=\rho_0 2^k\ (k=0,1,\ldots))，分配 (w_k=2^{-k-1})，使 (\sum_kw_k=1)。在合法同一个 (V) 上定义
\[
C_t^{multi}=\bigcap_{k\ge0}
 [\bar X_t\pm b_{\rho_k,\alpha w_k}(V_t)/t]\cap[0,1].
\]
每个 (k) 已具有总双尾错误率 (\alpha w_k)，所以全部 (k,t) 同时覆盖的概率至少为 (1-\sum_k\alpha w_k=1-\alpha)。因此也允许逐时选择任意 (k_t) 并报告其带有该预算的区间；不能将预算重新设为每组 (\alpha)。

**D、E 与可直接替换的结论。** D 的文献叙述与 S1 定理 1 及 S2 PDF p.4 的一般条件均值目标直接冲突。“正态混合”描述的是对指数参数的混合分布，不是正态误差假设。E 则正确：在事件 (G=\{\forall t\ge1:\mu\in C_t\}) 上，任意几乎处处有限的正整数值随机时间 (\tau) 都满足 (\mu\in C_\tau)，于是
\[
\Pr(\mu\notin C_\tau)\le\Pr(G^c)\le\alpha.
\]
此处无需可选停止定理，也无需 (\mathbb E\tau<\infty)；停止时刻条件甚至比这一事件包含论证所需更强。这只适用于已经成立的同时覆盖，不能挽救 B、C。

可直接写入备忘录：已有的非负超鞅框架提供了非参数、时间一致的序贯推断方法。固定正态混合边界适用于满足双向 sub-Gaussian 条件的合法方差过程；对有界观测，可取确定性 (t/4)。若使用可预测预测器产生的平方预测误差和，应采用相应的 sub-exponential 经验 Bernstein 构造，并分配双尾错误预算。混合参数可以为预定目标时间优化，或通过明确的多组错误预算容许选择。本次审查给出了两种不合法替换的解析反例及相应修正版；这些是对构造备忘录的核查结果，不构成对已有序贯方法的首次发明声明。

实际验证包括指定原文相关定义、定理与证明段落核对、上述手工推导，以及随附代码对反例概率与优化常数的数值校验。未运行形式证明器、未编译原 TeX，也未作超出两篇给定论文的全面文献检索；原始输入保持不变。
