@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 启动本地打印代理...
python print_agent.py
echo.
echo 代理已退出，按任意键关闭...
pause >nul
