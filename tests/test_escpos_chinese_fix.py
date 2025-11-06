#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试ESC/POS打印机中文打印修复
"""

import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

from src.core.escpos_printer import ESCPOSPrinter
import json


def test_chinese_raw_text():
    """测试中文纯文本打印"""
    
    print("\n" + "="*70)
    print("测试 ESC/POS 中文纯文本打印")
    print("="*70)
    
    # 读取打印机配置
    config_file = os.path.join(project_root, 'config', 'printer_config.json')
    if not os.path.exists(config_file):
        print("错误：配置文件不存在")
        return False
    
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # 查找ESC/POS打印机配置
    escpos_printer_cfg = None
    for printer_cfg in config.get('printers', []):
        types = printer_cfg.get('types', [])
        if 'escpos' in types or 'receipt' in types:
            escpos_printer_cfg = printer_cfg
            break
    
    if not escpos_printer_cfg:
        print("警告：未找到ESC/POS打印机配置，使用默认配置")
        # 使用默认配置进行测试
        escpos_printer_cfg = {
            'name': 'ESC/POS Printer',
            'ip': '192.168.1.100',  # 请修改为您的打印机IP
            'port': 9100
        }
    
    print(f"\n打印机配置:")
    print(f"  名称: {escpos_printer_cfg.get('name')}")
    print(f"  IP: {escpos_printer_cfg.get('ip')}")
    print(f"  端口: {escpos_printer_cfg.get('port', 9100)}")
    
    # 创建打印机实例
    printer = ESCPOSPrinter(
        printer_ip=escpos_printer_cfg.get('ip'),
        printer_port=escpos_printer_cfg.get('port', 9100),
        printer_name=escpos_printer_cfg.get('name'),
        device_path=escpos_printer_cfg.get('device')
    )
    
    # 测试用例1：包含ZPL命令和中文的文本
    print("\n" + "-"*70)
    print("测试用例1：ZPL命令（包含中文）")
    print("-"*70)
    
    test_data_1 = {
        "print_type": "escpos",
        "raw_text": """SIZE 60 mm, 40 mm
GAP 1 mm, 0 mm
DIRECTION 1,0
REFERENCE 0,0
OFFSET 0 mm
CLS
TEXT 20,10,"TSS24.BF2",0,1,1,"容器类型"
QRCODE 20,60,L,10,A,0,M2,S6,"ECKQ"
TEXT 240,60,"TSS24.BF2",0,1,2,"二次库区托盘"
TEXT 240,120,"TSS24.BF2",0,1,2,"编号:ECKQ"
TEXT 240,170,"TSS24.BF2",0,1,2,"尺寸:null*0*null"
TEXT 240,220,"TSS24.BF2",0,1,2,"载重:0"
PRINT 1
""",
        "encoding": "gb2312"
    }
    
    result_1 = printer.print_receipt(test_data_1)
    print(f"\n测试结果: {'✓ 成功' if result_1 else '✗ 失败'}")
    
    # 测试用例2：简单中文文本
    print("\n" + "-"*70)
    print("测试用例2：简单中文文本")
    print("-"*70)
    
    test_data_2 = {
        "print_type": "escpos",
        "raw_text": """测试打印
商品A  15.00元
商品B  30.00元
商品C  45.00元
总计:  90.00元
谢谢惠顾！

""",
        "encoding": "gb2312"
    }
    
    result_2 = printer.print_receipt(test_data_2)
    print(f"\n测试结果: {'✓ 成功' if result_2 else '✗ 失败'}")
    
    # 测试用例3：中英文混合
    print("\n" + "-"*70)
    print("测试用例3：中英文混合")
    print("-"*70)
    
    test_data_3 = {
        "print_type": "escpos",
        "raw_text": """Receipt 销售小票
--------------------------------
Product A 产品A   x2   ¥15.50
Product B 产品B   x1   ¥30.00
--------------------------------
Total 总计:            ¥61.00
Thank you! 谢谢惠顾！

""",
        "encoding": "gb2312"
    }
    
    result_3 = printer.print_receipt(test_data_3)
    print(f"\n测试结果: {'✓ 成功' if result_3 else '✗ 失败'}")
    
    print("\n" + "="*70)
    print("测试完成")
    print("="*70)
    
    return result_1 and result_2 and result_3


if __name__ == '__main__':
    try:
        success = test_chinese_raw_text()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n测试出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

