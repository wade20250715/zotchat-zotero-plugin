#!/usr/bin/env python3
"""
ZotChat Server — Zotero 论文对话后端
====================================
配置方式（三选一）：
  1. 环境变量:  set ZOTCHAT_API_KEY=sk-xxx
  2. 配置文件:  同目录 zotchat_config.json
  3. 交互输入:  首次运行自动询问

完整代码已从仓库移除配置文件，
请到 https://platform.deepseek.com 获取 API Key。
"""
import os, sys, json, logging, shutil
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [ZotChat] %(message)s")
log = logging.getLogger("zotchat")

# ── 首次运行配置引导 ──
CONFIG_FILE = Path(__file__).parent / "zotchat_config.json"

if not CONFIG_FILE.exists() and not os.environ.get("ZOTCHAT_API_KEY"):
    print("="*50)
    print("🔑 ZotChat 首次启动 - 配置 API Key")
    print("="*50)
    api_key = input("请输入你的 DeepSeek API Key (sk-...): ").strip()
    if not api_key:
        print("❌ API Key 不能为空")
        sys.exit(1)
    config = {
        "llm_api_key": api_key,
        "llm_base_url": input(f"API 地址 [https://api.deepseek.com/v1]: ").strip() or "https://api.deepseek.com/v1",
        "llm_model": input(f"模型 [deepseek-chat]: ").strip() or "deepseek-chat",
        "server_port": int(input(f"端口 [7890]: ").strip() or "7890"),
        "max_pdfs_to_index": 200,
        "chunk_size": 1500,
        "chunk_overlap": 200,
        "retrieval_k": 5
    }
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    print(f"✅ 配置已保存至 {CONFIG_FILE}")
    CONFIG_FILE.chmod(0o600)  # 仅当前用户可读（Unix）

# ── 加载配置 ──
CONFIG = json.loads(CONFIG_FILE.read_text(encoding="utf-8")) if CONFIG_FILE.exists() else {}
for k in ["llm_api_key", "llm_base_url", "llm_model", "server_port"]:
    env_val = os.environ.get(f"ZOTCHAT_{k.upper()}")
    if env_val:
        CONFIG[k] = int(env_val) if k == "server_port" else env_val

if not CONFIG.get("llm_api_key"):
    log.error("❌ 未配置 API Key！请设置环境变量 ZOTCHAT_API_KEY 或运行本脚本配置")
    sys.exit(1)

log.info(f"✅ ZotChat 就绪 | {CONFIG.get('llm_model','?')} | :{CONFIG.get('server_port',7890)}")

# ── 实际 API 逻辑见完整版 ──
# 完整源代码: https://github.com/wade20250715/zotchat-zotero-plugin
print(f"\n🌐 ZotChat API: http://127.0.0.1:{CONFIG.get('server_port',7890)}")
print("📖 安装 Zotero 插件后，在 Zotero 右侧面板使用")
