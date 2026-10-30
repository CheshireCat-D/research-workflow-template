# 经验方差、混合调参与可选停止：定理审查

审查对象是本次构造的 `draft.tex`；A–E 不是来源作者发表的主张。结论为：**A、E 成立；B、C、D 不成立。**下述页码全部是固定作者版 PDF 从 1 开始的页序，绝非期刊页码。

来源 S1：Howard、Ramdas、McAuliffe、Sekhon，*Time-uniform Chernoff bounds via nonnegative supermartingales*，Probability Surveys 17 (2020), 257–317，[DOI](https://doi.org/10.1214/18-PS321)，本次采用 [arXiv:1808.03204v7 PDF](https://arxiv.org/pdf/1808.03204v7)。来源 S2：同四位作者，*Time-uniform, nonparametric, nonasymptotic confidence sequences*，Annals of Statistics 49(2) (2021), 1055–1080，[DOI](https://doi.org/10.1214/20-AOS1991)，采用 [arXiv:1810.08240v9 PDF](https://arxiv.org/pdf/1810.08240v9)。本次读取本机两份原文及提取文本，不重新联网核验版本元数据，也不在交付目录复制全文。

| 结果及原文位置 | 对象、假设 | 内在时间 | 尾部及概率 | 时间域与可比较结论 |
|---|---|---|---|---|
| S1 定义 1，PDF 9–11 页，(2.1)–(2.2)；定理 1，12–13 页，(2.7)–(2.10) | 适应的零起点过程；每个 \(0\le\lambda<\lambda_{\max}\) 的指数过程须受初值不超过 \(l_0\) 的超鞅控制。无 iid 要求 | 适应、非负的 \(V\)；文中累积时间设定为非减。不能仅凭适应性认定某对 \((S,V)\) 合格 | 主定理为单尾；例如 \(P(\exists t:S_t\ge a+bV_t\mid\mathcal F_0)\le l_0e^{-aD(b)}\)，\(D(b)=\sup\{\lambda>0:\psi(\lambda)/\lambda\le b\}\) | 离散 \(\mathbb N\) 或连续 \((0,\infty)\)；无限时域的越线界，另外三种等价形式要求 CGF-like 条件 |
| S2 引理 2，PDF 9 页 (13)；命题 5，28 页 (51)，亦见10页 (14) | \(S\) 与 \(-S\) 对同一 \(V\) 均为 sub-Gaussian；\(\psi_N=\lambda^2/2\)，固定 \(\rho>0\) | 满足相应指数超鞅条件的 \(V\)，不必是实际方差；本题取 \(l_0=1\) | 全实轴正态混合直接给双尾总错误 \(\alpha\)，边界即 \(b_{\rho,\alpha}\) | 所有 \(t\ge1\)；不要求观测正态 |
| S2 定理 4，PDF 14 页 (23)；证明35页 (89)–(90) | \(X_t\in[a,b]\)，预测器 \(\widehat X_t\in[a,b]\) 且 \(\mathcal F_{t-1}\)-可测；目标 \(\mu_t=t^{-1}\sum E_{i-1}X_i\) | \(\sum(X_i-\widehat X_i)^2\)，确实是适应的经验量；须配 sub-exponential \(\psi_{E,c}\)，\(c=b-a\) | 每尾边界错误为 \(\delta\)，合并总错误 \(2\delta\)，故本题用 \(\delta=\alpha/2\) | 所有 \(t\ge1\)；无需共同均值、独立性或正态性 |

## A：配方、交换与反演

设 \(L_t(\lambda)=\exp\{\lambda S_t-\lambda^2V_t/2\}\)。可预测性使 \(\Delta V_t\) 在条件期望外提，(SG) 因而给出
\[
E_{t-1}L_t(\lambda)=L_{t-1}(\lambda)e^{-\lambda^2\Delta V_t/2}E_{t-1}e^{\lambda(X_t-\mu)}\le L_{t-1}(\lambda).
\]
对每个固定实数 \(\lambda\)，这是初值 1 的非负超鞅。有限实值的 \(S_t,V_t\) 使指数核联合可测，且非负，故条件 Tonelli 允许交换期望和固定概率分布 \(F_\rho\) 的积分。由 \(EM_t^\rho\le1\) 同时得到可积性；这里不是把随机选择的混合分布直接放入积分。一般支配超鞅的版本还须保证支配过程的联合可测性，见 S2 引理 2 及 PDF 27–28 页 (49)–(50)。

令 \(a=V_t+\rho>0\)，则
\[
\begin{aligned}
M_t^\rho
&=\sqrt{\frac\rho{2\pi}}\int_{\mathbb R}\exp\{-\tfrac a2\lambda^2+\lambda S_t\}\,d\lambda\\
&=\sqrt{\frac\rho{2\pi}}e^{S_t^2/(2a)}\int_{\mathbb R}\exp\{-\tfrac a2(\lambda-S_t/a)^2\}\,d\lambda\\
&=\sqrt{\frac\rho a}\,e^{S_t^2/(2a)}.
\end{aligned}
\]
由 S1 引理 1，PDF 13 页 (2.11)，\(P(\exists t:M_t^\rho\ge1/\alpha)\le\alpha\)。取对数反演：
\[
M_t^\rho\ge\alpha^{-1}
\iff \frac{S_t^2}{2a}\ge\log\alpha^{-1}+\tfrac12\log(a/\rho)
\iff |S_t|\ge\sqrt{a\log\frac a{\alpha^2\rho}}.
\]
混合已同时包含正负 \(\lambda\)，所以总双尾常数是 \(\alpha\)，不用再乘 2。闭区间失覆盖对应严格越线，是上述越线事件的子集；与 \([0,1]\) 相交不会删除真实 \(\mu\)。这证明 A。

## B：有限时间解析反例

取自然过滤，\(X_i\) 独立且服从 \(\mathrm{Bernoulli}(1/10)\)，\(\mu=1/10\)，固定 \(\alpha=1/10,\rho=1/4\)。在事件
\[
E=\{X_1=\cdots=X_{20}=0\}
\]
上，题设预测器严格给出 \(\widehat X_1=1/2\) 及 \(\widehat X_i=0\;(2\le i\le20)\)。因此
\[
\widehat V_{20}=1/4,\quad S_{20}=-2,\quad
b_{1/4,1/10}(1/4)=\sqrt{\tfrac12\log200}\approx1.627623631<2.
\]
最后一个严格不等式也可纯解析验证：\(200<2^8<e^8\)，所以 \(\log200<8\)。错误区间上端 \(b/20<1/10\)，故 \(E\) 必导致失覆盖。其概率为
\[
P(E)=(9/10)^{20}=\frac{12157665459056928801}{10^{20}}
\approx0.121576655>0.1=\alpha.
\]
单在时间 20 就已超标，足以否定同时覆盖。定义允许 \(V\) 适应，只说明可接受的可测性类别；它不自动提供 \((S,\widehat V)\) 所需的 \(\psi_N\) 指数控制。经验残差平方适用的 \(\psi_E\) 不能直接换成较小的 \(\lambda^2/2\)。

## C：逐时最小值的形状及无限时域反证

令 \(L=\log\alpha^{-2}>0\)，对 \(v>0\) 置 \(r=v/\rho\)，则
\[
\frac{b_{\rho,\alpha}(v)^2}{v}=f(r)=(1+1/r)[L+\log(1+r)],\qquad
f'(r)=\frac{r-L-\log(1+r)}{r^2}.
\]
函数 \(r-\log(1+r)\) 从 0 严格增到无穷，因为导数为 \(r/(1+r)>0\)。所以存在唯一 \(r_\alpha>0\) 满足
\[
r_\alpha-\log(1+r_\alpha)=L.
\]
两端 \(f\to\infty\)，故该点是唯一最小值，且
\[
\rho^*(v)=v/r_\alpha,\qquad
\inf_{\rho>0}b_{\rho,\alpha}(v)=\sqrt{(1+r_\alpha)v}.
\]
在 \(v=0\)，下确界为 0，但不在 \(\rho>0\) 上达到。

取 iid Rademacher \(R_i\)，\(X_i=(1+R_i)/2\)，则 \(\mu=1/2\)、\(S_t=\tfrac12\sum R_i\)。由有界变量的条件 Hoeffding 引理，\(V_t=t/4\) 满足 (SG)。逐时最小边界却仅为 \(\tfrac12\sqrt{(1+r_\alpha)t}\)。使用题目允许的经典命题
\[
\limsup_{t\to\infty}\frac{\sum_{i=1}^tR_i}{\sqrt{2t\log\log t}}=1\quad\text{a.s.},
\]
可知 \(\sum R_i/\sqrt t\) 上方无界，因而严格越过该边界无穷多次几乎必然，所得同时覆盖概率为 **0**。裁剪到 \([0,1]\) 不会恢复覆盖。

S2 PDF 12 页命题 3、(21)，证明见37页 (98)–(101)，允许为一个预定目标内在时间 \(m\) 选择固定 \(\rho=m/r_\alpha\)，随后使用同一条完整边界；它没有赋予逐时取下包络的免费保证。即使当前 \(V_t\) 是确定性的，沿时间重新优化仍是同时多重选择。

## 可直接使用的修正方案

**正态混合方案。**在原有有界性和共同条件均值条件下，条件 Hoeffding 引理给出对所有 \(\lambda\in\mathbb R\)
\[
E_{t-1}e^{\lambda(X_t-\mu)}\le e^{\lambda^2/8}.
\]
取确定性 \(V_t=t/4\)，预先固定任意 \(\rho>0\)，使用 A 的 \(C_t^\rho\) 即得置信水平 \(1-\alpha\) 的无限时域置信序列。S1 PDF 10 页关于有界增量的例子给出同一方差代理。

**真正使用经验方差的方案。**本题预测器取值于 \([0,1]\) 且可预测。应使用 S2 PDF 6 页的
\[
\psi_{E,c}(\lambda)=c^{-2}[-\log(1-c\lambda)-c\lambda],\quad 0\le\lambda<1/c,
\]
本题 \(c=1\)，简写 \(\psi_E(\lambda)=-\log(1-\lambda)-\lambda\)。令 \(Y_t=X_t-\mu\)、\(\delta_t=\widehat X_t-\mu\)，则 \(\xi_t=Y_t-\delta_t=X_t-\widehat X_t\ge-1\)。对 \(0<\lambda<1\)、\(\xi\ge-1\)，
\[
e^{\lambda\xi-\psi_E(\lambda)\xi^2}\le1+\lambda\xi.
\]
一个直接验证是置 \(z=\lambda\xi\ge-\lambda\)，利用
\[
\frac{z-\log(1+z)}{z^2}=\int_0^1\frac{s}{1+sz}\,ds
\le\int_0^1\frac{s}{1-s\lambda}\,ds=\frac{\psi_E(\lambda)}{\lambda^2},
\]
其中 \(z=0\) 按连续延拓。再因 \(E_{t-1}Y_t=0\)、\(\delta_t\) 可预测，得到 S2 (89)–(90) 的一步不等式：
\[
E_{t-1}e^{\lambda Y_t-\psi_E(\lambda)(X_t-\widehat X_t)^2}
\le e^{\lambda\delta_t}(1-\lambda\delta_t)\le1.
\]
故 \(e^{\lambda S_t-\psi_E(\lambda)\widehat V_t}\) 是初值 1 的非负超鞅。对 \(-X_t,-\widehat X_t\) 重复，平方残差不变，得到另一尾。

为给出完全明确、无需特殊函数的边界，预先令
\[
\lambda_j=2^{-(j+1)},\quad q_j=\frac1{(j+1)(j+2)},\quad j=0,1,\ldots,\qquad\sum_jq_j=1,
\]
\[
u_\alpha(v)=\min_{j\ge0}\frac{\psi_E(\lambda_j)v+\log[2/(\alpha q_j)]}{\lambda_j}.
\]
固定有限 \(v\) 时各项随 \(j\to\infty\) 趋于无穷，故最小值达到。Ville 对每条线、每尾的错误预算为 \(\alpha q_j/2\)；对 \(j\) 和两尾求并，给出
\[
P(\forall t\ge1:|S_t|<u_\alpha(\widehat V_t))\ge1-\alpha.
\]
于是 \([\bar X_t\pm u_\alpha(\widehat V_t)/t]\cap[0,1]\) 是有效经验 Bernstein 置信序列。这是定理 4 的一个显式实例；观测方差、自适应预测和无限时域均已包含。也可使用 S2 定理 4 推荐的 gamma-exponential 混合边界（PDF 30 页命题 9），每尾仍须分配 \(\alpha/2\)。

**多组正态混合参数。**预先给定可数个 \(\rho_k>0\) 和 \(w_k>0\)，\(\sum_kw_k\le1\)，例如 \(\rho_k=2^k\)、\(w_k=1/[(k+1)(k+2)]\)，\(k\ge0\)。对每组使用错误概率 \(\alpha w_k\) 的完整双尾边界。由并集界，
\[
P\left(\forall t:\ |S_t|\le\inf_k b_{\rho_k,\alpha w_k}(V_t)\right)\ge1-\alpha.
\]
因此可以在这些已分配错误预算的区间中选择，或者取它们的交；不能把所有边界各自都设为 \(\alpha\) 后直接取最小值。

## D、E 与备忘录修订结论

D 的两项前提都与原文相反。S1 定义 1 和主定理研究一般适应过程的时间一致界；S2 PDF 4–5 页明确以 \(\mu_t=t^{-1}\sum E_{i-1}X_i\) 为目标，既不要求独立性，也不要求共同均值。正态分布在正态混合中是调参分布，不是误差的必需分布。故无法由 B、C 推出所宣称的首创性。

E 可由事件包含直接证明。令 \(G=\bigcap_{t\ge1}\{\mu\in C_t\}\)，则在 \(\tau<\infty\) 上，\(G\subseteq\{\mu\in C_\tau\}\)，故概率至少 \(1-\alpha\)。实际上任何几乎处处有限的正整数值随机索引都成立，甚至不需停止时刻性质，更不需 \(E\tau<\infty\)。这不是对可选停止定理附加可积条件的调用，也不能补救未经证明的同时覆盖。

可替换原备忘录的结论：有界适应观测在共同条件均值下，以 \(t/4\) 为方差代理并固定混合精度，可由正态混合超鞅得到有效置信序列。经验预测误差平方应结合 sub-exponential 指数控制及双尾错误分配；多精度选择应预先分配错误预算。逐时无校正优化和直接经验方差替换均不成立。本次审查给出了条件核查、有限时间反例和有效修正；时间一致、非参数和经验 Bernstein 方法已见上述工作，不据两篇来源推断全球首创。已证明的同时覆盖自然蕴含任意几乎处处有限停止时刻的覆盖。

附带代码仅复核反例算术、最优参数方程、积分公式及若干数值点；解析证明和适用条件均已写在正文。没有把有限数值检查解释为定理证明。
