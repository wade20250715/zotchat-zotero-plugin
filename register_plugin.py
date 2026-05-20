#!/usr/bin/env python3
"""Register ZotChat in Zotero's extensions.json (schemaVersion 37)"""
import json, os, hashlib, time, zipfile

ext_dir = os.path.expandvars(r'%APPDATA%\Zotero\Zotero\Profiles\7xd44dxq.default\extensions')
ext_json_path = os.path.join(os.path.dirname(ext_dir), 'extensions.json')
ext_id = 'zotchat@myaifactory.local'
xpi_path = os.path.join(ext_dir, f'{ext_id}.xpi')

# Verify XPI exists
if not os.path.exists(xpi_path):
    src_xpi = r'D:\MyAiFactory\zotchat\zotchat.xpi'
    if os.path.exists(src_xpi):
        import shutil
        shutil.copy2(src_xpi, xpi_path)
        print(f"✅ XPI copied: {xpi_path}")

# Read manifest
with zipfile.ZipFile(xpi_path) as z:
    manifest = json.loads(z.read('manifest.json'))

version = manifest.get('version', '1.0.0')
name = manifest.get('name', 'ZotChat')
now = time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime())

addon_entry = {
    "id": ext_id,
    "syncGUID": hashlib.md5(ext_id.encode()).hexdigest()[:12],
    "version": version, "type": "extension",
    "appDisabled": False, "userDisabled": False, "softDisabled": False,
    "foreignInstall": True, "hasEmbeddedWebExtension": True,
    "installDate": now, "updateDate": now, "applyBackgroundUpdates": 1,
    "location": "app-profile",
    "sourceURI": f"file:///{xpi_path.replace(chr(92), '/')}",
    "active": True, "visible": True, "seen": True,
    "defaultLocale": {"name": name, "description": manifest.get('description', '')},
    "targetApplications": [{"id": "zotero@chnm.gmu.edu", "minVersion": "7.0", "maxVersion": "9.*"}]
}

if os.path.exists(ext_json_path):
    with open(ext_json_path, 'r', encoding='utf-8-sig') as f:
        ext_data = json.load(f)
else:
    ext_data = {"schemaVersion": 37, "addons": []}

addons = ext_data.get('addons', [])
for i, a in enumerate(addons):
    if a.get('id') == ext_id:
        addons[i] = addon_entry; break
else:
    addons.append(addon_entry)
ext_data['addons'] = addons

with open(ext_json_path, 'w', encoding='utf-8') as f:
    json.dump(ext_data, f, indent=2, ensure_ascii=False)

print(f"✅ ZotChat v{version} 已注册")
