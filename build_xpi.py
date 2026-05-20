#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
打包 ZotChat 插件为 .xpi 文件并部署到 Zotero。
"""
import os, sys, zipfile, json, shutil, tempfile, stat, time

PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))
XPI_PATH = os.path.join(PLUGIN_DIR, "zotchat.xpi")
ZOTERO_EXT_DIR = os.path.expandvars(
    r"%APPDATA%\Zotero\Zotero\Profiles\7xd44dxq.default\extensions"
)
PLUGIN_ID = "zotchat@myaifactory.local"

def build_xpi():
    manifest_path = os.path.join(PLUGIN_DIR, "manifest.json")
    if not os.path.exists(manifest_path):
        print("❌ 未找到 manifest.json"); return False
    include = ["manifest.json", "install.rdf", "chrome.manifest", "bootstrap.js", "prefs.js", "updates.json", "chrome"]
    with tempfile.TemporaryDirectory() as tmpdir:
        for item in include:
            src = os.path.join(PLUGIN_DIR, item)
            dst = os.path.join(tmpdir, item)
            if os.path.isfile(src): shutil.copy2(src, dst)
            elif os.path.isdir(src): shutil.copytree(src, dst)
        for f in ["build_xpi.py", "create_icon.py", "register_plugin.py"]:
            fp = os.path.join(tmpdir, f)
            if os.path.exists(fp): os.remove(fp)
        
        # Build XPI with Unix-style ZIP attributes (required by Zotero 9/Firefox 128)
        with zipfile.ZipFile(XPI_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(tmpdir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, tmpdir)
                    
                    # Create ZipInfo with Unix create_system=3
                    info = zipfile.ZipInfo(arcname)
                    info.compress_type = zipfile.ZIP_DEFLATED
                    # Set Unix-style permissions: 0644 for files
                    info.external_attr = (0o10644 << 16)  # Unix file + rw-r--r--
                    info.create_system = 3  # Unix
                    
                    with open(file_path, 'rb') as f:
                        data = f.read()
                    
                    zf.writestr(info, data)
    
    print(f"✅ XPI 创建: {XPI_PATH} ({os.path.getsize(XPI_PATH):,} bytes)")
    
    # Verify Unix attributes were set
    with zipfile.ZipFile(XPI_PATH) as z:
        first = z.infolist()[0]
        print(f"   create_system={first.create_system}, attr={oct(first.external_attr)}")
    
    return True

def install_xpi():
    if not os.path.exists(ZOTERO_EXT_DIR):
        print(f"❌ Zotero 扩展目录不存在: {ZOTERO_EXT_DIR}"); return False
    xpi_dst = os.path.join(ZOTERO_EXT_DIR, f"{PLUGIN_ID}.xpi")
    shutil.copy2(XPI_PATH, xpi_dst)
    stub_path = os.path.join(ZOTERO_EXT_DIR, PLUGIN_ID)
    if os.path.exists(stub_path) and not stub_path.endswith('.xpi'):
        os.remove(stub_path)
    print(f"✅ XPI 已部署: {xpi_dst} ({os.path.getsize(xpi_dst):,} bytes)")
    return True

if __name__ == "__main__":
    print("=" * 50)
    print("  ZotChat - 打包工具")
    print("=" * 50)
    print()
    if not build_xpi(): sys.exit(1)
    print()
    if install_xpi():
        print()
        # Register in extensions.json with schemaVersion 37
        exec(open(os.path.join(PLUGIN_DIR, "register_plugin.py")).read())
    print()
    print("🔔 重启 Zotero 后生效")
