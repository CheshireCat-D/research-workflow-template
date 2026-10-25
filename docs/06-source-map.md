# 外部规范与方法来源地图

通用来源核对日期：2026-10-24；法学增补核对日期：2026-10-25。下列官方资源用于架构选择，不复制其完整清单，也不表示已核对所有扩展、期刊要求、机构规则或司法辖区。实际项目应保存所选版本、适用理由、定位、核对日期和未完成事项。

| 资源 | 设计用途 | 适用边界 |
|---|---|---|
| [EQUATOR Library](https://www.equator-network.org/library/) | 按健康研究设计选择报告规范；库中分别列出随机试验、观察研究、系统综述、定性研究等入口 | 报告充分性不等于研究质量或伦理批准；不能把 PRISMA 强制用于所有文献综述 |
| [ARRIVE Guidelines](https://arriveguidelines.org/arrive-guidelines) | 为适用的动物研究提供报告要求入口，关注研究设计与实验单位等信息 | 只在动物研究及相应场景中选择，不是全部生命科学项目的通用清单 |
| [AHA Statement on Standards of Professional Conduct](https://www.historians.org/resource/statement-on-standards-of-professional-conduct/) | 支持史料身份、出处、解释与反对材料的可追溯设计 | 对应历史研究专业标准，不能替代所有人文方法或法律规定 |
| [OHA Principles and Best Practices，官方 2025 PDF](https://oralhistory.org/wp-content/uploads/2025/10/2025-OHA-Principles-and-Best-Practices-Complete.pdf) | 为口述史的同意、使用、保存与访问约定提供来源 | 该文件汇编含更早采纳的内容；不能仅据 URL 年份称其全部规则于 2025 年新制定 |
| [COS TOP Guidelines](https://www.cos.io/initiatives/top-guidelines) | 参考研究透明性与可核验实践的模块化设计，区分披露、分享与独立核对 | 主要面向经验研究主张；不是对所有材料强制开放，也不替代人文论证 |

这些来源支持“按方法与适用范围选择规范”的设计，而非产生通用质量分数。工程、农业、具体学科子领域及目标场所的其他专门规范在适配实施时继续核对，不把本表视为完整或最新的规范库。

法学另参照 [立法法2023官方文本](https://fgk.chinatax.gov.cn/zcfgk/c100009/c5211769/content.html)、[最高法案例指导实施细则官方转载](https://www.hncourt.gov.cn/public/detail.php?id=157832)、[英国立法数据库帮助](https://www.legislation.gov.uk/help)与[未整合变更](https://www.legislation.gov.uk/changes)、[美国第九巡回裁判说明](https://www.ca9.uscourts.gov/decisions)、[美国最高法院意见说明](https://www.supremecourt.gov/opinions/opinions.aspx)及[OSCOLA第五版官方PDF](https://www.law.ox.ac.uk/sites/default/files/2026-03/OSCOLA%205.pdf)。它们分别支持具体法域中的时间、权威或引证检查，不拼成一套全球法律效力规则；OSCOLA仅按目标场所选用。英国两个页面直接抓取失败，实际访问为官方搜索索引内容，未据此声称全文逐项核验。逐条版本、访问与适用限制见 [sources.json](../profiles/sources.json)。

未来每条规范引用应记录：`id`、`url`、`version_or_date`、`applies_to`、`checked_at`、`content_access`、`source_locator`、`remaining_gaps`。未读取的全文或附件要明确标记，不能由搜索摘要认证条款内容。公共规范链接可以记录，受版权保护的整套文本不因链接存在而自动取得再分发许可。
