#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
斑马打印机MQTT标签打印程序
功能：接收MQTT消息，生成并打印支持中文的标签
支持平台：Windows、Linux (AMD64/ARM)
"""

import json
import socket
import sys
import os
import platform
import re
from io import BytesIO


# ==================== 中文支持 ====================

def get_font_paths():
    """
    获取系统中文字体路径（跨平台）
    """
    system = platform.system()
    
    if system == 'Windows':
        return [
            'C:/Windows/Fonts/msyh.ttc',      # 微软雅黑
            'C:/Windows/Fonts/simhei.ttf',    # 黑体
            'C:/Windows/Fonts/simsun.ttc',    # 宋体
        ]
    elif system == 'Linux':
        return [
            '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',           # 文泉驿正黑
            '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',         # 文泉驿微米黑
            '/usr/share/fonts/truetype/arphic/uming.ttc',             # AR PL UMing
            '/usr/share/fonts/truetype/arphic/ukai.ttc',              # AR PL UKai
            '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', # Noto Sans CJK
            '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf', # Droid
        ]
    elif system == 'Darwin':  # macOS
        return [
            '/System/Library/Fonts/PingFang.ttc',
            '/Library/Fonts/Songti.ttc',
        ]
    else:
        return []


def text_to_image_zpl(text, font_size=30):
    """
    将中文文本转换为ZPL图像命令（跨平台）
    :param text: 要转换的文本
    :param font_size: 字体大小
    :return: (hex_string, width, height, bytes_per_row, total_bytes)
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # 尝试加载中文字体
        font = None
        font_paths = get_font_paths()
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    font = ImageFont.truetype(font_path, font_size)
                    break
                except:
                    continue
        
        if font is None:
            font = ImageFont.load_default()
        
        # 创建临时图像测量文本大小
        temp_img = Image.new('RGB', (1, 1), 'white')
        draw = ImageDraw.Draw(temp_img)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # 添加边距
        padding = 8
        img_width = text_width + padding * 2
        img_height = text_height + padding * 2
        
        # 创建黑白图像
        image = Image.new('1', (img_width, img_height), 1)
        draw = ImageDraw.Draw(image)
        draw.text((padding, padding - bbox[1]), text, font=font, fill=0)
        
        # 转换为ZPL十六进制
        width, height = image.size
        bytes_per_row = (width + 7) // 8
        
        hex_data = []
        pixels = image.load()
        
        for y in range(height):
            row_bytes = []
            for x in range(0, width, 8):
                byte_val = 0
                for bit in range(8):
                    if x + bit < width:
                        if pixels[x + bit, y] == 0:
                            byte_val |= (1 << (7 - bit))
                row_bytes.append(byte_val)
            hex_data.append(''.join([f'{b:02X}' for b in row_bytes]))
        
        hex_string = ''.join(hex_data)
        total_bytes = len(hex_string) // 2
        
        return hex_string, img_width, img_height, bytes_per_row, total_bytes
        
    except ImportError:
        print("警告：需要安装 Pillow 库支持中文: pip install Pillow")
        return None, 0, 0, 0, 0
    except Exception as e:
        print(f"文本转图像失败: {e}")
        return None, 0, 0, 0, 0


# ==================== ZPL标签生成 ====================

