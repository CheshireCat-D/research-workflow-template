# 01_assumptions: Assumptions

**Source:** input/draft.tex, line 18 onward.

**Item Status:** 🟢 Valid

## Statement

Let $(\mathcal F_t)_{t\geq 0}$ be a filtration and let $(X_t)$ be an adapted process with $X_t\in[0,1]$ and $\mathbb E[X_t\mid\mathcal F_{t-1}]=\mu$ for a constant $\mu\in[0,1]$. Write
$$\begin{aligned}
S_t&=\sum_{i=1}^t(X_i-\mu), & \bar X_t&=t^{-1}\sum_{i=1}^tX_i,\\
\widehat X_1&=\tfrac12, & \widehat X_t&=\bar X_{t-1}\quad(t\geq2), &
\widehat V_t&=\sum_{i=1}^t(X_i-\widehat X_i)^2.
\end{aligned}$$

## Original Proof

The draft provides no separate proof; its complete claim and short rationale are retained in Statement above.


## Audit Proof

| Step ID | Claim | Premises | Justification |
|---|---|---|---|
| S1 | $X_t$ and the filtration are specified; $X_t$ is adapted and bounded. | draft.tex:18 | These are assumptions, not consequences. |
| S2 | $S_t$ is a martingale with bounded increments. | Conditional mean in line 18 | Each increment has conditional mean zero and is integrable. |
| S3 | The stated predictor is predictable and $[0,1]$-valued. | draft.tex:21 | The initial value is deterministic; later values depend only on previous observations. |
| S4 | $\widehat V_t$ is adapted, nonnegative, and nondecreasing. | draft.tex:22 | It is a cumulative sum of nonnegative adapted residual squares; predictability is not implied. |

$\square$

## Notes / Errors

No error in these stipulated definitions. The distinction between adapted and predictable is used in B.
