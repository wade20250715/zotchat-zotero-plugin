#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZotChat Server — Zotero 论文对话后端（完整 RAG 版）
===================================================
自动构建向量库，支持全文检索和 AI 问答。

配置方式（三选一，优先级从高到低）：
  1. 环境变量: ZOTCHAT_API_KEY, ZOTCHAT_BASE_URL, ZOTCHAT_MODEL 等
  2. 配置文件: 同目录 zotchat_config.json（已在 .gitignore 中）
  3. 首次交互引导

启动:
  python zotchat_server.py               # 正常启动
  python zotchat_server.py --rebuild      # 重建向量库
  python zotchat_server.py --debug        # 调试日志

依赖:
  pip install fastapi uvicorn gradio openai langchain-chroma chromadb
  pip install langchain-community pymupdf langchain-text-splitters httpx
"""
import os, sys, json, logging, sqlite3, threading, time
from pathlib import Path
from typing import List, Dict, Optional, Any
from contextlib import asynccontextmanager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [ZotChat] %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
log = logging.getLogger("zotchat")

# ── 配置 ─────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent.resolve()
CONFIG_FILE = SCRIPT_DIR / "zotchat_config.json"

def load_config() -> dict:
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
        "persist_dir": str(SCRIPT_DIR / "notebook_lm_db"),
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
    print("\n" + "=" * 50)
    print("🔑 ZotChat - 首次启动，请输入 API Key")
    print("=" * 50)
    print("(如果没有，请到 https://platform.deepseek.com 注册获取)")
    api_key = input("DeepSeek API Key: ").strip()
    if not api_key:
        print("❌ API Key 不能为空，已退出")
        sys.exit(1)
    CONFIG["llm_api_key"] = api_key
    base_url = input(f"API 地址 [{CONFIG['llm_base_url']}]: ").strip()
    if base_url:
        CONFIG["llm_base_url"] = base_url
    port = input(f"端口 [{CONFIG['server_port']}]: ").strip()
    if port:
        CONFIG["server_port"] = int(port)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(CONFIG, f, ensure_ascii=False, indent=2)
    try:
        CONFIG_FILE.chmod(0o600)
    except Exception:
        pass
    print(f"✅ 配置已保存至 {CONFIG_FILE}，请勿分享此文件！\n")

log.info(f"✅ ZotChat 完整 RAG 版 | 模型: {CONFIG['llm_model']} | 端口: {CONFIG['server_port']}")

# ── LLM 客户端 ──────────────────────────────────────────────────────
_llm_client = None

def get_llm_client():
    global _llm_client
    if _llm_client is None:
        from openai import OpenAI
        _llm_client = OpenAI(
            api_key=CONFIG["llm_api_key"],
            base_url=CONFIG["llm_base_url"]
        )
    return _llm_client


# ── Zotero 数据库自动检测 ──────────────────────────────────────────

def find_zotero_db() -> Optional[str]:
    """跨平台自动寻找 Zotero SQLite 数据库"""
    candidates = []

    # Windows
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            candidates.extend(sorted(Path(appdata).glob("Zotero/Zotero/Profiles/*.default/zotero.sqlite")))
            candidates.extend(sorted(Path(appdata).glob("Zotero/Zotero/zotero.sqlite")))
        candidates.append(Path.home() / "Zotero" / "zotero.sqlite")

    # macOS
    elif sys.platform == "darwin":
        candidates.append(Path.home() / "Library/Application Support/Zotero/zotero.sqlite")

    # Linux
    else:
        candidates.extend([
            Path.home() / ".zotero" / "zotero.sqlite",
            Path.home() / "Zotero" / "zotero.sqlite",
        ])

    for c in candidates:
        if c.exists():
            log.info(f"✅ 找到 Zotero 数据库: {c}")
            return str(c)

    log.warning("⚠️ 未自动找到 Zotero 数据库。可设置 zotchat_config.json 中的 zotero_db_path")
    cfg_path = CONFIG.get("zotero_db_path", "")
    if cfg_path and os.path.exists(cfg_path):
        return cfg_path
    return None


def find_zotero_storage() -> Optional[str]:
    """跨平台自动寻找 Zotero storage 目录"""
    candidates = []

    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            candidates.extend(sorted(Path(appdata).glob("Zotero/Zotero/Profiles/*.default/storage")))
            candidates.extend(sorted(Path(appdata).glob("Zotero/Zotero/storage")))
        candidates.append(Path.home() / "Zotero" / "storage")

    elif sys.platform == "darwin":
        candidates.append(Path.home() / "Library/Application Support/Zotero/storage")

    else:
        candidates.extend([
            Path.home() / ".zotero" / "storage",
            Path.home() / "Zotero" / "storage",
        ])

    for c in candidates:
        if c.exists() and c.is_dir():
            log.info(f"✅ 找到 Zotero storage: {c}")
            return str(c)

    cfg_path = CONFIG.get("zotero_storage_path", "")
    if cfg_path and os.path.isdir(cfg_path):
        return cfg_path
    return None


# ── Zotero 数据库读取 ──────────────────────────────────────────────

def get_zotero_papers() -> List[Dict[str, Any]]:
    """从 Zotero SQLite 数据库中读取论文元信息"""
    db_path = find_zotero_db()
    if not db_path:
        log.warning("未找到 Zotero 数据库，返回空列表")
        return []
    try:
        conn = sqlite3.connect(db_path, timeout=5.0)
        conn.text_factory = str
        cur = conn.cursor()
        cur.execute("PRAGMA busy_timeout = 5000")

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
            paper = {
                "id": item_id, "key": item_key, "title": "", "authors": [],
                "journal": "", "date": "", "doi": "", "abstract": "",
                "pdf_path": None, "pdf_exists": False
            }
            field_map = {
                1: "title", 2: "abstract", 4: "title",
                5: "abstract", 6: "date", 8: "doi",
                10: "journal", 12: "journal", 41: "journal",
                # 实际 fieldID 可能因版本不同而变化，所以通过 fieldName 查
            }
            cur.execute("""
                SELECT f.fieldName, dv.value
                FROM itemData d
                JOIN itemDataValues dv ON d.valueID = dv.valueID
                JOIN fields f ON d.fieldID = f.fieldID
                WHERE d.itemID = ?
            """, (item_id,))
            for fname, val in cur.fetchall():
                fname_lower = fname.lower()
                if fname_lower == "title":
                    if not paper["title"]: paper["title"] = val
                elif fname_lower == "abstract":
                    if not paper["abstract"]: paper["abstract"] = val
                elif fname_lower == "date":
                    if not paper["date"]: paper["date"] = val
                elif fname_lower == "doi":
                    if not paper["doi"]: paper["doi"] = val
                elif fname_lower in ("publicationtitle", "journal", "booktitle"):
                    if not paper["journal"]: paper["journal"] = val

            # 作者
            cur.execute("""
                SELECT c.firstName, c.lastName
                FROM itemCreators ic
                JOIN creators c ON ic.creatorID = c.creatorID
                WHERE ic.itemID = ?
                ORDER BY ic.orderIndex
            """, (item_id,))
            for first, last in cur.fetchall():
                name = f"{first} {last}".strip()
                if name:
                    paper["authors"].append(name)

            # 检查附件 PDF
            cur.execute("""
                SELECT a.path, a.contentType, a.linkMode
                FROM itemAttachments a
                WHERE a.parentItemID = ? AND a.contentType = 'application/pdf'
                LIMIT 1
            """, (item_id,))
            attach = cur.fetchone()
            if attach and attach[0]:
                raw_path = attach[0]
                # 处理相对路径（Zotero 可能存相对路径）
                if not os.path.isabs(raw_path):
                    storage_dir = find_zotero_storage()
                    if storage_dir:
                        raw_path = os.path.join(os.path.dirname(storage_dir), raw_path)
                paper["pdf_path"] = raw_path
                paper["pdf_exists"] = os.path.exists(raw_path)

            papers.append(paper)

        conn.close()
        log.info(f"📖 从 Zotero 读取 {len(papers)} 篇论文")
        return papers
    except Exception as e:
        log.warning(f"读取 Zotero 数据库失败: {e}")
        return []


def find_all_pdf_paths() -> List[str]:
    """汇总所有 PDF 路径：Zotero storage + 附件"""
    pdf_set = set()

    # 1) 从 Zotero 数据库中的附件
    papers = get_zotero_papers()
    for p in papers:
        if p["pdf_path"] and os.path.exists(p["pdf_path"]):
            pdf_set.add(p["pdf_path"])

    # 2) 直接从 Zotero storage 目录扫描
    storage_dir = find_zotero_storage()
    if storage_dir and os.path.isdir(storage_dir):
        for root, _, files in os.walk(storage_dir):
            for f in files:
                if f.lower().endswith(".pdf"):
                    pdf_set.add(os.path.join(root, f))

    # 3) 配置中额外的 PDF 目录
    extra_dirs = CONFIG.get("pdf_dirs", [])
    if isinstance(extra_dirs, list):
        for d in extra_dirs:
            if os.path.isdir(d):
                for root, _, files in os.walk(d):
                    for f in files:
                        if f.lower().endswith(".pdf"):
                            pdf_set.add(os.path.join(root, f))

    pdf_list = sorted(pdf_set)
    log.info(f"📄 共找到 {len(pdf_list)} 篇 PDF")
    return pdf_list


# ── 向量数据库 ──────────────────────────────────────────────────────

def build_vector_db(force: bool = False):
    """构建或加载 ChromaDB 向量库（ONNX MiniLM L6 v2 本地嵌入）"""
    from langchain_community.document_loaders import PyMuPDFLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_chroma import Chroma
    from langchain_core.documents import Document
    import chromadb
    from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2

    # ONNX 本地嵌入
    raw_embed = ONNXMiniLM_L6_V2()

    class WrapEmbed:
        def embed_documents(self, texts):
            return raw_embed(texts)

        def embed_query(self, text):
            return raw_embed([text])[0]

    embed = WrapEmbed()

    persist_dir = CONFIG.get("persist_dir", str(SCRIPT_DIR / "notebook_lm_db"))
    chroma_file = os.path.join(persist_dir, "chroma.sqlite3")

    # 已有库且不强制重建
    if not force and os.path.exists(chroma_file):
        log.info("📦 加载已有向量库...")
        try:
            client = chromadb.PersistentClient(path=persist_dir)
            db = Chroma(client=client, collection_name="papers", embedding_function=embed)
            count = db._collection.count()
            if count > 0:
                log.info(f"✅ 向量库已加载，{count} 个向量块")
                return db
            else:
                log.warning("向量库为空，重新构建...")
        except Exception as e:
            log.warning(f"加载向量库失败: {e}，重新构建...")

    # 收集 PDF
    pdf_paths = find_all_pdf_paths()
    max_pdfs = CONFIG.get("max_pdfs_to_index", 200)
    pdf_paths = pdf_paths[:max_pdfs]

    if not pdf_paths:
        log.warning("⚠️ 未找到任何 PDF 文件")
        import chromadb
        client = chromadb.PersistentClient(path=persist_dir)
        return Chroma(client=client, collection_name="papers", embedding_function=embed)

    # 读取 PDF
    log.info(f"📖 正在读取 {len(pdf_paths)} 篇 PDF...")
    docs = []
    for i, pdf_path in enumerate(pdf_paths):
        try:
            filename = os.path.basename(pdf_path)
            if (i + 1) % 10 == 0:
                log.info(f"  [{i+1}/{len(pdf_paths)}] ...")
            pages = PyMuPDFLoader(pdf_path).load()
            text = "\n\n".join(p.page_content for p in pages)
            if len(text.strip()) > 50:
                docs.append(Document(
                    page_content=text,
                    metadata={"source": filename, "path": pdf_path}
                ))
        except Exception as e:
            log.debug(f"  跳过 {os.path.basename(pdf_path)}: {e}")

    log.info(f"✅ 成功读取: {len(docs)} 篇")

    if not docs:
        log.warning("⚠️ 没有成功读取任何 PDF，返回空向量库")
        import chromadb
        client = chromadb.PersistentClient(path=persist_dir)
        return Chroma(client=client, collection_name="papers", embedding_function=embed)

    # 切分
    chunk_size = CONFIG.get("chunk_size", 1500)
    chunk_overlap = CONFIG.get("chunk_overlap", 200)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    chunks = splitter.split_documents(docs)
    log.info(f"✂️ 切分: {len(chunks)} 块")

    # 向量化
    log.info("🧠 向量化 (ONNX MiniLM L6 v2 本地模型)...")
    import chromadb
    client = chromadb.PersistentClient(path=persist_dir)
    db = Chroma.from_documents(
        documents=chunks,
        embedding=embed,
        client=client,
        collection_name="papers"
    )
    log.info("✅ 向量库已保存")
    return db


# ── 服务器状态 ──────────────────────────────────────────────────────

class ServerState:
    def __init__(self):
        self.db = None
        self.papers_cache = []
        self.papers_cache_time = 0

    def get_retriever(self):
        if self.db is None:
            raise RuntimeError("向量库未初始化")
        return self.db.as_retriever(
            search_kwargs={"k": CONFIG.get("retrieval_k", 5)}
        )

    def get_papers(self, refresh=False):
        now = time.time()
        if refresh or not self.papers_cache or (now - self.papers_cache_time > 60):
            self.papers_cache = get_zotero_papers()
            self.papers_cache_time = now
        return self.papers_cache


state = ServerState()


# ── 辅助函数 ────────────────────────────────────────────────────────

def api_response(data=None, error=None, success=True):
    resp = {"success": success}
    if data is not None:
        resp["data"] = data
    if error is not None:
        resp["error"] = error
    return resp


# ── FastAPI ──────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app):
    rebuild = "--rebuild" in sys.argv
    log.info("🔄 初始化向量库...")
    try:
        state.db = build_vector_db(force=rebuild)
        log.info("✅ 向量库就绪")
    except Exception as e:
        log.error(f"❌ 向量库初始化失败: {e}")
    yield
    log.info("👋 服务器关闭")


from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(
    title="ZotChat API",
    description="Zotero 论文对话功能后端 REST API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SearchRequest(BaseModel):
    query: str


class ChatRequest(BaseModel):
    messages: List[Dict[str, str]]


# ── API 端点 ────────────────────────────────────────────────────────

@app.get("/api/status")
async def api_status():
    """返回服务状态、论文数和向量块数"""
    if state.db is None:
        return api_response(data={
            "status": "initializing",
            "message": "向量库正在初始化"
        })
    try:
        count = state.db._collection.count()
    except Exception:
        count = 0
    papers = state.get_papers()
    return api_response(data={
        "status": "running",
        "version": "1.0.0",
        "vector_db_chunks": count,
        "zotero_papers_total": len(papers),
        "zotero_papers_with_pdf": sum(1 for p in papers if p.get("pdf_exists")),
        "config": {
            "llm_model": CONFIG.get("llm_model", ""),
            "max_pdfs_indexed": CONFIG.get("max_pdfs_to_index", 200),
            "retrieval_k": CONFIG.get("retrieval_k", 5),
        }
    })


@app.get("/api/papers")
async def api_papers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    refresh: bool = False
):
    """返回论文列表（支持分页、搜索）"""
    papers = state.get_papers(refresh=refresh)
    if search:
        sl = search.lower()
        papers = [
            p for p in papers
            if sl in p.get("title", "").lower()
            or any(sl in a.lower() for a in p.get("authors", []))
        ]
    total = len(papers)
    start = (page - 1) * page_size
    page_papers = papers[start:start + page_size]
    result = []
    for p in page_papers:
        result.append({
            "id": p["id"],
            "key": p.get("key", ""),
            "title": p.get("title", "(无标题)"),
            "authors": p.get("authors", [])[:5],
            "journal": p.get("journal", ""),
            "date": p.get("date", ""),
            "doi": p.get("doi", ""),
            "has_pdf": p.get("pdf_exists", False),
        })
    return api_response(data={
        "papers": result,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if total else 0,
    })


@app.post("/api/search")
async def api_search(req: SearchRequest):
    """向量检索：根据 query 返回相关段落"""
    if state.db is None:
        raise HTTPException(status_code=503, detail="向量库未初始化")
    try:
        docs = state.get_retriever().invoke(req.query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"检索失败: {e}")

    results = []
    seen_sources = set()
    for doc in docs:
        source = doc.metadata.get("source", "Unknown")
        seen_sources.add(source)
        results.append({
            "content": doc.page_content[:800],
            "source": source,
            "path": doc.metadata.get("path", ""),
        })

    return api_response(data={
        "query": req.query,
        "results": results,
        "result_count": len(results),
        "source_count": len(seen_sources),
    })


@app.post("/api/chat")
async def api_chat(req: ChatRequest):
    """RAG 检索 + AI 回答 + 引用来源"""
    if state.db is None:
        raise HTTPException(status_code=503, detail="向量库未初始化")

    # 提取用户最新消息
    user_msg = ""
    for msg in reversed(req.messages):
        if msg.get("role") == "user":
            user_msg = msg["content"]
            break
    if not user_msg:
        raise HTTPException(status_code=400, detail="未找到用户消息")

    try:
        # 1) 检索相关段落
        docs = state.get_retriever().invoke(user_msg)
        context_parts = []
        sources = []
        for i, doc in enumerate(docs):
            content = doc.page_content[:2000]
            source = doc.metadata.get("source", f"来源 {i+1}")
            context_parts.append(f"[来源 {i+1}] {content}")
            sources.append({
                "index": i + 1,
                "title": source,
                "path": doc.metadata.get("path", ""),
            })

        context = "\n\n---\n\n".join(context_parts)

        # 2) 构造 LLM 消息
        system_prompt = (
            "你是一个科研助手，基于以下论文内容回答问题。"
            "请用中文回答。回答中标注引用来源，如 [来源 1]、[来源 2]。"
            "如果内容不足以回答，如实说不知道。回答要具体、专业、有条理。"
        )

        chat_msgs = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"# 参考论文\n{context}\n\n# 问题\n{user_msg}"}
        ]

        # 保留历史（最多最近 8 轮）
        history_msgs = [
            m for m in req.messages[:-1]
            if m.get("role") in ("user", "assistant")
        ]
        chat_msgs.extend(history_msgs[-16:])

        # 3) 调用 LLM
        client = get_llm_client()
        response = client.chat.completions.create(
            model=CONFIG.get("llm_model", "deepseek-chat"),
            messages=chat_msgs,
            temperature=0.3,
            max_tokens=2048,
        )
        reply = response.choices[0].message.content

        return api_response(data={
            "reply": reply,
            "sources": sources,
        })

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"对话错误: {e}")
        raise HTTPException(status_code=500, detail=f"对话生成失败: {e}")


@app.post("/api/rebuild")
async def api_rebuild():
    """重建向量库"""
    try:
        log.info("🔄 开始重建向量库...")
        state.db = build_vector_db(force=True)
        count = state.db._collection.count()
        log.info(f"✅ 重建完成，共 {count} 个块")
        return api_response(data={
            "message": "向量库重建完成",
            "chunks": count,
        })
    except Exception as e:
        log.error(f"重建失败: {e}")
        raise HTTPException(status_code=500, detail=f"重建失败: {e}")


@app.get("/api/paper/{paper_id}")
async def api_paper_detail(paper_id: int):
    """获取单篇论文详情"""
    papers = state.get_papers()
    for p in papers:
        if p["id"] == paper_id:
            pdf_preview = ""
            if p.get("pdf_path") and os.path.exists(p["pdf_path"]):
                try:
                    from langchain_community.document_loaders import PyMuPDFLoader
                    pages = PyMuPDFLoader(p["pdf_path"]).load()
                    pdf_preview = "\n\n".join(
                        page.page_content[:500] for page in pages[:4]
                    )[:3000]
                except Exception as e:
                    pdf_preview = f"(读取失败: {e})"
            return api_response(data={
                "id": p["id"],
                "key": p.get("key", ""),
                "title": p.get("title", ""),
                "authors": p.get("authors", []),
                "journal": p.get("journal", ""),
                "date": p.get("date", ""),
                "doi": p.get("doi", ""),
                "abstract": p.get("abstract", ""),
                "pdf_path": p.get("pdf_path"),
                "pdf_exists": p.get("pdf_exists", False),
                "pdf_preview": pdf_preview,
            })
    raise HTTPException(status_code=404, detail=f"论文 {paper_id} 未找到")


# ── Gradio UI ───────────────────────────────────────────────────────

def create_gradio_ui():
    import gradio as gr

    def respond(msg, history):
        if state.db is None:
            return "⚠️ 向量库未初始化，请等待服务就绪。"

        try:
            import httpx
            resp = httpx.post(
                f"http://{CONFIG['server_host']}:{CONFIG['server_port']}/api/chat",
                json={"messages": [{"role": "user", "content": msg}]},
                timeout=60
            )
            data = resp.json()
            if data.get("success"):
                reply = data["data"]["reply"]
                sources = data["data"].get("sources", [])
                if sources:
                    refs = "\n\n---\n**📚 引用来源:**"
                    for s in sources:
                        refs += f"\n[{s['index']}] {s['title']}"
                    reply += refs
                return reply
            else:
                return f"❌ 错误: {data.get('error', '未知错误')}"
        except Exception as e:
            return f"❌ 请求失败: {e}"

    with gr.Blocks(
        title="💬 ZotChat · 论文知识库",
        theme="soft",
    ) as demo:
        gr.Markdown(
            "# 💬 ZotChat\n"
            "与你的论文库对话，检索论文内容，获取 AI 回答。"
        )
        gr.ChatInterface(
            respond,
            type="messages",
            title="跟你的论文聊天",
            chatbot=gr.Chatbot(
                height=500,
                label="对话",
                type="messages",
            ),
            textbox=gr.Textbox(
                placeholder="输入问题，例如：有哪些关于纳米给药系统的研究？",
                scale=7,
            ),
        )
    return demo


# ── 入口 ────────────────────────────────────────────────────────────

def main():
    import uvicorn

    debug = "--debug" in sys.argv
    if debug:
        log.setLevel(logging.DEBUG)

    host = CONFIG["server_host"]
    port = CONFIG["server_port"]
    rebuild = "--rebuild" in sys.argv

    # 初始化向量库
    log.info("🔄 初始化向量库...")
    try:
        state.db = build_vector_db(force=rebuild)
        log.info("✅ 向量库就绪")
    except Exception as e:
        log.error(f"❌ 向量库初始化失败: {e}")

    # 后台启动 Gradio
    def run_gradio():
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            demo = create_gradio_ui()
            log.info(f"🌐 Gradio UI: http://{host}:{port + 1}")
            demo.launch(
                server_name=host,
                server_port=port + 1,
                share=False,
                quiet=True,
            )
        except Exception as e:
            log.warning(f"Gradio UI 启动失败（不影响 API）: {e}")

    gradio_thread = threading.Thread(target=run_gradio, daemon=True)
    gradio_thread.start()

    # 启动 FastAPI
    print(f"\n🌐 ZotChat API: http://{host}:{port}")
    print(f"🌐 Gradio UI:  http://{host}:{port + 1}")
    print(f"📖 安装插件后，在 Zotero 右侧面板使用")
    print(f"💡 启动参数: --rebuild 重建向量库 | --debug 调试日志\n")

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="debug" if debug else "info",
    )


if __name__ == "__main__":
    main()
