# 经验方差与混合调参的条件审查

**结论：A、E 成立；B、C、D 不成立。** 被审对象是本次构造的 `input/draft.tex`，不是来源论文的摘录。下述反例与错误均针对构造稿。本文使用本机提供的固定作者版原文，所有“页”均指 **PDF 从 1 起计的页序**，不指期刊页码；两份 PDF 的 SHA256 与输入清单一致。

来源作者均为 Steven R. Howard、Aaditya Ramdas、Jon McAuliffe、Jasjeet Sekhon：

- **S1**：[Time-uniform Chernoff bounds via nonnegative supermartingales，arXiv:1808.03204v7](https://arxiv.org/pdf/1808.03204v7)。期刊元数据：Probability Surveys 17 (2020), 257–317，[DOI](https://doi.org/10.1214/18-PS321)。核读 PDF 第 9–13 页。
- **S2**：[Time-uniform, nonparametric, nonasymptotic confidence sequences，arXiv:1810.08240v9](https://arxiv.org/pdf/1810.08240v9)。期刊元数据：Annals of Statistics 49(2) (2021), 1055–1080，[DOI](https://doi.org/10.1214/20-AOS1991)。核读下表、调参及自归一化证明相关原文。

记号约定：$X_t\in[0,1]$ 适应于 $(\mathcal F_t)$，$\mathbb E[X_t\mid\mathcal F_{t-1}]=\mu\in[0,1]$。令
$$
S_t=\sum_{i=1}^t(X_i-\mu),\quad \bar X_t=t^{-1}\sum_{i=1}^tX_i,\quad
\widehat X_1=1/2,\quad\widehat X_t=\bar X_{t-1}\ (t\ge2),\quad
\widehat V_t=\sum_{i=1}^t(X_i-\widehat X_i)^2.
$$
对 $0<\alpha<1,\rho>0,v\ge0$，边界是
$$
b_{\rho,\alpha}(v)=\sqrt{(v+\rho)\log\frac{v+\rho}{\alpha^2\rho}}.
$$
A 的额外前提为 $V$ 非减、可预测、$V_0=0$，且对所有实 $\lambda$、每个 $t\ge1$，
$$
\mathbb E_{t-1}e^{\lambda(X_t-\mu)}\le e^{\lambda^2(V_t-V_{t-1})/2}.\tag{SG}
$$

## 证据对照

| 原文定位 | 对象与假设 | 内在时间或方差量 | 尾部与概率 | 时间域及可比较结论 |
|---|---|---|---|---|
| S1 第 9–11 页，定义 1、式 (2.1)；第 12–13 页，定理 1、式 (2.7)–(2.10) | 适应的实过程对 $(S,V)$；对每个 $0\le\lambda<\lambda_{\max}$，须有非负超鞅 $L(\lambda)$ 支配 $\exp\{\lambda S-\psi(\lambda)V\}$，且 $L_0\le l_0$ | $V_0=0,V_t\ge0$；容许适应，不要求可预测；但必须验证上述支配关系 | 单尾；例如式 (2.7)：$\Pr(\exists t:S_t\ge a+bV_t\mid\mathcal F_0)\le l_0e^{-aD(b)}$，其中 $D(b)=\sup\{\lambda>0:\psi(\lambda)/\lambda\le b\}$ | 离散 $\mathbb N$ 或连续 $(0,\infty)$；定理是无限时域越界控制，不要求 iid |
| S2 第 10 页式 (14)、第 28 页命题 5、式 (51) | $(S,V)$ 与 $(-S,V)$ 均为 sub-Gaussian，即 $\psi_N(\lambda)=\lambda^2/2$ 的有证书过程对 | 同一个合格的 $V$，不是任取经验方差；固定 $\rho>0$ | 直接双尾，总错误 $\alpha$；一般 $l_0$ 时根号内为 $(v+\rho)\log[l_0^2(v+\rho)/(\alpha^2\rho)]$ | 全部整数 $t\ge1$，控制 $|S_t|$；本题 $l_0=1$ 时即 A 的边界 |
| S2 第 14 页定理 4、式 (23)；第 35 页式 (89)–(90) | $X_t\in[a,b]$；预测器 $\widehat X_t\in[a,b]$ 可预测；允许条件均值随时间变化 | $\sum_{i\le t}(X_i-\widehat X_i)^2$；用 sub-exponential $\psi_{E,c}$，$c=b-a$ | $u$ 为单尾错误 $\eta$ 的边界时，双尾错误至多 $2\eta$；总预算 $\alpha$ 应取 $\eta=\alpha/2$ | 全部整数 $t\ge1$；估计 $\mu_t=t^{-1}\sum_{i\le t}\mathbb E_{i-1}X_i$；共同均值只是特例 |

这里 $\psi_{E,c}(\lambda)=c^{-2}[-\log(1-c\lambda)-c\lambda]$，$0\le\lambda<1/c$（$c>0$）；见 S2 第 6 页。定义允许适应性，只是允许一种可测性，绝不自动赋予任意 $(S,V)$ 超鞅证书。S1 第 10 页还明确强调 sub-$\psi$ 是对过程对的条件。

## A：配方、交换积分与双尾常数

记 $L_t(\lambda)=\exp\{\lambda S_t-\lambda^2V_t/2\}$。由于 $\Delta V_t$ 对 $\mathcal F_{t-1}$ 可测，(SG) 给出
$$
\mathbb E_{t-1}L_t(\lambda)
=L_{t-1}(\lambda)e^{-\lambda^2\Delta V_t/2}
\mathbb E_{t-1}e^{\lambda(X_t-\mu)}\le L_{t-1}(\lambda),\qquad L_0(\lambda)=1.
$$
每个固定 $\lambda\in\mathbb R$ 都有非负超鞅。指数表达式对 $(\omega,\lambda)$ 联合可测，$F_\rho$ 为预先固定的概率分布；非负性允许条件 Tonelli 交换，故
$$
\mathbb E_{t-1}\!\int L_t\,dF_\rho\le\int L_{t-1}\,dF_\rho,
\qquad \mathbb EM_t^\rho\le1.
$$
后式同时保证混合量的可积性。这里直接混合显式指数过程，不需要额外选择一族不可测的支配超鞅。一般支配过程情形的乘积可测性条件见 S2 第 9 页引理 2、第 27–28 页式 (49)–(50)。

令 $q=V_t+\rho>0$，正态密度合并后配方为
$$
\lambda S_t-\frac q2\lambda^2
=-\frac q2\left(\lambda-\frac{S_t}q\right)^2+\frac{S_t^2}{2q}.
$$
因而
$$
M_t^\rho=\sqrt{\frac\rho{2\pi}}e^{S_t^2/(2q)}
\int_{\mathbb R}e^{-q(\lambda-S_t/q)^2/2}\,d\lambda
=\sqrt{\frac\rho q}e^{S_t^2/(2q)}.
$$
边界反演为
$$
M_t^\rho\ge\alpha^{-1}
\iff S_t^2\ge q[2\log(1/\alpha)+\log(q/\rho)]
\iff |S_t|\ge b_{\rho,\alpha}(V_t).
$$
Ville 不等式（S1 第 13 页引理 1、式 (2.11)）给出该越界事件概率至多 $\alpha$。正态分布混合整个实轴已同时处理正、负偏差，**无需再将 $\alpha$ 除以 2**。闭区间的失覆盖是严格越界，包含于上述事件；再截到 $[0,1]$ 不影响真实 $\mu$ 的包含关系。$\square$

## B：有限四步反例

取 $X_i$ 独立服从 $\operatorname{Bernoulli}(1/2)$，自然过滤，$\mu=1/2$，并固定
$$
\alpha=\frac1{16},\qquad\rho=\frac14,\qquad
E=\{X_1=X_2=X_3=X_4=0\}\cup\{X_1=X_2=X_3=X_4=1\}.
$$
严格使用题定预测器：在任一常值路径上，第一个残差平方是 $1/4$，此后预测值恰等于观测，故
$$
\widehat V_4=\frac14,\quad |S_4|=2,\quad
b_{1/4,1/16}^2(1/4)=\frac12\log512=\frac92\log2<4.
$$
这是解析严格不等式：$e^{3/4}>1+3/4+(3/4)^2/2=65/32>2$，所以 $\log2<3/4$，上式甚至小于 $27/8<4$。因此 $E$ 上错误区间在 $t=4$ 已排除 $\mu$，而
$$
\Pr(\exists t:\mu\notin C_t)\ge\Pr(E)
=2\left(\frac12\right)^4=\frac18>\frac1{16}=\alpha.
$$
这既非模拟，也非“尚未找到证明”。$\widehat V_t$ 一般不是可预测量，不能直接代入 A 的条件期望分解；即使放宽到 S1 的适应内在时间定义，仍缺少正确的 sub-Gaussian 证书。S2 第 18 页第 5 项本已讨论把预测残差平方直接塞入正态边界的 naive self-normalization 不能保证覆盖；本例独立给出题定预测器下的有限时间证明。$\square$

## C：逐点最小化会消掉无限时域所需的增长

令 $k=2\log(1/\alpha)>0$。当 $v>0$，置 $x=v/\rho$，则
$$
\frac{b_{\rho,\alpha}^2(v)}v=g(x):=(1+x^{-1})[k+\log(1+x)],\qquad
 g'(x)=\frac{x-\log(1+x)-k}{x^2}.
$$
函数 $h(x)=x-\log(1+x)$ 在 $x>0$ 严格递增，从 $0$ 增至 $\infty$；且 $g$ 在两端都趋于无穷。故唯一最小点 $x_\alpha>0$ 满足
$$
x_\alpha-\log(1+x_\alpha)=k,\qquad
\rho_*(v)=v/x_\alpha,\qquad
\inf_{\rho>0}b_{\rho,\alpha}(v)=\sqrt{(1+x_\alpha)v}.
$$
$v=0$ 时 $b^2=\rho k$，下确界为零但不取到，原稿的 argmin 在此为空。

仍取 iid $\operatorname{Bernoulli}(1/2)$，令 $R_i=2X_i-1$。这是满足 (SG) 的合法例子，$V_t=t/4$。写 $q_\alpha=1+x_\alpha$，逐时最小边界只是 $\sqrt{q_\alpha t}/2$。题目给定的经典 Rademacher LIL 说
$$
\limsup_{t\to\infty}\frac{\sum_{i\le t}R_i}{\sqrt{2t\log\log t}}=1\quad\text{a.s.}
$$
因 $\sqrt{2\log\log t}\to\infty$，几乎必然有无穷多个 $t$ 满足 $\sum_{i\le t}R_i>\sqrt{q_\alpha t}$。于是 $|S_t|$ 越过逐时最小边界无穷多次，**同时覆盖概率为零**。此处甚至没有随机的 $V$，问题仍存在。

S2 第 12 页命题 3、式 (21) 允许为预定目标内在时间 $m>0$ 选一个固定参数：$m/\rho=-W_{-1}(-\alpha^2/e)-1=x_\alpha$（本题 $l_0=1$）。这与上述微分一致。该命题比较不同固定边界在目标时间的紧度，不为逐时取下包络提供覆盖保证。$\square$

## 可替换的三个有效方案

**固定正态混合。** 在题定有界条件下，总可取 $V_t=t/4$ 和任一预先固定的 $\rho>0$，使用 A 的 $C_t^\rho$。理由是凸性给出 $\mathbb E_{t-1}e^{\lambda X_t}\le1-\mu+\mu e^\lambda$。函数 $f(\lambda)=\log(1-\mu+\mu e^\lambda)-\mu\lambda$ 满足 $f(0)=f'(0)=0$、$f''(\lambda)\le1/4$，故所有实 $\lambda$ 上 $f(\lambda)\le\lambda^2/8$，恰为 (SG)。端点 $\mu=0,1$ 时 $f\equiv0$。无须独立性或正态误差。

**确实使用 $\widehat V_t$ 的经验 Bernstein。** 取
$$
\psi_E(\lambda)=-\log(1-\lambda)-\lambda,\qquad0\le\lambda<1.
$$
预测器须对 $\mathcal F_{t-1}$ 可测且在 $[0,1]$ 内；本题初始化 $1/2$ 与过去平均值满足两者。令 $Y_t=X_t-\mu$、$\delta_t=\widehat X_t-\mu$，则 $Y_t-\delta_t\in[-1,1]$ 且 $\mathbb E_{t-1}Y_t=0$。为证明所需一步不等式，注意对 $\xi\ge-1$、$0<\lambda<1$，
$$
\lambda\xi-\log(1+\lambda\xi)
=(\lambda\xi)^2\int_0^1\frac{r}{1+r\lambda\xi}\,dr
\le(\lambda\xi)^2\int_0^1\frac r{1-r\lambda}\,dr
=\psi_E(\lambda)\xi^2.
$$
因此 $e^{\lambda\xi-\psi_E(\lambda)\xi^2}\le1+\lambda\xi$。应用于 $\xi=Y_t-\delta_t$，利用可预测性提出 $\delta_t$，有
$$
\mathbb E_{t-1}e^{\lambda Y_t-\psi_E(\lambda)(Y_t-\delta_t)^2}
\le e^{\lambda\delta_t}(1-\lambda\delta_t)\le1.
$$
$\lambda=0$ 显然成立。将 $(Y_t,\delta_t)$ 同时换为其负数得到另一尾；于是 $e^{\pm\lambda S_t-\psi_E(\lambda)\widehat V_t}$ 均是初值为 1 的超鞅。这也解释为何需要换 $\psi$，而不是只换方差符号；与 S2 第 35 页式 (89)–(90) 一致。

一个完全指定的边界是采用固定的均匀混合分布 $d\lambda$（$0\le\lambda<1$），令 $u_\eta(v)>0$ 为方程
$$
\int_0^1\exp\{\lambda u_\eta(v)-\psi_E(\lambda)v\}\,d\lambda
=\eta^{-1},\qquad \eta=\alpha/2
$$
的唯一根。积分在 $u=0$ 时至多为 1，对 $u$ 连续严格递增并趋于无穷，因此根存在唯一。条件 Tonelli 与 Ville 给每一尾预算 $\eta$；合并后
$$
C_t^E=[\bar X_t\pm u_{\alpha/2}(\widehat V_t)/t]\cap[0,1],\qquad
\Pr(\forall t\ge1:\mu\in C_t^E)\ge1-\alpha.
$$
这是 S2 引理 2 与定理 4 的直接实例，采用上述明确混合，未声称其常数最优；也可用原文第 30 页命题 9 的 gamma-exponential 边界。若条件均值随时间变化，同样的证明以 $\mathbb E_{t-1}X_t$ 代替 $\mu$，覆盖的是 $\mu_t$。

**多组正态混合参数。** 在 A 的合法 $(S,V)$ 上，预定 $\rho_j=2^{j-1}$、$\alpha_j=\alpha2^{-j}$，$j\ge1$，故 $\sum_j\alpha_j=\alpha$。令
$$
C_t^{\mathrm{multi}}=\bigcap_{j\ge1}
[\bar X_t\pm b_{\rho_j,\alpha_j}(V_t)/t]\cap[0,1].
$$
对所有 $(j,t)$ 作可数并集界，失覆盖至多 $\sum_j\alpha_j=\alpha$。因此也可根据数据逐时挑选任一 $j_t$，使用已分配预算 $\alpha_{j_t}$ 的区间。不能挑选后再把每组预算恢复成 $\alpha$。

## D、E 与可直接采用的修订结论

D 的三处定位均错误：S1 已处理非 iid 适应过程的无限时域越界；S2 的“正态”指一种混合选择，非要求数据正态；S2 定理 4 明确允许非共同均值。因此 B、C 既不构成有效新定理，也不能支持“首次”结论。

E 则直接来自事件包含关系。若 $G=\bigcap_{t\ge1}\{\mu\in C_t\}$ 且 $\Pr(G)\ge1-\alpha$，对任一几乎处处有限的正整数随机时间 $\tau$，
$$
G\cap\{\tau<\infty\}\subseteq\{\mu\in C_\tau\},\qquad
\Pr(\mu\in C_\tau)\ge1-\alpha.
$$
连停止时刻性质都不是这一方向所必需，更不需要 $\mathbb E\tau<\infty$；参见 S2 第 19 页引理 3。这里没有对无界停止时刻直接套可选停止期望等式。

**修订结论（可直接写入备忘录）：** 在有界、共同条件均值条件下，使用确定性内在时间 $t/4$ 与预先固定的正态混合精度，可得到非参数无限时域置信序列。预测残差平方和则须配合合格的 sub-exponential 指数过程及双尾错误预算，不能无条件代入同一正态边界。混合精度可以针对预定目标时间固定优化，或通过预分配错误预算的多参数方法选用；未经校正的逐时最小化会破坏同时覆盖。已建立的同时覆盖自动支持几乎处处有限的可选停止。上述构造建立在 Howard 等人的既有框架上；本次审查的内容是条件澄清、有限四步反例及逐时优化失败证明，不据两篇文献的核查宣称全球首创。

数值校验见 `checks.py` 与 `results/checks.json`；解析理由均已在本文给出。
