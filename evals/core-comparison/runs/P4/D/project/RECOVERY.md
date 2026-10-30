# 项目恢复

权威配置为project.json，权威记录、版本、游标与断点为records/registry.json。context/保存初始约束及义务，context/stage-C/保存后续明确授权；初始Q4范围不是当前窗口，PROJECT.md与旧handoff不覆盖较新的登记。

在项目根用Python 3.11+执行：

```text
python3 -I -B .agents/skills/_rw-runtime/tools/research.py resume --root .
python3 -I -B .agents/skills/_rw-runtime/tools/research.py check --root .
```

这些只读命令不执行计算。若材料变化，先保留旧字节与原因，复核受影响活动，再使用register或register-batch写入；替换须显式给出expected-version。checkpoint只保存状态，不使旧工作重新有效。

当前范围2011-11-01至2011-12-31，1460观察小时、61日，冻结模型不重训。结果见results/；核验、实际argv、失败和补救见validation/stage-C/及notes/stage-C-revision.md。若确需再复算，选择不存在的新输出目录：

```text
python3 -I -B scripts/compute.py --root . --output validation/NEW-UNUSED-RUN
```

不要原样重跑validation/stage-C/verify.py覆盖旧日志；该脚本保留本次实际核验代码，固定输出目录已存在。初始参数、结果、表、摘要在history/stage-A-initial/；尚未重算的漂移态和中间check原始输出在history/stage-C-before-recalculation/。当前参数的修订依据在context/stage-C/AUTHOR-REVISION.md，初始记录和选择的历史内容保留在登记history及registry快照。

D-SOURCE-CHECK独立于评价窗口：原始8645行2011切片、来源卡和来源核验文件不变，保持已完成。来源卡所列原完整hour.csv的17379行与网站metadata的17389差异只按给定来源保留；本次没有获取原ZIP、网站或文章。D-REMOTE仅DOI身份，无本地内容绑定或当前远端检查。notes/unregistered-scratch.md不登记、不作为依赖，不在自动变化检测覆盖。原CSV/PDF仅作私有研究缓存，data/被gitignore排除，不得外发。

其他约束保持：截止2026-12-15为给定作者约束，期刊未定，离线标准库，不采新数据、不重训、不外推2012；没有人类专家内容认可或外部投稿授权。新旧降幅变化来自评价集合不同，不能作为模型改善证据。

下一步：将2011年11月至12月的冻结模型指标与更新摘要交作者内容复核；保留原Q4结果作历史记录。
