@echo off
chcp 65001 >nul
title Python 智能助手 (开发模式)

cd /d "%~dp0"

echo.
echo   🔧 开发模式 - 跳过环境检查，直接启动
echo.

if not exist "venv\Scripts\python.exe" (
    echo   ❌ 请先运行 [启动助手.bat] 完成首次安装
    pause
    exit /b 1
)

echo   🚀 启动服务...
timeout /t 2 >nul
start http://localhost:5000/chat

venv\Scripts\python run.py
pause
