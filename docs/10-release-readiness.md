# 当前发行验收

本包采用单一当前版。源码仓库保留当前实现、测试与必要的冻结评估证据；用户包固定为 `research-workflow-template.zip`，只交付当前运行资源、双语指南、许可与来源归属，不含评估案例、测试、开发修改记录或旧版。个人技能包、真实研究项目及其记录独立；不因整理发行文件而清空研究项目的记录版本或历史。

| 要求 | 当前证据与验收方式 |
|---|---|
| 九个核心技能 | [技能接入](08-skills-and-methods.md)、项目内复制和布局检查 |
| 七学科与十类方法 | [方法和学科画像](02-disciplinary-adaptation.md)、[稳定目录](../design/catalog.json)，按实际任务绑定范围 |
| 研究行为回归 | [基础素材](../evals/d2/README.md)、[跨学科素材](../evals/d3/README.md)与独立审阅指纹；不同材料组不是软件旧版 |
| 法学新增任务 | [两项合成案例及范围](../evals/legal/README.md)、[覆盖](../evals/legal/coverage.json)与独立审阅；旧冻结任务不改写为新增方法的验证 |
| 登记与恢复闭环 | [核心用法](07-core-usage.md)，含标准输入、批量失败回滚、记录查询、配置更新与只读恢复 |
| 本地副本升级 | 完整性预检、拒绝本地修改、暂存与捕获失败回滚；切换间隙和恢复边界单独说明 |
| 来源与许可 | [MIT](../LICENSE)、[来源说明](../provenance/ORIGIN.md)、[逐文件清单](../provenance/file-origins.json) |
| 当前软件与平台检查 | [唯一当前核验记录](../evals/current/latest.json)；只报告真正执行的环境，不沿用旧阶段通过状态 |
| 当前用户归档 | `dist/research-workflow-template.zip`、相邻SHA文件及 `dist/release-validation.json`；核对用户资源闭包、链接、确定性构建和干净运行 |

`dist/`是生成产物，不进入源归档。最终归档身份和后续干净运行结果由伴随记录提供，避免把ZIP自己的SHA嵌入自身形成循环。构建工具拒绝覆盖已有输出：已有当前归档时，先在独立临时目录构建和验收，确认后再替换当前文件，而不在包内积累旧发行包。最终用户交付目录只保留当前 ZIP、SHA 文件和一次当前验收摘要。

首次生成时，从工具包根目录执行：

```sh
python3 -B tools/check_core.py --test-timeout 360
python3 -B tools/release_package.py check
python3 -B tools/package_user.py check
mkdir -p dist
python3 -B tools/package_user.py build --output dist/research-workflow-template.zip
python3 -B tools/package_user.py verify --archive dist/research-workflow-template.zip
python3 -B tools/package_user.py smoke --archive dist/research-workflow-template.zip
```

源内容变动后先审阅差异，再运行 `tools/release_package.py index` 更新来源清单，并重新验收。不能为让校验通过而自动接受未知变化。

`package_user.py` 复用 `core.bundle.build_payload()` 的运行资源闭包和净化后的目录，再将技能恢复为标准的 `skills/` 源布局，保留原相对链接。用户包使用面向日常工作的[中文指南](user-package-guide.md)与[英文指南](user-package-guide.en.md)，以根目录的 `中文介绍与使用说明.md`、`USER_GUIDE.en.md` 发布；简洁双语 README 与来源归属随包生成。详细开发文档链接到公开源码仓库，包内 Markdown 链接必须全部可解析。

用户包不包含 `evals/`、`tests/`、`.github/`、贡献记录、开发检查工具或来源仓库的全文件索引。其 `USER-PACKAGE-MANIFEST.json` 记录当前交付文件的字节身份；`profiles/sources.json` 与 `provenance/ORIGIN.md` 保留方法来源及许可边界。完整评估证据仍由源码仓库维护，`options` 明示这些材料不在用户运行资源内。

干净用户验收先验证并捕获当前 ZIP 的文件，再写入独立临时目录。空 HOME 下实际运行初始化、技能接入、登记、检查点与恢复；搬迁项目并移走工具包后，用项目副本继续查询与恢复，核对源文件和只读项目的字节及修改时间。缺失资源、坏链接、篡改和混入开发文件由专项测试拒绝。

完整源码归档另由 `tools/release_package.py build/verify` 在临时目录检查，不作为最终用户 ZIP。CI 同时运行完整源码回归、临时源码归档解压检查和用户包构建／验证／干净运行；本地与托管执行按实际 commit 和归档 SHA 分别记录。[Linux复查](11-linux-validation.md)另有说明。Windows、macOS 和 Linux 分别在 CI 中运行；工作流配置不等于本次执行已通过，实际结果须绑定到相应提交。

检查通过只说明所声明范围内的工程与登记一致性，不认证研究结论、伦理批准、场所政策或投稿接收，也不表示已经创建、推送或发布GitHub仓库。
