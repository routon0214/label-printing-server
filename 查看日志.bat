@echo off
chcp 65001 >nul
echo ============================================================
echo 查看MQTT日志 (UTF-8编码)
echo ============================================================
echo.

if not exist "data\logs" (
    echo [错误] 日志目录不存在
    pause
    exit /b 1
)

:: 获取最新的日志文件
for /f "delims=" %%i in ('dir /b /o-d "data\logs\mqtt_client_*.log" 2^>nul') do (
    set "latest_log=%%i"
    goto :found
)

:found
if "%latest_log%"=="" (
    echo [错误] 没有找到日志文件
    pause
    exit /b 1
)

echo 最新日志文件: %latest_log%
echo.
echo ============================================================
echo 最近50行日志:
echo ============================================================
echo.

powershell -NoProfile -Command "$OutputEncoding = [System.Text.Encoding]::UTF8; [Console]::OutputEncoding = [System.Text.Encoding]::UTF8; Get-Content 'data\logs\%latest_log%' -Tail 50 -Encoding UTF8"

echo.
echo ============================================================
echo 按任意键退出...
pause >nul

