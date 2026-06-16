@echo off
chcp 65001 >nul
title Python 多功能智能助手

:: ============================================
::  Python 多功能智能助手 - 一键启动脚本
::  双击此文件即可运行
:: ============================================

cd /d "%~dp0"

echo.
echo   ╔══════════════════════════════════════════╗
echo   ║     🤖 Python 多功能智能助手              ║
echo   ║     一键启动脚本                          ║
echo   ╚══════════════════════════════════════════╝
echo.

:: ---- 1. 检查 Python ----
echo [1/4] 检查 Python 环境...
set PYTHON=

:: 先检查 venv 中是否已有 python
if exist "venv\Scripts\python.exe" set PYTHON=venv\Scripts\python

:: 否则尝试系统 Python
if "%PYTHON%"=="" (
    for %%p in (python python3 py) do (
        where %%p >nul 2>&1
        if not errorlevel 1 set PYTHON=%%p
    )
)

if "%PYTHON%"=="" (
    echo   ❌ 未找到 Python！请先安装 Python 3.10+
    echo   📥 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

%PYTHON% --version
echo   ✅ Python 就绪

:: ---- 2. 检查/创建虚拟环境 ----
echo.
echo [2/4] 准备虚拟环境...

if not exist "venv\Scripts\python.exe" (
    echo   📦 首次运行，正在创建虚拟环境...
    %PYTHON% -m venv venv
    if errorlevel 1 (
        echo   ❌ 虚拟环境创建失败
        pause
        exit /b 1
    )
    echo   ✅ 虚拟环境创建成功

    echo   📥 安装依赖包（首次运行需要几分钟）...
    venv\Scripts\python -m pip install --upgrade pip -q
    venv\Scripts\python -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/ --trusted-host pypi.tuna.tsinghua.edu.cn
    if errorlevel 1 (
        echo   ❌ 依赖安装失败，尝试使用默认源...
        venv\Scripts\python -m pip install -r requirements.txt
        if errorlevel 1 (
            echo   ❌ 依赖安装失败，请检查网络连接
            pause
            exit /b 1
        )
    )
    echo   ✅ 依赖安装完成
) else (
    echo   ✅ 虚拟环境已就绪
)

:: ---- 3. 检查配置文件 ----
echo.
echo [3/4] 检查配置文件...

if not exist ".env" (
    echo   📝 创建默认配置文件 .env
    copy .env.example .env >nul
    echo   ⚠️  请编辑 .env 文件，填入你的 API Key
    echo   📝 正在用记事本打开 .env ...
    start notepad .env
) else (
    echo   ✅ 配置文件已存在
)

:: ---- 4. 启动服务 ----
echo.
echo [4/4] 正在启动服务...
echo.
echo   ╔══════════════════════════════════════════╗
echo   ║  服务启动中...                            ║
echo   ║  对话页面: http://localhost:5000/chat     ║
echo   ║  数据分析: http://localhost:5000/data     ║
echo   ║  工具集:   http://localhost:5000/tools    ║
echo   ║  按 Ctrl+C 停止服务                       ║
echo   ╚══════════════════════════════════════════╝
echo.

:: 延迟打开浏览器（等服务器启动）
start "" cmd /c "timeout /t 3 >nul && start http://localhost:5000/chat"

:: 启动 Flask
venv\Scripts\python run.py

pause
