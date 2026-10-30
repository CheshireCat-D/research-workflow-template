# T-CS-01 数学任务与评分键独立审查

审查日期：2026-10-29。审查角色为设计者、执行者之外的只读核验者。依据仅为指定的 `public/task.md`、`public/draft.tex`、`private/rubric.json`、`private/independent-derivation.md`、`private/source-location-map.md`，以及本地固定 S1 arXiv:1808.03204v7、S2 arXiv:1810.08240v9 的 PDF/TXT。未读 memory、任何 SKILL.md、个人技能包或执行者答案；未修改输入、评分键、来源及冻结文件。另由一个隔离子审查者只读检查 task/rubric 的评分义务与替代方案开放性。

## 审查结论与需要先对齐的项目

核心判定 **A 真、B 假、C 假、D 假、E 真（正整数索引）正确**；A 的混合常数、B 的严格有限时间反例、C 的优化及 LIL 失效、EB 修复、E 不需要可积停止时间，均通过独立推导核验。没有发现要求推翻参考数学答案的错误。下列设计问题应在正式冻结或评分前处理：

1. **评分义务有一处公开任务与私有 rubric 不完全一致。** `task.md:54` 是“若允许多组混合参数，说明一个有明确错误预算的有效方法”，属于条件要求；`rubric.json:56` 却无条件配置 3 分给多 rho 网格/固定 rho 混合方案。一个只给固定单 rho、明确限制事后调参的正确修复，可以满足公开条件句，却可能损失这 3 分。建议二选一：公开任务明确强制“另外给出一个多组参数的有效错误预算方案”；或评分键允许“限制为预先固定单 rho 并解释原因”的回答取得对应分数。此处属于评分公平性对齐问题，不是理论错误。
2. **来源定位表存在一行中的两处页码笔误。** `source-location-map.md:12`：S2 Definition 2 与 (6) 在 **PDF p5**，不是 p6；(2) 在 **PDF p2**，不是 p4–5。应改为“p4 (3)；p5 Definition 1/(4)–(5)、Definition 2/(6)；p6 五类 psi 定义”。正确写 p5/(6) 的执行者不得因私有定位表的错误被扣分。
3. **E 的索引域应明写。** 公开稿只定义了 t>=1 的 C_t，随后说“任意几乎处处有限停止时刻”。若停止时刻允许取 0，则 C_0 未定义。应写成 `tau ∈ {1,2,...}, tau<∞ a.s.`，或者先定义 C_0。该端点不推翻 E 的实质结论；评分键和独立推导已使用“正整数索引”这一正确解释。

全部要求的设计文件和两个固定版本来源均存在；未遇到缺失的必要输入。本报告没有重新冻结任何文件。

## A：积分、交换与双尾常数

令 L_t(lambda)=exp{lambda S_t-lambda^2 V_t/2}。对固定实 lambda，Delta V_t 为 F_{t-1} 可测，由 (SG) 得

\[
\mathbb E_{t-1}L_t(\lambda)
=L_{t-1}(\lambda)e^{-\lambda^2\Delta V_t/2}
\mathbb E_{t-1}e^{\lambda(X_t-\mu)}
\le L_{t-1}(\lambda),\quad L_0(\lambda)=1.
\]

这里指数关于 (omega,lambda) 联合可测：S_t、V_t 可测，指数对 lambda 连续。固定概率先验 F_rho 与非负条件 Tonelli 给

\[
\mathbb E_{t-1}\int L_t\,dF_\rho
=\int\mathbb E_{t-1}L_t\,dF_\rho
\le\int L_{t-1}\,dF_\rho.
\]

积分初始为 1，且无条件期望至多 1，故适合 Ville。不是任意观测依赖先验均可这样交换。

独立完成配方，Gaussian precision 为 rho：

\[
\sqrt{\rho/(2\pi)}\int_{\mathbb R}
e^{\lambda s-(v+\rho)\lambda^2/2}\,d\lambda
=\sqrt{\frac\rho{v+\rho}}
e^{s^2/[2(v+\rho)]},
\]

