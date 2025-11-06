@echo off
chcp 65001 >nul
echo ====================================
echo Label Printing Server - 项目初始化
echo ====================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误：未找到Python，请先安装Python 3.7+
    echo.
    echo 下载地址: https://www.python.org/downloads/
    echo 安装时请勾选 "Add Python to PATH"
    pause
    exit /b 1
)

echo 开始初始化项目...
echo.

REM 运行初始化脚本
python init.py

if errorlevel 1 (
    echo.
    echo 初始化失败，请查看上方错误信息
    pause
    exit /b 1
)

echo.
echo ====================================
echo 初始化成功完成！
echo ====================================
echo.
pause

