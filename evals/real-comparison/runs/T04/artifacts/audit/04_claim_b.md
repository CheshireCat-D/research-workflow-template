# 经验方差替换

**Source:** input/draft.tex L48–50

**Item Status:** 🔴 Contains Fatal Error

## Statement

原稿声称仅凭有界性、共同条件均值与 $\widehat V$ 的适应性，就可把 A 的 $V$ 换成 $\widehat V$ 并保留同一边界和概率。

## Original Proof

下列仅摘录本次构造稿，并非来源论文原文。

```tex
\begin{candidate}[B: empirical substitution]
The sub-$\psi$ definition of Howard et al.~\cite{H2020} permits adapted intrinsic time. Since $\widehat V_t$ is adapted, boundedness and the common conditional mean suffice to replace $V_t$ by $\widehat V_t$ in the baseline, retaining the same normal-mixture boundary and the same simultaneous coverage probability.
\end{candidate}
```

## Audit Proof

| Step ID | Claim | Premises | Justification |
|---|---|---|---|
| S1 | 取 iid Bernoulli(1/100) | 满足原稿全部观测假设 | 自然过滤与共同均值 |
| S2 | 前 200 次全零时 Vhat=1/4，|S|=2 | 指定预测器 | 首平方为 1/4，后续为 0 |
| S3 | 错误区间排除真均值 | alpha=1/20、rho=1/4 | b²=log(800)/2<4 |
| S4 | 事件概率严格大于 alpha | P=(99/100)^200 | log(1-x)>-x/(1-x)，得到 P>exp(-200/99)>1/20 |

## Notes / Errors

E01 确认：原稿第 49 行确实把适应性作为替换理由；上述固定时刻反例直接反驳所声称覆盖，置信度高。

$\square$
