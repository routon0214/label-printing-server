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
            # 优先直接写入设备（如果配置了设备路径，更可靠）
            if self.device_path:
                print(f"  [调试] 使用设备路径打印: {self.device_path}")
                result = self._print_device(zpl_code)
                if result:
                    return True
                # 如果设备打印失败，尝试CUPS作为备选
                print(f"  [调试] 设备打印失败，尝试CUPS...")
            
            # 其次CUPS
            if self.printer_name:
                return self._print_cups(zpl_code)
            else:
                print("错误：未配置打印机（需要设置 printer_name 或 device_path）")
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
            print(f"  [调试] 准备发送ZPL代码，长度: {len(zpl_code)} 字符")
            print(f"  [调试] ZPL代码预览: {zpl_code[:100]}...")
            
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.zpl', delete=False) as f:
                # ZPL代码需要编码为字节
                zpl_bytes = zpl_code.encode('utf-8')
                f.write(zpl_bytes)
                temp_file_path = f.name
                print(f"  [调试] 临时文件已创建: {temp_file_path} ({len(zpl_bytes)} 字节)")
            
            try:
                # 通过CUPS打印（使用空字典作为options，让CUPS自动处理RAW格式）
                conn = cups.Connection()
                
                # 检查打印机信息
                printers = conn.getPrinters()
                if self.printer_name in printers:
                    printer_info = printers[self.printer_name]
                    print(f"  [调试] 打印机信息: {printer_info.get('printer-info', 'N/A')}")
                    print(f"  [调试] 打印机状态: {printer_info.get('printer-state', 'N/A')}")
                    print(f"  [调试] 支持的格式: {printer_info.get('document-format-supported', [])}")
                
                # 检查ZPL代码中是否包含多个打印命令（多个^XZ）
                xz_count = zpl_code.count('^XZ')
                if xz_count > 1:
                    print(f"  ⚠ 警告: ZPL代码包含 {xz_count} 个打印命令（^XZ），可能导致重复打印")
                    print(f"  [调试] 只使用第一个打印命令，移除后续的^XZ...")
                    # 只保留第一个^XZ之前的内容，然后添加一个^XZ
                    first_xz_pos = zpl_code.find('^XZ')
                    if first_xz_pos >= 0:
                        zpl_code = zpl_code[:first_xz_pos + 3]  # 保留第一个^XZ
                        print(f"  [调试] 已清理ZPL代码，现在只包含1个打印命令")
                
                # 优先尝试：如果可以从CUPS获取设备路径，直接使用设备路径（避免CUPS处理ZPL的问题）
                device_path_to_try = self.device_path
                if not device_path_to_try:
                    try:
                        printer_attrs = conn.getPrinterAttributes(self.printer_name)
                        device_uri = printer_attrs.get('device-uri', '')
                        print(f"  [调试] 打印机设备URI: {device_uri}")
                        
                        if device_uri.startswith('usb://'):
                            # USB设备，尝试找到对应的/dev/usb/lp*设备
                            import glob
                            usb_devices = glob.glob('/dev/usb/lp*')
                            print(f"  [调试] 找到 {len(usb_devices)} 个USB设备: {usb_devices}")
                            if usb_devices:
                                # 使用第一个USB设备
                                device_path_to_try = usb_devices[0]
                                print(f"  [调试] 从CUPS获取到USB设备: {device_path_to_try}")
                                print(f"  [调试] 优先使用设备直接写入，避免CUPS处理ZPL的问题...")
                                
                                # 直接使用设备路径打印，完全跳过CUPS
                                try:
                                    # 临时设置设备路径
                                    original_device_path = self.device_path
                                    self.device_path = device_path_to_try
                                    try:
                                        result = self._print_device(zpl_code)
                                        if result:
                                            print(f"  ✓ 设备直接写入成功（跳过CUPS，避免重复打印）")
                                            return True
                                    finally:
                                        self.device_path = original_device_path
                                except Exception as device_error:
                                    print(f"  [调试] 设备直接写入失败，回退到CUPS: {device_error}")
                                    import traceback
                                    traceback.print_exc()
                                    # 如果设备写入失败，继续使用CUPS
                    except Exception as uri_error:
                        print(f"  [调试] 无法获取设备URI: {uri_error}")
                
                # 方法1: 使用空字典（标准方式）
                print(f"  [方法1] 使用CUPS API (空字典)...")
                try:
                    job_id = conn.printFile(
                        self.printer_name,
                        temp_file_path,
                        "ZPL Label Print",
                        {}  # 空字典，让CUPS自动处理RAW格式
                    )
                    
                    print(f"  [调试] CUPS返回作业ID: {job_id}")
                    
                    # 检查作业ID（如果为0或None，表示失败）
                    if not job_id or job_id == 0:
                        print(f"  [方法1失败] 作业ID无效: {job_id}")
                    else:
                        print(f"[OK] CUPS打印成功: {self.printer_name} (作业ID: {job_id})")
                        
                        # 等待并检查打印作业状态
                        import time
                        
                        # CUPS作业状态码：
                        # 3 = IPP_JOB_STATE_PENDING (等待处理)
                        # 4 = IPP_JOB_STATE_HELD (暂停)
                        # 5 = IPP_JOB_STATE_PROCESSING (处理中)
                        # 6 = IPP_JOB_STATE_STOPPED (停止)
                        # 7 = IPP_JOB_STATE_CANCELED (取消)
                        # 8 = IPP_JOB_STATE_ABORTED (中止)
                        # 9 = IPP_JOB_STATE_COMPLETED (完成)
                        
                        job_completed = False
                        max_wait_time = 2.0  # 最多等待2秒
                        check_interval = 0.3  # 每0.3秒检查一次
                        waited_time = 0
                        pending_count = 0  # 记录pending状态的次数
                        
                        while waited_time < max_wait_time:
                            time.sleep(check_interval)
                            waited_time += check_interval
                            
                            try:
                                # 获取打印作业信息
                                job_info = conn.getJobAttributes(job_id)
                                job_state = job_info.get('job-state', 'unknown')
                                job_state_reasons = job_info.get('job-state-reasons', [])
                                
                                print(f"  [调试] 打印作业状态: {job_state} (等待 {waited_time:.1f}秒)")
                                
                                if job_state_reasons and job_state_reasons != ['none']:
                                    print(f"  [调试] 状态原因: {job_state_reasons}")
                                
                                # 状态9表示完成
                                if job_state == 9:
                                    print(f"  ✓ 打印作业已完成")
                                    job_completed = True
                                    break
                                # 状态5表示正在处理（可能已经开始打印，立即取消）
                                elif job_state == 5:
                                    print(f"  ⚠ 警告: 打印作业正在处理中，可能已经开始打印")
                                    print(f"  [调试] 立即取消CUPS作业，避免重复打印...")
                                    try:
                                        conn.cancelJob(job_id)
                                        print(f"  [调试] 已取消CUPS打印作业 {job_id}")
                                    except Exception as cancel_error:
                                        print(f"  [调试] 取消CUPS作业失败: {cancel_error}")
                                    # 标记为未完成，后续会尝试直接写入设备
                                    break
                                # 状态3表示等待处理
                                elif job_state == 3:
                                    pending_count += 1
                                    print(f"  [调试] 打印作业等待处理中... (pending {pending_count}次)")
                                    # 如果pending超过1次（约0.3秒），立即取消并切换到直接写入
                                    # 因为ZPL代码通常CUPS无法处理，等待时间越长越可能已经开始处理
                                    if pending_count >= 1:
                                        print(f"  ⚠ 警告: 打印作业一直pending，可能CUPS无法处理ZPL")
                                        print(f"  [调试] 立即取消CUPS作业，切换到直接写入设备...")
                                        try:
                                            conn.cancelJob(job_id)
                                            print(f"  [调试] 已取消CUPS打印作业 {job_id}")
                                        except Exception as cancel_error:
                                            print(f"  [调试] 取消CUPS作业失败: {cancel_error}")
                                        break
                                # 其他状态可能是错误
                                elif job_state in [4, 6, 7, 8]:
                                    print(f"  ⚠ 警告: 打印作业状态异常: {job_state}")
                                    if job_state_reasons:
                                        print(f"    原因: {job_state_reasons}")
                                    # 如果作业被暂停或停止，尝试其他方法
                                    break
                                    
                            except Exception as status_error:
                                # 如果无法获取作业状态，可能是作业已完成或被删除
                                print(f"  [调试] 无法获取打印作业状态 (可能已完成): {status_error}")
                                # 假设已完成，继续执行
                                job_completed = True
                                break
                        
                        # 如果作业未完成或一直pending，尝试直接写入设备（CUPS可能无法处理ZPL）
                        if not job_completed:
                            print(f"  ⚠ 警告: CUPS打印作业一直处于pending状态，可能无法处理ZPL代码")
                            print(f"  [调试] 尝试直接写入设备以确保打印...")
                            
                            device_path_to_try = self.device_path
                            
                            # 如果没有配置设备路径，尝试从CUPS获取
                            if not device_path_to_try:
                                try:
                                    printer_attrs = conn.getPrinterAttributes(self.printer_name)
                                    device_uri = printer_attrs.get('device-uri', '')
                                    print(f"  [调试] 打印机设备URI: {device_uri}")
                                    
                                    if device_uri.startswith('usb://'):
                                        # USB设备，尝试找到对应的/dev/usb/lp*设备
                                        import glob
                                        usb_devices = glob.glob('/dev/usb/lp*')
                                        print(f"  [调试] 找到 {len(usb_devices)} 个USB设备: {usb_devices}")
                                        if usb_devices:
                                            # 使用第一个USB设备
                                            device_path_to_try = usb_devices[0]
                                            print(f"  [调试] 尝试使用USB设备: {device_path_to_try}")
                                except Exception as uri_error:
                                    print(f"  [调试] 无法获取设备URI: {uri_error}")
                            
                            # 如果找到了设备路径，尝试直接写入设备
                            if device_path_to_try:
                                try:
                                    # 注意：CUPS作业可能已经在pending检测时被取消了
                                    # 直接读取临时文件并写入设备
                                    with open(temp_file_path, 'rb') as f:
                                        zpl_bytes = f.read()
                                    
                                    # 解码为字符串，然后使用_print_device方法
                                    zpl_code = zpl_bytes.decode('utf-8')
                                    
                                    # 临时设置设备路径并尝试打印
                                    original_device_path = self.device_path
                                    self.device_path = device_path_to_try
                                    try:
                                        result = self._print_device(zpl_code)
                                        if result:
                                            print(f"  ✓ 设备直接写入成功（已取消CUPS作业，避免重复打印）")
                                            return True
                                    finally:
                                        self.device_path = original_device_path
                                except Exception as device_error:
                                    print(f"  [调试] 设备直接写入失败: {device_error}")
                                    import traceback
                                    traceback.print_exc()
                            else:
                                print(f"  ⚠ 无法找到设备路径，CUPS打印作业可能仍在队列中")
                                print(f"  提示: 如果打印机没有反应，可以尝试:")
                                print(f"    1. 检查CUPS打印队列: lpstat -p {self.printer_name}")
                                print(f"    2. 检查打印作业: lpstat -o")
                                print(f"    3. 检查打印机状态: lpstat -p {self.printer_name} -l")
                                print(f"    4. 在配置中添加设备路径（device）以使用直接写入")
                        
                        # 如果作业已完成或无法直接写入设备，返回True（CUPS已接受作业）
                        return True
                except Exception as method1_error:
                    print(f"  [方法1失败] CUPS API失败: {method1_error}")
                    import traceback
                    traceback.print_exc()
                
                # 方法2: 使用lp命令（备选方案）
                print(f"  [方法2] 尝试使用lp命令...")
                import subprocess
                result = subprocess.run(
                    ['lp', '-d', self.printer_name, temp_file_path],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    print(f"[OK] lp打印成功: {self.printer_name}")
                    print(f"  [调试] lp输出: {result.stdout}")
                    import time
                    time.sleep(0.5)
                    return True
                else:
                    print(f"  [方法2失败] lp命令失败: {result.stderr}")
                
                # 所有方法都失败
                print(f"[ERROR] 所有ZPL打印方法都失败")
                return False
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
            if not zpl_code or len(zpl_code) == 0:
                print(f"[ERROR] ZPL设备打印失败: ZPL代码为空")
                return False
            
            # 检查ZPL代码中是否包含多个打印命令（多个^XZ）
            xz_count = zpl_code.count('^XZ')
            if xz_count > 1:
                print(f"  ⚠ 警告: ZPL代码包含 {xz_count} 个打印命令（^XZ），可能导致重复打印")
                print(f"  [调试] 只使用第一个打印命令，移除后续的^XZ...")
                # 只保留第一个^XZ之前的内容，然后添加一个^XZ
                first_xz_pos = zpl_code.find('^XZ')
                if first_xz_pos >= 0:
                    zpl_code = zpl_code[:first_xz_pos + 3]  # 保留第一个^XZ
                    print(f"  [调试] 已清理ZPL代码，现在只包含1个打印命令")
            
            print(f"  [调试] 准备发送ZPL代码到设备: {self.device_path}")
            print(f"  [调试] ZPL代码长度: {len(zpl_code)} 字符")
            
            # 验证设备是否存在且可写
            import os
            import stat
            if not os.path.exists(self.device_path):
                print(f"[ERROR] 设备不存在: {self.device_path}")
                return False
            
            # 检查设备类型
            try:
                device_stat = os.stat(self.device_path)
                if not stat.S_ISCHR(device_stat.st_mode):
                    print(f"[ERROR] 不是字符设备: {self.device_path}")
                    return False
            except Exception as stat_error:
                print(f"  [调试] 无法获取设备信息: {stat_error}")
            
            # 编码ZPL代码
            zpl_bytes = zpl_code.encode('utf-8')
            print(f"  [调试] ZPL字节长度: {len(zpl_bytes)} 字节")
            
            # 使用O_SYNC标志确保数据立即写入设备
            try:
                # 以同步模式打开设备（O_SYNC确保数据立即写入）
                fd = os.open(self.device_path, os.O_WRONLY | os.O_SYNC)
                try:
                    # 写入数据
                    bytes_written = os.write(fd, zpl_bytes)
                    print(f"  [调试] 已写入 {bytes_written} 字节到文件描述符")
                    
                    # 使用fsync确保数据真正发送到设备
                    os.fsync(fd)
                    print(f"  [调试] 已调用fsync同步数据")
                    
                    print(f"[OK] ZPL设备打印成功: {self.device_path} (已写入 {bytes_written} 字节)")
                    
                    # 等待一小段时间，确保数据发送完成
                    import time
                    time.sleep(0.3)
                    
                    return True
                finally:
                    os.close(fd)
            except OSError as os_error:
                # 如果O_SYNC失败，尝试普通方式
                print(f"  [调试] O_SYNC模式失败，尝试普通模式: {os_error}")
                with open(self.device_path, 'wb') as device:
                    bytes_written = device.write(zpl_bytes)
                    print(f"  [调试] 已写入 {bytes_written} 字节")
                    device.flush()
                    print(f"  [调试] 已调用flush")
                    # 尝试同步
                    try:
                        os.fsync(device.fileno())
                        print(f"  [调试] 已调用fsync")
                    except Exception as sync_error:
                        print(f"  [调试] fsync失败: {sync_error}")
                print(f"[OK] ZPL设备打印成功: {self.device_path} (已写入 {bytes_written} 字节)")
                import time
                time.sleep(0.3)
                return True
            
        except PermissionError:
            print(f"[ERROR] 权限不足: {self.device_path}")
            print(f"提示：sudo chmod 666 {self.device_path} 或添加用户到lp组: sudo usermod -a -G lp $USER")
            return False
        except FileNotFoundError:
            print(f"[ERROR] 设备不存在: {self.device_path}")
            print(f"提示: 检查设备路径是否正确，可以使用 ls -l /dev/usb/lp* 查看可用设备")
            return False
        except Exception as e:
            print(f"[ERROR] ZPL设备打印失败: {e}")
            import traceback
            traceback.print_exc()
            return False

