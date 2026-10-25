# 当前发行验收

本包采用单一当前版：源码与归档使用固定名称，更新以来源清单和内容指纹区分。个人技能包、真实研究项目及其记录独立；不因整理发行文件而清空研究项目的记录版本或历史。

| 要求 | 当前证据与验收方式 |
|---|---|
| 八个核心技能 | [技能接入](08-skills-and-methods.md)、项目内复制和布局检查 |
| 六学科与九类方法 | [方法和学科画像](02-disciplinary-adaptation.md)、[稳定目录](../design/catalog.json)，按实际任务绑定范围 |
| 研究行为回归 | [基础素材](../evals/d2/README.md)、[跨学科素材](../evals/d3/README.md)与独立审阅指纹；不同材料组不是软件旧版 |
| 登记与恢复闭环 | [核心用法](07-core-usage.md)，含标准输入、批量失败回滚、记录查询、配置更新与只读恢复 |
| 本地副本升级 | 完整性预检、拒绝本地修改、暂存与捕获失败回滚；切换间隙和恢复边界单独说明 |
| 来源与许可 | [MIT](../LICENSE)、[来源说明](../provenance/ORIGIN.md)、[逐文件清单](../provenance/file-origins.json) |
| 当前软件与平台检查 | [唯一当前核验记录](../evals/current/latest.json)；只报告真正执行的环境，不沿用旧阶段通过状态 |
| 当前发行归档 | `dist/research-workflow-template.zip`、相邻SHA文件及 `dist/release-validation.json`；核对清单、确定性构建和干净解压 |

`dist/`是生成产物，不进入源归档。最终归档身份和后续干净运行结果由伴随记录提供，避免把ZIP自己的SHA嵌入自身形成循环。构建工具拒绝覆盖已有输出：已有当前归档时，先在独立临时目录构建和验收，确认后再替换当前文件，而不在包内积累旧发行包。

首次生成时，从工具包根目录执行：

```sh
python3 -B tools/check_core.py --test-timeout 360
python3 -B tools/release_package.py check
mkdir -p dist
python3 -B tools/release_package.py build --output dist/research-workflow-template.zip
python3 -B tools/release_package.py verify --archive dist/research-workflow-template.zip
```

源内容变动后先审阅差异，再运行 `tools/release_package.py index` 更新来源清单，并重新验收。不能为让校验通过而自动接受未知变化。

干净验收将当前ZIP解压到独立目录，用空HOME运行完整检查和初始化、技能接入、登记与恢复示例；搬迁项目后用复制接口继续，确认不依赖原源码或个人包。[Linux复查](11-linux-validation.md)和托管CI各按实际执行单独记账。Windows写锁不受支持。

检查通过只说明所声明范围内的工程与登记一致性，不认证研究结论、伦理批准、场所政策或投稿接收，也不表示已经创建、推送或发布GitHub仓库。
