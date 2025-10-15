#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 SumatraPDF 打印功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.pdf_printer import PDFPrinter


def test_pdf_print():
    """测试 PDF 打印"""
    print("="*70)
    print("测试 SumatraPDF 静默打印")
    print("="*70)
    
    # 检查是否有测试 PDF 文件
    test_pdf = "test_document_simple.pdf"
    if not os.path.exists(test_pdf):
        test_pdf = "绿色建筑评分标准.pdf"
    
    if not os.path.exists(test_pdf):
        print(f"\n⚠ 未找到测试 PDF 文件")
        print(f"请将 PDF 文件放到 tests/ 目录下")
        return False
    
    print(f"\n测试文件: {test_pdf}")
    print(f"文件大小: {os.path.getsize(test_pdf):,} 字节")
    
    # 询问用户要打印到哪台打印机
    print("\n可用的打印机:")
    try:
        import win32print
        printers = win32print.EnumPrinters(2)
        default_printer = win32print.GetDefaultPrinter()
        
        for i, printer_info in enumerate(printers, 1):
            printer_name = printer_info[2]
            is_default = " ⭐ (默认)" if printer_name == default_printer else ""
            print(f"  {i}. {printer_name}{is_default}")
        
        print(f"\n提示: 将使用默认打印机: {default_printer}")
        printer_to_use = default_printer
        
    except Exception as e:
        print(f"⚠ 无法列出打印机: {e}")
        printer_to_use = None
    
    # 创建 PDF 打印机实例
    pdf_printer = PDFPrinter(printer_name=printer_to_use)
    
    print("\n" + "="*70)
    print("开始打印测试")
    print("="*70)
    
    # 执行打印
    success = pdf_printer.print_pdf(test_pdf, printer_to_use)
    
    print("\n" + "="*70)
    if success:
        print("✓ 打印测试成功！")
        print("请检查打印机是否输出了文档。")
    else:
        print("✗ 打印测试失败")
        print("请查看上方的错误信息。")
    print("="*70)
    
    return success


if __name__ == '__main__':
    print("\n这将执行一次真实的打印测试")
    print("确保您的打印机已连接并准备好接收任务\n")
    
    input("按回车键继续测试...")
    
    success = test_pdf_print()
    
    sys.exit(0 if success else 1)

