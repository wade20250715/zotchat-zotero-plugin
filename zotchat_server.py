#!/usr/bin/env python3
"""
ZotChat Server — Zotero 论文对话后端
====================================
配置（三选一）：
  1. 环境变量:  set ZOTCHAT_API_KEY=sk-xxx ; python zotchat_server.py
  2. 配置文件:  同目录创建 zotchat_config.json
  3. 交互配置:  首次运行自动引导

安装依赖: pip install fastapi uvicorn gradio openai langchain-chroma chromadb langchain-community pymupdf
"""
import os, sys, json, logging, sqlite3, threading, time
from pathlib import Path
from typing import List, Dict, Optional, Any
from contextlib import asynccontextmanager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [ZotChat] %(message)s")
log = logging.getLogger("zotchat")

# ── 配置 ──
CONFIG_FILE = Path(__file__).parent / "zotchat_config.json"

def load_config():
    cfg = {}
    # 1) 配置文件
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg.update(json.load(f))
        except Exception as e:
            log.warning(f"配置文件读取失败: {e}")
    # 2) 环境变量（优先级更高）
    env_map = {
        "ZOTCHAT_API_KEY": "llm_api_key",
        "ZOTCHAT_BASE_URL": "llm_base_url",
        "ZOTCHAT_MODEL": "llm_model",
        "ZOTCHAT_HOST": "server_host",
        "ZOTCHAT_PORT": "server_port",
    }
    for env_key, cfg_key in env_map.items():
        val = os.environ.get(env_key)
        if val is not None:
            cfg[cfg_key] = int(val) if cfg_key == "server_port" else val
    # 3) 默认值
    defaults = {
        "llm_api_key": "",
        "llm_base_url": "https://api.deepseek.com/v1",
        "llm_model": "deepseek-chat",
        "server_host": "127.0.0.1",
        "server_port": 7890,
        "max_pdfs_to_index": 200,
        "chunk_size": 1500,
        "chunk_overlap": 200,
        "retrieval_k": 5,
    }
    for k, v in defaults.items():
        cfg.setdefault(k, v)
    return cfg

CONFIG = load_config()

# ── 首次运行配置引导 ──
if not CONFIG["llm_api_key"]:
    print("\n" + "="*50)
    print("🔑 ZotChat - 首次启动，请输入 API Key")
    print("="*50)
    print("(如果没有，请到 https://platform.deepseek.com 注册获取)")
    api_key = input("DeepSeek API Key: ").strip()
    if not api_key:
        print("❌ API Key 不能为空，已退出")
        sys.exit(1)
    CONFIG["llm_api_key"] = api_key
    base_url = input(f"API 地址 [{CONFIG['llm_base_url']}]: ").strip()
    if base_url: CONFIG["llm_base_url"] = base_url
    port = input(f"端口 [{CONFIG['server_port']}]: ").strip()
    if port: CONFIG["server_port"] = int(port)
    # 保存配置
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(CONFIG, f, ensure_ascii=False, indent=2)
    # 设置权限（Unix 下仅用户可读）
    try: CONFIG_FILE.chmod(0o600)
    except: pass
    print(f"✅ 配置已保存至 {CONFIG_FILE}，请勿分享此文件！\n")

log.info(f"✅ ZotChat v1.0.0 | {CONFIG['llm_model']} | :{CONFIG['server_port']}")

# ── Zotero 数据库读取 ──
def find_zotero_db():
    """自动寻找 Zotero 数据库"""
    candidates = []
    # Windows
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            candidates.extend(Path(appdata).glob("Zotero/Zotero/Profiles/*.default/zotero.sqlite"))
            candidates.extend(Path(appdata).glob("Zotero/Zotero/zotero.sqlite"))
        # 用户目录
        home = str(Path.home())
        candidates.extend(Path(home).glob("Zotero/zotero.sqlite"))
    # macOS
    elif sys.platform == "darwin":
        home = str(Path.home())
        candidates.extend(Path(home).glob("Library/Application Support/Zotero/zotero.sqlite"))
    # Linux
    else:
        home = str(Path.home())
        candidates.extend(Path(home).glob(".zotero/zotero.sqlite"))
        candidates.extend(Path(home).glob("Zotero/zotero.sqlite"))
    for c in candidates:
        if c.exists():
            log.info(f"找到 Zotero 数据库: {c}")
            return str(c)
    db_path = CONFIG.get("zotero_db_path", "")
    if db_path and os.path.exists(db_path):
        return db_path
    return None

