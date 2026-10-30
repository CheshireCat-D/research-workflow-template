已按作者授权将有效评价期改为2011-11-01至2011-12-31，使用原2011年1月至9月冻结模型、观察小时等权。1460个实际观察小时、61日的新结果已真实重算、独立按定义复核并更新JSON、表格及摘要。

|指标|C0|C1|
|---|---:|---:|
|MAE|56.641274309909|41.252622564019|
|RMSE|81.700383606317|64.158265648678|
|预测减实际的平均偏差|13.433264561295|13.347664992606|

C1相对C0的MAE降低27.16861853%。原Q4的2203小时、92日结果降低24.23172448%；两者相差约2.93689404个百分点。评价窗口改变，模型没有重训，不能把降幅差异解释为模型改善。

先保存了真实未重算漂移态：`management/checkpoints/C-pre-recompute/`包含31个原项目文件及完整散列清单，当时参数已变为11月至12月而结果和完成绑定仍对应Q4。随后只读运行原状态检查，exit=3，`notes/parameters.json`的旧SHA为16a467c8e7004e611dcd1c94498b9c769a1b07bd5ad534fb7571e0da18b0c837，新SHA为86afdf878f53587677cd4913aee2389558f87f0784ab2c079f888e362524e864。D-CALC、D-SYNTH须复核；新保存断点并未让旧done重新有效。原始输出完整保留于本答卷目录`intermediate-status.stdout.json`和项目内同名C证据，后续成功没有覆盖它。该检查前后项目字节、文件及目录mtime一致。

接着运行原`scripts/compute.py`至全新`management/evidence/C/recomputed/`，exit=0；独立按原数据与冻结预测逐小时计算MAE、RMSE、偏差和降幅，核对7行指标表及输入全SHA。`management/evidence/C/checks-before-promotion.json`保存实际数值检查。修订摘要也包含原Q4对比、范围边界和待作者复核状态。

`data/hour_2011.csv`（8645行）、`scripts/compute.py`、`model/frozen.json`、`management/source-identities.json`及`notes/source-check.md`均与修订前全SHA一致。D-SOURCE-CHECK只依赖原来源身份、本地切片与来源卡，与本次评价起点无关，保留原限定完成状态；D-CALC与D-SYNTH是在本次真实复核后更新完成状态和材料绑定。权威`management/state.json`同步当前约束范围、D-PARAM→D-CLAIM关系、D-CHOICE决定、活动证据与具体下一步；旧状态与决定完整保存在漂移态快照。初始Q4参数、结果、表格、摘要完整字节仍在`management/versions/A-initial/`，当前版本及状态在`management/checkpoints/C-final/`。

最终只读`management/status.py`和独立`management/verify_current.py`均exit=0；登记文件无变更/缺失，9份登记版本均完整，两个检查点31/6份内容散列均相符。最终检查前后项目字节及mtime一致。原始输出为本答卷目录`final-status.stdout.json`、`final-numerical-verification.stdout.json`和`final-check.json`，项目内C证据及最终检查点另存副本。该结果仅说明登记本地身份、依赖绑定和当前数值核对完成，作者内容复核仍未发生。

下一步：将2011年11月至12月的冻结模型指标与更新摘要交作者内容复核，保留原Q4历史。尚无人类专家认可，无投稿授权；不重训、不作因果推断或2012/任意未来保证。截止日期2026-12-15为所给约束，期刊未定。

恢复入口为`RECOVERY.md`。迁移后用可用Python运行`python -I -B management/status.py --root .`和`python -I -B management/verify_current.py --root .`，只需标准库。重算需给原计算器新的不存在输出目录，保留任何失败；旧handoff不得覆盖较新参数。state.json不通过自包含散列证明其自身未改，应结合保留的作者授权、初始版本和检查点判断。

来源边界：原完整hour.csv/ZIP、DOI文章内容及当前网页均未读取或联网确认；本地切片完整SHA可核查。来源卡所给完整CSV17379行与metadata17389行差异原样保留。`notes/unregistered-scratch.md`未登记科学依赖，不纳入自动变化检测。所有缓存和快照保持私有，原始CSV/PDF不对外分发。无网络、安装、重训、外部发送或投稿。执行记录另见`execution.json`；完整输入与产物身份见`inputs-and-artifacts.json`。
