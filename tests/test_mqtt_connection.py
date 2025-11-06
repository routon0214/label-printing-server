#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MQTT连接测试工具
用于诊断MQTT连接问题
"""

import sys
import os
import json

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

from src.config import ConfigManager


def test_mqtt_connection():
    """测试MQTT连接"""
    print("=" * 70)
    print(" " * 20 + "MQTT连接测试工具")
    print("=" * 70)
    print()
    
    # 加载配置
    config_manager = ConfigManager('config/printer_config.json')
    config = config_manager.load()
    mqtt_config = config_manager.get_mqtt_config()
    
    print("当前MQTT配置:")
    print(f"  URL: {mqtt_config.get('url', 'N/A')}")
    print(f"  主机: {mqtt_config.get('host', 'N/A')}")
    print(f"  端口: {mqtt_config.get('port', 'N/A')}")
    print(f"  协议: {mqtt_config.get('protocol', 'N/A')}")
    print(f"  主题: {mqtt_config.get('topic', 'N/A')}")
    print(f"  用户名: {mqtt_config.get('username', 'N/A')}")
    print()
    
    # 测试连接
    try:
        import paho.mqtt.client as mqtt
        import time
        
        protocol = mqtt_config.get('protocol', 'mqtt')
        host = mqtt_config.get('host', '127.0.0.1')
        port = mqtt_config.get('port', 1883)
        username = mqtt_config.get('username')
        password = mqtt_config.get('password')
        url = mqtt_config.get('url')
        
        print("正在测试连接...")
        print(f"  目标: {host}:{port}")
        print(f"  协议: {protocol}")
        print()
        
        # 创建客户端
        if protocol in ['ws', 'wss']:
            # WebSocket连接
            transport = "websockets"
            ws_path = '/mqtt'
            if url:
                try:
                    from urllib.parse import urlparse
                    parsed = urlparse(url)
                    ws_path = parsed.path if parsed.path else '/mqtt'
                except:
                    pass
            
            print(f"  WebSocket路径: {ws_path}")
            client = mqtt.Client(transport=transport)
            client.ws_set_options(path=ws_path)
        else:
            # TCP连接
            client = mqtt.Client()
        
        # 设置认证
        if username and password:
            client.username_pw_set(username, password)
            print(f"  使用认证: {username}")
        
        # 连接状态标记
        connected = False
        connection_error = None
        
        def on_connect(client, userdata, flags, rc):
            nonlocal connected, connection_error
            if rc == 0:
                connected = True
                print("[OK] 连接成功！")
            else:
                error_messages = {
                    1: "协议版本不正确",
                    2: "客户端标识符无效",
                    3: "服务器不可用",
                    4: "用户名或密码错误",
                    5: "未授权"
                }
                connection_error = error_messages.get(rc, f"未知错误码: {rc}")
                print(f"[ERROR] 连接失败: {connection_error} (错误码: {rc})")
        
        def on_disconnect(client, userdata, rc):
            nonlocal connected
            connected = False
            if rc != 0:
                print(f"[ERROR] 意外断开连接 (错误码: {rc})")
        
        client.on_connect = on_connect
        client.on_disconnect = on_disconnect
        
        # 启动非阻塞循环
        client.loop_start()
        
        # 尝试连接
        try:
            if protocol in ['wss', 'mqtts', 'ssl']:
                client.tls_set()
            
            result = client.connect(host, port, 60)
            if result != 0:
                print(f"[ERROR] 连接调用失败，返回码: {result}")
                client.loop_stop()
                return False
            
            # 等待连接结果（最多10秒）
            timeout = 10
            start_time = time.time()
            while not connected and (time.time() - start_time) < timeout:
                if connection_error:
                    print(f"[ERROR] 连接失败: {connection_error}")
                    client.loop_stop()
                    return False
                time.sleep(0.1)
            
            if connected:
                print()
                print("=" * 70)
                print("连接测试成功！")
                print("=" * 70)
                print()
                print("提示：")
                print("  1. MQTT服务器可达")
                print("  2. 认证信息正确（如果配置了）")
                print("  3. 网络连接正常")
                print()
                
                # 测试订阅
                topic = mqtt_config.get('topic', 'zebra/print')
                print(f"测试订阅主题: {topic}")
                client.subscribe(topic)
                time.sleep(0.5)
                print("[OK] 订阅成功")
                print()
                
                client.loop_stop()
                client.disconnect()
                return True
            else:
                print()
                print("=" * 70)
                print("连接测试失败！")
                print("=" * 70)
                print()
                print("可能的原因：")
                print("  1. MQTT服务器未运行或不可达")
                print("  2. 服务器地址或端口错误")
                print("  3. 防火墙阻止连接")
                print("  4. WebSocket路径不正确（WebSocket连接）")
                print("  5. 用户名或密码错误（如果配置了认证）")
                print()
                
                if connection_error:
                    print(f"错误信息: {connection_error}")
                    print()
                
                client.loop_stop()
                return False
                
        except Exception as e:
            print(f"[ERROR] 连接异常: {e}")
            import traceback
            traceback.print_exc()
            client.loop_stop()
            return False
            
    except ImportError:
        print("[ERROR] 错误：需要安装 paho-mqtt 库")
        print("  运行: pip install paho-mqtt")
        return False
    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_mqtt_connection()
    sys.exit(0 if success else 1)

