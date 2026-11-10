# 结果表与稿、图、图注的交付核对

一次明确的数值变化可能涉及摘要、主图或图注。沿用原分析输出中的稳定行标识、单位、分母和适用范围。对确实影响解读的字段建立核对，例如小亚组的实测人数。让项目的生成脚本同时重建这些材料；以下只读检查用于发现仍然引用旧数字或误贴标签的地方。

将核对说明保存在项目内，表和文件路径相对于说明文件。例中判断的权威来源是项目的 estimates.csv。表里有 id、value、unit 和 n 四列。

```json
{
  "table": "estimates.csv",
  "id_column": "id",
  "checks": [
    {"row":"main","file":"abstract.md","after":"Primary difference:","expect":"{value:.2f} {unit}"},
    {"row":"main","file":"figure.svg","after":"Primary difference","before":"Sensitivity","expect":"{value:+.2f}"},
    {"row":"small_group","file":"caption.txt","after":"June hot days measured:","expect":"{n}"}
  ]
}
```

```sh
python3 SKILL_DIR/scripts/check_result_surfaces.py checks.json
python3 SKILL_DIR/scripts/check_result_surfaces.py checks.json --render brief.pdf --page 1 --output preview.png
```

`after` 在文件内必须唯一。紧随其后的摘录与表内字段匹配，默认范围为本行；`before` 把检查扩展到指定结束标记前，例如 SVG 中相邻的文本图元。可用原样字段或十进制定点显示精度。选择实际描述该估计的标签，保留原文标点及标记。报告列出各项预期内容、实际状态和文件指纹。仅文字匹配支持 UTF-8 的 Markdown、纯文本、TeX 与 SVG 文本节点。位图、PDF 和转为路径的字形需要查看实际图件。该检查不分析线段坐标、统计推断或相互矛盾的其他叙述。

可选预览使用已安装的 Poppler `pdftoppm`，将指定 PDF 的一页写入新的 PNG。查看该页的图轴、数值、单位、图例、样本量和裁切，记录实际页码和观察；机器报告的 `rendered` 只表示成功渲染。完整论文的逐页检查按实际交付范围另行执行。退出码 0 为声明的核对项匹配，1 为摘录冲突，2 为输入错误或无法核查。保留含缺项的报告，并在已有审查记录中说明下一步。
