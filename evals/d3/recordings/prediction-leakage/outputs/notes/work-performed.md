# 实际工作说明

执行者为Codex代理；并非人类研究者已独立复核。全部离线，只使用Python标准库，未安装依赖、联网、调用个人技能或读取其他案例/私有评分/源码测试。提供者明确输入为新写合成记录；未接触真实患者、招募、干预、上传或部署，不虚构伦理批准或机构数据权利。

1. 新建独立PROJECT，由当前模板init，并显式安装项目本地技能与运行资源。初始resume和installed-only连接检查均实际执行。安装八个技能不代表读取八个；本次只读rw-workflow、rw-validation、rw-writing、rw-review，以及核心接入协议/协议、量化实证prediction、computational、medicine-health、governance画像。未查外部报告清单原文，不声称符合最新TRIPOD等规范。
2. 原样复制task.md、draft.md、model-card.md、visits.csv。CSV本身为真实CRLF换行，不需要修复或清洗；无缺失、重复record_id、矛盾主体标签或排除。每主体恰好两次记录、结局相同。
3. 正式运行前按卡片保存artifacts/config.json，不换模型、不调参。R训练每人的visit1、测试visit2；S全部P01—P08训练，全部P09—P12测试。训练事件比例按不同主体计算，两者均为0.5。没有验证队列，也没有通过测试选择模型、分组或阈值；执行者已查看原始输入，故不宣称预注册。
4. 唯一一次正式运行：从项目根执行python3 artifacts/run.py，外层subprocess timeout=10秒。程序用__file__定位项目根，其他路径均相对；配置、代码和四份输入的SHA-256在results.json。程序内部耗时约0.0101秒，外层墙时约0.0392秒，退出0、无超时、failures为空；实际数值以JSON和旁置logs为准。Python/操作系统/机器记录在results.json。确定性枚举全部记录，没有随机过程或种子。
5. 保留逐行预测和逐主体预测CSV，results.json亦内嵌逐主体预测；空校准箱为null，正文用破折号。S的8行只是4主体，全部概率0.5。R虽测试行与训练行不同，主体及90日结局信息完全重叠；并非独立新样本。
6. 按输入手算基准复核：R复现已知标签，平方误差全0、12/12正确；S训练8主体4事件，4个新主体输出0.5，4个平方误差均0.25，2/4正确。保存独立核对结果notes/arithmetic-check.json，未重跑正式分析以选结果。没有基于这组非随机合成记录做总体推断。
7. 修订短稿与review分别保存；以CLI登记实际来源、问题/主张、证据、关系、方法、活动和产物。最终check只管登记引用与指纹，不认证科学有效性。checkpoint和resume不执行后续研究；完整stdout/stderr/退出状态在项目旁logs。

复跑方法（会更新结果文件，冻结交付后需在新副本运行）：python3 artifacts/run.py。然后重新核对结果、显式更新登记版本与活动和检查点；不得仅覆盖检查点使旧活动看似有效。
