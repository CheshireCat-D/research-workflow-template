# 问题、方法与执行范围

任务：检查 `inputs/model.md` 的能量方程、试跑公式和 draft，利用独立的教学校准及操作输入重算，不能使用观测反估参数。

本轮实际读取项目内 rw-workflow、rw-validation、rw-writing、rw-review；先读接入和核心协议，再查 catalog 与七类登记 schema。读取画像 natural-sciences、formal-theory、computational、measurement-experiment，版本均为0.1。选择理由依次是物理边界与外推、手工解析推导、确定性计算与数值稳定性、校准和共同误差处理。analytic-derivation 是本任务实际理论变体；其画像当前验证重点为 proof，借用指导不代表该物理分支已被工具包认证。未执行真实实验，measurement-experiment仅用于合成校准记录的测量审查。

成功判据：由能量平衡推出满足初值和全部指定极限的解；校准给出H及u，基础独立输入一次传播至动态温度和跨时刻协方差；全部6时点复算，逐项对照6条试跑与4条观测；保存可移位重跑代码和原始日志。观测的t=0是初值一致性检查，三个非初始点才作预测对照。

输入仅限 `inputs/task.md`、`inputs/model.md`、`inputs/calibration.json`、`inputs/pilot.csv`、`inputs/observations.csv`，均全文读取并逐字节复制核对，见 input-manifest.json。无外部文献、网络、依赖安装或实际设备；无缺测、排除或参数拟合。单一合成物体的重复时点不是多个独立实验。

预先选定解析解及一阶不确定性传播；有限差分仅核对实现导数，两个步长检查误差。原始seed=29017不使用，因为没有随机数。真实源文件和工具包保持只读。结构检查只检查登记、指纹与恢复状态。
