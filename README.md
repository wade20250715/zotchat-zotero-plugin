# ZotChat — NotebookLM 风格的 Zotero 论文对话插件

在 Zotero 中直接与你的论文库对话，基于 AI 驱动的 RAG 检索。

## 功能
- 💬 与你的 Zotero 论文库 AI 对话
- 📚 自动索引 Zotero 中的 PDF 论文
- 🔍 RAG 检索 + DeepSeek 智能回答
- 🌐 支持中英文
- ⚡ 本地运行，论文数据不出本机

## 安装
1. 下载 zotchat.xpi
2. 打开 Zotero → 工具 → 附加组件
3. 将 .xpi 文件拖入 Zotero 窗口

## 启动后端
`ash
python zotchat_server.py
# 或双击 start_zotchat_server.bat
`

然后访问 http://localhost:7890 或直接在 Zotero 中使用。

## 依赖
- Python 3.10+
- Zotero 7/9
