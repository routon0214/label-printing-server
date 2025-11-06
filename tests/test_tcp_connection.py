#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TCP MQTT连接测试工具
专门用于测试 tcp:// 或 mqtt:// 协议的连接
"""

import sys
import os
import time
import socket

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))


def test_network_connectivity(host, port, timeout=3):
    """测试网络连通性"""
    print(f"测试网络连通性: {host}:{port}")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        if result == 0:
            print(f"[OK] 网络连接成功")
            return True
        else:
            print(f"[ERROR] 网络连接失败，错误码: {result}")
            return False
    except socket.gaierror as e:
        print(f"[ERROR] DNS解析失败: {e}")
        return False
    except socket.timeout:
        print(f"[ERROR] 连接超时")
        return False
    except Exception as e:
        print(f"[ERROR] 网络测试异常: {e}")
        return False


def test_mqtt_connection(url, topic='zebra/print', username=None, password=None):
    """测试MQTT连接"""
    print("=" * 70)
    print(" " * 20 + "TCP MQTT连接测试")
    print("=" * 70)
    print()
    
    try:
        from urllib.parse import urlparse
        from src.config import ConfigManager
        
        # 解析URL
        parsed = urlparse(url)
        protocol = parsed.scheme.lower()
        host = parsed.hostname or '127.0.0.1'
        port = parsed.port or 1883
        
        print(f"URL: {url}")
        print(f"解析结果:")
        print(f"  协议: {protocol}")
        print(f"  主机: {host}")
        print(f"  端口: {port}")
        print(f"  主题: {topic}")
        print()
        
        # 检查协议
        if protocol not in ['mqtt', 'tcp']:
            print(f"[ERROR] 错误：此工具仅测试TCP连接（mqtt://或tcp://）")
            print(f"  当前协议: {protocol}")
            return False
        
        # 测试网络连通性
        print("=" * 70)
        print("步骤1: 网络连通性测试")
        print("=" * 70)
        if not test_network_connectivity(host, port):
            print()
            print("网络连通性测试失败，MQTT连接将无法建立")
            print("建议检查:")
            print(f"  1. 服务器 {host}:{port} 是否运行")
            print(f"  2. 防火墙是否允许连接")
            print(f"  3. 网络路由是否正常")
            return False
        print()
        
        # 测试MQTT连接
        print("=" * 70)
        print("步骤2: MQTT连接测试")
        print("=" * 70)
        
        import paho.mqtt.client as mqtt
        
        connected = False
        subscribed = False
        connection_error = None
        
        def on_connect(client, userdata, flags, rc):
            nonlocal connected, connection_error
            if rc == 0:
                connected = True
                print(f"[OK] MQTT连接成功")
            else:
                error_messages = {
                    1: "协议版本不正确",
                    2: "客户端标识符无效",
                    3: "服务器不可用",
                    4: "用户名或密码错误",
                    5: "未授权"
                }
                connection_error = error_messages.get(rc, f"未知错误码: {rc}")
                print(f"[ERROR] MQTT连接失败: {connection_error} (错误码: {rc})")
        
        def on_subscribe(client, userdata, mid, granted_qos):
            nonlocal subscribed
            subscribed = True
            print(f"[OK] 订阅成功 (消息ID: {mid}, QoS: {granted_qos})")
        
        def on_disconnect(client, userdata, rc):
            nonlocal connected
            connected = False
            if rc != 0:
                print(f"[ERROR] 断开连接 (错误码: {rc})")
        
        client = mqtt.Client()
        client.on_connect = on_connect
        client.on_subscribe = on_subscribe
        client.on_disconnect = on_disconnect
        
        if username and password:
            client.username_pw_set(username, password)
            print(f"已设置认证信息")
        
        print("正在连接MQTT服务器...")
        client.loop_start()
        
        try:
            result = client.connect(host, port, 60)
            if result != 0:
                print(f"[ERROR] connect()返回错误码: {result}")
                client.loop_stop()
                return False
        except Exception as e:
            print(f"[ERROR] 连接异常: {e}")
            import traceback
            traceback.print_exc()
            client.loop_stop()
            return False
        
        # 等待连接（最多10秒）
        print("等待连接建立...")
        timeout = 10
        start_time = time.time()
        while not connected and (time.time() - start_time) < timeout:
            if connection_error:
                print(f"[ERROR] 连接失败: {connection_error}")
                client.loop_stop()
                return False
            time.sleep(0.1)
        
        if not connected:
            print(f"[ERROR] 连接超时（等待了{timeout}秒）")
            client.loop_stop()
            return False
        
        # 订阅主题
        print(f"\n订阅主题: {topic}")
        result, mid = client.subscribe(topic, 0)
        if result != 0:
            print(f"[ERROR] 订阅失败，错误码: {result}")
            client.loop_stop()
            return False
        
        # 等待订阅确认（最多5秒）
        timeout = 5
        start_time = time.time()
        while not subscribed and (time.time() - start_time) < timeout:
            time.sleep(0.1)
        
        if not subscribed:
            print(f"[WARNING] 订阅确认超时，但可能已订阅成功")
        
        print("\n" + "=" * 70)
        print("[OK] 连接测试成功！")
        print("=" * 70)
        print("\n按 Ctrl+C 退出...")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n正在断开连接...")
            client.loop_stop()
            client.disconnect()
            return True
            
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
    if len(sys.argv) < 2:
        print("用法: python test_tcp_connection.py <URL> [topic] [username] [password]")
        print("示例: python test_tcp_connection.py tcp://10.100.10.121:1883 zebra/print")
        sys.exit(1)
    
    url = sys.argv[1]
    topic = sys.argv[2] if len(sys.argv) > 2 else 'zebra/print'
    username = sys.argv[3] if len(sys.argv) > 3 else None
    password = sys.argv[4] if len(sys.argv) > 4 else None
    
    try:
        success = test_mqtt_connection(url, topic, username, password)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n测试已中断")
        sys.exit(0)

