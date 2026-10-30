# 经验方差、混合调参与可选停止：构造备忘录审查

结论：**A、E 成立；B、C、D 不成立。** 审查对象是 `input/draft.tex` 的构造稿，以下错误不归属于来源论文。

来源均为 Howard、Ramdas、McAuliffe、Sekhon 的指定作者全文版。页码一律是 PDF 从 1 起数的物理页码，不是期刊页码。

- **S1**：*Time-uniform Chernoff bounds via nonnegative supermartingales*，Probability Surveys **17** (2020), 257–317，[DOI](https://doi.org/10.1214/18-PS321)，[arXiv:1808.03204v7 PDF](https://arxiv.org/pdf/1808.03204v7)。
- **S2**：*Time-uniform, nonparametric, nonasymptotic confidence sequences*，Annals of Statistics **49**(2) (2021), 1055–1080，[DOI](https://doi.org/10.1214/20-AOS1991)，[arXiv:1810.08240v9 PDF](https://arxiv.org/pdf/1810.08240v9)。此作者版首页日期为 2022 年，不能把它当作 2021 年刊本的逐页复制。

## 原文证据与可比较结论

下表取标量情形 $l_0=1$，$\beta$ 表示单尾预算；$T$ 为 S1 的离散或连续时间域。$\mu_t=t^{-1}\sum_{i\le t}\mathbb E_{i-1}X_i$。

| 原文定位 | 对象与假设 | 内在时间／方差量 | 尾数、概率与时间域 | 可比较结论 |
|---|---|---|---|---|
| S1 PDF 第 9–10 页，定义 1、式 (2.1)–(2.2) | 适应的 $(S,V)$；每个 $\lambda\in[0,\lambda_{\max})$ 的指数过程须被初值不超过 1 的超鞅支配 | $V_t\ge0$，允许适应性；定义本身没有证明某个候选量可用 | 定义是单尾基础条件，尚非覆盖结论；允许非 iid | 条件约束的是一对 $(S,V)$，不是“$V$ 适应”这一项 |
| S1 PDF 第 12–13 页，定理 1(a)、式 (2.7)；引理 1、式 (2.11) | 已满足 sub-$\psi$ 条件；固定 $a,b>0$ | 已获验证的 $V$ | 单尾 $\mathbb P(\exists t\in T:S_t\ge a+bV_t)\le e^{-aD(b)}$；无限时间域 | $D(b)=\sup\{0<\lambda<\lambda_{\max}:\psi(\lambda)/\lambda\le b\}$；主定理不是仅固定样本量界 |
| S2 PDF 第 10 页式 (14)、第 28 页命题 5、式 (51) | $S$ 与 $-S$ 都对同一 $V$ 满足 sub-Gaussian 条件；固定 $\rho>0$ | 对该对过程合法的 $V$，不要求一定是确定时间 | 双尾 $\mathbb P(\exists t\ge1:|S_t|\ge b_{\rho,\alpha}(V_t))\le\alpha$ | 正态是混合分布；无需观测误差服从正态 |
| S2 PDF 第 14 页定理 4、式 (23)；第 35 页证明、式 (89)–(90) | $X_t\in[a,b]$；$\widehat X_t\in[a,b]$ 可预测；$\psi_{E,b-a}$ 型有效边界 $u_\beta$ | $\sum_{i\le t}(X_i-\widehat X_i)^2$，适应、一般不可预测 | 每尾 $\beta$，双尾 $2\beta$；所有 $t\ge1$ | $|\bar X_t-\mu_t|<u_\beta(\widehat V_t)/t$；无需独立或共同均值 |

## A：混合计算及双尾常数

构造稿第 30–44 行的 SG 是充分条件。令 $Y_t=X_t-\mu$，对固定 $\lambda\in\mathbb R$ 置
$$
L_t(\lambda)=\exp\{\lambda S_t-\lambda^2V_t/2\}.
$$
由于 $\Delta V_t$ 是 $\mathcal F_{t-1}$ 可测量，
$$
\mathbb E_{t-1}L_t(\lambda)
=L_{t-1}(\lambda)e^{-\lambda^2\Delta V_t/2}
\mathbb E_{t-1}e^{\lambda Y_t}\le L_{t-1}(\lambda),\qquad L_0=1.
$$
因此它是非负超鞅。假定各过程取有限实值；指数表达式对 $(\omega,\lambda)$ 联合可测。固定、非数据依赖的概率分布 $F_\rho$ 允许使用非负函数的条件 Tonelli 定理：
$$
\mathbb E_{t-1}\int L_t(\lambda)dF_\rho(\lambda)
\le\int L_{t-1}(\lambda)dF_\rho(\lambda).
$$
初始积分为 1，故每时刻期望不超过 1，可积性随之得到，无须另外假设一个可积的统一包络。此处核查的正是 S2 引理 2（PDF 第 9 页）及其证明（第 27–28 页）的联合可测条件。

把正态密度写入积分，记 $q=V_t+\rho>0$，配方得到
$$
\begin{aligned}
M_t^\rho
&=\sqrt{\frac\rho{2\pi}}\int_{\mathbb R}
 e^{\lambda S_t-q\lambda^2/2}d\lambda\\
&=\sqrt{\frac\rho{2\pi}}e^{S_t^2/(2q)}
\int_{\mathbb R}e^{-\frac q2(\lambda-S_t/q)^2}d\lambda
=\sqrt{\frac\rho q}e^{S_t^2/(2q)}.
\end{aligned}
$$
因此
$$
M_t^\rho\ge\alpha^{-1}
\iff S_t^2\ge(V_t+\rho)
\left[\log\frac{V_t+\rho}{\rho}+2\log\frac1\alpha\right]
\iff |S_t|\ge b_{\rho,\alpha}(V_t).
$$
Ville 不等式给出越界概率至多 $\alpha$。正负 $\lambda$ 已在同一概率混合中，**双尾总预算就是 $\alpha$**，无须再乘 2。因为 $\mu\in[0,1]$，与 $[0,1]$ 相交不破坏覆盖。$\square$

## B：有限时间解析反例

第 49 行把定义允许的适应性误作超鞅支配的充分条件。取独立
$$
X_i\sim\operatorname{Bernoulli}(1/100),\quad
\mu=1/100,\quad\alpha=1/20,\quad\rho=1/4.
$$
在明确事件 $A_{200}=\{X_1=\cdots=X_{200}=0\}$ 上，指定预测器满足 $\widehat X_1=1/2$，其后全为零，故
$$
\widehat V_{200}=\tfrac14,\quad \bar X_{200}=0,\quad |S_{200}|=2,
$$
$$
b_{1/4,1/20}(1/4)^2
=\tfrac12\log\frac{1/2}{(1/20)^2(1/4)}
=\tfrac12\log800<4.
$$
错误区间的上端是 $\sqrt{\log800/2}/200<1/100$，真均值必被排除。其概率精确为
$$
\mathbb P(A_{200})=(99/100)^{200}>e^{-200/99}>e^{-5/2}>1/20.
$$
第一步用 $\log(1-x)>-x/(1-x)$；最后一步可由 $e<3$ 和 $e^{5/2}<9\sqrt3<20$ 得到。因此失覆盖概率严格超过标称值，且在固定时刻 200 已失败。数值只作核验：$\sqrt{\log800/2}\approx1.828197$，$(99/100)^{200}\approx0.133980$。这也与 S2 PDF 第 18 页第 5 项对 naive self-normalization 的讨论一致。$\square$

## C：下包络形状与无限时域失败

第 53–57 行将“对每个固定参数有效”换成了“逐时取最优参数也有效”。对 $v>0$，令 $x=v/\rho$、$a=\log(1/\alpha)>0$，则
$$
\frac{b_{\rho,\alpha}(v)^2}{v}
=f(x)=(1+x^{-1})\log\frac{1+x}{\alpha^2},\qquad
f'(x)=\frac{x-\log((1+x)/\alpha^2)}{x^2}.
$$
$h(x)=x-\log(1+x)-2a$ 满足 $h(0)=-2a<0$、$h'(x)=x/(1+x)>0$、$h(x)\to\infty$。且 $f(x)\to\infty$ 于两端，故存在唯一最小点 $x_\alpha>0$，并有
$$
x_\alpha-\log(1+x_\alpha)=2a,\quad
\rho^*(v)=v/x_\alpha,\quad
\inf_{\rho>0}b_{\rho,\alpha}(v)=c_\alpha\sqrt v,\quad
c_\alpha=\sqrt{1+x_\alpha}.
$$
在 $v=0$，下确界为 0 而无正参数达到它。S2 PDF 第 12 页命题 3、式 (21) 等价地写成
$$
1+x_\alpha=-W_{-1}(-\alpha^2/e).
$$
它允许针对**预先指定的目标内在时间 $m$** 选定 $\rho=m/x_\alpha$，随后使用同一条完整边界；没有给第 55 行的逐时重选提供覆盖保证。

取独立 Rademacher $R_i$，令 $X_i=(1+R_i)/2$。合法确定性时间为 $V_t=t/4$：
$$
\mathbb E_{t-1}e^{\lambda(X_t-1/2)}=\cosh(\lambda/2)\le e^{\lambda^2/8}.
$$
优化后的覆盖要求 $|\sum_{i\le t}R_i|\le c_\alpha\sqrt t$ 对所有 $t$ 成立。然而题设允许使用的经典 LIL 为
$$
\limsup_{t\to\infty}
\frac{\sum_{i\le t}R_i}{\sqrt{2t\log\log t}}=1\quad\text{a.s.}
$$
由于 $\sqrt{2\log\log t}\to\infty$，上述 $\sqrt t$ 边界几乎必然被无限次越过，故 $C_t^*$ 的同时覆盖率为 **0**。此例中调参甚至不依赖数据；时间重选本身就足以失效。$\square$

## 可直接采用的三个有效方案

**固定正态混合。** 在原有界共同条件均值假设下，条件 Hoeffding 引理给出
$$
\mathbb E_{t-1}e^{\lambda(X_t-\mu)}\le e^{\lambda^2/8},\quad\lambda\in\mathbb R.
$$
故用 $V_t=t/4$ 和任意预定 $\rho>0$ 代入 A 即得到 $1-\alpha$ 置信序列。S2 PDF 第 18 页第 1 项给出同一构造；有界性而非正态误差支持它。

**使用指定经验方差的 Bernstein 构造。** 取
$$
\psi_E(\lambda)=-\log(1-\lambda)-\lambda,\qquad0\le\lambda<1.
$$
预测器须是 $\mathcal F_{t-1}$ 可测且取值于 $[0,1]$；题设预测器满足这些条件。令 $Y_t=X_t-\mu$、$\delta_t=\widehat X_t-\mu$，则 $\xi_t=Y_t-\delta_t=X_t-\widehat X_t\ge-1$。以下给出一阶条件期望的实质核查。对 $u>-1$，
$$
\frac{u-\log(1+u)}{u^2}=\int_0^1\frac{r}{1+ru}dr
$$
（$u=0$ 按连续延拓）。右侧随 $u$ 递减。对 $u=\lambda\xi\ge-\lambda$ 因而有
$$
\lambda\xi-\log(1+\lambda\xi)\le\psi_E(\lambda)\xi^2,
\quad
 e^{\lambda\xi-\psi_E(\lambda)\xi^2}\le1+\lambda\xi.
$$
$\lambda=0$ 平凡成立。利用 $\delta_t$ 可预测、$\mathbb E_{t-1}Y_t=0$ 得
$$
\mathbb E_{t-1}e^{\lambda Y_t-\psi_E(\lambda)(Y_t-\delta_t)^2}
\le e^{\lambda\delta_t}(1-\lambda\delta_t)\le1.
$$
于是 $\exp\{\lambda S_t-\psi_E(\lambda)\widehat V_t\}$ 是初值为 1 的非负超鞅。对 $-Y_t,-\delta_t$ 同理，方差量不变。这对应 S2 PDF 第 35 页式 (89)–(90)，而非错误的二次 $\psi_N$ 替换。

为给出一个完整可用边界，固定 $F=\operatorname{Unif}(0,1)$，设
$$
m_E(s,v)=\int_0^1 e^{\lambda s-\psi_E(\lambda)v}d\lambda,
\qquad m_E(u_\beta(v),v)=1/\beta.
$$
对每个有限 $v\ge0$，$m_E(0,v)\le1$，它对 $s$ 连续严格递增且趋于无穷，故此正根存在唯一。固定混合与 Ville 不等式分别控制两尾。取 $\beta=\alpha/2$，得到
$$
C_t^{EB}=\left[\bar X_t\pm\frac{u_{\alpha/2}(\widehat V_t)}t\right]\cap[0,1],\qquad
\mathbb P(\forall t\ge1:\mu\in C_t^{EB})\ge1-\alpha.
$$
这是 S2 引理 2 加定理 4 的一个具体实例；也可用其命题 9 的 gamma-exponential 混合边界。一般情形估计的是 $\mu_t$，本题共同均值条件使它等于 $\mu$。$\square$

**多组正态混合参数。** 预定 $\rho_j=\rho_0 2^j$、$j\ge1$、$\rho_0>0$，分配
$$
\alpha_j=\frac{\alpha}{j(j+1)},\qquad
\sum_{j\ge1}\alpha_j=\alpha.
$$
使用合法同一 $V$，定义
$$
\widetilde C_t=\bigcap_{j\ge1}
\left(\left[\bar X_t\pm b_{\rho_j,\alpha_j}(V_t)/t\right]\cap[0,1]\right).
$$
可数并集界使所有参数、所有时刻同时有效的概率至少为 $1-\alpha$，因此此交集有效，且可按当时最小宽度选取其中一组。这给“事后选择”提供明确预算；不能把每组都设为同一个总预算 $\alpha$。$\square$

## D、E 与备忘录修订结论

**D 不成立。** S1 定义 1、定理 1 覆盖适应过程及无限时域；S2 PDF 第 4–5 页允许平均条件均值变化，第 14 页定理 4 是有界非参数结论。因此“仅 iid 固定样本量”“要求共同均值和正态误差”均与原文冲突，B、C 又不成立，无法支持首次主张。这里只核查指定两篇文献。

**E 成立。** 设 $G=\bigcap_{t\ge1}\{\mu\in C_t\}$。只要 $\tau$ 几乎处处取有限正整数，就有
$$
G\cap\{\tau<\infty\}\subseteq\{\mu\in C_\tau\},\qquad
\mathbb P(\mu\in C_\tau)\ge\mathbb P(G)\ge1-\alpha.
$$
这是事件包含，不需要对停止后的鞅应用可选停止定理，也无需 $\mathbb E\tau<\infty$；甚至任意有限随机时刻都可。参见 S2 PDF 第 19 页引理 3。此性质以已经成立的同时覆盖为前提，不能补救 B、C。$\square$

**可替换原稿的结论段：** 已有非负超鞅与混合方法提供非参数、无限时域的置信序列。对有界且共同条件均值恒定的过程，固定正态混合配合 $V_t=t/4$ 有效；采用可预测预测误差平方和时，应使用经条件期望验证的 sub-exponential 经验 Bernstein 构造，并为两尾分配错误预算。混合参数可针对预定目标时间校准，也可在分配总错误预算后并行使用多组参数；逐时无校正最小化不保留覆盖。本次审查给出错误经验替换的有限时间反例，以及逐时优化的 LIL 反证。有效同时覆盖允许任意几乎处处有限的可选停止。这些内容是对本构造稿的核查与修订，不构成全球优先权主张。

本稿的解析证明与原文定位已逐项核对。`checks.py` 仅核验有限反例的精确概率比较及标量极值数值；未以模拟代替证明，未修改原构造稿或复制来源论文全文。
