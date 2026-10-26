# 中文介绍与使用说明

这份用户包用于本地科研工作。九个技能由 Codex 等兼容宿主中的助手执行；Python 工具保存研究材料、主张、证据关系、进度和恢复状态。需要 Python 3.11 或更新版本，支持 macOS 和 Linux；Windows 写锁尚不支持。

## 第一次使用

解压后进入 `research-workflow-template`，运行：

```sh
python3 tools/research.py options
python3 tools/research.py init --output ../my-research --title '我的研究问题'
python3 tools/connect_skills.py install --root ../my-research
python3 tools/connect_skills.py check --root ../my-research
```

输出目录必须尚不存在；路径含空格时加引号。然后在兼容宿主中打开 `my-research`，说明研究兴趣、已有材料或当前任务。工具包目录与研究项目目录分别保存；安装只写入所选项目的 `.agents/skills/`，不改全局技能。

已知学科或方法时，可在 `init` 加入 `--discipline law --method legal-analysis` 等选项；合法 ID 以 `options` 为准。尚未确定时先省略，之后用 `configure` 更新。

## 九个技能如何配合

| 技能 | 用途 |
|---|---|
| `rw-workflow` | 从当前任务选择下一步，恢复项目与协调交付 |
| `rw-question` | 澄清研究问题、范围和关键术语 |
| `rw-literature` | 查找和阅读来源，核对身份、引用与实际支持 |
| `rw-innovation` | 构造候选机制、猜想与最小验证 |
| `rw-candidates` | 比较多个方向的依据、障碍和可行性 |
| `rw-validation` | 按方法检查证明、计算、实验或解释的义务 |
| `rw-writing` | 起草、润色、翻译与压缩，保持论证与作者意思 |
| `rw-figures` | 制作和检查科研图件，区分数据、结构与视觉效果 |
| `rw-review` | 审阅、返修和按需核对多份材料中的共享事实 |

直接向助手说明任务即可，例如：“先读这些材料，帮我确定一个能检验的小问题。”跨材料审阅可说：“核对稿件与图表中同一结果的定义、条件和数值，说明实际检查范围。”只读请求不会新增登记。

学科与方法指导随包位于 `profiles/`，共用协议位于 `core/`。它们不认证整个专业已验证；数学证明、数值观察、法律解释、伦理许可和期刊要求需要各自的依据。

## 日常恢复与登记

在工具包根目录执行，把 `PROJECT` 换成实际项目路径：

```sh
python3 tools/research.py resume --root PROJECT
python3 tools/research.py status --root PROJECT
python3 tools/research.py check --root PROJECT
python3 tools/research.py list --root PROJECT --kind statement
python3 tools/research.py show --root PROJECT --kind statement --id S1
```

`resume`、`status`、`check`、`list` 和 `show` 是只读命令；`S1` 应替换成已有记录 ID。登记使用 `register --kind KIND --file INPUT.json`，批量使用 `register-batch --file INPUT.json`，也可用 `--file -` 从标准输入读取。已有记录的修改需要显式版本替换；保留项目的版本与依赖，不能直接清空或改写登记簿。

工作告一段落后保存下一步：

```sh
python3 tools/research.py checkpoint --root PROJECT --next-action '核对下一份原始来源'
```

可用 `python3 tools/research.py --help` 及子命令 `--help` 查看参数。完整 JSON 示例与接口说明见公开的[命令行指南](https://github.com/CheshireCat-D/research-workflow-template/blob/main/docs/07-core-usage.md)。

## 搬迁与更新

安装后的项目包含所需指导和运行时。搬迁完整项目后，可从项目根运行：

```sh
python3 .agents/skills/_rw-runtime/tools/research.py resume --root .
python3 .agents/skills/_rw-runtime/tools/connect_skills.py check --installed-only --root .
```

更新工具包时，取得新的当前用户包，保留研究项目；暂停正在使用该项目的助手，再从新工具包运行：

```sh
python3 tools/connect_skills.py upgrade --root PROJECT
```

副本有本地修改、缺失或未知文件时，升级拒绝覆盖，先保留并审阅这些变化。升级有短暂的读取切换间隙和已捕获失败回滚，不提供断电事务保证。具体边界见公开的[技能接入说明](https://github.com/CheshireCat-D/research-workflow-template/blob/main/docs/08-skills-and-methods.md)。

## 包含内容与边界

包中保留当前 `core/`、`skills/`、`profiles/`、目录资源、两个命令入口、双语指南、MIT 许可和来源归属。清单 `USER-PACKAGE-MANIFEST.json` 标识当前文件字节。评估案例、测试、开发记录和旧发行内容在用户包之外；完整证据与维护工具见[源码仓库](https://github.com/CheshireCat-D/research-workflow-template)。`options` 中的评估引用属于源码仓库的材料，不是用户包中的本地文件。

工具离线登记元数据，不执行来源中的命令，不上传数据或自动投稿。科学正确性、创新性、伦理批准和实际投稿状态分别核对。真实论文、私有数据、凭据与个人技能包独立保存；可选绘图工具由具体任务决定，核心没有第三方 Python 依赖。
