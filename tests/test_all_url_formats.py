#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试所有URL格式的解析
验证所有支持的MQTT URL格式都能正确解析
"""

import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

from src.config.config import parse_mqtt_url


def test_url_parsing():
    """测试所有URL格式的解析"""
    print("=" * 70)
    print(" " * 20 + "MQTT URL格式解析测试")
    print("=" * 70)
    print()
    
    test_urls = [
        ("mqtt://127.0.0.1:1883", "标准MQTT，带端口"),
        ("mqtt://127.0.0.1", "标准MQTT，默认端口1883"),
        ("ws://10.100.10.121:8083/mqtt", "WebSocket，带端口和路径"),
        ("ws://10.100.10.121/mqtt", "WebSocket，默认端口80，带路径"),
        ("wss://10.100.10.121/mqtt", "WebSocket Secure，默认端口443，带路径"),
        ("wss://10.100.10.121:8443/mqtt", "WebSocket Secure，自定义端口"),
        ("tcp://10.100.10.121:1883", "TCP协议（等同于MQTT）"),
        ("tcp://10.100.10.121", "TCP协议，默认端口"),
        ("mqtts://example.com:8883", "MQTT Secure，SSL/TLS"),
        ("mqtts://example.com", "MQTT Secure，默认端口8883"),
        ("ssl://example.com:8883", "SSL协议（等同于MQTTs）"),
    ]
    
    print(f"测试 {len(test_urls)} 种URL格式...\n")
    
    all_passed = True
    
    for url, description in test_urls:
        print(f"测试: {description}")
        print(f"  URL: {url}")
        
        try:
            config = parse_mqtt_url(url, {'topic': 'zebra/print'})
            
            if not config:
                print(f"  ✗ 解析失败：返回空配置")
                all_passed = False
                print()
                continue
            
            # 验证必要字段
            required_fields = ['host', 'port', 'protocol', 'url', 'topic']
            missing_fields = [f for f in required_fields if f not in config]
            
            if missing_fields:
                print(f"  ✗ 缺少字段: {', '.join(missing_fields)}")
                all_passed = False
            else:
                print(f"  ✓ 解析成功:")
                print(f"    主机: {config['host']}")
                print(f"    端口: {config['port']}")
                print(f"    协议: {config['protocol']}")
                print(f"    主题: {config['topic']}")
                if 'username' in config:
                    print(f"    用户名: {config['username']}")
                if 'password' in config:
                    print(f"    密码: {'*' * len(str(config['password']))}")
            
        except Exception as e:
            print(f"  ✗ 解析异常: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False
        
        print()
    
    print("=" * 70)
    if all_passed:
        print("✓ 所有URL格式解析测试通过！")
    else:
        print("✗ 部分URL格式解析测试失败")
    print("=" * 70)
    
    return all_passed


def test_expected_results():
    """测试预期结果"""
    print("\n" + "=" * 70)
    print(" " * 20 + "预期结果验证")
    print("=" * 70)
    print()
    
    test_cases = [
        {
            "url": "mqtt://127.0.0.1:1883",
            "expected": {"host": "127.0.0.1", "port": 1883, "protocol": "mqtt"}
        },
        {
            "url": "ws://10.100.10.121:8083/mqtt",
            "expected": {"host": "10.100.10.121", "port": 8083, "protocol": "ws"}
        },
        {
            "url": "wss://10.100.10.121/mqtt",
            "expected": {"host": "10.100.10.121", "port": 443, "protocol": "wss"}
        },
        {
            "url": "tcp://10.100.10.121:1883",
            "expected": {"host": "10.100.10.121", "port": 1883, "protocol": "mqtt"}
        },
        {
            "url": "mqtts://example.com:8883",
            "expected": {"host": "example.com", "port": 8883, "protocol": "mqtts"}
        },
    ]
    
    all_passed = True
    
    for case in test_cases:
        url = case["url"]
        expected = case["expected"]
        print(f"测试: {url}")
        
        config = parse_mqtt_url(url)
        
        failed = False
        for key, expected_value in expected.items():
            actual_value = config.get(key)
            if actual_value != expected_value:
                print(f"  ✗ {key}: 期望 {expected_value}, 实际 {actual_value}")
                failed = True
                all_passed = False
        
        if not failed:
            print(f"  ✓ 所有字段匹配")
    
    print()
    print("=" * 70)
    if all_passed:
        print("✓ 预期结果验证通过！")
    else:
        print("✗ 预期结果验证失败")
    print("=" * 70)
    
    return all_passed


if __name__ == '__main__':
    test1 = test_url_parsing()
    test2 = test_expected_results()
    
    sys.exit(0 if (test1 and test2) else 1)