def generate_label_zpl(label_data):
    """
    根据标签数据生成ZPL代码（支持中文）
    
    label_data 格式示例：
    {
        "title": "产品标签",
        "fields": [
            {"label": "产品名称", "value": "精密电子元件", "font_size": 28},
            {"label": "产品型号", "value": "ZX-2024-PRO", "font_size": 25},
            {"label": "序列号", "value": "SN20251015001", "font_size": 22},
            {"label": "生产日期", "value": "2025-10-15", "font_size": 22}
        ],
        "barcode": "SN20251015001",
        "qrcode": "SN20251015001"
    }
    """
    print(f"生成标签: {label_data.get('title', '未命名')}")
    
    zpl_parts = []
    zpl_parts.append("^XA")  # 开始
    zpl_parts.append("^PW800")  # 标签宽度
    zpl_parts.append("^LL600")  # 标签长度
    
    y_pos = 40
    
    # 标题
    title = label_data.get('title', '标签')
    if title:
        hex_data, w, h, bpr, total = text_to_image_zpl(title, font_size=40)
        if hex_data:
            zpl_parts.append(f"^FO50,{y_pos}^GFA,{total},{total},{bpr},{hex_data}^FS")
            y_pos += h + 15
    
    # 分隔线
    zpl_parts.append(f"^FO50,{y_pos}^GB700,3,3^FS")
    y_pos += 20
    
    # 字段内容
    fields = label_data.get('fields', [])
    for field in fields:
        label_text = field.get('label', '')
        value_text = field.get('value', '')
        font_size = field.get('font_size', 25)
        
        # 判断是否包含中文
        text = f"{label_text}：{value_text}" if label_text else value_text
        
        if any('\u4e00' <= char <= '\u9fff' for char in text):
            # 包含中文，使用图像方式
            hex_data, w, h, bpr, total = text_to_image_zpl(text, font_size=font_size)
            if hex_data:
                zpl_parts.append(f"^FO50,{y_pos}^GFA,{total},{total},{bpr},{hex_data}^FS")
                y_pos += h + 10
        else:
            # 纯英文数字，直接使用ZPL字体
            zpl_parts.append(f"^FO50,{y_pos}^A0N,{font_size},{font_size}^FD{text}^FS")
            y_pos += font_size + 10
    
    y_pos += 10
    
    # 条形码
    barcode = label_data.get('barcode')
    if barcode:
        zpl_parts.append(f"^FO50,{y_pos}^BY2,3,70^BCN,70,N,N,N^FD{barcode}^FS")
    
    # 二维码
    qrcode = label_data.get('qrcode')
    if qrcode:
        zpl_parts.append(f"^FO550,{y_pos - 30}^BQN,2,5^FDQA,{qrcode}^FS")
    
    zpl_parts.append("^XZ")  # 结束
    
    return '\n'.join(zpl_parts)


# ==================== 打印机模糊搜索 ====================

def fuzzy_match_printer(printer_name, search_pattern):
    """
    模糊匹配打印机名称
    :param printer_name: 打印机名称
    :param search_pattern: 搜索模式（支持通配符和正则）
    :return: 匹配分数（0-100），越高越匹配
    """
    if not search_pattern or not printer_name:
        return 0
    
    printer_lower = printer_name.lower()
    pattern_lower = search_pattern.lower()
    
    # 1. 完全匹配 - 100分
    if printer_lower == pattern_lower:
        return 100
    
    # 2. 开头匹配 - 90分
    if printer_lower.startswith(pattern_lower):
        return 90
    
    # 3. 包含关键词 - 根据位置给分
    if pattern_lower in printer_lower:
        # 越靠前分数越高
        pos = printer_lower.index(pattern_lower)
        score = 80 - (pos * 2)
        return max(score, 60)
    
    # 4. 分词匹配 - 检查是否包含所有关键词
    pattern_words = re.findall(r'\w+', pattern_lower)
    if pattern_words:
        matches = sum(1 for word in pattern_words if word in printer_lower)
        if matches == len(pattern_words):
            return 50 + (matches * 5)
        elif matches > 0:
            return 30 + (matches * 5)
    
    # 5. 模糊字符匹配 - 检查字符顺序
    pattern_chars = [c for c in pattern_lower if c.isalnum()]
    printer_chars = [c for c in printer_lower if c.isalnum()]
    
    if not pattern_chars:
        return 0
    
    matched = 0
    p_idx = 0
    for char in printer_chars:
        if p_idx < len(pattern_chars) and char == pattern_chars[p_idx]:
            matched += 1
            p_idx += 1
    
    if matched == len(pattern_chars):
        ratio = matched / len(printer_chars)
        return int(ratio * 40)
    
    return 0


def find_best_printer(printers, search_pattern):
    """
    从打印机列表中查找最匹配的打印机
    :param printers: 打印机列表或字典
    :param search_pattern: 搜索模式
    :return: 最匹配的打印机名称
    """
    if not printers or not search_pattern:
        return None
    
    # 如果是字典（CUPS），转换为列表
    if isinstance(printers, dict):
        printer_list = list(printers.keys())
    else:
        printer_list = printers
    
    # 计算每个打印机的匹配分数
    scores = []
    for printer in printer_list:
        score = fuzzy_match_printer(printer, search_pattern)
        if score > 0:
            scores.append((printer, score))
    
    # 按分数排序
    scores.sort(key=lambda x: x[1], reverse=True)
    
    # 返回最高分
    if scores and scores[0][1] >= 30:  # 最低30分才认为匹配
        return scores[0][0]
    
    return None


# ==================== 打印机控制（跨平台） ====================

