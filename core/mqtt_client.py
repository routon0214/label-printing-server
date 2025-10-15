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
from core.pdf_printer import PDFPrinter
from core.escpos_printer import ESCPOSPrinter


class LabelPrintMQTT:
    """MQTT标签打印客户端（跨平台）"""
    
    def __init__(self, broker_host, broker_port=1883, topic="zebra/print", 
                 username=None, password=None, printer_config=None, printers_config=None):
        """
        初始化MQTT客户端
        
        Args:
            broker_host: MQTT服务器地址
            broker_port: MQTT服务器端口
            topic: 订阅的主题
            username: MQTT用户名
            password: MQTT密码
            printer_config: 单打印机配置（兼容旧版）
            printers_config: 多打印机配置（新版）
        """
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.topic = topic
        self.username = username
        self.password = password
        
        # 打印机映射表 {print_type: printer_instance}
        self.printer_map = {}
        self.default_printer = None
        
        # 如果有多打印机配置（新版）
        if printers_config and isinstance(printers_config, list):
            self._init_multiple_printers(printers_config)
        # 否则使用单打印机配置（旧版兼容）
        elif printer_config:
            self._init_single_printer(printer_config)
        else:
            # 默认配置
            self._init_default_printers()
        
        self.client = None
        self.zpl_generator = ZPLGenerator()
    
    def _init_multiple_printers(self, printers_config):
        """初始化多打印机配置"""
        print(f"初始化多打印机配置，共 {len(printers_config)} 台打印机")
        
        for printer_cfg in printers_config:
            name = printer_cfg.get('name', '未命名')
            types = printer_cfg.get('types', [])
            is_default = printer_cfg.get('default', False)
            
            # 兼容旧的 print_type 字段（单个值）
            if not types and 'print_type' in printer_cfg:
                old_type = printer_cfg.get('print_type')
                if old_type == '*':
                    types = ['*']
                else:
                    types = [old_type]
                print(f"  注意: 打印机 {name} 使用了旧的 'print_type' 字段，建议改用 'types' 数组")
            
            # 验证配置
            if not types:
                print(f"  ⚠ 警告: 打印机 {name} 未指定类型，跳过")
                continue
            
            print(f"  配置打印机: {name} - 类型: {types}")
            
            # 为每种类型创建对应的打印机实例
            for print_type in types:
                if print_type == '*':
                    # 通用打印机，支持所有类型
                    print(f"    ✓ {name} 设置为通用打印机")
                    self._add_printer_for_all_types(printer_cfg)
                    break  # 通配符不需要继续处理其他类型
                elif print_type == 'label':
                    self.printer_map['label'] = self._create_zebra_printer(printer_cfg)
                    print(f"    ✓ 标签打印 → {name}")
                elif print_type == 'pdf':
                    self.printer_map['pdf'] = self._create_pdf_printer(printer_cfg)
                    print(f"    ✓ PDF打印 → {name}")
                elif print_type in ['receipt', 'escpos']:
                    self.printer_map['receipt'] = self._create_escpos_printer(printer_cfg)
                    self.printer_map['escpos'] = self.printer_map['receipt']
                    print(f"    ✓ 小票打印 → {name}")
                else:
                    print(f"    ⚠ 未知的打印类型: {print_type}")
            
            # 设置默认打印机
            if is_default:
                self.default_printer = printer_cfg
                print(f"    ⭐ {name} 设置为默认打印机")
    
    def _init_single_printer(self, printer_config):
        """初始化单打印机配置（兼容旧版）"""
        print("使用单打印机配置（兼容模式）")
        self._add_printer_for_all_types(printer_config)
    
    def _init_default_printers(self):
        """初始化默认打印机（自动检测）"""
        print("使用默认配置，自动检测打印机")
        default_config = {'name': None, 'ip': None, 'port': 9100, 'device': None}
        self._add_printer_for_all_types(default_config)
    
    def _add_printer_for_all_types(self, printer_cfg):
        """为所有类型添加打印机"""
        self.printer_map['label'] = self._create_zebra_printer(printer_cfg)
        self.printer_map['pdf'] = self._create_pdf_printer(printer_cfg)
        self.printer_map['receipt'] = self._create_escpos_printer(printer_cfg)
        self.printer_map['escpos'] = self.printer_map['receipt']
    
    def _create_zebra_printer(self, cfg):
        """创建ZPL打印机实例"""
        return ZebraPrinter(
            printer_name=cfg.get('name'),
            printer_ip=cfg.get('ip'),
            printer_port=cfg.get('port', 9100),
            device_path=cfg.get('device')
        )
    
    def _create_pdf_printer(self, cfg):
        """创建PDF打印机实例"""
        return PDFPrinter(printer_name=cfg.get('name'))
    
    def _create_escpos_printer(self, cfg):
        """创建ESC/POS打印机实例"""
        return ESCPOSPrinter(
            printer_ip=cfg.get('ip'),
            printer_port=cfg.get('port', 9100),
            printer_name=cfg.get('name'),
            device_path=cfg.get('device')
        )
    
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
            data = json.loads(msg.payload.decode('utf-8'))
            print(f"数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
            
            # 判断打印类型
            print_type = data.get('print_type', 'label')  # 默认是标签打印
            
            # 根据打印类型选择对应的打印机
            if print_type == 'pdf':
                # PDF文档打印
                print("类型: PDF文档打印")
                
                # 获取对应的打印机
                pdf_printer = self.printer_map.get('pdf')
                if not pdf_printer:
                    print("✗ 错误：未配置PDF打印机")
                    success = False
                else:
                    pdf_data = data.get('pdf_data') or data.get('pdf_file')
                    printer_name = data.get('printer')
                    
                    if not pdf_data:
                        print("✗ 错误：缺少PDF数据")
                        success = False
                    else:
                        success = pdf_printer.print_pdf(pdf_data, printer_name)
                
                # PDF打印结果
                if success:
                    print(f"{'='*60}\n")
                else:
                    print("✗ PDF打印失败")
                    print(f"{'='*60}\n")
            
            elif print_type == 'receipt' or print_type == 'escpos':
                # ESC/POS小票打印
                print("类型: ESC/POS小票打印")
                
                # 获取对应的打印机
                receipt_printer = self.printer_map.get('receipt')
                if not receipt_printer:
                    print("✗ 错误：未配置ESC/POS打印机")
                    success = False
                else:
                    success = receipt_printer.print_receipt(data)
                
                # 打印结果
                if success:
                    print(f"{'='*60}\n")
                else:
                    print("✗ ESC/POS打印失败")
                    print(f"{'='*60}\n")
                    
            else:
                # 标签打印（默认）
                print("类型: ZPL标签打印")
                
                # 获取对应的打印机
                label_printer = self.printer_map.get('label')
                if not label_printer:
                    print("✗ 错误：未配置标签打印机")
                    success = False
                else:
                    # 生成ZPL代码
                    zpl_code = self.zpl_generator.generate_label_zpl(data)
                    # 打印
                    success = label_printer.print_label(zpl_code)
                
                # 标签打印结果
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
            print("打印机MQTT服务")
            print("="*60)
            print(f"MQTT服务器: {self.broker_host}:{self.broker_port}")
            print(f"订阅主题: {self.topic}")
            
            # 显示已配置的打印机
            if self.printer_map:
                print("已配置的打印机:")
                for print_type, printer in self.printer_map.items():
                    if print_type != 'escpos':  # 跳过 escpos 别名
                        printer_info = "自动检测"
                        if hasattr(printer, 'printer_name') and printer.printer_name:
                            printer_info = printer.printer_name
                        elif hasattr(printer, 'printer_ip') and printer.printer_ip:
                            printer_info = printer.printer_ip
                        print(f"  {print_type}: {printer_info}")
            else:
                print("打印机: 未配置")
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

