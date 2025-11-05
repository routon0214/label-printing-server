#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MQTT客户端模块
提供MQTT消息接收和处理功能
"""

import json
import datetime
import os
import sys
# 添加utils目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src'))
from src.core.printer import ZebraPrinter
from src.core.zpl_generator import ZPLGenerator
from src.core.pdf_printer import PDFPrinter
from src.core.escpos_printer import ESCPOSPrinter

# 导入日志模块
try:
    from src.utils.logger import get_logger
    logger = get_logger('mqtt_client', 'data/logs')
except ImportError:
    # 如果日志模块不可用，使用简单的print
    logger = None
    def log_info(msg):
        print(f"[INFO] {msg}")
    def log_error(msg):
        print(f"[ERROR] {msg}")
    def log_warning(msg):
        print(f"[WARNING] {msg}")
    def log_debug(msg):
        print(f"[DEBUG] {msg}")


class LabelPrintMQTT:
    """MQTT标签打印客户端（跨平台）"""
    
    def __init__(self, broker_host, broker_port=1883, topic="zebra/print", 
                 username=None, password=None, protocol=None, url=None,
                 printer_config=None, printers_config=None):
        """
        初始化MQTT客户端
        
        Args:
            broker_host: MQTT服务器地址
            broker_port: MQTT服务器端口
            topic: 订阅的主题
            username: MQTT用户名
            password: MQTT密码
            protocol: 协议类型（ws, wss, mqtt, mqtts, tcp等）
            url: 原始URL（用于WebSocket路径提取）
            printer_config: 单打印机配置（兼容旧版）
            printers_config: 多打印机配置（新版）
        """
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.topic = topic
        self.username = username
        self.password = password
        self.protocol = protocol
        self.url = url
        
        # 打印机映射表 {print_type: printer_instance}
        self.printer_map = {}  # 专用打印机映射
        self.fallback_printer_config = None  # 通用打印机配置（types: ["*"]）
        self.fallback_printers = {}  # 通用打印机实例缓存
        # 打印机配置信息（用于启动显示）
        self.printer_info_list = []
        
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
        # 连接状态标记
        self.is_connected = False
        self.connection_error = None
        
        # 日志记录
        if logger:
            logger.info(f"初始化MQTT客户端: {broker_host}:{broker_port}, 主题: {topic}")
            if protocol:
                logger.info(f"使用协议: {protocol}")
            if url:
                logger.info(f"连接URL: {url}")
    
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
            
            # 收集支持的格式
            supported_formats = []
            
            # 为每种类型创建对应的打印机实例
            receipt_configured = False  # 标记是否已配置receipt打印机，避免重复
            for print_type in types:
                if print_type == '*':
                    # 通用打印机，作为备选打印机（只有在找不到专用打印机时才使用）
                    print(f"    ✓ {name} 设置为通用打印机（备选）")
                    self.fallback_printer_config = printer_cfg
                    supported_formats = ['label(ZPL)', 'pdf', 'receipt(ESC/POS)']
                    break  # 通配符不需要继续处理其他类型
                elif print_type == 'label':
                    # 只有当该类型还没有专用打印机时才设置
                    if 'label' not in self.printer_map:
                        self.printer_map['label'] = self._create_zebra_printer(printer_cfg)
                        print(f"    ✓ 标签打印（专用） → {name}")
                        supported_formats.append('label(ZPL)')
                    else:
                        print(f"    ⚠ 标签打印机已存在，跳过 {name}")
                elif print_type == 'pdf':
                    if 'pdf' not in self.printer_map:
                        self.printer_map['pdf'] = self._create_pdf_printer(printer_cfg)
                        print(f"    ✓ PDF打印（专用） → {name}")
                        supported_formats.append('pdf')
                    else:
                        print(f"    ⚠ PDF打印机已存在，跳过 {name}")
                elif print_type in ['receipt', 'escpos']:
                    if not receipt_configured and 'receipt' not in self.printer_map:
                        self.printer_map['receipt'] = self._create_escpos_printer(printer_cfg)
                        self.printer_map['escpos'] = self.printer_map['receipt']
                        print(f"    ✓ 小票打印（专用） → {name}")
                        supported_formats.append('receipt(ESC/POS)')
                        receipt_configured = True
                    else:
                        print(f"    ⚠ 小票打印机已存在，跳过 {name}")
                else:
                    print(f"    ⚠ 未知的打印类型: {print_type}")
            
            # 保存打印机信息
            printer_info = {
                'name': name,
                'formats': supported_formats,
                'is_fallback': '*' in types,
                'config': printer_cfg
            }
            self.printer_info_list.append(printer_info)
    
    def _get_printer(self, print_type):
        """
        获取指定类型的打印机
        优先返回专用打印机，找不到则返回通用打印机
        
        Args:
            print_type: 打印类型 ('label', 'pdf', 'receipt', 'escpos')
            
        Returns:
            打印机实例，如果没有返回 None
        """
        # 1. 优先查找专用打印机
        if print_type in self.printer_map:
            return self.printer_map[print_type]
        
        # 2. 如果没有专用打印机，使用备选打印机
        if self.fallback_printer_config:
            # 检查是否已经创建过该类型的备选打印机实例
            if print_type not in self.fallback_printers:
                # 创建备选打印机实例
                if print_type == 'label':
                    self.fallback_printers[print_type] = self._create_zebra_printer(self.fallback_printer_config)
                elif print_type == 'pdf':
                    self.fallback_printers[print_type] = self._create_pdf_printer(self.fallback_printer_config)
                elif print_type in ['receipt', 'escpos']:
                    self.fallback_printers[print_type] = self._create_escpos_printer(self.fallback_printer_config)
                else:
                    return None
            
            return self.fallback_printers.get(print_type)
        
        # 3. 没有找到任何打印机
        return None
    
    def _init_single_printer(self, printer_config):
        """初始化单打印机配置（兼容旧版）"""
        print("使用单打印机配置（兼容模式）")
        # 旧版单打印机配置作为备选打印机
        self.fallback_printer_config = printer_config
        
        # 添加打印机信息
        name = printer_config.get('name', '通用打印机')
        printer_info = {
            'name': name,
            'formats': ['label(ZPL)', 'pdf', 'receipt(ESC/POS)'],
            'is_fallback': True,
            'config': printer_config
        }
        self.printer_info_list.append(printer_info)
    
    def _init_default_printers(self):
        """初始化默认打印机（自动检测）"""
        print("使用默认配置，自动检测打印机")
        default_config = {'name': None, 'ip': None, 'port': 9100, 'device': None}
        # 作为备选打印机
        self.fallback_printer_config = default_config
        
        # 添加打印机信息
        printer_info = {
            'name': '自动检测打印机',
            'formats': ['label(ZPL)', 'pdf', 'receipt(ESC/POS)'],
            'is_fallback': True,
            'config': default_config
        }
        self.printer_info_list.append(printer_info)
    
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
            self.is_connected = True
            self.connection_error = None
            msg = f"✓ 已连接到MQTT服务器: {self.broker_host}:{self.broker_port}"
            print(msg)
            if logger:
                logger.info(msg)
            
            print(f"正在订阅主题: {self.topic}")
            if logger:
                logger.info(f"正在订阅主题: {self.topic}")
            
            # 订阅主题，QoS=0
            result, mid = client.subscribe(self.topic, 0)
            if result == 0:
                msg = f"✓ 订阅请求已发送 (消息ID: {mid})"
                print(msg)
                if logger:
                    logger.info(msg)
            else:
                error_msg = f"订阅失败，错误码: {result}"
                print(f"✗ {error_msg}")
                self.connection_error = error_msg
                if logger:
                    logger.error(error_msg)
        else:
            self.is_connected = False
            error_messages = {
                1: "协议版本不正确",
                2: "客户端标识符无效",
                3: "服务器不可用",
                4: "用户名或密码错误",
                5: "未授权"
            }
            error_msg = error_messages.get(rc, f"未知错误码: {rc}")
            self.connection_error = error_msg
            msg = f"✗ 连接失败，错误码: {rc} - {error_msg}"
            print(msg)
            if logger:
                logger.error(msg)
    
    def on_subscribe(self, client, userdata, mid, granted_qos):
        """订阅回调"""
        msg1 = f"✓ 订阅成功确认 (消息ID: {mid}, QoS: {granted_qos})"
        msg2 = f"✓ 主题: {self.topic}"
        msg3 = "服务已就绪，等待打印任务..."
        print(msg1)
        print(msg2)
        print(msg3 + "\n")
        if logger:
            logger.info(f"{msg1}, {msg2}")
            logger.info(msg3)
    
    def on_message(self, client, userdata, msg):
        """消息回调"""
        try:
            if logger:
                logger.info(f"收到MQTT消息 - 主题: {msg.topic}, 长度: {len(msg.payload)} 字节")
            
            print(f"\n{'='*60}")
            print(f"收到打印任务")
            print(f"主题: {msg.topic}")
            print(f"消息长度: {len(msg.payload)} 字节")
            
            # 解析JSON数据
            try:
                payload_str = msg.payload.decode('utf-8')
                preview = payload_str[:200] if len(payload_str) > 200 else payload_str
                print(f"消息内容: {preview}{'...' if len(payload_str) > 200 else ''}")
                if logger:
                    logger.debug(f"消息内容预览: {preview}")
            except Exception as decode_error:
                error_msg = f"消息解码失败: {decode_error}"
                print(f"✗ {error_msg}")
                print(f"原始数据: {msg.payload[:100]}")
                if logger:
                    logger.error(f"{error_msg}, 原始数据: {msg.payload[:100]}")
                return
            
            data = json.loads(payload_str)
            print(f"数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
            if logger:
                logger.info(f"消息解析成功，打印类型: {data.get('print_type', 'label')}")
            
            # 判断打印类型
            print_type = data.get('print_type', 'label')  # 默认是标签打印
            
            # 根据打印类型选择对应的打印机
            if print_type == 'pdf':
                # PDF文档打印
                print("类型: PDF文档打印")
                
                # 获取对应的打印机（优先专用，找不到用通用）
                pdf_printer = self._get_printer('pdf')
                if not pdf_printer:
                    print("✗ 错误：未配置PDF打印机")
                    success = False
                else:
                    # 判断是使用专用还是通用打印机
                    if 'pdf' in self.printer_map:
                        print("  使用: PDF专用打印机")
                    else:
                        print("  使用: 通用打印机（备选）")
                    
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
                
                # 获取对应的打印机（优先专用，找不到用通用）
                receipt_printer = self._get_printer('receipt')
                if not receipt_printer:
                    print("✗ 错误：未配置ESC/POS打印机")
                    success = False
                else:
                    # 判断是使用专用还是通用打印机
                    if 'receipt' in self.printer_map:
                        print("  使用: ESC/POS专用打印机")
                    else:
                        print("  使用: 通用打印机（备选）")
                    
                    # 检查是否使用原始文本格式
                    if 'raw_text' in data:
                        print("  格式: 原始文本")
                    else:
                        print("  格式: 结构化小票")
                    
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
                
                # 获取对应的打印机（优先专用，找不到用通用）
                label_printer = self._get_printer('label')
                if not label_printer:
                    print("✗ 错误：未配置标签打印机")
                    success = False
                else:
                    # 判断是使用专用还是通用打印机
                    if 'label' in self.printer_map:
                        print("  使用: 标签专用打印机")
                    else:
                        print("  使用: 通用打印机（备选）")
                    
                    # 获取ZPL代码：支持直接发送或自动生成
                    if 'zpl_code' in data:
                        # 直接使用提供的ZPL代码
                        zpl_code = data.get('zpl_code')
                        print("  ZPL来源: 直接提供")
                    else:
                        # 根据数据自动生成ZPL代码
                        zpl_code = self.zpl_generator.generate_label_zpl(data)
                        print("  ZPL来源: 自动生成")
                    
                    # 打印
                    success = label_printer.print_label(zpl_code)
                
                # 标签打印结果
                if success:
                    print(f"{'='*60}\n")
                else:
                    # 保存失败的ZPL到文件
                    try:
                        import os
                        os.makedirs('data/failed_labels', exist_ok=True)
                        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"data/failed_labels/failed_label_{timestamp}.zpl"
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
        self.is_connected = False
        if rc != 0:
            self.connection_error = f"意外断开，错误码: {rc}"
            print(f"✗ 断开连接，错误码: {rc}")
            print("尝试重新连接...")
        else:
            self.connection_error = None
            print("✓ 正常断开连接")
    
    def start(self):
        """启动MQTT客户端"""
        try:
            import paho.mqtt.client as mqtt
            
            print("="*70)
            print(" " * 20 + "打印机MQTT服务")
            print("="*70)
            print(f"MQTT服务器: {self.broker_host}:{self.broker_port}")
            print(f"订阅主题: {self.topic}")
            print("-"*70)
            
            # 显示已配置的打印机信息
            if self.printer_info_list:
                print("已配置的打印机:")
                for idx, printer_info in enumerate(self.printer_info_list, 1):
                    name = printer_info['name']
                    formats = printer_info['formats']
                    is_fallback = printer_info.get('is_fallback', False)
                    
                    # 获取实际的打印机名称或IP
                    config = printer_info['config']
                    actual_name = "自动检测"
                    
                    # 尝试从第一个格式的打印机实例获取实际名称
                    if formats and not is_fallback:
                        first_format = formats[0].split('(')[0]  # 提取格式名，去掉括号
                        if first_format == 'label':
                            printer_instance = self.printer_map.get('label')
                        elif first_format == 'pdf':
                            printer_instance = self.printer_map.get('pdf')
                        elif first_format == 'receipt':
                            printer_instance = self.printer_map.get('receipt')
                        else:
                            printer_instance = None
                        
                        if printer_instance:
                            if hasattr(printer_instance, 'printer_name') and printer_instance.printer_name:
                                actual_name = printer_instance.printer_name
                            elif hasattr(printer_instance, 'printer_ip') and printer_instance.printer_ip:
                                actual_name = f"网络打印机 {printer_instance.printer_ip}"
                    
                    # 显示打印机信息
                    type_mark = " 🔄 备选" if is_fallback else " ⭐ 专用"
                    print(f"\n  [{idx}] {name}{type_mark}")
                    print(f"      设备: {actual_name}")
                    print(f"      支持格式: {', '.join(formats)}")
                    if is_fallback:
                        print(f"      说明: 当找不到专用打印机时使用")
            elif self.printer_map:
                print("已配置的打印机: 通用打印机（兼容模式）")
                print("  支持格式: label(ZPL), pdf, receipt(ESC/POS)")
            else:
                print("打印机: 未配置")
            
            print("="*70)
            
            # 创建客户端 - 根据协议选择传输方式
            if self.protocol in ['ws', 'wss']:
                # WebSocket连接
                transport = "websockets"
                # 从URL中提取WebSocket路径
                ws_path = '/mqtt'  # 默认路径
                ws_headers = {}
                
                if self.url:
                    try:
                        from urllib.parse import urlparse
                        parsed = urlparse(self.url)
                        # 提取路径，如果没有路径则使用默认值
                        if parsed.path:
                            ws_path = parsed.path
                        else:
                            ws_path = '/mqtt'
                        
                        # 如果路径为空字符串，也使用默认值
                        if not ws_path or ws_path == '/':
                            ws_path = '/mqtt'
                        
                        # 记录解析结果
                        if logger:
                            logger.info(f"WebSocket URL解析: 主机={parsed.hostname}, 端口={parsed.port}, 路径={ws_path}")
                        
                    except Exception as parse_error:
                        ws_path = '/mqtt'
                        if logger:
                            logger.warning(f"WebSocket URL解析失败: {parse_error}, 使用默认路径: {ws_path}")
                
                print(f"使用WebSocket连接")
                print(f"  主机: {self.broker_host}")
                print(f"  端口: {self.broker_port}")
                print(f"  路径: {ws_path}")
                
                if logger:
                    logger.info(f"创建WebSocket客户端 - 主机: {self.broker_host}, 端口: {self.broker_port}, 路径: {ws_path}")
                
                # 创建WebSocket客户端
                self.client = mqtt.Client(transport=transport)
                
                # 设置WebSocket选项
                try:
                    self.client.ws_set_options(path=ws_path, headers=ws_headers)
                    if logger:
                        logger.info(f"WebSocket选项已设置: path={ws_path}")
                except Exception as ws_error:
                    if logger:
                        logger.error(f"设置WebSocket选项失败: {ws_error}")
                    # 尝试只设置路径
                    try:
                        self.client.ws_set_options(path=ws_path)
                    except:
                        pass
            else:
                # TCP连接（mqtt, mqtts, tcp等）
                self.client = mqtt.Client()
            
            self.client.on_connect = self.on_connect
            self.client.on_message = self.on_message
            self.client.on_disconnect = self.on_disconnect
            self.client.on_subscribe = self.on_subscribe
            
            # 设置认证
            if self.username and self.password:
                self.client.username_pw_set(self.username, self.password)
            
            # 连接服务器
            print("\n正在连接MQTT服务器...")
            if logger:
                logger.info(f"开始连接MQTT服务器: {self.broker_host}:{self.broker_port}")
                if self.protocol:
                    logger.info(f"使用协议: {self.protocol}")
                if self.url:
                    logger.info(f"连接URL: {self.url}")
            
            if self.protocol in ['wss', 'mqtts', 'ssl']:
                # SSL/TLS连接
                self.client.tls_set()
                if logger:
                    logger.info("已启用SSL/TLS加密")
            
            # 启动非阻塞循环（在连接前启动，以便处理连接回调）
            self.client.loop_start()
            if logger:
                logger.debug("MQTT事件循环已启动")
            
            try:
                # 对于WebSocket连接，需要确保在连接前所有设置都完成
                if self.protocol in ['ws', 'wss']:
                    if logger:
                        logger.info(f"准备WebSocket连接 - 主机: {self.broker_host}, 端口: {self.broker_port}")
                    # WebSocket连接可能需要特殊处理
                    # 先启动循环，再连接
                    print(f"正在连接WebSocket服务器: ws://{self.broker_host}:{self.broker_port}")
                else:
                    if logger:
                        logger.info(f"准备TCP连接 - 主机: {self.broker_host}, 端口: {self.broker_port}")
                
                result = self.client.connect(self.broker_host, self.broker_port, 60)
                
                if logger:
                    logger.info(f"connect()调用完成，返回码: {result} (0=成功, 其他=错误)")
                    if result != 0:
                        logger.error(f"连接调用返回错误码: {result}")
                if result != 0:
                    # 连接返回错误码
                    error_messages = {
                        1: "协议版本不正确",
                        2: "客户端标识符无效",
                        3: "服务器不可用",
                        4: "用户名或密码错误",
                        5: "未授权"
                    }
                    error_msg = error_messages.get(result, f"连接失败，错误码: {result}")
                    self.connection_error = error_msg
                    self.is_connected = False
                    print(f"✗ {error_msg}")
                    self.client.loop_stop()
                    return
                
                # 等待连接建立（最多等待5秒）
                import time
                timeout = 5
                start_time = time.time()
                while not self.is_connected and (time.time() - start_time) < timeout:
                    if self.connection_error:
                        # 如果有错误信息，说明连接失败
                        print(f"✗ {self.connection_error}")
                        self.client.loop_stop()
                        return
                    time.sleep(0.1)
                
                if not self.is_connected:
                    if not self.connection_error:
                        self.connection_error = "连接超时，请检查服务器地址和端口"
                    print(f"✗ {self.connection_error}")
                    self.client.loop_stop()
                    return
                
                print("服务已启动，等待打印任务...\n")
                
                # 保持线程运行，定期检查连接状态
                import time
                while True:
                    time.sleep(2)
                    # 检查连接状态
                    if self.client:
                        try:
                            # 检查是否实际连接
                            if hasattr(self.client, 'is_connected'):
                                if not self.client.is_connected():
                                    if self.is_connected:
                                        # 之前是连接的，现在断开了
                                        self.is_connected = False
                                        self.connection_error = "连接已断开"
                                        print("✗ 检测到连接断开")
                        except:
                            pass
                            
            except Exception as conn_error:
                # 连接异常（如网络错误）
                self.connection_error = f"连接异常: {str(conn_error)}"
                self.is_connected = False
                print(f"✗ 连接异常: {conn_error}")
                import traceback
                traceback.print_exc()
                if self.client:
                    try:
                        self.client.loop_stop()
                    except:
                        pass
                # 不抛出异常，让线程正常结束
                return
            
        except ImportError:
            self.connection_error = "需要安装 paho-mqtt 库"
            self.is_connected = False
            print("错误：需要安装 paho-mqtt 库")
            print("请运行: pip install paho-mqtt")
        except Exception as e:
            self.connection_error = f"启动失败: {str(e)}"
            self.is_connected = False
            print(f"启动失败: {e}")
            import traceback
            traceback.print_exc()

