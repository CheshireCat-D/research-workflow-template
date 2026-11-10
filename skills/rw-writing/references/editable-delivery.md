# 从 Markdown 交付可编辑的 Word、LaTeX 和 PDF

作者以 Markdown 为主稿、合作者需要 Word 或 LaTeX 时，可用已有的 Pandoc 导出。先复制本次确认的稿源、图件和文献库到一个新的版本目录。以下命令在该目录内运行，输出名应当尚未使用。若作者指定 Word 或 TeX 为主稿，沿用那个文件修订；收到合作者的修改时，把已接受的改动合回主稿，再生成下一版。

## 准备稿件和图件

保留作者的图源，例如 `figures/ozone.svg` 和绘图代码。用原绘图工具另存清晰的 PNG，供 Word 和 XeLaTeX 共用。稿内使用相对路径。下面这段 Markdown 使用已有的独立图注，图中数值来自同一版结果表。

```markdown
![Measured ozone differences](figures/ozone.png){width=92%}

*Figure 1. Hot-minus-other differences in measured afternoon ozone.
The primary estimate weights June through September equally.*
```

保留原文的引文键，例如 `[@airquality]`，以及相应的 `references.bib`。需要指定引文体例时，把已确认的 CSL 文件也放在目录内，并在两条 Pandoc 命令中使用同一个 `--csl=style.csl`。Word 接收的是排好的引文和书目文字；需要文献管理器活动字段的项目须在目标编辑器中另行核对。

## 导出并检读

```sh
pandoc manuscript.md --from=markdown-implicit_figures --citeproc --bibliography=references.bib -o manuscript.docx
pandoc manuscript.md --from=markdown-implicit_figures --citeproc --bibliography=references.bib --standalone -V geometry:margin=25mm -o manuscript.tex
xelatex -interaction=nonstopmode -halt-on-error manuscript.tex
xelatex -interaction=nonstopmode -halt-on-error manuscript.tex
```

`markdown-implicit_figures` 让已有的独立图注只出现一次。以图片替代文本自动生成图注的稿件应保留 Pandoc 的默认 Markdown 读法。没有引文库的稿件可省略两条命令中的引文参数。工具未加入 PATH 时，使用本机已有程序的实际路径；中文稿应沿用目标模板和已验证的中文字体配置。这里的 `manuscript.pdf` 由所交付的 TeX 编译得到。

用 Word 或已有 LibreOffice 打开 DOCX 并导出到单独的预览目录。需要命令行预览时，先建好 `qa-word` 和 `qa-tex` 两个目录，再运行：

```sh
soffice --headless --convert-to pdf --outdir qa-word manuscript.docx
pdftoppm -png -r 120 qa-word/manuscript.pdf qa-word/page
pdftoppm -png -r 120 manuscript.pdf qa-tex/page
```

在可编辑稿中确认正文与图注可选取、修改。逐页查看两套渲染，核对结果和单位、图与图注的位置、引文与条目的对应、图轴、字号和分页。臭氧短稿试跑中，两种渲染均为一页，可见正文的 40.16 ppb、图内另两项 +45.38 和 +47.90、Figure 1 图注及资料条目。该次 Word 预览使用 LibreOffice；若收件人要求指定版本的 Word，以目标环境的导出结果复查。

交付所需的 `.docx`、`.tex`、`.pdf`，同时保留 `.md`、文献库、实际使用的模板或 CSL、`figures/` 中的插图和可编辑图源。将这些文件复制到另一处，从新目录重新编译 TeX 并打开 DOCX，再核对相对链接。对持续项目，按需把这版文件登记为交付物，由[本地评阅页](../../rw-review/references/review-desk.md)导出选定版本。
