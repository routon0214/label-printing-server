#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试打印机优先级选择逻辑
验证专用打印机优先，通用打印机备选的机制
"""

import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

from src.config import ConfigManager
from src.core import LabelPrintMQTT


def test_printer_priority():
    """测试打印机优先级选择"""
    print("="*70)
    print("测试打印机优先级选择逻辑")
    print("="*70)
    
    # 加载配置
    config_manager = ConfigManager('config/printer_config.json')
    config = config_manager.load()
    
    mqtt_config = config.get('mqtt', {})
    printers_config = config.get('printers')
    
    # 显示配置
    print("\n当前配置:")
    print("-"*70)
    for i, p in enumerate(printers_config, 1):
        print(f"{i}. {p.get('name')} - types: {p.get('types')}")
    
    # 创建MQTT客户端
    print("\n" + "="*70)
    print("初始化MQTT客户端")
    print("="*70)
    
    client = LabelPrintMQTT(
        broker_host=mqtt_config.get('host', '127.0.0.1'),
        broker_port=mqtt_config.get('port', 1883),
        topic=mqtt_config.get('topic', 'zebra/print'),
        printers_config=printers_config
    )
    
    # 测试打印机选择
    print("\n" + "="*70)
    print("测试打印机选择逻辑")
    print("="*70)
    
    test_types = ['label', 'pdf', 'receipt']
    
    for print_type in test_types:
        print(f"\n请求打印类型: {print_type}")
        print("-"*70)
        
        # 获取打印机
        printer = client._get_printer(print_type)
        
        if printer:
            # 判断是专用还是备选
            if print_type in client.printer_map:
                source = "专用打印机"
                print(f"✓ 找到 {source}")
            elif client.fallback_printer_config:
                source = "备选打印机（通用）"
                print(f"✓ 找到 {source}")
            else:
                source = "未知"
            
            # 显示打印机信息
            if hasattr(printer, 'printer_name'):
                print(f"  打印机名称: {printer.printer_name}")
            if hasattr(printer, 'configured_name'):
                print(f"  配置名称: {printer.configured_name}")
            
        else:
            print(f"✗ 未找到打印机")
    
    # 显示打印机映射表
    print("\n" + "="*70)
    print("打印机映射表")
    print("="*70)
    print(f"\n专用打印机:")
    if client.printer_map:
        for pt, p in client.printer_map.items():
            if pt != 'escpos':  # 跳过别名
                print(f"  {pt}: {type(p).__name__}")
    else:
        print("  (无)")
    
    print(f"\n备选打印机配置:")
    if client.fallback_printer_config:
        name = client.fallback_printer_config.get('name', '自动检测')
        print(f"  名称: {name}")
        print(f"  支持: 所有类型")
    else:
        print("  (无)")
    
    print(f"\n已缓存的备选打印机实例:")
    if client.fallback_printers:
        for pt, p in client.fallback_printers.items():
            print(f"  {pt}: {type(p).__name__}")
    else:
        print("  (无)")
    
    return True


def test_scenarios():
    """测试不同配置场景"""
    print("\n" + "="*70)
    print("测试不同配置场景")
    print("="*70)
    
    scenarios = [
        {
            "name": "场景1: 有专用label打印机 + 通用打印机",
            "printers": [
                {"name": "ZT411", "types": ["label"]},
                {"name": "KONICA", "types": ["*"]},
            ],
            "expected": {
                "label": "专用",
                "pdf": "备选",
                "receipt": "备选"
            }
        },
        {
            "name": "场景2: 只有通用打印机",
            "printers": [
                {"name": "KONICA", "types": ["*"]},
            ],
            "expected": {
                "label": "备选",
                "pdf": "备选",
                "receipt": "备选"
            }
        },
        {
            "name": "场景3: 所有类型都有专用打印机",
            "printers": [
                {"name": "ZT411", "types": ["label"]},
                {"name": "HP", "types": ["pdf"]},
                {"name": "热敏", "types": ["receipt"]},
            ],
            "expected": {
                "label": "专用",
                "pdf": "专用",
                "receipt": "专用"
            }
        }
    ]
    
    all_passed = True
    
    for scenario in scenarios:
        print(f"\n{scenario['name']}")
        print("-"*70)
        
        try:
            client = LabelPrintMQTT(
                broker_host='127.0.0.1',
                broker_port=1883,
                topic='test/print',
                printers_config=scenario['printers']
            )
            
            for print_type, expected in scenario['expected'].items():
                printer = client._get_printer(print_type)
                
                if printer:
                    if print_type in client.printer_map:
                        actual = "专用"
                    else:
                        actual = "备选"
                    
                    status = "✓" if actual == expected else "✗"
                    print(f"  {status} {print_type}: {actual} (期望: {expected})")
                    
                    if actual != expected:
                        all_passed = False
                else:
                    print(f"  ✗ {print_type}: 未找到 (期望: {expected})")
                    all_passed = False
            
        except Exception as e:
            print(f"  ✗ 场景测试失败: {e}")
            all_passed = False
    
    return all_passed


def main():
    """主函数"""
    print("\n打印机优先级选择逻辑测试\n")
    
    # 测试1: 当前配置
    print("【测试1】当前配置测试")
    test_printer_priority()
    
    # 测试2: 不同场景
    print("\n\n【测试2】不同场景测试")
    all_passed = test_scenarios()
    
    # 总结
    print("\n" + "="*70)
    if all_passed:
        print("✓ 所有测试通过")
        print("\n新逻辑说明:")
        print("  1. 优先使用专用打印机（types: ['label']、['pdf']、['receipt']）")
        print("  2. 找不到专用打印机时，使用备选打印机（types: ['*']）")
        print("  3. 没有默认打印机的概念")
    else:
        print("✗ 部分测试失败")
    print("="*70)
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())

