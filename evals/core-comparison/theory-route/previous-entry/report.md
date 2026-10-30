# 经验方差、混合调参与可选停止：定理条件审查

审查对象是本次构造的备忘录及其 A–E，不是两篇论文的已发表主张。结论是：**A、E 成立；B、C、D 不成立。** B 有有限时间解析反例；C 即使用确定性合法内在时间也会几乎必然失覆盖。

## 1. 来源身份与证据表

两文作者均为 Steven R. Howard、Aaditya Ramdas、Jon McAuliffe、Jasjeet Sekhon。本次使用固定作者全文版本，以下页码均为 **PDF 从 1 开始的页序，不是期刊页码**：

- **S1**：[arXiv:1808.03204v7 全文](https://arxiv.org/pdf/1808.03204v7)，63 页；*Time-uniform Chernoff bounds via nonnegative supermartingales*，Probability Surveys 17 (2020), 257–317，[DOI](https://doi.org/10.1214/18-PS321)。
- **S2**：[arXiv:1810.08240v9 全文](https://arxiv.org/pdf/1810.08240v9)，48 页；*Time-uniform, nonparametric, nonasymptotic confidence sequences*，Annals of Statistics 49(2) (2021), 1055–1080，[DOI](https://doi.org/10.1214/20-AOS1991)。

两份 PDF 的 SHA-256 与给定清单一致；下表所引关键页的缓存文本已与 PDF 实际提取逐页对照。只交付来源定位、审查和必要公式，不复制全文。

| 原文位置 | 对象与条件 | 内在时间／方差量 | 尾部、概率与时间域 | 可比较结论 |
|---|---|---|---|---|
| S1，PDF 9–10 页，定义 1、式 (2.1)；12 页，定理 1(a)、式 (2.7) | 适应的实过程对 \((S,V)\)，初值 0，\(V\ge0\)；每个 \(\lambda\in[0,\lambda_{\max})\) 的指数过程须被初值至多 \(l_0\) 的非负超鞅控制 | \(V\) 可适应，但必须连同 \(S\) 满足支配条件；不能任意替换 | 原式为右尾；\(\Pr(\exists t:S_t\ge a+bV_t\mid\mathcal F_0)\le l_0e^{-aD(b)}\)，\(D(b)=\sup\{\lambda>0:\psi(\lambda)/\lambda\le b\}\)；离散 \(t\in\mathbb N\) 或符合正则条件的连续 \(t>0\) | 不要求 iid，给出无限时域直线边界；左尾须另核查 \(-S\) |
| S2，PDF 28 页，命题 5、式 (51)；10 页，式 (14) | \(S\) 与 \(-S\) 均为 sub-Gaussian，\(\psi_N(\lambda)=\lambda^2/2\)，同一 \(V\) | 满足上述条件的 \(V\)，不必是观测经验方差；本任务标量取 \(l_0=1\) | 直接双尾，总错误率 \(\alpha\)；全部 \(t\ge1\) | \(\Pr(\forall t:|S_t|<b_{\rho,\alpha}(V_t))\ge1-\alpha\)，\(\rho>0\) 固定 |
| S2，PDF 14 页，定理 4、式 (23)；35 页，证明、式 (89)–(90) | \(X_t\in[a,b]\) 适应；任意 \([a,b]\) 值可预测器；不要求共同条件均值，更不要求正态误差 | \(\sum_{i\le t}(X_i-\widehat X_i)^2\)，配 sub-exponential 边界，尺度 \(c=b-a\) | 单尾边界错误率 \(\delta\)，双尾总错误率 \(2\delta\)；全部 \(t\ge1\) | 覆盖目标 \(\mu_t=t^{-1}\sum_{i\le t}\mathbb E_{i-1}X_i\)；本任务 \(\mu_t=\mu\)。取 \(\delta=\alpha/2\) 得 \(1-\alpha\) |

**定义与证书必须区分。** S1 定义 1 允许 \(V\) 适应，仅是对象的可测性条件；式 (2.1) 的超鞅支配才是浓缩结论的依据。S1 PDF 10 页还明确强调该条件施加在过程对 \((S,V)\) 上。S2 PDF 5 页定义 1、式 (4) 同样保留这一要求。

## 2. A：配方、积分交换与双尾常数

假设 (SG)，且 \(S_t,V_t\) 为有限实随机变量。令
\[
L_t(\lambda)=\exp\{\lambda S_t-\lambda^2V_t/2\},\qquad L_0=1.
\]
由于 \(\Delta V_t\) 可预测，(SG) 给出
\[
\mathbb E_{t-1}L_t(\lambda)
=L_{t-1}(\lambda)e^{-\lambda^2\Delta V_t/2}
  \mathbb E_{t-1}e^{\lambda(X_t-\mu)}\le L_{t-1}(\lambda).
\]
故对每个实 \(\lambda\)，\(L(\lambda)\) 是非负、可积超鞅。对固定且不依赖观测的概率分布 \(F_\rho\) 积分；指数表达式对 \((\omega,\lambda)\) 联合可测，条件 Tonelli 对非负函数成立，因此
\[
\mathbb E_{t-1}\!\int L_t\,dF_\rho
=\int\mathbb E_{t-1}L_t\,dF_\rho
\le\int L_{t-1}\,dF_\rho,\quad \mathbb E M_t^\rho\le1.
\]
这是需要核查的积分交换条件；不要求先找一个对所有实 \(\lambda\) 共用的零测集。相应原理见 S2 PDF 9 页引理 2、式 (13)，以及 PDF 27–28 页式 (49)–(50) 的乘积可测性论证。

写 \(a=v+\rho>0\)，逐项配方得
\[
\begin{aligned}
M^\rho(s,v)
&=\sqrt{\frac\rho{2\pi}}\int_{\mathbb R}
 e^{\lambda s-a\lambda^2/2}\,d\lambda\\
&=\sqrt{\frac\rho{2\pi}}e^{s^2/(2a)}
 \int_{\mathbb R}e^{-\frac a2(\lambda-s/a)^2}\,d\lambda\\
&=\sqrt{\frac\rho a}e^{s^2/(2a)}.
\end{aligned}
\]
所以
\[
M^\rho(s,v)\ge\alpha^{-1}
\iff\frac{s^2}{2a}\ge\log\alpha^{-1}+\tfrac12\log(a/\rho)
\iff |s|\ge\sqrt{a\log\frac a{\alpha^2\rho}}.
\]
Ville 不等式给 \(\Pr(\exists t:M_t^\rho\ge1/\alpha)\le\alpha\)。这里一次对整个实轴的正态混合已同时处理正、负尾，**总错误率就是 \(\alpha\)，不再乘 2**。取闭区间并截到 \([0,1]\) 不损失覆盖，故 A 正确；这也匹配 S2 命题 5。

## 3. B：有限时间解析反例

令 \(X_i\) iid Bernoulli\((1/10)\)，自然过滤，\(\mu=1/10\)，固定
\(\alpha=1/20,\rho=1/4,n=20\)。考虑明确事件
\[
E=\{X_1=\cdots=X_{20}=0\}.
\]
在该事件上，严格使用题设预测器：\(\widehat X_1=1/2\)，其余 \(\widehat X_i=0\)。于是
\[
\widehat V_{20}=1/4,\quad \bar X_{20}=0,\quad S_{20}=-2,
\quad b_{1/4,1/20}(1/4)^2=\tfrac12\log800<4.
\]
最后一个严格不等式可由 \(e>8/3\)、\((8/3)^8>800\) 推出。故错误区间在 \(E\) 上的上端点为 \(b/20<1/10=\mu\)，必然失覆盖。而
\[
\Pr(\exists t:\mu\notin C_t)\ge\Pr(E)
=(9/10)^{20}>1/20=\alpha,
\]
其中严格比较等价于整数不等式 \(20\cdot9^{20}>10^{20}\)。数值核对为
\(\sqrt{\log(800)/2}\approx1.8281974357<2\)，
\((9/10)^{20}\approx0.1215766546>0.05\)。这直接否定 B，不是以证明缺失或模拟代替反例。\(\widehat V\) 通常不可预测，但更根本的问题是该过程对没有获得正态 \(\psi_N\) 的有效证书。

## 4. C：逐时优化将同时覆盖降为零

记 \(L=2\log(1/\alpha)>0\)。对 \(v>0\)，令 \(q=v/\rho>0\)，则
\[
b_{\rho,\alpha}(v)^2
=v(1+q^{-1})[L+\log(1+q)],
\quad
\frac d{dq}\frac{b^2}v
=\frac{q-L-\log(1+q)}{q^2}.
\]
函数 \(q-\log(1+q)\) 从 0 严格增至无穷，故存在唯一 \(q_\alpha>0\) 满足
\[
q_\alpha-\log(1+q_\alpha)=L.
\]
导数在此点由负变正，因而
\[
\rho^*(v)=v/q_\alpha,\qquad
\inf_{\rho>0}b_{\rho,\alpha}(v)=\sqrt{(1+q_\alpha)v}.
\]
在 \(v=0\) 时 \(b^2=\rho L\)，下确界为 0，但没有正的最小化参数；因此 C 在此点连 argmin 都不存在。

再令 \(X_i=(1+R_i)/2\)，其中 \(R_i\) 为题设允许引用的 iid Rademacher 变量。此时 \(\mu=1/2\)，\(S_t=\frac12\sum_{i\le t}R_i\)，而 \(V_t=t/4\) 满足 (SG)。优化后的覆盖要求
\[
\left|\sum_{i\le t}R_i\right|\le\sqrt{(1+q_\alpha)t}\quad\text{对所有 }t.
\]
使用经典命题
\(\limsup_{t\to\infty}\sum_{i\le t}R_i/\sqrt{2t\log\log t}=1\) 几乎必然：因 \(\log\log t\to\infty\)，上式阈值几乎必然被正向越过无穷多次。因此 **C 的无限时域同时覆盖概率为 0**。失败甚至不需要随机调参，\(\rho_t=t/(4q_\alpha)\) 已是确定性序列。

S2 PDF 12 页命题 3、式 (21)，及 PDF 37 页式 (98)–(101)，是在预先选定的目标内在时间 \(m\) 处优化，然后使用对应的一个固定 \(\rho=m/q_\alpha\) 形成整条有效边界。它没有授权把不同固定参数的有效边界逐时取未经校正的下包络。

## 5. 可直接采用的三个有效方案

**正态混合。** 在原有 \([0,1]\) 有界性与共同条件均值下，条件 Hoeffding 引理给
\[
\mathbb E_{t-1}e^{\lambda(X_t-\mu)}\le e^{\lambda^2/8}
\quad(\lambda\in\mathbb R).
\]
例如由凸性先上界为 \(e^{-\lambda\mu}(1-\mu+\mu e^\lambda)\)；其对数在零点的值、一阶导数均为零，二阶导数为倾斜 Bernoulli 方差、至多 \(1/4\)，两次积分即得结论。故取 \(V_t=t/4\) 和任意预先固定 \(\rho>0\)，应用 A 就得到有效双尾 \(1-\alpha\) 置信序列。S1 PDF 10 页也给出了有界增量对应的 sub-Gaussian 内在时间。

**使用题设 \(\widehat V_t\) 的经验 Bernstein 方案。** 采用 S2 的
\[
\psi_{E,c}(\lambda)=c^{-2}[-\log(1-c\lambda)-c\lambda],
\quad 0\le\lambda<1/c,\ c>0.
\]
本题 \(c=1\)，写 \(\psi(\lambda)=-\log(1-\lambda)-\lambda\)。预测器必须取值于 \([0,1]\) 且 \(\mathcal F_{t-1}\)-可测；题设的初值和过去均值均满足。

一阶条件不等式可独立验证。对 \(z\ge-1\)、\(0\le\lambda<1\)，
\[
\lambda z-\log(1+\lambda z)
=\lambda^2z^2\int_0^1\frac{r}{1+r\lambda z}\,dr
\le z^2[-\log(1-\lambda)-\lambda].
\]
因此 \(e^{\lambda z-\psi(\lambda)z^2}\le1+\lambda z\)。令
\(Y_t=X_t-\mu\)，\(d_t=\widehat X_t-\mu\)，则
\(z=Y_t-d_t=X_t-\widehat X_t\in[-1,1]\)，\(d_t\) 可预测且 \(\mathbb E_{t-1}Y_t=0\)，从而
\[
\mathbb E_{t-1}e^{\lambda Y_t-\psi(\lambda)(X_t-\widehat X_t)^2}
\le e^{\lambda d_t}(1-\lambda d_t)\le1.
\]
对 \(-Y_t,-d_t\) 同理。于是 \(e^{\pm\lambda S_t-\psi(\lambda)\widehat V_t}\) 分别为非负超鞅。这与 S2 PDF 35 页式 (89)–(90) 一致。

给出一个完全确定的可用边界：选 S2 PDF 30 页命题 9 的 gamma-exponential 混合，在其参数 \(c=\rho=1\) 时密度为
\[
f(\lambda)=\frac{e^\lambda}{e-1},\quad0<\lambda<1.
\]
令 \(u_\delta(v)>0\) 为唯一解
\[
\frac1{e-1}\int_0^1 e^{\lambda[s+v+1]}(1-\lambda)^v\,d\lambda
=\delta^{-1},\qquad s=u_\delta(v),\ v\ge0.
\]
积分在有限 \(s,v\ge0\) 时有限，关于 \(s\) 连续严格递增，在零点至多为 1，并在 \(s\to\infty\) 时发散，故根确实存在且唯一。它就是相应的一侧混合边界。两尾各分配 \(\delta=\alpha/2\)，得到
\[
\left[\bar X_t\pm\frac{u_{\alpha/2}(\widehat V_t)}t\right]\cap[0,1],
\qquad
\Pr(\forall t:\mu\text{ 在区间内})\ge1-\alpha.
\]
这里必须改变 \(\psi\) 和边界，不能沿用 B 中的正态边界。此方案是 S2 定理 4 的实例。

**多组混合参数。** 在满足 A 的同一过程对上，预先选
\(\rho_k=2^k\)、\(w_k=2^{-(k+1)}\)、\(\alpha_k=\alpha w_k\)，\(k=0,1,\ldots\)。使用半径
\[
r_t=\frac1t\inf_{k\ge0}b_{\rho_k,\alpha_k}(V_t).
\]
每条固定边界的双尾错误率至多 \(\alpha_k\)，可数并合界给
\(\Pr(\exists t,k:|S_t|>b_{\rho_k,\alpha_k}(V_t))\le\sum_k\alpha_k=\alpha\)。因此交集区间仍同时有效；观测后可以选择较窄者，代价已由明确的错误预算支付。

## 6. D、E 与可直接替换的修订结论

**D 错误。** S1 的定义与主定理已经覆盖非 iid、适应过程及无限时域；S2 PDF 4–5 页明确允许变化的平均条件均值 \(\mu_t\)，14 页定理 4 在有界、非正态条件下就给出经验 Bernstein 置信序列。“正态混合”描述混合测度，并非观测误差必须正态。B、C 已被否定，不能支持所声称的首次贡献。

**E 正确。** 若 \(G=\bigcap_{t\ge1}\{\mu\in C_t\}\) 且 \(\Pr(G)\ge1-\alpha\)，则对几乎处处有限的整数值 \(\tau\)，
\(G\cap\{\tau<\infty\}\subseteq\{\mu\in C_\tau\}\)。所以结论直接由事件包含得到，无需 \(\mathbb E\tau<\infty\) 或可选停止定理；事实上该推论对任意几乎处处有限的可测整数随机时刻均成立。

> 修订结论：在有界适应观测和共同条件均值下，固定参数的正态混合可结合 \(V_t=t/4\) 给出无限时域置信序列。若使用过去信息构造的预测平方误差 \(\widehat V_t\)，应采用 sub-exponential 证书及相应经验 Bernstein 边界，并为两尾分配错误概率。未经校正的逐时混合参数最优化不保留同时覆盖；预先指定多组参数并分配总错误预算则有效。以上构造属于 Howard 等既有时间一致浓缩与置信序列框架；本次审查的内容是条件核对、解析反例和有效修订，不构成全球首创性声明。已证明的同时覆盖可直接用于几乎处处有限的随机停止时刻。

附带代码只核对显式数值、微分公式的数值一致性和标量不等式的有限网格；上述数学结论来自正文论证，未运行形式化证明器。
