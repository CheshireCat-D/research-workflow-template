# 恢复与继续

本项目当前元数据的唯一权威为 `.research/state.json`。初始材料、旧交接、输入约束副本仅是历史依据；不能据旧笔记覆盖实际较新的有效版本。恢复后先核对当前文件，不因活动历史状态为 done 就沿用。

在项目内用任何可用的 Python 3.9+ 标准库环境执行（脚本不依赖原绝对目录、第三方包或本阶段外部 output）：

```sh
python3 -I -B scripts/manage.py status
```

该命令只读，比较当前登记材料与各活动完成时输入/输出及逻辑声明/选择的指纹，再沿 T-CALC → T-SYNTH 传播需复核状态。登记范围含 companion `results/table.csv`。目录 mtime 不作为科研版本。`T-SOURCE-CHECK` 仅核对所给固定本地来源身份和卡片口径；未读 PDF 正文，未联网。`T-REMOTE` 只有身份元数据，未绑定本地内容；`notes/unregistered-scratch.md` 被保留但不在自动依赖范围。

当前条件：l0=1；S 与 −S 在同一非负内在时间 V 下满足相应 sub-Gaussian 指数控制；alpha=0.05 是双侧总预算，rho=1 在观察前固定，v=[0,1,10,100]。这里只计算给定公式，不证明覆盖、不做模拟验证、不声称新颖性。初始摘要已与真实重算和表核对。

具体下一步以 state.json 的 next_action 为准：先运行只读状态检查，再将当前四点边界和条件交作者讨论。尚无人工专家批准，目标期刊未定，未经内容复核不投稿；供给截止日 2026-12-15 是组织者给定约束。

## 完整内容与失败记录

`.research/versions/A-initial/` 保存 parameters、result、table、summary 的原始完整字节和索引，可在未来覆盖/删除后恢复。大型 PDF 只保留项目内原缓存一份。`.research/evidence/A/` 保存正常实际执行、结果、逐项核对、无效参数退出 2 的错误及前后 SHA/mtime 证据。无效 alpha=1 是受控输入拒绝测试，未改变有效成果。

若需恢复初始内容，先检查当前完整 SHA，再运行预览，例如：

```sh
python3 -I -B scripts/manage.py restore-initial notes/parameters.json --expected-current CURRENT_FULL_SHA256
```

明确需要写入的阶段才加 `--write`。缺失文件用 `--expected-current MISSING`。工具先核对已保存内容 SHA 和当前 SHA，冲突即拒绝；写入前归档现有内容。恢复不会更新元数据或把活动标成已完成。之后按真实复核更新 state.json、保留修订前字节与依据，再重算受影响活动，不能靠保存 checkpoint 消除过期。只读阶段禁止任何恢复写入。

外部验证的 CSV 为标准库 csv 默认 CRLF，原表为 LF，解析行和数值完全一致。结果 JSON 字节一致；不能把 CSV SHA 不同误报为数值不同。

## 原始来源分发范围

原 PDF 仅供私人研究缓存，不放进公开仓库；公开交付使用来源身份、项目结果与自行编写程序。URL 是所给身份信息，本阶段未远程访问。来源卡给出的 p10 (14)、p28 Proposition 5 (51) 仅为所给卡片的定位陈述，本阶段未逐页核验。
