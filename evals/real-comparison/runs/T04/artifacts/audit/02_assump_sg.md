# 条件 SG

**Source:** input/draft.tex L30–34

**Item Status:** 🟢 Valid

## Statement

$V_0=0$，$V$ 非减可预测；对所有 $t\ge1,\lambda\in\mathbb R$，$\mathbb E_{t-1}e^{\lambda(X_t-\mu)}\le e^{\lambda^2\Delta V_t/2}$。

## Original Proof

下列仅摘录本次构造稿，并非来源论文原文。

```tex
Suppose a nondecreasing predictable process $V_t$, with $V_0=0$, satisfies, for every $\lambda\in\R$ and $t\geq1$,
\begin{equation}\label{eq:sg}
\E[\exp\{\lambda(X_t-\mu)\}\mid\F_{t-1}]
\leq\exp\{\lambda^2(V_t-V_{t-1})/2\}.
\end{equation}
```

## Audit Proof

| Step ID | Claim | Premises | Justification |
|---|---|---|---|
| S1 | SG 是附加假设 | 并非由任意适应 V 自动得到 | 须核查具体一对 (S,V) |
| S2 | t/4 是原有界设定下的一项合法选择 | 条件 Hoeffding 引理 | 范围长度 1 给出指数上界 exp(lambda²/8) |

## Notes / Errors

核验：原稿第 30–34 行明确增加 SG 和可预测性，A 可以使用这些假设。

$\square$
