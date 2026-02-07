@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
echo ===============================================
echo  2K历史选秀生成器 - 构建脚本
echo ===============================================
echo.

REM 确定Python路径：优先使用虚拟环境
set PYTHON_EXE=python
set PIP_EXE=pip
set PYINSTALLER_EXE=pyinstaller

if exist "%~dp0.venv\Scripts\python.exe" (
    set PYTHON_EXE=%~dp0.venv\Scripts\python.exe
    set PIP_EXE=%~dp0.venv\Scripts\pip.exe
    set PYINSTALLER_EXE=%~dp0.venv\Scripts\pyinstaller.exe
    echo 使用虚拟环境: .venv
) else (
    echo 使用系统Python
)
echo.

REM 检查Python是否可用
"!PYTHON_EXE!" --version >nul 2>nul
if !errorlevel! neq 0 (
    echo 错误: 未找到Python
    echo 请确保Python已安装并添加到系统PATH
    pause
    exit /b 1
)

echo 检查依赖项...
echo.

REM 检查pyinstaller是否安装
"!PYTHON_EXE!" -c "import PyInstaller" 2>nul
if !errorlevel! neq 0 (
    echo PyInstaller未安装，正在安装...
    "!PIP_EXE!" install pyinstaller
    if !errorlevel! neq 0 (
        echo 错误: 安装PyInstaller失败
        pause
        exit /b 1
    )
    echo PyInstaller安装成功！
    echo.
)

REM 检查python-dotenv是否安装
"!PYTHON_EXE!" -c "import dotenv" 2>nul
if !errorlevel! neq 0 (
    echo python-dotenv未安装，正在安装...
    "!PIP_EXE!" install python-dotenv
    if !errorlevel! neq 0 (
        echo 错误: 安装python-dotenv失败
        pause
        exit /b 1
    )
    echo python-dotenv安装成功！
    echo.
)

REM 检查.env文件
if not exist "%~dp0.env" (
    echo .env文件不存在，正在创建默认配置...
    echo SIMULATION_START_YEAR=2026 > "%~dp0.env"
    echo 已创建.env文件
    echo.
)

REM 检查图标文件
set ICON_OPTION=
if exist "%~dp0icon.ico" (
    set ICON_OPTION=--icon=icon.ico
    echo 找到图标文件
) else (
    echo icon.ico文件不存在，将不使用图标
)

REM 清理之前的构建文件
if exist "%~dp0build" (
    echo 清理build目录...
    rmdir /s /q "%~dp0build"
)
if exist "%~dp0dist" (
    echo 清理dist目录...
    rmdir /s /q "%~dp0dist"
)

echo.
echo 开始构建...
echo.

"!PYINSTALLER_EXE!" --name="2KDraftPicker" ^
    --windowed ^
    --onefile ^
    !ICON_OPTION! ^
    --add-data ".env;." ^
    --add-data "requirements.txt;." ^
    --hidden-import=dotenv ^
    --hidden-import=tkinter ^
    gui_main.py

if !errorlevel! neq 0 (
    echo 错误: 构建失败
    pause
    exit /b 1
)

echo.
echo ===============================================
echo  构建成功！
echo  可执行文件: dist\2KDraftPicker.exe
echo ===============================================
echo.
pause
