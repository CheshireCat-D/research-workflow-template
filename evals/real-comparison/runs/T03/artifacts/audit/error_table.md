# Validated error index

| File | Error ID | One-line description | Status | Severity | Confidence |
|---|---|---|---|---|---|
| 04_claim_B.md | B1 | Adaptedness is substituted for a sub-Gaussian certificate; four-step failure exceeds alpha | 🚨 Confirmed Error | Critical | High |
| 05_claim_C.md | C1 | Pointwise optimization produces an O(sqrt(t)) boundary crossed a.s. under valid deterministic intrinsic time | 🚨 Confirmed Error | Critical | High |
| 05_claim_C.md | C2 | At v=0, the claimed argmin over rho>0 is empty | 🚨 Confirmed Error | Minor | High |
| 06_claim_D.md | D1 | Claimed source restrictions and consequent novelty contradict the original theorems | 🚨 Confirmed Error | Major | High |

Validation: B1 locates draft.tex:49 and uses the exact predictor at lines 21-22; C1 locates lines 53-57 and C2 line 55 with the domain in line 24; D1 locates line 61. Full analytic witnesses are in the corresponding item and report.md. A and E were checked and are valid. No open or discarded flag remains.
