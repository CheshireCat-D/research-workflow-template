# 经验方差、混合调参与可选停止：构造备忘录审查

审查对象是本次构造的 `draft.tex`，不是已发表论文的主张。结论：**A、E 成立；B、C 不成立；D 的两项来源描述和首创结论均不成立。**以下页码一律是固定作者版 PDF 从 1 起数的页序，不能当作期刊页码。

来源 S1：Howard、Ramdas、McAuliffe、Sekhon，*Time-uniform Chernoff bounds via nonnegative supermartingales*，Probability Surveys 17 (2020), 257–317，[DOI](https://doi.org/10.1214/18-PS321)，[arXiv:1808.03204v7 PDF](https://arxiv.org/pdf/1808.03204v7)。来源 S2：同四位作者，*Time-uniform, nonparametric, nonasymptotic confidence sequences*，Annals of Statistics 49(2) (2021), 1055–1080，[DOI](https://doi.org/10.1214/20-AOS1991)，[arXiv:1810.08240v9 PDF](https://arxiv.org/pdf/1810.08240v9)。本审查使用随任务提供的这两个版本全文，PDF 分别为 63、48 页；关键 PDF 页与所附逐页提取相符。

## 1. 来源支持与命题判断

| 原文结果及位置 | 对象和实质假设 | 内在时间／方差量 | 尾部、错误概率、时间域及可比结论 |
|---|---|---|---|
| S1 定义 1，PDF p.9，式 (2.1)–(2.2)；定理 1，pp.12–13，式 (2.7)–(2.10) | 适应过程对 \((S,V)\)；对每个允许的 \(\lambda\)，指数过程必须被初值至多 \(l_0\) 的非负超鞅控制。不是只要求“适应” | \(V\ge0\)，可为适应量；具体过程对仍须验证 sub-\(\psi\) 条件 | 定义取 \(\lambda\ge0\)，控制上尾。定理 1(a) 给出 \(P(\exists t:S_t\ge a+bV_t)\le l_0e^{-aD(b)}\)；离散 \(t\in\mathbb N\) 或连续 \(t>0\)，不限 iid 或固定终点；双尾须另有反向条件并正确分配概率 |
| S2 正态混合，PDF p.10 式 (14)；p.28 命题 5、式 (51) | \(S\) 与 \(-S\) 均对同一个 \(V\) 满足 sub-Gaussian 条件，\(\psi_N(\lambda)=\lambda^2/2\)；预先固定 \(\rho>0\) | 满足上述条件的 \(V\)，不能任换经验量 | 直接双尾，\(P(\forall t\ge1:|S_t|<\sqrt{(V_t+\rho)\log[l_0^2(V_t+\rho)/(\alpha^2\rho)]})\ge1-\alpha\)。A 对应 \(l_0=1\) |
| S2 经验 Bernstein，PDF p.14 定理 4、式 (23)；证明 p.35 式 (89)–(90) | \(X_t\in[a,b]\) 适应；预测器 \(\widehat X_t\in[a,b]\) 可预测；目标可为 \(\mu_t=t^{-1}\sum E_{i-1}X_i\)，无须共同均值或正态误差 | \(\sum(X_i-\widehat X_i)^2\)；\(\psi_{E,c}(\lambda)=c^{-2}[-\log(1-c\lambda)-c\lambda]\)，\(c=b-a>0\)，\(0\le\lambda<1/c\) | 任意该 sub-exponential 单尾边界 \(u_\delta\)，对所有 \(t\ge1\) 得双尾错误率 \(2\delta\)。要总错误率 \(\alpha\)，取 \(\delta=\alpha/2\)；不等于直接套正态边界 |

**A 成立。**它的条件比抽象定义更具体，足以直接构造指数超鞅；下节独立给出积分和反演。

**B 不成立。**S1 PDF pp.9–10 明确 sub-\(\psi\) 是过程对的属性。定义许可 \(V\) 适应，并不担保任意适应的经验量都可配 \(\psi_N\)。此外 \(\widehat V_t\) 通常不是 \(\mathcal F_{t-1}\)-可测，A 的可预测前提本身已不能直接沿用。真正的修复需要改变 \(\psi\)，见第 5 节。

**C 不成立。**S2 PDF p.12 命题 3、式 (21) 是针对预定目标内在时间 \(m>0\)，选择一个固定 \(\rho\) 来优化整条边界。其导数推导见 PDF p.37 式 (98)–(101)。它不授权在每个时刻重新挑选当前最小边界。第 4 节说明即使调参路径完全确定，失覆盖也可达到概率 1。

**D 不成立。**S1 的定义及主定理已直接否定“仅 iid、固定样本量”的描述。S2 PDF pp.4–5 将目标定义为平均条件期望，并说明不要求独立或共同均值；其定理 4 只要求有界观测和可预测的有界预测器。“正态混合”指用于积分的混合分布，不能解释为观测误差正态。因此 B、C 也不能据此支撑首创定位。

**E 成立。**令 \(G=\bigcap_{t\ge1}\{\mu\in C_t\}\)。若 \(\tau\) 几乎处处有限且取正整数值，则
\[
\{\mu\notin C_\tau\}\subseteq G^c\quad\text{几乎处处},\qquad
P(\mu\notin C_\tau)\le\alpha.
\]
这里用的是事件包含，不是对 \(\tau\) 使用可选抽样定理；故无需 \(E\tau<\infty\)，甚至不必要求有限随机时刻是停止时刻。S2 PDF p.19 引理 3(a)–(c) 给出对应等价关系。该结论只能用于已有效的同时覆盖，不能挽救 B、C。

## 2. A 的配方计算、超鞅与双尾常数

取 \(S_0=0\)，假定 \(V_t\) 是有限实值、非减可预测过程。对固定 \(\lambda\in\mathbb R\)，令
\[
L_t(\lambda)=e^{\lambda S_t-\lambda^2V_t/2}.
\]
由于 \(\Delta V_t\) 在 \(\mathcal F_{t-1}\) 可测，(SG) 给出
\[
E_{t-1}L_t(\lambda)
=L_{t-1}(\lambda)e^{-\lambda^2\Delta V_t/2}
 E_{t-1}e^{\lambda(X_t-\mu)}\le L_{t-1}(\lambda).
\]
它非负且 \(L_0=1\)，迭代得 \(EL_t\le1\)，所以可积。混合分布必须预先固定；此处指数函数对 \((\omega,\lambda)\) 联合可测。非负性允许 Tonelli 及条件 Tonelli 交换，故
\[
E_{t-1}\int L_t\,dF_\rho=\int E_{t-1}L_t\,dF_\rho
\le\int L_{t-1}\,dF_\rho,
\qquad EM_t^\rho\le1.
\]
这也保证混合随机变量几乎处处有限。无需凭空假设统一的积分支配函数。S2 的一般混合论证另强调产品可测性：PDF p.9 引理 2、式 (13)，证明 pp.27–28 式 (49)–(50)。

写 \(A=V_t+\rho>0\)，正态密度中的 \(\rho\) 与指数中的 \(V_t\) 合并：
\[
\begin{aligned}
M_t^\rho
&=\sqrt{\frac\rho{2\pi}}\int_{\mathbb R}
 \exp\{\lambda S_t-A\lambda^2/2\}\,d\lambda,\\
\lambda S_t-A\lambda^2/2
&=-\frac A2\left(\lambda-\frac{S_t}{A}\right)^2
 +\frac{S_t^2}{2A},\\
M_t^\rho
&=\sqrt{\frac\rho{2\pi}}\sqrt{\frac{2\pi}{A}}
 e^{S_t^2/(2A)}
=\sqrt{\frac\rho A}e^{S_t^2/(2A)}.
\end{aligned}
\]
边界反演为
\[
M_t^\rho\ge\alpha^{-1}
\iff -\tfrac12\log(A/\rho)+\frac{S_t^2}{2A}\ge\log\alpha^{-1}
\iff S_t^2\ge A\log\frac{A}{\alpha^2\rho}
\iff |S_t|\ge b_{\rho,\alpha}(V_t).
\]
Ville 不等式给出 \(P(\exists t\ge1:M_t^\rho\ge1/\alpha)\le\alpha\)（S1 PDF p.13 引理 1、式 (2.11)）。一个对称混合已经同时控制两个符号，总错误预算就是 \(\alpha\)，不用再乘 2。闭区间的失覆盖事件是严格越界，包含于上述事件；与 \([0,1]\) 相交不改变真值 \(\mu\in[0,1]\) 的覆盖。

## 3. B 的有限时间解析反例

令 \(X_i\) 独立同分布为 Bernoulli\((1/10)\)，采用自然过滤；因此共同条件均值为 \(\mu=1/10\)，全部取值在 \([0,1]\)。固定
\[
\alpha=\frac1{20},\qquad \rho=\frac14,\qquad t=20,
\quad H=\{X_1=\cdots=X_{20}=0\}.
\]
严格采用题设预测器：在 \(H\) 上，首项平方误差为 \((0-1/2)^2=1/4\)，以后 \(\widehat X_i=\bar X_{i-1}=0\)，所以
\[
\widehat V_{20}=\frac14,\quad S_{20}=-2,\quad
b_{1/4,1/20}(1/4)^2=\frac12\log800<4.
\]
最后一个严格不等式可不用小数：\(e>5/2\)，故 \(e^8>(5/2)^8>800\)，即 \(\log800<8\)。于是错误区间的上端
\(\sqrt{\tfrac12\log800}/20<1/10=\mu\)，在 \(H\) 上必失覆盖，而
\[
P(H)=\left(\frac9{10}\right)^{20}
=\frac{12157665459056928801}{10^{20}}
>\frac1{20}.
\]
因此仅一个有限时刻的失覆盖率已严格超过 \(\alpha\)。作数值校验：\(\sqrt{\tfrac12\log800}\approx1.82819744\)，\((9/10)^{20}\approx0.12157665\)；解析证明不依赖这些近似。

## 4. C 的最小包络及无限时域失败

设 \(c=2\log(1/\alpha)>0\)。对 \(v>0\) 令 \(x=v/\rho\)，则
\[
\frac{b_{\rho,\alpha}(v)^2}{v}
=f(x):=(1+x^{-1})[c+\log(1+x)],\qquad
f'(x)=\frac{x-c-\log(1+x)}{x^2}.
\]
函数 \(g(x)=x-\log(1+x)\) 自 0 严格递增至无穷，因 \(g'(x)=x/(1+x)>0\)。唯一 \(x_\alpha>0\) 解
\[
x_\alpha-\log(1+x_\alpha)=c
\]
给出全局最小值（\(f\) 两端均趋无穷）：
\[
\rho^*(v)=v/x_\alpha,\qquad
\inf_{\rho>0}b_{\rho,\alpha}(v)=\sqrt{(1+x_\alpha)v}.
\]
等价地 \(1+x_\alpha=-W_{-1}(-\alpha^2/e)\)，与 S2 命题 3 的固定目标调参公式一致。对 \(v=0\)，\(b^2=c\rho\)，下确界是 0，但没有正的最优 \(\rho\)；故 C 的 argmin 在该点还未定义。

现在令 \(X_i=(1+R_i)/2\)，其中 \(R_i\) 独立等概率取 \(\pm1\)。条件矩母函数满足
\[
E e^{\lambda(X_i-1/2)}=\cosh(\lambda/2)\le e^{\lambda^2/8},
\]
例如由 \(\log\cosh u\le u^2/2\)（对 \(u\ge0\) 积分 \(\tanh u\le u\)，再用偶性）可得，故 \(V_t=t/4\) 合法。
最小包络变成 \(b^*(V_t)=\tfrac12\sqrt{(1+x_\alpha)t}\)。题许的经典 Rademacher LIL 是
\[
\limsup_{t\to\infty}\frac{\sum_{i\le t}R_i}{\sqrt{2t\log\log t}}=1
\quad\text{几乎必然}.
\]
由于 \(\log\log t\to\infty\)，\(\sum R_i>\sqrt{(1+x_\alpha)t}\) 几乎必然无穷多次发生。对应 \(S_t=\tfrac12\sum R_i>b^*(V_t)\)，所以 C 的无限时域失覆盖率为 **1**。此例的 \(\rho_t=t/(4x_\alpha)\) 完全确定，说明问题在于无校正地取整族边界的下包络，不限于“看数据”才会出错。

## 5. 可替换的三个有效方案

**固定正态混合。**在题设有界共同条件均值下，条件 Hoeffding 引理给出 \(E_{t-1}e^{\lambda(X_t-\mu)}\le e^{\lambda^2/8}\)，所有实 \(\lambda\) 均成立。取 \(V_t=t/4\) 和任意预先固定 \(\rho>0\)，使用 A 的区间即可。它只用有界性与条件均值，不要求独立、同分布或正态性。相应 Hoeffding 方差尺度可核对 S1 PDF p.10 的定义后说明。

**真正使用 \(\widehat V_t\) 的经验 Bernstein 方案。**题设的 \(\widehat X_1=1/2\)、\(\widehat X_t=\bar X_{t-1}\) 均在 \([0,1]\) 且可预测。取
\[
\psi_E(\lambda)=-\log(1-\lambda)-\lambda,
\qquad0\le\lambda<1.
\]
下面给出一阶条件期望的原因，而不是把“适应”当成充分理由。对 \(\xi\ge-1\)、\(0<\lambda<1\)，积分恒等式给出
\[
\lambda\xi-\log(1+\lambda\xi)
=(\lambda\xi)^2\int_0^1\frac{u}{1+u\lambda\xi}\,du
\le\xi^2\lambda^2\int_0^1\frac{u}{1-u\lambda}\,du
=\psi_E(\lambda)\xi^2.
\]
因此 \(e^{\lambda\xi-\psi_E(\lambda)\xi^2}\le1+\lambda\xi\)。设 \(Y_t=X_t-\mu\)、\(d_t=\widehat X_t-\mu\)，则 \(Y_t-d_t=X_t-\widehat X_t\in[-1,1]\)，\(d_t\) 可预测且 \(E_{t-1}Y_t=0\)。于是
\[
E_{t-1}e^{\lambda Y_t-\psi_E(\lambda)(Y_t-d_t)^2}
\le e^{\lambda d_t}(1-\lambda d_t)\le1.
\]
最后用 \(1-z\le e^{-z}\)。\(\lambda=0\) 时等号成立。以 \((-Y_t,-d_t)\) 重做同一计算，反向也成立。因此 \(e^{\pm\lambda S_t-\psi_E(\lambda)\widehat V_t}\) 都是初值 1 的非负超鞅；这对应 S2 PDF p.35 式 (89)–(90)。

可给出完全明确的边界，避免依赖某个未说明的经验方差公式。预先固定 \(\lambda_k=2^{-k}\)、\(w_k=1/[k(k+1)]\)（\(k\ge1\)，\(\sum w_k=1\)），定义
\[
u_\delta(v)=\min_{k\ge1}
\frac{\psi_E(\lambda_k)v+\log(1/(\delta w_k))}{\lambda_k},
\qquad 0<\delta<1.
\]
对固定有限 \(v\)，被取最小的项随 \(k\to\infty\) 趋无穷，故最小值确实取得。每个 \(k\) 的 Ville 越界概率至多 \(\delta w_k\)，对 \(k\) 求并得 \(u_\delta\) 为单尾 sub-exponential 一致边界。于是
\[
C_t^{\rm EB}=
\left[\bar X_t\pm\frac{u_{\alpha/2}(\widehat V_t)}{t}\right]\cap[0,1],
\qquad P(\forall t\ge1:\mu\in C_t^{\rm EB})\ge1-\alpha.
\]
两个符号各用 \(\alpha/2\)，每个符号内部的 \(k\) 再分配 \(\alpha w_k/2\)。这也是 S2 定理 4 的一个可直接实施的特例；原文 p.14 式 (24) 另给出闭式曲线边界，p.30 命题 9 给出 gamma-exponential 混合。

**多组正态混合参数。**在合法的同一个 \(V\) 下，预定 \(\rho_j>0\) 及 \(q_j>0\)，\(j\ge1\)、\(\sum_jq_j=1\)（例如 \(\rho_j=2^j\)、\(q_j=1/[j(j+1)]\)）。第 \(j\) 条双尾正态边界用错误预算 \(\alpha q_j\)。由可数并界，所有 \(j,t\) 同时满足相应界的概率至少 \(1-\alpha\)，因此
\[
B(v)=\inf_{j\ge1}b_{\rho_j,\alpha q_j}(v),\qquad
\left[\bar X_t\pm B(V_t)/t\right]\cap[0,1]
\]
是有效置信序列。下确界即使不取得也无碍：在共同好事件上 \(|S_t|\le b_j(V_t)\) 对所有 \(j\) 成立，故 \(|S_t|\le\inf_jb_j(V_t)\)。这允许按当前时刻挑较窄的一条，但预算必须随参数选择一起校正。也可把相应 \(M_t^{\rho_j}\) 按 \(q_j\) 再混合，再对得到的单个超鞅使用 Ville；同样不能把各条都用未分配的 \(\alpha\)。

## 可直接替换备忘录的修订结论

在有界适应观测与共同条件均值假设下，固定正态混合结合 \(V_t=t/4\) 给出非参数、无限时域有效的双尾置信序列。平方预测误差 \(\widehat V_t\) 则应配合 sub-exponential 指数补偿和正确的双尾错误预算；其有效性来自条件期望不等式，而非经验量的适应性。参数优化可针对预定内在时间选择固定参数；跨时刻或多参数选择需要预先分配错误预算或再混合。上述框架及经验 Bernstein 构造已有 S1、S2 的明确基础。本次审查补充了针对本构造稿的有限时间反例、逐时最优包络的 LIL 失败证明和有效替代方案，不据两篇来源的核查提出全球首创主张。有效的同时覆盖通过事件包含自动延伸至任意几乎处处有限停止时刻，无需停止时间的一阶矩条件。
