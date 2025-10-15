#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
带纸张设置的打印测试
"""

import win32print
import win32ui
from PIL import Image
import os

def print_with_paper_size(file_path, printer_name, paper_size_code=9):
    """
    指定纸张大小打印
    
    Args:
        file_path: 文件路径
        printer_name: 打印机名称
        paper_size_code: 纸张大小代码
                        1 = Letter
                        9 = A4
                        256 = 自定义
    """
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
            sumatra_path = r"C:\Users\admin\AppData\Local\SumatraPDF\SumatraPDF.exe"
            
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
