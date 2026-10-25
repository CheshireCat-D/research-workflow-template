# 重跑

仅需Python3标准库。从项目目录运行 `python3 artifacts/run.py`；也可任意cwd用项目代码路径调用。代码按自身位置定位inputs，重建results.json及run-metadata.json；结果数值无随机过程，输入seed29017不适用。实际原始命令、stdout、stderr、退出码与墙钟时间在项目旁logs；项目内run-metadata记录本次数值运行。results.json内容确定性，metadata中的耗时随运行变化。

公式为闭式解，不需要积分网格；有限差分步长仅用于导数核对。小H使用expm1并有H=0分支。复算会改变metadata的指纹，研究恢复时应先查看变化并重新登记相关产物/活动，不能直接覆盖后声称原检查仍新鲜。
