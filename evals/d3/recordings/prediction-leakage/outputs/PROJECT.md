# 合成院内预测评估：主体泄漏与用途边界

本轮为Codex代理执行的离线方法与报告练习，材料均为案例作者新写合成记录。正式运行、主体汇总、校准表、修订稿及有界自审已完成；没有临床部署或实际诊疗行为。

主要文件：notes/issue.md、notes/work-performed.md、artifacts/run.py、artifacts/config.json、artifacts/results.json、artifacts/subject_predictions.csv、manuscript/report.md、review.md。

R训练/测试各12主体、各12行，交集12，准确率1、Brier0；S训练8主体16行、测试4主体8行、交集0，准确率0.5、Brier0.25。两者平均概率和事件比例均0.5；S只有一个非空概率箱，不支持所有风险段可靠。R恢复训练中同一主体的已知结局，不能验证首次接触新主体用途。S只描述4个合成留出主体的基础率输出。

已读项目本地rw-workflow、rw-validation、rw-writing、rw-review，量化实证prediction、computational、medicine-health与governance；其余安装技能未加载。登记、指纹检查与恢复不构成科学或临床认证。

保存下一步：制定锁定的首次接触验证协议，明确目标人群与day0可用信息；规定独立主体、后续时期/外部机构队列、样本量及区分度/校准/不确定性标准，在任何真实访问或收集前由相应责任方核定治理条件。该下一步尚未执行。
