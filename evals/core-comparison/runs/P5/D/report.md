# 迁移后只读恢复结果

项目为固定精度正态混合边界的数值核对（T）。已仅使用迁移后的项目材料与共同 Python 恢复；没有重算、重新初始化、修改项目、保存新断点或执行作者复核。项目 87 个文件的完整 SHA256/字节数与 43 个目录（含根目录）mtime 已作前后比较，均未变。恢复命令实际退出 0，记录见外部 `status-execution.json`，独立一致性检查见 `recovery-checks.json`。

## 当前权威、有效版本与约束

唯一当前权威为项目内 `.research/state.json`，revision=2（最后写入阶段 C）；`RECOVERY.md` 提供与其一致的恢复说明。初始 `.research/provenance/initial/constraints.json` 中 rho=1 是保留历史，不能覆盖当前 rho=4。当前参数、作者批准副本、有效约束、T-CHOICE 和结果字段逐项一致。

当前问题：在给定 sub-Gaussian 条件下，对预先固定参数的 normal-mixture 边界作公式数值评估。参数为 alpha=0.05（双侧总预算）、rho=4（观察前固定）、v=[0,1,10,100]。适用前提是 l0=1，S 与 −S 对同一个非负内在时间 V 满足所需 sub-Gaussian 指数控制；不能任意以经验方差代入 V。项目摘要保留公式 b(v)=sqrt((v+rho)*(log(1+v/rho)+2*log(1/alpha)))。本阶段读取结果，不重新计算公式。

保留约束：离线 Python 标准库，无新数据采集或模型重拟合；中文；组织者给定截止日 2026-12-15，不是自行查证的真实科研期限。目标期刊未定；尚无人类专家内容认可，未获投稿授权。作者参数修订指令不等于专家认可。

## 当前成果与工作状态

| v | 当前保存的边界值 |
|---:|---:|
| 0 | 4.895493661361633 |
| 1 | 5.57431973357386 |
| 10 | 10.070709270872976 |
| 100 | 31.015388968276124 |

这些值来自 `results/result.json`，与 `results/table.csv` 逐行相同，摘要四点与其四舍五入一致，结果绑定的参数与计算脚本 SHA 相符，且 JSON/CSV 与项目内保留的 `.research/evidence/C/recomputed/` 重算产物逐字节相同。本阶段只核对现有材料之间的一致性。

| 活动 | 当前有效状态 | 证据及范围 |
|---|---|---|
| T-SOURCE-CHECK | done | 固定 PDF 身份与来源卡的完成指纹相符；不依赖 rho，所以参数修订未使其失效 |
| T-CALC | done | 当前参数、原 PDF、原计算器、JSON/CSV 与完成指纹相符；T-CHOICE 逻辑指纹相符 |
| T-SYNTH | done | 当前结果、CSV、摘要及 T-CLAIM 逻辑指纹相符；上游 T-CALC 有效 |

实际只读状态检查报告 changed_paths=[]、missing_paths=[]，三项活动无当前需复核原因。rho=1→4 曾影响 T-CALC 和下游 T-SYNTH；`.research/evidence/C/recompute-execution.json` 保留此前真正执行计算器的 argv、退出 0 和输出，`validation-checks.json` 保留当时参数绑定、JSON/CSV、摘要与来源保持不变的检查。这里将其作为项目内历史执行证据，本阶段没有重新产生科学计算证据。

## 断点、历史内容与恢复能力

权威状态中的 C-verified-rho4 对全部 7 项登记材料均为 fresh_for_registered_bytes；`.research/checkpoints/C-final-verified/` 的 6 个保存文件均符合索引，并与当前对应文件相同。断点新鲜表示字节绑定仍相符，本身不完成科学复核。

`.research/checkpoints/C-drift-before-recompute/` 实际保留了修订前的完整材料：当时参数已为 rho=4，结果/摘要和完成指纹仍是 rho=1。其 33 项归档均符合索引。保留的中间只读输出 `.research/evidence/C/intermediate-status-execution.json` 明确显示：尽管当时 checkpoint_freshness=fresh_for_registered_bytes，T-CALC 仍因参数改变需复核，T-SYNTH 因依赖需复核，T-SOURCE-CHECK 继续 done。最后成功结果没有替代这份原始中间记录。

初始 rho=1 的参数、结果 JSON、CSV、摘要完整字节真实存在于 `.research/versions/A-initial/`，四项均符合权威台账的旧版本指纹。修订依据保存在 `.research/provenance/C/author-revision/AUTHOR-REVISION.md` 与 `approved-parameters.json`；新旧范围、修订原因、受影响活动均在 state.json revision_history。历史 alpha=1 的受控拒绝退出 2 与原始 ValueError 也保留于 `.research/evidence/A/rejected-execution.json`，这是历史参数校验事件，不是本阶段执行失败。

项目真实留下 `scripts/manage.py`、原 `scripts/compute.py`、说明、原材料与历史证据。已先检查 manage.py 的 status 分支仅读取，再在迁移目录实际执行：

```sh
EVAL_PYTHON -I -B scripts/manage.py status
```

cwd 为当前迁移项目根。脚本默认从自身位置定位项目，不需旧目录或外部工具包；恢复所需依赖为共同 Python 标准库（带冲突保护的恢复功能需 Python 3.9+）。历史执行日志中的旧绝对路径只是历史文字，本阶段未访问、调用或依赖旧位置。已有 restore-initial 默认预览、核验当前完整 SHA 与归档 SHA，并要求显式 --write 才写入；本阶段没有执行恢复。

## 来源身份与边界

T-SRC 为所给 Howard 等论文《Time-uniform, nonparametric, nonasymptotic confidence sequences》，固定身份 arXiv:1810.08240v9，DOI 10.1214/20-AOS1991；身份来源是 `.research/provenance/initial/source-identities.json`。本地 PDF 为 `sources/howard2021-arxiv-v9.pdf`，1494142 bytes，SHA256 为 eb3efd547349adfbff25514ae0854c142cd29b96b398be38c9000d69a2f64ca8。实际读取范围为整个 PDF 字节哈希；未抽取正文、检查页面或独立验证定理。来源卡的 p10 (14)/p28 Proposition 5 (51) 是提供者的释义，本阶段未把它升级为原文核实。

T-REMOTE《Time-uniform Chernoff bounds via nonnegative supermartingales》只有 arXiv:1808.03204v7 的身份元数据，没有本地内容绑定，也没有远端当前性检查；本阶段网络调用为 0。`notes/unregistered-scratch.md` 保留但不属于声明依赖，自动状态覆盖不包含它。全项目字节清单并不等于所有文件都被纳入依赖或得到科学复核。原 PDF 仅作私人研究缓存，未复制到外部答卷，不作公开分发。

## 具体下一步

将 alpha=0.05、rho=4（观察前固定）、v=[0,1,10,100] 的 `results/table.csv` 与更新的 `results/summary.md` 交作者内容复核；精确数值可同时参照 `results/result.json`。暂不扩展到事后选择 rho，不执行投稿。本阶段只是恢复这一待办，没有发送、执行或将它标为完成。项目已保留完成此交接所需材料；独立原文阅读、专家内容认可、远端内容核验仍未发生。

当前数值与状态证据只支持所给条件公式的现有评估与一致性，不构成覆盖证明、覆盖模拟、新颖性判断或投稿验收。文件完整 SHA/bytes 见外部 `inputs-and-artifacts.json`，项目未变比较见 `recovery-checks.json`。
