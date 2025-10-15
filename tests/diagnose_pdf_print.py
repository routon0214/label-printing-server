#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF 打印诊断工具
帮助排查 SumatraPDF 打印问题
"""

import os
import sys
import subprocess
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def find_sumatra_pdf():
    """查找 SumatraPDF"""
    user_profile = os.environ.get('USERPROFILE', '')
    
    sumatra_paths = [
        r"C:\Program Files\SumatraPDF\SumatraPDF.exe",
        r"C:\Program Files (x86)\SumatraPDF\SumatraPDF.exe",
        os.path.join(user_profile, r"AppData\Local\SumatraPDF\SumatraPDF.exe") if user_profile else None,
        os.path.join(user_profile, r"AppData\Local\Programs\SumatraPDF\SumatraPDF.exe") if user_profile else None,
    ]
    
    sumatra_paths = [p for p in sumatra_paths if p]
    
    for path in sumatra_paths:
        if os.path.exists(path):
            return path
    return None


def get_printers():
    """获取打印机列表"""
    try:
        import win32print
        printers = []
        default_printer = win32print.GetDefaultPrinter()
        
        for printer_info in win32print.EnumPrinters(2):
            printer_name = printer_info[2]
            printers.append({
                'name': printer_name,
                'is_default': printer_name == default_printer
            })
        
        return printers, default_printer
    except Exception as e:
        print(f"✗ 获取打印机列表失败: {e}")
        return [], None


def create_test_pdf():
    """创建测试 PDF 文件"""
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        
        # 创建临时 PDF
        temp_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
        temp_file.close()
        
        c = canvas.Canvas(temp_file.name, pagesize=A4)
        c.setFont("Helvetica", 20)
        c.drawString(100, 750, "SumatraPDF Print Test")
        c.setFont("Helvetica", 12)
        c.drawString(100, 700, "This is a test document for PDF printing.")
        c.drawString(100, 680, "If you can see this, the print was successful!")
        c.save()
        
        return temp_file.name
    except ImportError:
        print("⚠ reportlab 未安装，尝试使用现有 PDF 文件")
        
        # 尝试查找现有的 PDF 文件
        test_files = [
            "tests/test_document_simple.pdf",
            "tests/绿色建筑评分标准.pdf",
        ]
        
        for f in test_files:
            if os.path.exists(f):
                return f
        
        return None


def test_sumatra_command(sumatra_path, printer_name, pdf_file):
    """测试 SumatraPDF 打印命令"""
    print("\n" + "="*70)
    print("测试 SumatraPDF 打印命令")
    print("="*70)
    
    cmd = [
        sumatra_path,
        '-print-to', printer_name,
        '-silent',
        pdf_file
    ]
    
    print(f"\n执行命令:")
    print(f"  {' '.join(cmd)}")
    print(f"\n命令参数详解:")
    print(f"  程序: {sumatra_path}")
    print(f"  -print-to: 指定打印机")
    print(f"  打印机名称: '{printer_name}'")
    print(f"  -silent: 静默模式")
    print(f"  PDF文件: {pdf_file}")
    
    print(f"\n开始执行...")
    print("-"*70)
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=30,
            text=True
        )
        
        print(f"返回码: {result.returncode}")
        
        if result.stdout:
            print(f"\n标准输出:")
            print(result.stdout)
        
        if result.stderr:
            print(f"\n标准错误:")
            print(result.stderr)
        
        print("-"*70)
        
        if result.returncode == 0:
            print("✓ 命令执行成功")
            return True
        else:
            print(f"✗ 命令返回错误码: {result.returncode}")
            
            # 分析错误码
            if result.returncode == 1:
                print("\n错误码 1 通常表示:")
                print("  - 打印机名称不匹配")
                print("  - 打印机不可用或离线")
                print("  - 文件无法读取")
            
            return False
            
    except subprocess.TimeoutExpired:
        print("✗ 命令超时（30秒）")
        return False
    except Exception as e:
        print(f"✗ 执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_printer_name_variants(sumatra_path, base_printer_name, pdf_file):
    """测试打印机名称的不同变体"""
    print("\n" + "="*70)
    print("测试打印机名称变体")
    print("="*70)
    
    # 不同的打印机名称格式
    variants = [
        base_printer_name,  # 原始名称
        base_printer_name.strip(),  # 去除空格
        f'"{base_printer_name}"',  # 添加引号
    ]
    
    for i, variant in enumerate(variants, 1):
        print(f"\n尝试 {i}/{len(variants)}: {variant}")
        print("-"*70)
        
        cmd = [sumatra_path, '-print-to', variant, '-silent', pdf_file]
        
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=10)
            
            if result.returncode == 0:
                print(f"✓ 成功！使用此格式: {variant}")
                return variant
            else:
                print(f"✗ 失败，返回码: {result.returncode}")
        except Exception as e:
            print(f"✗ 错误: {e}")
    
    return None


def main():
    """主函数"""
    print("="*70)
    print(" " * 20 + "PDF 打印诊断工具")
    print("="*70)
    
    # 1. 查找 SumatraPDF
    print("\n[1/5] 查找 SumatraPDF...")
    sumatra_path = find_sumatra_pdf()
    
    if not sumatra_path:
        print("✗ 未找到 SumatraPDF")
        print("请先安装 SumatraPDF: https://www.sumatrapdfreader.org/")
        return 1
    
    print(f"✓ 找到: {sumatra_path}")
    
    # 2. 获取打印机列表
    print("\n[2/5] 获取打印机列表...")
    printers, default_printer = get_printers()
    
    if not printers:
        print("✗ 未找到打印机")
        return 1
    
    print(f"✓ 找到 {len(printers)} 台打印机")
    print(f"默认打印机: {default_printer}")
    
    for i, p in enumerate(printers, 1):
        mark = " ⭐" if p['is_default'] else ""
        print(f"  {i}. {p['name']}{mark}")
    
    # 3. 创建测试 PDF
    print("\n[3/5] 准备测试 PDF 文件...")
    pdf_file = create_test_pdf()
    
    if not pdf_file:
        print("✗ 无法创建测试 PDF")
        return 1
    
    print(f"✓ 测试文件: {pdf_file}")
    print(f"  大小: {os.path.getsize(pdf_file):,} 字节")
    
    # 4. 测试默认打印机
    if default_printer:
        success = test_sumatra_command(sumatra_path, default_printer, pdf_file)
        
        if not success:
            print("\n尝试打印机名称变体...")
            working_name = test_printer_name_variants(sumatra_path, default_printer, pdf_file)
            
            if working_name:
                print(f"\n✓ 找到有效的打印机名称格式: {working_name}")
            else:
                print("\n✗ 所有名称格式都失败了")
    
    # 5. 建议
    print("\n" + "="*70)
    print("诊断建议")
    print("="*70)
    
    print("\n如果打印失败，请检查:")
    print("  1. 打印机是否在线并准备就绪")
    print("  2. 打印机驱动是否正确安装")
    print("  3. 在 Windows 设置中能否正常打印测试页")
    print("  4. 打印机名称是否完全匹配（区分大小写）")
    
    print("\n配置文件中的打印机名称应该完全匹配系统中的名称:")
    print(f'  "name": "{default_printer}"')
    
    # 清理临时文件
    if pdf_file and pdf_file.startswith(tempfile.gettempdir()):
        try:
            os.remove(pdf_file)
        except:
            pass
    
    print("\n" + "="*70)
    print("诊断完成")
    print("="*70)
    
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n诊断已中断")
        sys.exit(1)

