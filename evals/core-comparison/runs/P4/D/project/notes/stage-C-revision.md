# 参数修订与复核记录

作者明确批准评价窗口从2011-10-01—12-31改为2011-11-01—12-31；未更改原始数据、脚本、冻结模型或其他约束。新旧降幅差异属于评价集合变化，不是模型重训改善。

授权原文与批准参数保存在context/stage-C/，原始约束context/保持原样；当前有效窗口以新版D-PARAM、D-CLAIM、D-CHOICE及其权威登记为准。

修订前先保存断点并实际check，发现D-CALC、D-INVALID-TEST、D-SYNTH仍过期，D-SOURCE-CHECK仍有效；原始输出及registry快照保存在history/stage-C-before-recalculation/。后续实质复算与逐项核对见validation/stage-C/verification.json及revision-review.json。

第一次自写核验脚本发生csv.reader切片TypeError，原代码与报错保留在history/stage-C-verification-failure/；修复自己的核验代码后在新目录复算成功。科学计算器未修改。重试覆盖了首次科学计算器stdout/stderr同名日志，首次数值输出仍在validation/stage-C/recalculation/；此日志缺口保留，不补造原输出。

独立来源活动不依赖评价窗口，原始CSV、来源卡及其核验文件身份不变，因此保持D-SOURCE-CHECK完成且不重新登记。D-INVALID-TEST曾因其共享验证输出传递引用参数/结果而过期，本次实际重跑并改用专用负例证据，保留旧综合验证记录。

下一步：将2011年11月至12月的冻结模型指标与更新摘要交作者内容复核；保留原Q4结果作历史记录。没有人类专家内容认可或投稿授权。
