@echo off
chcp 65001 >nul
echo ============================================================
echo 一键修复ZPL中文乱码
echo ============================================================
echo.

if "%~1"=="" (
    echo 用法: 将ZPL文件拖放到此批处理文件上
    echo.
    echo 或者指定文件路径:
    echo   一键修复ZPL中文.bat data\print_text.txt
    echo.
    echo 功能:
    echo   1. 自动修复文件编码
    echo   2. 格式化换行符
    echo   3. 转换中文为图像
    echo.
    pause
    exit /b
)

set "input_file=%~1"

if not exist "%input_file%" (
    echo [错误] 文件不存在: %input_file%
    pause
    exit /b 1
)

python 一键修复ZPL中文.py "%input_file%"

echo.
echo ============================================================
pause

