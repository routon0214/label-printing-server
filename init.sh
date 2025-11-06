#!/bin/bash

echo "===================================="
echo "Label Printing Server - 项目初始化"
echo "===================================="
echo

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误：未找到Python3，请先安装Python 3.7+"
    echo
    echo "Ubuntu/Debian: sudo apt install python3 python3-pip python3-venv"
    echo "CentOS/RHEL: sudo yum install python3 python3-pip"
    echo "macOS: brew install python3"
    exit 1
fi

echo "开始初始化项目..."
echo

# 运行初始化脚本
python3 init.py

if [ $? -ne 0 ]; then
    echo
    echo "初始化失败，请查看上方错误信息"
    exit 1
fi

echo
echo "===================================="
echo "初始化成功完成！"
echo "===================================="
echo

