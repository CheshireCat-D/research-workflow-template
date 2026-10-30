# 04_claim_B: B: empirical substitution

**Source:** input/draft.tex, line 49 onward.

**Item Status:** 🔴 Contains Fatal Error

## Statement

The sub-$\psi$ definition of Howard et al.~\cite{H2020} permits adapted intrinsic time. Since $\widehat V_t$ is adapted, boundedness and the common conditional mean suffice to replace $V_t$ by $\widehat V_t$ in the baseline, retaining the same normal-mixture boundary and the same simultaneous coverage probability.

## Original Proof

The draft provides no separate proof; its complete claim and short rationale are retained in Statement above.


## Audit Proof

| Step ID | Claim | Premises | Justification |
|---|---|---|---|
| S1 | Adaptedness is necessary here but is not a sub-Gaussian certificate. | draft.tex:49; S1 PDF pp9-11 Definition 1 (2.1) | The definition additionally requires dominating supermartingales. |
| S2 | On four all-zero or all-one Bernoulli(1/2) observations, $\widehat V_4=1/4$ and $|S_4|=2$. | draft.tex:21-22; specified predictor | Only the first residual is nonzero. |
| S3 | At $\rho=1/4,\alpha=1/16$, the substituted boundary squared is $(9/2)\log2<4$. | S2; draft.tex:26 | Use $e^{3/4}>65/32>2$, hence $\log2<3/4$. |
| S4 | Miscoverage probability is at least $2(1/2)^4=1/8>1/16$. | S2,S3; independent Bernoulli law | The disjoint two constant-path events both fail at time 4. |

$\square$

## Notes / Errors

B1 confirmed at draft.tex:49. This is a finite analytic counterexample under all base assumptions, not a citation-based or numerical objection.
