# 通用科研工作流模板

[English](README.en.md) · [中文介绍与使用说明](中文介绍与使用说明.md) · [English user guide](USER_GUIDE.en.md)

一套面向理工医农、人文社科与法学的本地科研工作流：从研究兴趣、文献定位、创新与候选比较，到最小验证、证明或实验、写作、图件与审阅。九个技能由宿主助手执行实际任务，标准库 Python 工具保存主张、材料、引用、进度和恢复状态。

本仓库维护当前源码、测试和必要的冻结评估证据。面向用户的发行包固定为 `research-workflow-template.zip`，只含当前运行资源、双语指南、许可与来源归属，不含测试、评估过程、开发修改记录或旧版。源码与用户包分别检查，更新由清单和 SHA-256 内容指纹标识；项目数据格式、记录与依赖的必要版本字段继续保留。

## 开始使用

直接使用可下载[当前用户运行包](https://github.com/CheshireCat-D/research-workflow-template/releases/latest/download/research-workflow-template.zip)与[SHA-256](https://github.com/CheshireCat-D/research-workflow-template/releases/latest/download/research-workflow-template.zip.sha256)。发行入口只维护一个当前包；GitHub 的源码下载另含开发测试材料。

需要 Python 3.11 或更新版本。核心提供 Windows、macOS 与 Linux 本地项目支持；各平台的实际执行记录见[平台核验](docs/11-linux-validation.md)。macOS/Linux 在本目录运行：

```sh
python3 tools/research.py init --output ../my-research --title '我的研究问题'
python3 tools/connect_skills.py install --root ../my-research
python3 tools/connect_skills.py check --root ../my-research
```

Windows PowerShell 可运行同一组命令：

```powershell
py -3 -X utf8 tools/research.py init --output "../我的研究" --title "我的研究问题"
py -3 -X utf8 tools/connect_skills.py install --root "../我的研究"
py -3 -X utf8 tools/connect_skills.py check --root "../我的研究"
```

先用 `py -3 --version` 确认 Python 为 3.11 或更新版本；若没有 `py` 启动器，把 `py -3` 换成已安装的 `python`。命令中的项目根路径可使用系统惯用路径，登记材料的项目相对路径统一用 `/`。

将输出路径换成尚不存在的新目录。然后在 Codex 等兼容宿主中打开新项目，描述研究兴趣或当前任务即可。已有项目先运行 `resume`。首次接入和显式升级分别保护已有目录与本地修改；不改全局技能或个人完整版。

也可以让具备本地文件与执行能力的 Agent 先读中文指南，再发送：

> 我的专业／研究方向是【……】，目前的兴趣和想法是【……】，已有知识、文献、材料与可用资源是【……】，时间限制是【……】，希望发表在【……】期刊。

尚未确定期刊时可以填“待定”，先推进当前可开展的研究。目标期刊用于核对读者、研究范围和投稿要求，不代表录用承诺。

`rw-review` 按需支持结构化评审、多视角隔离模拟审稿、逐条审稿回复和投稿材料准备。直接说明当前任务即可；具体用法见[完整指南](中文介绍与使用说明.md#审阅返修与投稿材料)。

## 按需要查阅

| 文件 | 用途 |
|---|---|
| [中文介绍与使用说明](中文介绍与使用说明.md) | 从第一次启动到日常恢复、技能更新与交付 |
| [English user guide](USER_GUIDE.en.md) | 与中文指南对应的完整英文介绍与使用说明 |
| [命令行详细用法](docs/07-core-usage.md) | 查询、标准输入、原子批量登记、配置与检查点 |
| [技能与方法](docs/08-skills-and-methods.md) | 九个技能、项目内接入、方法资源与升级边界 |
| [技能检索与取舍](docs/12-skills-selection.md) | 已核验来源、选择理由与未采用边界 |
| [学科适配](docs/02-disciplinary-adaptation.md) | 七类学科、十类方法及跨学科组合 |
| [专业与问题导航](profiles/selection.md) | 教育、经管、心理、哲学与艺术的现有入口及未专测范围 |
| [配对栏饲喂演示](examples/paired-pens/README.md) | 从120条合成记录复算海报同例的栏均值、区间与精确P值 |
| [结果表与稿源交付](examples/submission-table/README.md) | 将同例数据整理成小数对齐的三线表与可编译主稿 |
| [科研质量实作](evals/quality/README.md) | 真实检索、正确稿/缺陷稿审阅及资源改变后的推荐调整 |
| [法学项目模板](profiles/templates/legal-research.md) | 法域、法条时效、效力依据、判例与引证台账 |
| [证据契约](docs/03-evidence-contract.md) | 主张、材料、支持关系和研究进度的边界 |
| [当前验收](evals/current/latest.json) | 当前内容的实际检查结果与执行范围 |
| [发行验收](docs/10-release-readiness.md) | 来源、归档、干净环境与可交付检查 |
| [用户包指南](docs/user-package-guide.md) | 最终用户 ZIP 随附的简洁使用说明 |
| [平台核验](docs/11-linux-validation.md) | 实际平台范围、复查方法与未测环境 |

## 检查与边界

```sh
python3 -B tools/check_core.py --test-timeout 360
python3 -B tools/release_package.py check
python3 -B tools/package_user.py check
```

命令行离线工作，不执行材料中的命令、不上传数据或自动投稿。登记或软件检查通过不认证证明、创新性、伦理批准或期刊合规；相应检查仍由作者与实际执行者负责。源码中的 `evals/` 保留当前回归所需的合成任务、真实来源笔记及复核证据，用户 ZIP 不包含这些开发材料。构建与干净运行命令见[发行验收](docs/10-release-readiness.md)。

原创实现、指导与合成材料采用[MIT许可证](LICENSE)。外部方法资料保留自身权利，见[来源说明](provenance/ORIGIN.md)与[方法来源](profiles/sources.json)。维护流程见[贡献说明](CONTRIBUTING.md)，数据边界见[安全说明](SECURITY.md)。本目录与个人包独立，远程发布由维护者显式执行。
