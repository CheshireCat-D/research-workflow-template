# 05_claim_C: C: moving precision

**Source:** input/draft.tex, line 53 onward.

**Item Status:** 🔴 Contains Fatal Error

## Statement

Howard et al.~\cite{H2021} allow optimization of mixture precision. Therefore one may choose, at every time,
$$
\rho_t\in\operatorname*{arg\,min}_{\rho>0}b_{\rho,\alpha}(V_t)
$$
and use the resulting intervals $C_t^*$ without changing the simultaneous coverage guarantee. This remains true even with the valid deterministic intrinsic time $V_t=t/4$.

## Original Proof

The draft provides no separate proof; its complete claim and short rationale are retained in Statement above.


## Audit Proof

| Step ID | Claim | Premises | Justification |
|---|---|---|---|
| S1 | For $v>0$, $b^2/v=g(x)$ with $x=v/\rho$. | draft.tex:26,55 | Substitute $\rho=v/x$. |
| S2 | $g'(x)=[x-\log(1+x)-2\log(1/\alpha)]/x^2$. | S1 | Differentiate the product explicitly. |
| S3 | The unique minimizer satisfies $x-\log(1+x)=2\log(1/\alpha)$. | S2 | The left side has derivative $x/(1+x)>0$, range $(0,\infty)$. |
| S4 | The minimized boundary is $\sqrt{(1+x_\alpha)v}$; at $v=0$ the argmin is empty. | S1-S3 | At the stationary point the bracket equals $x$; for $v=0$, $b^2=2\rho\log(1/\alpha)$. |
| S5 | For iid Bernoulli(1/2), $V_t=t/4$ is legitimate. | Boundedness; conditional Hoeffding calculation in report.md | CGF second derivative is at most $1/4$. |
| S6 | The minimized $O(\sqrt t)$ boundary is crossed infinitely often almost surely. | S4,S5; stipulated iid Rademacher LIL | The LIL scale $\sqrt{2t\log\log t}$ exceeds every fixed multiple of $\sqrt t$ eventually. |
| S7 | S2 Proposition 3 optimizes one fixed precision for a prescribed target time. | S2 PDF p12, eq(21) | It gives no crossing certificate for the time-varying lower envelope. |

$\square$

## Notes / Errors

C1 confirmed at draft.tex:53-57 by the LIL counterexample. C2: empty argmin at $v=0$ confirmed at line 55 from the actual domain in line 24.
