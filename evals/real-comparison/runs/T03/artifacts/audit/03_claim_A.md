# 03_claim_A: A: baseline

**Source:** input/draft.tex, line 30 onward.

**Item Status:** 🟢 Valid

## Statement

Suppose a nondecreasing predictable process $V_t$, with $V_0=0$, satisfies, for every $\lambda\in\mathbb R$ and $t\geq1$,
$$
\mathbb E[\exp\{\lambda(X_t-\mu)\}\mid\mathcal F_{t-1}]
\leq\exp\{\lambda^2(V_t-V_{t-1})/2\}.
$$
For a fixed $\rho>0$, let $F_\rho=N(0,1/\rho)$. Then
$$
M_t^\rho=\int_{\mathbb R}\exp\{\lambda S_t-\lambda^2V_t/2\}\,dF_\rho(\lambda)
=\sqrt{\frac{\rho}{V_t+\rho}}\exp\left\{\frac{S_t^2}{2(V_t+\rho)}\right\}.
$$
Consequently,
$$
C_t^\rho=\left[\bar X_t-\frac{b_{\rho,\alpha}(V_t)}t,\bar X_t+\frac{b_{\rho,\alpha}(V_t)}t\right]\cap[0,1]
\quad\text{satisfies}\quad
\mathbb P(\forall t\geq1:\mu\in C_t^\rho)\geq1-\alpha.
$$

## Original Proof

The draft provides no separate proof; its complete claim and short rationale are retained in Statement above.


## Audit Proof

| Step ID | Claim | Premises | Justification |
|---|---|---|---|
| S1 | For each real $\lambda$, $L_t(\lambda)=e^{\lambda S_t-\lambda^2V_t/2}$ is a nonnegative supermartingale. | draft.tex:30-33; $\Delta V_t$ predictable | Take conditional expectation and factor out $e^{-\lambda^2\Delta V_t/2}$. |
| S2 | The fixed normal mixture is a supermartingale with initial value 1. | S1; joint measurability; nonnegative integrands | Conditional Tonelli and $\mathbb EL_t(\lambda)\le1$ give integrability. |
| S3 | The closed expression in line 38 holds. | draft.tex:35-38 | Combine the normal density exponent and complete the square; see report.md. |
| S4 | $M_t\ge1/\alpha$ iff $|S_t|\ge b(V_t)$. | S3; $V_t+\rho>0$ | Take logarithms and multiply by $2(V_t+\rho)$. |
| S5 | Total two-sided crossing probability is at most $\alpha$. | S2, S4; Ville | The mixture over the full real axis already includes both signs. |
| S6 | The closed, clipped intervals cover simultaneously with probability at least $1-\alpha$. | S5; $\mu\in[0,1]$ | Strict miscoverage is contained in the crossing event. |

$\square$

## Notes / Errors

Validated at draft.tex:29-46. Source anchors: S1 PDF p13 Lemma 1 (2.11); S2 PDF p28 Proposition 5 (51). No flag remains.
