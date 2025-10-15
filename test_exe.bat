@echo off
chcp 65001 >nul
echo 测试打包后的exe文件
echo ====================================
echo.

if not exist "dist\label-printing-server.exe" (
    echo 错误：找不到exe文件
    pause
    exit /b 1
)

echo 文件信息：
dir dist\label-printing-server.exe | findstr "label"
echo.

echo 启动测试（会自动退出）...
echo ====================================
echo.

REM 创建临时测试配置
mkdir dist\config 2>nul
echo {"mqtt":{"host":"127.0.0.1","port":1883},"printer":{"name":"test"}} > dist\config\printer_config.json

REM 启动exe（会因为MQTT连接失败而退出，但能验证依赖是否完整）
cd dist
start /wait label-printing-server.exe

echo.
echo 如果看到了程序输出和错误提示，说明依赖打包成功！
echo 如果直接闪退没有任何输出，说明还有依赖缺失。
echo.
pause

