#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试MQTT自动重连功能

这个脚本用于测试MQTT客户端的自动重连机制。
运行后，可以通过以下方式测试：
1. 启动脚本
2. 停止MQTT服务器
3. 观察客户端是否自动尝试重连
4. 重启MQTT服务器
5. 观察客户端是否成功重连
"""

import sys
import os
import time

# 添加项目路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

from src.config import ConfigManager
from src.core.mqtt_client import LabelPrintMQTT

def test_mqtt_reconnect():
    """测试MQTT自动重连"""
    print("="*70)
    print(" " * 20 + "MQTT自动重连测试")
    print("="*70)
    print()
    
    # 加载配置
    config_file = 'config/printer_config.json'
    if not os.path.exists(config_file):
        print(f"错误：配置文件不存在 - {config_file}")
        print("请先创建配置文件或运行主程序生成默认配置")
        return
    
    config_manager = ConfigManager(config_file)
    config = config_manager.load()
    mqtt_config = config_manager.get_mqtt_config()
    printers_config = config.get('printers', [])
    printer_config = config.get('printer')
    
    print("配置信息:")
    print(f"  MQTT服务器: {mqtt_config.get('host', '127.0.0.1')}:{mqtt_config.get('port', 1883)}")
    print(f"  协议: {mqtt_config.get('protocol', 'mqtt')}")
    print(f"  主题: {mqtt_config.get('topic', 'zebra/print')}")
    if mqtt_config.get('url'):
        print(f"  URL: {mqtt_config.get('url')}")
    print()
    
    # 创建MQTT客户端
    mqtt_client = LabelPrintMQTT(
        broker_host=mqtt_config.get('host', '127.0.0.1'),
        broker_port=mqtt_config.get('port', 1883),
        topic=mqtt_config.get('topic', 'zebra/print'),
        username=mqtt_config.get('username'),
        password=mqtt_config.get('password'),
        protocol=mqtt_config.get('protocol'),
        url=mqtt_config.get('url'),
        client_id=mqtt_config.get('client_id'),
        printer_config=printer_config,
        printers_config=printers_config
    )
    
    print("\n测试说明:")
    print("  1. 脚本将尝试连接到MQTT服务器")
    print("  2. 连接成功后，您可以停止MQTT服务器来测试自动重连")
    print("  3. 观察客户端是否自动尝试重连")
    print("  4. 重启MQTT服务器，观察客户端是否成功重连")
    print("  5. 按 Ctrl+C 停止测试")
    print()
    
    try:
        # 启动MQTT客户端（阻塞运行）
        mqtt_client.start()
    except KeyboardInterrupt:
        print("\n\n收到停止信号，正在退出...")
        mqtt_client.stop()
        print("\n测试结束")

if __name__ == '__main__':
    test_mqtt_reconnect()

