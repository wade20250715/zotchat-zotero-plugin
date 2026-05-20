"use strict";

/*
 * ZotChat Panel - 面板逻辑
 *
 * 此文件是 Zotero 插件的面板逻辑入口。
 * 主要 UI 渲染在 bootstrap.js 的 PANEL_HTML 中完成。
 * 此文件负责 Zotero 端的事件处理和 API 通信。
 */

/* globals Zotero */

class ZotChatPanel {
    constructor() {
        this.apiBase = "http://127.0.0.1:7890";
        this.papers = [];
    }

    /**
     * 通过本地 API 搜索论文
     */
    async searchPapers(query) {
        try {
            const resp = await fetch(`${this.apiBase}/api/search`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ query }),
                signal: AbortSignal.timeout(10000)
            });
            const data = await resp.json();
            return data.success ? data.data : null;
        } catch (e) {
            Zotero.logError(`ZotChat: Search failed - ${e}`);
            return null;
        }
    }

    /**
     * 发送聊天消息
     */
    async sendChat(messages) {
        try {
            const resp = await fetch(`${this.apiBase}/api/chat`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ messages }),
                signal: AbortSignal.timeout(60000)
            });
            const data = await resp.json();
            return data.success ? data.data : null;
        } catch (e) {
            Zotero.logError(`ZotChat: Chat failed - ${e}`);
            return null;
        }
    }
}

if (typeof module !== "undefined") {
    module.exports = { ZotChatPanel };
}
