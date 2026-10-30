# 冻结模型交接

接续时先读本文件、report.md与RUN.md，使用results/model.json，保留results/首次结果。阶段A已完成，仅使用2011输入，未读取、获取或推测2012观测。没有为留出结果调参。

## 已冻结的决定

- 数据：UCI Bike Sharing，Capital Bikeshare单系统。输入hour_2011.csv SHA256=`294d25e98ef1c9c9cec746e17ba3ff9818627ba5aa14baf1b93db7ae218de115`，day_2011.csv SHA256=`a15d6536bae4f15ec0b27ccef8b510a9fd7caf46b2f1dbe1ffd00c6a32920d5b`。完整读取逻辑名和哈希见execution.json。
- 训练：2011-01-01至2011-09-30，273日、6442小时；freeze在2011-09-30日终。
- 一次时间留出：2011-10-01至2011-12-31，92日、2203小时。
- C0：按训练hr分组cnt算术均值。C1：按训练(workingday,hr)分组cnt算术均值，未见组合回退C0。不取整，不使用其他变量。24+48组合均出现，本次回退0。
- 参数：results/model.json，格式calendar-mean-v1，每组保存sum、n、mean。SHA256=`dba591a44fff2d14514b4b38d00c8985e93f41cf2b1ab684a6abd2f2620d078d`。不要使用未来cnt更新参数，也不要把score改为fit。
- 比较规则：主指标为所有已观测小时等权MAE；Δ=MAE0−MAE1，R=1−MAE1/MAE0；有用门槛R≥0.10。另报RMSE、预测减真实的平均偏差、先各日计算日内MAE再日期等权的均值、完整24小时日期和workingday分组。
- 区间：同批日期成对循环移动块bootstrap，日期排序，D=评估日期数，randrange(D)取起点，每块连续7日或28日、末端循环，抽至≥D后截断D。保留日内全部小时，用绝对误差总和/小时数。B=2000，每种块长重新random.Random(20261029)，百分位区间用排序(B−1)p线性插值。

## 当前证据

空单元格和重复键均为0，但8645小时少于8760个日历小时；305日完整、60日不完整，共缺115小时。cnt=casual+registered全通过；逐日3个计数的小时和与日表一致，全年总cnt=1,243,103。不应把缺少的行自动补0。season标签、temp/atemp逆变换和全量小时数在原README与当前页面摘录冲突；保留原观测、不做反归一化，三个变量都没有用于模型。

留出主MAE：C0=58.825190494512434，C1=44.570832407531775；Δ=14.254358086980659，R=0.24231724482575867；日等权R=0.24178070599588253。完整日期87日/2088小时，R=0.25549971431189。workingday=0与1的R分别0.37618608960904465和0.12611712674255904。7日块95% R区间[0.17071940679252828,0.3148328823524696]；28日块[0.15571346410314052,0.325449081470458]。

C1改善和超过10%是两个问题，本留出点估计均成立，规定bootstrap区间在相应时间稳定性近似下也支持两者。只限该期、该系统已观测小时；尚不能保证跨年或干预因果效果，不能推断个体行为。bootstrap固定训练参数，不包含训练不确定性或缺失小时误差。

## 下一阶段无需重新训练

1. 获得阶段B明确提供的新小时表后，先检查身份、日期、键、缺失小时和计数口径；本阶段不要提前获取新观测。检查模型SHA256不变。
2. 按RUN.md的score命令，传新hour CSV、现有model.json及新输出目录。score读取日历列预测，读取cnt打分，忽略天气、类别计数及其他列；不会更新模型。未来workingday需要从已知节日日历或所提供日历字段确定。
3. 报告新期完整范围、小时/日期数、同口径主指标与10%门槛、日等权、完整日及分组敏感性；保持本阶段首结果可对照，不以新结果回改规则。
4. score已在2011留出重播实跑：results与replay_check的指标完全相同，预测、逐日误差和两份bootstrap CSV逐字节一致。独立statistics.mean核对72个训练均值，预置指标函数核对MAE/RMSE，全通过，证据见verification.json。

文件索引：analyze.py（复跑与冻结评分）；verify.py（核验）；results/audit.json与calendar_coverage.csv、missing_calendar_hours.csv（数据审计）；results/results.json（完整指标）；results/predictions.csv（逐小时）；results/daily_errors.csv（每日误差和与小时数）；results/bootstrap_7d.csv、bootstrap_28d.csv（每次统计量）；results/runtime.json（实际Python与运行参数）；execution.json（执行记录）。
