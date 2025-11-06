#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ESC/POS 中文打印测试
测试修复后的GB2312编码支持
"""

import sys
import os

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

from src.config import ConfigManager
from src.core.escpos_printer import ESCPOSPrinter


def test_raw_text_print():
    """测试原始文本打印（使用GB2312编码）"""
    print("="*70)
    print("测试1: 原始文本打印（GB2312编码）")
    print("="*70)
    
    # 加载配置
    config_manager = ConfigManager('config/printer_config.json')
    config = config_manager.load()
    
    # 查找ESC/POS打印机配置
    printers = config.get('printers', [])
    escpos_printer_config = None
    
    for printer in printers:
        if 'receipt' in printer.get('types', []) or 'escpos' in printer.get('types', []):
            escpos_printer_config = printer
            break
    
    if not escpos_printer_config:
        # 使用默认配置
        escpos_printer_config = config.get('printer', {})
    
    print(f"\n打印机配置:")
    print(f"  名称: {escpos_printer_config.get('name', '未设置')}")
    print(f"  IP: {escpos_printer_config.get('ip', '未设置')}")
    print(f"  端口: {escpos_printer_config.get('port', 9100)}")
    
    # 创建打印机实例
    printer = ESCPOSPrinter(
        printer_ip=escpos_printer_config.get('ip'),
        printer_port=escpos_printer_config.get('port', 9100),
        printer_name=escpos_printer_config.get('name'),
        device_path=escpos_printer_config.get('device')
    )
    
    # 测试文本（包含中文）
    test_text = """
中文打印测试
============

产品名称: 精密电子元件
型号: ZX-2025-PRO
序列号: SN20251106001
生产日期: 2025-11-06
质检员: 李明

测试内容:
1. 中文字符显示测试
2. English character test
3. 数字测试: 123456789
4. 符号测试: !@#$%^&*()

感谢使用！
"""
    
    # 打印数据
    receipt_data = {
        'raw_text': test_text,
        'encoding': 'gb2312'  # 使用GB2312编码
    }
    
    print("\n发送打印任务...")
    print(f"文本长度: {len(test_text)} 字符")
    print(f"编码方式: gb2312")
    print("-"*70)
    print(test_text)
    print("-"*70)
    
    confirm = input("\n确认打印? (y/n，默认n): ").strip().lower()
    if confirm != 'y':
        print("已取消")
        return False
    
    success = printer.print_receipt(receipt_data)
    
    if success:
        print("\n✓ 打印成功！")
        return True
    else:
        print("\n✗ 打印失败")
        return False


def test_structured_receipt():
    """测试结构化小票打印"""
    print("\n" + "="*70)
    print("测试2: 结构化小票打印")
    print("="*70)
    
    # 加载配置
    config_manager = ConfigManager('config/printer_config.json')
    config = config_manager.load()
    
    # 查找ESC/POS打印机配置
    printers = config.get('printers', [])
    escpos_printer_config = None
    
    for printer in printers:
        if 'receipt' in printer.get('types', []) or 'escpos' in printer.get('types', []):
            escpos_printer_config = printer
            break
    
    if not escpos_printer_config:
        escpos_printer_config = config.get('printer', {})
    
    # 创建打印机实例
    printer = ESCPOSPrinter(
        printer_ip=escpos_printer_config.get('ip'),
        printer_port=escpos_printer_config.get('port', 9100),
        printer_name=escpos_printer_config.get('name'),
        device_path=escpos_printer_config.get('device')
    )
    
    # 测试小票数据
    receipt_data = {
        "title": "购物小票",
        "items": [
            {"name": "苹果", "qty": 2, "price": 5.50},
            {"name": "香蕉", "qty": 3, "price": 3.00},
            {"name": "橙子", "qty": 1, "price": 8.00},
        ],
        "total": 27.00,
        "footer": "感谢惠顾，欢迎再次光临！",
        "barcode": "2025110600001"
    }
    
    print("\n小票内容:")
    print(f"  标题: {receipt_data['title']}")
    print(f"  商品数: {len(receipt_data['items'])}")
    print(f"  总计: ¥{receipt_data['total']}")
    
    confirm = input("\n确认打印? (y/n，默认n): ").strip().lower()
    if confirm != 'y':
        print("已取消")
        return False
    
    success = printer.print_receipt(receipt_data)
    
    if success:
        print("\n✓ 打印成功！")
        return True
    else:
        print("\n✗ 打印失败")
        return False


def main():
    """主函数"""
    print("="*70)
    print(" "*20 + "ESC/POS 中文打印测试")
    print("="*70)
    print("\n本测试用于验证GB2312编码修复")
    print("确保ESC/POS打印机已正确配置在 config/printer_config.json\n")
    
    # 检查配置
    if not os.path.exists('config/printer_config.json'):
        print("✗ 配置文件不存在: config/printer_config.json")
        print("请先配置打印机")
        input("\n按回车键退出...")
        return
    
    try:
        # 测试1: 原始文本打印
        test_raw_text_print()
        
        # 测试2: 结构化小票打印
        print("\n")
        choice = input("是否继续测试结构化小票打印? (y/n，默认n): ").strip().lower()
        if choice == 'y':
            test_structured_receipt()
        
        print("\n" + "="*70)
        print("测试完成")
        print("="*70)
        print("\n如果出现乱码，请检查:")
        print("  1. 打印机是否支持GB2312编码")
        print("  2. 打印机字符集设置是否正确")
        print("  3. 网络连接是否正常")
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    input("\n按回车键退出...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用户中断")
    except Exception as e:
        print(f"\n测试程序错误: {e}")
        import traceback
        traceback.print_exc()
        input("\n按回车键退出...")

