#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ESC/POS打印测试脚本
测试通过MQTT发送小票/收据打印任务
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
        'host': mqtt_config.get('host', '10.100.10.121'),
        'port': mqtt_config.get(1883, 1883),
        'topic': mqtt_config.get('topic', 'zebra/print'),
        'username': mqtt_config.get('username'),
        'password': mqtt_config.get('password')
    }


def test_simple_receipt():
    """测试1: 简单收据"""
    mqtt_cfg = get_mqtt_config()
    
    receipt_data = {
        "print_type": "receipt",  # ESC/POS小票打印
        "title": "购物小票",
        "items": [
            {"name": "苹果", "qty": 2, "price": 5.50},
            {"name": "香蕉", "qty": 3, "price": 3.00},
            {"name": "橙子", "qty": 1, "price": 8.00}
        ],
        "total": 28.00,
        "footer": "感谢惠顾，欢迎再来！",
        "barcode": "1234567890128"
    }
    
    print("=" * 60)
    print("测试1: 简单购物小票")
    print("=" * 60)
    print(f"MQTT服务器: {mqtt_cfg['host']}:{mqtt_cfg['port']}")
    print(f"MQTT主题: {mqtt_cfg['topic']}")
    print(f"\n小票内容: {json.dumps(receipt_data, ensure_ascii=False, indent=2)}")
    
    # 发送MQTT消息
    client = mqtt.Client()
    if mqtt_cfg['username'] and mqtt_cfg['password']:
        client.username_pw_set(mqtt_cfg['username'], mqtt_cfg['password'])
    
    client.connect(mqtt_cfg['host'], mqtt_cfg['port'], 60)
    result = client.publish(mqtt_cfg['topic'], json.dumps(receipt_data))
    client.disconnect()
    
    if result.rc == 0:
        print("\n✓ 消息发送成功")
    else:
        print(f"\n✗ 消息发送失败: {result.rc}")
    
    print("=" * 60)
    return result.rc == 0


def test_restaurant_receipt():
    """测试2: 餐厅订单"""
    mqtt_cfg = get_mqtt_config()
    
    receipt_data = {
        "print_type": "receipt",
        "title": "餐厅订单",
        "items": [
            {"name": "宫保鸡丁", "qty": 1, "price": 38.00},
            {"name": "麻婆豆腐", "qty": 1, "price": 28.00},
            {"name": "米饭", "qty": 2, "price": 3.00},
            {"name": "可乐", "qty": 2, "price": 5.00}
        ],
        "total": 82.00,
        "footer": "欢迎光临，祝您用餐愉快！\n桌号: A08\n时间: 2025-10-15 12:30"
    }
    
    print("\n" + "=" * 60)
    print("测试2: 餐厅订单小票")
    print("=" * 60)
    print(f"小票内容: {json.dumps(receipt_data, ensure_ascii=False, indent=2)}")
    
    client = mqtt.Client()
    if mqtt_cfg['username'] and mqtt_cfg['password']:
        client.username_pw_set(mqtt_cfg['username'], mqtt_cfg['password'])
    
    client.connect(mqtt_cfg['host'], mqtt_cfg['port'], 60)
    result = client.publish(mqtt_cfg['topic'], json.dumps(receipt_data))
    client.disconnect()
    
    if result.rc == 0:
        print("\n✓ 消息发送成功")
    else:
        print(f"\n✗ 消息发送失败: {result.rc}")
    
    print("=" * 60)
    return result.rc == 0


def test_barcode_only():
    """测试3: 纯条形码"""
    mqtt_cfg = get_mqtt_config()
    
    receipt_data = {
        "print_type": "receipt",
        "title": "商品条码",
        "barcode": "6901234567892",
        "footer": "商品编码: 6901234567892"
    }
    
    print("\n" + "=" * 60)
    print("测试3: 纯条形码打印")
    print("=" * 60)
    print(f"小票内容: {json.dumps(receipt_data, ensure_ascii=False, indent=2)}")
    
    client = mqtt.Client()
    if mqtt_cfg['username'] and mqtt_cfg['password']:
        client.username_pw_set(mqtt_cfg['username'], mqtt_cfg['password'])
    
    client.connect(mqtt_cfg['host'], mqtt_cfg['port'], 60)
    result = client.publish(mqtt_cfg['topic'], json.dumps(receipt_data))
    client.disconnect()
    
    if result.rc == 0:
        print("\n✓ 消息发送成功")
    else:
        print(f"\n✗ 消息发送失败: {result.rc}")
    
    print("=" * 60)
    return result.rc == 0


def main():
    """主函数"""
    print("=" * 60)
    print("ESC/POS热敏打印机测试")
    print("=" * 60)
    print()
    print("请选择测试场景:")
    print("1. 简单购物小票")
    print("2. 餐厅订单小票")
    print("3. 纯条形码打印")
    print("4. 全部测试")
    print()
    
    try:
        choice = input("请输入选项 (1-4): ").strip()
        
        if choice == '1':
            test_simple_receipt()
        elif choice == '2':
            test_restaurant_receipt()
        elif choice == '3':
            test_barcode_only()
        elif choice == '4':
            test_simple_receipt()
            import time
            time.sleep(2)
            test_restaurant_receipt()
            time.sleep(2)
            test_barcode_only()
        else:
            print("无效的选项")
            return 1
        
        print("\n提示:")
        print("  1. 确保MQTT服务器正在运行")
        print("  2. 确保打印服务正在运行: python app.py")
        print("  3. 检查打印服务的输出确认是否收到消息")
        print("  4. ESC/POS适合热敏小票打印机（58mm/80mm）")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n测试已取消")
        return 0
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

