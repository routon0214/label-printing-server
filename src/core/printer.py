#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
打印机控制模块
提供跨平台的打印机控制功能
"""

import os
import socket
import platform
from src.utils.fuzzy_match import find_best_printer, fuzzy_match_printer


class ZebraPrinter:
    """斑马打印机类（跨平台）"""
    
    def __init__(self, printer_name=None, printer_ip=None, printer_port=9100, device_path=None):
        """
        初始化打印机
        
        Args:
            printer_name: 打印机名称（Windows/CUPS）- 支持模糊搜索
            printer_ip: 打印机IP地址（网络打印）
            printer_port: 打印机端口（网络打印，默认9100）
            device_path: 设备路径（Linux直接访问，如/dev/usb/lp0）
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
        
        Args:
            search_name: 搜索名称（可以是部分名称）
            
        Returns:
            str: 实际打印机名称或None
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
                    print(f"  [OK] 匹配到: {result} (分数: {score})")
                    return result
                else:
                    print(f"  [ERROR] 未找到匹配的打印机")
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
                    print(f"  [OK] 匹配到CUPS打印机: {result} (分数: {score})")
                    return result
                else:
                    print(f"  [ERROR] 未找到匹配的CUPS打印机")
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
                print(f"[OK] 匹配打印机: {best_printer} (模式: {best_pattern}, 分数: {best_score})")
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
                    print(f"[OK] 匹配CUPS打印机: {best_printer} (模式: {best_pattern}, 分数: {best_score})")
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
                print(f"[OK] 找到USB设备: {device}")
                self.device_path = device
                return
        
        print("警告：未找到打印机，请在配置文件中指定")
    
    def print_label(self, zpl_code):
        """
        打印标签（跨平台）
        
        Args:
            zpl_code: ZPL命令
            
        Returns:
            bool: 是否成功
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
            print(f"[OK] 网络打印成功: {self.printer_ip}:{self.printer_port}")
            return True
        except Exception as e:
            print(f"[ERROR] 网络打印失败: {e}")
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
            
            print(f"[OK] Windows打印成功: {self.printer_name}")
            return True
            
        except ImportError:
            print("错误：Windows需要安装 pywin32: pip install pywin32")
            return False
        except Exception as e:
            print(f"[ERROR] Windows打印失败: {e}")
            return False
    
    def _print_cups(self, zpl_code):
        """CUPS打印（Linux）"""
        try:
            import cups
            import tempfile
        except ImportError:
            print("提示：Linux建议安装 pycups: pip install pycups")
            return False
        
        try:
            # 创建临时文件（使用二进制模式，因为ZPL可能包含特殊字符）
            temp_file_path = None
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.zpl', delete=False) as f:
                # ZPL代码需要编码为字节
                f.write(zpl_code.encode('utf-8'))
                temp_file_path = f.name
            
            try:
                # 通过CUPS打印（使用空字典作为options，让CUPS自动处理RAW格式）
                conn = cups.Connection()
                job_id = conn.printFile(
                    self.printer_name,
                    temp_file_path,
                    "ZPL Label Print",
                    {}  # 空字典，让CUPS自动处理RAW格式
                )
                
                # 检查作业ID（如果为0或None，表示失败）
                if not job_id or job_id == 0:
                    print(f"[ERROR] CUPS打印失败: 作业ID无效 ({job_id})")
                    return False
                
                print(f"[OK] CUPS打印成功: {self.printer_name} (作业ID: {job_id})")
                return True
            finally:
                # 删除临时文件
                if temp_file_path and os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
            
        except Exception as e:
            # 检查是否是IPPError
            import cups
            if hasattr(cups, 'IPPError') and isinstance(e, cups.IPPError):
                print(f"[ERROR] CUPS打印失败 (IPP错误): {e}")
            else:
                print(f"[ERROR] CUPS打印失败: {e}")
                import traceback
                traceback.print_exc()
            return False
    
    def _print_device(self, zpl_code):
        """直接写入设备（Linux）"""
        try:
            with open(self.device_path, 'wb') as device:
                device.write(zpl_code.encode('utf-8'))
            
            print(f"[OK] 设备打印成功: {self.device_path}")
            return True
            
        except PermissionError:
            print(f"[ERROR] 权限不足: {self.device_path}")
            print(f"提示：请运行 sudo chmod 666 {self.device_path}")
            return False
        except Exception as e:
            print(f"[ERROR] 设备打印失败: {e}")
            return False

