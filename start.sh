#!/bin/bash

echo "===================================="
echo "斑马打印机MQTT标签打印服务"
echo "===================================="
echo

# 设置阿里云pip镜像源
export PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/
export PIP_TRUSTED_HOST=mirrors.aliyun.com

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误：未找到Python3，请先安装Python 3.7+"
    exit 1
fi

echo "已配置使用阿里云pip镜像源"
echo

# 检查虚拟环境是否存在
if [ ! -d "venv" ]; then
    echo "未找到虚拟环境，正在创建..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "虚拟环境创建失败"
        exit 1
    fi
    echo "虚拟环境创建成功！"
    echo
fi

# 激活虚拟环境
echo "正在激活虚拟环境..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "虚拟环境激活失败"
    exit 1
fi
echo "虚拟环境已激活"
echo

# 升级pip到最新版本
echo "正在升级pip..."
python -m pip install --upgrade pip -i https://mirrors.aliyun.com/pypi/simple/
echo

# 检查依赖是否安装
echo "检查并安装依赖..."
if ! python -c "import paho.mqtt.client" 2>/dev/null; then
    echo "首次运行，正在安装所有依赖..."
    pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
    if [ $? -ne 0 ]; then
        echo "依赖安装失败"
        exit 1
    fi
    echo "依赖安装完成！"
else
    echo "依赖已安装"
fi

echo
echo "启动服务..."
echo

# 启动主程序（app.py内部已包含暂停功能）
python app.py

# 如果程序正常退出（Ctrl+C），不需要额外暂停
# 如果程序异常退出，app.py内部会暂停等待用户

