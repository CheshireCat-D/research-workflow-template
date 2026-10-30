# 阶段 C 续作结果

已按作者授权完成 rho=4 的真实复算、成果和摘要修订，最终登记材料无缺失或未解释漂移。权威状态是项目内 `.research/state.json`（revision 2），下一步为将 `results/table.csv` 与 `results/summary.md` 交作者内容复核，暂不扩展到事后选择 rho。尚无人类专家内容认可，未获投稿授权，目标期刊未定。

## 新断点与中间检查

在任何重算前，已将原有项目的所有文件完整保存到 `.research/checkpoints/C-drift-before-recompute/files/`，含旧权威元数据、旧选择、旧结果、旧摘要和实际已经漂移为 rho=4 的参数。索引 `index.json` 逐文件记录完整 SHA256 与字节数。另把当前观测字节写入新的 checkpoint 字段，未改旧活动完成时的指纹。

随后真实运行 `python -I -B scripts/manage.py status`，原始标准输出为本输出目录 `intermediate-status.stdout.json`，完整执行记录是 `intermediate-status-execution.json`；项目内也保存原始执行记录。检查得到：新 checkpoint 为 fresh_for_registered_bytes，`notes/parameters.json` 相对旧有效材料已变；T-CALC 为 needs_recheck，T-SYNTH 因依赖 T-CALC 也为 needs_recheck，T-SOURCE-CHECK 仍为 done。此时结果与摘要仍是 rho=1，权威约束/旧选择也仍是旧范围。保存新断点只证明观测字节已保存，不能使旧完成工作重新有效。中间证据保留，未被最后成功覆盖。

## 真实复核与修订

先确认当前参数 JSON 与作者 approved-parameters.json 的内容一致，再将授权原件保存到 `.research/provenance/C/author-revision/`。按授权接受 alpha=0.05、rho=4（观察前固定）、v=[0,1,10,100]，保留其余约束；在活动暂置需复核后，用原封未动的 `scripts/compute.py` 实际生成新的 `.research/evidence/C/recomputed/result.json` 与 `table.csv`，退出码为 0。以下为边界值：

| v | b(v) |
| --- | ---: |
| 0 | 4.895493661362 |
| 1 | 5.574319733574 |
| 10 | 10.070709270873 |
| 100 | 31.015388968276 |

计算式为 b(v)=sqrt((v+rho)[log(1+v/rho)+2 log(1/alpha)])。已核对四点网格、参数/计算器 SHA 绑定、CSV 与 JSON 的全部四行数值，并用代数等价的数值表达式独立核算（相对/绝对容差 1e-14）；这仍只是公式数值复核。新结果、表复制至正式 results，摘要更新四点值、假设和下一步；正式结果和表与本次真实运行产物字节一致。

已更新材料 SHA/字节数绑定、当前范围、T-PARAM→T-CLAIM 关系的参数范围、T-CHOICE 选择及理由、T-CALC/T-SYNTH 的完成指纹和活动证据。T-SOURCE-CHECK 的完成指纹、活动证据和有限核验范围原样保留：其输入固定 PDF 和输出来源卡均逐字节未变，且不依赖 rho，因此不能因参数变化将此独立分支判失败。

最终真实只读状态检查退出 0，changed_paths=[]、missing_paths=[]，三个活动的有效状态均 done；其含义只是所声明局部工作已做。原始输出在 `final-status.stdout.json`，项目证据在 `.research/evidence/C/final-status-execution.json`。在该检查后又保存 `.research/checkpoints/C-final-verified/`，含当前权威状态、恢复说明、参数及正式成果的完整字节及索引。

## 历史内容、失败与恢复

最初 rho=1 的参数、结果、表、摘要完整字节仍在 `.research/versions/A-initial/`，本次逐项确认其 SHA 与原版本索引一致；不是仅保留旧版本标签。阶段 C 修订前的真实字节与旧选择保存在漂移态快照，修订原因及新旧范围在 state.json 的 revision_history。旧 RECOVERY.md 也在漂移快照，当前恢复说明已同步为 rho=4。

本阶段执行无非零退出或失败修补；中间需复核是检测到真实过期，并非程序错误。此前受控 alpha=1 输入拒绝的退出 2 与原始 ValueError 记录仍完整保存在 `.research/evidence/A/rejected-execution.json`，未改写为成功。本阶段所有实际命令和输出、读取 SHA/字节数在 `execution.json`，文件清单在 `inputs-and-artifacts.json`；执行记录与主报告分离。网络调用 0，无安装、重训或来源/既有脚本更改。

迁移后只需项目与任一具备标准库的 Python 3.9+：在项目目录执行 `python3 -I -B scripts/manage.py status`。无需本阶段外部输出或原绝对路径。若以后获得写入授权才可向未使用的新目录执行 calculator，再实际核对并更新权威状态；恢复原版有 --expected-current 完整 SHA 的冲突保护，恢复本身不会完成活动。只读阶段不得执行写入恢复。

## 来源与研究范围

primary 为所给 Howard 等论文的 arXiv:1810.08240v9 本地缓存，身份 URI 为 https://arxiv.org/abs/1810.08240v9，所给 DOI 为 10.1214/20-AOS1991；本阶段未联网验证。缓存 `sources/howard2021-arxiv-v9.pdf` 为 1494142 字节，SHA256 为 eb3efd547349adfbff25514ae0854c142cd29b96b398be38c9000d69a2f64ca8，保持不变。PDF 仅整份字节读取以哈希/保存，未抽取正文、查看页面或独立核验定理。来源卡 p10 (14)、p28 Proposition 5 (51) 是所给释义的定位陈述。

科学条件保留为 l0=1，S 与 −S 在同一非负内在时间 V 下满足相应 sub-Gaussian 指数控制；alpha 是双侧总预算，rho 在观察前固定。换一个预先固定正 rho 的程序计算没有证明新的覆盖保证，也没有模拟覆盖验证或新颖性结论。T-REMOTE 仅元数据，未绑定本地正文或检查远端当前内容。notes/unregistered-scratch.md 虽完整保留并参与快照清单，但未登记为科学依赖，不在自动失效传播范围；不宣称全项目自动覆盖。原始 PDF 仅作私人研究缓存，不在外部输出分发；公开交付只用来源身份、结果和自写程序。模型、温度、seed、token 与系统上限均未知为 null。
