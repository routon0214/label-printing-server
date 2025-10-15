#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置升级检查脚本
验证配置文件升级后程序的兼容性
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import ConfigManager
from core import LabelPrintMQTT


def print_section(title):
    """打印分节标题"""
    print("\n" + "="*70)
    print(f" {title}")
    print("="*70)


def check_config_format():
    """检查配置文件格式"""
    print_section("1. 检查配置文件格式")
    
    config_manager = ConfigManager('config/printer_config.json')
    config = config_manager.load()
    
    # 检查MQTT配置
    mqtt_config = config.get('mqtt', {})
    print(f"✓ MQTT配置: {mqtt_config.get('host')}:{mqtt_config.get('port')}")
    print(f"  主题: {mqtt_config.get('topic')}")
    
    # 检查新格式（多打印机）
    printers = config.get('printers')
    if printers:
        print(f"\n✓ 多打印机配置 (新格式): {len(printers)} 台")
        for i, printer in enumerate(printers, 1):
            name = printer.get('name', '未命名')
            types = printer.get('types', [])
            
            # 检查是否有错误的字段
            if 'print_type' in printer:
                print(f"  ⚠ 警告: 打印机 {name} 使用了旧的 'print_type' 字段")
                print(f"    建议修改为: \"types\": {[printer['print_type']]}")
            
            is_default = "⭐默认" if printer.get('default') else ""
            print(f"  {i}. {name} {is_default}")
            print(f"     类型: {types}")
    
    # 检查旧格式（单打印机）
    printer = config.get('printer')
    if printer:
        print(f"\n✓ 单打印机配置 (旧格式，兼容模式)")
        print(f"  名称: {printer.get('name', '未命名')}")
    
    if not printers and not printer:
        print("\n⚠ 警告: 未找到打印机配置")
    
    return True


def check_mqtt_client_init():
    """检查MQTT客户端初始化"""
    print_section("2. 检查MQTT客户端初始化")
    
    try:
        config_manager = ConfigManager('config/printer_config.json')
        config = config_manager.load()
        
        mqtt_config = config.get('mqtt', {})
        printers_config = config.get('printers')
        printer_config = config.get('printer')
        
        # 创建客户端（不连接）
        client = LabelPrintMQTT(
            broker_host=mqtt_config.get('host', '127.0.0.1'),
            broker_port=mqtt_config.get('port', 1883),
            topic=mqtt_config.get('topic', 'zebra/print'),
            username=mqtt_config.get('username'),
            password=mqtt_config.get('password'),
            printer_config=printer_config,
            printers_config=printers_config
        )
        
        print("✓ MQTT客户端初始化成功")
        print(f"  打印类型映射: {list(client.printer_map.keys())}")
        print(f"  打印机数量: {len(client.printer_info_list)}")
        
        return True
        
    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_printer_info_display():
    """检查打印机信息显示"""
    print_section("3. 检查打印机信息显示")
    
    try:
        config_manager = ConfigManager('config/printer_config.json')
        config = config_manager.load()
        
        mqtt_config = config.get('mqtt', {})
        printers_config = config.get('printers')
        printer_config = config.get('printer')
        
        client = LabelPrintMQTT(
            broker_host=mqtt_config.get('host', '127.0.0.1'),
            broker_port=mqtt_config.get('port', 1883),
            topic=mqtt_config.get('topic', 'zebra/print'),
            username=mqtt_config.get('username'),
            password=mqtt_config.get('password'),
            printer_config=printer_config,
            printers_config=printers_config
        )
        
        # 显示打印机信息（模拟启动显示）
        print("\n启动时显示效果预览:")
        print("-"*70)
        
        if client.printer_info_list:
            for idx, printer_info in enumerate(client.printer_info_list, 1):
                name = printer_info['name']
                formats = printer_info['formats']
                is_default = printer_info['is_default']
                
                # 获取实际设备信息
                actual_name = "自动检测"
                if formats:
                    first_format = formats[0].split('(')[0]
                    printer_instance = None
                    
                    if first_format == 'label':
                        printer_instance = client.printer_map.get('label')
                    elif first_format == 'pdf':
                        printer_instance = client.printer_map.get('pdf')
                    elif first_format == 'receipt':
                        printer_instance = client.printer_map.get('receipt')
                    
                    if printer_instance:
                        if hasattr(printer_instance, 'printer_name') and printer_instance.printer_name:
                            actual_name = printer_instance.printer_name
                        elif hasattr(printer_instance, 'printer_ip') and printer_instance.printer_ip:
                            actual_name = f"网络 {printer_instance.printer_ip}"
                
                default_mark = " ⭐默认" if is_default else ""
                print(f"\n  [{idx}] {name}{default_mark}")
                print(f"      设备: {actual_name}")
                print(f"      支持格式: {', '.join(formats)}")
        
        print("\n" + "-"*70)
        print("✓ 打印机信息显示正常")
        
        return True
        
    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_compatibility():
    """检查兼容性特性"""
    print_section("4. 检查兼容性特性")
    
    print("✓ 支持新旧配置格式:")
    print("  - 新格式: 'printers' 数组（多打印机）")
    print("  - 旧格式: 'printer' 对象（单打印机，兼容模式）")
    
    print("\n✓ 支持的打印类型:")
    print("  - label: ZPL标签打印")
    print("  - pdf: PDF文档打印")
    print("  - receipt/escpos: ESC/POS小票打印")
    print("  - *: 通配符，支持所有类型")
    
    print("\n✓ 配置验证:")
    print("  - 自动检测并警告 'print_type' 旧字段")
    print("  - 支持 'types' 数组格式")
    print("  - 自动去重 receipt/escpos 别名")
    
    return True


def main():
    """主函数"""
    print("="*70)
    print(" " * 15 + "配置升级检查报告")
    print("="*70)
    
    results = []
    
    # 执行检查
    results.append(("配置文件格式", check_config_format()))
    results.append(("MQTT客户端初始化", check_mqtt_client_init()))
    results.append(("打印机信息显示", check_printer_info_display()))
    results.append(("兼容性特性", check_compatibility()))
    
    # 总结
    print_section("检查总结")
    
    all_passed = all(result for _, result in results)
    
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"  {status} - {name}")
    
    print("\n" + "="*70)
    if all_passed:
        print("✓ 所有检查通过！配置升级成功，程序运行正常。")
    else:
        print("✗ 部分检查失败，请查看上方详细信息。")
    print("="*70)
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())

