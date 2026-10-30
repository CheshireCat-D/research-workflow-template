# 定义与预测器

**Source:** input/draft.tex L18–27

**Item Status:** 🟢 Valid

## Statement

$(X_t)$ 适应，$0\le X_t\le1$ 且 $\mathbb E_{t-1}X_t=\mu\in[0,1]$。$S_t=\sum_{i\le t}(X_i-\mu)$，$\bar X_t=t^{-1}\sum_{i\le t}X_i$，$\widehat X_1=1/2$、$\widehat X_t=\bar X_{t-1}$，$\widehat V_t=\sum_{i\le t}(X_i-\widehat X_i)^2$。$b_{\rho,\alpha}(v)=\sqrt{(v+\rho)\log((v+\rho)/(\alpha^2\rho))}$，$v\ge0,\rho>0,0<\alpha<1$。

## Original Proof

下列仅摘录本次构造稿，并非来源论文原文。

```tex
Let $(\F_t)_{t\geq 0}$ be a filtration and let $(X_t)$ be an adapted process with $X_t\in[0,1]$ and $\E[X_t\mid\F_{t-1}]=\mu$ for a constant $\mu\in[0,1]$. Write
\begin{align*}
S_t&=\sum_{i=1}^t(X_i-\mu), & \bar X_t&=t^{-1}\sum_{i=1}^tX_i,\\
\widehat X_1&=\tfrac12, & \widehat X_t&=\bar X_{t-1}\quad(t\geq2), &
\widehat V_t&=\sum_{i=1}^t(X_i-\widehat X_i)^2.
\end{align*}
For $0<\alpha<1$, $\rho>0$, and $v\geq0$, define
\begin{equation}\label{eq:normal-boundary}
b_{\rho,\alpha}(v)=\sqrt{(v+\rho)\log\frac{v+\rho}{\alpha^2\rho}}.
\end{equation}
```

## Audit Proof

| Step ID | Claim | Premises | Justification |
|---|---|---|---|
| S1 | 预测器位于 [0,1] | 样本有界 | 过去样本平均保持区间，首项为 1/2 |
| S2 | 预测器可预测 | t≥2 时只用过去观测 | 对前一时刻 sigma 代数可测 |
| S3 | 经验平方和适应、非减 | 每个平方项为非负当前可测量 | 不能由此推出 SG 或 sub-Gaussian 条件 |

## Notes / Errors

核验：原稿第 18–27 行的定义自洽；适应性不等价于合法方差代理。

$\square$
