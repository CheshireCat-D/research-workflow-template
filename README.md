# 通用科研工作流模板

[English](README.en.md) · [中文介绍与使用说明](中文介绍与使用说明.md) · [English user guide](USER_GUIDE.en.md)

一套面向理工医农与人文社科的本地科研工作流：从研究兴趣、文献定位、创新与候选比较，到最小验证、证明或实验、写作与审阅。八个技能由宿主助手执行实际任务，标准库 Python 工具保存主张、材料、引用、进度和恢复状态。

本目录只维护一份当前内容，发行包固定为 `research-workflow-template.zip`。更新由来源清单和 SHA-256 内容指纹标识；项目数据格式、记录与依赖的必要版本字段继续保留。

## 开始使用

需要 Python 3.11 或更新版本，以及 macOS 或 Linux。Windows 的写锁尚不支持。在本目录运行：

```sh
python3 tools/research.py init --output ../my-research --title '我的研究问题'
python3 tools/connect_skills.py install --root ../my-research
python3 tools/connect_skills.py check --root ../my-research
```

将输出路径换成尚不存在的新目录。然后在 Codex 等兼容宿主中打开新项目，描述研究兴趣或当前任务即可。已有项目先运行 `resume`。首次接入和显式升级分别保护已有目录与本地修改；不改全局技能或个人完整版。

## 按需要查阅

| 文件 | 用途 |
|---|---|
| [中文介绍与使用说明](中文介绍与使用说明.md) | 从第一次启动到日常恢复、技能更新与交付 |
| [English user guide](USER_GUIDE.en.md) | 与中文指南对应的完整英文介绍与使用说明 |
| [命令行详细用法](docs/07-core-usage.md) | 查询、标准输入、原子批量登记、配置与检查点 |
| [技能与方法](docs/08-skills-and-methods.md) | 八个技能、项目内接入、方法资源与升级边界 |
| [学科适配](docs/02-disciplinary-adaptation.md) | 六类学科、九类方法及跨学科组合 |
| [证据契约](docs/03-evidence-contract.md) | 主张、材料、支持关系和研究进度的边界 |
| [当前验收](evals/current/latest.json) | 当前内容的实际检查结果与执行范围 |
| [发行验收](docs/10-release-readiness.md) | 来源、归档、干净环境与可交付检查 |
| [平台核验](docs/11-linux-validation.md) | 实际平台范围、复查方法与未测环境 |

## 检查与边界

```sh
python3 -B tools/check_core.py --test-timeout 360
python3 -B tools/release_package.py check
```

命令行离线工作，不执行材料中的命令、不上传数据或自动投稿。登记或软件检查通过不认证证明、创新性、伦理批准或期刊合规；相应检查仍由作者与实际执行者负责。完整的学科合成材料和回归测试保留在 `evals/`，纯旧发行阶段记录移出当前包。

原创实现、指导与合成材料采用[MIT许可证](LICENSE)。外部方法资料保留自身权利，见[来源说明](provenance/ORIGIN.md)与[方法来源](profiles/sources.json)。维护流程见[贡献说明](CONTRIBUTING.md)，数据边界见[安全说明](SECURITY.md)。本目录与个人包独立，远程发布由维护者显式执行。
