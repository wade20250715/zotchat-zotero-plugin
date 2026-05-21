# ZotChat — Zotero AI 论文对话 + 智能引用推荐

> 基于 Zotero 本地文献库的 AI 对话助手，内置 **CiteBot** 智能引用推荐引擎。

---

## ✨ 功能

### 💬 论文对话
用自然语言与你的 Zotero 论文库对话。AI 基于本地文献回答，所有数据在本地处理，不上传。

**支持：**
- 基于向量检索的本地文献问答
- 自动检测 Zotero 文献路径（PDF/数据库）
- 多轮对话上下文理解
- DeepSeek / OpenAI 兼容 API

### 🔖 CiteBot 智能引用推荐
粘贴文章 → AI 自动分析哪些句子需要引用 → 从你的论文库匹配最相关的文献。

**工作流程：**
1. **粘贴文章** — 在 CiteBot 界面粘贴你的文章正文
2. **智能分析** — AI 识别需要引用的句子 + 建议引用位置
3. **文献匹配** — 从本地论文库检索最相关的 3-5 篇文献
4. **逐条审阅** — 对每条引用建议可：✅ **接受** / ✏️ **自定义** / ❌ **跳过**
5. **一键导出** — 导出带引用标记的 Markdown 文档

### 📄 导出
- 一键导出带引用标记的 Markdown
- 引用格式：`[作者, 年份 #编号]`
- 文末自动生成参考文献列表

### 🔒 隐私安全
- **100% 本地运行** — 论文数据不出本机
- **本地向量库** — ChromaDB + ONNX MiniLM 本地嵌入，不需要联网
- **仅 LLM 查询** — 仅文章分析请求经 API 发送

---

## 🚀 快速开始

### 下载
从 [Releases](https://github.com/wade20250715/zotchat-zotero-plugin/releases) 下载 `ZotChat.exe`（推荐）或 `zotchat.xpi`（Zotero 插件）。

### 方式一：使用 ZotChat.exe（推荐）

```bash
# 设置 API Key（DeepSeek API，必填）
set ZOTCHAT_API_KEY=sk-your-key-here

# 双击运行
ZotChat.exe
```

浏览器打开 `http://127.0.0.1:7891` 即可使用。

### 方式二：Zotero 插件 + Python 后端

**1. 安装插件**
- 打开 Zotero → 工具 → 附加组件
- 将 `zotchat.xpi` 拖入 Zotero 窗口
- 重启 Zotero，右侧栏出现 **ZotChat** 标签页

**2. 启动后端**
```bash
pip install -r requirements.txt
set ZOTCHAT_API_KEY=sk-your-key-here
python zotchat_server.py
```

---

## ⚙️ 配置

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `ZOTCHAT_API_KEY` | DeepSeek / OpenAI API Key | **必填** |
| `ZOTCHAT_BASE_URL` | API 地址 | `https://api.deepseek.com/v1` |
| `ZOTCHAT_MODEL` | 模型名 | `deepseek-chat` |
| `ZOTCHAT_HOST` | API 监听地址 | `127.0.0.1` |
| `ZOTCHAT_PORT` | API 端口 | `7890` |
| `ZOTCHAT_UI_PORT` | Gradio UI 端口 | `7891` |

### 配置文件

或创建 `zotchat_config.json` 与 `ZotChat.exe` 同目录：

```json
{
  "llm_api_key": "sk-your-key-here",
  "llm_base_url": "https://api.deepseek.com/v1",
  "llm_model": "deepseek-chat",
  "server_port": 7890,
  "ui_port": 7891
}
```

---

## 📁 项目结构

```
zotchat/
├── zotchat_server.py        # 主后端（FastAPI + Gradio）
├── zotchat.xpi              # Zotero 插件包
├── requirements.txt         # Python 依赖
├── bootstrap.js             # Zotero 插件入口
├── install.rdf              # 插件元数据
├── chrome/
│   ├── content/
│   │   ├── panel.xhtml      # 侧边栏 UI
│   │   ├── overlay.xhtml    # 界面覆盖
│   │   ├── schema.json      # 插件配置架构
│   │   ├── icons/           # 插件图标
│   │   └── scripts/
│   │       └── panel.js     # 前端逻辑
│   └── locale/
│       ├── en-US/           # 英文语言包
│       └── zh-CN/           # 中文语言包
├── manifest.json            # WebExtension 清单
├── chrome.manifest          # 插件注册
├── prefs.js                 # 默认偏好
├── updates.json             # 自动更新配置
├── build_exe.py             # PyInstaller 打包脚本
├── build_xpi.py             # XPI 打包脚本
├── INSTALL.md               # 安装指南
└── README.md                # 本文件
```

---

## 🛠 技术栈

| 组件 | 技术 |
|------|------|
| **后端框架** | Python 3.10 + FastAPI |
| **UI 界面** | Gradio |
| **向量数据库** | ChromaDB |
| **本地嵌入** | ONNX MiniLM (all-MiniLM-L6-v2) |
| **LLM API** | DeepSeek / OpenAI 兼容 API |
| **PDF 解析** | PyMuPDF |
| **插件** | Zotero XUL + WebExtension |
| **打包** | PyInstaller |

---

## 📸 截图

> *（截图待补充 - 欢迎 PR 贡献截图）*

- ZotChat 对话界面
- CiteBot 引用推荐分析
- 逐条审阅卡片界面
- 导出 Markdown 示例

---

## 📄 许可证

[GNU General Public License v3](LICENSE)

---

## 🙏 致谢

- [Zotero](https://www.zotero.org/) — 开源文献管理工具
- [ChromaDB](https://www.trychroma.com/) — 开源向量数据库
- [Gradio](https://www.gradio.app/) — ML 演示框架
- [DeepSeek](https://deepseek.com/) — 大语言模型 API
