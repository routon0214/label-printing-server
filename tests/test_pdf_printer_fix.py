#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 PDF 打印机名称解析修复
"""

import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

from src.core.pdf_printer import PDFPrinter


def test_printer_name_resolution():
    """测试打印机名称解析"""
    print("="*70)
    print("测试 PDF 打印机名称解析")
    print("="*70)
    
    # 测试用例
    test_cases = [
        ("KONICA", "应该匹配到 KONICA MINOLTA Universal PCL"),
        ("KONICA MINOLTA Universal PCL", "完整名称应该保持不变"),
        ("ZT411", "应该匹配到 ZDesigner ZT411-300dpi ZPL"),
        ("不存在的打印机", "应该返回原名称"),
    ]
    
    for printer_name, expected in test_cases:
        print(f"\n测试: '{printer_name}'")
        print(f"期望: {expected}")
        print("-"*70)
        
        pdf_printer = PDFPrinter(printer_name=printer_name)
        
        print(f"配置名称: {pdf_printer.configured_name}")
        print(f"解析名称: {pdf_printer.printer_name}")
        
        if pdf_printer.printer_name:
            print(f"✓ 成功解析")
        else:
            print(f"⚠ 解析为 None（将使用默认打印机）")


def test_pdf_print_with_fuzzy_match():
    """测试使用模糊匹配的 PDF 打印"""
    print("\n" + "="*70)
    print("测试使用模糊名称的 PDF 打印初始化")
    print("="*70)
    
    # 使用简短名称 "KONICA" 创建 PDF 打印机
    print("\n使用配置名称: 'KONICA'")
    pdf_printer = PDFPrinter(printer_name="KONICA")
    
    print(f"配置名称: {pdf_printer.configured_name}")
    print(f"实际打印机: {pdf_printer.printer_name}")
    
    if pdf_printer.printer_name and "KONICA MINOLTA" in pdf_printer.printer_name:
        print("\n✓ 成功！模糊匹配工作正常")
        print(f"✓ 'KONICA' 正确解析为 '{pdf_printer.printer_name}'")
        print("✓ SumatraPDF 将使用完整的打印机名称")
        return True
    else:
        print("\n✗ 失败！模糊匹配没有工作")
        return False


def main():
    """主函数"""
    print("\nPDF 打印机名称解析修复测试\n")
    
    # 测试1: 名称解析
    test_printer_name_resolution()
    
    # 测试2: 实际应用场景
    success = test_pdf_print_with_fuzzy_match()
    
    print("\n" + "="*70)
    if success:
        print("✓ 修复成功！现在可以使用简短名称 'KONICA' 进行 PDF 打印")
        print("  系统会自动解析为完整名称 'KONICA MINOLTA Universal PCL'")
        print("  SumatraPDF 将收到正确的打印机名称")
    else:
        print("✗ 测试失败，请检查模糊匹配功能")
    print("="*70)
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())

