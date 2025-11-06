#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断ZT411打印问题
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

def check_printer_status():
    """检查打印机状态"""
    print("="*70)
    print("诊断ZT411打印机")
    print("="*70)
    print()
    
    try:
        import win32print
        
        # 查找ZT411打印机
        printers = [p[2] for p in win32print.EnumPrinters(2)]
        
        print(f"发现 {len(printers)} 台打印机:")
        for i, name in enumerate(printers, 1):
            print(f"  {i}. {name}")
        
        print()
        
        # 查找ZT411
        zt411_printers = [p for p in printers if 'ZT411' in p or 'ZDesigner' in p]
        
        if not zt411_printers:
            print("[ERROR] 未找到ZT411打印机!")
            return
        
        printer_name = zt411_printers[0]
        print(f"[OK] 找到打印机: {printer_name}")
        print()
        
        # 检查打印机状态
        print("检查打印机状态...")
        try:
            handle = win32print.OpenPrinter(printer_name)
            info = win32print.GetPrinter(handle, 2)
            
            status = info['Status']
            attributes = info['Attributes']
            
            print(f"  状态码: {status}")
            
            # 解析状态
            status_messages = {
                0x00000001: "暂停",
                0x00000002: "错误",
                0x00000004: "正在删除",
                0x00000008: "纸张问题",
                0x00000010: "纸张用完",
                0x00000020: "需要手动送纸",
                0x00000040: "纸张问题",
                0x00000080: "脱机",
                0x00000100: "IO活动",
                0x00000200: "忙",
                0x00000400: "打印中",
                0x00000800: "输出槽满",
                0x00001000: "不可用",
                0x00002000: "等待",
                0x00004000: "处理中",
                0x00008000: "正在初始化",
                0x00010000: "预热",
                0x00020000: "碳粉不足",
                0x00040000: "无碳粉",
                0x00080000: "页面异常",
                0x00100000: "用户干预",
                0x00200000: "内存不足",
                0x00400000: "门打开"
            }
            
            if status == 0:
                print("  [OK] 打印机状态: 正常")
            else:
                print("  [WARNING] 打印机状态异常:")
                for flag, msg in status_messages.items():
                    if status & flag:
                        print(f"    - {msg}")
            
            print()
            
            # 检查队列
            print("检查打印队列...")
            jobs = win32print.EnumJobs(handle, 0, -1, 1)
            
            if jobs:
                print(f"  队列中有 {len(jobs)} 个任务:")
                for job in jobs:
                    print(f"    - 任务ID: {job['JobId']}, 状态: {job['Status']}, 页数: {job['TotalPages']}")
            else:
                print("  [OK] 打印队列为空")
            
            win32print.ClosePrinter(handle)
            
        except Exception as e:
            print(f"  [ERROR] 无法检查打印机状态: {e}")
        
        print()
        print("="*70)
        print("诊断建议")
        print("="*70)
        print()
        
        if "重定向" in printer_name:
            print("[WARNING] 打印机名称包含'重定向'")
            print("  可能原因:")
            print("    1. 打印机通过网络重定向连接")
            print("    2. 打印机驱动配置为端口重定向")
            print()
            print("  建议:")
            print("    1. 检查打印机是否在线")
            print("    2. 检查网络连接")
            print("    3. 尝试打印测试页:")
            print("       - 控制面板 -> 设备和打印机")
            print("       - 右键打印机 -> 打印机属性 -> 打印测试页")
            print()
        
        print("其他检查项:")
        print("  1. 打印机是否开机")
        print("  2. 打印机是否有纸")
        print("  3. 打印机是否有错误灯闪烁")
        print("  4. 尝试使用网络打印 (IP地址)")
        print()
        
    except ImportError:
        print("[ERROR] 需要安装 pywin32")
        print("  运行: pip install pywin32")


def test_simple_zpl():
    """测试简单ZPL打印"""
    print("="*70)
    print("测试简单ZPL打印")
    print("="*70)
    print()
    
    # 简单的ZPL代码（纯英文）
    simple_zpl = """^XA
^FO50,50^A0N,50,50^FDTest Print^FS
^FO50,120^A0N,40,40^FDHello World^FS
^FO50,180^BCN,100,Y,N,N^FD123456^FS
^XZ"""
    
    print("测试ZPL代码:")
    print(simple_zpl)
    print()
    
    confirm = input("是否发送到ZT411打印机? (y/n): ").strip().lower()
    if confirm != 'y':
        print("已取消")
        return
    
    try:
        from src.core.printer import ZebraPrinter
        
        printer = ZebraPrinter(printer_name="ZT411")
        
        print("\n正在发送...")
        success = printer.print_label(simple_zpl)
        
        if success:
            print("[OK] 发送成功!")
            print("\n请检查打印机:")
            print("  - 是否有纸张输出")
            print("  - 是否有错误灯")
            print("  - 是否需要按打印机上的按钮")
        else:
            print("[ERROR] 发送失败!")
    
    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()


def test_network_print():
    """测试网络打印"""
    print("="*70)
    print("测试网络打印 (绕过Windows驱动)")
    print("="*70)
    print()
    
    ip = input("请输入ZT411的IP地址 (如 10.100.10.121): ").strip()
    if not ip:
        print("已取消")
        return
    
    port = input("端口 (默认9100): ").strip() or "9100"
    port = int(port)
    
    # 简单测试ZPL
    test_zpl = """^XA
^FO50,50^A0N,50,50^FDNetwork Test^FS
^FO50,120^A0N,40,40^FDDirect IP Print^FS
^XZ"""
    
    print(f"\n尝试连接到 {ip}:{port}...")
    
    try:
        import socket
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((ip, port))
        
        print("[OK] 连接成功!")
        
        print("发送ZPL代码...")
        sock.sendall(test_zpl.encode('utf-8'))
        sock.close()
        
        print("[OK] 数据已发送!")
        print("\n请检查打印机是否有输出")
        
    except socket.timeout:
        print(f"[ERROR] 连接超时 - 打印机可能不在线或IP错误")
    except ConnectionRefusedError:
        print(f"[ERROR] 连接被拒绝 - 端口{port}可能不正确")
    except Exception as e:
        print(f"[ERROR] 网络打印失败: {e}")


def main():
    """主菜单"""
    while True:
        print("\n" + "="*70)
        print("ZT411 打印诊断工具")
        print("="*70)
        print()
        print("选项:")
        print("  1. 检查打印机状态")
        print("  2. 测试简单ZPL打印 (纯英文)")
        print("  3. 测试网络打印 (绕过驱动)")
        print("  0. 退出")
        print()
        
        choice = input("请选择 (0-3): ").strip()
        
        if choice == '0':
            break
        elif choice == '1':
            check_printer_status()
        elif choice == '2':
            test_simple_zpl()
        elif choice == '3':
            test_network_print()
        else:
            print("无效选项")
        
        input("\n按回车继续...")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n已中断")

