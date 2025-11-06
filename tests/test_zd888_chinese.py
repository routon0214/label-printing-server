#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZD888 中文打印测试
针对 ZDesigner ZD888-203dpi ZPL 打印机
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.core.printer import ZebraPrinter
from src.core.zpl_generator import ZPLGenerator


def test_english_only():
    """测试1: 纯英文（确认基础功能）"""
    print("="*70)
    print("测试1: 纯英文打印")
    print("="*70)
    
    zpl = """^XA
^FO50,50^A0N,40,40^FDEnglish Test^FS
^FO50,100^A0N,30,30^FDPrint Success^FS
^FO50,150^BCN,80,Y,N,N^FD123456^FS
^XZ"""
    
    print("\nZPL代码:")
    print(zpl)
    
    confirm = input("\n打印到ZD888? (y/n): ").strip().lower()
    if confirm == 'y':
        printer = ZebraPrinter(printer_name="ZD888")
        success = printer.print_label(zpl)
        if success:
            print("[OK] 发送成功! 请检查打印机输出")
        else:
            print("[ERROR] 发送失败")
    else:
        print("已跳过")


def test_chinese_simple():
    """测试2: 简单中文（小图像）"""
    print("\n" + "="*70)
    print("测试2: 简单中文打印 (小图像)")
    print("="*70)
    
    # 使用JSON数据生成
    data = {
        "title": "测试",
        "fields": [
            {"label": "名称", "value": "产品A", "font_size": 25}
        ]
    }
    
    print("\n生成ZPL代码...")
    generator = ZPLGenerator()
    zpl = generator.generate_label_zpl(data)
    
    print(f"ZPL长度: {len(zpl)} 字符")
    print(f"预览: {zpl[:200]}...")
    
    confirm = input("\n打印到ZD888? (y/n): ").strip().lower()
    if confirm == 'y':
        printer = ZebraPrinter(printer_name="ZD888")
        success = printer.print_label(zpl)
        if success:
            print("[OK] 发送成功! 请检查打印机输出")
            print("\n检查项:")
            print("  - 标签上是否有'测试'两个字")
            print("  - 是否有'名称：产品A'")
            print("  - 中文是否清晰")
        else:
            print("[ERROR] 发送失败")
    else:
        print("已跳过")


def test_chinese_mixed():
    """测试3: 中英文混合"""
    print("\n" + "="*70)
    print("测试3: 中英文混合打印")
    print("="*70)
    
    data = {
        "title": "Product 产品",
        "fields": [
            {"label": "Name", "value": "Component-A", "font_size": 28},
            {"label": "名称", "value": "电子元件", "font_size": 28},
            {"label": "Serial", "value": "SN-2025-001", "font_size": 25}
        ],
        "barcode": "SN2025001"
    }
    
    print("\n生成ZPL代码...")
    generator = ZPLGenerator()
    zpl = generator.generate_label_zpl(data)
    
    print(f"ZPL长度: {len(zpl)} 字符")
    
    # 保存到文件
    filename = "data/zd888_mixed_test.zpl"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(zpl)
    print(f"已保存到: {filename}")
    
    confirm = input("\n打印到ZD888? (y/n): ").strip().lower()
    if confirm == 'y':
        printer = ZebraPrinter(printer_name="ZD888")
        success = printer.print_label(zpl)
        if success:
            print("[OK] 发送成功! 请检查打印机输出")
            print("\n应该能看到:")
            print("  - 标题: 'Product 产品'")
            print("  - Name: Component-A")
            print("  - 名称: 电子元件")
            print("  - Serial: SN-2025-001")
            print("  - 条形码")
        else:
            print("[ERROR] 发送失败")
    else:
        print("已跳过")


