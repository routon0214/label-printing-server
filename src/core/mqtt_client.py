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
                 client_id=None, printer_config=None, printers_config=None):
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
            client_id: MQTT客户端ID（如果为None，则自动生成随机ID）
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
        self.client_id = client_id
        
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
        # 自动重连配置
        self.auto_reconnect = True  # 是否启用自动重连
        self.reconnect_delay = 5  # 重连延迟（秒）
        self.max_reconnect_delay = 60  # 最大重连延迟（秒）
        self.reconnect_count = 0  # 重连次数计数
        self.is_stopping = False  # 是否正在停止（用于区分主动断开和意外断开）
        
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
        print("\n[回调] on_connect 被触发")
        print(f"  返回码 (rc): {rc}")
        print(f"  标志 (flags): {flags}")
        if logger:
            logger.info(f"on_connect回调被触发 - rc={rc}, flags={flags}")
        
        if rc == 0:
            print("  ✓ 连接成功！")
            self.is_connected = True
            self.connection_error = None
            # 重置重连计数器（连接成功后）
            if self.reconnect_count > 0:
                print(f"  ✓ 重连成功！（共尝试 {self.reconnect_count} 次）")
                if logger:
                    logger.info(f"重连成功！共尝试了 {self.reconnect_count} 次")
            self.reconnect_count = 0
            # 如果client_id未设置，尝试从客户端获取（paho-mqtt自动生成的）
            if not self.client_id:
                try:
                    if hasattr(client, '_client_id') and client._client_id:
                        self.client_id = client._client_id
                        print(f"  获取到自动生成的客户端ID: {self.client_id}")
                        if logger:
                            logger.info(f"获取到自动生成的客户端ID: {self.client_id}")
                except:
                    pass
            msg = f"✓ 已连接到MQTT服务器: {self.broker_host}:{self.broker_port}"
            if self.client_id:
                msg += f" (客户端ID: {self.client_id})"
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
            print(f"  ✗ 连接失败！")
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
                logger.error(f"连接详情 - 服务器: {self.broker_host}:{self.broker_port}, 协议: {self.protocol}")
    
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
        print(f"\n[回调] on_disconnect 被触发 - 错误码: {rc}")
        if logger:
            logger.info(f"on_disconnect回调被触发 - rc={rc}")
        
        self.is_connected = False
        
        if rc != 0:
            # 意外断开
            self.connection_error = f"意外断开，错误码: {rc}"
            msg = f"✗ 意外断开连接，错误码: {rc}"
            print(msg)
            if logger:
                logger.warning(msg)
                logger.warning(f"断开时的服务器信息 - {self.broker_host}:{self.broker_port}")
            
            # 自动重连（如果启用且不是主动停止）
            if self.auto_reconnect and not self.is_stopping:
                self.reconnect_count += 1
                # 计算重连延迟（指数退避，但有上限）
                delay = min(self.reconnect_delay * (1.5 ** (self.reconnect_count - 1)), self.max_reconnect_delay)
                
                print(f"\n{'='*70}")
                print(f"自动重连机制已启动")
                print(f"  重连次数: {self.reconnect_count}")
                print(f"  延迟时间: {delay:.1f} 秒")
                print(f"{'='*70}")
                
                if logger:
                    logger.info(f"启动自动重连 - 第 {self.reconnect_count} 次尝试，延迟 {delay:.1f} 秒")
                
                # 在后台线程中延迟重连
                import threading
                import time
                
                def delayed_reconnect():
                    time.sleep(delay)
                    if not self.is_stopping and not self.is_connected:
                        print(f"\n开始重连到MQTT服务器...")
                        if logger:
                            logger.info(f"开始第 {self.reconnect_count} 次重连尝试")
                        try:
                            # 尝试重连
                            client.reconnect()
                            if logger:
                                logger.info("reconnect() 调用完成")
                        except Exception as e:
                            print(f"✗ 重连失败: {e}")
                            if logger:
                                logger.error(f"重连失败: {e}")
                
                reconnect_thread = threading.Thread(target=delayed_reconnect, daemon=True, name="MQTT-Reconnect-Thread")
                reconnect_thread.start()
        else:
            # 正常断开（主动断开）
            self.connection_error = None
            msg = "✓ 正常断开连接"
            print(msg)
            if logger:
                logger.info(msg)
    
    def on_log(self, client, userdata, level, buf):
        """日志回调（用于调试）"""
        # paho-mqtt的日志级别: DEBUG=1, INFO=2, NOTICE=3, WARNING=4, ERROR=5
        # 控制台输出（只输出重要信息）
        if level >= 4:  # WARNING及以上才输出到控制台
            print(f"[MQTT-{level}] {buf}")
        
        # 文件日志（记录所有级别）
        if logger:
            if level <= 1:  # DEBUG
                logger.debug(f"MQTT调试: {buf}")
            elif level == 2:  # INFO
                logger.info(f"MQTT信息: {buf}")
            elif level == 3:  # NOTICE
                logger.info(f"MQTT通知: {buf}")
            elif level == 4:  # WARNING
                logger.warning(f"MQTT警告: {buf}")
            elif level >= 5:  # ERROR
                logger.error(f"MQTT错误: {buf}")
    
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
                
                protocol_name = "WebSocket Secure (WSS)" if self.protocol == 'wss' else "WebSocket (WS)"
                print(f"使用{protocol_name}连接")
                print(f"  主机: {self.broker_host}")
                print(f"  端口: {self.broker_port}")
                print(f"  路径: {ws_path}")
                
                if logger:
                    logger.info(f"创建WebSocket客户端 - 主机: {self.broker_host}, 端口: {self.broker_port}, 路径: {ws_path}")
                
                # 创建WebSocket客户端
                # 处理client_id：如果为None或空字符串，让paho-mqtt自动生成
                print("  创建MQTT客户端实例...")
                if self.client_id:
                    # 使用指定的客户端ID
                    print(f"  客户端ID: {self.client_id}")
                    if logger:
                        logger.info(f"创建WebSocket客户端 - 客户端ID: {self.client_id}")
                    self.client = mqtt.Client(client_id=self.client_id, transport=transport)
                    print("  ✓ 客户端实例已创建")
                    if logger:
                        logger.info(f"✓ WebSocket客户端已创建，使用客户端ID: {self.client_id}")
                else:
                    # 不传client_id，让paho-mqtt自动生成
                    print(f"  客户端ID: 自动生成")
                    if logger:
                        logger.info("创建WebSocket客户端 - 客户端ID将自动生成")
                    self.client = mqtt.Client(transport=transport)
                    print("  ✓ 客户端实例已创建")
                    # paho-mqtt会自动生成client_id，我们稍后可以从客户端获取
                    if logger:
                        logger.info("✓ WebSocket客户端已创建，客户端ID将自动生成")
                
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
                # TCP连接（mqtt, tcp, mqtts等）
                # 注意：paho-mqtt默认使用TCP传输，所以mqtt://和tcp://都使用标准Client
                # mqtts://会在后面启用SSL/TLS
                protocol_name = "MQTT over SSL/TLS (MQTTs)" if self.protocol == 'mqtts' else "MQTT (TCP)"
                if logger:
                    logger.info(f"创建TCP客户端 (协议: {self.protocol} - {protocol_name})")
                print(f"使用{protocol_name}连接")
                print(f"  主机: {self.broker_host}")
                print(f"  端口: {self.broker_port}")
                
                # 处理client_id：如果为None或空字符串，让paho-mqtt自动生成
                print("  创建MQTT客户端实例...")
                if self.client_id:
                    # 使用指定的客户端ID
                    print(f"  客户端ID: {self.client_id}")
                    if logger:
                        logger.info(f"创建TCP客户端 - 客户端ID: {self.client_id}")
                    self.client = mqtt.Client(client_id=self.client_id)
                    print("  ✓ 客户端实例已创建")
                    if logger:
                        logger.info(f"✓ TCP客户端已创建，使用客户端ID: {self.client_id}")
                else:
                    # 不传client_id，让paho-mqtt自动生成
                    print(f"  客户端ID: 自动生成")
                    if logger:
                        logger.info("创建TCP客户端 - 客户端ID将自动生成")
                    self.client = mqtt.Client()
                    print("  ✓ 客户端实例已创建")
                    # paho-mqtt会自动生成client_id，我们稍后可以从客户端获取
                    if logger:
                        logger.info("✓ TCP客户端已创建，客户端ID将自动生成")
            
            # 设置回调函数
            print("  设置MQTT回调函数...")
            self.client.on_connect = self.on_connect
            self.client.on_message = self.on_message
            self.client.on_disconnect = self.on_disconnect
            self.client.on_subscribe = self.on_subscribe
            print("  ✓ 回调函数已设置 (on_connect, on_message, on_disconnect, on_subscribe)")
            
            # 启用日志回调（用于调试）
            if logger:
                self.client.on_log = self.on_log
                print("  ✓ 日志回调已启用")
                logger.info("✓ MQTT回调函数已设置（包括日志回调）")
                # 设置日志级别（可选，用于调试）
                # self.client.enable_logger(logger)
            else:
                print("  ⚠ 日志模块未加载，日志回调未启用")
            
            # 设置认证
            if self.username and self.password:
                print(f"  设置认证信息 (用户名: {self.username})...")
                self.client.username_pw_set(self.username, self.password)
                print("  ✓ 认证信息已设置")
                if logger:
                    logger.info(f"✓ MQTT认证已配置 - 用户名: {self.username}")
            else:
                print("  认证: 无（匿名连接）")
                if logger:
                    logger.info("MQTT连接未配置认证（匿名连接）")
            
            # 连接服务器
            print("\n" + "="*70)
            print("准备连接MQTT服务器")
            print("="*70)
            print("连接配置摘要:")
            print(f"  协议: {self.protocol or 'mqtt'}")
            print(f"  服务器: {self.broker_host}:{self.broker_port}")
            if self.url:
                print(f"  原始URL: {self.url}")
            if self.username:
                print(f"  认证: 用户名={self.username}, 密码=***")
            else:
                print(f"  认证: 无（匿名）")
            print(f"  客户端状态: is_connected={self.is_connected}")
            print("="*70)
            
            if logger:
                logger.info("="*70)
                logger.info(f"开始连接MQTT服务器: {self.broker_host}:{self.broker_port}")
                if self.protocol:
                    logger.info(f"使用协议: {self.protocol}")
                if self.url:
                    logger.info(f"连接URL: {self.url}")
                if self.username:
                    logger.info(f"认证信息: 用户名={self.username}")
                logger.info("="*70)
            
            # 处理SSL/TLS连接
            # wss: WebSocket Secure (HTTPS) - 在WebSocket传输层启用SSL
            # mqtts: MQTT over SSL/TLS - 在TCP传输层启用SSL
            if self.protocol in ['wss', 'mqtts']:
                # SSL/TLS连接
                try:
                    # 设置TLS（使用默认CA证书）
                    self.client.tls_set()
                    if logger:
                        logger.info(f"已启用SSL/TLS加密 (协议: {self.protocol})")
                    print(f"使用SSL/TLS加密连接 ({self.protocol})")
                except Exception as tls_error:
                    error_msg = f"启用SSL/TLS失败: {tls_error}"
                    if logger:
                        logger.error(error_msg)
                    print(f"⚠ 警告：{error_msg}")
                    # 对于某些自签名证书，可以尝试不验证证书（仅用于测试）
                    try:
                        import ssl
                        self.client.tls_set(cert_reqs=ssl.CERT_NONE)
                        if logger:
                            logger.warning("使用不验证证书的SSL/TLS模式（仅用于测试）")
                        print("⚠ 使用不验证证书的SSL模式（仅用于测试）")
                    except Exception as tls_fallback_error:
                        if logger:
                            logger.error(f"SSL/TLS回退模式也失败: {tls_fallback_error}")
                        print(f"✗ SSL/TLS配置失败，连接可能无法建立")
            
            # 启动非阻塞循环（在连接前启动，以便处理连接回调）
            print("\n[步骤1] 启动MQTT事件循环...")
            if logger:
                logger.info("启动MQTT事件循环 (loop_start)")
            self.client.loop_start()
            print("  ✓ 事件循环已启动")
            if logger:
                logger.info("✓ MQTT事件循环已启动")
            
            try:
                # 对于WebSocket连接，需要确保在连接前所有设置都完成
                if self.protocol in ['ws', 'wss']:
                    if logger:
                        logger.info(f"准备WebSocket连接 - 主机: {self.broker_host}, 端口: {self.broker_port}")
                    # WebSocket连接可能需要特殊处理
                    # 先启动循环，再连接
                    protocol_prefix = 'wss' if self.protocol == 'wss' else 'ws'
                    print(f"正在连接WebSocket服务器: {protocol_prefix}://{self.broker_host}:{self.broker_port}")
                else:
                    if logger:
                        logger.info(f"准备TCP连接 - 主机: {self.broker_host}, 端口: {self.broker_port}")
                
                # 对于TCP连接，先测试网络连通性
                if self.protocol in ['mqtt', 'tcp']:
                    print("\n[步骤2] 测试网络连通性...")
                    if logger:
                        logger.info(f"测试TCP连接: {self.broker_host}:{self.broker_port}")
                    try:
                        import socket
                        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        test_socket.settimeout(3)
                        print(f"  正在连接 {self.broker_host}:{self.broker_port}...")
                        test_result = test_socket.connect_ex((self.broker_host, self.broker_port))
                        test_socket.close()
                        if test_result != 0:
                            error_msg = f"网络连接测试失败，无法连接到 {self.broker_host}:{self.broker_port}"
                            print(f"  ✗ {error_msg} (错误码: {test_result})")
                            if logger:
                                logger.error(f"{error_msg} (错误码: {test_result})")
                            self.connection_error = error_msg
                            self.is_connected = False
                            self.client.loop_stop()
                            print("\n" + "="*70)
                            print("连接失败：网络不通")
                            print("请检查:")
                            print(f"  1. 服务器地址是否正确: {self.broker_host}")
                            print(f"  2. 端口是否正确: {self.broker_port}")
                            print(f"  3. 防火墙是否允许连接")
                            print(f"  4. MQTT服务器是否运行")
                            print("="*70 + "\n")
                            return
                        else:
                            print(f"  ✓ 网络连接测试通过，服务器可达")
                            if logger:
                                logger.info(f"✓ 网络连接测试通过，服务器可达")
                    except Exception as test_error:
                        print(f"  ⚠ 网络测试异常: {test_error}，继续尝试MQTT连接")
                        if logger:
                            logger.warning(f"网络连接测试异常: {test_error}，继续尝试MQTT连接")
                
                # 调用MQTT连接
                print("\n[步骤3] 启动MQTT连接...")
                print(f"  目标服务器: {self.broker_host}")
                print(f"  目标端口: {self.broker_port}")
                print(f"  保活时间: 60秒")
                print(f"  调用 client.connect({self.broker_host}, {self.broker_port}, 60)...")
                if logger:
                    logger.info(f"准备调用MQTT connect() - 主机: {self.broker_host}, 端口: {self.broker_port}, 超时: 60秒")
                
                try:
                    result = self.client.connect(self.broker_host, self.broker_port, 60)
                    print(f"  ✓ connect() 调用完成")
                    print(f"  返回码: {result} {'(0=成功)' if result == 0 else '(错误)'}")
                    
                    if logger:
                        logger.info(f"connect()调用完成，返回码: {result} (0=成功, 其他=错误)")
                        if result != 0:
                            logger.error(f"连接调用返回错误码: {result}")
                except Exception as connect_ex:
                    print(f"  ✗ connect() 调用异常: {connect_ex}")
                    if logger:
                        logger.error(f"connect()调用异常: {connect_ex}")
                    import traceback
                    traceback.print_exc()
                    raise
                
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
                
                # 等待连接建立（WebSocket需要更长时间）
                import time
                timeout = 15 if self.protocol in ['ws', 'wss'] else 10  # WebSocket给更多时间
                start_time = time.time()
                last_log_time = 0
                
                print(f"\n[步骤4] 等待连接建立 (最多等待{timeout}秒)...")
                if logger:
                    protocol_type = 'WebSocket' if self.protocol in ['ws', 'wss'] else 'TCP'
                    logger.info(f"等待连接建立，超时时间: {timeout}秒 ({protocol_type})")
                
                while not self.is_connected and (time.time() - start_time) < timeout:
                    if self.connection_error:
                        # 如果有错误信息，说明连接失败
                        print(f"✗ {self.connection_error}")
                        if logger:
                            logger.error(f"连接过程中出错: {self.connection_error}")
                        self.client.loop_stop()
                        return
                    
                    elapsed = time.time() - start_time
                    # 每秒记录一次等待状态
                    if elapsed - last_log_time >= 1:
                        status_msg = f"  等待连接中... ({elapsed:.1f}/{timeout}秒)"
                        print(status_msg)
                        if logger:
                            logger.debug(f"等待连接中... ({elapsed:.1f}/{timeout}秒)")
                        last_log_time = elapsed
                    
                    # 检查客户端内部状态（用于调试）
                    if self.client:
                        try:
                            # 检查是否有socket创建
                            if hasattr(self.client, '_sock'):
                                if self.client._sock is None and elapsed > 2:
                                    # socket未创建，可能是连接失败
                                    if logger and elapsed - last_log_time >= 2:
                                        logger.debug("客户端socket未创建，可能连接失败或服务器拒绝")
                            # 检查连接状态
                            if hasattr(self.client, '_state'):
                                state = self.client._state
                                if logger and elapsed > 5 and state != 1:
                                    # 不是连接状态（1=connected）
                                    logger.debug(f"客户端状态: {state} (1=connected, 0=disconnected)")
                        except:
                            pass
                    
                    time.sleep(0.1)
                
                if not self.is_connected:
                    if not self.connection_error:
                        protocol_hint = ""
                        if self.protocol in ['ws', 'wss']:
                            protocol_hint = " 提示：WebSocket连接可能需要检查路径是否正确（如 /mqtt）"
                        elif self.protocol in ['mqtt', 'tcp']:
                            protocol_hint = f" 提示：请检查MQTT服务器 {self.broker_host}:{self.broker_port} 是否运行，以及防火墙是否允许连接"
                        self.connection_error = f"连接超时（{timeout}秒），请检查服务器地址和端口{protocol_hint}"
                    
                    print("\n" + "="*70)
                    print("✗ MQTT连接失败")
                    print("="*70)
                    print(f"错误: {self.connection_error}")
                    print(f"\n连接信息:")
                    print(f"  协议: {self.protocol}")
                    print(f"  主机: {self.broker_host}")
                    print(f"  端口: {self.broker_port}")
                    if self.url:
                        print(f"  URL: {self.url}")
                    if self.username:
                        print(f"  认证: 使用用户名/密码")
                    
                    print(f"\n诊断建议:")
                    if self.protocol in ['mqtt', 'tcp']:
                        print(f"  1. 检查MQTT服务器是否运行")
                        print(f"  2. 验证服务器地址: {self.broker_host}")
                        print(f"  3. 验证端口: {self.broker_port}")
                        print(f"  4. 检查用户名和密码是否正确")
                        print(f"  5. 查看服务器日志获取更多信息")
                    elif self.protocol in ['ws', 'wss']:
                        print(f"  1. 检查WebSocket路径是否正确")
                        print(f"  2. 验证服务器支持WebSocket")
                        print(f"  3. 检查防火墙设置")
                    print(f"\n日志文件: data/logs/mqtt_client_*.log")
                    print("="*70 + "\n")
                    
                    if logger:
                        logger.error(f"MQTT连接超时: {self.connection_error}")
                        logger.error(f"连接信息 - 协议: {self.protocol}, 主机: {self.broker_host}, 端口: {self.broker_port}")
                        if self.url:
                            logger.error(f"原始URL: {self.url}")
                    self.client.loop_stop()
                    return
                
                print("\n" + "="*70)
                print("✓ MQTT服务已启动，等待打印任务...")
                print("  自动重连: 已启用")
                print(f"  重连延迟: {self.reconnect_delay} 秒（首次），最大 {self.max_reconnect_delay} 秒")
                print("="*70 + "\n")
                
                if logger:
                    logger.info("MQTT服务已完全启动，进入主循环")
                    logger.info(f"自动重连已启用 - 初始延迟: {self.reconnect_delay}秒, 最大延迟: {self.max_reconnect_delay}秒")
                
                # 保持线程运行，定期检查连接状态
                import time
                last_status_log = time.time()
                
                while not self.is_stopping:
                    time.sleep(2)
                    
                    # 每60秒输出一次状态（如果连接正常）
                    if self.is_connected and (time.time() - last_status_log) > 60:
                        if logger:
                            logger.debug(f"MQTT连接正常 - 服务器: {self.broker_host}:{self.broker_port}")
                        last_status_log = time.time()
                    
                    # 检查连接状态（用于检测异常情况）
                    if self.client:
                        try:
                            # 检查是否实际连接
                            if hasattr(self.client, 'is_connected'):
                                if not self.client.is_connected():
                                    if self.is_connected:
                                        # 之前是连接的，现在断开了（但on_disconnect可能还未触发）
                                        self.is_connected = False
                                        if logger:
                                            logger.warning("检测到连接状态异常")
                        except:
                            pass
                
                # 循环退出（is_stopping=True时）
                print("\n" + "="*70)
                print("MQTT服务正在停止...")
                print("="*70)
                if logger:
                    logger.info("MQTT服务主循环退出，正在停止")
                            
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
    
    def stop(self):
        """停止MQTT客户端（正常断开，不自动重连）"""
        print("\n" + "="*70)
        print("正在停止MQTT客户端...")
        print("="*70)
        
        # 设置停止标志，防止自动重连
        self.is_stopping = True
        self.auto_reconnect = False
        
        if logger:
            logger.info("开始停止MQTT客户端")
        
        if self.client:
            try:
                # 停止事件循环
                print("  停止事件循环...")
                self.client.loop_stop()
                print("  ✓ 事件循环已停止")
                if logger:
                    logger.info("MQTT事件循环已停止")
                
                # 断开连接
                if self.is_connected:
                    print("  断开连接...")
                    self.client.disconnect()
                    print("  ✓ 连接已断开")
                    if logger:
                        logger.info("MQTT连接已断开")
                
                self.is_connected = False
                self.connection_error = None
                
            except Exception as e:
                print(f"  ⚠ 停止过程中出现异常: {e}")
                if logger:
                    logger.warning(f"停止MQTT客户端时出现异常: {e}")
        
        print("="*70)
        print("✓ MQTT客户端已停止")
        print("="*70 + "\n")
        
        if logger:
            logger.info("MQTT客户端已完全停止")

