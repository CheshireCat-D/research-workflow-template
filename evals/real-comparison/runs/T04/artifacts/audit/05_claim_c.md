# 逐时最优参数

**Source:** input/draft.tex L52–58

**Item Status:** 🔴 Contains Fatal Error

## Statement

原稿声称逐时取 $\rho_t\in\arg\min_{\rho>0}b_{\rho,\alpha}(V_t)$ 后仍有 $1-\alpha$ 同时覆盖，包含 $V_t=t/4$。

## Original Proof

下列仅摘录本次构造稿，并非来源论文原文。

```tex
\begin{candidate}[C: moving precision]
Howard et al.~\cite{H2021} allow optimization of mixture precision. Therefore one may choose, at every time,
\begin{equation}\label{eq:moving-rho}
\rho_t\in\operatorname*{arg\,min}_{\rho>0}b_{\rho,\alpha}(V_t)
\end{equation}
and use the resulting intervals $C_t^*$ without changing the simultaneous coverage guarantee. This remains true even with the valid deterministic intrinsic time $V_t=t/4$.
\end{candidate}
```

## Audit Proof

| Step ID | Claim | Premises | Justification |
|---|---|---|---|
| S1 | 缩放成 f(x) | v>0；x=v/rho | f=(1+1/x)log((1+x)/alpha²) |
| S2 | 唯一最小点 | h=x-log(1+x)-2log(1/alpha) | h 严格递增，由负到正；f 两端发散 |
| S3 | 下包络为 c sqrt(v) | x_star 解 h=0 | 最优处 f=1+x_star；v=0 时 inf=0 但无 argmin |
| S4 | Bernoulli(1/2) 对 V=t/4 满足 SG | cosh(lambda/2)≤exp(lambda²/8) | 仍是合法基准 |
| S5 | 优化同时覆盖率为零 | 题设给定 Rademacher LIL | 固定 c sqrt(t) 被无限次越过 |
| S6 | 来源优化是预定目标 m 的固定参数 | S2 PDF 第12页命题3式21 | 没有无预算逐时选择结论 |

## Notes / Errors

E02 确认：原稿第 53–57 行确实允许逐时无校正取最小值；LIL 给出合法确定性时间下同时覆盖率为零。

$\square$
