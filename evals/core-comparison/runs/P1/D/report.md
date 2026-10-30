已从迁移后的项目自身材料恢复当前状态。当前有效范围为 alpha=0.05、观察前固定的 rho=4、v=[0,1,10,100]；三个已登记活动均仍有效完成，当前断点为 current，未发现登记覆盖范围内的变更或缺失。项目配置以 `project.json` 为准，登记、版本和断点以 `records/registry.json` 为准（revision 46）。`PROJECT.md` 的初始化说明、初始约束中的 rho=1 和历史恢复说明均不覆盖较新的作者批准版本。

研究问题是在规定 sub-Gaussian 条件下核对给定 normal-mixture 公式的数值。公式为 b(v)=sqrt((v+rho)[log(1+v/rho)+2log(1/alpha)])。保留的条件是标量 l0=1，S 与 −S 对同一非负内在时间 V 满足相应指数控制，alpha 为两侧总预算，rho 在观察前固定；不允许把任意经验方差代入。

当前 `notes/parameters.json` 与 `provenance/stage-c/approved-parameters.json` 的内容和 SHA 完全一致，作者授权正文在 `provenance/stage-c/AUTHOR-REVISION.md`。当前已保存数值如下，本阶段只读取比较，未重新计算。

| v | 边界 |
|---|---|
| 0 | 4.895493661361633 |
| 1 | 5.57431973357386 |
| 10 | 10.070709270872976 |
| 100 | 31.015388968276124 |

`results/result.json` 与 `results/table.csv` 四行数值一致，参数和网格吻合；结果中保存的参数及计算器完整 SHA 与现存文件一致。`results/summary.md` 使用 rho=4，四个舍入值和 v=10 表述一致，保留了条件范围。当前结果为版本2，表和摘要为版本2；参数、选择、关系、主张及计算/摘要活动也为版本2；独立来源核验活动仍为版本1。

当前工作状态与实际依据：

- `T-SOURCE-CHECK`：有效 done。仅核对固定来源身份/版本、完整本地 SHA 和来源卡范围，未审阅定理正文；原 PDF、来源记录和来源卡没有随 rho 修订改变，因此该独立分支仍可保持完成。
- `T-CALC`：有效 done。`notes/stage-c-validation.json` 留有原脚本在批准 rho=4 下的实际执行记录（exit 0）、四值等价式核算、v=0、CSV/JSON 和输入 SHA 比较；对应输出在 `validation/stage-c/rho4/`。这些是项目已经保存的数值复核证据，本阶段未运行计算器。
- `T-SYNTH`：有效 done，依赖 `T-CALC`。当前摘要对应新数值与限定解释；作者内容复核尚未完成。

修订前内容真实保留在 `history/stage-a-initial/`，包括 rho=1 的完整参数、结果、表和摘要，v=10 为 9.606401928868575。`history/stage-c-before-recompute/` 保留当时 rho=4 参数与仍为 rho=1 的旧成果、配置和登记；本阶段逐项比对两份历史 manifest 的 SHA/bytes，全部一致。当前登记 history 还保存了旧记录内容和替换版本，修订原因是作者明确批准另一预先固定的 rho=4，未修订原论文。

`validation/stage-c/checkpoint-drift.json` 和 `check-drift.json` 留有中间状态：保存新断点后断点虽 current，参数文件仍 changed，`T-CALC`、`T-SYNTH` 仍 stale，而来源核验有效。这说明保存断点本身并不重新核验旧工作；最终状态有实际复算、更新及重新登记作依据。初始 alpha=1 控制失败（exit 2）及未覆盖有效成果的记录保留在 `notes/stage-a-validation.json`。操作错误及补救另在 `notes/stage-c-operational-corrections.json`，未用最终成功覆盖原始失败。

来源身份为 Howard 等，Time-uniform, nonparametric, nonasymptotic confidence sequences，arXiv:1810.08240v9，DOI 10.1214/20-AOS1991。本地 `sources/howard2021-arxiv-v9.pdf` 为 1494142 bytes，SHA256 `eb3efd547349adfbff25514ae0854c142cd29b96b398be38c9000d69a2f64ca8`，与保存身份一致。本阶段只完整哈希该 PDF 并阅读项目来源卡，未读取数学页面或核验远端。来源卡是给定释义，卡内页码/命题号不因本阶段身份检查而成为已独立证实。

覆盖限制仍在：`T-REMOTE` 仅登记 arXiv:1808.03204v7 身份，没有本地内容绑定，也没有当前远端核验；`notes/unregistered-scratch.md` 未登记，不在自动科学依赖覆盖内。恢复检查绑定22个本地路径，不能扩大为全部项目文件或全部研究依赖均已科学审核。原始 PDF 只作私有缓存，本答卷未复制或分发。

其他有效约束：中文；仅离线 Python 标准库和现有资料；不收新数据，不重训或重拟合；目标期刊未定；2026-12-15 是任务作者给定日期，未被观察为真实研究截止日期；尚无人类专家完成内容认可，无外部投稿授权。当前工作限于四点公式数值和摘要，不构成新覆盖证明、覆盖模拟、形式化验证或新颖性判定。

迁移后的项目自带只读恢复程序实际运行成功：登记 revision 46、三个活动 effective done、checkpoint current、findings 为空。项目内运行资源的独立完整性检查通过，67个文件；只核对已安装副本，不对照原工具包，也不表示科学内容验收。外部原始输出为本答卷目录中的 `resume.json` 和 `runtime-check.json`。项目所有文件字节、文件 mtime 和目录 mtime 的前后清单一致，详见 `project-baseline.json`、`project-after.json` 与 `read-only-verification.json`。

具体下一步保持为：把 rho=4、alpha=0.05、v=[0,1,10,100] 的 `results/table.csv`、`results/summary.md` 及完整数值 `results/result.json` 交作者内容复核；暂不扩展到事后选择 rho。本阶段没有执行此步骤，也没有初始化、写登记、保存断点、修复项目或重算结果。项目自身资源足以恢复该步骤；保留的远端内容核验与人类专家内容认可缺口尚未填补。
