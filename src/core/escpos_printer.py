#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ESC/POS打印机模块
支持热敏小票打印机、收据打印机
"""

import os
import platform
import socket
import codecs


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
        
        # 验证配置
        has_config = bool(printer_ip or printer_name or device_path)
        if not has_config:
            print(f"⚠ 警告: ESC/POS打印机配置不完整 - IP: {printer_ip}, 名称: {printer_name}, 设备: {device_path}")
            print(f"  提示: 需要至少配置 printer_ip、printer_name 或 device_path 之一")
        else:
            config_info = []
            if printer_ip:
                config_info.append(f"IP={printer_ip}:{printer_port}")
            if printer_name:
                config_info.append(f"名称={printer_name}")
            if device_path:
                config_info.append(f"设备={device_path}")
            print(f"✓ ESC/POS打印机已配置: {', '.join(config_info)}")
    
    def print_receipt(self, receipt_data):
        """
        打印小票/收据
        
        Args:
            receipt_data: 小票数据字典
                支持两种格式：
                1. 结构化格式:
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
                2. 原始文本格式:
                {
                    "raw_text": "原始文本内容\\n换行",
                    "encoding": "gb2312"  # 可选，推荐gb2312/gbk（中文打印）
                }
                
        Returns:
            bool: 是否成功
        """
        # 如果包含 raw_text 字段，直接打印原始文本
        if receipt_data is None:
            print("[ERROR] receipt_data为空，无法打印")
            return False
        
        if 'raw_text' in receipt_data:
            raw_text = receipt_data.get('raw_text', '')
            # 对于中文打印机，推荐使用 gb2312 或 gbk 编码
            encoding = receipt_data.get('encoding', 'gb2312')
            
            # 注意：JSON解析器已经处理了 \n, \t 等转义字符
            # 不需要再次解码，否则会破坏中文字符
            # 直接使用原始文本即可
            
            # 生成ESC/POS指令
            commands = bytearray()
            
            # 1. 初始化打印机
            commands.extend(self.CMD_INIT)  # ESC @ - 初始化
            
            # 2. 设置字符集为简体中文（关键！避免乱码）
            # ESC t n - 选择字符代码表
            # n=14 (0x0E) = 简体中文 GB2312
            commands.extend(b'\x1B\x74\x0E')
            
            # 3. 将文本转换为字节
            print(f"  原始文本长度: {len(raw_text)} 字符")
            print(f"  原始文本预览: {raw_text[:100]}...")
            
            try:
                # 首选 gb2312/gbk 编码（最适合中文ESC/POS打印机）
                if encoding.lower() in ['gb2312', 'gbk', 'gb18030']:
                    text_bytes = raw_text.encode(encoding, errors='ignore')
                    print(f"  ✓ 使用编码: {encoding}")
                    print(f"  ✓ 编码后字节数: {len(text_bytes)}")
                else:
                    # 如果指定其他编码，尝试使用，失败则fallback到gb2312
                    try:
                        text_bytes = raw_text.encode(encoding, errors='ignore')
                        print(f"  ✓ 使用编码: {encoding}")
                        print(f"  ✓ 编码后字节数: {len(text_bytes)}")
                    except (UnicodeEncodeError, LookupError):
                        text_bytes = raw_text.encode('gb2312', errors='ignore')
                        print(f"  ⚠ 警告: {encoding}编码失败，使用gb2312")
            except (UnicodeEncodeError, LookupError) as e:
                # 如果所有编码都失败，使用gb2312并替换无法编码的字符
                text_bytes = raw_text.encode('gb2312', errors='ignore')
                print(f"  ⚠ 警告: 编码失败 ({e})，使用gb2312")
            
            # 4. 添加文本内容
            commands.extend(text_bytes)
            
            # 5. 添加换行
            commands.extend(self.LF * 2)
            
            # 验证生成的命令
            final_commands = bytes(commands)
            print(f"  生成的ESC/POS命令总长度: {len(final_commands)} 字节")
            if len(final_commands) < 10:
                print(f"  ⚠ 警告: 命令长度过短，可能有问题")
            
            # 发送到打印机
            result = self.send_commands(final_commands)
            if result:
                print(f"  ✓ 打印命令已成功发送")
            else:
                print(f"  ✗ 打印命令发送失败")
            return result
        
        # 否则使用结构化格式
        print("  使用结构化格式生成小票")
        # 生成ESC/POS指令
        commands = self.generate_receipt_commands(receipt_data)
        
        # 验证生成的命令
        print(f"  生成的ESC/POS命令总长度: {len(commands)} 字节")
        if len(commands) < 10:
            print(f"  ⚠ 警告: 命令长度过短，可能有问题")
        
        # 发送到打印机
        result = self.send_commands(commands)
        if result:
            print(f"  ✓ 打印命令已成功发送")
        else:
            print(f"  ✗ 打印命令发送失败")
        return result
    
    def generate_receipt_commands(self, data):
        """生成小票ESC/POS指令"""
        commands = bytearray()
        
        # 1. 初始化打印机
        commands.extend(self.CMD_INIT)
        
        # 2. 设置字符集为简体中文（关键！避免乱码）
        # ESC t n - 选择字符代码表
        # n=14 (0x0E) = 简体中文 GB2312
        commands.extend(b'\x1B\x74\x0E')
        
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
        # 验证命令数据
        if not commands:
            print("✗ 错误：ESC/POS命令数据为空")
            return False
        
        if len(commands) == 0:
            print("✗ 错误：ESC/POS命令数据长度为0")
            return False
        
        print(f"  准备发送ESC/POS命令: {len(commands)} 字节")
        print(f"  命令预览 (前32字节): {commands[:32].hex()}")
        print(f"  当前配置 - IP: {self.printer_ip}, 名称: {self.printer_name}, 设备: {self.device_path}")
        
        # 优先使用网络打印
        if self.printer_ip:
            print(f"  → 使用网络打印模式")
            return self._send_network(commands)
        
        # Windows打印
        if self.system == 'Windows' and self.printer_name:
            print(f"  → 使用Windows打印模式")
            return self._send_windows(commands)
        
        # Linux设备直连
        if self.system == 'Linux' and self.device_path:
            print(f"  → 使用Linux设备直连模式")
            return self._send_device(commands)
        
        # 没有可用的配置
        error_msg = f"✗ 错误：未配置打印机（需要设置 printer_ip、printer_name 或 device_path）"
        print(error_msg)
        print(f"  当前系统: {self.system}")
        print(f"  当前配置: IP={self.printer_ip}, 名称={self.printer_name}, 设备={self.device_path}")
        return False
    
    def _send_network(self, commands):
        """网络打印（所有平台通用）"""
        try:
            if not commands or len(commands) == 0:
                print(f"✗ ESC/POS网络打印失败: 命令数据为空")
                return False
            
            print(f"  准备发送 {len(commands)} 字节到 {self.printer_ip}:{self.printer_port}")
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((self.printer_ip, self.printer_port))
            
            # 发送数据
            sent = sock.sendall(commands)
            
            # 等待一小段时间确保数据发送完成
            import time
            time.sleep(0.1)
            
            # 关闭连接
            sock.close()
            
            print(f"✓ ESC/POS网络打印成功: {self.printer_ip}:{self.printer_port} (已发送 {len(commands)} 字节)")
            return True
        except socket.timeout:
            print(f"✗ ESC/POS网络打印失败: 连接超时 ({self.printer_ip}:{self.printer_port})")
            return False
        except socket.error as e:
            print(f"✗ ESC/POS网络打印失败: 网络错误 - {e} ({self.printer_ip}:{self.printer_port})")
            return False
        except Exception as e:
            print(f"✗ ESC/POS网络打印失败: {e} ({self.printer_ip}:{self.printer_port})")
            return False
    
    def _send_windows(self, commands):
        """Windows打印"""
        try:
            if not commands or len(commands) == 0:
                print(f"✗ ESC/POS Windows打印失败: 命令数据为空")
                return False
            
            import win32print
            import win32api
            import win32con
            
            print(f"  准备发送 {len(commands)} 字节到打印机: {self.printer_name}")
            
            # 检查打印机是否存在和状态
            printer_handle = None
            try:
                # 打开打印机以检查状态
                printer_handle = win32print.OpenPrinter(self.printer_name)
                
                # 获取打印机信息
                printer_info = win32print.GetPrinter(printer_handle, 2)
                printer_status = printer_info.get('Status', 0)
                
                # 检查打印机状态
                if printer_status != 0:
                    status_messages = []
                    if printer_status & win32print.PRINTER_STATUS_PAUSED:
                        status_messages.append("已暂停")
                    if printer_status & win32print.PRINTER_STATUS_ERROR:
                        status_messages.append("错误")
                    if printer_status & win32print.PRINTER_STATUS_PAPER_JAM:
                        status_messages.append("卡纸")
                    if printer_status & win32print.PRINTER_STATUS_PAPER_OUT:
                        status_messages.append("缺纸")
                    if printer_status & win32print.PRINTER_STATUS_OFFLINE:
                        status_messages.append("离线")
                    
                    if status_messages:
                        print(f"  ⚠ 警告: 打印机状态异常 - {', '.join(status_messages)}")
                        print(f"  提示: 请检查打印机状态，但将继续尝试打印")
                    else:
                        print(f"  ✓ 打印机状态正常 (状态码: {printer_status})")
                else:
                    print(f"  ✓ 打印机状态正常")
                
            except Exception as status_error:
                print(f"  ⚠ 警告: 无法获取打印机状态: {status_error}")
                print(f"  提示: 将继续尝试打印")
                if printer_handle:
                    win32print.ClosePrinter(printer_handle)
                    printer_handle = None
            
            # 如果状态检查时已经打开了打印机，直接使用；否则重新打开
            if not printer_handle:
                try:
                    printer_handle = win32print.OpenPrinter(self.printer_name)
                except Exception as open_error:
                    print(f"✗ 无法打开打印机 '{self.printer_name}': {open_error}")
                    print(f"  提示: 请检查打印机名称是否正确，或打印机是否在线")
                    return False
            
            try:
                # 使用RAW数据类型发送ESC/POS命令
                job_info = ("Receipt Print", None, "RAW")
                job_id = win32print.StartDocPrinter(printer_handle, 1, job_info)
                print(f"  打印作业已创建 (ID: {job_id})")
                
                # 开始页面
                win32print.StartPagePrinter(printer_handle)
                
                # 写入数据
                try:
                    bytes_written = win32print.WritePrinter(printer_handle, commands)
                    print(f"  数据已写入打印队列: {bytes_written} 字节")
                    
                    if bytes_written != len(commands):
                        print(f"  ⚠ 警告: 写入字节数不匹配 (期望: {len(commands)}, 实际: {bytes_written})")
                    
                except Exception as write_error:
                    print(f"✗ 写入打印队列失败: {write_error}")
                    import traceback
                    traceback.print_exc()
                    return False
                
                # 结束页面
                win32print.EndPagePrinter(printer_handle)
                
                # 结束文档
                win32print.EndDocPrinter(printer_handle)
                
                print(f"✓ ESC/POS Windows打印成功: {self.printer_name}")
                print(f"  打印作业ID: {job_id}")
                print(f"  已写入: {bytes_written} 字节")
                print(f"  提示: 如果打印机没有打印，请检查:")
                print(f"    1. 打印机是否在线")
                print(f"    2. 打印机驱动是否正确")
                print(f"    3. Windows打印队列中是否有错误")
                print(f"    4. 打印机是否支持RAW格式打印")
                
                return True
            except Exception as print_error:
                print(f"✗ 打印过程出错: {print_error}")
                import traceback
                traceback.print_exc()
                return False
            finally:
                win32print.ClosePrinter(printer_handle)
            
        except ImportError:
            print("错误：需要安装 pywin32: pip install pywin32")
            return False
        except Exception as e:
            print(f"✗ ESC/POS Windows打印失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _send_device(self, commands):
        """Linux设备直连打印"""
        try:
            if not commands or len(commands) == 0:
                print(f"✗ ESC/POS设备打印失败: 命令数据为空")
                return False
            
            print(f"  准备发送 {len(commands)} 字节到设备: {self.device_path}")
            with open(self.device_path, 'wb') as device:
                bytes_written = device.write(commands)
                device.flush()  # 确保数据写入
            
            print(f"✓ ESC/POS设备打印成功: {self.device_path} (已写入 {bytes_written} 字节)")
            return True
            
        except PermissionError:
            print(f"✗ 权限不足: {self.device_path}")
            print(f"提示：sudo chmod 666 {self.device_path}")
            return False
        except FileNotFoundError:
            print(f"✗ 设备不存在: {self.device_path}")
            return False
        except Exception as e:
            print(f"✗ ESC/POS设备打印失败: {e}")
            import traceback
            traceback.print_exc()
            return False

