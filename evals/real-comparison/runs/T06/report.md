# 经验方差、混合调参与可选停止：定理审查

结论：**A、E成立；B、C、D不成立。** 这里审查的是提供的构造备忘录（`draft.tex` 中同名 A–E），不是来源作者发表的主张。以下页码均指给定作者版 PDF 的物理页序，从第一页计数，不能换成期刊页码。

本文沿用离散时间过滤 \((\mathcal F_t)\)，假设 \(X_t\in[0,1]\) 适应且 \(E[X_t\mid\mathcal F_{t-1}]=\mu\in[0,1]\)。记 \(\bar X_t=t^{-1}\sum_{i\le t}X_i\)、\(S_t=\sum_{i\le t}(X_i-\mu)\)，指定 \(\widehat X_1=1/2\)、\(\widehat X_t=\bar X_{t-1}\ (t\ge2)\)，以及 \(\widehat V_t=\sum_{i\le t}(X_i-\widehat X_i)^2\)。审查的正态混合边界为
\[
b_{\rho,\alpha}(v)=\sqrt{(v+\rho)\log[(v+\rho)/(\alpha^2\rho)]},
\quad 0<\alpha<1,\ \rho>0,\ v\ge0.
\]

来源：Howard、Ramdas、McAuliffe、Sekhon，S1 *Time-uniform Chernoff bounds via nonnegative supermartingales*，Probability Surveys 17 (2020), 257–317，[DOI](https://doi.org/10.1214/18-PS321)，本次使用 [arXiv:1808.03204v7 PDF](https://arxiv.org/pdf/1808.03204v7)；S2 同四位作者，*Time-uniform, nonparametric, nonasymptotic confidence sequences*，Annals of Statistics 49(2) (2021), 1055–1080，[DOI](https://doi.org/10.1214/20-AOS1991)，使用 [arXiv:1810.08240v9 PDF](https://arxiv.org/pdf/1810.08240v9)（封面日期为2022年8月9日）。已离线阅读相关正文及附录，并将关键定理同 PDF 文本直接核对；没有进行外部文献检索。

| 来源与定位 | 对象和实质条件 | 内在时间／方差量 | 尾部和概率 | 时间域及可比结论 |
|---|---|---|---|---|
| S1 PDF第9页 Definition 1、(2.1)；第12–13页 Theorem 1、(2.7)–(2.10) | 适应的实过程对 \((S,V)\)，零初值、\(V\ge0\)；每个 \(\lambda\in[0,\lambda_{\max})\) 须存在初值不超过 \(l_0\) 的超鞅支配 \(e^{\lambda S-\psi(\lambda)V}\)。不是只检查适应性 | 指定的适应过程 \(V\)；不必可预测，但须与 \(S,\psi\) 一起满足支配条件 | 主定理为单尾。例如 \(P(\exists t:S_t\ge a+bV_t\mid\mathcal F_0)\le l_0e^{-aD(b)}\)，其中 \(D(b)=\sup\{\lambda>0:\psi(\lambda)/\lambda\le b\}\) | \(t\in\mathbb N\) 或 \((0,\infty)\)；连续时间另有通常条件及 càdlàg 要求；无需 iid，统一控制越界 |
| S2 PDF第10页 (14)、第28页 Proposition 5、(51)；混合依据第9页 Lemma 2、(13) | \(S\) 与 \(-S\) 均对同一 \(V\) 为 sub-Gaussian；\(\psi_N=\lambda^2/2\)，预先固定 \(\rho>0\)，可测的混合超鞅 | 满足上述条件的 \(V\)；有界观测可取 \(t/4\)，并非任意经验方差 | 双尾总错误 \(\alpha\)，半径边界 \(\sqrt{(v+\rho)\log[l_0^2(v+\rho)/(\alpha^2\rho)]}\) | 全部 \(t\ge1\)；本题 \(l_0=1\) 就是 A 的边界 |
| S2 PDF第14页 Theorem 4、(23)；第35页 A.8、(89)–(90) | \(X_t\in[a,b]\) 适应；\(\widehat X_t\in[a,b]\) 可预测；估计 \(\mu_t=t^{-1}\sum_{i\le t}E_{i-1}X_i\)，不要求共同均值 | \(\sum_{i\le t}(X_i-\widehat X_i)^2\)，配 \(\psi_{E,c}(\lambda)=c^{-2}[-\log(1-c\lambda)-c\lambda]\)，\(c=b-a>0\)，\(0\le\lambda<1/c\) | 每尾使用越界概率 \(\delta\) 的 sub-exponential 边界 \(u_\delta\)，双尾总错误 \(2\delta\)；本题取 \(\delta=\alpha/2\) | 全部 \(t\ge1\)，半径 \(u_\delta(\widehat V_t)/t\)；不能把它改成未验证的正态混合边界 |

**A：成立，需固定同一个混合分布。** 记 \(L_t(\lambda)=\exp\{\lambda S_t-\lambda^2V_t/2\}\)。因为增量 \(V_t-V_{t-1}\) 对 \(\mathcal F_{t-1}\) 可测，(SG) 给出
\[
E_{t-1}L_t(\lambda)
=L_{t-1}(\lambda)e^{-\lambda^2\Delta V_t/2}
 E_{t-1}e^{\lambda(X_t-\mu)}\le L_{t-1}(\lambda).
\]
取有限实值 \(V_t\)，且 \(S_0=V_0=0\)。指数核对 \((\omega,\lambda)\) 联合可测、非负，故条件 Tonelli 允许交换积分与条件期望。初值为1，递推得混合过程可积、\(EM_t^\rho\le1\)，从而为非负超鞅。这正是 S2 PDF第27–28页 Lemma 2 证明、(49)–(50) 所需的可测性与积分条件；这里核是显式的，不需另选支配过程。

把正态密度写入积分，令 \(a=V_t+\rho>0\)，独立配方得
\[
\begin{aligned}
M_t^\rho
&=\sqrt{\rho/(2\pi)}\int_{\mathbb R}
 \exp\{-a\lambda^2/2+\lambda S_t\}\,d\lambda\\
&=\sqrt{\rho/(2\pi)}e^{S_t^2/(2a)}
 \int_{\mathbb R}e^{-a(\lambda-S_t/a)^2/2}\,d\lambda
=\sqrt{\rho/a}\,e^{S_t^2/(2a)}.
\end{aligned}
\]
反演阈值：
\[
\begin{aligned}
M_t^\rho\ge\alpha^{-1}
&\iff {S_t^2\over2a}+{1\over2}\log{\rho\over a}\ge\log\alpha^{-1}\\
&\iff S_t^2\ge a\log{a\over\alpha^2\rho}
\iff |S_t|\ge b_{\rho,\alpha}(V_t).
\end{aligned}
\]
S1 PDF第13页 Lemma 1、(2.11) 的 Ville 不等式给出整个时间域内越界概率至多 \(\alpha\)。混合支持为整个实轴，**这里的 \(\alpha\) 已经是双尾总预算**，无需再乘2。闭区间失覆盖事件用严格越界，包含于上式事件；与 \([0,1]\) 相交不排除真实的 \(\mu\)。

**B：不成立，有有限时刻的解析反例。** 定义允许 \(V\) 适应，不等于每个适应 \(V\) 都合格；必须证明相应指数过程的超鞅支配。\(\widehat V\) 一般也不可预测，所以不能沿用 A 中提出增量指数因子的步骤。

令 \(X_i\) 独立同分布为 Bernoulli\((1/10)\)，取自然过滤、\(\mu=1/10\)、\(\alpha=1/20\)、预先固定 \(\rho=1/4\)。在明确事件
\[
A_{20}=\{X_1=\cdots=X_{20}=0\}
\]
上，严格使用题定预测器有 \(\widehat X_1=1/2\)，其余 \(\widehat X_i=\bar X_{i-1}=0\)，故
\[
\widehat V_{20}=1/4,\qquad\bar X_{20}=0,\qquad |S_{20}|=2,
\qquad b_{1/4,1/20}(1/4)^2={1\over2}\log800<4.
\]
最后一个严格不等式无需小数：\(e^8>\sum_{k=0}^{6}8^k/k!>800\)。因此上端点为 \(\sqrt{\log800/2}/20<1/10\)，在 \(A_{20}\) 上必失覆盖，而且
\[
P(A_{20})=(9/10)^{20}
={12157665459056928801\over100000000000000000000}
>1/20.
\]
数值校验为 \(b=\sqrt{\log800/2}\approx1.828197436\)、\(P(A_{20})\approx0.121576655\)。这已经反驳固定 \(t=20\) 的覆盖，更反驳同时覆盖。S2 PDF第18页第5种“Naive SN”策略也明确指出把在线经验方差塞进正态混合公式不保证覆盖；上述有限事件及解析概率是本次审查的具体论证。

**C：不成立，即使内在时间完全合法且确定。** 对 \(v>0\)，令 \(q=v/\rho\)、\(L=\log\alpha^{-2}>0\)，则
\[
{b_{\rho,\alpha}(v)^2\over v}
=h(q):=(1+q^{-1})[\log(1+q)+L],\quad
h'(q)={q-\log(1+q)-L\over q^2}.
\]
函数 \(q-\log(1+q)\) 从0严格增加至无穷，故有唯一正根 \(q_\alpha\) 满足
\[
q_\alpha-\log(1+q_\alpha)=L.
\]
导数由负转正，两端 \(h\) 均趋无穷，所以
\[
\rho_*(v)=v/q_\alpha,\qquad
\inf_{\rho>0}b_{\rho,\alpha}(v)=\sqrt{(1+q_\alpha)v}.
\]
当 \(v=0\) 时，\(b_{\rho,\alpha}(0)^2=\rho L\)，下确界为0但没有正 \(\rho\) 实现它；此时原文的 argmin 本身为空。

取 iid Rademacher \(R_i\)，令 \(X_i=(1+R_i)/2\)、\(\mu=1/2\)、\(V_t=t/4\)。A 的条件对该确定性 \(V\) 成立。逐时最小边界却变成 \(\sqrt{(1+q_\alpha)t}/2\)。使用题目给定的经典 LIL 命题
\[
\limsup_{t\to\infty}{\sum_{i\le t}R_i\over\sqrt{2t\log\log t}}=1
\quad\text{a.s.},
\]
得到 \(\limsup S_t/\sqrt t=\infty\) 几乎必然，因而该 \(O(\sqrt t)\) 边界几乎必然被越过无穷次，**同时覆盖概率为0**。即使 \(\rho_t=t/(4q_\alpha)\) 是确定的，也不能把不同超鞅在不同时间的最优值拼成一个超鞅。

S2 PDF第12页 §3.5、Proposition 3、(21) 允许选定目标内在时间 \(m\)，再预先固定在该 \(m\) 处优化的 \(\rho\)。原文的“对固定 \(m\) 优化”不支持看过当前 \(V_t\) 后免费重选混合分布。上式 \(m/\rho=q_\alpha\) 与 (21) 完全一致。

**可替换的有效构造。** 第一种保留 A 的正态混合边界，在本题条件下取 \(V_t=t/4\) 和预先固定的 \(\rho>0\)。条件 Hoeffding 引理可直接验证：凸性给出
\[
E_{t-1}e^{\lambda(X_t-\mu)}
\le e^{-\lambda\mu}(1-\mu+\mu e^\lambda)\le e^{\lambda^2/8}.
\]
对于第二步，\(g(\lambda)=\log(1-\mu+\mu e^\lambda)-\mu\lambda\) 满足 \(g(0)=g'(0)=0\)，且 \(g''(\lambda)=p_\lambda(1-p_\lambda)\le1/4\)；二阶积分余项对正负 \(\lambda\) 均给出结论（\(\mu=0,1\) 为退化情形）。故 (SG) 成立，无需独立性或正态误差。使用 A 的 \(C_t^\rho\) 即得 \(1-\alpha\) 同时覆盖。

第二种确实使用题定 \(\widehat V_t\)，改用 S2 的经验 Bernstein 路线。令
\[
\psi_E(\lambda)=-\log(1-\lambda)-\lambda,
\quad 0\le\lambda<1,\qquad
Y_t=X_t-\mu,\quad d_t=\widehat X_t-\mu.
\]
题定预测器 \([0,1]\) 值且可预测，\(\xi_t=Y_t-d_t=X_t-\widehat X_t\in[-1,1]\)。为独立验证一阶条件不等式，利用绝对收敛的对数级数，对 \(|\xi|\le1\) 有
\[
\log(1+\lambda\xi)-\lambda\xi
\ge-\sum_{k\ge2}{\lambda^k|\xi|^k\over k}
\ge-\xi^2\sum_{k\ge2}{\lambda^k\over k}
=-\psi_E(\lambda)\xi^2.
\]
于是
\[
E_{t-1}e^{\lambda Y_t-\psi_E(\lambda)(Y_t-d_t)^2}
\le e^{\lambda d_t}E_{t-1}[1+\lambda(Y_t-d_t)]
=e^{\lambda d_t}(1-\lambda d_t)\le1.
\]
这里使用 \(E_{t-1}Y_t=0\) 与 \(d_t\) 可预测；最后由 \(1-x\le e^{-x}\) 得到。对 \(-Y_t,-d_t\) 重复论证，平方误差保持不变。故两个指数过程
\(e^{\pm\lambda S_t-\psi_E(\lambda)\widehat V_t}\) 都是初值1的非负超鞅。这也逐步说明 S2 PDF第35页 (89)–(90) 的条件为什么在本题成立。

下面给出一个无需特殊函数的明确边界，而不是仅声称“套用经验 Bernstein”。令 \(\lambda_k=2^{-k}\)、\(w_k=1/[k(k+1)]\)、\(k\ge1\)，定义
\[
u_\delta(v)=\inf_{k\ge1}
{\psi_E(\lambda_k)v+\log[1/(\delta w_k)]\over\lambda_k}.
\]
每条直线由 Ville 控制一尾错误 \(\delta w_k\)，且 \(\sum_{k\ge1}w_k=1\)。对每个有限 \(v\)，截距随 \(k\) 趋无穷，故下确界会达到；取并集即得一尾越界概率至多 \(\delta\)。因此一个有效的经验 Bernstein 置信序列是
\[
C_t^{\rm EB}=
[\bar X_t\pm u_{\alpha/2}(\widehat V_t)/t]\cap[0,1],
\qquad P(\forall t:\mu\in C_t^{\rm EB})\ge1-\alpha.
\]
这里每个方向、每个 \(k\) 的错误预算为 \(\alpha/[2k(k+1)]\)，两方向合计 \(\alpha\)。该构造属于 S2 Theorem 4 允许的 sub-exponential 边界；论文还给出更便于实践的 stitching 与 gamma-exponential 混合边界，而非本题错误的正态混合替换。

第三种允许在多组正态混合参数间自适应选择：预先取 \(\rho_j=2^{j-1}\)、\(\alpha_j=\alpha/[j(j+1)]\)，\(j\ge1\)，在合法的同一 \(V\) 上定义
\[
C_t^{\rm multi}=\bigcap_{j\ge1}
[\bar X_t\pm b_{\rho_j,\alpha_j}(V_t)/t]\cap[0,1]
=[\bar X_t\pm\inf_{j\ge1}b_{\rho_j,\alpha_j}(V_t)/t]\cap[0,1].
\]
每个 \(j\) 已是双尾总错误 \(\alpha_j\)，而 \(\sum_j\alpha_j=\alpha\)，故并集界给出同时覆盖至少 \(1-\alpha\)。也可以在每时刻根据数据选择任何一个 \(j_t\)：同一个“所有 \(j,t\) 均覆盖”的事件保证其合法。校正来自明确的预算，不能把所有 \(\alpha_j\) 都设成 \(\alpha\)。

**D：文献定位错误。** S1 Definition 1 与 Theorem 1 已覆盖适应过程和无限时域，S2 Theorem 4 直接允许非常数的平均条件均值及任意有界可预测预测器；“normal mixture”描述混合分布，并不要求观测误差正态。S2 PDF第3页 §1.1 还明确回顾更早的置信序列和经验 Bernstein 研究。故备忘录对两篇论文的限制描述均不符原文，B、C又为假，不能支持所谓首次结果。

**E：成立。** 设 \(G=\{\forall t\ge1:\mu\in C_t\}\)，在 \(\tau<\infty\) 的概率1事件上，\(G\subseteq\{\mu\in C_\tau\}\)，所以后者概率至少 \(1-\alpha\)。这是事件包含，不是对超鞅使用需要额外可积条件的可选停止定理，因而无须 \(E\tau<\infty\)。甚至任意几乎处处有限的随机选时也成立；对应 S2 PDF第19页 Lemma 3。

**供备忘录直接采用的修订结论：** 对有界适应观测及共同条件均值，条件 Hoeffding 界与预先固定的双侧正态混合分布给出非参数、无限时域的置信序列。在线平方预测误差可以作为经验 Bernstein 方法的内在时间，但需要相应的 sub-exponential 指数超鞅，不能直接沿用正态混合边界。正态混合参数可为预定目标时间调优，也可通过预分配错误预算在多组参数间选择；逐时无校正最小化会破坏无限时域覆盖。以上有效构造建立在已有文献的超鞅及混合框架上。本次审查补充了针对构造稿的有限时间解析反例、移动参数边界的精确最小化及 LIL 失效论证，不据此宣称全球首创。任一真正具有同时覆盖的方案，都在任意几乎处处有限停止时刻保持相同覆盖保证。

复核范围：手工证明、给定两篇全文的相关段落核对及附带代码的数值自查；未运行形式证明器，也未编译或改写原 TeX。`checks.py` 只校验反例数值、精确有理概率、最小化及一阶不等式的有限网格；它不替代上述证明。原 PDF、全文提取均留在输入缓存，交付物不复制全文。
