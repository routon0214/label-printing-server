@echo off
chcp 65001 >nul
cd /d "%~dp0"
title 标签打印代理
echo 启动标签打印代理 GUI...
start "" pythonw print_agent_gui.py
exit
