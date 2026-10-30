# 独立机械、数值与工程能力审计

本报告只审计真实档案、数值复算和冻结工程探针，不作科研内容评分，不增加共同科研分，不评总冠军。所有无效写入仅发生在 mechanical-audit/ 独立副本，原封存项目与主链未改。

24个阶段的封存项目计数、分配信息和封存输出SHA全部相符。6次统一事件从A到B重新比较，均仅改变 notes/parameters.json，参数语义与相应T/D新范围一致。12份B/D前后清单逐项相同，覆盖完整文件字节、大小、mtime和目录mtime；当前封存副本也与原清单完全一致。6次D的旧项目和旧toolkit路径当前均不存在；baseline原本不依赖toolkit。迁移收据及本次执行只证明实际入口运行和路径不可达，隔离为指令边界，没有OS访问审计或公共缓存读取拒绝的系统调用证据。

12次A/C均在新副本运行原compute.py，全部exit0；result.json及table.csv与canonical逐字节相同。独立从T公式、D的CSV及冻结模型复算，未舍入结果/表格的最大绝对误差为 5.5511151231257827e-17。原source/model/code/source-card身份、实际参数SHA与结果绑定全部相符。摘要当前必需数字均按显示精度相符；12位小数舍入最大误差4.8316906031686813e-13，8位百分比（含新旧差）最大舍入误差4.0701153558586611e-09个百分点。该核对不验证原理论或科学真伪。

所有C都保留了真实漂移态的参数、旧result/table/summary，逐字节匹配对应B；初始四文件也全部匹配供给原字节。保存checkpoint没有冒充重验：P1/P4实际checkpoint接口、P3/P5/P6保留中间态的checkpoint-only重放均显示快照current/fresh时CALC与SYNTH仍stale/needs_recheck。P2保存独立checkpoint树，其status仍按旧绑定返回exit3并报告两个受影响活动；未提供自动checkpoint接口，不虚构该功能。

| 链 | 旧版本写入 | 悬空目标 | 合法前项+非法后项事务 | dirty checkpoint | 只读/迁移入口 |
|---|---|---|---|---|---|
| P1 | 逻辑record版本拒写，exit2 | statement_id未知目标拒绝 | exit2，authority原字节保留，前项未提交 | 自动保存后current但工作stale | 均无写入；迁移exit0 |
| P2 | 未提供写API/不可比 | 未提供/不可比 | 未提供/不可比 | 手工checkpoint树；status仍报受影响 | status与独立numeric verifier均通过 |
| P3 | global revision和record version均拒写，exit2 | 实际to字段未知目标被exit0接受 | 错版本后项整批拒绝；悬空目标后项与前项均提交 | 重放fresh但工作stale；无自动保存API | 均无写入；迁移exit0 |
| P4 | 逻辑record版本拒写，exit2 | statement_id未知目标拒绝 | exit2，authority原字节保留，前项未提交 | 自动保存后current但工作stale | 均无写入；迁移exit0 |
| P5 | expected-current文件SHA恢复拒绝旧SHA，exit2 | 未提供record写API/不可比 | 未提供batch/不可比 | checkpoint-only重放fresh但needs_recheck；status仍exit0 | 均无写入；迁移exit0 |
| P6 | state版本+SHA与record增量版本拒写，exit2 | 实际to_id字段未知目标被exit0接受 | 错版本后项整批拒绝；悬空目标后项与前项均提交 | 重放current但工作stale；无自动保存API | 均无写入；迁移exit0 |

四组关系探针均修改原来就存在的关系目标字段：P1/P4的statement_id、P3的to、P6的to_id；AUDIT-MISSING在各自原权威记录中确实不存在。原关系、候选关系、写后实际值和authority前后SHA见 mechanical-audit/relation-adaptations.json 与engineering.json。P1/P4此前的evidence_id未知端点测试也保留，结果同为拒绝。每组批次合法前项都在额外新副本独立执行成功（exit0并核对实际保存值），所以不以无效前项冒充回滚。P3/P6对无效版本后项的全批拒绝是真实保障；接受悬空关系是另一项观测，不能据此称其没有版本/事务能力。

P2的verify_current.py还真实独立复算D指标、输入SHA、CSV表、活动绑定和摘要，并在迁移副本exit0且不写文件。P5实际交付manage.py，支持只读status和有SHA冲突保护、旧内容归档的restore-initial；A/C/D均无.git，不归因为Git CAS。P5 status即使遇到漂移也exit0，自动调用者必须解析effective_status及changed_paths。

6组恢复输出都明确区分source-only身份和本地内容绑定；没有假造远端变更或把source locator当内容监测。未登记scratch及未知依赖不在自动覆盖范围。原字节历史均由执行者显式复制；core的metadata历史/checkpoint不会自动归档后来覆盖的研究文件原字节。

| 链 | 交付的自写管理接口 | 代码行数 | 随项目预制runtime |
|---|---|---:|---|
| P1 | 使用已封装native CLI | 0 | 68 files / 414713 bytes |
| P2 | management/status.py, management/verify_current.py | 86 | 无复制runtime |
| P3 | resume.py, update-state.py | 83 | 无复制runtime |
| P4 | 使用已封装native CLI | 0 | 68 files / 414713 bytes |
| P5 | scripts/manage.py | 90 | 无复制runtime |
| P6 | scripts/project_status.py, scripts/guarded_state_update.py | 87 | 无复制runtime |

该代码行数只算持久管理入口，不含供给的45行compute.py、研究验证脚本、编排脚本或历史副本。完整预制target-user-runtime.zip为528969字节，81文件，解压513293字节；P1/P4项目安装副本各68文件、414713字节。不能拿整个runtime与某组作者新增脚本混为同一开发负担，不能由字节推算token或由本次运行时间推算人类工时。

实际使用负担：native入口要求正确导出record data、使用kind/expected-version/batch格式并显式重绑活动，checkpoint可自动保存；P3要维护global revision、逐record expected_version及patch并手工保存checkpoint/重绑；P6要构造完整候选ledger、递增state/record版本、供给旧SHA并维护checkpoint；P2需显式文件版本/状态维护，数值核对脚本降低D复核操作负担；P5恢复需获得当前完整SHA，通用元数据修订和checkpoint仍依赖自写文件流程。以上为观察到的接口与维护步骤，不是人类耗时估计。

未测或不可比：未提供的更新/批次/自动checkpoint接口、真正OS公共缓存拒读、并发竞争/断电/恶意文件系统压力、远端当前内容、科研证明与新颖性。不同组未提供接口不算科研失败。未发生成功委派：一次数值子任务spawn被平台以agent thread limit拒绝，未收到外部内容，已原样记入attempt_notes.json。初始rg仅列出route文件名，没有打开route执行或评分内容。

完整机读结果：mechanical-audit.json。原始stdout/stderr/exit及前后文件SHA/mtime/目录mtime：mechanical-audit/receipts/。审计脚本与详细中间结果均在mechanical-audit/；所有原封存项目在结束时再次与未修改副本/原始清单一致。
