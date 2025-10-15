@echo off
chcp 65001 >nul
echo ====================================
echo Windows 平台打包脚本
echo ====================================
echo.

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误：未找到Python
    pause
    exit /b 1
)

echo 开始打包...
echo.

REM 运行打包脚本
python build.py

if errorlevel 1 (
    echo.
    echo 打包失败！
    pause
    exit /b 1
)

echo.
echo 打包成功！
echo.
echo 输出目录: dist\windows-*\
echo.

pause

