@echo off
chcp 65001 >nul
title ZotChat Server

echo ============================================
echo   ZotChat Server
echo   AI 论文对话后端
echo ============================================
echo.

set PYTHONPATH=C:\Users\12462\AppData\Local\Programs\Python\Python310

echo 启动 API 服务器 (端口 7890)...
echo Gradio Web UI: http://127.0.0.1:7891
echo API 端点:      http://127.0.0.1:7890
echo.

"%PYTHONPATH%\python.exe" D:\MyAiFactory\zotchat_server.py

if errorlevel 1 (
    echo.
    echo ⚠️ 启动失败，请检查：
    echo   1. 端口 7890 是否被占用
    echo   2. Python 依赖是否安装
    echo.
    pause
)
