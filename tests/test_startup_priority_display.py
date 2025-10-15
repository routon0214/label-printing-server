#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试启动显示（包含打印机优先级）
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import ConfigManager
from core import LabelPrintMQTT


def test_startup_display():
    """测试启动显示"""
    print("测试启动显示（打印机优先级）\n")
    
    # 加载配置
    config_manager = ConfigManager('config/printer_config.json')
    config = config_manager.load()
    
    mqtt_config = config.get('mqtt', {})
    printers_config = config.get('printers')
    
    # 创建客户端
    client = LabelPrintMQTT(
        broker_host=mqtt_config.get('host', '127.0.0.1'),
        broker_port=mqtt_config.get('port', 1883),
        topic=mqtt_config.get('topic', 'zebra/print'),
        printers_config=printers_config
    )
    
    # 模拟启动显示
    print("\n" + "="*70)
    print(" " * 20 + "打印机MQTT服务")
    print("="*70)
    print(f"MQTT服务器: {client.broker_host}:{client.broker_port}")
    print(f"订阅主题: {client.topic}")
    print("-"*70)
    
    # 显示打印机信息
    if client.printer_info_list:
        print("已配置的打印机:")
        for idx, printer_info in enumerate(client.printer_info_list, 1):
            name = printer_info['name']
            formats = printer_info['formats']
            is_fallback = printer_info.get('is_fallback', False)
            
            # 获取实际的打印机名称或IP
            config_item = printer_info['config']
            actual_name = "自动检测"
            
            # 尝试从第一个格式的打印机实例获取实际名称
            if formats and not is_fallback:
                first_format = formats[0].split('(')[0]
                if first_format == 'label':
                    printer_instance = client.printer_map.get('label')
                elif first_format == 'pdf':
                    printer_instance = client.printer_map.get('pdf')
                elif first_format == 'receipt':
                    printer_instance = client.printer_map.get('receipt')
                else:
                    printer_instance = None
                
                if printer_instance:
                    if hasattr(printer_instance, 'printer_name') and printer_instance.printer_name:
                        actual_name = printer_instance.printer_name
                    elif hasattr(printer_instance, 'printer_ip') and printer_instance.printer_ip:
                        actual_name = f"网络打印机 {printer_instance.printer_ip}"
            
            # 显示打印机信息
            type_mark = " 🔄 备选" if is_fallback else " ⭐ 专用"
            print(f"\n  [{idx}] {name}{type_mark}")
            print(f"      设备: {actual_name}")
            print(f"      支持格式: {', '.join(formats)}")
            if is_fallback:
                print(f"      说明: 当找不到专用打印机时使用")
    
    print("\n" + "="*70)
    print("\n打印机优先级说明:")
    print("  ⭐ 专用 = 优先使用的打印机")
    print("  🔄 备选 = 找不到专用打印机时使用")
    print("\n打印逻辑:")
    print("  1. 接收到打印任务时，先查找对应类型的专用打印机")
    print("  2. 如果没有专用打印机，使用备选打印机")
    print("  3. 如果都没有，打印失败")
    print("="*70)


if __name__ == '__main__':
    test_startup_display()

