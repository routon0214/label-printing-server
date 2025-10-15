#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查 SumatraPDF 安装情况
"""

import os
import sys
import subprocess


def check_sumatra_pdf():
    """检查 SumatraPDF 安装路径"""
    print("="*70)
    print("检查 SumatraPDF 安装情况")
    print("="*70)
    
    # 获取用户目录
    user_profile = os.environ.get('USERPROFILE', '')
    print(f"\n用户目录: {user_profile}")
    
    # 所有可能的路径
    sumatra_paths = [
        r"C:\Program Files\SumatraPDF\SumatraPDF.exe",
        r"C:\Program Files (x86)\SumatraPDF\SumatraPDF.exe",
        os.path.join(user_profile, r"AppData\Local\SumatraPDF\SumatraPDF.exe") if user_profile else None,
        os.path.join(user_profile, r"AppData\Local\Programs\SumatraPDF\SumatraPDF.exe") if user_profile else None,
    ]
    
    # 过滤掉 None 值
    sumatra_paths = [p for p in sumatra_paths if p]
    
    print(f"\n检查以下路径:")
    print("-"*70)
    
    found_paths = []
    for path in sumatra_paths:
        exists = os.path.exists(path)
        status = "✓ 找到" if exists else "✗ 不存在"
        print(f"{status}: {path}")
        
        if exists:
            found_paths.append(path)
            # 获取文件信息
            try:
                size = os.path.getsize(path)
                print(f"       大小: {size:,} 字节 ({size/1024/1024:.2f} MB)")
            except:
                pass
    
    print("\n" + "="*70)
    
    if found_paths:
        print(f"✓ 找到 {len(found_paths)} 个 SumatraPDF 安装")
        print(f"将使用: {found_paths[0]}")
        
        # 测试调用
        print("\n测试 SumatraPDF 命令行...")
        try:
            result = subprocess.run(
                [found_paths[0], '-?'],
                capture_output=True,
                timeout=5
            )
            print(f"✓ SumatraPDF 可以正常调用")
            if result.stdout:
                print("\n命令行帮助信息:")
                print(result.stdout.decode('utf-8', errors='ignore')[:500])
        except Exception as e:
            print(f"⚠ 调用测试失败: {e}")
        
        return True
    else:
        print("✗ 未找到 SumatraPDF")
        print("\n请从以下位置下载并安装:")
        print("  https://www.sumatrapdfreader.org/")
        print("\n或者使用便携版解压到以下任意位置:")
        for path in sumatra_paths:
            print(f"  - {os.path.dirname(path)}")
        
        return False


def check_print_capability():
    """检查打印功能"""
    print("\n" + "="*70)
    print("检查打印机列表")
    print("="*70)
    
    try:
        import win32print
        
        # 获取默认打印机
        default_printer = win32print.GetDefaultPrinter()
        print(f"\n默认打印机: {default_printer}")
        
        # 列出所有打印机
        printers = win32print.EnumPrinters(2)
        print(f"\n系统中共有 {len(printers)} 台打印机:")
        print("-"*70)
        
        for i, printer_info in enumerate(printers, 1):
            printer_name = printer_info[2]
            is_default = " ⭐ (默认)" if printer_name == default_printer else ""
            print(f"{i}. {printer_name}{is_default}")
        
        return True
        
    except ImportError:
        print("⚠ 未安装 pywin32，无法列出打印机")
        print("安装命令: pip install pywin32")
        return False
    except Exception as e:
        print(f"✗ 获取打印机列表失败: {e}")
        return False


if __name__ == '__main__':
    print("\nSumatraPDF 和打印功能检查\n")
    
    sumatra_ok = check_sumatra_pdf()
    printer_ok = check_print_capability()
    
    print("\n" + "="*70)
    print("检查总结")
    print("="*70)
    print(f"SumatraPDF: {'✓ 可用' if sumatra_ok else '✗ 未安装'}")
    print(f"打印机:     {'✓ 可用' if printer_ok else '✗ 检查失败'}")
    
    if sumatra_ok and printer_ok:
        print("\n✓ PDF 静默打印功能已就绪")
    else:
        print("\n⚠ 需要完成上述配置才能使用 PDF 静默打印")
    
    print("="*70)