因为指数等于
`-(v+rho)(lambda-s/(v+rho))^2/2+s^2/[2(v+rho)]`。解 M>=1/alpha 得

\[
|s|\ge\sqrt{(v+\rho)\log\frac{v+\rho}{\alpha^2\rho}}.
\]

同一个混合同时整合正负 lambda，所以 **总双尾错误为 alpha**，不能再把 alpha/2 强制套在 A 上。闭区间只使严格失覆盖事件更小，截断到 [0,1] 不排除真均值。A 无实质问题。

来源支持：S1 PDF p9 Definition 1/(2.1)–(2.2)，p13 Lemma 1/(2.11)，p15/(2.12)–(2.15)；S2 PDF p9 Lemma 2/(13)，p27–28/(49)–(50)，p10/(14)，p28 Proposition 5/(51)。S2 Lemma 2 默认非负 lambda；其 p9 末段明确说明跨实轴混合直接给双尾，Proposition 5 处理该结果。A 的显式指数过程消除了通用支配超鞅选择的额外可测性疑问。

## B：指定预测器的严格反例

取 iid Ber(1/100)、alpha=1/20、rho=1、n=280，E={X_1=...=X_280=0}。在 E 上，预测器为 (1/2,0,...,0)，故

\[
\widehat V_{280}=1/4,\quad \bar X_{280}=0,\quad |S_{280}|=14/5,
\quad b_{1,1/20}(1/4)=\sqrt{(5/4)\log500}<14/5.
\]

严格边界比较可以完全不用浮点：正指数级数的前 12 项给
`sum_{k=0}^{11}(25/4)^k/k! > 500`，所以 log500<25/4，进而
`b^2 < (5/4)(25/4)=125/16 < 196/25=(14/5)^2`。

E 上区间右端小于 0.01，故 E 是固定 t=280 的失覆盖事件的子集。概率是精确有理数 `(99/100)^280`，并可用整数交叉乘法检查

\[
\frac{59959}{10^6} < \left(\frac{99}{100}\right)^{280}
<\frac{59960}{10^6},\qquad \frac{59959}{10^6}>\frac1{20}.
\]

例如左侧检验就是 `10^6*99^280 > 59959*100^280`，右侧亦为整数比较。它们给严格解析概率超过 alpha，不是模拟证据。

独立 80 位 Decimal 校验：b=2.7871598667869304...；概率=0.059959014671465589...；距离 2.8 的边界间隙约 0.01284013。键中的概率 0.05995901467146544 是普通浮点舍入差别，不影响严格不等式或预定容差。

机制解释正确：适应性本身不足以让 (S,Vhat) 属于 sub-Gaussian 类；“不够可预测”也不是定义层面的排除原因。S1 p10–11 明确允许适应 V，并在额外条件下用可观测平方变差。参考推导另给的一步期望 `.99*exp(.02)+.01*exp(-3.98)=1.01018618...>1` 也正确，但只有前述概率反例才直接排除所声称的覆盖。

来源：S2 PDF p17 Figure 7 caption、p18 §5 item 5 确实讨论 naive self-normalized normal mixture 失败，并含 Ber(.01) 的情形；它们没有给出本任务 n=280、rho=1 的上述解析证明。键已正确区分该点。

## C：最优参数与无限时域失效

对 v>0，令 r=v/rho，则 b^2/v=g(r)=(1+1/r)log((1+r)/alpha^2)，并有

\[
g'(r)=\frac{r-\log((1+r)/\alpha^2)}{r^2}.
\]

分子从 log(alpha^2)<0 严格增加到无穷，导数 r/(1+r)>0；g 在 r->0 和 r->∞ 两端发散。故存在唯一全局最小点 r_alpha，由

\[
r_\alpha=\log\frac{1+r_\alpha}{\alpha^2},\quad
\rho^*=v/r_\alpha,\quad
\inf_{\rho>0}b_{\rho,\alpha}(v)=\sqrt{(1+r_\alpha)v}
\]

