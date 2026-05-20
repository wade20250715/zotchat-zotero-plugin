"use strict";

/*
 * ZotChat — Bootstrap
 *
 * 在 Zotero 右侧边栏添加 "ZotChat" 标签页。
 * 通过 <iframe> 加载内置面板 HTML，连接 http://127.0.0.1:7890/api 后端。
 *
 * Zotero 7+ bootstrapped addon 入口：
 *   install()   — 安装
 *   startup()   — 启动（注册 UI）
 *   shutdown()  — 关闭（卸载 UI）
 *   uninstall() — 卸载
 */

/* globals Zotero, Services, ChromeUtils, Components */
/* eslint-env es2021 */

const PLUGIN_ID   = "zotchat@myaifactory.local";
const PLUGIN_NAME = "ZotChat";

// ── install / uninstall ────────────────────────────────────────

function install(data, reason) {
    Zotero.log(`${PLUGIN_NAME} installed`, "zotchat");
}

function uninstall(data, reason) {
    Zotero.log(`${PLUGIN_NAME} uninstalled`, "zotchat");
}

// ── startup / shutdown ─────────────────────────────────────────

async function startup({ id, version, rootURI }, reason) {
    Zotero.log(`${PLUGIN_NAME} v${version} starting`, "zotchat");
    await Zotero.initializationPromise;

    for (const win of Zotero.getMainWindows()) {
        addPanel(win, rootURI);
    }

    Services.obs.addObserver(winObserver, "Zotero:MainWindowCreated", false);
    Zotero.log(`${PLUGIN_NAME} started`, "zotchat");
}

function shutdown({ id, version, rootURI }, reason) {
    Zotero.log(`${PLUGIN_NAME} shutting down`, "zotchat");
    try { Services.obs.removeObserver(winObserver, "Zotero:MainWindowCreated"); } catch (_) {}

    for (const win of Zotero.getMainWindows()) {
        removePanel(win);
    }
}

// ── 窗口观察者 ────────────────────────────────────────────────

const winObserver = {
    observe(subject) {
        const win = subject;
        win.setTimeout(() => {
            try { addPanel(win, null); } catch (e) {
                Zotero.logError(`${PLUGIN_NAME}: addPanel error: ${e}`);
            }
        }, 800);
    },
    QueryInterface: ChromeUtils.generateQI(["nsIObserver"])
};

// ── 添加面板 ──────────────────────────────────────────────────

function addPanel(win, rootURI) {
    if (win.document.getElementById("zotchat-box")) return;

    const doc = win.document;
    const paneHeader = doc.querySelector("#zotero-item-pane-header");
    if (!paneHeader) {
        Zotero.log(`${PLUGIN_NAME}: item-pane-header not found, will retry`, "zotchat");
        win.setTimeout(() => addPanel(win, rootURI), 1000);
        return;
    }

    // ── 标签按钮 ──
    const tab = doc.createElement("toolbarbutton");
    tab.id = "zotchat-tab";
    tab.setAttribute("label", "ZotChat");
    tab.setAttribute("class", "zotero-tab toolbarbutton-1");
    tab.setAttribute("tooltiptext", "AI 对话 · 跟论文聊天");
    tab.addEventListener("click", () => toggle(win));

    const tabBox = paneHeader.querySelector("tabbox, .tab-bar") || paneHeader;
    tabBox.appendChild(tab);

    // ── 面板容器 ──
    const box = doc.createElement("vbox");
    box.id = "zotchat-box";
    box.setAttribute("flex", "1");
    box.setAttribute("hidden", "true");
    box.style.overflow = "hidden";

    const iframe = doc.createElement("iframe");
    iframe.id = "zotchat-iframe";
    iframe.setAttribute("type", "content");
    iframe.setAttribute("flex", "1");
    iframe.style.cssText = "width:100%;height:100%;border:none;background:#fff";
    box.appendChild(iframe);

    const target = doc.querySelector("#zotero-item-pane-content, #zotero-item-pane, .zotero-pane-content");
    if (target) target.appendChild(box);
    else paneHeader.parentNode.appendChild(box);

    iframe.src = "about:blank";
    iframe.addEventListener("load", function onLoad() {
        iframe.removeEventListener("load", onLoad);
        const cd = iframe.contentDocument;
        cd.open();
        cd.write(PANEL_HTML);
        cd.close();
    }, { once: true });

    Zotero.log(`${PLUGIN_NAME}: panel added`, "zotchat");
}

function removePanel(win) {
    const doc = win.document;
    const tab = doc.getElementById("zotchat-tab");
    const box = doc.getElementById("zotchat-box");
    if (tab) tab.remove();
    if (box) box.remove();
}

function toggle(win) {
    const box = win.document.getElementById("zotchat-box");
    const tab = win.document.getElementById("zotchat-tab");
    if (!box) return;
    const hidden = box.getAttribute("hidden") !== "false";
    box.setAttribute("hidden", hidden ? "false" : "true");
    if (tab) tab.setAttribute("checked", !hidden);
}

