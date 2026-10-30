# 复跑说明

使用共同解释器Python标准库，无需安装依赖。运行命令中的路径可替换；输出目录必须为空或不存在，首次results/不可覆盖。

```sh
PY=EVAL_PYTHON
SCRIPT=WORKSPACE/analyze.py
INPUT_DIR=PRIOR_INPUT_DIR
OUTPUT_DIR=WORKSPACE/reproduction_new
"$PY" -I -B "$SCRIPT" train --input-dir "$INPUT_DIR" --output-dir "$OUTPUT_DIR"
```

train要求输入目录下有data/hour_2011.csv与data/day_2011.csv，严格只在2011-10-01前拟合，评价2011-10-01至12-31，生成审计、冻结参数、指标及预测。上述只用于复现2011开发结果，不用于下一阶段重训。

无需重训的评分：

```sh
PY=EVAL_PYTHON
SCRIPT=WORKSPACE/analyze.py
MODEL=WORKSPACE/results/model.json
HOUR_FILE=/path/to/authorized/hour_new.csv
NEW_OUTPUT=/path/to/new_score_directory
"$PY" -I -B "$SCRIPT" score --hour-file "$HOUR_FILE" --model "$MODEL" --output-dir "$NEW_OUTPUT" --start 2012-01-01 --end 2012-12-31
```

评分文件需包含dteday(ISO日期)、hr(0–23)、workingday(0/1)、cnt(实际整数结局)。该接口用于有结局后评价；预测均值本身来自已冻结参数。其他列忽略。未来实际文件未提供也未访问；上面只是下一阶段命令模板，可更换日期范围。score会保存输入/模型SHA与retrained=false证明链，并按同样算法输出完整日期、子组及两种块长区间；调用前须核验新输入唯一键与口径。模型SHA-256：`f8a758c6c73cf7e0cfcfa0936b594afb8f23b1260610ecae15929f601dc8e5d4`。

本次实际执行：

```sh
"$PY" -I -B "$SCRIPT" train --input-dir "$INPUT_DIR" --output-dir WORKSPACE/results
"$PY" -I -B WORKSPACE/verify.py
"$PY" -I -B "$SCRIPT" score --hour-file "$INPUT_DIR/data/hour_2011.csv" --model "$MODEL" --start 2011-10-01 --end 2011-12-31 --output-dir WORKSPACE/score_check
```

三条命令已退出0；首次输出保留。verify.py是本目录定位的2011阶段独立检查器，需保留同级原input；生产评分analyze.py通过参数可脱离该布局。结果和预测文件使用全双精度表示，报告舍入仅展示。环境详见results/runtime.json。
