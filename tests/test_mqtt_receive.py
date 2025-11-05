#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MQTT消息接收测试工具
用于测试MQTT订阅和消息接收功能
"""

import sys
import os
import json
import time

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

from src.config import ConfigManager


def test_mqtt_receive():
    """测试MQTT消息接收"""
    print("=" * 70)
    print(" " * 20 + "MQTT消息接收测试")
    print("=" * 70)
    print()
    
    # 加载配置
    config_manager = ConfigManager('config/printer_config.json')
    config = config_manager.load()
    mqtt_config = config_manager.get_mqtt_config()
    
    print("MQTT配置:")
    print(f"  主机: {mqtt_config.get('host', 'N/A')}")
    print(f"  端口: {mqtt_config.get('port', 'N/A')}")
    print(f"  协议: {mqtt_config.get('protocol', 'N/A')}")
    print(f"  主题: {mqtt_config.get('topic', 'N/A')}")
    print()
    
    # 测试订阅和接收
    try:
        import paho.mqtt.client as mqtt
        
        protocol = mqtt_config.get('protocol', 'mqtt')
        host = mqtt_config.get('host', '127.0.0.1')
        port = mqtt_config.get('port', 1883)
        username = mqtt_config.get('username')
        password = mqtt_config.get('password')
        topic = mqtt_config.get('topic', 'zebra/print')
        url = mqtt_config.get('url')
        
        print("正在连接MQTT服务器...")
        
        # 创建客户端
        if protocol in ['ws', 'wss']:
            transport = "websockets"
            ws_path = '/mqtt'
            if url:
                try:
                    from urllib.parse import urlparse
                    parsed = urlparse(url)
                    ws_path = parsed.path if parsed.path else '/mqtt'
                except:
                    pass
            
            print(f"  使用WebSocket，路径: {ws_path}")
            client = mqtt.Client(transport=transport)
            client.ws_set_options(path=ws_path)
        else:
            client = mqtt.Client()
        
        # 设置认证
        if username and password:
            client.username_pw_set(username, password)
        
        # 消息计数
        message_count = 0
        
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                print("✓ 连接成功")
                print(f"正在订阅主题: {topic}")
                result, mid = client.subscribe(topic, 0)
                if result == 0:
                    print(f"✓ 订阅请求已发送 (消息ID: {mid})")
                else:
                    print(f"✗ 订阅失败，错误码: {result}")
            else:
                print(f"✗ 连接失败，错误码: {rc}")
        
        def on_subscribe(client, userdata, mid, granted_qos):
            print(f"✓ 订阅成功确认 (消息ID: {mid}, QoS: {granted_qos})")
            print(f"✓ 主题: {topic}")
            print()
            print("=" * 70)
            print("等待接收消息...")
            print("=" * 70)
            print("提示：请在另一个终端发送测试消息")
            print("示例：")
            print(f'  python -c "import paho.mqtt.client as mqtt; import json; c=mqtt.Client(); c.connect(\'{host}\', {port}); c.publish(\'{topic}\', json.dumps({{\"print_type\": \"label\", \"zpl_code\": \"^XA^FO50,50^A0N,50,50^FDTest^FS^XZ\"}})); c.disconnect()"')
            print()
            print("按 Ctrl+C 退出")
            print("=" * 70)
            print()
        
        def on_message(client, userdata, msg):
            nonlocal message_count
            message_count += 1
            print(f"\n[消息 #{message_count}]")
            print(f"主题: {msg.topic}")
            print(f"长度: {len(msg.payload)} 字节")
            try:
                payload_str = msg.payload.decode('utf-8')
                print(f"内容: {payload_str[:500]}")
                try:
                    data = json.loads(payload_str)
                    print(f"JSON解析成功:")
                    print(json.dumps(data, ensure_ascii=False, indent=2))
                except json.JSONDecodeError:
                    print("⚠ 不是有效的JSON格式")
            except Exception as e:
                print(f"✗ 解码失败: {e}")
            print("-" * 70)
        
        def on_disconnect(client, userdata, rc):
            if rc != 0:
                print(f"\n✗ 意外断开连接 (错误码: {rc})")
        
        client.on_connect = on_connect
        client.on_subscribe = on_subscribe
        client.on_message = on_message
        client.on_disconnect = on_disconnect
        
        # 启动非阻塞循环
        client.loop_start()
        
        # 连接
        try:
            if protocol in ['wss', 'mqtts', 'ssl']:
                client.tls_set()
            
            result = client.connect(host, port, 60)
            if result != 0:
                print(f"✗ 连接调用失败，返回码: {result}")
                client.loop_stop()
                return False
            
            # 等待连接和订阅
            time.sleep(2)
            
            # 保持运行
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print(f"\n\n收到 {message_count} 条消息")
                print("正在断开连接...")
                client.loop_stop()
                client.disconnect()
                return True
                
        except Exception as e:
            print(f"✗ 连接异常: {e}")
            import traceback
            traceback.print_exc()
            client.loop_stop()
            return False
            
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
    try:
        test_mqtt_receive()
    except KeyboardInterrupt:
        print("\n\n测试已中断")
        sys.exit(0)

