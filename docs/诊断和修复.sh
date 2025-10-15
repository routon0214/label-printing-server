#!/bin/bash

echo "===================================="
echo "程序诊断和修复工具"
echo "===================================="
echo

echo "[1/5] 检查Python版本..."
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未找到Python3，请先安装Python 3.7+"
    exit 1
fi
python3 --version
echo

echo "[2/5] 检查项目文件..."
if [ ! -f "app.py" ]; then
    echo "[错误] 未找到app.py，请在项目根目录运行此脚本"
    exit 1
fi
echo "[OK] 项目文件完整"
echo

echo "[3/5] 检查并创建必要目录..."
mkdir -p config logs failed_labels
echo "[OK] 目录结构完整"
echo

echo "[4/5] 检查依赖包..."
python3 tests/test_error_scenarios.py
echo

echo "[5/5] 诊断完成"
echo
echo "===================================="
echo "下一步操作："
echo "===================================="
echo
echo "如果测试全部通过："
echo "  python3 app.py"
echo
echo "如果有依赖包缺失："
echo "  pip3 install -r requirements.txt"
echo
echo "如果有其他问题："
echo "  查看上方的错误信息"
echo

