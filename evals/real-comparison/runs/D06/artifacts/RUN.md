# 冻结模型的两年审查复跑

共同Python 3.12.14，全部运行用`-I -B`，只需标准库，不安装包。先确认原model.json的SHA-256为`84c6c80033718b1c0b7c0333d90ebe66c0978fd305b44d65ffd5ca9fd6f19a47`。

把下面输出目录替换为可写的新目录。代码读取指定INPUT内的四份2011/2012 CSV及清单，原参数和原2011结果只读。不会调用fit；核对2011训练sum/n/mean不是重训。

```sh
EVAL_PYTHON -I -B \
 WORKSPACE/stage_b.py \
 --input-dir INPUT_DIR \
 --prior-dir WORKSPACE/stage_a_snapshot \
 --model WORKSPACE/model.json \
 --output-dir /absolute/path/to/new-output
```

独立核对新输出（实际已对stage_b_results执行通过）：

```sh
EVAL_PYTHON -I -B \
 WORKSPACE/verify_b.py \
 --result-dir /absolute/path/to/new-output \
 --model WORKSPACE/model.json
```

成功标识为verification.json中的`"status": "passed"`；该验证器检查本次8734小时/366日输入的预定评价规模，并逐小时展开所有4000次bootstrap。评价脚本stage_b.py本身可指定合法输入目录，冻结模型SHA和原训练恢复条件保持固定。

本次实际输出在stage_b_results/；原2011结果和原RUN.md在stage_a_snapshot/，原model.json从未覆盖。主报告更新在report.md；新交接在handoff.md，执行日志stage_b_run.log、stage_b_verify.log。publish_b.py可从已保存结果重写根目录报告/交接，其参数为`--workspace WORKSPACE --result-dir /absolute/path/to/new-output`；运行会覆盖两份文稿，只在要更新文稿时执行。

stage_b_results中的comparison_metrics.csv并列提供2011Q4和2012所有总体/分组指标；results.json为2012全精度指标，根目录旧results.json仍是2011原始结果。
