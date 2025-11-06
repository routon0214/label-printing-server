#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MQTT打印测试 - 发送端
用于测试发送打印任务到MQTT服务器
"""

import json
import time


def send_test_label(broker_host='10.100.10.121', broker_port=1883, topic='zebra/print'):
    """
    发送测试标签数据
    """
    try:
        import paho.mqtt.client as mqtt
        
        print("="*60)
        print("MQTT打印测试 - 发送端")
        print("="*60)
        print(f"连接到: {broker_host}:{broker_port}")
        print(f"主题: {topic}")
        
        # 测试标签数据
        label_data = {
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
        
        print("\n发送数据:")
        print(json.dumps(label_data, ensure_ascii=False, indent=2))
        
        # 创建客户端
        client = mqtt.Client()
        
        # 连接
        print(f"\n正在连接...")
        client.connect(broker_host, broker_port, 60)
        
        # 发送
        result = client.publish(topic, json.dumps(label_data, ensure_ascii=False))
        
        if result.rc == 0:
            print("[OK] 消息已发送")
        else:
            print(f"[ERROR] 发送失败，错误码: {result.rc}")
        
        # 断开
        time.sleep(0.5)
        client.disconnect()
        
        print("="*60)
        
    except ImportError:
        print("\n错误：需要安装 paho-mqtt")
        print("请运行: pip install paho-mqtt")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 可以修改这些参数
    send_test_label(
        broker_host='10.100.10.121',  # MQTT服务器地址
        broker_port=1883,          # MQTT服务器端口
        topic='zebra/print'        # MQTT主题
    )

