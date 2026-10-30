# 阶段C续作结果

当前有效评价范围已改为2011-11-01至2011-12-31，1460观察小时、61日。已实际复算，更新数值结果、配套表、摘要、材料绑定、范围关系、作者选择和三个受影响活动。最终只读检查及恢复均退出0，四项活动有效状态均为done，断点revision 43为current，无未解决的身份或依赖发现。该结果只说明登记和本次有范围复核已完成，没有人类专家内容认可或投稿授权。

参数授权原文及批准文件逐字保留在项目context/stage-C/。权威配置为project.json，当前记录、版本和下一步以records/registry.json为准；初始context/中的Q4约束作为历史来源保留，PROJECT.md与旧handoff不覆盖新版本。离线标准库、不采集新数据、不重训、不外推2012、截止2026-12-15、期刊未定等其他约束保持。

## 先保存漂移态，再实质复核

首次resume退出1，发现notes/parameters.json从Q4改为11月至12月，而已有result/table/summary仍为Q4；D-CALC、D-INVALID-TEST、D-SYNTH过期，D-SOURCE-CHECK有效。尚未重算时先保存断点revision 23，随后check仍退出1：断点已current，但三个旧活动仍stale。保存断点没有使旧工作重新有效。原始输出为外部02-check-after-drift-checkpoint.txt，持久副本及当时registry、参数、旧成果字节在history/stage-C-before-recalculation/。

之后用原scripts/compute.py、data/hour_2011.csv和model/frozen.json运行到独立新目录。实际正常命令退出0；另用标准库逐项计算观察数、MAE、RMSE、预测减实际偏差，容差1e-14核对通过；表中每项与JSON一致，输入完整SHA一致。结果保存在validation/stage-C/recalculation-retry/，核验证据为verification.json。完成核验后才替换results/result.json、table.csv及summary.md，并通过正式版本接口显式重新登记。

| 指标 | C0 | C1 |
|---|---:|---:|
| MAE | 56.641274309909 | 41.252622564019 |
| RMSE | 81.700383606317 | 64.158265648678 |
| 偏差（预测减实际） | 13.433264561295 | 13.347664992606 |

新窗口C1相对C0的MAE降低27.16861853%；原Q4为24.23172448%（2203小时、92日）。模型字节未变，差别伴随评价集合变化，不能解释为重训变好，也不能将窗口调整作为改善模型的证据。旧参数、结果、表、摘要的实际内容在history/stage-A-initial/，修订前漂移快照另存；修订理由在notes/stage-C-revision.md及validation/stage-C/revision-review.json。

D-INVALID-TEST原来因共享验证产物传递引用参数/结果而一起过期。本次实际重跑无效起止日期，退出2，未产生输出目录，负例测试时旧规范成果前后SHA相同；这是成功拒绝无效输入。现改为专用负例验证产物，旧综合验证保留为历史。D-CALC、D-INVALID-TEST、D-SYNTH均为版本2。

D-SOURCE-CHECK保持版本1，整个登记封装与修订前完全相同：原始8645行CSV、来源卡、独立来源核验文件字节不变，来源活动不依赖评价起点，因此无需判失败或重做。原始数据、科学脚本、冻结模型完整SHA分别为：

- data/hour_2011.csv：294d25e98ef1c9c9cec746e17ba3ff9818627ba5aa14baf1b93db7ae218de115
- scripts/compute.py：e7b2f754ed7a449ee76a45c80ce3888a36be20f5c783f9a67c630fc7c25c74a1
- model/frozen.json：9642962f82483eded749138c58ead59c51e1aa2c8a7e99c2185ec33474f11025

## 失败、范围和下一步

首次自写核验代码对csv.reader作切片，实际出现TypeError，核验退出1；外层记录随后因verification.json尚未生成再次报错。原失败代码及报错保留在history/stage-C-verification-failure/，没有把首次失败改写为成功。仅修复自己的核验代码，使用新计算目录重试后完成核验，科学脚本未改。重试误用了同名stdout/stderr文件，覆盖首次科学计算器原始日志；首次数值输出目录和核验失败输出仍保留，无法恢复的首次原始stdout不补造。详见execution.json及项目修订记录。

最终check前仅剩断点旧；保存当前下一步后，07-final-check.txt与08-final-resume.txt均无发现。checkpoint当前是身份和流程结论，scientific_validity仍为not-assessed。本次科学结论仅为指定观察小时、既定冻结模型下的描述性数值和摘要一致性，没有置信区间、因果识别、未来年保证或人类专家认可。

来源身份保留UCI数据DOI 10.24432/C5W894及本地2011切片SHA；未获取原ZIP、完整CSV或网站，来源卡的17379/17389差异按给定资料保留。D-REMOTE仅DOI 10.1007/s13748-013-0040-3身份元数据，没有本地文章绑定或当前远端检查。notes/unregistered-scratch.md仍未登记；自动检查只覆盖19个已绑定本地文件及其登记依赖，不能扩张到全部项目文件。原始CSV/PDF仅私有缓存，未复制进外部答卷或发布。

具体下一步：将2011年11月至12月的冻结模型指标与更新摘要交作者内容复核；保留原Q4结果作历史记录。恢复先核对当前2011-11-01至12-31参数与1460小时结果的依赖；不重训，不外推2012。

恢复命令与新目录复算方式在RECOVERY.md；当前数值、表与可交作者摘要在results/，实际命令、核验与修订证据在validation/stage-C/。
