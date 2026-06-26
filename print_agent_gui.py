#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
标签打印代理 - 图形客户端
- 可视化选择/切换默认打印机
- 开机自动启动
- 最小化到系统托盘
- 实时显示打印状态和日志

依赖: pip install requests pywin32 pillow
"""

import sys
import os
import json
import time
import threading
import traceback
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import ctypes
import struct

# ── 路径 ──────────────────────────────────────
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(BASE_DIR, 'agent_config.json')

DEFAULT_CONFIG = {
    'server_url': 'http://iot.klxzdh.com',
    'api_token': 'wps-print-token-2026',
    'printer_name': 'Deli DL-825T',
    'poll_interval': 5,
    'auto_start': False
}

# ── 系统托盘图标 (win32) ──────────────────────

# 托盘消息
WM_TRAY = 0x8001
WM_USER = 0x0400
NIM_ADD = 0x00000000
NIM_MODIFY = 0x00000001
NIM_DELETE = 0x00000002
NIF_MESSAGE = 0x00000001
NIF_ICON = 0x00000002
NIF_TIP = 0x00000004
NIF_INFO = 0x00000010
NIIF_INFO = 0x00000001
WM_LBUTTONDBLCLK = 0x0203
WM_RBUTTONUP = 0x0205
TPM_RETURNCMD = 0x0100
MF_STRING = 0x0000
MF_SEPARATOR = 0x0800
IMAGE_ICON = 1
LR_LOADFROMFILE = 0x0010


class TrayIcon:
    """Windows 系统托盘图标"""

    def __init__(self, callback_show=None, callback_exit=None):
        self.callback_show = callback_show
        self.callback_exit = callback_exit
        self.hwnd = None
        self._running = False

    def _create_icon(self, size=32):
        """用 Pillow 创建简单的打印图标"""
        from PIL import Image, ImageDraw
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        # 简化的打印机图标
        m = size // 8
        # 打印机主体
        draw.rectangle([m, m * 2, m * 7, m * 7], fill=(64, 64, 64), outline=(32, 32, 32), width=1)
        # 进纸口
        draw.rectangle([m * 3, 0, m * 5, m * 2], fill=(255, 255, 255), outline=(32, 32, 32), width=1)
        # 出纸口
        draw.rectangle([m * 2, m * 5, m * 6, m * 6], fill=(255, 255, 255), outline=(128, 128, 128), width=1)
        return img

    def _create_icon_handle(self):
        try:
            img = self._create_icon(32)
            import io
            buf = io.BytesIO()
            img.save(buf, format='BMP')
            buf.seek(0)
            data = buf.read()
            hicon = ctypes.windll.user32.CreateIconFromResource(
                data[14:], len(data) - 14, 1, 0x00030000
            )
            if hicon:
                return hicon
        except Exception:
            pass
        # 降级：使用默认应用程序图标
        return ctypes.windll.user32.LoadIconW(0, 32512)  # IDI_APPLICATION

    def _wnd_proc(self, hwnd, msg, wparam, lparam):
        if msg == WM_TRAY:
            if lparam == WM_LBUTTONDBLCLK:
                if self.callback_show:
                    self.callback_show()
            elif lparam == WM_RBUTTONUP:
                self._show_menu()
        return ctypes.windll.user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    def _show_menu(self):
        menu = ctypes.windll.user32.CreatePopupMenu()
        ctypes.windll.user32.AppendMenuW(menu, MF_STRING, 1, "显示窗口")
        ctypes.windll.user32.AppendMenuW(menu, MF_SEPARATOR, 0, None)
        ctypes.windll.user32.AppendMenuW(menu, MF_STRING, 2, "退出代理")
        ctypes.windll.user32.SetForegroundWindow(self.hwnd)
        cmd = ctypes.windll.user32.TrackPopupMenu(
            menu, TPM_RETURNCMD, 0, 0, 0, 0, self.hwnd, None
        )
        ctypes.windll.user32.DestroyMenu(menu)
        if cmd == 1 and self.callback_show:
            self.callback_show()
        elif cmd == 2 and self.callback_exit:
            self.callback_exit()

    def show(self):
        if self._running:
            return
        self._running = True

        # 注册窗口类
        wndclass = ctypes.WinDLL('user32')
        wc = struct.pack('I', 24)  # cbSize
        wc += struct.pack('I', 0)  # style
        wc += ctypes.c_void_p(ctypes.WINFUNCTYPE(
            ctypes.c_long, ctypes.c_long, ctypes.c_uint,
            ctypes.c_long, ctypes.c_long
        )(self._wnd_proc))
        # Pack remaining fields
        wc += b'\x00' * 48

        # The above approach is fragile. Let me use a simpler method.
        # Actually, let me register the class properly.
        hinst = ctypes.windll.kernel32.GetModuleHandleW(None)

        class WNDCLASS(ctypes.Structure):
            _fields_ = [
                ("style", ctypes.c_uint),
                ("lpfnWndProc", ctypes.WINFUNCTYPE(
                    ctypes.c_long, ctypes.c_long, ctypes.c_uint,
                    ctypes.c_long, ctypes.c_long)),
                ("cbClsExtra", ctypes.c_int),
                ("cbWndExtra", ctypes.c_int),
                ("hInstance", ctypes.c_void_p),
                ("hIcon", ctypes.c_void_p),
                ("hCursor", ctypes.c_void_p),
                ("hbrBackground", ctypes.c_void_p),
                ("lpszMenuName", ctypes.c_wchar_p),
                ("lpszClassName", ctypes.c_wchar_p),
            ]

        wnd_proc = ctypes.WINFUNCTYPE(
            ctypes.c_long, ctypes.c_long, ctypes.c_uint,
            ctypes.c_long, ctypes.c_long
        )(self._wnd_proc)

        wc = WNDCLASS()
        wc.style = 0
        wc.lpfnWndProc = wnd_proc
        wc.cbClsExtra = 0
        wc.cbWndExtra = 0
        wc.hInstance = hinst
        wc.hIcon = 0
        wc.hCursor = 0
        wc.hbrBackground = 0
        wc.lpszMenuName = None
        wc.lpszClassName = "PrintAgentTray"

        ctypes.windll.user32.RegisterClassW(ctypes.byref(wc))

        self.hwnd = ctypes.windll.user32.CreateWindowExW(
            0, "PrintAgentTray", "Tray", 0,
            0, 0, 0, 0, None, None, hinst, None
        )

        hicon = self._create_icon_handle()

        # NOTIFYICONDATA
        class NOTIFYICONDATA(ctypes.Structure):
            _fields_ = [
                ("cbSize", ctypes.c_uint),
                ("hWnd", ctypes.c_void_p),
                ("uID", ctypes.c_uint),
                ("uFlags", ctypes.c_uint),
                ("uCallbackMessage", ctypes.c_uint),
                ("hIcon", ctypes.c_void_p),
                ("szTip", ctypes.c_wchar * 128),
                ("dwState", ctypes.c_uint),
                ("dwStateMask", ctypes.c_uint),
                ("szInfo", ctypes.c_wchar * 256),
                ("uTimeout", ctypes.c_uint),
                ("szInfoTitle", ctypes.c_wchar * 64),
                ("dwInfoFlags", ctypes.c_uint),
            ]

        nid = NOTIFYICONDATA()
        nid.cbSize = ctypes.sizeof(NOTIFYICONDATA)
        nid.hWnd = self.hwnd
        nid.uID = 1
        nid.uFlags = NIF_MESSAGE | NIF_ICON | NIF_TIP
        nid.uCallbackMessage = WM_TRAY
        nid.hIcon = hicon
        nid.szTip = "标签打印代理"
        ctypes.windll.shell32.Shell_NotifyIconW(NIM_ADD, ctypes.byref(nid))

    def remove(self):
        if self.hwnd:
            nid = struct.pack('I', ctypes.sizeof(ctypes.c_int) * 50)  # dummy
            # Re-create proper NID for removal
            class _NID(ctypes.Structure):
                _fields_ = [("cbSize", ctypes.c_uint), ("hWnd", ctypes.c_void_p), ("uID", ctypes.c_uint)]
            nid = _NID()
            nid.cbSize = ctypes.sizeof(_NID)
            nid.hWnd = self.hwnd
            nid.uID = 1
            ctypes.windll.shell32.Shell_NotifyIconW(NIM_DELETE, ctypes.byref(nid))
            ctypes.windll.user32.DestroyWindow(self.hwnd)
            self.hwnd = None
            self._running = False


# ── 导入检查 ──────────────────────────────────

def check_imports():
    """检查必要库，返回缺失列表"""
    missing = []
    try:
        import requests
    except ImportError:
        missing.append('requests')
    try:
        import win32print
        import win32ui
    except ImportError:
        missing.append('pywin32')
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        missing.append('pillow')
    return missing


# ── 图形客户端 ──────────────────────────────────

class PrintAgentGUI:
    """标签打印代理 GUI"""

    def __init__(self):
        self.config = self._load_config()
        self.running = False
        self.total_printed = 0
        self.agent_thread = None
        self.printer_list = []
        self.tray = None
        self._exit_requested = False

        # 主窗口
        self.root = tk.Tk()
        self.root.title("标签打印代理 v1.0")
        self.root.geometry("520x560")
        self.root.resizable(True, True)
        self.root.minsize(480, 480)

        # 关闭按钮 → 最小化到托盘
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # 窗口图标
        try:
            self.root.iconbitmap(default=os.path.join(BASE_DIR, 'static', 'favicon.ico'))
        except:
            pass

        self._setup_ui()
        self._refresh_printers()

        # 加载打印机选择
        saved_printer = self.config.get('printer_name', '')
        if saved_printer and saved_printer in self.printer_list:
            self.printer_var.set(saved_printer)
        elif self.printer_list:
            self.printer_var.set(self.printer_list[0])

        # 居中窗口
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.root.geometry(f"+{x}+{y}")

    def _load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
                for k, v in DEFAULT_CONFIG.items():
                    if k not in cfg:
                        cfg[k] = v
                return cfg
            except:
                pass
        return dict(DEFAULT_CONFIG)

    def _save_config(self):
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self._log(f"[WARN] 保存配置失败: {e}")

    def _setup_ui(self):
        main = ttk.Frame(self.root, padding=12)
        main.pack(fill=tk.BOTH, expand=True)

        row = 0

        # ── 服务器配置 ──
        ttk.Label(main, text="服务器地址", font=('', 9, 'bold')).grid(
            row=row, column=0, columnspan=3, sticky=tk.W, pady=(0, 2))
        row += 1
        self.server_entry = ttk.Entry(main, width=50)
        self.server_entry.insert(0, self.config.get('server_url', ''))
        self.server_entry.grid(row=row, column=0, columnspan=3, sticky=tk.EW, pady=(0, 6))

        row += 1
        ttk.Label(main, text="API Token", font=('', 9, 'bold')).grid(
            row=row, column=0, columnspan=3, sticky=tk.W, pady=(0, 2))
        row += 1
        token_frame = ttk.Frame(main)
        token_frame.grid(row=row, column=0, columnspan=3, sticky=tk.EW, pady=(0, 6))
        self.token_entry = ttk.Entry(token_frame, width=50)
        self.token_entry.insert(0, self.config.get('api_token', ''))
        self.token_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.show_token_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(token_frame, text="显示", variable=self.show_token_var,
                        command=lambda: self.token_entry.configure(
                            show='' if self.show_token_var.get() else '*')
                        ).pack(side=tk.LEFT, padx=(5, 0))
        # 初始化隐藏
        self.token_entry.configure(show='*')

        row += 1
        ttk.Label(main, text="默认打印机", font=('', 9, 'bold')).grid(
            row=row, column=0, columnspan=3, sticky=tk.W, pady=(0, 2))
        row += 1
        printer_frame = ttk.Frame(main)
        printer_frame.grid(row=row, column=0, columnspan=3, sticky=tk.EW, pady=(0, 6))
        self.printer_var = tk.StringVar()
        self.printer_combo = ttk.Combobox(printer_frame, textvariable=self.printer_var,
                                          state='readonly', width=40)
        self.printer_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(printer_frame, text="🔄 刷新", command=self._refresh_printers,
                   width=8).pack(side=tk.LEFT, padx=(5, 0))

        row += 1
        lang_frame = ttk.Frame(main)
        lang_frame.grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=(0, 6))
        ttk.Label(lang_frame, text="打印机语言:", font=('', 9)).pack(side=tk.LEFT)
        self.language_var = tk.StringVar(value=self.config.get('printer_language', 'zpl'))
        self.lang_combo = ttk.Combobox(lang_frame, textvariable=self.language_var,
                                       values=['zpl', 'tspl', 'auto'], state='readonly', width=12)
        self.lang_combo.pack(side=tk.LEFT, padx=(5, 5))
        ttk.Label(lang_frame, text="zpl=直通 | tspl=自动转换 | auto=自动检测", font=('', 8)).pack(side=tk.LEFT)

        row += 1
        self.force_printer_var = tk.BooleanVar(value=self.config.get('force_configured_printer', True))
        ttk.Checkbutton(main, text="⚡ 忽略任务指定的打印机，始终使用上方选择的打印机",
                        variable=self.force_printer_var).grid(
            row=row, column=0, columnspan=3, sticky=tk.W, pady=(0, 4))

        row += 1
        ttk.Label(main, text="轮询间隔 (秒)", font=('', 9, 'bold')).grid(
            row=row, column=0, sticky=tk.W, pady=(0, 2))
        row += 1
        interval_frame = ttk.Frame(main)
        interval_frame.grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=(0, 6))
        self.interval_var = tk.IntVar(value=self.config.get('poll_interval', 5))
        self.interval_spin = ttk.Spinbox(interval_frame, from_=1, to=60, textvariable=self.interval_var,
                    width=5)
        self.interval_spin.pack(side=tk.LEFT)
        ttk.Label(interval_frame, text="（建议 3-10 秒）").pack(side=tk.LEFT, padx=(5, 0))

        # ── 开机自启动 ──
        self.auto_start_var = tk.BooleanVar(value=self.config.get('auto_start', False))
        ttk.Checkbutton(interval_frame, text="开机自启动", variable=self.auto_start_var,
                        command=self._toggle_auto_start).pack(side=tk.RIGHT, padx=(30, 0))

        # ── 控制按钮 ──
        row += 1
        btn_frame = ttk.Frame(main)
        btn_frame.grid(row=row, column=0, columnspan=3, pady=(10, 5), sticky=tk.EW)
        self.start_btn = ttk.Button(btn_frame, text="▶ 启动代理", command=self._toggle_agent, width=14)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="💾 保存配置", command=self._save_settings, width=14).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🔽 最小化到托盘", command=self._minimize_to_tray, width=16).pack(side=tk.LEFT, padx=5)

        # ── 状态栏 ──
        row += 1
        status_frame = ttk.Frame(main, relief=tk.SUNKEN, borderwidth=1)
        status_frame.grid(row=row, column=0, columnspan=3, sticky=tk.EW, pady=(5, 2))
        status_frame.columnconfigure(1, weight=1)
        self.status_label = ttk.Label(status_frame, text="● 就绪", foreground="gray")
        self.status_label.pack(side=tk.LEFT, padx=(8, 0), pady=4)
        self.count_label = ttk.Label(status_frame, text="已打印: 0")
        self.count_label.pack(side=tk.RIGHT, padx=(0, 8), pady=4)

        # ── 日志区 ──
        row += 1
        ttk.Label(main, text="运行日志", font=('', 9, 'bold')).grid(
            row=row, column=0, columnspan=3, sticky=tk.W, pady=(8, 2))
        row += 1
        self.log_area = scrolledtext.ScrolledText(main, width=58, height=14,
                                                   state=tk.DISABLED, font=('Consolas', 9))
        self.log_area.grid(row=row, column=0, columnspan=3, sticky=tk.NSEW)
        main.rowconfigure(row, weight=1)
        main.columnconfigure(1, weight=1)

        # 右键菜单
        self.log_menu = tk.Menu(self.root, tearoff=0)
        self.log_menu.add_command(label="清空日志", command=self._clear_log)
        self.log_area.bind("<Button-3>", lambda e: self.log_menu.post(e.x_root, e.y_root))

    def _refresh_printers(self):
        """刷新打印机列表"""
        try:
            import win32print
            printers = win32print.EnumPrinters(2)  # PRINTER_ENUM_LOCAL
            self.printer_list = [p[2] for p in printers]
            current = self.printer_var.get()
            self.printer_combo['values'] = self.printer_list
            if not current and self.printer_list:
                self.printer_var.set(self.printer_list[0])
            elif current not in self.printer_list and self.printer_list:
                self.printer_var.set(self.printer_list[0])
            self._log(f"检测到 {len(self.printer_list)} 台打印机")
            for name in self.printer_list:
                self._log(f"  - {name}")
        except Exception as e:
            self._log(f"[WARN] 无法列举打印机: {e}")

    def _save_settings(self):
        """保存配置"""
        self.config['server_url'] = self.server_entry.get().strip()
        self.config['api_token'] = self.token_entry.get().strip()
        self.config['printer_name'] = self.printer_var.get()
        self.config['printer_language'] = self.language_var.get()
        self.config['poll_interval'] = self.interval_var.get()
        self.config['auto_start'] = self.auto_start_var.get()
        self.config['force_configured_printer'] = self.force_printer_var.get()
        self._save_config()
        self._log("配置已保存")
        # 也尝试保存到 print_agent.py（兼容旧版直接运行）
        self._save_to_agent_py()

    def _save_to_agent_py(self):
        """将配置同步到 print_agent.py（兼容命令行直接运行）"""
        agent_py = os.path.join(BASE_DIR, 'print_agent.py')
        if not os.path.exists(agent_py):
            return
        try:
            with open(agent_py, 'r', encoding='utf-8') as f:
                content = f.read()

            # 替换关键配置行
            replacements = {
                r"SERVER_URL = '": f"SERVER_URL = '{self.config['server_url']}",
                r"API_TOKEN = '": f"API_TOKEN = '{self.config['api_token']}",
                r"DEFAULT_PRINTER_NAME = '": f"DEFAULT_PRINTER_NAME = '{self.config['printer_name']}",
                r"DEFAULT_PRINTER_LANGUAGE = '": f"DEFAULT_PRINTER_LANGUAGE = '{self.config.get('printer_language', 'zpl')}",
            }

            lines = content.split('\n')
            modified = False
            for i, line in enumerate(lines):
                for old_prefix, new_line in replacements.items():
                    if line.strip().startswith(old_prefix.rstrip("'")):
                        indent = line[:len(line) - len(line.lstrip())]
                        lines[i] = f"{indent}{new_line}'"
                        modified = True
                        break

            if modified:
                with open(agent_py, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(lines))
                self._log("已同步配置到 print_agent.py")
        except Exception as e:
            pass  # 静默失败，GUI 配置优先

    def _toggle_auto_start(self):
        """切换开机自启动"""
        enabled = self.auto_start_var.get()
        self.config['auto_start'] = enabled
        self._save_config()
        if enabled:
            self._set_auto_start()
        else:
            self._remove_auto_start()

    def _set_auto_start(self):
        """写入注册表实现开机自启动"""
        try:
            import winreg
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
                app_path = os.path.abspath(__file__)
                python_path = sys.executable
                cmd = f'"{python_path}" "{app_path}"'
                winreg.SetValueEx(key, "PrintAgent", 0, winreg.REG_SZ, cmd)
            self._log("已设置开机自启动")
        except Exception as e:
            self._log(f"[WARN] 设置开机自启动失败: {e}")
            messagebox.showwarning("开机自启动", f"设置失败：{e}\n请以管理员身份运行后重试。")

    def _remove_auto_start(self):
        """删除开机自启动注册表项"""
        try:
            import winreg
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
                try:
                    winreg.DeleteValue(key, "PrintAgent")
                except FileNotFoundError:
                    pass
            self._log("已取消开机自启动")
        except Exception as e:
            self._log(f"[WARN] 取消开机自启动失败: {e}")

    def _toggle_agent(self):
        """启动/停止代理"""
        if self.running:
            self._stop_agent()
        else:
            self._start_agent()

    def _start_agent(self):
        """启动打印代理后台线程"""
        # 先保存配置
        self._save_settings()

        server = self.config.get('server_url', '').strip()
        token = self.config.get('api_token', '').strip()
        if not server:
            messagebox.showwarning("配置错误", "请输入服务器地址")
            return
        if not token:
            messagebox.showwarning("配置错误", "请输入 API Token")
            return

        self.running = True
        self._exit_requested = False
        self.start_btn.configure(text="⏸ 停止代理")
        self.server_entry.configure(state='disabled')
        self.token_entry.configure(state='disabled')
        self.printer_combo.configure(state='disabled')
        self.interval_spin.configure(state='disabled')

        self.status_label.configure(text="● 运行中", foreground="green")
        self._log("=" * 50)
        self._log("打印代理已启动")
        self._log(f"服务器: {server}")
        self._log(f"默认打印机: {self.config['printer_name']}")
        self._log(f"轮询间隔: {self.config['poll_interval']} 秒")
        self._log("=" * 50)

        self.agent_thread = threading.Thread(target=self._agent_loop, daemon=True)
        self.agent_thread.start()

    def _stop_agent(self):
        """停止打印代理"""
        self.running = False
        self._exit_requested = True
        self.start_btn.configure(text="▶ 启动代理")
        self.server_entry.configure(state='normal')
        self.token_entry.configure(state='normal')
        self.printer_combo.configure(state='readonly')
        self.interval_spin.configure(state='normal')
        self.status_label.configure(text="● 已停止", foreground="gray")
        self._log("打印代理已停止")

    def _agent_loop(self):
        """后台代理主循环"""
        import requests
        from src.core.printer import ZebraPrinter

        server = self.config['server_url'].strip().rstrip('/')
        token = self.config['api_token'].strip()
        printer_name = self.config.get('printer_name', '')
        printer_language = self.config.get('printer_language', 'zpl') or None  # 'auto' → None 触发自动检测
        if printer_language == 'auto':
            printer_language = None
        interval = self.config.get('poll_interval', 5)

        consecutive_errors = 0

        # 初始化打印机
        try:
            printer = ZebraPrinter(printer_name=printer_name, printer_language=printer_language)
        except Exception as e:
            self.root.after(0, self._log, f"[FAIL] 打印机初始化失败: {e}")
            self.root.after(0, self._stop_agent)
            return

        self.root.after(0, self._log, "开始轮询待打印任务...")

        while self.running:
            try:
                resp = requests.get(
                    f'{server}/api/print/wps/pending',
                    headers={'X-API-Token': token},
                    timeout=15
                )
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get('has_jobs'):
                        job_id = data['job_id']
                        title = data['title']
                        zpl_code = data['zpl_code']
                        job_printer_name = data.get('printer_name', '').strip()
                        force = self.config.get('force_configured_printer', True)
                        if force or not job_printer_name:
                            target = printer_name
                        else:
                            target = job_printer_name

                        self.root.after(0, self._log, f"[JOB] 发现任务: {job_id} - {title}")
                        self.root.after(0, self._log, f"  任务指定打印机: {job_printer_name or '(无)'} → 使用: {target}")

                        try:
                            if target != printer_name:
                                # 不同打印机，创建新实例
                                job_printer = ZebraPrinter(printer_name=target, printer_language=printer_language)
                            else:
                                job_printer = printer

                            success = job_printer.print_label(zpl_code)
                            if success:
                                self.root.after(0, self._log, f"[OK] 打印成功: {job_id}")
                                self._report_result(server, token, job_id, True)
                                self.total_printed += 1
                                self.root.after(0, self._update_count)
                            else:
                                self.root.after(0, self._log, f"[FAIL] 打印失败: {job_id}")
                                self._report_result(server, token, job_id, False, '打印机返回失败')
                        except Exception as pe:
                            self.root.after(0, self._log, f"[FAIL] 打印异常: {job_id}: {pe}")
                            self._report_result(server, token, job_id, False, str(pe))

                        consecutive_errors = 0

                elif resp.status_code == 401:
                    self.root.after(0, self._log, "[FAIL] 认证失败！请检查 API Token")
                    consecutive_errors += 1
                elif resp.status_code != 200:
                    consecutive_errors += 1
            except requests.exceptions.ConnectionError:
                consecutive_errors += 1
                if consecutive_errors == 1:
                    self.root.after(0, self._log, f"[WARN] 无法连接到服务器 {server}")
            except Exception as e:
                consecutive_errors += 1
                if consecutive_errors <= 3:
                    self.root.after(0, self._log, f"[WARN] 轮询出错: {e}")

            # 等间隔
            for _ in range(interval):
                if not self.running:
                    break
                time.sleep(1)

    def _report_result(self, server, token, job_id, success, error=''):
        """上报打印结果"""
        try:
            import requests
            requests.post(
                f'{server}/api/print/wps/result',
                json={'job_id': job_id, 'success': success, 'error': error},
                headers={'X-API-Token': token},
                timeout=10
            )
        except:
            pass

    def _update_count(self):
        self.count_label.configure(text=f"已打印: {self.total_printed}")

    def _log(self, msg):
        """写入日志"""
        timestamp = time.strftime('%H:%M:%S')
        line = f"[{timestamp}] {msg}"
        self.log_area.configure(state=tk.NORMAL)
        self.log_area.insert(tk.END, line + '\n')
        self.log_area.see(tk.END)
        self.log_area.configure(state=tk.DISABLED)

    def _clear_log(self):
        self.log_area.configure(state=tk.NORMAL)
        self.log_area.delete(1.0, tk.END)
        self.log_area.configure(state=tk.DISABLED)

    def _minimize_to_tray(self):
        """最小化到系统托盘"""
        if not self.tray:
            try:
                self.tray = TrayIcon(
                    callback_show=self._restore_from_tray,
                    callback_exit=self._exit_from_tray
                )
                self.tray.show()
            except Exception as e:
                self._log(f"[WARN] 无法创建托盘图标: {e}")
                self.root.iconify()
                return
        self.root.withdraw()

    def _restore_from_tray(self):
        """从托盘恢复窗口"""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def _exit_from_tray(self):
        """从托盘退出"""
        self._exit_requested = True
        if self.running:
            self._stop_agent()
        if self.tray:
            try:
                self.tray.remove()
            except:
                pass
        self.root.destroy()

    def on_close(self):
        """关闭窗口 → 最小化到托盘"""
        if self.running:
            reply = messagebox.askyesno(
                "标签打印代理",
                "代理正在运行中。\n\n选择「是」最小化到托盘继续运行\n选择「否」停止代理并退出"
            )
            if reply:
                self._minimize_to_tray()
            else:
                self._exit_from_tray()
        else:
            self._exit_from_tray()

    def run(self):
        """启动 GUI 主循环"""
        self.root.mainloop()


# ── 主入口 ──────────────────────────────────────

def main():
    # 检查依赖
    missing = check_imports()
    if missing:
        root = tk.Tk()
        root.withdraw()
        msg = "缺少以下 Python 库，请先安装：\n\n"
        for m in missing:
            msg += f"  pip install {m}\n"
        msg += "\n安装完成后重新运行本程序。"
        messagebox.showerror("缺少依赖", msg)
        root.destroy()
        sys.exit(1)

    # 确保能导入 ZebraPrinter
    sys.path.insert(0, BASE_DIR)
    sys.path.insert(0, os.path.join(BASE_DIR, 'src'))
    try:
        from src.core.printer import ZebraPrinter
    except ImportError as e:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "导入错误",
            f"无法导入打印模块: {e}\n\n"
            "请确保在项目根目录下运行本程序。"
        )
        root.destroy()
        sys.exit(1)

    app = PrintAgentGUI()
    app.run()


if __name__ == '__main__':
    main()
