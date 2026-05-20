# ZotChat - 安装说明

## 系统要求

- **Zotero 7.0 - 9.x** (当前: 9.0.3)
- **Python 3.10+** (当前: 3.10.6)
- **操作系统**: Windows 10/11

## 文件结构

```
D:\MyAiFactory\
├── zotchat_server.py            ← Python 后端（API 服务器）
├── zotchat_config.json          ← 后端配置文件（自动生成）
├── notebook_lm_db\              ← 向量数据库（ChromaDB，兼容旧版）
├── start_zotchat_server.bat     ← 后端启动脚本
│
└── zotchat\                     ← Zotero 插件
    ├── zotchat.xpi              ← 插件包（已构建）
    ├── manifest.json            ← 插件元数据
    ├── install.rdf              ← 兼容性清单
    ├── chrome.manifest          ← 资源映射
    ├── bootstrap.js             ← 插件入口（内嵌面板 UI）
    ├── content/
    │   ├── panel.js             ← 面板逻辑
    │   ├── panel.xhtml          ← 面板 UI（参考）
    │   └── overlay.xhtml        ← XUL 覆盖（参考）
    ├── locale/zh-CN/           ← 中文语言包
    ├── locale/en-US/            ← 英文语言包
    └── skin/                    ← 图标
```

## 安装步骤

### 1. 启动后端

**方式一: 双击脚本**
```
双击 D:\MyAiFactory\start_zotchat_server.bat
```

**方式二: 命令行**
```bash
cd D:\MyAiFactory
python zotchat_server.py
```

**可选参数:**
- `--rebuild` — 强制重建向量数据库
- `--debug`   — 调试模式

启动后:
- API 服务器:    http://127.0.0.1:7890
- Gradio Web UI: http://127.0.0.1:7891

### 2. 安装 Zotero 插件

**方式一: 拖拽安装（推荐）**
1. 打开 Zotero
2. 将 `D:\MyAiFactory\zotchat\zotchat.xpi` 拖拽到 Zotero 窗口
3. 点击"立即安装"

**方式二: 自动安装（已执行）**
插件已注册到 extensions.json，重启 Zotero 即可生效。

### 3. 使用

1. 确保后端已启动
2. 重启 Zotero
3. 右侧面板找到 **ZotChat** 标签
4. 点击打开 → 输入问题对话

## API 端点

| GET  | /api/status    | 服务器状态                      |
| GET  | /api/papers    | 论文列表（分页 + 搜索）         |
| POST | /api/search    | 论文内容检索                    |
| POST | /api/chat      | AI 对话（带引用）               |
| POST | /api/rebuild   | 重建向量库                      |
| GET  | /api/paper/:id | 单篇论文详情                    |

## 配置

`D:\MyAiFactory\zotchat_config.json`

| 配置项          | 说明                        |
|----------------|-----------------------------|
| llm_api_key    | DeepSeek / OpenAI API 密钥  |
| llm_base_url   | API 地址                   |
| llm_model      | 模型名称                   |
| server_port    | 端口（默认 7890）           |
| max_pdfs_to_index | 最大索引 PDF 数量        |
| retrieval_k    | 检索返回结果数              |

## 验证

```bash
curl http://127.0.0.1:7890/api/status
# {"success":true,"data":{"status":"running",...}}
```

## 常见问题

**Q: 端口被占用？**
A: 修改 `zotchat_config.json` 中的 `server_port`。

**Q: 向量库为空？**
A: 运行 `python zotchat_server.py --rebuild` 重建。

**Q: 插件不显示？**
A: 检查 Zotero 附加组件 → 确认 ZotChat 已启用。
