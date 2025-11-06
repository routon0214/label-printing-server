#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试直接ZPL代码（包含中文）
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.core.printer import ZebraPrinter
from src.utils.zpl_chinese_converter import detect_and_convert_zpl

print("="*70)
print("测试直接ZPL代码（与Web输入完全相同）")
print("="*70)
print()

# 与Web完全相同的数据
original_zpl = "^XA^FO20,10^A0N,25,25^FD测试标签^FS^XZ"

print("原始ZPL代码:")
print(original_zpl)
print(f"长度: {len(original_zpl)} 字符")
print()

# 检测并转换中文（Web应用会做这一步）
print("步骤1: 检测并转换中文...")
converted_zpl, was_converted = detect_and_convert_zpl(original_zpl)

print()
print(f"转换结果: {'已转换' if was_converted else '无需转换'}")
print(f"转换后长度: {len(converted_zpl)} 字符")
print()

print("转换后的ZPL:")
print("="*70)
print(converted_zpl)
print("="*70)
print()

# 保存两个版本
with open('data/test_original.zpl', 'w', encoding='utf-8') as f:
    f.write(original_zpl)
print("原始ZPL保存: data/test_original.zpl")

with open('data/test_converted.zpl', 'w', encoding='utf-8') as f:
    f.write(converted_zpl)
print("转换后ZPL保存: data/test_converted.zpl")
print()

# 测试打印
print("="*70)
print("测试打印")
print("="*70)
print()

print("测试1: 打印原始ZPL（包含中文TEXT）")
choice = input("是否测试? (y/n): ").strip().lower()
if choice == 'y':
    printer = ZebraPrinter(printer_name="ZT411")
    result = printer.print_label(original_zpl)
    print(f"结果: {'成功发送' if result else '失败'}")
    if result:
        print("检查打印机: 中文可能显示为方块或空白（因为没转换）")

print()
print("测试2: 打印转换后的ZPL（中文转图像）")
choice = input("是否测试? (y/n): ").strip().lower()
if choice == 'y':
    printer = ZebraPrinter(printer_name="ZT411")
    result = printer.print_label(converted_zpl)
    print(f"结果: {'成功发送' if result else '失败'}")
    if result:
        print("检查打印机: 中文应该清晰显示（已转换为图像）")

print()
print("="*70)
print("结论")
print("="*70)
print()
print("如果测试2能正常显示中文:")
print("  → 说明中文转换功能正常")
print("  → Web应用应该也能工作")
print()
print("如果测试2也不行:")
print("  → 检查转换后的ZPL文件内容")
print("  → 查看是否包含^GFA图像命令")

