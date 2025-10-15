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

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import ConfigManager, create_default_config
from core import LabelPrintMQTT


def print_banner():
    """打印服务启动横幅"""
    print("=" * 70)
    print(" " * 15 + "斑马打印机MQTT标签打印服务")
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


def main():
    """主函数"""
    try:
        # 打印横幅
        print_banner()
        
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
        
        # 获取MQTT和打印机配置
        mqtt_config = config_manager.get_mqtt_config()
        printer_config = config_manager.get_printer_config()
        
        # 创建并启动MQTT客户端
        try:
            client = LabelPrintMQTT(
                broker_host=mqtt_config.get('host', '127.0.0.1'),
                broker_port=mqtt_config.get('port', 1883),
                topic=mqtt_config.get('topic', 'zebra/print'),
                username=mqtt_config.get('username'),
                password=mqtt_config.get('password'),
                printer_config=printer_config
            )
            
            client.start()
            
        except KeyboardInterrupt:
            print("\n\n服务已停止")
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
    sys.exit(main())

