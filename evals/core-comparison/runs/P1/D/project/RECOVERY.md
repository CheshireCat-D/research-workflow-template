# 恢复说明

唯一权威配置为 project.json；唯一权威登记、版本历史及检查点为 records/registry.json。本文、旧handoff及provenance/initial不覆盖较新的有效登记。

从项目根目录执行（Python 3.11+，仅标准库）：

```sh
python3 -I -B .agents/skills/_rw-runtime/tools/research.py resume --root .
python3 -I -B .agents/skills/_rw-runtime/tools/connect_skills.py check --installed-only --root .
```

恢复只读且不执行登记中的命令。先读 configuration、activities、findings、checkpoint。文件或记录变化先定位及实质复核受影响分支；新检查点不清除旧活动失效。同ID替换先show读取envelope.version，再register --replace --expected-version N；不手改权威JSON。

当前作者批准范围见 provenance/stage-c/AUTHOR-REVISION.md 和 approved-parameters.json：alpha=0.05、rho=4、rho在观察前固定、v=[0,1,10,100]。当前结果依次为 4.895493661361633、5.57431973357386、10.070709270872976、31.015388968276124，对应 results/result.json、table.csv、summary.md。本轮真实重算及逐项比较见 notes/stage-c-validation.json；公式计算不构成新覆盖证明，且未进行人类专家内容认可。T-SOURCE-CHECK只核对固定来源身份/卡片，与rho变化独立，其原来源/PDF/来源卡未改。

初始rho=1完整参数、结果、表、摘要及SHA在 history/stage-a-initial。history/stage-c-before-recompute保存本轮重算前rho=4参数、仍rho=1的结果/表/摘要、当时配置/登记/旧恢复说明及manifest。validation/stage-c/checkpoint-drift.json与check-drift.json保存重算前的新断点和真实检查：断点current，但T-PARAM file_changed，T-CALC/T-SYNTH仍stale；保存本身不等于重新核验。内部registry快照仅历史，不能作当前权威。

复算用原 scripts/compute.py --root . --output 一个尚不存在的新目录；使用python3 -I -B。按JSON参数、值、完整输入SHA及CSV数值逐行比较，再审摘要舍入与范围。原阶段A的alpha=1控制失败及原有效内容保留证据仍在notes/stage-a-validation.json、validation/stage-a，未覆盖。

其他约束见provenance/initial/constraints.json、obligations.json和source-identities.json：中文；截止2026-12-15为任务作者给定；离线标准库；不收新数据、不重训/重拟合；目标期刊未定；无人类专家认可且无投稿授权。原始PDF为私有缓存，不再分发。T-REMOTE仅来源身份，无本地内容绑定或当前远端核验；notes/unregistered-scratch.md未登记，不纳入自动覆盖。

当前具体下一步：将rho=4、alpha=0.05、v=[0,1,10,100]的边界表与更新摘要交作者内容复核；暂不扩展到事后选择rho。若恢复发现漂移，先查明并实质复核T-CALC及依赖T-SYNTH后显式更新登记。
