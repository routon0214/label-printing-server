#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试禁用 SumatraPDF 的打印（使用备用方案）
验证在没有 SumatraPDF 时打印是否正常
"""

import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))


def test_print_without_sumatra():
    """测试不使用 SumatraPDF 的打印"""
    print("="*70)
    print("测试备用打印方案（不使用 SumatraPDF）")
    print("="*70)
    
    # 临时重命名 SumatraPDF 路径
    import src.core.pdf_printer as pdf_module
    
    # 保存原始路径检查函数
    original_exists = os.path.exists
    
    # 创建一个修改版的 exists 函数，让它找不到 SumatraPDF
    def mock_exists(path):
        if 'SumatraPDF' in str(path):
            return False  # 假装找不到 SumatraPDF
        return original_exists(path)
    
    # 临时替换
    os.path.exists = mock_exists
    
    try:
        from src.core.pdf_printer import PDFPrinter
        import base64
        
        print("\n测试 PDF 打印（无 SumatraPDF）")
        print("-"*70)
        
        # 创建 PDF 打印机
        pdf_printer = PDFPrinter(printer_name="KONICA")
        
        # 准备测试文件
        test_file = "tests/test_document_simple.pdf"
        if os.path.exists(test_file):
            # 读取并编码
            with open(test_file, 'rb') as f:
                pdf_base64 = base64.b64encode(f.read()).decode('utf-8')
            
            # 尝试打印
            print("\n开始打印...")
            success = pdf_printer.print_pdf(pdf_base64)
            
            print("\n" + "="*70)
            if success:
                print("✓ 备用打印方案成功！")
                print("\n说明:")
                print("  - SumatraPDF 被禁用")
                print("  - 使用了备用打印方案（Adobe Reader/notepad/win32print）")
                print("  - 打印成功，说明备用方案工作正常")
            else:
                print("✗ 备用打印方案失败")
            print("="*70)
            
            return success
        else:
            print(f"✗ 测试文件不存在: {test_file}")
            return False
    
    finally:
        # 恢复原始函数
        os.path.exists = original_exists


def compare_with_sumatra():
    """对比使用和不使用 SumatraPDF 的结果"""
    print("\n\n" + "="*70)
    print("对比测试：SumatraPDF vs 备用方案")
    print("="*70)
    
    from src.core.pdf_printer import PDFPrinter
    import base64
    
    test_file = "tests/test_document_simple.pdf"
    if not os.path.exists(test_file):
        print("✗ 测试文件不存在")
        return
    
    with open(test_file, 'rb') as f:
        pdf_base64 = base64.b64encode(f.read()).decode('utf-8')
    
    # 测试1: 使用 SumatraPDF（如果有）
    print("\n[测试1] 使用 SumatraPDF")
    print("-"*70)
    pdf_printer = PDFPrinter(printer_name="KONICA")
    result1 = pdf_printer.print_pdf(pdf_base64)
    print(f"结果: {'✓ 成功' if result1 else '✗ 失败'}")
    
    print("\n[总结]")
    print("-"*70)
    print("如果 SumatraPDF 打印失败:")
    print("  1. 程序会自动尝试备用方案")
    print("  2. 备用方案包括: Adobe Reader, notepad, win32print")
    print("  3. 或者可以临时禁用/卸载 SumatraPDF，使用备用方案")


def main():
    """主函数"""
    print("\n备用打印方案测试工具\n")
    
    print("说明:")
    print("  此工具用于测试在没有 SumatraPDF 时的打印功能")
    print("  帮助诊断 SumatraPDF 引起的纸张匹配问题")
    print()
    
    # 测试不使用 SumatraPDF
    success = test_print_without_sumatra()
    
    # 对比测试
    # compare_with_sumatra()
    
    print("\n" + "="*70)
    print("建议")
    print("="*70)
    print("\n如果备用方案打印成功，但 SumatraPDF 失败:")
    print("  方案1: 临时禁用 SumatraPDF")
    print("    重命名: SumatraPDF.exe -> SumatraPDF.exe.bak")
    print()
    print("  方案2: 修改打印机设置")
    print("    在 KONICA 打印首选项中启用纸张自适应")
    print()
    print("  方案3: 使用配置禁用 SumatraPDF")
    print("    在配置文件中添加 use_sumatra: false")
    print("="*70)
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())

