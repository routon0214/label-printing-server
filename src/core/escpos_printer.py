#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ESC/POS打印机模块
支持热敏小票打印机、收据打印机
"""

import os
import platform
import socket


class ESCPOSPrinter:
    """ESC/POS热敏打印机类"""
    
    # ESC/POS指令常量
    ESC = b'\x1b'
    GS = b'\x1d'
    
    # 初始化
    CMD_INIT = ESC + b'@'
    
    # 对齐方式
    ALIGN_LEFT = ESC + b'a' + b'\x00'
    ALIGN_CENTER = ESC + b'a' + b'\x01'
    ALIGN_RIGHT = ESC + b'a' + b'\x02'
    
    # 字体大小
    FONT_NORMAL = ESC + b'!' + b'\x00'
    FONT_DOUBLE_HEIGHT = ESC + b'!' + b'\x10'
    FONT_DOUBLE_WIDTH = ESC + b'!' + b'\x20'
    FONT_DOUBLE = ESC + b'!' + b'\x30'
    FONT_BOLD = ESC + b'!' + b'\x08'
    
    # 切纸
    CUT_FULL = GS + b'V' + b'\x00'
    CUT_PARTIAL = GS + b'V' + b'\x01'
    
    # 换行
    LF = b'\n'
    
    def __init__(self, printer_ip=None, printer_port=9100, printer_name=None, device_path=None):
        """
        初始化ESC/POS打印机
        
        Args:
            printer_ip: 打印机IP地址（网络打印）
            printer_port: 打印机端口（默认9100）
            printer_name: 打印机名称（Windows/CUPS）
            device_path: 设备路径（Linux，如/dev/usb/lp0）
        """
        self.system = platform.system()
        self.printer_ip = printer_ip
        self.printer_port = printer_port
        self.printer_name = printer_name
        self.device_path = device_path
    
    def print_receipt(self, receipt_data):
        """
        打印小票/收据
        
        Args:
            receipt_data: 小票数据字典
                {
                    "title": "收据标题",
                    "items": [
                        {"name": "商品名称", "qty": 1, "price": 10.00},
                        ...
                    ],
                    "total": 100.00,
                    "footer": "感谢惠顾",
                    "barcode": "1234567890"  # 可选
                }
                
        Returns:
            bool: 是否成功
        """
        # 生成ESC/POS指令
        commands = self.generate_receipt_commands(receipt_data)
        
        # 发送到打印机
        return self.send_commands(commands)
    
    def generate_receipt_commands(self, data):
        """生成小票ESC/POS指令"""
        commands = bytearray()
        
        # 初始化打印机
        commands.extend(self.CMD_INIT)
        
        # 标题（居中、加粗、双倍大小）
        title = data.get('title', '收据')
        commands.extend(self.ALIGN_CENTER)
        commands.extend(self.FONT_DOUBLE)
        commands.extend(self.FONT_BOLD)
        commands.extend(title.encode('gbk', errors='ignore'))
        commands.extend(self.LF * 2)
        
        # 分隔线
        commands.extend(self.ALIGN_LEFT)
        commands.extend(self.FONT_NORMAL)
        commands.extend(b'-' * 32)
        commands.extend(self.LF)
        
        # 商品列表
        items = data.get('items', [])
        for item in items:
            name = item.get('name', '')
            qty = item.get('qty', 1)
            price = item.get('price', 0.0)
            total = qty * price
            
            # 格式化行
            line = f"{name[:16]:16s} x{qty}"
            commands.extend(line.encode('gbk', errors='ignore'))
            commands.extend(self.LF)
            
            # 价格（右对齐）
            price_line = f"{'':16s} ¥{total:.2f}"
            commands.extend(price_line.encode('gbk', errors='ignore'))
            commands.extend(self.LF)
        
        # 分隔线
        commands.extend(b'-' * 32)
        commands.extend(self.LF)
        
        # 总计（加粗）
        total = data.get('total', 0.0)
        commands.extend(self.FONT_BOLD)
        total_line = f"{'总计:':16s} ¥{total:.2f}"
        commands.extend(total_line.encode('gbk', errors='ignore'))
        commands.extend(self.LF)
        commands.extend(self.FONT_NORMAL)
        
        # 条形码
        barcode = data.get('barcode')
        if barcode:
            commands.extend(self.LF)
            commands.extend(self.ALIGN_CENTER)
            # CODE39条形码
            commands.extend(self.GS + b'k' + b'\x04')  # CODE39
            commands.extend(barcode.encode('ascii'))
            commands.extend(b'\x00')  # 结束符
            commands.extend(self.LF)
        
        # 页脚
        footer = data.get('footer', '')
        if footer:
            commands.extend(self.LF)
            commands.extend(self.ALIGN_CENTER)
            commands.extend(footer.encode('gbk', errors='ignore'))
            commands.extend(self.LF * 2)
        
        # 切纸
        commands.extend(self.LF * 3)
        commands.extend(self.CUT_PARTIAL)
        
        return bytes(commands)
    
    def send_commands(self, commands):
        """
        发送ESC/POS指令到打印机
        
        Args:
            commands: ESC/POS指令字节
            
        Returns:
            bool: 是否成功
        """
        # 优先使用网络打印
        if self.printer_ip:
            return self._send_network(commands)
        
        # Windows打印
        if self.system == 'Windows' and self.printer_name:
            return self._send_windows(commands)
        
        # Linux设备直连
        if self.system == 'Linux' and self.device_path:
            return self._send_device(commands)
        
        print("错误：未配置打印机")
        return False
    
    def _send_network(self, commands):
        """网络打印（所有平台通用）"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((self.printer_ip, self.printer_port))
            sock.sendall(commands)
            sock.close()
            print(f"✓ ESC/POS网络打印成功: {self.printer_ip}:{self.printer_port}")
            return True
        except Exception as e:
            print(f"✗ ESC/POS网络打印失败: {e}")
            return False
    
    def _send_windows(self, commands):
        """Windows打印"""
        try:
            import win32print
            
            printer_handle = win32print.OpenPrinter(self.printer_name)
            job_info = ("Receipt Print", None, "RAW")
            win32print.StartDocPrinter(printer_handle, 1, job_info)
            win32print.StartPagePrinter(printer_handle)
            win32print.WritePrinter(printer_handle, commands)
            win32print.EndPagePrinter(printer_handle)
            win32print.EndDocPrinter(printer_handle)
            win32print.ClosePrinter(printer_handle)
            
            print(f"✓ ESC/POS Windows打印成功: {self.printer_name}")
            return True
            
        except ImportError:
            print("错误：需要安装 pywin32: pip install pywin32")
            return False
        except Exception as e:
            print(f"✗ ESC/POS Windows打印失败: {e}")
            return False
    
    def _send_device(self, commands):
        """Linux设备直连打印"""
        try:
            with open(self.device_path, 'wb') as device:
                device.write(commands)
            
            print(f"✓ ESC/POS设备打印成功: {self.device_path}")
            return True
            
        except PermissionError:
            print(f"✗ 权限不足: {self.device_path}")
            print(f"提示：sudo chmod 666 {self.device_path}")
            return False
        except Exception as e:
            print(f"✗ ESC/POS设备打印失败: {e}")
            return False

