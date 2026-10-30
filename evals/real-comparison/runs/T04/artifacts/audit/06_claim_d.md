# 文献定位

**Source:** input/draft.tex L60–62

**Item Status:** 🔴 Contains Fatal Error

## Statement

原稿声称 S1 仅处理 iid 固定样本量，S2 要求共同均值与正态误差，据此把 B、C 称作首个自适应非参数无限时域置信序列。

## Original Proof

下列仅摘录本次构造稿，并非来源论文原文。

```tex
\begin{candidate}[D: positioning]
Howard et al.~\cite{H2020} only provide fixed-sample bounds for independent identically distributed observations. The confidence sequences of Howard et al.~\cite{H2021} require a common mean and normally distributed errors. Thus B and C provide the first adaptive, nonparametric confidence sequences valid over an infinite time horizon.
\end{candidate}
```

## Audit Proof

| Step ID | Claim | Premises | Justification |
|---|---|---|---|
| S1 | S1 不是仅 iid 固定时刻 | PDF 第9页定义1、第12页定理1 | 适应过程与存在某时间的越界事件 |
| S2 | S2 不要求一般共同均值或正态误差 | PDF 第4–5页、第14页定理4 | 平均条件均值可变；有界非参数结果 |
| S3 | 首次主张无依据 | B、C 均已被反例否定；仅核查两文 | 不能据有限文献范围宣布全球优先权 |

## Notes / Errors

E03 确认：原稿第 61 行与已读原文定理条件、时间域冲突；B、C 的首创论断无成立基础。

$\square$