def test_chinese_only():
    """测试4: 纯中文（完整标签）"""
    print("\n" + "="*70)
    print("测试4: 纯中文打印 (完整标签)")
    print("="*70)
    
    data = {
        "title": "产品标签",
        "fields": [
            {"label": "产品名称", "value": "精密电子元件", "font_size": 28},
            {"label": "产品型号", "value": "型号甲", "font_size": 25},
            {"label": "生产日期", "value": "二零二五年", "font_size": 22},
            {"label": "质检员", "value": "张三", "font_size": 22}
        ],
        "barcode": "20251106001"
    }
    
    print("\n生成ZPL代码...")
    generator = ZPLGenerator()
    zpl = generator.generate_label_zpl(data)
    
    print(f"ZPL长度: {len(zpl)} 字符")
    
    # 保存到文件
    filename = "data/zd888_chinese_test.zpl"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(zpl)
    print(f"已保存到: {filename}")
    
    confirm = input("\n打印到ZD888? (y/n): ").strip().lower()
    if confirm == 'y':
        printer = ZebraPrinter(printer_name="ZD888")
        success = printer.print_label(zpl)
        if success:
            print("[OK] 发送成功! 请检查打印机输出")
            print("\n如果中文显示正常，说明一切OK!")
            print("如果中文是空白或方块，请检查:")
            print("  1. 确认已安装Pillow: pip install Pillow")
            print("  2. 确认有中文字体: C:\\Windows\\Fonts\\msyh.ttc")
            print("  3. 查看生成的ZPL文件确认包含^GFA命令")
        else:
            print("[ERROR] 发送失败")
    else:
        print("已跳过")


def check_printer():
    """检查打印机状态"""
    print("="*70)
    print("检查ZD888打印机")
    print("="*70)
    print()
    
    try:
        import win32print
        
        printers = [p[2] for p in win32print.EnumPrinters(2)]
        
        print(f"系统中有 {len(printers)} 台打印机:")
        for i, name in enumerate(printers, 1):
            print(f"  {i}. {name}")
        
        print()
        
        # 查找ZD888
        zd888 = [p for p in printers if 'ZD888' in p or 'zd888' in p.lower()]
        
        if zd888:
            print(f"[OK] 找到ZD888打印机: {zd888[0]}")
            
            # 检查状态
            try:
                handle = win32print.OpenPrinter(zd888[0])
                info = win32print.GetPrinter(handle, 2)
                
                status = info['Status']
                if status == 0:
                    print("[OK] 打印机状态: 正常")
                else:
                    print(f"[WARNING] 打印机状态码: {status}")
                
                # 检查队列
                jobs = win32print.EnumJobs(handle, 0, -1, 1)
                if jobs:
                    print(f"[INFO] 队列中有 {len(jobs)} 个任务")
                else:
                    print("[OK] 打印队列为空")
                
                win32print.ClosePrinter(handle)
            except Exception as e:
                print(f"[WARNING] 无法检查详细状态: {e}")
        else:
            print("[WARNING] 未找到ZD888打印机")
            print("请确认打印机名称包含'ZD888'")
    
    except ImportError:
        print("[ERROR] 需要安装 pywin32: pip install pywin32")
    except Exception as e:
        print(f"[ERROR] 检查失败: {e}")


def main():
    """主测试流程"""
    print("\n" + "="*70)
    print("ZD888 中文打印测试套件")
    print("="*70)
    print()
    print("打印机型号: ZDesigner ZD888-203dpi ZPL")
    print()
    print("测试计划:")
    print("  1. 纯英文测试 (确认基础功能)")
    print("  2. 简单中文测试 (小图像)")
    print("  3. 中英文混合测试")
    print("  4. 纯中文测试 (完整标签)")
    print()
    
    while True:
        print("-" * 70)
        print("选项:")
        print("  1. 测试纯英文")
        print("  2. 测试简单中文")
        print("  3. 测试中英文混合")
        print("  4. 测试纯中文")
        print("  5. 检查打印机状态")
        print("  6. 运行全部测试")
        print("  0. 退出")
        print()
        
        choice = input("请选择 (0-6): ").strip()
        
        if choice == '0':
            break
        elif choice == '1':
            test_english_only()
        elif choice == '2':
            test_chinese_simple()
        elif choice == '3':
            test_chinese_mixed()
        elif choice == '4':
            test_chinese_only()
        elif choice == '5':
            check_printer()
        elif choice == '6':
            print("\n开始全部测试...")
            test_english_only()
            test_chinese_simple()
            test_chinese_mixed()
            test_chinese_only()
            print("\n全部测试完成!")
        else:
            print("无效选项")
        
        input("\n按回车继续...")
    
    print("\n测试结束!")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n已中断")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()

