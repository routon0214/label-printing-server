#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地打印代理 (Windows)
运行在本机（连接 Zebra USB 打印机的电脑上），定时拉取云端待打印任务并执行打印。

使用方法:
  1. 修改下方配置区（服务器地址、Token、打印机名称）
  2. 双击运行，或在命令行执行: python print_agent.py
  3. 保持运行即可，Ctrl+C 退出

依赖:
  pip install requests pywin32
"""

import sys
import os
import time
import json
import traceback

# PyInstaller 打包兼容：检测是否为 frozen 环境
if getattr(sys, 'frozen', False):
    # 打包后运行
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # 源码运行
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Windows 控制台编码修复（中文输出）- 仅在非 frozen 环境
if sys.platform == 'win32' and not getattr(sys, 'frozen', False):
    import io
    try:
        if sys.stdout.encoding != 'utf-8':
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        if sys.stderr.encoding != 'utf-8':
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass

# 添加项目路径，以便导入 src 模块
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, 'src'))

# ============================================================
# 📌 配置区 - 请根据实际情况修改
# ============================================================

# 云端打印服务器地址
SERVER_URL = 'http://iot.klxzdh.com'

# API Token（与服务器 config/printer_config.json 中一致）
API_TOKEN = 'wps-print-token-2026'

# 默认打印机名称（任务未指定打印机时使用）
# 名称在 Windows「设置→蓝牙和其他设备→打印机和扫描仪」中查看
DEFAULT_PRINTER_NAME = 'Deli DL-888T'

# 多打印机路由（可选）
# 本代理会自动根据任务中的 printer 字段匹配本机打印机名称
# 支持模糊匹配，名称不需要完全一致（如 "Deli DL-888T" ≈ "DL-888T"）
# 如果任务未指定打印机，使用上方的 DEFAULT_PRINTER_NAME
#
# 示例：WPS 提交 {"printer": "Deli DL-825T"} → 代理路由到 "Deli DL-825T(NEW)"

# 轮询间隔（秒），建议 3-10 秒
POLL_INTERVAL = 5

# 是否显示详细日志
DEBUG = True

# ============================================================
# 以下代码一般不需要修改
# ============================================================

try:
    import requests
except ImportError:
    print("=" * 60)
    print("错误: 缺少 requests 库")
    print("请运行: pip install requests")
    print("=" * 60)
    sys.exit(1)

try:
    from src.core.printer import ZebraPrinter
except ImportError:
    print("=" * 60)
    print("错误: 无法导入 src.core.printer 模块")
    print("请确保在项目根目录下运行本脚本")
    print("=" * 60)
    sys.exit(1)


def log(msg):
    """带时间戳的日志输出"""
    timestamp = time.strftime('%H:%M:%S')
    print(f"[{timestamp}] {msg}")


def get_pending_job():
    """从云端拉取一个待打印任务"""
    try:
        resp = requests.get(
            f'{SERVER_URL}/api/print/wps/pending',
            headers={'X-API-Token': API_TOKEN},
            timeout=15
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get('has_jobs'):
                return data
        elif resp.status_code == 401:
            log("[FAIL] 认证失败！请检查 API_TOKEN 配置")
        else:
            log(f"[WARN] 服务器返回异常: HTTP {resp.status_code}")
    except requests.exceptions.ConnectionError:
        log(f"[WARN] 无法连接到服务器 {SERVER_URL}，请检查网络")
    except requests.exceptions.Timeout:
        log("[WARN] 请求超时")
    except Exception as e:
        if DEBUG:
            log(f"[WARN] 拉取任务出错: {e}")
    return None


def report_result(job_id, success, error=''):
    """上报打印结果到云端"""
    try:
        resp = requests.post(
            f'{SERVER_URL}/api/print/wps/result',
            json={'job_id': job_id, 'success': success, 'error': error},
            headers={'X-API-Token': API_TOKEN},
            timeout=10
        )
        return resp.status_code == 200
    except Exception as e:
        if DEBUG:
            log(f"[WARN] 上报结果出错: {e}")
        return False



def main():
    print("=" * 60)
    print("  本地打印代理（多打印机支持）")
    print(f"  服务器: {SERVER_URL}")
    print(f"  默认打印机: {DEFAULT_PRINTER_NAME}")
    print(f"  轮询间隔: {POLL_INTERVAL}秒")
    print("=" * 60)
    print("  按 Ctrl+C 退出")
    print("=" * 60)
    print()
    
    # 检测本机可用打印机
    log("正在检测本机打印机...")
    try:
        import win32print
        all_printers = win32print.EnumPrinters(2)
        printer_names = [p[2] for p in all_printers]
        log(f"本机共 {len(printer_names)} 台打印机:")
        for name in printer_names:
            marker = " [默认]" if name == DEFAULT_PRINTER_NAME else ""
            log(f"  - {name}{marker}")
    except Exception as e:
        log(f"[WARN] 无法列举打印机: {e}")
    
    print()
    log("开始轮询待打印任务...")
    
    consecutive_errors = 0
    total_printed = 0
    # 缓存已创建的打印机实例，避免重复初始化
    printer_cache = {}
    
    def get_printer(printer_name):
        """获取打印机实例（带缓存）"""
        if not printer_name:
            printer_name = DEFAULT_PRINTER_NAME
        if printer_name not in printer_cache:
            printer_cache[printer_name] = ZebraPrinter(printer_name=printer_name)
        return printer_cache[printer_name]
    
    while True:
        try:
            job = get_pending_job()
            
            if job:
                job_id = job['job_id']
                title = job['title']
                zpl_code = job['zpl_code']
                target_printer = job.get('printer_name', '').strip() or DEFAULT_PRINTER_NAME
                
                log(f"[JOB] 发现任务: {job_id} - {title}")
                log(f"   目标打印机: {target_printer}")
                log(f"   ZPL长度: {len(zpl_code)} 字符")
                
                # 执行打印
                try:
                    printer = get_printer(target_printer)
                    success = printer.print_label(zpl_code)
                    if success:
                        log(f"[OK] 打印成功: {job_id} -> {target_printer}")
                        report_result(job_id, True)
                        total_printed += 1
                    else:
                        log(f"[FAIL] 打印失败: {job_id} -> {target_printer}")
                        report_result(job_id, False, '打印机返回失败')
                except Exception as print_error:
                    error_msg = str(print_error)
                    log(f"[FAIL] 打印异常: {job_id} -> {target_printer}: {error_msg}")
                    report_result(job_id, False, error_msg)
                
                consecutive_errors = 0
            else:
                # 没有任务，只在非空闲→空闲时打一次日志
                consecutive_errors = 0
            
            time.sleep(POLL_INTERVAL)
            
        except KeyboardInterrupt:
            print()
            log(f"收到退出信号。本次运行共打印: {total_printed} 个标签")
            break
        except Exception as e:
            consecutive_errors += 1
            if DEBUG or consecutive_errors <= 3:
                log(f"[WARN] 轮询出错: {e}")
                traceback.print_exc()
            time.sleep(min(POLL_INTERVAL * 2, 30))


if __name__ == '__main__':
    main()