// ── 面板 HTML ─────────────────────────────────────────────────

const PANEL_HTML = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;font-size:13px;color:#1f2937;background:#fff;height:100vh;display:flex;flex-direction:column;overflow:hidden}

/* 头部 */
.hdr{background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;padding:8px 12px;display:flex;align-items:center;justify-content:space-between;flex-shrink:0;font-weight:600;font-size:13px}
.hdr .st{font-size:11px;font-weight:400}
.sd{display:inline-block;width:6px;height:6px;border-radius:50%;margin-right:4px}
.sd.on{background:#34d399}
.sd.off{background:#f87171}
.sd.busy{background:#fbbf24;animation:p 1s infinite}
@keyframes p{50%{opacity:.4}}

/* 标签 */
.tabbar{display:flex;border-bottom:1px solid #e5e7eb;flex-shrink:0}
.tabi{flex:1;padding:7px;text-align:center;font-size:12px;cursor:pointer;color:#6b7280;border-bottom:2px solid transparent;transition:.15s;user-select:none}
.tabi.on{color:#4f46e5;border-bottom-color:#4f46e5;font-weight:500}
.tabi:hover{background:#f9fafb}

/* 消息区 */
.msgs{flex:1;overflow-y:auto;padding:10px;display:flex;flex-direction:column;gap:10px}
.msg{max-width:92%;padding:8px 12px;border-radius:12px;line-height:1.5;font-size:13px;word-wrap:break-word}
.msg.u{align-self:flex-end;background:#667eea;color:#fff;border-bottom-right-radius:4px}
.msg.a{align-self:flex-start;background:#f3f4f6;color:#1f2937;border-bottom-left-radius:4px}
.msg .ref{font-size:11px;color:#6b7280;margin-top:6px;border-top:1px solid #e5e7eb;padding-top:4px}
.msg .ref a{color:#4f46e5;text-decoration:none;cursor:pointer}
.msg .ref a:hover{text-decoration:underline}

/* 输入区 */
.ia{padding:8px 12px 10px;border-top:1px solid #e5e7eb;flex-shrink:0;display:flex;gap:8px;align-items:flex-end}
.ia textarea{flex:1;border:1px solid #d1d5db;border-radius:8px;padding:8px 10px;font-size:13px;font-family:inherit;resize:none;outline:none;min-height:34px;max-height:100px;line-height:1.4}
.ia textarea:focus{border-color:#667eea;box-shadow:0 0 0 2px rgba(102,126,234,.15)}
.ia button{background:#667eea;color:#fff;border:none;border-radius:8px;padding:7px 14px;font-size:13px;cursor:pointer;transition:.15s;white-space:nowrap}
.ia button:hover{background:#5a6fd6}
.ia button:disabled{background:#d1d5db;cursor:default}

/* 空状态 */
.emp{display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;color:#9ca3af;text-align:center;padding:20px}
.emp .ico{font-size:32px;margin-bottom:10px}
.emp h3{font-size:14px;color:#6b7280;margin-bottom:6px}
.emp p{font-size:12px;line-height:1.5}
.emp .btn{margin-top:10px;padding:5px 14px;border:1px solid #d1d5db;border-radius:6px;background:#fff;cursor:pointer;font-size:12px;color:#4f46e5}
.emp .btn:hover{background:#f9fafb}

/* 论文列表 */
.pl{padding:4px}
.pi{padding:6px 8px;border-bottom:1px solid #f3f4f6;cursor:pointer;transition:.15s;font-size:12px;line-height:1.4}
.pi:hover{background:#f9fafb}
.pi .pt{font-weight:500;color:#1f2937;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.pi .pm{font-size:11px;color:#9ca3af;margin-top:2px}

.er{padding:10px;background:#fef2f2;border:1px solid #fecaca;border-radius:8px;color:#dc2626;font-size:12px;margin:8px;line-height:1.5}

::-webkit-scrollbar{width:4px}
::-webkit-scrollbar-thumb{background:#d1d5db;border-radius:2px}
</style>
</head>
<body>

<div class="hdr">
  <span>💬 ZotChat</span>
  <span class="st"><span class="sd busy" id=sd></span><span id=st>连接中...</span></span>
</div>

<div class="tabbar">
  <div class="tabi on" data-t="chat" onclick=sw("chat")>💬 对话</div>
  <div class="tabi" data-t="papers" onclick=sw("papers")>📄 论文</div>
</div>

<div id="tc" style="display:flex;flex-direction:column;flex:1">
  <div class="msgs" id=msgs>
    <div class=emp id=emp>
      <div class=ico>🤖</div>
      <h3>跟你的论文聊天</h3>
      <p>输入问题，AI 会根据论文库回答。</p>
      <p style="margin-top:4px;font-size:11px">例如：纳米给药系统在脑部疾病中的应用</p>
    </div>
  </div>
  <div class=ia>
    <textarea id=inp placeholder="输入问题..." rows=1 onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();go()}"></textarea>
    <button id=snd onclick=go()>发送</button>
  </div>
</div>

<div id="tp" style="display:none;flex:1;overflow-y:auto">
  <div class=emp id=pll>
    <div class=ico>📄</div>
    <h3>加载论文列表...</h3>
  </div>
  <div class=pl id=pl></div>
</div>

<script>
const API="http://127.0.0.1:7890";
let his=[],busy=false,pc=[];

addEventListener("DOMContentLoaded",()=>{st();ld();setInterval(st,30e3)});

function sw(t){
  document.querySelectorAll(".tabi").forEach(x=>x.classList.toggle("on",x.dataset.t===t));
  document.getElementById("tc").style.display=t==="chat"?"flex":"none";
  document.getElementById("tp").style.display=t==="papers"?"block":"none";
  if(t==="papers")ld();
}

async function st(){
  try{
    const r=await fetch(API+"/api/status",{signal:AbortSignal.timeout(3e3)});
    const d=await r.json();
    if(d.success){
      document.getElementById("sd").className="sd on";
      document.getElementById("st").textContent="已连接 ("+(d.data?.zotero_papers_total||"?")+" 篇)";
    }else throw 0;
  }catch(e){
    document.getElementById("sd").className="sd off";
    document.getElementById("st").textContent="后端离线";
  }
}

async function ld(){
  const c=document.getElementById("pl"),l=document.getElementById("pll");
  try{
    const r=await fetch(API+"/api/papers?page_size=50",{signal:AbortSignal.timeout(5e3)});
    const d=await r.json();
    if(d.success&&d.data.papers.length){
      l.style.display="none";pc=d.data.papers;c.innerHTML="";
      for(const p of d.data.papers){
        const e=document.createElement("div");
        e.className="pi";
        e.innerHTML='<div class="pt">'+(p.title||"(无标题)")+'</div><div class="pm">'+(p.authors?.slice(0,3).join("; ")||"无作者")+(p.date?" · "+p.date:"")+(p.has_pdf?" 📎":"")+'</div>';
        e.onclick=()=>{document.getElementById("inp").value="请介绍这篇论文: "+p.title;sw("chat");document.getElementById("inp").focus()};
        c.appendChild(e);
      }
    }else{
      l.innerHTML='<div class=ico>📄</div><h3>暂无论文</h3><p>请先在 Zotero 中导入论文。</p><button class=btn onclick=ld()>刷新</button>';
    }
  }catch(e){
    l.innerHTML='<div class=ico>⚠️</div><h3>连接后端失败</h3><p>'+e.message+'</p><button class=btn onclick=ld()>重试</button>';
  }
}

async function go(){
  const i=document.getElementById("inp"),b=document.getElementById("snd"),c=document.getElementById("msgs");
  const t=i.value.trim();
  if(!t||busy)return;
  i.value="";i.style.height="auto";busy=true;b.disabled=true;
  const emp=document.getElementById("emp");if(emp)emp.style.display="none";
  ad(t,"u");
  const ld=ad("思考中...","a","ld");
  c.scrollTop=c.scrollHeight;
  try{
    const msgs=[{role:"system",content:"你是科研助手，基于论文回答问题。用中文。"},...his.slice(-6).map(m=>({role:m.r,content:m.c})),{role:"user",content:t}];
    const r=await fetch(API+"/api/chat",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({messages:msgs}),signal:AbortSignal.timeout(60e3)});
    const d=await r.json();ld.remove();
    if(d.success){
      let h=d.data.reply;
      if(d.data.sources?.length){
        h+='<div class=ref>📚 来源:<br>'+d.data.sources.map(s=>'['+s.index+'] '+s.title).join("<br>")+'</div>';
      }
      ad(h,"a",null,1);
      his.push({r:"user",c:t},{r:"assistant",c:d.data.reply});
    }else{ld.remove();ad("❌ "+(d.error||"未知错误"),"a");}
  }catch(e){
    ld.remove();
    ad(e.name==="TimeoutError"?"⏰ 请求超时，检查后端":"❌ "+e.message,"a");
  }
  busy=false;b.disabled=false;i.focus();
}

function ad(t,r,ex,html){
  const c=document.getElementById("msgs");
  const d=document.createElement("div");
  d.className="msg "+(r==="u"?"u":"a")+(ex?" "+ex:"");
  d[html?"innerHTML":"textContent"]=t;
  c.appendChild(d);c.scrollTop=c.scrollHeight;
  return d;
}

addEventListener("DOMContentLoaded",()=>{
  document.getElementById("inp").addEventListener("input",function(){this.style.height="auto";this.style.height=Math.min(this.scrollHeight,100)+"px"});
});
<\/script>
</body>
</html>`;
