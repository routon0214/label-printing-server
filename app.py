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
    """主函数 - 直接启动Web服务"""
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
        
        # 获取Web认证配置
        web_config = config.get('web', {})
        username = web_config.get('username', 'admin')
        password = web_config.get('password', 'admin123')
        
        print("\n" + "=" * 70)
        print(" " * 20 + "启动Web服务")
        print("=" * 70)
        print(f"Web访问地址: http://127.0.0.1:5000")
        print(f"登录用户名: {username}")
        print(f"登录密码: {password}")
        print("提示: Web服务将同时启动MQTT接收功能")
        print("=" * 70)
        print("\n按 Ctrl+C 停止服务\n")
        
        # 导入并启动Web应用
        try:
            import web_app
            web_app.config_manager = config_manager
            import uvicorn
            uvicorn.run(web_app.app, host="0.0.0.0", port=8000, log_level="info")
            return 0
        except ImportError as e:
            print("\n[ERROR] 错误: 无法导入web_app模块")
            print(f"详细错误: {e}")
            print("请确保已安装所有依赖: pip install -r requirements.txt")
            wait_for_user_exit()
            return 1
        except KeyboardInterrupt:
            print("\n\nWeb服务已停止")
            return 0
        except Exception as e:
            print(f"\n[ERROR] Web服务启动失败: {e}")
            import traceback
            traceback.print_exc()
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

