#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebSocket MQTT连接测试工具
专门用于测试 ws:// 或 wss:// 协议的MQTT连接
"""

import sys
import os
import time

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))


def test_websocket_connection(url, topic='zebra/print', username=None, password=None):
    """测试WebSocket MQTT连接"""
    print("=" * 70)
    print(" " * 20 + "WebSocket MQTT连接测试")
    print("=" * 70)
    print()
    
    try:
        import paho.mqtt.client as mqtt
        from urllib.parse import urlparse
        
        # 解析URL
        parsed = urlparse(url)
        protocol = parsed.scheme.lower()
        host = parsed.hostname or '127.0.0.1'
        port = parsed.port
        ws_path = parsed.path if parsed.path else '/mqtt'
        
        # 设置默认端口
        if port is None:
            if protocol == 'ws':
                port = 80
            elif protocol == 'wss':
                port = 443
            else:
                port = 1883
        
        print(f"URL: {url}")
        print(f"解析结果:")
        print(f"  协议: {protocol}")
        print(f"  主机: {host}")
        print(f"  端口: {port}")
        print(f"  路径: {ws_path}")
        print(f"  主题: {topic}")
        print()
        
        # 检查是否支持WebSocket
        if protocol not in ['ws', 'wss']:
            print(f"✗ 错误：URL协议必须是 ws:// 或 wss://，当前是 {protocol}://")
            return False
        
        # 创建WebSocket客户端
        print("正在创建WebSocket客户端...")
        transport = "websockets"
        client = mqtt.Client(transport=transport)
        
        # 设置WebSocket路径
        print(f"设置WebSocket路径: {ws_path}")
        try:
            client.ws_set_options(path=ws_path)
            print("✓ WebSocket选项设置成功")
        except Exception as e:
            print(f"✗ 设置WebSocket选项失败: {e}")
            return False
        
        # 设置认证
        if username and password:
            client.username_pw_set(username, password)
            print(f"✓ 已设置认证信息")
        
        # 连接状态
        connected = False
        subscribed = False
        connection_error = None
        
        def on_connect(client, userdata, flags, rc):
            nonlocal connected, connection_error
            if rc == 0:
                connected = True
                print(f"✓ 连接成功！")
            else:
                error_messages = {
                    1: "协议版本不正确",
                    2: "客户端标识符无效",
                    3: "服务器不可用",
                    4: "用户名或密码错误",
                    5: "未授权"
                }
                connection_error = error_messages.get(rc, f"未知错误码: {rc}")
                print(f"✗ 连接失败: {connection_error} (错误码: {rc})")
        
        def on_subscribe(client, userdata, mid, granted_qos):
            nonlocal subscribed
            subscribed = True
            print(f"✓ 订阅成功 (消息ID: {mid}, QoS: {granted_qos})")
        
        def on_message(client, userdata, msg):
            print(f"\n收到消息:")
            print(f"  主题: {msg.topic}")
            print(f"  内容: {msg.payload.decode('utf-8')[:200]}")
        
        def on_disconnect(client, userdata, rc):
            nonlocal connected
            connected = False
            if rc != 0:
                print(f"✗ 断开连接 (错误码: {rc})")
        
        client.on_connect = on_connect
        client.on_subscribe = on_subscribe
        client.on_message = on_message
        client.on_disconnect = on_disconnect
        
        # 启动非阻塞循环
        print("\n启动事件循环...")
        client.loop_start()
        
        # 连接
        print(f"正在连接 {host}:{port}...")
        try:
            result = client.connect(host, port, 60)
            if result != 0:
                print(f"✗ connect()返回错误码: {result}")
                client.loop_stop()
                return False
        except Exception as e:
            print(f"✗ 连接异常: {e}")
            import traceback
            traceback.print_exc()
            client.loop_stop()
            return False
        
        # 等待连接（最多15秒）
        print("等待连接建立...")
        timeout = 15
        start_time = time.time()
        while not connected and (time.time() - start_time) < timeout:
            if connection_error:
                print(f"✗ 连接失败: {connection_error}")
                client.loop_stop()
                return False
            time.sleep(0.1)
        
        if not connected:
            print(f"✗ 连接超时（等待了{timeout}秒）")
            client.loop_stop()
            return False
        
        # 订阅主题
        print(f"\n订阅主题: {topic}")
        result, mid = client.subscribe(topic, 0)
        if result != 0:
            print(f"✗ 订阅失败，错误码: {result}")
            client.loop_stop()
            return False
        
        # 等待订阅确认（最多5秒）
        print("等待订阅确认...")
        timeout = 5
        start_time = time.time()
        while not subscribed and (time.time() - start_time) < timeout:
            time.sleep(0.1)
        
        if not subscribed:
            print(f"⚠ 订阅确认超时，但可能已订阅成功")
        
        print("\n" + "=" * 70)
        print("连接测试成功！")
        print("=" * 70)
        print("\n按 Ctrl+C 退出...")
        
        # 保持运行
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n正在断开连接...")
            client.loop_stop()
            client.disconnect()
            return True
            
    except ImportError:
        print("✗ 错误：需要安装 paho-mqtt 库")
        print("  运行: pip install paho-mqtt")
        return False
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python test_websocket_mqtt.py <URL> [topic] [username] [password]")
        print("示例: python test_websocket_mqtt.py ws://10.100.10.121:8083/mqtt zebra/print")
        sys.exit(1)
    
    url = sys.argv[1]
    topic = sys.argv[2] if len(sys.argv) > 2 else 'zebra/print'
    username = sys.argv[3] if len(sys.argv) > 3 else None
    password = sys.argv[4] if len(sys.argv) > 4 else None
    
    success = test_websocket_connection(url, topic, username, password)
    sys.exit(0 if success else 1)


