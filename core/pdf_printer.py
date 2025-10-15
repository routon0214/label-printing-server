#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF打印模块
支持普通文档打印
"""

import os
import platform
import tempfile
import base64


class PDFPrinter:
    """PDF打印机类"""
    
    def __init__(self, printer_name=None):
        """
        初始化PDF打印机
        
        Args:
            printer_name: 打印机名称（支持模糊匹配）
        """
        self.system = platform.system()
        self.configured_name = printer_name  # 配置的名称（可能是模糊名称）
        self.printer_name = self._resolve_printer_name(printer_name)  # 实际的系统名称
    
    def _resolve_printer_name(self, printer_name):
        """
        解析打印机名称，如果是模糊名称则查找实际名称
        
        Args:
            printer_name: 配置的打印机名称
            
        Returns:
            str: 实际的打印机名称
        """
        if not printer_name or self.system != 'Windows':
            return printer_name
        
        try:
            from utils.fuzzy_match import fuzzy_search_printer
            
            # 尝试模糊匹配
            matched_name = fuzzy_search_printer(printer_name)
            if matched_name:
                if matched_name != printer_name:
                    print(f"PDF打印机名称解析: '{printer_name}' → '{matched_name}'")
                return matched_name
            else:
                # 没有找到匹配，返回原名称
                return printer_name
                
        except Exception as e:
            # 如果模糊匹配失败，返回原名称
            return printer_name
    
    def print_pdf(self, pdf_data, printer_name=None):
        """
        打印PDF文件
        
        Args:
            pdf_data: PDF数据（可以是base64编码或文件路径）
            printer_name: 打印机名称（可选，覆盖默认）
            
        Returns:
            bool: 是否成功
        """
        # 如果传入了打印机名称，也需要解析
        if printer_name:
            printer = self._resolve_printer_name(printer_name)
        else:
            printer = self.printer_name
        
        print(f"开始处理PDF打印...")
        print(f"目标打印机: {printer or '默认打印机'}")
        print(f"数据类型判断: 长度={len(pdf_data)}")
        
        # 判断是文件路径还是base64编码
        # 简单启发式：如果数据很短且包含文件扩展名，可能是文件路径
        is_likely_path = (len(pdf_data) < 500 and 
                         ('.' in pdf_data and pdf_data.split('.')[-1].lower() in ['pdf', 'txt', 'doc', 'docx']))
        
        if is_likely_path and os.path.exists(pdf_data):
            # 文件路径且文件存在
            print(f"✓ 使用本地文件路径: {pdf_data}")
            pdf_file = pdf_data
            temp_file = None
        elif is_likely_path and not os.path.exists(pdf_data):
            # 看起来是文件路径但文件不存在
            print(f"✗ 错误：文件不存在: {pdf_data}")
            print("提示：请确保文件路径正确，或使用base64编码发送文件内容")
            return False
        else:
            # base64编码的数据
            print(f"解码Base64数据（长度: {len(pdf_data):,} 字符）...")
            try:
                pdf_bytes = base64.b64decode(pdf_data)
                print(f"✓ 解码成功，字节数: {len(pdf_bytes):,}")
                
                # 检测文件类型
                if pdf_bytes.startswith(b'%PDF'):
                    file_ext = '.pdf'
                    print("✓ 检测到PDF文件")
                elif pdf_bytes.startswith(b'PK\x03\x04'):
                    file_ext = '.docx'
                    print("✓ 检测到Word文档")
                elif pdf_bytes.startswith(b'\xd0\xcf\x11\xe0'):
                    file_ext = '.doc'
                    print("✓ 检测到旧版Word文档")
                else:
                    # 尝试解码为文本
                    try:
                        pdf_bytes.decode('utf-8')
                        file_ext = '.txt'
                        print("✓ 检测到文本文件")
                    except:
                        file_ext = '.bin'
                        print("⚠ 未知文件类型，保存为二进制文件")
                
                # 创建临时文件
                temp_file = tempfile.NamedTemporaryFile(suffix=file_ext, delete=False)
                temp_file.write(pdf_bytes)
                temp_file.close()
                pdf_file = temp_file.name
                print(f"临时文件已创建: {pdf_file}")
                
            except Exception as e:
                print(f"✗ 解码数据失败: {e}")
                import traceback
                traceback.print_exc()
                return False
        
        try:
            if self.system == 'Windows':
                return self._print_windows(pdf_file, printer)
            elif self.system == 'Linux':
                return self._print_linux(pdf_file, printer)
            else:
                print(f"不支持的系统: {self.system}")
                return False
        finally:
            # 清理临时文件
            if temp_file and os.path.exists(pdf_file):
                try:
                    os.remove(pdf_file)
                except:
                    pass
    
    def _print_windows(self, pdf_file, printer_name):
        """Windows PDF/文档静默打印"""
        try:
            import win32print
            import subprocess
            import time
            
            # 如果没有指定打印机，使用默认打印机
            if not printer_name:
                printer_name = win32print.GetDefaultPrinter()
            
            print(f"使用Windows打印机: {printer_name}")
            print(f"打印文件: {pdf_file}")
            
            # 方案1: 使用SumatraPDF静默打印（推荐，最快）
            # 获取用户目录
            user_profile = os.environ.get('USERPROFILE', '')
            
            sumatra_paths = [
                r"C:\Program Files\SumatraPDF\SumatraPDF.exe",
                r"C:\Program Files (x86)\SumatraPDF\SumatraPDF.exe",
                os.path.join(user_profile, r"AppData\Local\SumatraPDF\SumatraPDF.exe") if user_profile else None,
                os.path.join(user_profile, r"AppData\Local\Programs\SumatraPDF\SumatraPDF.exe") if user_profile else None,
            ]
            
            # 过滤掉 None 值
            sumatra_paths = [p for p in sumatra_paths if p]
            
            print(f"正在检查 SumatraPDF 路径...")
            sumatra_found = None
            for sumatra in sumatra_paths:
                print(f"  检查: {sumatra}")
                if os.path.exists(sumatra):
                    print(f"  ✓ 找到: {sumatra}")
                    sumatra_found = sumatra
                    break
            
            if sumatra_found:
                print(f"使用SumatraPDF打印（显示对话框）: {sumatra_found}")
                try:
                    # 使用打印对话框，让用户可以调整设置
                    cmd = [
                        sumatra_found,
                        '-print-dialog',  # 显示打印对话框
                        pdf_file
                    ]
                    print(f"执行命令: {' '.join(cmd)}")
                    print(f"提示: 将显示打印对话框，请手动确认设置")
                    
                    # 启动进程但不等待（因为需要用户交互）
                    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    
                    print(f"✓ 已打开打印对话框")
                    print(f"  目标打印机: {printer_name}")
                    print(f"  请在对话框中确认设置并打印")
                    return True
                    
                except Exception as e:
                    print(f"✗ SumatraPDF启动失败: {e}")
                    import traceback
                    traceback.print_exc()
                    print(f"  尝试其他打印方案...")
            
            # 方案2: 使用Adobe Reader打印（显示对话框）
            adobe_paths = [
                r"C:\Program Files\Adobe\Acrobat DC\Acrobat\Acrobat.exe",
                r"C:\Program Files (x86)\Adobe\Acrobat Reader DC\Reader\AcroRd32.exe",
                r"C:\Program Files\Adobe\Acrobat Reader DC\Reader\AcroRd32.exe",
            ]
            
            for adobe in adobe_paths:
                if os.path.exists(adobe):
                    print(f"使用Adobe Reader打印（显示对话框）...")
                    try:
                        # 使用 /p 显示打印对话框，而不是 /t 静默打印
                        cmd = [
                            adobe,
                            '/p',  # 显示打印对话框
                            pdf_file
                        ]
                        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        print(f"✓ 已打开Adobe Reader打印对话框")
                        print(f"  请在对话框中选择打印机: {printer_name}")
                        return True
                    except Exception as e:
                        print(f"Adobe Reader启动失败: {e}")
                        break
            
            # 方案3: 对于文本文件，使用notepad打印（显示对话框）
            if pdf_file.endswith('.txt'):
                print(f"使用notepad打印文本文件（显示对话框）...")
                try:
                    # notepad /p 会显示打印对话框
                    cmd = ['notepad', '/p', pdf_file]
                    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    print(f"✓ 已打开notepad打印对话框")
                    print(f"  请在对话框中选择打印机: {printer_name}")
                    return True
                except Exception as e:
                    print(f"notepad启动失败: {e}")
            
            # 方案4: 使用win32print直接打印（适合文本和ZPL）
            if pdf_file.endswith(('.txt', '.zpl')):
                print(f"使用win32print RAW模式打印...")
                return self._print_windows_raw(pdf_file, printer_name)
            
            # 方案5: 提示用户安装工具
            print("\n" + "=" * 60)
            print("⚠ 未找到合适的PDF打印工具")
            print("=" * 60)
            print("\n为了打印PDF文档，请安装以下工具之一：")
            print("\n1. SumatraPDF（推荐）⭐")
            print("   - 免费、轻量、易用")
            print("   - 下载: https://www.sumatrapdfreader.org/")
            print("   - 安装到默认路径即可")
            print("\n2. Adobe Acrobat Reader DC")
            print("   - 官方PDF阅读器")
            print("   - 功能完整")
            print("\n说明: 打印时会显示打印对话框，可以手动调整设置")
            print("=" * 60)
            
            return False
            
        except ImportError:
            print("✗ 错误：需要安装 pywin32: pip install pywin32")
            return False
        except Exception as e:
            print(f"✗ Windows打印失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _print_windows_raw(self, file_path, printer_name):
        """Windows备用打印方案（直接打印原始数据）"""
        try:
            import win32print
            
            print(f"使用RAW打印方式...")
            
            # 读取文件内容
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # 打开打印机
            printer_handle = win32print.OpenPrinter(printer_name)
            
            try:
                # 开始打印任务
                job_info = ("Document Print", None, "RAW")
                win32print.StartDocPrinter(printer_handle, 1, job_info)
                win32print.StartPagePrinter(printer_handle)
                
                # 发送数据
                win32print.WritePrinter(printer_handle, file_data)
                
                # 结束打印
                win32print.EndPagePrinter(printer_handle)
                win32print.EndDocPrinter(printer_handle)
                
                print(f"✓ RAW打印成功: {printer_name}")
                return True
                
            finally:
                win32print.ClosePrinter(printer_handle)
                
        except Exception as e:
            print(f"✗ RAW打印失败: {e}")
            return False
    
    def _print_linux(self, pdf_file, printer_name):
        """Linux PDF打印"""
        try:
            import subprocess
            
            # 使用lpr命令打印
            cmd = ['lpr']
            if printer_name:
                cmd.extend(['-P', printer_name])
            cmd.append(pdf_file)
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✓ Linux PDF打印成功: {printer_name or '默认打印机'}")
                return True
            else:
                print(f"✗ Linux PDF打印失败: {result.stderr}")
                return False
                
        except FileNotFoundError:
            print("错误：未找到lpr命令，请安装CUPS")
            return False
        except Exception as e:
            print(f"✗ Linux PDF打印失败: {e}")
            return False