class ZebraPrinter:
    """斑马打印机类（跨平台）"""
    
    def __init__(self, printer_name=None, printer_ip=None, printer_port=9100, device_path=None):
        """
        初始化打印机
        :param printer_name: 打印机名称（Windows/CUPS）- 支持模糊搜索
        :param printer_ip: 打印机IP地址（网络打印）
        :param printer_port: 打印机端口（网络打印，默认9100）
        :param device_path: 设备路径（Linux直接访问，如/dev/usb/lp0）
        """
        self.system = platform.system()
        self.printer_ip = printer_ip
        self.printer_port = printer_port
        self.device_path = device_path
        self.printer_name = None
        
        # 如果提供了打印机名称，尝试模糊匹配
        if printer_name:
            self.printer_name = self._fuzzy_find_printer(printer_name)
        
        # 如果没有配置或模糊匹配失败，自动检测
        if not self.printer_name and not self.printer_ip and not self.device_path:
            self._auto_detect()
    
    def _fuzzy_find_printer(self, search_name):
        """
        模糊查找打印机
        :param search_name: 搜索名称（可以是部分名称）
        :return: 实际打印机名称或None
        """
        print(f"模糊搜索打印机: '{search_name}'")
        
        if self.system == 'Windows':
            try:
                import win32print
                printers = [printer[2] for printer in win32print.EnumPrinters(2)]
                
                if not printers:
                    print("  未找到任何打印机")
                    return None
                
                # 使用模糊搜索
                result = find_best_printer(printers, search_name)
                if result:
                    score = fuzzy_match_printer(result, search_name)
                    print(f"  ✓ 匹配到: {result} (分数: {score})")
                    return result
                else:
                    print(f"  ✗ 未找到匹配的打印机")
                    print(f"  可用打印机: {', '.join(printers[:3])}")
                    return None
                    
            except Exception as e:
                print(f"  获取打印机列表失败: {e}")
                return None
                
        elif self.system == 'Linux':
            try:
                import cups
                conn = cups.Connection()
                printers = conn.getPrinters()
                
                if not printers:
                    print("  未找到任何CUPS打印机")
                    return None
                
                # 使用模糊搜索
                result = find_best_printer(printers, search_name)
                if result:
                    score = fuzzy_match_printer(result, search_name)
                    print(f"  ✓ 匹配到CUPS打印机: {result} (分数: {score})")
                    return result
                else:
                    print(f"  ✗ 未找到匹配的CUPS打印机")
                    print(f"  可用打印机: {', '.join(list(printers.keys())[:3])}")
                    return None
                    
            except ImportError:
                print("  提示：需要安装pycups")
                return None
            except Exception as e:
                print(f"  CUPS查询失败: {e}")
                return None
        
        return None
    
    def _auto_detect(self):
        """自动检测打印机"""
        if self.system == 'Windows':
            self._find_windows_printer()
        elif self.system == 'Linux':
            self._find_linux_printer()
    
    def _find_windows_printer(self):
        """查找Windows打印机（支持模糊搜索）"""
        try:
            import win32print
            printers = [printer[2] for printer in win32print.EnumPrinters(2)]
            
            if not printers:
                print("警告：未找到任何打印机")
                return
            
            # 显示所有打印机
            print(f"发现 {len(printers)} 台打印机:")
            for i, printer in enumerate(printers, 1):
                print(f"  {i}. {printer}")
            
            # 模糊搜索候选词
            search_patterns = ["ZT411", "zebra", "ZDesigner"]
            
            best_printer = None
            best_score = 0
            best_pattern = None
            
            # 尝试每个搜索模式
            for pattern in search_patterns:
                result = find_best_printer(printers, pattern)
                if result:
                    score = fuzzy_match_printer(result, pattern)
                    if score > best_score:
                        best_printer = result
                        best_score = score
                        best_pattern = pattern
            
            if best_printer and best_score >= 50:
                print(f"✓ 匹配打印机: {best_printer} (模式: {best_pattern}, 分数: {best_score})")
                self.printer_name = best_printer
            elif printers:
                # 未找到好的匹配，使用第一个
                print(f"未找到理想匹配，使用: {printers[0]}")
                self.printer_name = printers[0]
                
        except ImportError:
            print("警告：需要安装 pywin32")
        except Exception as e:
            print(f"警告：获取Windows打印机列表失败 - {e}")
    
    def _find_linux_printer(self):
        """查找Linux打印机（支持模糊搜索）"""
        # 尝试CUPS
        try:
            import cups
            conn = cups.Connection()
            printers = conn.getPrinters()
            
            if printers:
                # 显示所有打印机
                print(f"发现 {len(printers)} 台CUPS打印机:")
                for i, (name, info) in enumerate(printers.items(), 1):
                    desc = info.get('printer-info', info.get('printer-make-and-model', ''))
                    print(f"  {i}. {name} ({desc})")
                
                # 模糊搜索候选词
                search_patterns = ["ZT411", "zebra", "ZDesigner"]
                
                best_printer = None
                best_score = 0
                best_pattern = None
                
                # 尝试每个搜索模式
                for pattern in search_patterns:
                    result = find_best_printer(printers, pattern)
                    if result:
                        score = fuzzy_match_printer(result, pattern)
                        if score > best_score:
                            best_printer = result
                            best_score = score
                            best_pattern = pattern
                
                if best_printer and best_score >= 50:
                    print(f"✓ 匹配CUPS打印机: {best_printer} (模式: {best_pattern}, 分数: {best_score})")
                    self.printer_name = best_printer
                    return
                elif printers:
                    # 未找到好的匹配，使用第一个
                    first = list(printers.keys())[0]
                    print(f"未找到理想匹配，使用CUPS打印机: {first}")
                    self.printer_name = first
                    return
                    
        except ImportError:
            print("提示：未安装pycups，尝试查找USB设备")
        except Exception as e:
            print(f"CUPS查询失败: {e}")
        
        # 尝试USB设备
        usb_devices = ['/dev/usb/lp0', '/dev/usb/lp1', '/dev/usb/lp2']
        for device in usb_devices:
            if os.path.exists(device):
                print(f"✓ 找到USB设备: {device}")
                self.device_path = device
                return
        
        print("警告：未找到打印机，请在配置文件中指定")
    
    def print_label(self, zpl_code):
        """
        打印标签（跨平台）
        :param zpl_code: ZPL命令
        :return: 是否成功
        """
        # 优先使用网络打印（所有平台通用）
        if self.printer_ip:
            return self._print_network(zpl_code)
        
        # Windows打印
        if self.system == 'Windows':
            return self._print_windows(zpl_code)
        
        # Linux打印
        elif self.system == 'Linux':
            # 优先CUPS
            if self.printer_name:
                return self._print_cups(zpl_code)
            # 其次USB设备
            elif self.device_path:
                return self._print_device(zpl_code)
            else:
                print("错误：未配置打印机")
                return False
        
        else:
            print(f"错误：不支持的系统 {self.system}")
            return False
    
    def _print_network(self, zpl_code):
        """网络打印（所有平台通用）"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((self.printer_ip, self.printer_port))
            sock.sendall(zpl_code.encode('utf-8'))
            sock.close()
            print(f"✓ 网络打印成功: {self.printer_ip}:{self.printer_port}")
            return True
        except Exception as e:
            print(f"✗ 网络打印失败: {e}")
            return False
    
    def _print_windows(self, zpl_code):
        """Windows打印"""
        try:
            import win32print
            
            if not self.printer_name:
                print("错误：未指定Windows打印机")
                return False
            
            printer_handle = win32print.OpenPrinter(self.printer_name)
            job_info = ("Label Print", None, "RAW")
            win32print.StartDocPrinter(printer_handle, 1, job_info)
            win32print.StartPagePrinter(printer_handle)
            win32print.WritePrinter(printer_handle, zpl_code.encode('utf-8'))
            win32print.EndPagePrinter(printer_handle)
            win32print.EndDocPrinter(printer_handle)
            win32print.ClosePrinter(printer_handle)
            
            print(f"✓ Windows打印成功: {self.printer_name}")
            return True
            
        except ImportError:
            print("错误：Windows需要安装 pywin32: pip install pywin32")
            return False
        except Exception as e:
            print(f"✗ Windows打印失败: {e}")
            return False
    
    def _print_cups(self, zpl_code):
        """CUPS打印（Linux）"""
        try:
            import cups
            import tempfile
            
            # 创建临时文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.zpl', delete=False) as f:
                f.write(zpl_code)
                temp_file = f.name
            
            # 通过CUPS打印
            conn = cups.Connection()
            conn.printFile(self.printer_name, temp_file, "Label Print", {})
            
            # 删除临时文件
            os.remove(temp_file)
            
            print(f"✓ CUPS打印成功: {self.printer_name}")
            return True
            
        except ImportError:
            print("提示：Linux建议安装 pycups: pip install pycups")
            return False
        except Exception as e:
            print(f"✗ CUPS打印失败: {e}")
            return False
    
    def _print_device(self, zpl_code):
        """直接写入设备（Linux）"""
        try:
            with open(self.device_path, 'wb') as device:
                device.write(zpl_code.encode('utf-8'))
            
            print(f"✓ 设备打印成功: {self.device_path}")
            return True
            
        except PermissionError:
            print(f"✗ 权限不足: {self.device_path}")
            print(f"提示：请运行 sudo chmod 666 {self.device_path}")
            return False
        except Exception as e:
            print(f"✗ 设备打印失败: {e}")
            return False


# ==================== MQTT客户端 ====================

class LabelPrintMQTT:
    """MQTT标签打印客户端（跨平台）"""
    
    def __init__(self, broker_host, broker_port=1883, topic="zebra/print", 
                 username=None, password=None, printer_config=None):
        """
        初始化MQTT客户端
        :param broker_host: MQTT服务器地址
        :param broker_port: MQTT服务器端口
        :param topic: 订阅的主题
        :param username: MQTT用户名
        :param password: MQTT密码
        :param printer_config: 打印机配置字典
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
            zpl_code = generate_label_zpl(label_data)
            
            # 打印
            success = self.printer.print_label(zpl_code)
            
            if success:
                print(f"{'='*60}\n")
            else:
                # 保存失败的ZPL到文件
                import datetime
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"failed_label_{timestamp}.zpl"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(zpl_code)
                print(f"ZPL已保存到: {filename}")
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
            print(f"打印机: {self.printer.printer_name or '未找到'}")
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


