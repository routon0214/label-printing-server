#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
打印机控制模块
提供跨平台的打印机控制功能
"""

import os
import socket
import platform
import re
from src.utils.fuzzy_match import find_best_printer, fuzzy_match_printer

# TSPL 模式检测关键词
TSPL_PRINTER_PATTERNS = ['825T', 'DL-', 'TSC', 'tsc', 'deli', 'DELI', 'Deli']

# 真正的 Zebra 品牌打印机关键词（用于 SGD 初始化等 Zebra 专有功能）
ZEBRA_PRINTER_PATTERNS = ['zebra', 'ZT', 'ZD', 'ZDesigner', 'ZP', 'GC', 'GK', 'GT']


class ZebraPrinter:
    """斑马打印机类（跨平台）"""
    
    def __init__(self, printer_name=None, printer_ip=None, printer_port=9100, device_path=None, remove_newlines=None, printer_language=None):
        """
        初始化打印机
        
        Args:
            printer_name: 打印机名称（Windows/CUPS）- 支持模糊搜索
            printer_ip: 打印机IP地址（网络打印）
            printer_port: 打印机端口（网络打印，默认9100）
            device_path: 设备路径（Linux直接访问，如/dev/usb/lp0）
            remove_newlines: 是否移除ZPL代码中的换行符（已废弃，现在自动检测）
            printer_language: 打印机语言 ('zpl'|'tspl'|None=自动检测)
        """
        self.system = platform.system()
        self.printer_ip = printer_ip
        self.printer_port = printer_port
        self.device_path = device_path
        self.printer_name = None
        
        # 自动检测架构并设置换行符处理方式
        self.remove_newlines = self._auto_detect_newlines_handling()
        
        # 打印机语言模式: 'zpl' | 'tspl' | None=自动检测
        # 'auto' 字符串等同于 None（自动检测）
        if printer_language == 'auto':
            printer_language = None
        self.printer_language = printer_language or 'zpl'
        
        # 如果提供了打印机名称，尝试模糊匹配
        if printer_name:
            self.printer_name = self._fuzzy_find_printer(printer_name)
            # 自动检测 TSPL 模式
            if self.printer_name and not printer_language:
                self.printer_language = self._detect_language(self.printer_name)
        
        # 如果没有配置或模糊匹配失败，自动检测
        if not self.printer_name and not self.printer_ip and not self.device_path:
            self._auto_detect()
    
    def _detect_language(self, printer_name):
        """
        根据打印机名称自动检测语言模式
        
        Returns:
            str: 'zpl' 或 'tspl'
        """
        for pattern in TSPL_PRINTER_PATTERNS:
            if pattern.lower() in printer_name.lower():
                print(f"[DETECT] 检测到 TSC 打印机: {printer_name}，使用 TSPL 模式")
                return 'tspl'
        return 'zpl'

    def _is_zebra_printer(self):
        """检测是否为真正的 Zebra 品牌打印机（用于 SGD 等专有功能）"""
        if not self.printer_name:
            return False
        name_lower = self.printer_name.lower()
        for pattern in ZEBRA_PRINTER_PATTERNS:
            if pattern.lower() in name_lower:
                return True
        return False

    def _auto_detect_newlines_handling(self):
        """
        根据系统架构自动检测换行符处理方式
        
        Returns:
            bool: True=移除换行符, False=保留换行符
        """
        system = platform.system()
        machine = platform.machine().lower()
        
        # Windows: 移除换行符（大多数Windows打印机需要）
        if system == 'Windows':
            print(f"[ZPL] 检测到 Windows 系统，将移除ZPL代码中的换行符")
            return True
        
        # Linux: 根据架构判断
        if system == 'Linux':
            # ARM架构（如树莓派、ARM服务器）: 保留换行符
            if 'arm' in machine or 'aarch64' in machine:
                print(f"[ZPL] 检测到 Linux ARM 架构 ({machine})，将保留ZPL代码中的换行符")
                return False
            # x86/x64架构: 移除换行符
            else:
                print(f"[ZPL] 检测到 Linux x86/x64 架构 ({machine})，将移除ZPL代码中的换行符")
                return True
        
        # 其他系统: 默认移除换行符
        print(f"[ZPL] 检测到 {system} 系统 ({machine})，默认移除ZPL代码中的换行符")
        return True
    
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
    
    def _debug_save(self, zpl_code, output_bytes=None, suffix='zpl'):
        """保存打印数据到文件，方便诊断
        
        Args:
            zpl_code: 原始 ZPL 代码
            output_bytes: 转换/规范化后的输出 bytes（None 则保存原始 ZPL）
            suffix: 文件后缀 ('zpl' | 'tspl')
        """
        debug_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'debug')
        os.makedirs(debug_dir, exist_ok=True)
        ts = __import__('time').strftime('%Y%m%d_%H%M%S')
        # 保存原始 ZPL
        zpl_path = os.path.join(debug_dir, f'zpl_input_{ts}.txt')
        with open(zpl_path, 'w', encoding='utf-8') as f:
            f.write(zpl_code)
        print(f"[DEBUG] ZPL 已保存: {zpl_path} ({len(zpl_code)} 字符)")
        # 保存输出数据
        if output_bytes:
            out_path = os.path.join(debug_dir, f'{suffix}_output_{ts}.txt')
            mode = 'wb' if isinstance(output_bytes, bytes) else 'w'
            encoding = None if mode == 'wb' else 'utf-8'
            params = {}
            if encoding:
                params['encoding'] = encoding
            with open(out_path, mode, **params) as f:
                f.write(output_bytes)
            preview = output_bytes.decode('utf-8', errors='replace')[:500] if isinstance(output_bytes, bytes) else output_bytes[:500]
            print(f"[DEBUG] {suffix.upper()} 已保存: {out_path} ({len(output_bytes)} bytes)")
            print(f"[DEBUG] {suffix.upper()} 预览:\n{preview}")

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
    
    def _normalize_zpl(self, zpl_code):
        """
        规范化ZPL代码：根据打印机类型和架构自动处理换行符
        
        Args:
            zpl_code: 原始ZPL代码
            
        Returns:
            str: 规范化后的ZPL代码
        """
        # 移除首尾空白字符
        zpl_code = zpl_code.strip()
        
        # 统一换行符格式
        zpl_code = zpl_code.replace('\r\n', '\n').replace('\r', '\n')
        
        # 非 Zebra 打印机（如得力）：保留换行符，帮助固件正确解析 ZPL 命令
        is_zebra = self._is_zebra_printer()
        
        if self.remove_newlines and is_zebra:
            # 真正的 Zebra 打印机：移除所有换行符（Windows/Linux x86）
            zpl_code = zpl_code.replace('\n', '')
        else:
            # 非 Zebra 打印机或 ARM 架构：保留换行符，清理多余空白行
            zpl_code = re.sub(r'\n{3,}', '\n\n', zpl_code)
            # 非 Zebra 打印机（TSC/Deli 固件）：使用 \r\n 行尾（TSC 固件要求）
            if not is_zebra:
                zpl_code = zpl_code.replace('\n', '\r\n')
        
        # 确保ZPL代码以 ^XZ 结束
        if not zpl_code.endswith('^XZ'):
            zpl_code = zpl_code.rstrip() + '^XZ'
        
        return zpl_code
    
    def print_label(self, zpl_code):
        """
        打印标签（跨平台）
        
        Args:
            zpl_code: ZPL命令（TSPL 模式会自动转换）
            
        Returns:
            bool: 是否成功
        """
        # ── TSPL 模式：转换 ZPL → TSPL ──
        if self.printer_language == 'tspl':
            try:
                from src.utils.zpl_to_tspl import zpl_to_tspl
                tspl_bytes = zpl_to_tspl(zpl_code)

                # ── DEBUG: 保存转换结果到文件 ──
                self._debug_save(zpl_code, tspl_bytes, suffix='tspl')

                return self._print_raw(tspl_bytes)
            except ImportError as e:
                print(f"[ERROR] 无法导入 TSPL 转换器: {e}")
                return False
            except Exception as e:
                print(f"[ERROR] ZPL→TSPL 转换失败: {e}")
                traceback = __import__('traceback')
                traceback.print_exc()
                return False
        
        # ── ZPL 模式：直通逻辑 ──
        # 规范化ZPL代码
        zpl_normalized = self._normalize_zpl(zpl_code)
        zpl_bytes = zpl_normalized.encode('utf-8')
        
        # ── DEBUG: 保存 ZPL 输出到文件 ──
        self._debug_save(zpl_code, zpl_normalized, suffix='zpl')
        
        return self._print_raw(zpl_bytes)
    
    def _print_raw(self, data: bytes):
        """
        发送原始数据到打印机
        
        Args:
            data: 要发送的 bytes
            
        Returns:
            bool: 是否成功
        """
        # 优先使用网络打印（所有平台通用）
        if self.printer_ip:
            return self._print_network_bytes(data)
        
        # Windows打印
        if self.system == 'Windows':
            return self._print_windows_bytes(data)
        
        # Linux打印
        elif self.system == 'Linux':
            # 优先CUPS
            if self.printer_name:
                return self._print_cups_bytes(data)
            # 其次USB设备
            elif self.device_path:
                return self._print_device_bytes(data)
            else:
                print("错误：未配置打印机")
                return False
        
        else:
            print(f"错误：不支持的系统 {self.system}")
            return False
    
    def _print_network_bytes(self, data: bytes):
        """网络打印（bytes）"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((self.printer_ip, self.printer_port))
            sock.sendall(data)
            sock.close()
            print(f"[OK] 网络打印成功: {self.printer_ip}:{self.printer_port}")
            return True
        except Exception as e:
            print(f"[ERROR] 网络打印失败: {e}")
            return False

    def _print_windows_bytes(self, data: bytes):
        """Windows 打印（bytes，自动处理 ZPL/TSPL）"""
        try:
            import win32print

            if not self.printer_name:
                print("错误：未指定Windows打印机")
                return False

            printer_handle = win32print.OpenPrinter(self.printer_name)

            # ── ZPL 模式：发送 SGD 命令初始化（Zebra 和 TSC/Deli 固件均支持）──
            if self.printer_language == 'zpl':
                try:
                    init_cmd = b'! U1 setvar "device.languages" "zpl"\r\n'
                    win32print.StartDocPrinter(printer_handle, 1, ("Init", None, "RAW"))
                    win32print.StartPagePrinter(printer_handle)
                    win32print.WritePrinter(printer_handle, init_cmd)
                    win32print.EndPagePrinter(printer_handle)
                    win32print.EndDocPrinter(printer_handle)
                    print("[ZPL] 已发送 SGD 初始化命令 (切换至 ZPL 模式)")
                except Exception:
                    pass  # 初始化失败不影响后续打印

            # ── 发送标签数据 ──
            lang = self.printer_language.upper()
            job_info = (f"Label Print ({lang})", None, "RAW")
            win32print.StartDocPrinter(printer_handle, 1, job_info)
            win32print.StartPagePrinter(printer_handle)
            win32print.WritePrinter(printer_handle, data)
            win32print.EndPagePrinter(printer_handle)
            win32print.EndDocPrinter(printer_handle)
            win32print.ClosePrinter(printer_handle)

            print(f"[OK] Windows打印成功 ({lang}): {self.printer_name}")
            return True

        except ImportError:
            print("错误：Windows需要安装 pywin32: pip install pywin32")
            return False
        except Exception as e:
            print(f"[ERROR] Windows打印失败: {e}")
            return False

    def _print_cups_bytes(self, data: bytes):
        """CUPS打印（bytes）"""
        try:
            import cups
            import tempfile

            suffix = '.tspl' if self.printer_language == 'tspl' else '.zpl'
            with tempfile.NamedTemporaryFile(mode='wb', suffix=suffix, delete=False) as f:
                f.write(data)
                temp_file = f.name

            conn = cups.Connection()
            conn.printFile(self.printer_name, temp_file, "Label Print", {})
            os.remove(temp_file)

            print(f"[OK] CUPS打印成功: {self.printer_name}")
            return True

        except ImportError:
            print("提示：Linux建议安装 pycups: pip install pycups")
            return False
        except Exception as e:
            print(f"[ERROR] CUPS打印失败: {e}")
            return False

    def _print_device_bytes(self, data: bytes):
        """直接写入设备（bytes）"""
        try:
            with open(self.device_path, 'wb') as device:
                device.write(data)
            print(f"[OK] 设备打印成功: {self.device_path}")
            return True
        except PermissionError:
            print(f"[ERROR] 权限不足: {self.device_path}")
            return False
        except Exception as e:
            print(f"[ERROR] 设备打印失败: {e}")
            return False

    # ── 兼容旧接口（字符串版本） ──

    def _print_network(self, zpl_code):
        return self._print_network_bytes(zpl_code.encode('utf-8'))

    def _print_windows(self, zpl_code):
        return self._print_windows_bytes(zpl_code.encode('utf-8'))

    def _print_cups(self, zpl_code):
        return self._print_cups_bytes(zpl_code.encode('utf-8'))

    def _print_device(self, zpl_code):
        return self._print_device_bytes(zpl_code.encode('utf-8'))

