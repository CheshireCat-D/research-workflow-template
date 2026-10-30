# 项目恢复

权威配置为 project.json；权威登记、版本与游标为 records/registry.json。context/ 保存给定原始约束与义务，只作来源，不覆盖以后显式修订后的当前配置/登记。PROJECT.md 和本文件不反向覆盖登记。

先用可用的 Python 3.11+ 运行：

```text
python3 -I -B .agents/skills/_rw-runtime/tools/research.py resume --root .
python3 -I -B .agents/skills/_rw-runtime/tools/research.py check --root .
```

指令不自动执行计算。恢复后按实际任务决定下一步；变更登记须使用 register 或 register-batch，替换显式 --replace --expected-version N。历史初始内容可从 history/stage-A-initial/ 的四份原字节恢复，manifest.json 给出SHA；context/ 保存本次来源/约束/逻辑义务。不能只保存新checkpoint来承认旧工作仍有效。

冻结模型为所给2011年1—9月参数；本阶段是2203观察小时、92日的2011第四季度描述性复算，不重新拟合、无置信区间、无因果或2012外推。未有人类专家批准；未授权外部投稿。截止日2026-12-15为给定项目约束，并非观察到的真实截止日；目标期刊未知，project.json保留null。

来源卡记录原完整CSV的17379/官网metadata的17389差异；本次只独立检查给定8645行2011切片及本地SHA，未访问原ZIP/网站/文章。D-REMOTE仅身份元数据，没有本地内容绑定。notes/unregistered-scratch.md不登记，不是计算依赖，不在自动变化检测覆盖内。原始CSV/PDF只留私有研究缓存；data/被gitignore排除，无外发。

验证与两次真实命令、受控无效输入退出2及失败前后SHA在validation/stage-A/。失败是预期输入校验；原有效成果未改变。

具体下一步：2011第四季度指标与摘要已逐项核对；下一步由作者讨论该描述性比较的解释与用途。恢复先运行项目内 resume，核对当前 parameters/result/table/summary 及依赖；若有漂移，保留旧字节与原因并复核 D-CALC、D-SYNTH 后显式重登，不重训或外推2012。