给出。若用 Lambert W，则 `r_alpha=-W_{-1}(-alpha^2/e)-1`；必须取负一支。alpha=.05 时 r_alpha=8.211968062068254...，常数 sqrt(1+r_alpha)=3.035122413028551...。键中数值一致。v=0 时 inf=0，但没有正 rho 达到，是独立的端点问题。

取 iid Ber(1/2)，令 R_i=2X_i-1，则 S_t=(1/2)sum R_i，V_t=t/4 合法，包络为 `(sqrt(1+r_alpha)/2)*sqrt(t)`。给定的 Rademacher LIL 推出

\[
\limsup_{t\to\infty}\frac{S_t}{\sqrt{V_t}}=+\infty\quad a.s.
\]

因而会无限多次严格越过该包络，失去同时覆盖的概率为 1。该反例只用合法确定性 V，与 B 无关。S2 PDF p12 Proposition 3/(21) 明确是固定 rho 的最适时间和固定目标 m 的最优 rho，未授权每时刻无预算地替换 m=V_t。C 的参考推导通过。

## EB：系数、预测器范围与双尾预算

S2 PDF p6 定义 `psi_{E,c}(lambda)=c^{-2}[-log(1-c*lambda)-c*lambda]`，范围 0<=lambda<1/c（c>0）。对本任务 [0,1]，c=1，故

\[
\psi_E(\lambda)=-\log(1-\lambda)-\lambda,\quad 0\le\lambda<1.
\]

在保持 S 与 Vhat 为任务原定义时，平方残差的系数就是 psi_E，**没有额外 /4**。若执行者改用 phi=4 psi_E、再写 phi/4，或者把 V 改成 4 Vhat、psi 改为 psi_E/4，这些一致缩放可接受。孤立把当前 psi_E 除以 4 则一般失效：例如 X~Ber(1/2)、预测器 1/2、lambda=1/2，错误一步期望是

\[
\cosh(1/4)\exp\{-(\log2-1/2)/16\}=1.01903704\ldots>1.
\]

当前参考键没有该系数错误，并明确接受等价缩放。

可独立证明参考标量不等式。对 xi>=-1、0<=lambda<1，

\[
\lambda\xi-\log(1+\lambda\xi)
=\lambda^2\xi^2\int_0^1\frac{u}{1+\lambda\xi u}\,du
\le\lambda^2\xi^2\int_0^1\frac{u}{1-\lambda u}\,du
=\psi_E(\lambda)\xi^2.
\]

因此 `exp{lambda*xi-psi_E(lambda)*xi^2}<=1+lambda*xi`。设 Y_t=X_t-E_{t-1}X_t，delta_t=Xhat_t-E_{t-1}X_t，则 delta 可预测；任务预测器确实取值于 [0,1]，故 xi=Y-delta=X-Xhat∈[-1,1]。从而

\[
\mathbb E_{t-1}e^{\lambda Y_t-\psi_E(\lambda)(Y_t-\delta_t)^2}
\le e^{\lambda\delta_t}(1-\lambda\delta_t)\le1.
\]

对 -X 和 -Xhat 同做一次，两边平方残差相同。若一侧界使用 crossing 预算 alpha/2，则两尾合计 alpha。S2 Theorem 4 原始写法是一侧 alpha、双侧 2alpha，不能误把它直接当双尾 alpha。若引用 Theorem 4，预测器必须取值于与 X 相同的 [a,b]；仅说“有某个有限界”而不保证相应 c 值，尚不充分。更广范围预测器可另行证明并调整尺度，不能无说明沿用 c=1。

来源直接支持：S2 PDF p14 Theorem 4/(23)；p35 Appendix A.8/(89)–(90)。已对实际 PDF p35 的公式和正文渲染进行目视核对。Theorem 4 的目标为平均条件均值 mu_t，不要求共同均值；本任务共同 mu 是特例。

