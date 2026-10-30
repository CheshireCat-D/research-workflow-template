# 恢复与继续

当前元数据唯一权威：`.research/state.json`；历史约束、副本与旧交接不能覆盖当前有效版本。恢复后在项目目录运行：

```sh
python3 -I -B scripts/manage.py status
```

该命令只读核对登记材料、各活动的完成指纹与逻辑指纹，并将 T-CALC 的过期状态传播给 T-SYNTH。覆盖包括 results/table.csv。目录 mtime 不作为科学版本。脚本相对于自身定位项目，迁移无需原绝对目录、第三方包或外部 output。所用 guarded restore 依赖 Path.is_relative_to，需 Python 3.9+。

当前已真实使用原脚本重算 alpha=0.05、rho=4（观察前固定）、v=[0,1,10,100]，核对 JSON、CSV、四点摘要。实际执行和核对在 `.research/evidence/C/`。下一步：将 rho=4 边界表与更新摘要交作者内容复核；暂不扩展到事后选择 rho。目标期刊未定，尚无人类专家认可，未获投稿授权。

科学范围：l0=1；S 与 −S 在同一非负内在时间 V 下满足相应 sub-Gaussian 指数控制；alpha 是双侧总预算。程序只评价所给公式，不证明覆盖、不模拟覆盖、不判断新颖性。primary PDF、原 compute.py、manage.py 与固定来源卡未变；来源分支独立于此次参数选择，原有限来源身份核验可保持完成。PDF 只整体哈希，未抽取正文或看页；来源卡的页码/命题是所给释义，未独立原文核验。T-REMOTE 只有身份元数据，无本地内容绑定或远端当前性检查；notes/unregistered-scratch.md 保留但未纳入自动依赖覆盖。

初始 rho=1 的完整参数/结果/表/摘要在 `.research/versions/A-initial/`。修订前漂移态完整字节、旧权威状态与旧选择在 `.research/checkpoints/C-drift-before-recompute/files/`，索引是其上级 index.json。中间只读检查保存在 `.research/evidence/C/intermediate-status-execution.json`，当时新断点字节新鲜但 T-CALC/T-SYNTH 仍需复核；保存断点没有重新完成它们。作者授权原件在 `.research/provenance/C/author-revision/`，修订理由与新旧范围在 state.json revision_history。

如授权写入阶段需再次计算，用未占用的新目录（保留历史，勿覆盖已有结果）：

```sh
python3 -I -B scripts/compute.py --root . --output .research/evidence/NEW-UNUSED-NAME
```

先保存当前完整字节与状态，再运行上述重算，核对参数绑定、JSON、CSV、摘要和来源不变，最后才更新活动指纹/选择/状态。脚本重算不会自动更新权威状态。只读阶段禁止写入。

原始版本恢复支持冲突保护：

```sh
python3 -I -B scripts/manage.py restore-initial notes/parameters.json --expected-current CURRENT_FULL_SHA256
```

默认为预览；只有授权写入才加 --write。缺失时用 MISSING。命令核对归档与当前 SHA，冲突拒绝，恢复前保留现有内容。恢复不会将活动标成完成。A 中受控 alpha=1 拒绝的真实退出 2 与原始错误仍在 `.research/evidence/A/rejected-execution.json`；不是本阶段失败，不可抹除。

原始 PDF 只作私人研究缓存，不公开分发；公开交付只用来源身份、项目结果与自写程序。供给截止日 2026-12-15 属组织者给定约束。
