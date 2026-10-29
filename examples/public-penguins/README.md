# 公开企鹅数据：同物种内雌雄体质量比较

本例对真实动物生态测量数据做一项有限的描述性二次分析：分别计算三物种的雄性均值减雌性均值，并按岛屿和年份共同分层。先读 `question-method.md`。本例不主张重现原论文的全部模型，也不把这项小分析称为新的论文成果。

使用 Python 3.11+ 标准库，无须安装依赖。在仓库根目录运行，输出目录必须尚不存在、其父目录必须已经存在：

```sh
python3 -B examples/public-penguins/fetch_data.py --output ../penguins-input
python3 -B examples/public-penguins/analyze.py --input ../penguins-input/penguins.csv --output ../penguins-results
```

Windows PowerShell 可把 `python3` 换成 `py -3 -X utf8`。也可从其他工作目录使用脚本的完整路径；输入和输出始终由参数显式指定。

## 数据与取得方式

原始公开 CSV **不随本例或用户包重分发**。`source.json` 固定了上游提交、单个下载 URL、字节数、SHA-256、提供者和来源链接。`fetch_data.py` 是本例唯一的网络入口：只下载这份固定输入，核对字节数与 SHA-256 后写入用户指定的新目录；已有目录会被拒绝。失败下载可能留下空目录，再试时换一个新路径。

数据来自 [palmerpenguins 官方项目](https://allisonhorst.github.io/palmerpenguins/)，由 Kristen Gorman 与 Palmer Station LTER 提供，**原始数据为 CC0**。工具包的 MIT 许可不替换数据许可。本例统计表、结果文字和图均由本分析生成，没有复制来源图件。

固定提交为 `8957207b78d6ccd1b4654a9dd9c9041b657478ab`；输入 SHA-256 为 `f204db2c753b0937caac3cb35258562c14f073e4bbc76be24b4c51ce22767a93`。分析器离线运行；对其他合法输入，`matches_pinned_public_input=false`，生成短稿会明确标记其不匹配固定公开数据。

## 结果与口径

固定真实输入共344行，性别、物种和体质量完整333行。性别缺失11行，体质量缺失2行，二者重叠2行；不是排除13行。三物种的雄减雌均值差为 Adelie `674.6575 g`、Chinstrap `411.7647 g`、Gentoo `805.0947 g`。15个可比较岛屿—年份层均为正，但幅度不同；全部27个网格中的12个空层仍保留。Adelie 覆盖三个岛屿，Chinstrap 仅 Dream，Gentoo 仅 Biscoe。

`observed/` 保存本次实际复算的紧凑结果：`summary.json`、`species_contrasts.csv`、`strata.csv`、两份可编辑 SVG 及 `results.md`。没有把原始 CSV、逐行排除表、完整练习项目或冗长日志放进示例。

用户实际重跑时，新输出目录包含：

- `summary.json`：输入哈希、样本流转、缺失、物种差异、分层覆盖与敏感性结果。
- `grouped_by_species_sex.csv`：各物种各性别的原始分母、可用 n、均值、样本标准差、中位数及范围。
- `species_contrasts.csv`：物种内雄减雌差异、共同层权重结果及缺失性别分配范围。
- `strata.csv`：完整27层，含分母和空层状态。
- `row_audit.csv`：CSV行号、缺失字段及两种分析的纳入标记。
- `species-mass.svg`、`stratum-differences.svg`：原生文本、点和线，可分别编辑；没有误差条或整图位图嵌入。
- `results.md`：简短中文问题、方法、结果、范围与下一步。

必要列为 `species,island,year,sex,body_mass_g`；本例固定三物种、三个岛屿和2007—2009年这些水平。空字符串或 `NA` 为缺失；未知类别、畸形行、重复表头、非有限或非正体质量及空输入会明确报错。其他原始列不参与筛选。主分析排除物种、性别或体质量缺失行；分层分析再要求岛屿和年份完整。不插补、不把缺失当零，不因喙或鳍测量缺失排除可用体质量。

CSV 中不可计算的统计量留空，JSON 中为 `null`；标准差至少需要两个值，并使用 n−1 分母。没有观测或无法同时比较两性时，不填成零差异。共同层权重按每个物种可比较层的雌雄可用 n 之和计算，并对两性使用同一组权重。每物种体质量已知、性别缺失行不超过16时，枚举全部雌雄分配，报告均值差的最小和最大值；这是缺失性别的敏感性范围，不是置信区间。

简化 CSV 没有个体和巢标识，不能据此核实配对、重复个体或独立观察单位，因此没有计算 p 值、标准误或总体置信区间。下一步先检查原始身份、抽样与测量时点，再按真实结构选择推断方法。

所有生成 CSV 显式使用 LF 换行。发布副本仅补充这一输出约定；科学计算与冻结执行版本相同，真实复算确认 JSON、SVG、短稿逐字节一致，四份 CSV 仅由 CRLF 统一为 LF。

## 审阅与项目恢复记录

[独立 base-R 核对](../../evals/public-data/assessment.md)给出实际复算结论与重跑命令；[执行记录](../../evals/public-data/recording.json)保留来源、失败与纠正、登记及迁移恢复的范围。上面的命令生成分析产物；需要持续管理时，按[命令行指南](../../docs/07-core-usage.md)将产物登记到独立的 RWT 项目，再恢复该项目。这里不分发完整临时项目副本。

## 单一离线测试入口

在仓库根目录运行：

```sh
python3 -B -m unittest discover -s tests -p test_public_penguins.py -v
```

专项测试只定义于 `tests/test_public_penguins.py`；`synthetic.csv` 是原创、可手算的小夹具，用于核对均值/标准差、缺失分母、空层与单性别层、共同权重、未知性别穷举范围、输入校验、原生 SVG、LF 输出与拒绝覆盖。夹具数值不是生态研究结果，CI 不联网也不下载真实 CSV。真实数据复算是上面单独的取得与运行步骤。

背景来源：Gorman KB, Williams TD, Fraser WR (2014). *Ecological Sexual Dimorphism and Environmental Variability within a Community of Antarctic Penguins (Genus Pygoscelis)*. PLoS ONE 9(3):e90081. [doi:10.1371/journal.pone.0090081](https://doi.org/10.1371/journal.pone.0090081)。来源支持范围见本例的资料说明；本例只做体质量的描述性比较。
