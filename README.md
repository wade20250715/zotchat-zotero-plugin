# ZotChat - AI 论文对话插件

在 Zotero 9 右侧面板添加 AI 对话功能，与你的论文库聊天。

## 文件结构

\\\
zotchat-zotero-plugin/
├── server/                    ← Python 后端
│   ├── zotchat_server.py      ← API 服务器 (FastAPI + Gradio)
│   ├── zotchat_config.json    ← 后端配置
│   └── start_zotchat_server.bat
├── zotchat.xpi               ← Zotero 9 插件
├── bootstrap.js               ← 插件入口
├── manifest.json              ← 插件元数据
├── install.rdf                ← 兼容清单
├── chrome.manifest            ← 资源映射
├── chrome/                    ← 插件资源
│   ├── content/               ← UI 组件
│   └── locale/                ← 语言包
├── install_zotchat_xpi.ps1   ← 安装脚本
└── INSTALL.md                 ← 安装说明
\\\

## 安装

1. 启动后端: \python server/zotchat_server.py\
2. 安装插件: 将 \zotchat.xpi\ 拖入 Zotero 窗口
3. 重启 Zotero，右侧面板出现 \ZotChat\ 标签

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/status | 服务器状态 |
| GET | /api/papers | 论文列表 |
| POST | /api/chat | AI 对话 |
| POST | /api/search | 论文检索 |
| POST | /api/rebuild | 重建向量库 |

## 技术栈

- 后端: Python FastAPI + ChromaDB + DeepSeek
- 前端: Zotero 9 插件 (bootstrap.js + iframe)
- 向量库: ONNX MiniLM-L6 轻量嵌入模型
