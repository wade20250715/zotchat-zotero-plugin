# ZotChat — NotebookLM 风格的 Zotero 论文对话插件

在 Zotero 中直接与你的论文库 AI 对话。

## 📦 下载

从 Releases 下载 `zotchat.xpi`。

## 🔧 安装

### 1. 安装插件
- 打开 Zotero → 工具 → 附加组件
- 将 `zotchat.xpi` 拖入 Zotero 窗口
- 重启 Zotero，右侧栏出现 **ZotChat** 标签页

### 2. 启动后端服务

**方式一：一键脚本（推荐）**
```bash
pip install fastapi uvicorn gradio openai langchain-chroma chromadb langchain-community pymupdf
python server_template.py
# 首次运行会引导输入 API Key
```

**方式二：环境变量**
```bash
set ZOTCHAT_API_KEY=sk-your-key-here
python server_template.py
```

**方式三：配置文件**
创建 `zotchat_config.json`：
```json
{
  "llm_api_key": "sk-your-key-here",
  "llm_base_url": "https://api.deepseek.com/v1",
  "llm_model": "deepseek-chat",
  "server_port": 7890
}
```

### 3. 使用
- 后端运行后，打开 Zotero
- 点击右侧 **ZotChat** 标签
- 在聊天框输入论文相关的问题

## ⚙️ 配置

| 环境变量 | 说明 | 默认值 |
|---------|------|--------|
| `ZOTCHAT_API_KEY` | DeepSeek API Key | **必填** |
| `ZOTCHAT_BASE_URL` | API 地址 | `https://api.deepseek.com/v1` |
| `ZOTCHAT_MODEL` | 模型名 | `deepseek-chat` |
| `ZOTCHAT_HOST` | 监听地址 | `127.0.0.1` |
| `ZOTCHAT_PORT` | 端口 | `7890` |

## 🔒 安全

- **API Key 仅存本地**，不联网上传
- 论文数据不出本机（本地向量库 + 本地检索）
- 仅 LLM 查询经 API 发送

## 🏗 项目结构

```
zotchat/
├── zotchat.xpi           # Zotero 插件包
├── server_template.py    # 后端服务模板
├── README.md
└── chrome/               # 插件资源
    ├── content/          # UI 文件
    └── locale/           # 多语言
```

## 📄 开源协议

MIT
