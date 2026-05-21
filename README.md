# ZotChat 鈥?Zotero AI 璁烘枃瀵硅瘽 + 鏅鸿兘寮曠敤鎺ㄨ崘

> 鍩轰簬 Zotero 鏈湴鏂囩尞搴撶殑 AI 瀵硅瘽鍔╂墜锛屽唴缃?**CiteBot** 鏅鸿兘寮曠敤鎺ㄨ崘寮曟搸銆?
---

## 鉁?鍔熻兘

### 馃挰 璁烘枃瀵硅瘽
鐢ㄨ嚜鐒惰瑷€涓庝綘鐨?Zotero 璁烘枃搴撳璇濄€侫I 鍩轰簬鏈湴鏂囩尞鍥炵瓟锛屾墍鏈夋暟鎹湪鏈湴澶勭悊锛屼笉涓婁紶銆?
**鏀寔锛?*
- 鍩轰簬鍚戦噺妫€绱㈢殑鏈湴鏂囩尞闂瓟
- 鑷姩妫€娴?Zotero 鏂囩尞璺緞锛圥DF/鏁版嵁搴擄級
- 澶氳疆瀵硅瘽涓婁笅鏂囩悊瑙?- DeepSeek / OpenAI 鍏煎 API

### 馃敄 CiteBot 鏅鸿兘寮曠敤鎺ㄨ崘
绮樿创鏂囩珷 鈫?AI 鑷姩鍒嗘瀽鍝簺鍙ュ瓙闇€瑕佸紩鐢?鈫?浠庝綘鐨勮鏂囧簱鍖归厤鏈€鐩稿叧鐨勬枃鐚€?
**宸ヤ綔娴佺▼锛?*
1. **绮樿创鏂囩珷** 鈥?鍦?CiteBot 鐣岄潰绮樿创浣犵殑鏂囩珷姝ｆ枃
2. **鏅鸿兘鍒嗘瀽** 鈥?AI 璇嗗埆闇€瑕佸紩鐢ㄧ殑鍙ュ瓙 + 寤鸿寮曠敤浣嶇疆
3. **鏂囩尞鍖归厤** 鈥?浠庢湰鍦拌鏂囧簱妫€绱㈡渶鐩稿叧鐨?3-5 绡囨枃鐚?4. **閫愭潯瀹￠槄** 鈥?瀵规瘡鏉″紩鐢ㄥ缓璁彲锛氣渽 **鎺ュ彈** / 鉁忥笍 **鑷畾涔?* / 鉂?**璺宠繃**
5. **涓€閿鍑?* 鈥?瀵煎嚭甯﹀紩鐢ㄦ爣璁扮殑 Markdown 鏂囨。

