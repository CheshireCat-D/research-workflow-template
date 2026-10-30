# 02_boundary: Definition

**Source:** input/draft.tex, line 24 onward.

**Item Status:** 🟢 Valid

## Statement

For $0<\alpha<1$, $\rho>0$, and $v\geq0$, define
$$
b_{\rho,\alpha}(v)=\sqrt{(v+\rho)\log\frac{v+\rho}{\alpha^2\rho}}.
$$

## Original Proof

The draft provides no separate proof; its complete claim and short rationale are retained in Statement above.


## Audit Proof

| Step ID | Claim | Premises | Justification |
|---|---|---|---|
| S1 | $v+\rho>0$ and $(v+\rho)/(\alpha^2\rho)>1$. | draft.tex:24-26 | The domain makes the logarithm positive. |
| S2 | $b_{\rho,\alpha}$ is real and positive. | S1 | Positive square root. At $v=0$ it equals $\sqrt{2\rho\log(1/\alpha)}$. |

$\square$

## Notes / Errors

Definition itself is valid. It does not make every variance substitution a valid bound.
