# 《寻找狄利克雷》HTML 阅读版

项目位置：M:\Dirichlet-Web。原稿 M:\Dirichlet 保持只读。

使用 Node.js 运行 server.mjs，然后打开 http://127.0.0.1:4173/ 。
网页入口是 index.html。普通静态托管也可使用这些文件；不要直接用 file:// 打开模块网页。

## 本版内容

- 直接从 main1.tex 导入 30 个章节/后记/附录单元，正文是可选择的 HTML 文字。
- 596 处数学表达式（367 个不同表达式）在构建时通过 KaTeX 渲染。
- 110 处原稿 index 全部建立双向链接；能可靠定位的词直接链接，其余在原位置显示小索引入口。索引面板可返回精确标记位置。
- 左侧导航为黑色。章节底色与文字色按 main1.tex 的 xcolor/dvipsnames 命令计算；章节中途的颜色切换也保留。
- 右侧外围背景为章节 RGB 的 72% 加黑色 28%；正文底色不压暗。
- 12 段 LilyPond 乐谱使用本机 LilyPond 2.24.4 预编译：11 段行内、1 段行间，SVG 直接嵌入。
- 正文插入的 26 个 PDF 全部转换为 33 页 SVG，按原位置、原页序嵌入。原 PDF 链接只作为备用。
- 已有音频以原生播放器嵌入，按需加载。
- original.html 保留之前的 268 页中文版 PDF 阅读入口。

## 内容、颜色与资源

content/ch-*.html 为按章生成的 HTML，content/book.json 为章节与索引目录。
content/ch-*.tex 是本次导入用的章节源材料，非前端必需文件；tools 与 work 不应公开部署。
content/scores.json、content/pdf-svg.json 记录乐谱和图谱来源、校验值、输出文件。
reports/import-report.json、math-report.json、colors.json、validation.json 为核对报告。

颜色来自 LaTeX 自然颜色模型：先按原模型逐步混合，再把 CMYK/gray 转为 RGB；首尾 OliveGreen 采用本机 default_cmyk ICC 转为 sRGB，作为印刷色的屏幕近似；不再使用 PDF 像素取色。印刷色彩管理与浏览器显示可能有差异。

## 更新流程

使用本机配置好的 Python（pypdf）和 Node.js：
1. tools/import_book.py 读取最新 main1.tex，提取章节及乐谱源。
2. tools/derive_colors.py 读取逐章颜色命令并计算 RGB。
3. tools/build_scores.py 预编译乐谱 SVG。
4. tools/convert_pdfs.py 转换所有引用 PDF 的各页。
5. 再运行 tools/import_book.py，接入新颜色及 SVG。
6. tools/build_math.mjs 生成数学 HTML。
7. tools/validate_site.py 检查所有索引、公式和资源引用。

源码只作为数据读取，不执行 main1.tex 的 shell-escape 或原目录脚本。
LilyPond 在本项目 work/scores 中编译经过检查的纯乐谱片段，不重新编译整本 TeX。

## 当前边界

这是针对本书的 TeX→HTML 转换器，不是通用 LaTeX 引擎。纸本页码、浮动排版和装饰坐标不会逐像素复刻；文字、公式和资源仍需作者逐章校对。
前置页仍可从原版入口阅读，其日文按作者要求保留。
索引显示源稿明确标记的位置，不宣称已找出所有未标记的同名词语。

## Live Server 兼容与完整性
阅读器通过逐章 JSON 载入 HTML，避免 Live Server 向 KaTeX 内嵌 SVG 注入刷新脚本而截断章节。直接打开项目根目录 index.html。构建时同时保留章节 HTML、生成 JSON 传输文件及 SHA-256/字节长度，客户端验证后才显示。reports/live-server-integrity.json 记录 30 章经 5500 端口的完整性核验。分享目录必须一并包含这些章节 JSON。
