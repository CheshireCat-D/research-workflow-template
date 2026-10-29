# Pens, birds and independent replication: a bounded literature note

This is an edited public digest of an already executed, bounded literature investigation, not the original report or a new complete investigation. The original executor was a Codex agent. A separate Codex audit/compilation agent checked selected primary sources and prepared this note on 2026-10-29 UTC. The original report remains unchanged; its SHA-256 is `0f138340ca3b55ff7783dac44534b7a3e0c4f94fe87600a20871899c2c6447e0` (21,183 bytes). This digest has different bytes and omits detail. Audit scope and adjustments are recorded in `source-audit.json`.

## Request and scope

The original research-interest request was:

> 农学/动物营养与生物统计，想弄清饲料按笼或栏分配时，增加栏内个体测量能否替代增加独立处理重复，并从已有研究提出一个可继续调查的小问题。没有给定文献包。

The executed investigation sought accessible original methods research or official guidance, mainly poultry/pigs. It compared small follow-up questions without judging feed efficacy. It was a narrative survey without a registered protocol, not a systematic review. No supplied literature package was used.

## Original search record

The following 13 queries were reported as actually issued by the original executor on 2026-10-29 through general web search. They are preserved as execution history; the audit agent did not rerun them. Q6 contains a domain-looking term without a `site:` operator; no effective site restriction was verified. There were no reported year/language/discipline filters, pagination, bulk exports or database-advanced searches; ranking was tool-default and unaudited. Direct source-page visits followed discovery.

| Batch | Query | Exact expression |
|---|---|---|
| A | Q1 | `animal nutrition pen experimental unit subsampling pigs number of pigs sampled pen power experimental design` |
| A | Q2 | `poultry experimental unit pen individual bird pseudoreplication statistical power number pens` |
| B | Q3 | `"Partition of variation for predicting experimental power" Pesti Billard DOI` |
| B | Q4 | `"Impact of sample size of birds processed per pen" Maynard` |
| B | Q5 | `"Design and analysis of pen studies" St-Pierre 2007 DOI` |
| B | Q6 | `site.pubmed.ncbi.nlm.nih.gov "Partition of variation for predicting experimental power"` |
| C | Q7 | `"broiler" "within pen" "sampling" "confidence" "woody breast"` |
| C | Q8 | `"sample size" "birds sampled per pen" "treatment" power` |
| D | Q9 | `"Technical note: utilization of various allotment strategies" DOI` |
| D | Q10 | `"Impact of sample size of birds processed per pen" data availability` |
| D | Q11 | `"Partition of variation for predicting experimental power" data availability` |
| E | Q12 | `"Reducing broiler breast myopathies through supplementation of guanidinoacetic acid in broiler diets"` |
| E | Q13 | `"10.1016/j.psj.2026.106879" data pen raw` |

The executor manually counted displayed items by batch: A=22, B=18, C=15, D=18, E=15; total 88. These include duplicate links, versions and irrelevant results, not 88 independent studies or database hit totals. Per-query hit totals were unavailable. Not every displayed item received full-text screening. PubMed, Web of Science, Scopus, Crossref API and Google Scholar were not separately searched as databases.

## Source identity and access

Dates below refer to the selected records; source access was checked on 2026-10-29 UTC. Repeated URLs/versions are not additional evidence votes. “Original” describes the executor's report; “audit” describes this separate targeted check.

