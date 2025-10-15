#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
纸张匹配问题诊断工具
帮助解决"没有匹配到对应的纸张"错误
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def check_printer_settings():
    """检查打印机设置"""
    print("="*70)
    print("检查打印机纸张设置")
    print("="*70)
    
    try:
        import win32print
        
        # 获取所有打印机
        printers = win32print.EnumPrinters(2)
        default_printer = win32print.GetDefaultPrinter()
        
        print(f"\n默认打印机: {default_printer}")
        print("-"*70)
        
        # 检查每台打印机的纸张设置
        for printer_info in printers:
            printer_name = printer_info[2]
            
            if printer_name == default_printer or 'KONICA' in printer_name or 'ZT411' in printer_name:
                print(f"\n打印机: {printer_name}")
                print("-"*70)
                
                try:
                    # 获取打印机句柄
                    printer_handle = win32print.OpenPrinter(printer_name)
                    
                    # 获取打印机属性
                    printer_info_2 = win32print.GetPrinter(printer_handle, 2)
                    
                    # 获取 DEVMODE
                    if printer_info_2 and 'pDevMode' in printer_info_2:
                        devmode = printer_info_2['pDevMode']
                        
                        if devmode:
                            # 纸张大小
                            paper_size = devmode.PaperSize if hasattr(devmode, 'PaperSize') else "未知"
                            paper_width = devmode.PaperWidth if hasattr(devmode, 'PaperWidth') else "未知"
                            paper_length = devmode.PaperLength if hasattr(devmode, 'PaperLength') else "未知"
                            
                            print(f"  纸张大小代码: {paper_size}")
                            
                            # 常见纸张大小对照
                            paper_sizes = {
                                1: "Letter (8.5 x 11 英寸)",
                                5: "Legal (8.5 x 14 英寸)",
                                8: "A3 (297 x 420 毫米)",
                                9: "A4 (210 x 297 毫米)",
                                11: "A5 (148 x 210 毫米)",
                                256: "自定义"
                            }
                            
                            if paper_size in paper_sizes:
                                print(f"  纸张类型: {paper_sizes[paper_size]}")
                            
                            if paper_width != "未知" and paper_length != "未知":
                                width_mm = paper_width / 10
                                length_mm = paper_length / 10
                                print(f"  纸张尺寸: {width_mm:.1f} x {length_mm:.1f} 毫米")
                                print(f"           ({width_mm/25.4:.2f} x {length_mm/25.4:.2f} 英寸)")
                            
                            # 方向
                            orientation = devmode.Orientation if hasattr(devmode, 'Orientation') else "未知"
                            if orientation == 1:
                                print(f"  打印方向: 纵向")
                            elif orientation == 2:
                                print(f"  打印方向: 横向")
                    
                    win32print.ClosePrinter(printer_handle)
                    
                except Exception as e:
                    print(f"  ⚠ 无法获取详细信息: {e}")
        
        return True
        
    except ImportError:
        print("✗ 需要安装 pywin32")
        print("  运行: pip install pywin32")
        return False
    except Exception as e:
        print(f"✗ 检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def suggest_solutions():
    """提供解决方案建议"""
    print("\n" + "="*70)
    print("解决方案建议")
    print("="*70)
    
    print("\n【问题原因】")
    print("  打印机驱动配置的纸张大小与实际打印任务不匹配")
    
    print("\n【解决方案1】调整打印机默认纸张 ⭐ 推荐")
    print("-"*70)
    print("  1. 打开 Windows 设置 → 设备 → 打印机和扫描仪")
    print("  2. 选择对应的打印机 → 管理 → 打印首选项")
    print("  3. 设置纸张大小：")
    print("     - ZT411 标签打印机 → 设置为标签纸大小（如 4x6 英寸）")
    print("     - KONICA 文档打印机 → 设置为 A4 或 Letter")
    print("  4. 点击确定保存设置")
    
    print("\n【解决方案2】在打印时指定纸张大小")
    print("-"*70)
    print("  修改打印代码，添加纸张大小参数")
    print("  （需要修改 PDF 打印机代码）")
    
    print("\n【解决方案3】使用无边距打印模式")
    print("-"*70)
    print("  1. 打开打印机首选项")
    print("  2. 启用无边距打印或自动适应纸张")
    
    print("\n【解决方案4】禁用纸张大小检查（临时方案）")
    print("-"*70)
    print("  某些打印机驱动可以禁用纸张大小检查")
    print("  在打印机属性中查找相关选项")
    
    print("\n【针对不同打印类型的建议】")
    print("-"*70)
    print("  ZT411 标签打印机:")
    print("    - 设置纸张: 4x6 英寸 或对应的标签尺寸")
    print("    - 打印模式: 热敏/热转印")
    print("    - 不需要边距")
    
    print("\n  KONICA 文档打印机:")
    print("    - 设置纸张: A4 (210x297mm) 或 Letter (8.5x11英寸)")
    print("    - 默认即可")
    
    print("\n  小票打印机:")
    print("    - 设置纸张: 80mm 或 58mm 热敏纸")
    print("    - 连续纸模式")


def create_test_with_paper_size():
    """创建带纸张大小设置的测试"""
    print("\n" + "="*70)
    print("创建测试脚本（带纸张大小设置）")
    print("="*70)
    
    script_content = """#!/usr/bin/env python3
# -*- coding: utf-8 -*-
\"\"\"
带纸张设置的打印测试
\"\"\"

import win32print
import win32ui
from PIL import Image
import os

def print_with_paper_size(file_path, printer_name, paper_size_code=9):
    \"\"\"
    指定纸张大小打印
    
    Args:
        file_path: 文件路径
        printer_name: 打印机名称
        paper_size_code: 纸张大小代码
                        1 = Letter
                        9 = A4
                        256 = 自定义
    \"\"\"
    try:
        # 打开打印机
        hprinter = win32print.OpenPrinter(printer_name)
        
        # 获取默认 DEVMODE
        properties = win32print.GetPrinter(hprinter, 2)
        devmode = properties['pDevMode']
        
        # 设置纸张大小
        devmode.PaperSize = paper_size_code
        
        # 如果是自定义大小
        if paper_size_code == 256:
            # 设置自定义尺寸（以 0.1mm 为单位）
            devmode.PaperWidth = 2100  # 210mm = A4 宽度
            devmode.PaperLength = 2970  # 297mm = A4 高度
        
        print(f"打印机: {printer_name}")
        print(f"纸张代码: {paper_size_code}")
        print(f"文件: {file_path}")
        
        # 使用 SumatraPDF 打印（如果是 PDF）
        if file_path.lower().endswith('.pdf'):
            import subprocess
            sumatra_path = r"C:\\Users\\admin\\AppData\\Local\\SumatraPDF\\SumatraPDF.exe"
            
            if os.path.exists(sumatra_path):
                cmd = [
                    sumatra_path,
                    '-print-to', printer_name,
                    '-silent',
                    file_path
                ]
                result = subprocess.run(cmd, capture_output=True)
                if result.returncode == 0:
                    print("✓ 打印成功")
                    return True
                else:
                    print(f"✗ 打印失败: {result.returncode}")
                    return False
        
        win32print.ClosePrinter(hprinter)
        return True
        
    except Exception as e:
        print(f"✗ 打印失败: {e}")
        return False


if __name__ == '__main__':
    # 测试
    printer_name = "KONICA MINOLTA Universal PCL"
    file_path = "test_document_simple.pdf"
    
    # 使用 A4 纸张
    print_with_paper_size(file_path, printer_name, paper_size_code=9)
"""
    
    script_file = "tests/test_with_paper_size.py"
    with open(script_file, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print(f"✓ 已创建: {script_file}")
    print("  运行: python tests/test_with_paper_size.py")


def main():
    """主函数"""
    print("\n" + "="*70)
    print(" " * 15 + "纸张匹配问题诊断工具")
    print("="*70)
    
    # 检查打印机设置
    check_printer_settings()
    
    # 提供解决方案
    suggest_solutions()
    
    # 创建测试脚本
    print("\n是否创建带纸张大小设置的测试脚本？(y/N): ", end='')
    response = input()
    if response.lower() == 'y':
        create_test_with_paper_size()
    
    print("\n" + "="*70)
    print("诊断完成")
    print("="*70)
    print("\n下一步:")
    print("  1. 按照上述建议调整打印机设置")
    print("  2. 在打印机首选项中设置正确的纸张大小")
    print("  3. 重新运行打印测试")
    print("="*70)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

