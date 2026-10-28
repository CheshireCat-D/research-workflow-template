# 登记语义复核与更正依据

执行者：Codex代理，依据维护者转达的独立复核发现，重新核对 inputs/draft.md 第1行、inputs/source-packet.md 第3–5行和实际初始化日志。此次只修登记目标、关系范围和执行来源，不修改原输入及科学正文。

## 原记录中的缺陷

- S-industrial v1 写的是“原草稿主张作者唯一意图是谴责工业劳动制度。”；S-nofigure v1 写的是“原草稿主张原画完全没有人物。”。这两个报告性命题都由原稿直接支持，而原assessment及图像关系实际评估的是被引出的内容命题；对象发生了混用。
- R-industrial-E1 v1 的 supports 实际只对应1970年说法存在，不对应S-industrial的唯一作者意图；E1原节录只有“作者必在谴责工业劳动制度”，没有“唯一”二字。
- R-industrial-counter v1 以原图有人挑战工业意图。有人直接反驳的是E1所用的无人前提，不能由此直接断定艺术家不可能具有任何工业劳动批判意图。
- E-init-failure v1 的provenance套用了“从inputs复制件读取/查看”的通用表述，实际证据是checks/initial-init-failure.json中保存的CLI执行结果。

## 更正选择

1. S-industrial直接登记“作者的唯一意图是谴责工业劳动制度。”，继续排除于正文采纳；assessment改为insufficient：E1的后出归因不确认原作者意图，更未提供唯一性；原图反驳其无人前提也不等于反证一切工业批判可能。
2. S-nofigure直接登记“原画完全没有人物。”，assessment保持challenged，原图左下可见人形是直接反向依据。
3. R-industrial-E1改为contextualizes，范围只到1970年后出归因的存在；不把“唯一”归于E1。R-industrial-counter改为qualifies，范围只到原图对E1推论前提和支持力度的限制。
4. 新增R-industrial-draft与R-nofigure-draft，将E-draft作为上述被审命题的原稿出处，用contextualizes连接；由此分开“稿中确有这句话”和“这句话的内容成立”。
5. E-init-failure.provenance改为Codex实际subprocess.run命令的argv、返回stdout/stderr和退出状态来源，保留原失败日志及failed活动。
6. A-interpret显式重新绑定修正后的内容命题、关系及当前失败日志来源版本，原科学产物哈希保持不变；登记本次更正活动后更新下一活动依赖与checkpoint。

原始版本由CLI登记历史保留，修改前show输出另存checks/semantic-correction/before-*.json。更正采用显式--replace和从show取得的--expected-version，执行及最终检查记录存同目录与execution.json。核心检查不替代上述内容判断。
