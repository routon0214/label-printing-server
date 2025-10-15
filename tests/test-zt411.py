#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZT411-300dpi 打印机快速测试脚本
直接使用你的 ZDesigner ZT411-300dpi 打印机进行测试
"""

import importlib.util
import sys

# 导入 zebra-print.py 模块（因为文件名包含连字符）
spec = importlib.util.spec_from_file_location("zebra_print", "zebra-print.py")
zebra_print = importlib.util.module_from_spec(spec)
spec.loader.exec_module(zebra_print)

# 使用导入的函数
ZebraPrinter = zebra_print.ZebraPrinter
create_simple_label = zebra_print.create_simple_label
create_zt411_high_res_label = zebra_print.create_zt411_high_res_label
create_zt411_asset_label = zebra_print.create_zt411_asset_label
create_chinese_label = zebra_print.create_chinese_label


def list_printers_and_select():
    """列出打印机并让用户选择"""
    try:
        import win32print
        
        printers = [printer[2] for printer in win32print.EnumPrinters(2)]
        
        if not printers:
            print("未找到可用的打印机！")
            return None
        
        print("\n系统中可用的打印机：")
        for i, printer in enumerate(printers, 1):
            default = win32print.GetDefaultPrinter()
            marker = " (默认)" if printer == default else ""
            print(f"{i}. {printer}{marker}")
        
        choice = input("\n请输入打印机编号（或按回车使用默认值）: ").strip()
        
        if not choice:
            # 检查是否有ZT411打印机
            zt411_printers = [p for p in printers if "ZT411" in p]
            if zt411_printers:
                return zt411_printers[0]
            else:
                return win32print.GetDefaultPrinter()
        elif choice.isdigit():
            index = int(choice) - 1
            if 0 <= index < len(printers):
                return printers[index]
            else:
                print(f"无效的编号！")
                return None
        else:
            return choice
            
    except Exception as e:
        print(f"获取打印机列表失败：{e}")
        return None


def print_test_label():
    """打印测试标签"""
    print("=" * 70)
    print("ZT411-300dpi 打印机测试")
    print("=" * 70)
    
    # 让用户选择打印机
    printer_name = list_printers_and_select()
    
    if not printer_name:
        print("\n未选择打印机，退出。")
        return
    
    print(f"\n使用打印机: {printer_name}")
    
    print("\n请选择要测试的标签：")
    print("1. 简单产品标签")
    print("2. 高分辨率产品标签")
    print("3. 资产标签")
    print("4. 中文标签（推荐）⭐")
    
    choice = input("\n请输入选项 (1-4，默认4): ").strip()
    
    if not choice:
        choice = "4"
    
    if choice == "1":
        zpl_code = create_simple_label()
        label_name = "简单产品标签"
    elif choice == "2":
        zpl_code = create_zt411_high_res_label()
        label_name = "高分辨率产品标签"
    elif choice == "3":
        zpl_code = create_zt411_asset_label()
        label_name = "资产标签"
    elif choice == "4":
        print("正在生成中文标签...")
        zpl_code = create_chinese_label()
        label_name = "中文标签"
    else:
        print("无效的选项！")
        return
    
    print(f"\n准备打印: {label_name}")
    print("\nZPL代码预览：")
    print("-" * 70)
    print(zpl_code)
    print("-" * 70)
    
    confirm = input("\n确认打印？(y/n，默认y): ").strip().lower()
    
    if confirm == 'n':
        print("已取消打印")
        return
    
    printer = ZebraPrinter()
    success = printer.print_via_usb(zpl_code, printer_name)
    
    if success:
        print("\n✓ 打印任务已发送到打印机！")
        print("请检查打印机输出。")
    else:
        print("\n✗ 打印失败！")
        print("\n可能的原因：")
        print("1. 打印机未正确连接或未开机")
        print("2. 打印机驱动未正确安装")
        print("3. 未安装 pywin32 库（运行: pip install pywin32）")
        print("4. 打印机处于错误状态（缺纸、卡纸等）")
        print("\n提示：请检查打印机状态并重试")


if __name__ == "__main__":
    try:
        print_test_label()
    except KeyboardInterrupt:
        print("\n\n测试已取消")
    except Exception as e:
        print(f"\n错误：{e}")
        import traceback
        traceback.print_exc()

