# 参数修订与当前恢复状态

已按明确授权使用 alpha=0.05、观察前固定 rho=4、V∈{0,1,10,100} 真实复算，更新结果、表格、摘要、材料绑定、关系、选择和受影响活动。权威状态在 `project/research/state.json`，元数据修订为4；截止日2026-12-15、离线标准库预算、不采新数据/不重拟合、期刊未定等约束未变。

## 先保存漂移，再实际复核

未重算时的全部既存项目文件及完整 SHA/字节/mtime 清单保存在 `project/.history/C-drift/files/`、`manifest.json`；新漂移断点在同目录 `checkpoint.json`。保存后立即运行现有 `resume.py`，真实退出1。原始标准输出保存在本交付目录 `intermediate-resume.stdout`，同时在项目 `validation/stage-C-intermediate-resume.stdout` 保留，未被最终成功输出覆盖。

该中间检查确认：`notes/parameters.json` 已变成rho=4，而权威配置和旧结果仍为rho=1。新断点自身 fresh=true，但 T-CALC 和 T-SYNTH 仍 stale；后者还受到计算依赖失效的影响。因此保存新断点没有重新验证先前完成的工作。独立 T-SOURCE-CHECK 仍 done：原PDF、来源身份记录、固定核验卡及该活动捕获的文件/记录均未变化，rho不是此活动依赖。

## 真实计算与修订

使用未改动的 `scripts/compute.py`，通过离线Python标准库实际计算到独立新目录 `validation/stage-C-recompute/`，退出0。核对批准参数与现有参数、结果记录的输入SHA、四点网格、直接公式数值及JSON/CSV逐项对应，均通过。canonical结果从该实际输出更新至 `results/result.json` 与 `results/table.csv`，摘要已重新写入并完整读取核对。

| V | rho=4边界值 |
|---:|---:|
| 0 | 4.895493661362 |
| 1 | 5.574319733574 |
| 10 | 10.070709270873 |
| 100 | 31.015388968276 |

完整精度与输入SHA见JSON；本表仅显示12位小数。计算式为 sqrt((V+rho)·(log(1+V/rho)+2log(1/alpha)))，l0=1，alpha为两侧总错误预算。固定原始资料要求 S与−S 对同一非负内在时间V满足相应sub-Gaussian指数控制；V不能被任意经验方差替代。本轮改变另一个预先固定的正rho，没有改变alpha或预先固定政策；程序复算没有证明新的覆盖保证。

T-PARAM、T-CLAIM、T-REL、T-CHOICE、T-RESULT、T-SUMMARY、T-CALC、T-SYNTH 均显式升为版本2；来源、原始材料、计算器、固定来源卡及来源核验记录仍为版本1。修订使用当前元数据修订2及各记录预期版本，通过现有带冲突保护的 `update-state.py` 实际提交，退出0。该提交本身仍未重新绑定活动；只有在实际复算/审阅之后才显式更新T-CALC和T-SYNTH的文件SHA及记录版本捕获。T-SOURCE-CHECK未重新绑定。

初始rho=1的参数、结果、表格、摘要完整内容保留在 `.history/A-initial/files/`；C修订前的完整现状在 `.history/C-drift/files/`；每次旧权威状态保留在 `.history/metadata/revision-1.json` 至 `revision-3.json`。明确授权及实际修订patch保留在 `provenance/stage-C/`。实际验证记录在 `validation/stage-C.json`，中间、最终恢复输出分别保存。原PDF、计算器、来源核验卡、现有rho=4参数文件的字节与mtime均未修改；数值成果和状态依授权更新。

## 最终检查与下一步

最后运行现有只读恢复程序，退出0：changed_or_missing_paths为空，三项活动的effective_status均为done，最终断点fresh=true。项目内保存 `research/checkpoints/C-final.json`。这仅说明所声明依赖和登记当前一致；done表示这次有界工作实际完成，不是内容认可或科学认证。

可执行恢复命令：在项目根执行 `python3 -I -B resume.py`；程序及所有必要状态都在项目中，不依赖本交付目录或原输入路径。当前具体下一步已写入权威状态：将rho=4的边界表与更新摘要交作者内容复核，确认V的含义及过程控制条件，暂不扩展到事后选择rho。没有人类专家认可、形式化验证或投稿授权。

## 来源范围与保留的异常

原PDF是 Howard等 (2021), arXiv:1810.08240v9，DOI 10.1214/20-AOS1991；完整SHA为 `eb3efd547349adfbff25514ae0854c142cd29b96b398be38c9000d69a2f64ca8`，1494142字节。此次读取完整字节仅为指纹和私有快照保留，读取来源卡及已存身份记录；没有在本轮阅读PDF页面、验证公式出处或证明。继承的来源活动原范围是身份版本核验，不能将其表述为全文科学审稿。T-REMOTE仅有远端来源身份，无本地内容绑定，也没有联网核查。`notes/unregistered-scratch.md`不进入自动活动失效覆盖；历史快照保存它的字节不扩大此覆盖。

第一次批量显示输出被工具截断，已保留该执行异常说明；随后完整重读两个本地状态脚本，并完整解析权威JSON，未用截断显示代替状态检查。中间检查退出1是实际发现过期活动，已按顺序保存并修复其原因；没有用最终退出0覆盖。计算和修订未出现非零退出。网络调用0，未安装依赖，未知模型/温度/seed/token和系统上限保持null。原始PDF只在本项目私有缓存与历史快照中保留，不对外分发。
