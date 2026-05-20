# ZotChat XPI 安装脚本
# 用法: 打开 Zotero，然后运行此脚本

$xpiPath = "D:\MyAiFactory\zotchat\zotchat.xpi"
$zotero = Get-Process -Name "zotero" -ErrorAction SilentlyContinue | Select-Object -First 1

if (-not $zotero) {
    Write-Host "❌ Zotero 未运行。请先启动 Zotero。" -ForegroundColor Red
    exit 1
}

Write-Host "Zotero 运行中 (PID: $($zotero.Id))" -ForegroundColor Green
Write-Host "安装 XPI: $xpiPath" -ForegroundColor Cyan

# 方法 1: 直接复制到 extensions 目录
$extDir = "$env:APPDATA\Zotero\Zotero\Profiles\7xd44dxq.default\extensions"
$dstXpi = "$extDir\zotchat@myaifactory.local.xpi"

Copy-Item $xpiPath $dstXpi -Force
Write-Host "✅ XPI 已复制到: $dstXpi" -ForegroundColor Green

# 方法 2: 复制到桌面，用户可手动拖拽
$desktop = [Environment]::GetFolderPath("Desktop")
Copy-Item $xpiPath "$desktop\zotchat.xpi" -Force
Write-Host "✅ 桌面副本: $desktop\zotchat.xpi" -ForegroundColor Green

Write-Host ""
Write-Host "=== 安装说明 ===" -ForegroundColor Yellow
Write-Host "1️⃣  将桌面上的 zotchat.xpi 拖拽到 Zotero 窗口" -ForegroundColor Yellow
Write-Host "2️⃣  在弹出的对话框中点击「立即安装」" -ForegroundColor Yellow
Write-Host "3️⃣  重启 Zotero" -ForegroundColor Yellow
Write-Host ""
Write-Host "或通过菜单: 工具 → 附加组件 → 齿轮图标 → 从文件安装附加组件" -ForegroundColor Yellow
