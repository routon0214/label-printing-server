#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块
提供配置文件加载和默认配置生成功能
"""

import json
import os
import platform


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file='config/printer_config.json'):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径
        """
        self.config_file = config_file
        self.config = None
    
    def load(self):
        """
        加载配置文件
        
        Returns:
            dict: 配置字典
        """
        self.config = load_config(self.config_file)
        return self.config
    
    def get(self, key, default=None):
        """
        获取配置项
        
        Args:
            key: 配置键
            default: 默认值
            
        Returns:
            配置值
        """
        if self.config is None:
            self.load()
        return self.config.get(key, default)
    
    def get_mqtt_config(self):
        """获取MQTT配置"""
        if self.config is None:
            self.load()
        return self.config.get('mqtt', {})
    
    def get_printer_config(self):
        """获取打印机配置（单打印机，兼容旧版）"""
        if self.config is None:
            self.load()
        return self.config.get('printer', {})
    
    def get_printers_config(self):
        """获取多打印机配置（新版）"""
        if self.config is None:
            self.load()
        return self.config.get('printers', [])


def load_config(config_file='../config/printer_config.json'):
    """
    加载配置文件
    
    Args:
        config_file: 配置文件路径
        
    Returns:
        dict: 配置字典
    """
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"未找到配置文件: {config_file}")
        print("使用默认配置...")
        return get_default_config()
    except Exception as e:
        print(f"加载配置失败: {e}")
        return get_default_config()


def get_default_config():
    """
    获取默认配置
    
    Returns:
        dict: 默认配置字典
    """
    return {
        "mqtt": {
            "host": "127.0.0.1",
            "port": 1883,
            "topic": "zebra/print",
            "username": None,
            "password": None
        },
        "printer": {
            "name": None,
            "ip": None,
            "port": 9100,
            "device": None
        }
    }


def create_default_config(config_file='config/printer_config.json'):
    """
    创建默认配置文件（跨平台）
    
    Args:
        config_file: 配置文件路径
    """
    system = platform.system()
    
    config = {
        "mqtt": {
            "host": "127.0.0.1",
            "port": 1883,
            "topic": "zebra/print",
            "username": None,
            "password": None
        },
        "printer": {
            "name": None,
            "ip": None,
            "port": 9100,
            "device": None,
            "_comment": {
                "name": "打印机名称 (Windows/CUPS)",
                "ip": "打印机IP地址（网络打印，所有平台通用）",
                "port": "网络打印端口（默认9100）",
                "device": "设备路径 (Linux USB，如/dev/usb/lp0)",
                "说明": "配置其中一项即可，优先级: ip > name > device > 自动检测"
            }
        }
    }
    
    # 添加平台特定的示例
    if system == 'Windows':
        config["_examples"] = {
            "Windows USB": {"printer": {"name": "ZDesigner ZT411-300dpi"}},
            "网络打印": {"printer": {"ip": "192.168.1.100", "port": 9100}}
        }
    elif system == 'Linux':
        config["_examples"] = {
            "CUPS": {"printer": {"name": "Zebra-ZT411"}},
            "USB设备": {"printer": {"device": "/dev/usb/lp0"}},
            "网络打印": {"printer": {"ip": "192.168.1.100", "port": 9100}}
        }
    
    # 确保目录存在
    os.makedirs(os.path.dirname(config_file), exist_ok=True)
    
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    print(f"已创建默认配置文件: {config_file} (平台: {system})")

