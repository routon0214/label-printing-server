#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动显示测试
测试打印机信息的显示效果
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import ConfigManager
from core import LabelPrintMQTT


def test_startup_display():
    """测试启动显示"""
    print("测试启动时的打印机信息显示\n")
    
    # 加载配置
    config_manager = ConfigManager('config/printer_config.json')
    config = config_manager.load()
    
    mqtt_config = config.get('mqtt', {})
    printers_config = config.get('printers')
    printer_config = config.get('printer')
    
    # 创建客户端实例
    client = LabelPrintMQTT(
        broker_host=mqtt_config.get('host', '127.0.0.1'),
        broker_port=mqtt_config.get('port', 1883),
        topic=mqtt_config.get('topic', 'zebra/print'),
        username=mqtt_config.get('username'),
        password=mqtt_config.get('password'),
        printer_config=printer_config,
        printers_config=printers_config
    )
    
    # 模拟启动显示（不实际连接MQTT）
    print("\n" + "="*70)
    print(" " * 20 + "打印机MQTT服务")
    print("="*70)
    print(f"MQTT服务器: {client.broker_host}:{client.broker_port}")
    print(f"订阅主题: {client.topic}")
    print("-"*70)
    
    # 显示已配置的打印机信息
    if client.printer_info_list:
        print("已配置的打印机:")
        for idx, printer_info in enumerate(client.printer_info_list, 1):
            name = printer_info['name']
            formats = printer_info['formats']
            is_default = printer_info['is_default']
            
            # 获取实际的打印机名称或IP
            config_item = printer_info['config']
            actual_name = "自动检测"
            
            # 尝试从第一个格式的打印机实例获取实际名称
            if formats:
                first_format = formats[0].split('(')[0]  # 提取格式名，去掉括号
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
            default_mark = " ⭐默认" if is_default else ""
            print(f"\n  [{idx}] {name}{default_mark}")
            print(f"      设备: {actual_name}")
            print(f"      支持格式: {', '.join(formats)}")
    elif client.printer_map:
        print("已配置的打印机: 通用打印机（兼容模式）")
        print("  支持格式: label(ZPL), pdf, receipt(ESC/POS)")
    else:
        print("打印机: 未配置")
    
    print("="*70)
    print("\n✓ 启动显示测试完成")


if __name__ == '__main__':
    test_startup_display()

