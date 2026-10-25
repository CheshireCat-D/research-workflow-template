# 实际执行与设计依据

预定脚本保存后，先运行冻结 inputs/gate.py。共 1578 项，987 通过、591 失败，退出码 1；结果与逐项异常保存在 artifacts/prototype-results.json，完整原始输出在 artifacts/logs/prototype.stdout.log，命令、退出码和全进程时间在 artifacts/logs/prototype.json。没有将其解释为运行环境失败。

## 确认原因

1. 原型使用 active[0] < cutoff，故恰位于 t-window 的请求仍计入窗口。limit=1,window=10，a 在 0 获准后，10 应获准，实际拒绝。修复为 <=。基线演示第9、11行调用结果也不同于定义参考。
2. 原型将时间转换 float；2**53 与 2**53+1 混同。math.isfinite(10**400) 抛 OverflowError，而需求没有整数上限，此值是合法有限整数。修复为先区分 int/float，仅对 float 检查有限性，再以 Fraction 精确表示数字。

保持原始队列结构、客户独立水位与拒绝不入队规则。非法参数的类型、符号、有限性与水位检查全部先于状态写入；合法拒绝推进水位，过期元素只按左开边界移除。Fraction 保留调用方浮点数的实际二进制值，不假定十进制意图。

## 修复复跑

对 artifacts/gate.py 运行相同未改验收：1578 项全通过，退出码 0；计时段 0.018970 秒，全进程以 artifacts/logs/fixed.json 为准，均少于10秒。1512个参考轨迹按定义保留全部允许历史并直接计数；另有66项手工场景、异常检查与CSV重放。R1..R9逐项结果见 artifacts/results.json 的 requirement_coverage。种子不适用。

验收只提供有限执行依据。单客户每个已允许请求至多入队、出队各一次（手工代码检查，未进行复杂度形式验证）；活跃队列最多 limit 条，但客户水位会持续保留。精确有理数的算术成本随整数位数增长。本轮没有内存上限或生产负载阈值，不声明性能达标。
