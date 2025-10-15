@echo off
chcp 65001 >nul
echo ====================================
echo 斑马打印机MQTT标签打印服务
echo ====================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误：未找到Python，请先安装Python 3.7+
    pause
    exit /b 1
)

REM 检查依赖是否安装
echo 检查依赖...
pip show paho-mqtt >nul 2>&1
if errorlevel 1 (
    echo 安装依赖...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo 依赖安装失败
        pause
        exit /b 1
    )
)

echo.
echo 启动服务...
echo.

REM 启动主程序
python app.py

pause

