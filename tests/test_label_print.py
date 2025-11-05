#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
标签打印测试脚本
测试通过MQTT发送ZPL标签打印任务
"""

import json
import sys
import os

# 添加项目根目录和src目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

from src.config import ConfigManager
import paho.mqtt.client as mqtt


def get_mqtt_config():
    """从配置文件获取MQTT设置"""
    config_manager = ConfigManager('config/printer_config.json')
    config = config_manager.load()
    mqtt_config = config_manager.get_mqtt_config()
    return {
        'host': mqtt_config.get('host', '127.0.0.1'),
        'port': mqtt_config.get('port', 1883),
        'topic': mqtt_config.get('topic', 'zebra/print'),
        'username': mqtt_config.get('username'),
        'password': mqtt_config.get('password')
    }


def main():
    """主函数"""
    # 获取配置
    mqtt_cfg = get_mqtt_config()
    
    print("发送测试MQTT消息 - 标签打印")
    print("=" * 60)
    print(f"MQTT服务器: {mqtt_cfg['host']}:{mqtt_cfg['port']}")
    print(f"MQTT主题: {mqtt_cfg['topic']}")
    
    # 测试标签数据
    label_data = {
        "print_type": "label",  # 指定打印类型
        "title": "产品标签",
        "fields": [
            {"label": "产品名称", "value": "精密电子元件", "font_size": 28},
            {"label": "产品型号", "value": "ZX-2024-PRO", "font_size": 25},
            {"label": "序列号", "value": "SN20251015001", "font_size": 22},
            {"label": "生产日期", "value": "2025-10-15", "font_size": 22},
            {"label": "质检员", "value": "李四", "font_size": 22}
        ],
        "barcode": "SN20251015001",
        "qrcode": "SN20251015001"
    }
    
    print("\n标签数据:")
    print(json.dumps(label_data, ensure_ascii=False, indent=2))
    
    # 连接MQTT服务器
    client = mqtt.Client()
    
    # 设置认证
    if mqtt_cfg['username'] and mqtt_cfg['password']:
        client.username_pw_set(mqtt_cfg['username'], mqtt_cfg['password'])
        print(f"\n使用认证: {mqtt_cfg['username']}")
    
    print(f"\n连接到MQTT服务器...")
    client.connect(mqtt_cfg['host'], mqtt_cfg['port'], 60)
    
    # 发送消息
    print(f"发送消息到主题: {mqtt_cfg['topic']}")
    result = client.publish(mqtt_cfg['topic'], json.dumps(label_data))
    
    if result.rc == 0:
        print("✓ 消息发送成功")
    else:
        print(f"✗ 消息发送失败，错误码: {result.rc}")
    
    # 断开连接
    client.disconnect()
    
    print("=" * 60)
    print("\n提示:")
    print("  1. 确保MQTT服务器正在运行")
    print("  2. 确保打印服务正在运行: python app.py")
    print("  3. 查看打印服务的输出确认是否收到消息")
    
    return 0 if result.rc == 0 else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n测试已取消")
        sys.exit(0)
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

