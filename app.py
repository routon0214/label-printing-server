#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
斑马打印机MQTT标签打印服务 - 主入口

功能：
- 接收MQTT消息，生成并打印支持中文的标签
- 支持平台：Windows、Linux (AMD64/ARM)
- 支持多种打印方式：USB、网络、CUPS

作者：Label Printing Server
日期：2025-10-15
"""

import sys
import os
import platform
import threading
import time

# Windows 控制台编码修复
if sys.platform == 'win32':
    import io
    try:
        if sys.stdout.encoding != 'utf-8':
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        if sys.stderr.encoding != 'utf-8':
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass

# 添加项目根目录和src目录到路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

from src.config import ConfigManager, create_default_config
from src.core import LabelPrintMQTT
from src.utils.printer_setup import printer_setup_wizard


def print_banner():
    """打印服务启动横幅"""
    print("=" * 70)
    print(" " * 15 + "打印机MQTT标签打印服务")
    print("=" * 70)
    print(f"系统: {platform.system()} {platform.machine()}")
    print(f"Python: {sys.version.split()[0]}")
    print("=" * 70)
    print()


def wait_for_user_exit():
    """等待用户按键退出"""
    try:
        input("\n按回车键退出...")
    except:
        pass


def ensure_directories():
    """确保所有必要的目录存在"""
    directories = [
        'config',
        'data/logs',
        'data/failed_labels'
    ]
    
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
        except Exception as e:
            print(f"警告：无法创建目录 {directory}: {e}")


def main():
    """主函数"""
    try:
        # 打印横幅
        print_banner()
        
        # 确保必要的目录存在
        ensure_directories()
        
        # 检查配置文件是否存在
        config_file = 'config/printer_config.json'
        if not os.path.exists(config_file):
            print(f"配置文件不存在，正在创建默认配置...")
            create_default_config(config_file)
            print()
        
        # 加载配置
        config_manager = ConfigManager(config_file)
        config = config_manager.load()
        
        if not config:
            print("\n" + "=" * 70)
            print("错误：配置加载失败")
            print("=" * 70)
            wait_for_user_exit()
            return 1
        
        # 检查是否有打印机配置
        printers_config = config.get('printers', [])
        printer_config = config.get('printer')
        
        # 显示启动菜单
        print("\n" + "=" * 70)
        print(" " * 20 + "启动选项")
        print("=" * 70)
        print("  [1] 启动服务 (默认)")
        print("  [2] 配置打印机")
        print("  [0] 退出")
        print("=" * 70)
        
        # 如果没有配置打印机，特别提示
        if not printers_config and not printer_config:
            print("\n⚠ 未检测到打印机配置，建议先配置打印机")
        
        # 倒计时自动启动
        print("\n将在 3 秒后自动启动服务...")
        print("(按回车键中断并选择选项)")
        
        user_input = None
        
        # 使用线程实现倒计时和输入检测
        def countdown_with_input():
            """倒计时，同时检测用户输入"""
            nonlocal user_input
            for i in range(3, 0, -1):
                if user_input is not None:
                    return
                print(f"\r将在 {i} 秒后自动启动... ", end='', flush=True)
                time.sleep(1)
            if user_input is None:
                print("\r" + " " * 40 + "\r", end='')  # 清除倒计时行
                print("已自动启动服务")
        
        def get_input():
            """获取用户输入"""
            nonlocal user_input
            try:
                user_input = input("\r请输入选择 (0-2, 默认1): ").strip()
            except:
                pass
        
        # 启动倒计时线程
        timer_thread = threading.Thread(target=countdown_with_input, daemon=True)
        timer_thread.start()
        
        # 启动输入线程
        input_thread = threading.Thread(target=get_input, daemon=True)
        input_thread.start()
        
        # 等待倒计时完成或用户输入
        timer_thread.join(timeout=3.5)
        
        # 如果用户输入了，使用用户输入
        if user_input is not None:
            if not user_input:
                choice = 1  # 默认启动
            else:
                try:
                    choice = int(user_input)
                except ValueError:
                    choice = 1  # 无效输入，默认启动
        else:
            choice = 1  # 自动启动
        
        if choice == 0:
            print("退出程序")
            return 0
        elif choice == 1:
            # 检查是否有配置，没有则提示
            if not printers_config and not printer_config:
                print("\n⚠ 警告: 未配置打印机，服务启动后可能无法打印")
                try:
                    confirm = input("是否继续启动? (y/n, 默认y): ").strip().lower()
                    if confirm == 'n':
                        print("退出程序")
                        return 0
                except:
                    pass  # 自动启动时继续
            # 继续启动服务
        elif choice == 2:
            printer_setup_wizard(config_file)
            # 重新加载配置
            config = config_manager.load()
            printers_config = config.get('printers', [])
            printer_config = config.get('printer')
            print("\n配置完成！")
            # 配置完成后询问是否启动服务
            try:
                start = input("是否立即启动服务? (y/n, 默认y): ").strip().lower()
                if start == 'n':
                    print("退出程序")
                    return 0
            except:
                pass  # 自动启动
        else:
            choice = 1  # 无效选择，默认启动服务
        
        # 获取MQTT和打印机配置
        mqtt_config = config_manager.get_mqtt_config()
        
        # 创建并启动MQTT客户端
        try:
            client = LabelPrintMQTT(
                broker_host=mqtt_config.get('host', '127.0.0.1'),
                broker_port=mqtt_config.get('port', 1883),
                topic=mqtt_config.get('topic', 'zebra/print'),
                username=mqtt_config.get('username'),
                password=mqtt_config.get('password'),
                protocol=mqtt_config.get('protocol'),  # 传递协议信息
                url=mqtt_config.get('url'),  # 传递原始URL
                printer_config=printer_config,      # 兼容旧版
                printers_config=printers_config     # 新版多打印机
            )
            
            # 如果配置了URL，显示连接信息
            if mqtt_config.get('url'):
                print(f"MQTT连接URL: {mqtt_config.get('url')}")
            
            client.start()
            
        except KeyboardInterrupt:
            print("\n\n服务已停止")
            # Ctrl+C时不等待，直接返回
            return 0
        except Exception as e:
            print("\n" + "=" * 70)
            print(f"错误: {e}")
            print("=" * 70)
            import traceback
            traceback.print_exc()
            print("\n提示：")
            print("  1. 检查MQTT服务器是否运行")
            print("  2. 检查打印机配置是否正确")
            print("  3. 查看上方的详细错误信息")
            wait_for_user_exit()
            return 1
    
    except Exception as e:
        # 捕获所有未预期的异常
        print("\n" + "=" * 70)
        print(f"严重错误: {e}")
        print("=" * 70)
        import traceback
        traceback.print_exc()
        wait_for_user_exit()
        return 1


if __name__ == "__main__":
    # 在最外层添加异常捕获，确保导入错误等也能被捕获
    try:
        exit_code = main()
        # 如果是正常退出（返回0），也等待确认
        if exit_code == 0:
            print("\n程序正常退出")
        wait_for_user_exit()
        sys.exit(exit_code if exit_code else 0)
    except SystemExit as e:
        # SystemExit也要等待
        if e.code != 0:
            print(f"\n程序退出，代码: {e.code}")
            wait_for_user_exit()
        raise
    except KeyboardInterrupt:
        print("\n\n用户中断程序")
        wait_for_user_exit()
        sys.exit(0)
    except Exception as e:
        # 捕获所有其他异常（包括导入错误等）
        print("\n" + "=" * 70)
        print(f"启动失败: {e}")
        print("=" * 70)
        import traceback
        traceback.print_exc()
        print("\n可能的原因:")
        print("  1. 缺少必要的Python库")
        print("  2. 配置文件错误")
        print("  3. 文件权限问题")
        print("  4. MQTT服务器连接问题")
        wait_for_user_exit()
        sys.exit(1)

