#!/bin/bash

echo "===================================="
echo "斑马打印机MQTT标签打印服务"
echo "===================================="
echo

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误：未找到Python3，请先安装Python 3.7+"
    exit 1
fi

# 检查依赖是否安装
echo "检查依赖..."
if ! python3 -c "import paho.mqtt.client" 2>/dev/null; then
    echo "安装依赖..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "依赖安装失败"
        exit 1
    fi
fi

echo
echo "启动服务..."
echo

# 启动主程序（app.py内部已包含暂停功能）
python3 app.py

# 如果程序正常退出（Ctrl+C），不需要额外暂停
# 如果程序异常退出，app.py内部会暂停等待用户

