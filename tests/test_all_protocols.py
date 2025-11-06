#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试所有MQTT协议支持
验证 mqtt://, tcp://, ws://, wss://, mqtts:// 等协议
"""

import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

from src.config import ConfigManager


def test_url_parsing():
    """测试URL解析功能"""
    print("=" * 70)
    print(" " * 20 + "MQTT协议URL解析测试")
    print("=" * 70)
    print()
    
    # 测试URL列表
    test_urls = [
        "mqtt://127.0.0.1:1883",
        "tcp://10.100.10.121:1883",
        "ws://10.100.10.121:8083/mqtt",
        "wss://10.100.10.121/mqtt",
        "mqtts://example.com:8883",
        "ws://example.com:80/mqtt",
        "wss://example.com:443/mqtt",
    ]
    
    config_manager = ConfigManager('config/printer_config.json')
    
    print("测试URL解析:")
    print("-" * 70)
    
    all_passed = True
    for url in test_urls:
        try:
            # 创建临时配置
            temp_config = {'mqtt': {'url': url, 'topic': 'test/topic'}}
            config_manager.config = temp_config
            
            # 获取MQTT配置
            mqtt_config = config_manager.get_mqtt_config()
            
            # 验证解析结果
            host = mqtt_config.get('host')
            port = mqtt_config.get('port')
            protocol = mqtt_config.get('protocol')
            
            print(f"\nURL: {url}")
            print(f"  协议: {protocol}")
            print(f"  主机: {host}")
            print(f"  端口: {port}")
            
            # 验证协议映射
            if url.startswith('mqtt://') or url.startswith('tcp://'):
                if protocol != 'mqtt':
                    print(f"  [ERROR] 错误：协议应该是 'mqtt'，实际是 '{protocol}'")
                    all_passed = False
                else:
                    print(f"  [OK] 协议映射正确")
            
            elif url.startswith('ws://'):
                if protocol != 'ws':
                    print(f"  [ERROR] 错误：协议应该是 'ws'，实际是 '{protocol}'")
                    all_passed = False
                else:
                    print(f"  [OK] 协议映射正确")
            
            elif url.startswith('wss://'):
                if protocol != 'wss':
                    print(f"  [ERROR] 错误：协议应该是 'wss'，实际是 '{protocol}'")
                    all_passed = False
                else:
                    print(f"  [OK] 协议映射正确")
            
            elif url.startswith('mqtts://'):
                if protocol != 'mqtts':
                    print(f"  [ERROR] 错误：协议应该是 'mqtts'，实际是 '{protocol}'")
                    all_passed = False
                else:
                    print(f"  [OK] 协议映射正确")
            
            # 验证端口
            if port and port > 0:
                print(f"  [OK] 端口解析正确")
            else:
                print(f"  [WARNING] 警告：端口未正确解析")
            
        except Exception as e:
            print(f"\nURL: {url}")
            print(f"  [ERROR] 解析失败: {e}")
            all_passed = False
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 70)
    if all_passed:
        print("[OK] 所有URL解析测试通过")
    else:
        print("[ERROR] 部分URL解析测试失败")
    print("=" * 70)
    
    return all_passed


def test_protocol_features():
    """测试协议特性"""
    print("\n" + "=" * 70)
    print(" " * 20 + "协议特性说明")
    print("=" * 70)
    print()
    
    protocols = {
        'mqtt': {
            'description': '标准MQTT协议 (TCP)',
            'default_port': 1883,
            'transport': 'TCP',
            'ssl': False,
            'examples': ['mqtt://127.0.0.1:1883', 'tcp://10.100.10.121:1883']
        },
        'mqtts': {
            'description': 'MQTT over SSL/TLS (TCP + SSL)',
            'default_port': 8883,
            'transport': 'TCP',
            'ssl': True,
            'examples': ['mqtts://example.com:8883']
        },
        'ws': {
            'description': 'WebSocket (HTTP)',
            'default_port': 80,
            'transport': 'WebSocket',
            'ssl': False,
            'examples': ['ws://10.100.10.121:8083/mqtt']
        },
        'wss': {
            'description': 'WebSocket Secure (HTTPS)',
            'default_port': 443,
            'transport': 'WebSocket',
            'ssl': True,
            'examples': ['wss://10.100.10.121/mqtt']
        }
    }
    
    for protocol, info in protocols.items():
        print(f"{protocol.upper()}:")
        print(f"  说明: {info['description']}")
        print(f"  默认端口: {info['default_port']}")
        print(f"  传输层: {info['transport']}")
        print(f"  SSL/TLS: {'是' if info['ssl'] else '否'}")
        print(f"  示例:")
        for example in info['examples']:
            print(f"    - {example}")
        print()


if __name__ == '__main__':
    print()
    test_protocol_features()
    print()
    success = test_url_parsing()
    sys.exit(0 if success else 1)

