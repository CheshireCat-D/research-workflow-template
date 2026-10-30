# 当前研究摘要

采用作者批准的 alpha=0.05、rho=4，rho在观察前固定；intrinsic time 为 v=[0,1,10,100]。按所给公式 b(v)=sqrt((v+rho)[log(1+v/rho)+2log(1/alpha)]) 计算，两侧 normal-mixture 边界依次为 4.895493661362、5.574319733574、10.070709270873、31.015388968276。完整数值见 results/result.json 和 results/table.csv；v=10 时边界为 10.070709270873。

这是规定 sub-Gaussian 条件下、预先固定正 rho 的公式评估；alpha和预先固定rho的政策未变。程序重算没有证明新的覆盖保证，也不允许事后选择rho；原始来源和公式脚本未改动。来源卡见 notes/source-check.md，本轮执行与算术比较见 notes/stage-c-validation.json。尚无人类专家完成内容认可。