# ==================== 配置和启动 ====================

def load_config(config_file='printer_config.json'):
    """加载配置文件"""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"未找到配置文件: {config_file}")
        print("使用默认配置...")
        return {
            "mqtt": {
                "host": "127.0.0.1",
                "port": 1883,
                "topic": "zebra/print",
                "username": None,
                "password": None
            },
            "printer": {
                "name": None,
                "ip": None,
                "port": 9100,
                "device": None
            }
        }
    except Exception as e:
        print(f"加载配置失败: {e}")
        return None


def create_default_config():
    """创建默认配置文件（跨平台）"""
    system = platform.system()
    
    config = {
        "mqtt": {
            "host": "127.0.0.1",
            "port": 1883,
            "topic": "zebra/print",
            "username": None,
            "password": None
        },
        "printer": {
            "name": None,
            "ip": None,
            "port": 9100,
            "device": None,
            "_comment": {
                "name": "打印机名称 (Windows/CUPS)",
                "ip": "打印机IP地址（网络打印，所有平台通用）",
                "port": "网络打印端口（默认9100）",
                "device": "设备路径 (Linux USB，如/dev/usb/lp0)",
                "说明": "配置其中一项即可，优先级: ip > name > device > 自动检测"
            }
        }
    }
    
    # 添加平台特定的示例
    if system == 'Windows':
        config["_examples"] = {
            "Windows USB": {"printer": {"name": "ZDesigner ZT411-300dpi"}},
            "网络打印": {"printer": {"ip": "192.168.1.100", "port": 9100}}
        }
    elif system == 'Linux':
        config["_examples"] = {
            "CUPS": {"printer": {"name": "Zebra-ZT411"}},
            "USB设备": {"printer": {"device": "/dev/usb/lp0"}},
            "网络打印": {"printer": {"ip": "192.168.1.100", "port": 9100}}
        }
    
    with open('printer_config.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    print(f"已创建默认配置文件: printer_config.json (平台: {system})")


def main():
    """主函数"""
    # 显示平台信息
    print(f"系统: {platform.system()} {platform.machine()}")
    print(f"Python: {sys.version.split()[0]}")
    print()
    
    # 加载配置
    config = load_config()
    
    if not config:
        print("配置加载失败，退出")
        return
    
    # 创建并启动MQTT客户端
    mqtt_config = config.get('mqtt', {})
    printer_config = config.get('printer', {})
    
    client = LabelPrintMQTT(
        broker_host=mqtt_config.get('host', '127.0.0.1'),
        broker_port=mqtt_config.get('port', 1883),
        topic=mqtt_config.get('topic', 'zebra/print'),
        username=mqtt_config.get('username'),
        password=mqtt_config.get('password'),
        printer_config=printer_config
    )
    
    client.start()


if __name__ == "__main__":
    try:
        # 检查是否需要创建配置文件
        import os
        if not os.path.exists('printer_config.json'):
            create_default_config()
        
        main()
    except KeyboardInterrupt:
        print("\n\n服务已停止")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()

