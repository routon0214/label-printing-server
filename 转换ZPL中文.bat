@echo off
chcp 65001 >nul
echo ============================================================
echo ZPL中文转换工具
echo ============================================================
echo.

if "%~1"=="" (
    echo 用法: 将ZPL文件拖放到此批处理文件上
    echo.
    echo 或者指定文件路径:
    echo   转换ZPL中文.bat data\print_text.txt
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

echo 输入文件: %input_file%
echo.

python convert_zpl_chinese.py "%input_file%"

echo.
echo ============================================================
pause

