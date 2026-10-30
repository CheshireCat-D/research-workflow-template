# 当前研究摘要

作者已将工作参数改为 alpha=0.05、rho=4，rho 在观察前固定；两侧总预算 alpha 和预先固定 rho 的政策未变。

计算公式为 b(v)=sqrt((v+rho)*(log(1+v/rho)+2*log(1/alpha)))。

| v | 边界 b(v) |
| --- | ---: |
| 0 | 4.895493661362 |
| 1 | 5.574319733574 |
| 10 | 10.070709270873 |
| 100 | 31.015388968276 |

完整精度见 results/result.json 与 results/table.csv。适用范围：l0=1；S 与 −S 在同一非负内在时间 V 下满足相应 sub-Gaussian 指数控制，不能将任意经验方差直接作为 V。这里只复算所给条件公式，不重做覆盖证明，不做模拟覆盖验证，不评估事后选择 rho。来源卡定位仍是提供者的释义，未独立阅读 PDF 正文。

旧 rho=1 的参数、结果、表与摘要完整保存在 .research/versions/A-initial/；修订前的实际漂移态完整保存在 .research/checkpoints/C-drift-before-recompute/。

下一步：将 rho=4 的边界表与本摘要交作者内容复核；暂不扩展到事后选择 rho。尚无人类专家完成内容认可，目标期刊未定，未获投稿授权。
