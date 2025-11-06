@echo off
chcp 65001 >nul
echo ====================================
echo 斑马打印机MQTT标签打印服务
echo ====================================
echo.

REM 设置阿里云pip镜像源
set PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/
set PIP_TRUSTED_HOST=mirrors.aliyun.com

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误：未找到Python，请先安装Python 3.7+
    pause
    exit /b 1
)

echo 已配置使用阿里云pip镜像源
echo.

REM 检查虚拟环境是否存在
if not exist "venv" (
    echo 未找到虚拟环境，正在创建...
    python -m venv venv
    if errorlevel 1 (
        echo 虚拟环境创建失败
        pause
        exit /b 1
    )
    echo 虚拟环境创建成功！
    echo.
)

REM 激活虚拟环境
echo 正在激活虚拟环境...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo 虚拟环境激活失败
    pause
    exit /b 1
)
echo 虚拟环境已激活
echo.

REM 升级pip到最新版本
echo 正在升级pip...
python -m pip install --upgrade pip -i https://mirrors.aliyun.com/pypi/simple/
echo.

REM 检查依赖是否安装
echo 检查并安装依赖...
python -c "import paho.mqtt.client" >nul 2>&1
if errorlevel 1 (
    echo 首次运行，正在安装所有依赖...
    pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
    if errorlevel 1 (
        echo 依赖安装失败
        pause
        exit /b 1
    )
    echo 依赖安装完成！
) else (
    echo 依赖已安装
)

echo.
echo 启动服务...
echo.

REM 启动主程序（app.py内部已包含暂停功能）
python app.py

REM 如果程序正常退出（Ctrl+C），不需要额外暂停
REM 如果程序异常退出，app.py内部会暂停等待用户

