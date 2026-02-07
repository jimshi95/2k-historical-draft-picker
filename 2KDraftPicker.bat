@echo off
chcp 65001 >nul
echo ===============================================
echo  2K历史选秀年份生成器
echo ===============================================
echo.

REM 检查Python是否可用
python --version >nul 2>nul
if %errorlevel% neq 0 (
    echo 错误: 未找到Python
    echo 请确保Python已安装并添加到系统PATH
    echo.
    echo 可以从以下地址下载Python: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

REM 检查虚拟环境是否存在
if exist ".venv\Scripts\python.exe" (
    echo 使用虚拟环境...
    set PYTHON_EXE=.venv\Scripts\python.exe
) else (
    echo 使用系统Python...
    set PYTHON_EXE=python
)

REM 检查必要模块
echo 检查必要模块...
%PYTHON_EXE% -c "import tkinter; import json; import os; import sys" 2>nul
if %errorlevel% neq 0 (
    echo 错误: Python模块检查失败
    echo 确保已安装必要的模块
    echo.
    pause
    exit /b 1
)

REM 检查dotenv模块
%PYTHON_EXE% -c "import dotenv" 2>nul
if %errorlevel% neq 0 (
    echo 警告: python-dotenv模块未安装
    echo 正在尝试安装python-dotenv...
    pip install python-dotenv
    if %errorlevel% neq 0 (
        echo 错误: 安装python-dotenv失败
        echo 请手动运行: pip install python-dotenv
        echo.
        pause
        exit /b 1
    )
    echo python-dotenv安装成功！
    echo.
)

echo 正在启动2K历史选秀年份生成器...
echo 请稍候...
echo.

REM 运行GUI应用
%PYTHON_EXE% gui_main.py

if %errorlevel% neq 0 (
    echo.
    echo 程序运行出错，错误代码: %errorlevel%
    echo 请检查Python环境和依赖项
    echo.
    pause
    exit /b %errorlevel%
)

echo.
echo 程序已正常退出。
pause