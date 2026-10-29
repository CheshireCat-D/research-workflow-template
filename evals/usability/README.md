# 首次使用：两项 AI 代理情境

本目录保留两项多语 AI 代理首次使用模拟的请求、必要输入与首成果，以及独立 AI 审阅的公开整理记录。**真人参与者为 0；这不是人类或英语单语用户的可用性研究。**

| 情境 | 输入和首成果 | AI 墙钟至首成果 | AI 墙钟至成功登记 |
|---|---|---:|---:|
| 中文农学兴趣启动 | [请求](cases/zh-interest/request.md) · [四周问题卡](cases/zh-interest/first-output.md) | 约 145.41 秒 | 约 145.49 秒 |
| 英文合成 CS pilot | [请求](cases/en-pilot/request.md) · [六行 CSV](cases/en-pilot/input.csv) · [导师讨论短稿](cases/en-pilot/first-output.md) | 约 83.54 秒 | **约 147.14 秒** |

计时起点精度为 1 秒，数值只描述这两次 AI 执行，不能推断新手学习时间。英文原反馈把 `register-batch --help` 的 93.84 秒误作登记完成；[recording.json](recording.json) 同时保留旧值、帮助事件、实际 13 条登记成功事件与纠正后的 147.135799 秒。受审原件没有改写。

测试时的分发提交为 `df511bba4f9e9c0719e001ad62c8c0d34cf4ae9a`，当时用户 ZIP 的 SHA256 为 `e8c3f21a12b084fc8f6e2862ed76bb531f0fd34c3d21d31c82630b14f75c6550`。之后指南增加了 `{kind, record}` 数组的最小离线示例，英文指南也说明中文内部指导供助手按需阅读；这两份首成果保留测试时的原字节，不是用后续补丁重新生成的结果。

[assessment.md](assessment.md) 区分成果用途、历史日志核对、当前六条实际只读 CLI 复验与独立 CSV 复算。[recording.json](recording.json) 是本目录唯一结构化台账，连接原始执行、原始审阅、树聚合快照和所有公开分发文件的 SHA；其清单排除自身，并包含专项回归入口。

这里只分发首成果和必要输入。完整临时研究项目、运行时、恢复 ZIP、大日志、分析脚本、结果 summary 和空模板没有分发。首成果中提到的项目相对路径属于当时完整临时项目；**本目录不是可独立运行的完整研究项目**。中文成果没有执行文献检索或真实取数，英文数值来自给定合成 CSV，没有运行真实 benchmark。

专项回归从当前源码的 `package_user` 实际构建 ZIP，读取解压包双语指南里的真实 JSON/命令示例，执行初始化、项目内接入、批量登记、读取、检查点与只读恢复，并核对内容、哈希和 mtime：

```sh
python3 -B -m unittest discover -s tests -p 'test_first_use.py' -v
```

该测试验证分发身份、CSV 算术和离线接口，不调用模型、联网或全局技能，也不以关键词评分科研质量。

如愿意提供真实使用体验，可打开[首次使用反馈表单](https://github.com/CheshireCat-D/research-workflow-template/issues/new?template=first-use-feedback.yml)。目前记录的真人反馈为 0；这里只提供表单入口，没有联系任何外部人员。
