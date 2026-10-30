# 迁移后的只读恢复结果

项目根为 `PROJECT_ROOT`。已在该根实际运行共同 Python 的 `-I -B resume.py`，退出码0；当前登记文件没有变更或缺失，三个活动的有效状态均为 done，当前断点新鲜。具体输出在本答卷旁的 `resume.stdout.json`，这表示所声明身份与依赖一致，不表示科学认证。执行前后对全项目文件的字节、SHA256、mtime和目录mtime逐项比较，结论见 `read-only-audit.json`。

## 当前问题、约束与有效版本

研究问题是：对满足规定 sub-Gaussian 指数控制的过程，按给定 normal-mixture 公式核对固定参数的四点边界数值。唯一权威是 `research/state.json`，元数据修订4；当前 `T-PARAM/T-CLAIM/T-REL/T-CHOICE/T-RESULT/T-SUMMARY/T-CALC/T-SYNTH` 均为版本2。原始约束和旧断点不能覆盖当前权威。

当前 alpha=0.05、rho=4，rho在观察前固定，V取0、1、10、100。标量 l0=1，alpha为两侧总错误预算，公式为 `sqrt((V+rho)*(log(1+V/rho)+2*log(1/alpha)))`。S与−S须对同一个非负内在时间V满足相应过程控制条件，不能任意代入经验方差。此处只抄录项目的科学范围，没有重算或新证明。

截止日为2026-12-15，属于所给作者工作约束；中文，期刊未定。预算限离线Python标准库，不采集新数据、不重新拟合。原始PDF/CSV仅作私有研究缓存，不向仓库再分发。尚无人类专家完成内容认可，也没有投稿授权。

## 成果与已完成工作的证据

现有 `results/result.json` 和 `results/table.csv` 的四点既存数值逐项相同；本阶段只比较既存内容，没有调用计算器或评估公式。

| V | 当前边界值 |
|---:|---:|
| 0 | 4.895493661361633 |
| 1 | 5.57431973357386 |
| 10 | 10.070709270872976 |
| 100 | 31.015388968276124 |

`results/summary.md`已经改为rho=4并保留条件与下一步。`provenance/stage-C/AUTHOR-REVISION.md`提供作者参数修订依据；`approved-parameters.json`与当前参数文件内容相同。

- `T-SOURCE-CHECK`：仍为done。只核对固定来源身份、版本与卡片范围，输入T-SRC/T-RAW、输出T-SOURCE-NOTE均未漂移；rho不是该活动的依赖，故参数修订不要求重复这个独立分支。项目中的原始执行证据是 `validation/stage-A.json`。
- `T-CALC`：当前为done，绑定rho=4参数、原PDF、计算器和当前结果/CSV。`validation/stage-C.json`与`validation/stage-C-recompute-verification.json`记载阶段C真实复算、公式比较和CSV核对，计算器执行退出0；复算输出自身也留在 `validation/stage-C-recompute/`。本阶段确认这些记录和当前绑定存在且无漂移，没有重演该复算。
- `T-SYNTH`：当前为done，输入T-CLAIM/T-RESULT，依赖T-CALC，输出T-SUMMARY。阶段C记录说明摘要读过并更新，但仍等待作者内容复核。

## 历史与断点不能混用

初始rho=1的真实参数、结果、CSV和摘要仍在 `.history/A-initial/files/`，例如旧V=10数值为9.606401928868575，不能作为当前结果。元数据修订1/2/3的实际内容在 `.history/metadata/revision-1.json` 等文件。

`.history/C-drift/`保存参数已改但成果未重算的状态。项目保留的原始 `validation/stage-C-intermediate-resume.stdout`表明：当时新断点fresh=true，恢复检查仍退出1，T-CALC和T-SYNTH为stale，T-SOURCE-CHECK仍done。保存断点并没有重新核验旧工作。修订3虽然更新参数记录，但活动仍抓取rho=1指纹；修订4才在实际复算后显式重新绑定受影响活动。

当前 `research/checkpoints/C-final.json`与权威JSON内嵌断点完全相同，配置、记录、活动摘要与登记文件指纹均匹配。目录迁移本身未造成登记内容漂移；无须重新初始化。当前无需要因迁移重做的登记活动。

## 来源和覆盖缺口

主来源身份为 *Time-uniform, nonparametric, nonasymptotic confidence sequences*，arXiv 1810.08240v9，DOI 10.1214/20-AOS1991。本地 `sources/howard2021-arxiv-v9.pdf`，1494142字节，SHA256为 `eb3efd547349adfbff25514ae0854c142cd29b96b398be38c9000d69a2f64ca8`，与项目来源登记一致。本阶段对PDF只读取完整字节做身份哈希，没有读页、核查公式或审阅证明。`notes/source-check.md`为提供者的释义卡；其页码和定理归属未在本阶段独立核实。

T-REMOTE只留来源身份（arXiv 1808.03204v7），没有本地正文或远端内容绑定，本阶段没有联网。`notes/unregistered-scratch.md`未纳入活动自动失效覆盖。本次全项目哈希盘点用于只读完整性证据，不扩大原有科学依赖覆盖，也不把历史快照、状态检查、四点数值或现成摘要当成覆盖证明、新颖性或形式化验证。

## 具体下一步与可恢复范围

下一步仅是把rho=4的 `results/table.csv`和 `results/summary.md`交作者内容复核，确认V的含义以及S/−S的过程条件。暂不扩展到事后选择rho，不投稿。本阶段只恢复该下一步，没有执行交付、内容审批、重算、修复或写入新状态/断点。

迁移项目自身保留 `resume.py`、`update-state.py`、`scripts/compute.py`及上述来源、历史和证据，恢复程序仅依赖Python标准库，可在迁移根运行 `python -I -B resume.py`。已阅读写入接口：它要求预期元数据/记录版本和修订理由，保留旧状态并拒绝冲突；它不自动重新绑定活动或更新断点。本阶段未运行该写入接口。历史执行日志含原位置绝对路径，只作为历史证据；未访问那些路径，也不依赖旧外部答卷完成当前恢复。当前未发现阻止这次只读恢复的项目资源缺失。
