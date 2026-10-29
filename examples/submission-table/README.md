# 配对栏结果到表格与可编译稿源

本例读取[配对栏公开案例](../paired-pens/README.md)的实际输出，不再保存一份原始数据。它生成两张可编辑三线表、一份短 LaTeX 稿源和逐文件清单。

在源码根目录运行，两个输出目录均须尚不存在：

```sh
python3 -B examples/paired-pens/analyze.py --output ../paired-pens-output
python3 -B examples/submission-table/build.py --data ../paired-pens-output/paired-differences.csv --output ../table-delivery
```

Windows PowerShell 可把 `python3` 换成已安装的 Python 3.11+ 命令，例如 `py -3`。输入和脚本可用绝对路径，因此也可从其他工作目录调用。父目录须已存在，带空格的路径加引号。

## 产物与数据合同

交付目录包含 `main.tex`、原字节复制的 `paired-differences.csv` 和 `manifest.json`。清单给出实际字节数、SHA-256、生成来源与当前检查状态，不将自身摘要嵌入自身。脚本不运行外部命令，也不上传或投稿。

CSV 列必须依次为 `block,control_mean_g,treatment_mean_g,difference_g`，六行分别代表六个匹配区组。区组标签唯一，使用最多24个可打印 ASCII 字符；LaTeX 特殊字符作为文本转义。测量为普通十进制数，最多12位小数、绝对值不超过十亿；差值必须等于饲料 B 栏均值减对照栏均值。脚本拒绝额外或缺少字段、非有限值、重复区组和不一致差值。

区组代码居中，测量使用 `dcolumn` 按小数点对齐，描述性文字列向左。表头独立居中，首行及规则线留出适当间距；数值不靠整表缩小字号来挤进版心。第一张表保留输入精度，汇总表的估计与区间显示两位小数，精确 P 值显示四位小数。完整输入保持原样。

本例固定六个匹配区组，配对 t 参考区间使用自由度5的97.5%分位数 `2.5705818356363146`，沿用公开案例中的数值与独立、近似正态区组差工作模型。六个差值的样本方差为零时，区间记录为 `null`、表中显示横线，并说明未计算原因。随机化计算仍枚举六个区组内的整栏标签互换，假设各区组独立、公平分配且不存在跨栏干扰，并检验尖锐无处理效应零假设。它保留全部64种分配和等于观测统计量的情况。更换研究设计或区组数时应选用相应方法。

## 编译与版式核对

生成器只需 Python 标准库。实际 PDF 编译需要已有的 pdfLaTeX、`geometry`、`booktabs` 和 `dcolumn`；它不会安装 TeX 或额外包。从交付目录运行两遍：

```sh
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

在新的检查目录保存编译输出和页面预览。检查退出状态、交叉引用及 overfull 警告，再按实际页面尺寸查看两张表，分别核对表头归属、小数点、负号、零值、首行与行间距。缺少编译环境时仍可交付稿源，清单的编译和目视状态保持 `not-run`。实际编译与目视检查结果放在既有交付说明或项目记录中，不以生成成功代替验收。

本例采用普通 article 文类。已有期刊模板时保留其文类、字体和表题规则，将表格内容接入真实主稿；目标刊物的要求按当前作者指南核对。
