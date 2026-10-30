# 固定正态混合

**Source:** input/draft.tex L29–46

**Item Status:** 🟢 Valid

## Statement

在 SG 条件下，每个固定 $\rho>0$，$M_t=\int e^{\lambda S_t-\lambda^2V_t/2}dN(0,1/\rho)=\sqrt{\rho/(V_t+\rho)}e^{S_t^2/(2(V_t+\rho))}$，且 $C_t=[\bar X_t\pm b_{\rho,\alpha}(V_t)/t]\cap[0,1]$ 同时覆盖 $\mu$ 的概率至少为 $1-\alpha$。

## Original Proof

下列仅摘录本次构造稿，并非来源论文原文。

```tex
\begin{candidate}[A: baseline]
Suppose a nondecreasing predictable process $V_t$, with $V_0=0$, satisfies, for every $\lambda\in\R$ and $t\geq1$,
\begin{equation}\label{eq:sg}
\E[\exp\{\lambda(X_t-\mu)\}\mid\F_{t-1}]
\leq\exp\{\lambda^2(V_t-V_{t-1})/2\}.
\end{equation}
For a fixed $\rho>0$, let $F_\rho=N(0,1/\rho)$. Then
\begin{equation}\label{eq:normal-mixture}
M_t^\rho=\int_{\R}\exp\{\lambda S_t-\lambda^2V_t/2\}\,dF_\rho(\lambda)
=\sqrt{\frac{\rho}{V_t+\rho}}\exp\left\{\frac{S_t^2}{2(V_t+\rho)}\right\}.
\end{equation}
Consequently,
\begin{equation}\label{eq:cs}
C_t^\rho=\left[\bar X_t-\frac{b_{\rho,\alpha}(V_t)}t,\bar X_t+\frac{b_{\rho,\alpha}(V_t)}t\right]\cap[0,1]
\quad\text{satisfies}\quad
\Prb(\forall t\geq1:\mu\in C_t^\rho)\geq1-\alpha.
\end{equation}
\end{candidate}
```

## Audit Proof

| Step ID | Claim | Premises | Justification |
|---|---|---|---|
| S1 | 固定指数过程是非负超鞅 | SG；Delta V 可预测 | 把条件可测因子提出期望，L0=1 |
| S2 | 固定正态混合仍是超鞅 | 联合可测；非负积分；概率混合 | 条件 Tonelli，期望不超过 1 保证可积性 |
| S3 | 配方得到闭式混合 | V+rho>0 | 高斯积分乘 exp(S²/(2(V+rho))) |
| S4 | 边界反演 | log M≥log(1/alpha) | 等价于 |S|≥b；正负 lambda 在同一混合 |
| S5 | 双尾总预算 alpha | Ville 不等式；mu∈[0,1] | 与参数区间相交保留覆盖 |

## Notes / Errors

核验：原稿第 35–44 行的积分和概率常数均成立；完整配方与反演见 report.md。

$\square$
