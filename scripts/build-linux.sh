#!/bin/bash

echo "===================================="
echo "Linux 平台打包脚本"
echo "===================================="
echo

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "错误：未找到Python3"
    exit 1
fi

echo "开始打包..."
echo

# 运行打包脚本
python3 build.py

if [ $? -ne 0 ]; then
    echo
    echo "打包失败！"
    exit 1
fi

echo
echo "打包成功！"
echo
echo "输出目录: dist/linux-*/"
echo

# 设置可执行权限
if [ -f dist/linux-*/label-printing-server/label-printing-server ]; then
    chmod +x dist/linux-*/label-printing-server/label-printing-server
    echo "✓ 已设置可执行权限"
fi

echo
echo "完成！"

