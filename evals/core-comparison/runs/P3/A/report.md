# 阶段 A 交付

项目已建于 `PROJECT_ROOT`。给定参数的实际重算成功，`results/result.json` 与 `results/table.csv` 和原有预制文件逐字节一致；当前三项活动在已声明的核验范围内完成，检查点新鲜，没有已登记材料漂移。预制内容来自提供材料，本次是在其基础上重算、核对并建立持久记录。

当前 alpha=0.05、rho=1，rho 在观察前固定；内在时间 v 为 0、1、10、100，边界分别为 2.4477468306808166、3.6563948713638483、9.606401928868575、32.73018624234933。另用等价标量公式与 CSV 数值核对，摘要中的 v=10 舍入值 9.606401928869 正确。

实际正常命令（退出 0）：

```text
EVAL_PYTHON -I -B PROJECT_ROOT/scripts/compute.py --root PROJECT_ROOT --output OUTPUT_DIR/verification-normal
```

随后以 `notes/rejected-parameters.json` 的 alpha=1.0 运行同一计算器，指定独立的 `verification-rejected` 输出位置，实际退出 2，错误为 `ValueError: Require 0<alpha<1, rho>0 and finite nonnegative intrinsic times`。无效试算未生成输出目录。对有效参数、result、table、summary、计算器和原 PDF 的前后完整 SHA、字节数及文件 mtime 均相同，见 `verification.json` 和项目内 `validation/stage-A.json`。这是受控输入校验测试，不是科研分析失败。

权威状态在 `research/state.json`，包含约束、问题与主张、来源身份、材料、选择、活动、依赖、完成时指纹和检查点。`PROJECT.md` 是阅读入口，旧笔记不覆盖权威 JSON。T-CALC 绑定参数、原 PDF、计算器、选择和结果/表格；T-SYNTH 依赖 T-CALC 及主张和结果；T-SOURCE-CHECK 只核对固定来源身份和来源卡，不随数值参数自动失效。完成状态不表示科学认证。

初始四个小文件 `notes/parameters.json`、`results/result.json`、`results/table.csv`、`results/summary.md` 的完整原字节保存在 `.history/A-initial/files/`，对应完整 SHA 和字节数在 `.history/A-initial/manifest.json`。初始权威状态也保留在 `.history/A-initial/state.json`。约束、义务、来源身份、简报及阶段协议真实复制在项目的 `provenance/` 中，恢复不依赖本阶段外部答卷。

实际核对了所给原 PDF 的完整身份 SHA `eb3efd547349adfbff25514ae0854c142cd29b96b398be38c9000d69a2f64ca8`，大小 1494142 字节，与本地材料清单及给定来源身份一致。所登记版本为 Howard 等论文 arXiv:1810.08240v9、DOI 10.1214/20-AOS1991；这是所给固定身份与字节绑定，并非联网版本核实。阅读范围为身份元数据、组织者来源卡以及少量解码文本片段，未独立审阅公式 (14)、命题 5 或全文证明。T-REMOTE 仅保存 arXiv:1808.03204v7 的身份，没有本地内容绑定，未联网检查。`notes/unregistered-scratch.md` 虽随材料保留并具有交付清单指纹，但不作为已登记科学依赖，恢复脚本不自动覆盖它。原 PDF 仅作私有研究缓存，不随外部报告重发。

科学范围是 l0=1 且同一非负 V 下 S、−S 满足相应 sub-Gaussian 指数控制时，固定 rho 和两侧总 alpha 的给定 normal-mixture 边界数值。不能把任意经验方差当作 V。本次未完成新证明、覆盖率模拟、新颖性论证、形式化验证或人类专家批准。

在项目内运行 `python3 -I -B resume.py` 可只读查看当前约束、下一步、变化文件、三项活动状态及检查点。已实际执行两次，均退出 0；最后一次前后项目所有普通文件字节、文件 mtime 与目录 mtime 均保持相同，证据在 `readonly-recovery-test.json`。该脚本只检查显式登记范围，不执行后续科学动作。`update-state.py` 提供预期版本、旧状态保存及冲突拒绝，且不会自动刷新活动；本阶段只检查其语法，未声称完成写入/冲突测试。

下一步：将当前四点边界表和摘要交作者讨论，具体确认 V 的定义、过程控制条件和 rho 的预先固定。截止日为材料作者给出的 2026-12-15，目标期刊未定；预算仅离线标准库，不采集新数据或重拟合。未经内容复核不投稿。

辅助操作中，首次 PDF 正则扫描未捕获最终退出，随后改用线性扫描成功；为清理自身迟滞扫描而尝试的 `ps` 操作被沙箱拒绝，没有获得进程信息，也未完成该清理。首次失败和补救保留在 `execution.json`，没有以重试成功覆盖原记录。
