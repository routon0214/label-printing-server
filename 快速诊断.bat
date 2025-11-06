@echo off
chcp 65001 >nul
echo ========================================
echo 打印乱码问题诊断工具
echo ========================================
echo.
python scripts\diagnose_encoding.py
pause

