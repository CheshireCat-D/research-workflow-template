# 07_claim_E: E: stopping

**Source:** input/draft.tex, line 65 onward.

**Item Status:** 🟢 Valid

## Statement

If a construction has in fact established simultaneous coverage, then for any almost surely finite stopping time $\tau$ taking values in $\{1,2,\ldots\}$,
$$
\mathbb P(\mu\in C_\tau)\geq1-\alpha,
$$
without a requirement that $\mathbb E\tau<\infty$.

## Original Proof

The draft provides no separate proof; its complete claim and short rationale are retained in Statement above.


## Audit Proof

| Step ID | Claim | Premises | Justification |
|---|---|---|---|
| S1 | Let $G=\bigcap_{t\ge1}\{\mu\in C_t\}$. | draft.tex:65 | By hypothesis, $\Pr(G)\ge1-\alpha$. |
| S2 | $G\cap\{\tau<\infty\}\subseteq\{\mu\in C_\tau\}$. | S1; $\tau$ positive integer and finite almost surely | Every realized finite index is one of the indices in the intersection. |
| S3 | $\Pr(\mu\in C_\tau)\ge1-\alpha$. | S1,S2 | The null event $\tau=\infty$ does not change the probability bound; no expected-time argument is used. |

$\square$

## Notes / Errors

Validated at draft.tex:65-69. Source: S2 PDF p19 Lemma 3; the forward inclusion even holds for arbitrary finite random times.