### 馃搫 瀵煎嚭
- 涓€閿鍑哄甫寮曠敤鏍囪鐨?Markdown
- 寮曠敤鏍煎紡锛歚[浣滆€? 骞翠唤 #缂栧彿]`
- 鏂囨湯鑷姩鐢熸垚鍙傝€冩枃鐚垪琛?
### 馃敀 闅愮瀹夊叏
- **100% 鏈湴杩愯** 鈥?璁烘枃鏁版嵁涓嶅嚭鏈満
- **鏈湴鍚戦噺搴?* 鈥?ChromaDB + ONNX MiniLM 鏈湴宓屽叆锛屼笉闇€瑕佽仈缃?- **浠?LLM 鏌ヨ** 鈥?浠呮枃绔犲垎鏋愯姹傜粡 API 鍙戦€?
---

## 馃殌 蹇€熷紑濮?
### 涓嬭浇
浠?[Releases](https://github.com/wade20250715/zotchat-zotero-plugin/releases) 涓嬭浇 `ZotChat.exe`锛堟帹鑽愶級鎴?`zotchat.xpi`锛圸otero 鎻掍欢锛夈€?
### 鏂瑰紡涓€锛氫娇鐢?ZotChat.exe锛堟帹鑽愶級

```bash
# 璁剧疆 API Key锛圖eepSeek API锛屽繀濉級
set ZOTCHAT_API_KEY=sk-your-key-here

# 鍙屽嚮杩愯
ZotChat.exe
```

娴忚鍣ㄦ墦寮€ `http://127.0.0.1:7891` 鍗冲彲浣跨敤銆?
### 鏂瑰紡浜岋細Zotero 鎻掍欢 + Python 鍚庣

**1. 瀹夎鎻掍欢**
- 鎵撳紑 Zotero 鈫?宸ュ叿 鈫?闄勫姞缁勪欢
- 灏?`zotchat.xpi` 鎷栧叆 Zotero 绐楀彛
- 閲嶅惎 Zotero锛屽彸渚ф爮鍑虹幇 **ZotChat** 鏍囩椤?
**2. 鍚姩鍚庣**
```bash
pip install -r requirements.txt
set ZOTCHAT_API_KEY=sk-your-key-here
python zotchat_server.py
```

---

## 鈿欙笍 閰嶇疆

### 鐜鍙橀噺

| 鍙橀噺 | 璇存槑 | 榛樿鍊?|
|------|------|--------|
| `ZOTCHAT_API_KEY` | DeepSeek / OpenAI API Key | **蹇呭～** |
| `ZOTCHAT_BASE_URL` | API 鍦板潃 | `https://api.deepseek.com/v1` |
| `ZOTCHAT_MODEL` | 妯″瀷鍚?| `deepseek-chat` |
| `ZOTCHAT_HOST` | API 鐩戝惉鍦板潃 | `127.0.0.1` |
| `ZOTCHAT_PORT` | API 绔彛 | `7890` |
| `ZOTCHAT_UI_PORT` | Gradio UI 绔彛 | `7891` |

### 閰嶇疆鏂囦欢

鎴栧垱寤?`zotchat_config.json` 涓?`ZotChat.exe` 鍚岀洰褰曪細

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

## 馃搧 椤圭洰缁撴瀯

```
zotchat/
鈹溾攢鈹€ zotchat_server.py        # 涓诲悗绔紙FastAPI + Gradio锛?鈹溾攢鈹€ zotchat.xpi              # Zotero 鎻掍欢鍖?鈹溾攢鈹€ requirements.txt         # Python 渚濊禆
鈹溾攢鈹€ bootstrap.js             # Zotero 鎻掍欢鍏ュ彛
鈹溾攢鈹€ install.rdf              # 鎻掍欢鍏冩暟鎹?鈹溾攢鈹€ chrome/
鈹?  鈹溾攢鈹€ content/
鈹?  鈹?  鈹溾攢鈹€ panel.xhtml      # 渚ц竟鏍?UI
鈹?  鈹?  鈹溾攢鈹€ overlay.xhtml    # 鐣岄潰瑕嗙洊
鈹?  鈹?  鈹溾攢鈹€ schema.json      # 鎻掍欢閰嶇疆鏋舵瀯
鈹?  鈹?  鈹溾攢鈹€ icons/           # 鎻掍欢鍥炬爣
鈹?  鈹?  鈹斺攢鈹€ scripts/
鈹?  鈹?      鈹斺攢鈹€ panel.js     # 鍓嶇閫昏緫
鈹?  鈹斺攢鈹€ locale/
鈹?      鈹溾攢鈹€ en-US/           # 鑻辨枃璇█鍖?鈹?      鈹斺攢鈹€ zh-CN/           # 涓枃璇█鍖?鈹溾攢鈹€ manifest.json            # WebExtension 娓呭崟
鈹溾攢鈹€ chrome.manifest          # 鎻掍欢娉ㄥ唽
鈹溾攢鈹€ prefs.js                 # 榛樿鍋忓ソ
鈹溾攢鈹€ updates.json             # 鑷姩鏇存柊閰嶇疆
鈹溾攢鈹€ build_exe.py             # PyInstaller 鎵撳寘鑴氭湰
鈹溾攢鈹€ build_xpi.py             # XPI 鎵撳寘鑴氭湰
鈹溾攢鈹€ INSTALL.md               # 瀹夎鎸囧崡
鈹斺攢鈹€ README.md                # 鏈枃浠?```

---

## 馃洜 鎶€鏈爤

| 缁勪欢 | 鎶€鏈?|
|------|------|
| **鍚庣妗嗘灦** | Python 3.10 + FastAPI |
| **UI 鐣岄潰** | Gradio |
| **鍚戦噺鏁版嵁搴?* | ChromaDB |
| **鏈湴宓屽叆** | ONNX MiniLM (all-MiniLM-L6-v2) |
| **LLM API** | DeepSeek / OpenAI 鍏煎 API |
| **PDF 瑙ｆ瀽** | PyMuPDF |
| **鎻掍欢** | Zotero XUL + WebExtension |
| **鎵撳寘** | PyInstaller |

---

## 馃摳 鎴浘

> *锛堟埅鍥惧緟琛ュ厖 - 娆㈣繋 PR 璐＄尞鎴浘锛?

- ZotChat 瀵硅瘽鐣岄潰
- CiteBot 寮曠敤鎺ㄨ崘鍒嗘瀽
- 閫愭潯瀹￠槄鍗＄墖鐣岄潰
- 瀵煎嚭 Markdown 绀轰緥

---

## 馃搫 璁稿彲璇?
[GNU General Public License v3](LICENSE)

---

## 馃檹 鑷磋阿

- [Zotero](https://www.zotero.org/) 鈥?寮€婧愭枃鐚鐞嗗伐鍏?- [ChromaDB](https://www.trychroma.com/) 鈥?寮€婧愬悜閲忔暟鎹簱
- [Gradio](https://www.gradio.app/) 鈥?ML 婕旂ず妗嗘灦
- [DeepSeek](https://deepseek.com/) 鈥?澶ц瑷€妯″瀷 API