def get_zotero_papers():
    db_path = find_zotero_db()
    if not db_path:
        return []
    try:
        conn = sqlite3.connect(db_path)
        conn.text_factory = str
        cur = conn.cursor()
        # 获取论文
        cur.execute("SELECT itemID, key FROM items WHERE itemTypeID IN (SELECT itemTypeID FROM itemTypes WHERE typeName='journalArticle') ORDER BY dateAdded DESC")
        items = cur.fetchall()
        papers = []
        for item_id, item_key in items:
            p = {"id": item_id, "key": item_key, "title": "", "authors": [], "journal": "", "date": "", "doi": "", "abstract": "", "has_pdf": False}
            # 获取字段
            cur.execute("SELECT f.fieldName, dv.value FROM itemData d JOIN itemDataValues dv ON d.valueID=dv.valueID JOIN fields f ON d.fieldID=f.fieldID WHERE d.itemID=?", (item_id,))
            for fname, val in cur.fetchall():
                if fname in p: p[fname] = val
            # 获取作者
            cur.execute("SELECT c.firstName, c.lastName FROM itemCreators ic JOIN creators c ON ic.creatorID=c.creatorID WHERE ic.itemID=? ORDER BY ic.orderIndex", (item_id,))
            authors = []
            for first, last in cur.fetchall():
                name = f"{first} {last}".strip()
                if name: authors.append(name)
            p["authors"] = authors
            # 检查 PDF
            cur.execute("SELECT 1 FROM itemAttachments WHERE parentItemID=? AND contentType='application/pdf' AND path IS NOT NULL LIMIT 1", (item_id,))
            p["has_pdf"] = cur.fetchone() is not None
            papers.append(p)
        conn.close()
        log.info(f"Zotero: {len(papers)} 篇论文")
        return papers
    except Exception as e:
        log.warning(f"读取 Zotero 数据库失败: {e}")
        return []

# ── FastAPI + Gradio ──
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

class ChatRequest(BaseModel):
    messages: List[Dict[str, str]]

state = type("State", (), {"db": None, "papers": [], "llm": None})()

@asynccontextmanager
async def lifespan(app):
    yield

app = FastAPI(title="ZotChat", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/api/status")
async def api_status():
    return {"success": True, "data": {
        "status": "running",
        "version": "1.0.0",
        "zotero_papers_total": len(state.papers),
        "config": {"model": CONFIG["llm_model"]}
    }}

@app.get("/api/papers")
async def api_papers(page_size: int = Query(50, le=200)):
    return {"success": True, "data": {"papers": state.papers[:page_size], "total": len(state.papers)}}

@app.post("/api/chat")
async def api_chat(req: ChatRequest):
    # 简单 LLM 调用
    from openai import OpenAI
    client = OpenAI(api_key=CONFIG["llm_api_key"], base_url=CONFIG["llm_base_url"])
    resp = client.chat.completions.create(
        model=CONFIG["llm_model"],
        messages=req.messages,
        temperature=0.3
    )
    reply = resp.choices[0].message.content
    return {"success": True, "data": {"reply": reply, "sources": []}}

# ── Gradio UI ──
def run_gradio():
    import gradio as gr
    def respond(msg, history):
        from openai import OpenAI
        client = OpenAI(api_key=CONFIG["llm_api_key"], base_url=CONFIG["llm_base_url"])
        resp = client.chat.completions.create(
            model=CONFIG["llm_model"],
            messages=[{"role": "user", "content": msg}], temperature=0.3)
        return resp.choices[0].message.content
    ui = gr.ChatInterface(respond, title="ZotChat")
    ui.launch(server_name=CONFIG["server_host"], server_port=CONFIG["server_port"]+1, share=False, quiet=True)

# ── 入口 ──
if __name__ == "__main__":
    rebuild = "--rebuild" in sys.argv
    # 加载论文
    state.papers = get_zotero_papers()
    # 启动 Gradio
    threading.Thread(target=run_gradio, daemon=True).start()
    print(f"\n🌐 ZotChat API: http://{CONFIG['server_host']}:{CONFIG['server_port']}")
    print(f"🌐 Gradio UI:  http://{CONFIG['server_host']}:{CONFIG['server_port']+1}")
    print("📖 安装插件后，在 Zotero 右侧面板使用\n")
    uvicorn.run(app, host=CONFIG["server_host"], port=CONFIG["server_port"], log_level="info")
