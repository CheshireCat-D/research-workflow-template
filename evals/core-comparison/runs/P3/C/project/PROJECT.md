# 固定精度正态混合边界数值核对

唯一权威状态为 research/state.json，当前元数据修订4，alpha=0.05、rho=4，rho在观察前固定；截止日2026-12-15，期刊未定。预算限离线Python标准库，不采新数据、不重新拟合，原PDF仅作私有缓存，不向仓库分发。

恢复：在本项目根执行 python3 -I -B resume.py，或指定 --root PROJECT。退出0表示已声明的文件/记录/活动/断点未发现漂移；1表示漂移或失效；2表示读取或接口错误。恢复只读，不依赖外部报告、原输入目录或指导工具包。PROJECT.md与历史断点不反向覆盖当前JSON。

阶段C先将未重算漂移态完整保存在.history/C-drift/files/及manifest.json，保存新断点后实际只读检查仍退出1：T-CALC和T-SYNTH失效，T-SOURCE-CHECK仍完成。validation/stage-C-intermediate-resume.stdout保留该原始结果；新断点没有使旧工作恢复有效。随后按provenance/stage-C/中的明确授权真实重算到validation/stage-C-recompute/，核对公式、结果JSON和CSV，更新results/summary.md，并显式重新绑定两项受影响活动。validation/stage-C.json保留执行及范围证据。初始rho=1参数、结果、表格、摘要完整字节仍在.history/A-initial/files/，metadata旧版本在.history/metadata/。

原PDF、计算器、固定来源卡片及当前参数文件字节和mtime保持不变；只有成果和管理状态依授权更新。独立来源核验分支的输入、输出及记录没有改变，因此继续有效；本轮仅核对其身份完整性，未审查PDF公式或证明。远端T-REMOTE只有元数据身份，未联网核对内容。notes/unregistered-scratch.md未进入活动自动失效覆盖；历史快照保存字节不等于科学核验。

下一步：将rho=4的边界表与更新摘要交作者内容复核，确认内在时间V和sub-Gaussian过程条件；暂不扩展到事后选择rho。没有人类专家认可、新覆盖证明、形式化验证或投稿授权。

修改权威配置/记录可用update-state.py --expected-revision N --patch PATCH.json；它要求修订理由及预期版本，保留旧状态并拒绝冲突，不会自动重新绑定活动或更新检查点。活动重绑定只应在实际复核后进行。阶段C已实际运行本地接口完成受授权修订。