| ID | Identity and deduplication | Access boundary |
|---|---|---|
| S1 | [ARRIVE, item 1b](https://arriveguidelines.org/arrive-guidelines/study-design/1b/explanation), official dynamic page; no DOI/date shown | Original and audit: explanation body read. Its cited papers were not thereby read. |
| S2 | G.M. Pesti; L. Billard; S.-B. Wu; N.K. Morgan; P.S. Taylor; S. de las Heras-Saldana. *Poultry Science* 102(7), 102698, online 2023-04-12; DOI [10.1016/j.psj.2023.102698](https://doi.org/10.1016/j.psj.2023.102698); PMC10239017, PMID37245437 | Original and audit: selected [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC10239017/) sections/table. [Curtin](https://espace.curtin.edu.au/handle/20.500.11937/91466) has the same DOI, although its brief record lists only Morgan. One work; no PDF-byte/version equivalence established. |
| S3 | C.J. Maynard; K. Thompson; A. Mauromoustakos; C.M. Owens. *Poultry Science* 105(7), 106879, online 2026-03-28; DOI [10.1016/j.psj.2026.106879](https://doi.org/10.1016/j.psj.2026.106879); PMC13087773, PMID41933528 | Original and audit: selected [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC13087773/) methods, Tables 1/2, notes and discussion. Online/issue dates are one work. Audit PubMed open returned cache miss; PMC supplied identity/content. |
| S4 | Mi Yeon Shim; Gene M. Pesti. UGA Bulletin 1417, 2013-03-31; no DOI | Original and audit: [official bulletin](https://fieldreport.caes.uga.edu/publications/B1417/pen-size-optimization-workbook-of-experimental-research-design-power-for-poultry/) text. Old UGA URL redirects here; one source. Neither executor nor auditor ran Excel macros. |
| S5 | N.R. St-Pierre, 2007; *J Dairy Sci* 90 Suppl 1:E87–99; DOI [10.3168/jds.2006-612](https://doi.org/10.3168/jds.2006-612), PMID17517755 | Original: metadata/abstract; publisher attempts 403. Audit: [PubMed](https://pubmed.ncbi.nlm.nih.gov/17517755/) metadata/abstract readable; no full text attempted. Identity retained; no unexamined numerical claim imported. |
| S6 | A.K. Jenkins et al., 2024; *J Anim Sci* 102:skae088; DOI [10.1093/jas/skae088](https://doi.org/10.1093/jas/skae088), PMID38571338, PMC11034435 | Original: PubMed metadata/abstract, PMC verification page, OUP abstract. Audit: [OUP](https://academic.oup.com/jas/article/doi/10.1093/jas/skae088/7640097) redirects to abstract, identity/author order checked; PubMed yielded only footer. Original full-text failure was not replayed. |
| S7 | C.J. Maynard; D.S. Nelson; S.J. Rochell; C.M. Owens, 2023; *J Appl Poult Res* 32(1):100324; DOI [10.1016/j.japr.2022.100324](https://doi.org/10.1016/j.japr.2022.100324) | Original: [Arkansas](https://scholarworks.uark.edu/poscpub/4/) metadata/abstract; publisher/repository full-text attempts 403. Audit: repository identity checked, not full text. S3 Methods/Ref. 20 identify prior data reuse: distinct publication, not an independent repeat of its male experiment. |

Other unexamined search leads remain leads. A possible related conference abstract was not established as a distinct dataset. Access failures describe particular requests, not global article availability.

## What the checked sources support

**S1 — unit definition.** Item 1b, Explanation paragraphs 2–6: independently treated entities determine the experimental units; whole-cage diet is a cage-level example. Subsamples cannot simply increase treatment replication. Thus four independently assigned pens with ten birds measured in each still provide four treatment units per group. If treatment is assigned by house, house-level dependence must be addressed. This is an application of the guidance, not a poultry variance estimate. [Official explanation](https://arriveguidelines.org/arrive-guidelines/study-design/1b/explanation).

**S2 — nested variation.** Materials and Methods and Table 2 separate birds within pens from pens within treatments. Its first example uses therapeutic agents, not a feed intervention. An internal count conflict remains: Methods says 210 birds, but 3×7×5 and Table 2 total df=104 imply 105 analyzed observations. The original report already flagged this. We retain the hierarchy lesson, not its prediction tables or a universal variance value. [PMC, Methods/Table 2](https://pmc.ncbi.nlm.nih.gov/articles/PMC10239017/).

**S3 — endpoint sensitivity.** Methods and Tables 1/2 describe reanalysis of 48 existing pens, including 30 male diet pens. At five sampled birds, reported live-weight deviations are 4.40%/5.16%, versus 45.26%/41.30% for WB mean score. Footnotes define a maximum relative deviation at simulated 5th/95th percentiles; this is not treatment-effect power or 95% coverage. The available methods do not establish the original treatment-randomization procedure or fully specify the resampling implementation. [PMC, Methods; Tables 1/2 notes; discussion](https://pmc.ncbi.nlm.nih.gov/articles/PMC13087773/).

**S4 — resource trade-off.** “Why Is Estimating Experimental Power Important?” and “What Can Be Concluded…” discuss birds per pen versus pen replication, including loss of error degrees of freedom with fewer pens. The general trade-off is already established; identifying it is not a new contribution. The workbook's calculations, current costs and numerical examples were not validated here. [Official bulletin](https://fieldreport.caes.uga.edu/publications/B1417/pen-size-optimization-workbook-of-experimental-research-design-power-for-poultry/).

## A transparent model

For two treatments with r independent pens each and m measured birds per pen, take

\[
Y_{ijk}=\mu+\tau_i+b_{ij}+\varepsilon_{ijk},\qquad
\operatorname{Var}(b_{ij})=\sigma_p^2,\quad
\operatorname{Var}(\varepsilon_{ijk})=\sigma_w^2.
\]

Assume independent pens and individual residuals, independence between both components, common variances, and no house effect confounded with treatment. Variance addition gives the standard treatment-contrast formula

\[
\operatorname{Var}(\widehat\tau_1-\widehat\tau_0)
=\frac{2}{r}\left(\sigma_p^2+\frac{\sigma_w^2}{m}\right).
\]

With r fixed, more birds reduce the within-pen term, while positive between-pen variation remains. With N=rm fixed, the variance is \(2\sigma_p^2/r+2\sigma_w^2/N\). This is an illustrative population model, not an empirical feed recommendation. Without-replacement sampling from an already observed finite pen requires its own conditional sampling variance; the formula is not an exact replacement for that calculation. One pen per treatment cannot supply a separate within-treatment pen-error estimate under this design.

## Candidates and the next small investigation

| Candidate | Decision |
|---|---|
| Can additional birds be counted as independent treatment repeats? | Answered conceptually above; use as a design-learning exercise. |
| Under a fixed measurement budget, compare 8 pens×5 birds with 4 pens×10 birds for body weight and WB mean score. | Preferred local design diagnostic. It is not established as globally novel. |
| Investigate pig allocation by initial weight. | First obtain S6 full text and data; its stated topic substantially overlaps this candidate. |

The preferred question is conditional: in a dataset with verified pen-level treatment allocation, do the two sampling plans change the precision of one prespecified diet contrast differently for body weight and WB? First make a data-feasibility table: pen ID, diet, individual endpoints, missing/death records, original randomization/blocking, stocking numbers and final sampling rules. Require at least eight eligible pens per compared treatment and ten measurable birds in each eligible pen. S3's male dataset is a possible lead, not an acquired or already eligible dataset. No bird-level data were obtained in either investigation; no claim is made that none exist.

If lawful public data pass these checks, select four/eight existing pens within treatment and original blocks, then sample ten/five birds without replacement per selected pen. Repeat 1,000 times and compare bias relative to the full observed-data contrast, empirical spread, and interval widths; retain pen dependence in analysis. These repetitions do not create new independent pens. This examines measurement allocation among existing pens; it does not by itself establish the effect of changing the number of pens housed in a future trial or changing density.

Call inclusion of the full observed contrast a resampling-stability diagnostic. Coverage of a population effect and power require a separate known-truth hierarchical simulation. With no suitable data, use explicitly synthetic ICC sensitivity analysis and give no endpoint-specific empirical recommendation.

A prior study matching the same endpoints and contrast would turn this into replication. High pen costs with small between-pen variation may favor more within-pen measurement once independent replication is adequate. Missing allocation information, nonrandom final bird selection, house-level treatment, interference or altered density would change the design. Rare-lesion risk needs an appropriate endpoint/model rather than an unexamined mean-score calculation.

## Editorial adjustments and reuse

The audit found no substantive error requiring reversal of the original core answer. This digest preserves Q6 as issued without treating its domain term as an applied site filter, replaces rounded S3 deviations with checked exact values, explicitly leaves its treatment-randomization procedure unverified, and distinguishes finite-dataset resampling from the population formula and a future housing design. The original report was not edited. The original search counts and access failures remain attributed execution records, not claims independently replayed by the auditor.

This file contains original commentary and links, with no copied article body, figures or tables. It grants no license to third-party material. Any repository license applies only to the original commentary to which its owner applies it; linked sources retain their own terms. No feed-efficacy conclusion, global novelty determination, author contact or submission was performed.
