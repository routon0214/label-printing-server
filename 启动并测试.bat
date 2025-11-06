@echo off
chcp 65001 >nul
echo ============================================================
echo 启动Web服务并打开测试页面
echo ============================================================
echo.

echo [1/3] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python未安装或不在PATH中
    pause
    exit /b 1
)
echo [OK] Python环境正常
echo.

echo [2/3] 检查依赖...
python -c "import fastapi, uvicorn" >nul 2>&1
if errorlevel 1 (
    echo [WARNING] 缺少依赖，正在安装...
    pip install -r requirements.txt
)
echo [OK] 依赖完整
echo.

echo [3/3] 启动Web服务...
echo.
echo ============================================================
echo Web服务地址: http://127.0.0.1:5000
echo 用户名: admin
echo 密码: admin
echo ============================================================
echo.
echo 测试文件位置: data\test_samples\
echo   - zd888_english.zpl        (纯英文)
echo   - zd888_chinese_simple.json (简单中文)
echo   - zd888_chinese_mixed.json  (中英混合)
echo   - escpos_chinese.json       (ESC/POS小票)
echo.
echo ============================================================
echo 提示: 
echo   - 按 Ctrl+C 停止服务
echo   - 浏览器打开 http://127.0.0.1:5000
echo   - 查看控制台输出了解打印状态
echo ============================================================
echo.

REM 启动浏览器（后台）
start http://127.0.0.1:5000

REM 启动Web服务
python web_app.py

pause

