# 复跑数值自查

使用共同解释器；不联网、不安装依赖。指定输入与一个新输出目录：

```sh
EVAL_PYTHON -I -B WORKSPACE/checks.py --input INPUT_DIR --output WORKSPACE/recheck-new
```

`--input` 可替换为同结构输入目录，`--output` 可替换为新的输出目录。首次数值结果保存在 `results/checks_results.json`，复跑不覆盖它。解析证明及来源页码见 `report.md`；`audit.md` 为同内容交付副本。有限网格检查不是一般证明。没有拟合统计模型，没有数据阶段交接。
