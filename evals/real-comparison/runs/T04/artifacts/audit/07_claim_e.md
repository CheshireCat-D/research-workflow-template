# 停止时刻

**Source:** input/draft.tex L64–70

**Item Status:** 🟢 Valid

## Statement

若已证明 $\mathbb P(\forall t\ge1:\mu\in C_t)\ge1-\alpha$，则任意几乎处处有限正整数停止时刻 $\tau$ 满足 $\mathbb P(\mu\in C_\tau)\ge1-\alpha$，无须 $\mathbb E\tau<\infty$。

## Original Proof

下列仅摘录本次构造稿，并非来源论文原文。

```tex
\begin{candidate}[E: stopping]
If a construction has in fact established simultaneous coverage, then for any almost surely finite stopping time $\tau$ taking values in $\{1,2,\ldots\}$,
\begin{equation}\label{eq:stop}
\Prb(\mu\in C_\tau)\geq1-\alpha,
\end{equation}
without a requirement that $\E\tau<\infty$.
\end{candidate}
```

## Audit Proof

| Step ID | Claim | Premises | Justification |
|---|---|---|---|
| S1 | 建立好事件 G | 所有确定时刻同时覆盖 | P(G)≥1-alpha |
| S2 | 好事件上停止时刻也覆盖 | tau 几乎处处有限且为正整数 | G 与 tau有限 的交集包含于停止时刻覆盖事件 |
| S3 | 不需要 E tau 有限 | 纯事件包含 | 与 S2 PDF 第19页引理3一致 |

## Notes / Errors

核验：原稿第 65–69 行的前提足够；结论由事件包含直接得到。

$\square$
