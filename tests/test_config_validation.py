#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置验证测试
验证配置文件升级后的兼容性
"""

import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

from src.config import ConfigManager


def test_config_loading():
    """测试配置加载"""
    print("="*60)
    print("测试配置加载")
    print("="*60)
    
    config_manager = ConfigManager('config/printer_config.json')
    config = config_manager.load()
    
    print("\n✓ 配置加载成功")
    print(f"  MQTT: {config.get('mqtt', {}).get('host')}:{config.get('mqtt', {}).get('port')}")
    
    # 测试新格式
    printers = config.get('printers')
    if printers:
        print(f"\n✓ 多打印机配置 (新格式): {len(printers)} 台打印机")
        for i, printer in enumerate(printers, 1):
            name = printer.get('name', '未命名')
            types = printer.get('types', [])
            is_default = printer.get('default', False)
            print(f"  {i}. {name}")
            print(f"     类型: {types}")
            if is_default:
                print(f"     默认: ⭐")
    
    # 测试旧格式
    printer = config.get('printer')
    if printer:
        print(f"\n✓ 单打印机配置 (旧格式): {printer.get('name', '未命名')}")
    
    return True


def test_mqtt_client_init():
    """测试MQTT客户端初始化"""
    print("\n" + "="*60)
    print("测试MQTT客户端初始化")
    print("="*60)
    
    try:
        from core import LabelPrintMQTT
        
        config_manager = ConfigManager('config/printer_config.json')
        config = config_manager.load()
        
        mqtt_config = config.get('mqtt', {})
        printers_config = config.get('printers')
        printer_config = config.get('printer')
        
        # 创建客户端实例（不启动连接）
        client = LabelPrintMQTT(
            broker_host=mqtt_config.get('host', '127.0.0.1'),
            broker_port=mqtt_config.get('port', 1883),
            topic=mqtt_config.get('topic', 'zebra/print'),
            username=mqtt_config.get('username'),
            password=mqtt_config.get('password'),
            printer_config=printer_config,
            printers_config=printers_config
        )
        
        print("\n✓ MQTT客户端初始化成功")
        print(f"  打印机映射表: {list(client.printer_map.keys())}")
        
        return True
        
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("配置验证测试")
    print()
    
    success = True
    
    # 测试1: 配置加载
    try:
        if not test_config_loading():
            success = False
    except Exception as e:
        print(f"\n✗ 配置加载测试失败: {e}")
        import traceback
        traceback.print_exc()
        success = False
    
    # 测试2: MQTT客户端初始化
    try:
        if not test_mqtt_client_init():
            success = False
    except Exception as e:
        print(f"\n✗ MQTT客户端测试失败: {e}")
        import traceback
        traceback.print_exc()
        success = False
    
    # 总结
    print("\n" + "="*60)
    if success:
        print("✓ 所有测试通过")
    else:
        print("✗ 部分测试失败")
    print("="*60)
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())

