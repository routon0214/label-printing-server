#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MQTT客户端模块
提供MQTT消息接收和处理功能
"""

import json
import datetime
from core.printer import ZebraPrinter
from core.zpl_generator import ZPLGenerator


class LabelPrintMQTT:
    """MQTT标签打印客户端（跨平台）"""
    
    def __init__(self, broker_host, broker_port=1883, topic="zebra/print", 
                 username=None, password=None, printer_config=None):
        """
        初始化MQTT客户端
        
        Args:
            broker_host: MQTT服务器地址
            broker_port: MQTT服务器端口
            topic: 订阅的主题
            username: MQTT用户名
            password: MQTT密码
            printer_config: 打印机配置字典
        """
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.topic = topic
        self.username = username
        self.password = password
        
        # 初始化打印机
        if printer_config:
            self.printer = ZebraPrinter(
                printer_name=printer_config.get('name'),
                printer_ip=printer_config.get('ip'),
                printer_port=printer_config.get('port', 9100),
                device_path=printer_config.get('device')
            )
        else:
            self.printer = ZebraPrinter()
        
        self.client = None
        self.zpl_generator = ZPLGenerator()
    
    def on_connect(self, client, userdata, flags, rc):
        """连接回调"""
        if rc == 0:
            print(f"✓ 已连接到MQTT服务器: {self.broker_host}:{self.broker_port}")
            print(f"✓ 订阅主题: {self.topic}")
            client.subscribe(self.topic)
        else:
            print(f"✗ 连接失败，错误码: {rc}")
    
    def on_message(self, client, userdata, msg):
        """消息回调"""
        try:
            print(f"\n{'='*60}")
            print(f"收到打印任务")
            print(f"主题: {msg.topic}")
            
            # 解析JSON数据
            label_data = json.loads(msg.payload.decode('utf-8'))
            print(f"数据: {json.dumps(label_data, ensure_ascii=False, indent=2)}")
            
            # 生成ZPL代码
            zpl_code = self.zpl_generator.generate_label_zpl(label_data)
            
            # 打印
            success = self.printer.print_label(zpl_code)
            
            if success:
                print(f"{'='*60}\n")
            else:
                # 保存失败的ZPL到文件
                try:
                    import os
                    os.makedirs('failed_labels', exist_ok=True)
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"failed_labels/failed_label_{timestamp}.zpl"
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(zpl_code)
                    print(f"ZPL已保存到: {filename}")
                except Exception as save_error:
                    print(f"警告：无法保存失败的ZPL: {save_error}")
                print(f"{'='*60}\n")
                
        except json.JSONDecodeError as e:
            print(f"✗ JSON解析失败: {e}")
        except Exception as e:
            print(f"✗ 处理消息失败: {e}")
            import traceback
            traceback.print_exc()
    
    def on_disconnect(self, client, userdata, rc):
        """断开连接回调"""
        print(f"✗ 断开连接，错误码: {rc}")
        if rc != 0:
            print("尝试重新连接...")
    
    def start(self):
        """启动MQTT客户端"""
        try:
            import paho.mqtt.client as mqtt
            
            print("="*60)
            print("斑马打印机MQTT服务")
            print("="*60)
            print(f"MQTT服务器: {self.broker_host}:{self.broker_port}")
            print(f"订阅主题: {self.topic}")
            print(f"打印机: {self.printer.printer_name or self.printer.printer_ip or '未找到'}")
            print("="*60)
            
            # 创建客户端
            self.client = mqtt.Client()
            self.client.on_connect = self.on_connect
            self.client.on_message = self.on_message
            self.client.on_disconnect = self.on_disconnect
            
            # 设置认证
            if self.username and self.password:
                self.client.username_pw_set(self.username, self.password)
            
            # 连接服务器
            print("\n正在连接MQTT服务器...")
            self.client.connect(self.broker_host, self.broker_port, 60)
            
            # 启动循环
            print("服务已启动，等待打印任务...\n")
            self.client.loop_forever()
            
        except ImportError:
            print("错误：需要安装 paho-mqtt 库")
            print("请运行: pip install paho-mqtt")
        except Exception as e:
            print(f"启动失败: {e}")
            import traceback
            traceback.print_exc()

