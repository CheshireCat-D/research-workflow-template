# 科研质量实作与离线回归

本组补充三类实际任务，材料与结果由不同上下文产生或核对。沿用现有九个技能和记录结构；既有评估材料保持原字节。

| 任务 | 输入与实际产物 | 独立核对 |
|---|---|---|
| 从研究兴趣开展真实文献调查 | [公开检索笔记](literature/report.md)：13条实际查询、来源身份、访问范围、候选比较与最小调查 | [原始来源核对](literature/source-audit.json)：定向读取四项主要原始/官方来源，保留去重、不可读正文和资料门槛 |
| 成立稿与缺陷稿审阅 | `review/cases/` 的四份原创稿件与 `review/reports/` 的四份单独报告 | [参考与报告核对](review/assessment.md)：数学与农生统计各一份成立稿、一份缺陷稿；核对误报、漏报和问题依据 |
| 资源改变后调整推荐 | [新增资源](adaptation/resource-update.md)、[8栏汇总](adaptation/pen-summary.csv)、[第二阶段报告](adaptation/report.md) | 原建议保留，决定版本1替换为2；独立只读查实际项目，重算4区组差和留一敏感性 |

## 真实检索与版本身份

第一阶段从农学/动物营养兴趣出发，未提供文献包。执行者实际搜索并阅读部分正文，区分同一作品的多渠道记录与复用同一试验数据的不同出版物。独立核对者另读主来源；它没有重演原检索。公开笔记是压缩整理版，原完整报告的摘要身份保留在清单中，未把第三方全文、图表或原始动物数据收入仓库。

第二阶段是明确标为合成的资源变更：只有8栏均值，不能取得个体数据。执行者暂缓原个体抽样比较，实际完成可用的汇总分析。`adaptation/calculate.py` 是当次执行的计算代码，不是通用动物试验分析器。复算到一个新输出文件，例如从源码根目录运行：

```sh
python3 -B evals/quality/adaptation/calculate.py evals/quality/adaptation/pen-summary.csv ../adaptation-results.json
```

该计算脚本按传入路径写结果；先选未存在的项目外文件。原临时项目与逐命令JSON不分发，`state-receipt.json` 保留真实执行摘要；独立核对结论收在 `manifest.json`。登记完整性、计算结果与研究判断分别解释。

## 审阅的隔离与核对

四名执行评审各在新上下文中只收到一份原稿及相关RWT指导；没有收到[参考键](review/reference-key.json)、其他稿件或其他报告。报告完成并冻结后，另一名评估者才对照全部材料和参考键核对。全部为AI代理，四个小练习的观察不换算成总体准确率。

两份成立稿的主要问题为空；两份缺陷稿分别发现同分布误推协方差为零，以及整栏随机分配下的伪重复。可选表述建议与主要错误分开计数。`review/checks.json` 保留独立反例、精确枚举和浮点区间核对；报告语义由已执行的内容核对判断，CI不靠关键词重新打分。

## 数据到表格和稿源

[配对栏示例](../../examples/paired-pens/README.md)从120条原创合成个体记录复算介绍图中的同例。[稿源示例](../../examples/submission-table/README.md)读取其配对CSV，生成可编辑主稿、三线表及文件清单。已在本地实际用 `booktabs+dcolumn` 编译两轮并检查最终页与两张表；观察到的文件指纹与检查范围保存在本组清单，PDF及辅助文件不混入源码。

## 当前回归

```sh
python3 -B -m unittest discover -s tests -p test_quality_evaluations.py -v
python3 -B -m unittest discover -s tests -p test_paired_pens.py -v
python3 -B -m unittest discover -s tests -p test_submission_table.py -v
```

离线回归核对输入、指导与报告身份，重算明确数值，并通过改变输入检查代码是否真实读取材料。它不重新运行模型评审、在线检索或TeX编译；编译和视觉核对以实际执行记录为准。`manifest.json` 是本组文件与范围的单一入口，不包含自身摘要。
