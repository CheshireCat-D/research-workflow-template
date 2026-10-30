# 06_claim_D: D: positioning

**Source:** input/draft.tex, line 61 onward.

**Item Status:** 🔴 Contains Fatal Error

## Statement

Howard et al.~\cite{H2020} only provide fixed-sample bounds for independent identically distributed observations. The confidence sequences of Howard et al.~\cite{H2021} require a common mean and normally distributed errors. Thus B and C provide the first adaptive, nonparametric confidence sequences valid over an infinite time horizon.

## Original Proof

The draft provides no separate proof; its complete claim and short rationale are retained in Statement above.


## Audit Proof

| Step ID | Claim | Premises | Justification |
|---|---|---|---|
| S1 | S1 Theorem 1 is time-uniform and its objects are adapted process pairs. | S1 PDF pp9,12-13 Definition 1, Theorem 1 | The event explicitly quantifies over the full time index set. |
| S2 | S2 Theorem 4 covers average conditional means without normal observations. | S2 PDF p14 Theorem 4 (23) | Boundedness and predictable predictions suffice; common means are explicitly unnecessary. |
| S3 | Normal mixture refers to the distribution over the tuning variable. | S2 PDF p28 Proposition 5; A integration | It is not an observation-distribution assumption. |
| S4 | The proposed novelty conclusion has no valid theorem as its premise. | B,C plus S1-S3 | The two asserted extensions are false and the claimed literature restrictions contradict the originals. |

$\square$

## Notes / Errors

D1 confirmed at draft.tex:61. Only the two specified source papers are compared; no claim of exhaustive global novelty review is made.