参考点质量 lambda=1/2 的一侧边界为 `u(v)=2log(2/alpha)+(2log2-1)v`，因为 psi_E(1/2)=log2-1/2，公式正确。它合法但通常不保证半径趋于零；参考键已明说这一限制，且公开任务未强制 LIL 速率或收缩半径，不应因此扣分。固定 rho 正态方案以 Hoeffding 的 V=t/4 修复，同样正确。可数 rho_j 和 alpha*w_j 的 union bound 方案、固定先验混合方案也正确；事后无校正取 inf 或 supremum 不正确。

## D、E 与来源表整体核验

D 假。S1 PDF p9 定义、p12–13 Theorem 1 处理过滤下无限时间 crossing，而非只处理 iid 固定 n。S2 PDF p4 明确无需独立或共同均值，p14 Theorem 4 无正态误差假设；“normal mixture”的 normal 是混合分布。仅查这两篇不能给全球首创结论。

E 对几乎处处有限的正整数随机索引成立：令 G={所有 t>=1 都覆盖}，则
`G∩{1<=tau<∞} ⊆ {mu∈C_tau}`。概率至少 1-alpha，无需 E tau<∞，甚至无需 tau 为停止时刻。若可取无穷，只能先说 `P(tau<∞ 且失覆盖)<=alpha`，除非另定义 C_infty。当前参考推导正确，只有公开索引域需澄清。

除前述 S2 行中的两个页码笔误外，定位表所列数学来源均支持相应范围：

| 引用 | 独立核验 |
|---|---|
| S1 p9 Definition 1/(2.1)–(2.2) | (S,V) 成对、适应 V、超鞅支配，支持 |
| S1 p10–11 说明 | 适应不等于任意 V 可用，支持 |
| S1 p12–13 Theorem 1/(2.7) | 一侧无限时域线性 crossing，支持 |
| S1 p15/(2.12)–(2.15) | Ville 与固定参数指数推理，支持 |
| S1 p26 Table 3、p28 Lemma 3(c)–(e) | Hoeffding 代理、条件对称平方变差、下界增量 sub-exponential，支持 |
| S2 p4–5 定义与 (3)–(6) | mu_t、pair-based sub-psi、uniform boundary，支持；(2) 另在 p2 |
| S2 p9 Lemma 2/(13)、p27–28/(49)–(50) | 固定混合及 product measurability，支持 |
| S2 p10/(14)、p28 Proposition 5/(51) | 固定 rho、总 alpha 的双尾 normal mixture，支持 |
| S2 p12 Proposition 3/(21) | 固定目标参数优化，支持 |
| S2 p14 Theorem 4/(23)、p35/(89)–(90) | EB 条件、一步不等式和双尾 2alpha，支持 |
| S2 p17 Figure 7、p18 §5 | naive SN 失败定位，支持；不能冒充本次有限 n 证明 |

固定 PDF 分别为 63 页和 48 页；核查的相关页实际页脚与 PDF 一基序号一致。期刊页码不能直接替代这些坐标。未对许可表述作超出两份原文的法律判断，也未向报告复制任何来源全文。

## 评分公平性与替代方案

rubric 六大项分值和为 100。文字上不按 RWT、skill、工具数量、运行时或自评加分，明确要求隐藏这些信息盲评；当前文件不能证明后续执行确已盲化，须由实验组织过程另核验。

它明确允许其他严格有限反例、不同优化变量、Lambert W、有限时间 crossing 证明替代 LIL、等价 EB 缩放或另证 EB 构造、线性 EB 界及不同数值实现。没有要求参考证人的特定 prose、包或函数。关键 cap 针对最终仍推荐错误 B/C、决定性捏造来源及误归因构造稿，与任务核心风险相称，且普通页码笔误明确不触发造假 cap。

除上述“多 rho 3 分”的条件义务歧义，未发现明确偏袒特定方法或 RWT 身份的评分条款。正式评分应按数学意义接受等价证据，尤其不能要求存在感更强的工具轨迹，也不能以参考页码表的笔误否定正确定位。修正这项义务对齐和来源定位后，该任务的理论键可用于正式执行；本报告未评价任何执行者表现。
