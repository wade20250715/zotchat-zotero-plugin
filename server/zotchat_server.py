#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZotChat Server
Zotero 论文对话功能的 Python 后端，在 7890 端口提供 REST API。
兼容原有的向量库，并添加 Zotero 专用端点。

启动方式:
  python zotchat_server.py          # 正常启动
  python zotchat_server.py --rebuild # 重建向量库
  python zotchat_server.py --debug   # 调试模式

依赖:
  pip install fastapi uvicorn gradio openai langchain-chroma chromadb
  pip install langchain-community pymupdf langchain-text-splitters
"""
import os
import sys
import json
import logging
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

# ── 路径配置 ──────────────────────────────────────────────────────────
ZOTERO_DATA_DIR = r"C:\Users\12462\Zotero"
ZOTERO_DB_PATH = os.path.join(ZOTERO_DATA_DIR, "zotero.sqlite")
ZOTERO_STORAGE_DIR = os.path.join(ZOTERO_DATA_DIR, "storage")

# 向量库持久化目录（与旧版兼容）
PERSIST_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "notebook_lm_db")

EXTRA_PDF_DIRS = [
    r"D:\研究计划\lunwen\My EndNote Library.Data\PDF",
    r"D:\中文版论文库"
]

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "zotchat_config.json")

# ── 日志 ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("zotchat")

# ── 配置 ─────────────────────────────────────────────────────────────
DEFAULT_CONFIG = {
    "llm_api_key": "sk-64921a4aaf174676a8229e781bc235e4",
    "llm_base_url": "https://api.deepseek.com/v1",
    "llm_model": "deepseek-v4-flash",
    "server_host": "127.0.0.1",
    "server_port": 7890,
    "zotero_db_path": ZOTERO_DB_PATH,
    "pdf_dirs": EXTRA_PDF_DIRS,
    "max_pdfs_to_index": 200,
    "chunk_size": 1500,
    "chunk_overlap": 200,
    "retrieval_k": 5
}

def load_config() -> dict:
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            for k, v in DEFAULT_CONFIG.items():
                cfg.setdefault(k, v)
            return cfg
        except Exception as e:
            logger.warning(f"配置加载失败: {e}，使用默认配置")
    else:
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_CONFIG, f, ensure_ascii=False, indent=2)
            logger.info(f"已创建默认配置文件: {CONFIG_PATH}")
        except Exception as e:
            logger.warning(f"无法写入配置文件: {e}")
    return dict(DEFAULT_CONFIG)

CONFIG = load_config()
VECTOR_DB = None
LLM_CLIENT = None


# ── Zotero 数据库 ──────────────────────────────────────────────────
def get_zotero_papers() -> List[Dict[str, Any]]:
    import sqlite3
    if not os.path.exists(ZOTERO_DB_PATH):
        logger.warning(f"Zotero 数据库不存在: {ZOTERO_DB_PATH}")
        return []
    try:
        conn = sqlite3.connect(ZOTERO_DB_PATH)
        conn.text_factory = str
        cur = conn.cursor()
        cur.execute("""
            SELECT i.itemID, i.key, it.typeName
            FROM items i
            JOIN itemTypes it ON i.itemTypeID = it.itemTypeID
            WHERE it.typeName = 'journalArticle'
            ORDER BY i.dateAdded DESC
        """)
        items = cur.fetchall()
        papers = []
        for item_id, item_key, _ in items:
            paper = {"id": item_id, "key": item_key, "title": "", "authors": [],
                     "journal": "", "date": "", "doi": "", "abstract": "",
                     "pdf_path": None, "pdf_exists": False}
            field_map = {1: "title", 2: "abstract", 6: "date", 8: "doi", 41: "journal", 85: "journal_abbr"}
            cur.execute("SELECT d.fieldID, dv.value FROM itemData d JOIN itemDataValues dv ON d.valueID=dv.valueID WHERE d.itemID=?", (item_id,))
            for field_id, value in cur.fetchall():
                fn = field_map.get(field_id)
                if fn: paper[fn] = value
            cur.execute("SELECT c.firstName, c.lastName FROM itemCreators ic JOIN creators c ON ic.creatorID=c.creatorID WHERE ic.itemID=? ORDER BY ic.orderIndex", (item_id,))
            authors = []
            for first, last in cur.fetchall():
                if first and last: authors.append(f"{first} {last}")
                elif last: authors.append(last)
                else: authors.append(first or "Unknown")
            paper["authors"] = authors
            cur.execute("SELECT a.path, a.contentType, a.linkMode FROM itemAttachments a WHERE a.parentItemID=? AND a.contentType='application/pdf' LIMIT 1", (item_id,))
            attach = cur.fetchone()
            if attach and attach[0]:
                paper["pdf_path"] = attach[0]
                paper["pdf_exists"] = os.path.exists(attach[0])
            papers.append(paper)
        conn.close()
        logger.info(f"从 Zotero 数据库读取 {len(papers)} 篇论文")
        return papers
    except Exception as e:
        logger.error(f"读取 Zotero 数据库失败: {e}")
        return []


# ── 向量数据库 ──────────────────────────────────────────────────
def build_vector_db(force: bool = False) -> Any:
    from langchain_community.document_loaders import PyMuPDFLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_chroma import Chroma
    from langchain_core.documents import Document
    import chromadb
    from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2

    raw_embed = ONNXMiniLM_L6_V2()
    class WrapEmbed:
        def embed_documents(self, texts): return raw_embed(texts)
        def embed_query(self, text): return raw_embed([text])[0]
    embed = WrapEmbed()

    chroma_db = os.path.join(PERSIST_DIR, "chroma.sqlite3")
    if not force and os.path.exists(chroma_db):
        logger.info("加载已有向量库...")
        try:
            client = chromadb.PersistentClient(path=PERSIST_DIR)
            db = Chroma(client=client, collection_name="papers", embedding_function=embed)
            count = db._collection.count()
            if count > 0:
                logger.info(f"向量库中有 {count} 个块")
                return db
            else:
                logger.warning("向量库为空，重新构建...")
        except Exception as e:
            logger.warning(f"加载向量库失败: {e}，重新构建...")

    pdf_paths = []
    papers = get_zotero_papers()
    for p in papers:
        if p["pdf_path"] and os.path.exists(p["pdf_path"]):
            pdf_paths.append(p["pdf_path"])
    for d in EXTRA_PDF_DIRS:
        if os.path.exists(d):
            for root, _, files in os.walk(d):
                for f in files:
                    if f.lower().endswith('.pdf'):
                        pdf_paths.append(os.path.join(root, f))
    if os.path.exists(ZOTERO_STORAGE_DIR):
        for root, _, files in os.walk(ZOTERO_STORAGE_DIR):
            for f in files:
                if f.lower().endswith('.pdf'):
                    pdf_paths.append(os.path.join(root, f))
    pdf_paths = sorted(set(pdf_paths))
    logger.info(f"找到 {len(pdf_paths)} 篇 PDF")
    max_pdfs = CONFIG.get("max_pdfs_to_index", 200)
    if len(pdf_paths) > max_pdfs:
        logger.info(f"限制处理前 {max_pdfs} 篇")
        pdf_paths = pdf_paths[:max_pdfs]

    docs = []
    for i, pdf_path in enumerate(pdf_paths):
        try:
            filename = os.path.basename(pdf_path)
            logger.info(f"  [{i+1}/{len(pdf_paths)}] {filename}")
            pages = PyMuPDFLoader(pdf_path).load()
            text = "\n\n".join(p.page_content for p in pages)
            if len(text.strip()) > 50:
                docs.append(Document(page_content=text, metadata={"source": filename, "path": pdf_path}))
        except Exception as e:
            logger.debug(f"  跳过 {pdf_path}: {e}")
    logger.info(f"成功读取: {len(docs)} 篇")
    if not docs:
        logger.warning("没有成功读取任何 PDF")
        client = chromadb.PersistentClient(path=PERSIST_DIR)
        return Chroma(client=client, collection_name="papers", embedding_function=embed)
    chunks = RecursiveCharacterTextSplitter(chunk_size=CONFIG["chunk_size"], chunk_overlap=CONFIG["chunk_overlap"]).split_documents(docs)
    logger.info(f"切分: {len(chunks)} 块")
    logger.info("向量化 (ONNX 轻量模型)...")
    client = chromadb.PersistentClient(path=PERSIST_DIR)
    db = Chroma.from_documents(documents=chunks, embedding=embed, client=client, collection_name="papers")
    logger.info("向量库已保存")
    return db


# ── LLM 客户端 ──────────────────────────────────────────────────
def get_llm_client():
    global LLM_CLIENT
    if LLM_CLIENT is None:
        from openai import OpenAI
        LLM_CLIENT = OpenAI(api_key=CONFIG["llm_api_key"], base_url=CONFIG["llm_base_url"])
    return LLM_CLIENT


# ── 状态 ─────────────────────────────────────────────────────────────
class ServerState:
    def __init__(self):
        self.db = None
        self.papers_cache = []
        self.papers_cache_time = 0
    def get_retriever(self):
        if self.db is None:
            raise RuntimeError("向量库未初始化")
        return self.db.as_retriever(search_kwargs={"k": CONFIG["retrieval_k"]})
    def get_papers(self, refresh=False):
        import time
        now = time.time()
        if refresh or not self.papers_cache or (now - self.papers_cache_time > 60):
            self.papers_cache = get_zotero_papers()
            self.papers_cache_time = now
        return self.papers_cache

state = ServerState()


# ── 响应格式 ──────────────────────────────────────────────────────
def api_response(data=None, error=None, success=True):
    resp = {"success": success}
    if data is not None: resp["data"] = data
    if error is not None: resp["error"] = error
    return resp


# ── FastAPI ──────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app):
    global VECTOR_DB
    rebuild = "--rebuild" in sys.argv
    logger.info("初始化向量库...")
    try:
        state.db = build_vector_db(force=rebuild)
        VECTOR_DB = state.db
        logger.info("向量库就绪")
    except Exception as e:
        logger.error(f"向量库初始化失败: {e}")
    yield
    logger.info("服务器关闭")

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="ZotChat API", description="Zotero 论文对话功能后端 API", version="1.0.0", lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

class SearchRequest(BaseModel):
    query: str

class ChatRequest(BaseModel):
    messages: List[Dict[str, str]]


# ── API 端点 ──────────────────────────────────────────────────────────

@app.get("/api/status")
async def api_status():
    if state.db is None:
        return api_response(data={"status": "initializing", "message": "向量库正在初始化"})
    try:
        count = state.db._collection.count()
    except Exception:
        count = 0
    papers = state.get_papers()
    return api_response(data={
        "status": "running", "version": "1.0.0",
        "vector_db_chunks": count,
        "zotero_papers_total": len(papers),
        "zotero_papers_with_pdf": sum(1 for p in papers if p["pdf_exists"]),
        "config": {"llm_model": CONFIG["llm_model"], "max_pdfs_indexed": CONFIG["max_pdfs_to_index"], "retrieval_k": CONFIG["retrieval_k"]}
    })

@app.get("/api/papers")
async def api_papers(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), search: Optional[str] = None, refresh: bool = False):
    papers = state.get_papers(refresh=refresh)
    if search:
        sl = search.lower()
        papers = [p for p in papers if sl in p["title"].lower() or any(sl in a.lower() for a in p["authors"])]
    total = len(papers)
    start = (page - 1) * page_size
    page_papers = papers[start:start + page_size]
    result = []
    for p in page_papers:
        result.append({"id": p["id"], "key": p["key"], "title": p["title"], "authors": p["authors"][:5],
                        "journal": p["journal"], "date": p["date"], "doi": p["doi"], "has_pdf": p["pdf_exists"]})
    return api_response(data={"papers": result, "total": total, "page": page, "page_size": page_size, "total_pages": (total + page_size - 1) // page_size})

@app.post("/api/search")
async def api_search(req: SearchRequest):
    if state.db is None:
        raise HTTPException(status_code=503, detail="向量库未初始化")
    try:
        docs = state.get_retriever().invoke(req.query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"检索失败: {e}")
    results = []
    for doc in docs:
        results.append({"content": doc.page_content[:800], "source": doc.metadata.get("source", "Unknown"),
                        "path": doc.metadata.get("path", ""), "relevance_score": 1.0})
    return api_response(data={"query": req.query, "results": results, "result_count": len(results), "source_count": len(set(r["source"] for r in results))})

@app.post("/api/chat")
async def api_chat(req: ChatRequest):
    if state.db is None:
        raise HTTPException(status_code=503, detail="向量库未初始化")
    user_msg = ""
    for msg in reversed(req.messages):
        if msg.get("role") == "user":
            user_msg = msg["content"]; break
    if not user_msg:
        raise HTTPException(status_code=400, detail="未找到用户消息")
    try:
        docs = state.get_retriever().invoke(user_msg)
        context_parts = []; sources = []
        for i, doc in enumerate(docs):
            content = doc.page_content[:2000]
            source = doc.metadata.get("source", f"来源 {i+1}")
            context_parts.append(f"[来源 {i+1}] {content}")
            sources.append({"index": i+1, "title": source, "path": doc.metadata.get("path", "")})
        context = "\n\n---\n\n".join(context_parts)
        client = get_llm_client()
        chat_msgs = [
            {"role": "system", "content": "你是一个科研助手，基于以下论文内容回答问题。请用中文回答。回答中标注引用来源，如 [来源 1]、[来源 2]。如果内容不足以回答，如实说不知道。回答要具体、专业。"},
            {"role": "user", "content": f"# 参考论文\n{context}\n\n# 问题\n{user_msg}"}
        ]
        for msg in req.messages[:-1]:
            if msg.get("role") in ("user", "assistant"):
                chat_msgs.append({"role": msg["role"], "content": msg["content"]})
        response = client.chat.completions.create(model=CONFIG["llm_model"], messages=chat_msgs, temperature=0.3, max_tokens=2048)
        reply = response.choices[0].message.content
        return api_response(data={"reply": reply, "sources": sources})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"对话错误: {e}")
        raise HTTPException(status_code=500, detail=f"对话生成失败: {e}")

@app.post("/api/rebuild")
async def api_rebuild():
    try:
        logger.info("开始重建向量库...")
        state.db = build_vector_db(force=True)
        count = state.db._collection.count()
        logger.info(f"重建完成，共 {count} 个块")
        return api_response(data={"message": "向量库重建完成", "chunks": count})
    except Exception as e:
        logger.error(f"重建失败: {e}")
        raise HTTPException(status_code=500, detail=f"重建失败: {e}")

@app.get("/api/paper/{paper_id}")
async def api_paper_detail(paper_id: int):
    papers = state.get_papers()
    for p in papers:
        if p["id"] == paper_id:
            pdf_preview = ""
            if p["pdf_path"] and os.path.exists(p["pdf_path"]):
                try:
                    from langchain_community.document_loaders import PyMuPDFLoader
                    pages = PyMuPDFLoader(p["pdf_path"]).load()
                    pdf_preview = "\n\n".join(page.page_content[:500] for page in pages[:4])[:3000]
                except Exception as e:
                    pdf_preview = f"(读取失败: {e})"
            return api_response(data={
                "id": p["id"], "key": p["key"], "title": p["title"], "authors": p["authors"],
                "journal": p["journal"], "date": p["date"], "doi": p["doi"], "abstract": p["abstract"],
                "pdf_path": p["pdf_path"], "pdf_exists": p["pdf_exists"], "pdf_preview": pdf_preview
            })
    raise HTTPException(status_code=404, detail=f"论文 {paper_id} 未找到")


# ── Gradio UI ────────────────────────────────────────────────────
def create_gradio_ui():
    import gradio as gr
    def respond(msg, history):
        if state.db is None:
            return "⚠️ 向量库未初始化，请等待服务就绪。"
        try:
            import httpx
            resp = httpx.post(f"http://{CONFIG['server_host']}:{CONFIG['server_port']}/api/chat",
                              json={"messages": [{"role": "user", "content": msg}]}, timeout=60)
            data = resp.json()
            if data.get("success"):
                reply = data["data"]["reply"]
                sources = data["data"]["sources"]
                if sources:
                    refs = "  \n\n**📚 引用来源:**"
                    for s in sources:
                        refs += f"  \n[{s['index']}] {s['title']}"
                    reply += refs
                return reply
            else:
                return f"❌ 错误: {data.get('error', '未知错误')}"
        except Exception as e:
            return f"❌ 请求失败: {e}"
    with gr.Blocks(title="💬 ZotChat", theme="soft", css="#chatbot {height: 600px}") as demo:
        gr.Markdown("# 💬 ZotChat\n与你的论文库对话，检索论文内容，获取 AI 回答。")
        gr.ChatInterface(respond, type="messages", title="跟你的论文聊天",
                         chatbot=gr.Chatbot(height=500, label="对话", type="messages"),
                         textbox=gr.Textbox(placeholder="输入问题，例如：有哪些关于纳米给药系统的研究？", scale=7))
    return demo


# ── 启动入口 ──────────────────────────────────────────────────
def main():
    import uvicorn, threading
    debug = "--debug" in sys.argv
    if debug:
        logger.setLevel(logging.DEBUG)
    host = CONFIG["server_host"]
    port = CONFIG["server_port"]
    rebuild = "--rebuild" in sys.argv
    logger.info("初始化向量库...")
    try:
        state.db = build_vector_db(force=rebuild)
        logger.info("向量库就绪")
    except Exception as e:
        logger.error(f"向量库初始化失败: {e}")

    def run_gradio():
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        demo = create_gradio_ui()
        logger.info(f"Gradio UI 启动: http://{host}:{port}/?ui=true")
        demo.launch(server_name=host, server_port=port + 1, share=False, quiet=True)

    gradio_thread = threading.Thread(target=run_gradio, daemon=True)
    gradio_thread.start()

    logger.info(f"ZotChat API 服务器启动: http://{host}:{port}")
    logger.info(f"Gradio Web UI: http://{host}:{port + 1}")
    logger.info(f"Zotero 插件连接: http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info" if not debug else "debug")

if __name__ == "__main__":
    main()
