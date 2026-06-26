#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块
提供配置文件加载和默认配置生成功能
"""

import json
import os
import platform
from urllib.parse import urlparse


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
            dict: 配置字典1
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
        """
        获取MQTT配置
        支持URL格式和分离格式，自动解析
        如果设置了platform_code且topic为空，会自动生成主题：tpm-iot-protocol/platform/{code}/devicePrintJson
        
        Returns:
            dict: MQTT配置字典，包含host、port、topic、username、password等
        """
        if self.config is None:
            self.load()
        
        mqtt_config = self.config.get('mqtt', {})
        
        # 检查是否有platform_code，如果topic为空则自动生成主题
        platform_code = self.config.get('platform_code')
        if platform_code and platform_code.strip():
            # 只有当topic为空或未设置时，才使用自动生成的主题
            if not mqtt_config.get('topic') or not mqtt_config.get('topic').strip():
                auto_topic = f"tpm-iot-protocol/platform/{platform_code.strip()}/devicePrintJson"
                mqtt_config['topic'] = auto_topic
        
        # 如果配置中有url字段，优先使用URL格式
        if 'url' in mqtt_config and mqtt_config['url']:
            result = parse_mqtt_url(mqtt_config['url'], mqtt_config)
            # 如果设置了platform_code且topic为空，使用自动生成的主题
            if platform_code and platform_code.strip():
                if not result.get('topic') or not result.get('topic').strip():
                    auto_topic = f"tpm-iot-protocol/platform/{platform_code.strip()}/devicePrintJson"
                    result['topic'] = auto_topic
            return result
        
        # 否则使用分离格式（向后兼容）
        return mqtt_config
    
    def save(self, config_data=None):
        """
        保存配置到文件
        
        Args:
            config_data: 要保存的配置数据，为None则保存当前内存中的配置
        """
        if config_data is not None:
            self.config = config_data
        if self.config is None:
            raise ValueError("没有配置数据可保存")
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)

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


def parse_mqtt_url(url, extra_config=None):
    """
    解析MQTT URL配置
    
    支持的URL格式（完整协议支持）：
    - mqtt://127.0.0.1:1883               # 标准MQTT (TCP)，默认端口1883
    - tcp://10.100.10.121:1883            # TCP连接（等同于mqtt://）
    - ws://10.100.10.121:8083/mqtt        # WebSocket，默认端口80，路径/mqtt
    - wss://10.100.10.121/mqtt            # WebSocket Secure (HTTPS)，默认端口443，路径/mqtt
    - mqtts://example.com:8883            # MQTT over SSL/TLS (TCP + SSL)，默认端口8883
    
    注意：
    - URL中的路径部分（如 /mqtt）会保留，用于WebSocket路径配置
    - topic需要单独配置，不从URL路径提取
    - 如果URL中未指定端口，会根据协议使用默认端口
    
    Args:
        url: MQTT连接URL
        extra_config: 额外的配置（如username、password、topic）
        
    Returns:
        dict: 解析后的配置字典
    """
    if not url:
        return {}
    
    extra_config = extra_config or {}
    
    try:
        parsed = urlparse(url)
        
        # 提取并规范化协议
        scheme = parsed.scheme.lower()
        
        # 协议映射：将不同协议映射到标准协议
        protocol_map = {
            'mqtt': 'mqtt',      # 标准MQTT (TCP)
            'tcp': 'mqtt',       # TCP等同于MQTT
            'mqtts': 'mqtts',    # MQTT over SSL/TLS (TCP + SSL)
            'ssl': 'mqtts',      # SSL等同于MQTTs
            'ws': 'ws',          # WebSocket (HTTP)
            'wss': 'wss'         # WebSocket Secure (HTTPS)
        }
        
        protocol = protocol_map.get(scheme, 'mqtt')  # 默认使用mqtt
        
        # 提取主机和端口
        host = parsed.hostname or '127.0.0.1'
        port = parsed.port
        
        # 如果没有指定端口，根据协议设置默认端口
        if port is None:
            if protocol == 'ws':
                port = 80  # WebSocket默认端口（HTTP）
            elif protocol == 'wss':
                port = 443  # WebSocket安全默认端口（HTTPS）
            elif protocol == 'mqtts':
                port = 8883  # SSL MQTT默认端口
            else:  # mqtt, tcp
                port = 1883  # 标准MQTT默认端口
        
        # 提取用户名和密码（如果URL中包含）
        username = parsed.username or extra_config.get('username')
        password = parsed.password or extra_config.get('password')
        
        # 构建配置字典
        config = {
            'host': host,
            'port': port,
            'protocol': protocol,
            'url': url  # 保留原始URL
        }
        
        # topic作为独立配置项，不从URL路径提取
        # 优先使用配置中的topic，如果没有则使用默认值
        topic = extra_config.get('topic', 'zebra/print')
        config['topic'] = topic
        
        if username:
            config['username'] = username
        if password:
            config['password'] = password
        
        # 合并额外配置（优先级低于URL解析的结果）
        for key in ['username', 'password', 'topic', 'client_id']:
            if key in extra_config and key not in config:
                config[key] = extra_config[key]
        
        # client_id如果没有配置，设置为None（会在MQTT客户端中自动生成）
        if 'client_id' not in config:
            config['client_id'] = None
        
        return config
        
    except Exception as e:
        print(f"警告：解析MQTT URL失败: {e}")
        print(f"URL: {url}")
        print("使用默认配置...")
        return {
            'host': '127.0.0.1',
            'port': 1883,
            'topic': 'zebra/print',
            'url': url
        }


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
            "url": "mqtt://127.0.0.1:1883",
            "topic": "zebra/print",
            "username": None,
            "password": None,
            "_comment": {
                "url": "MQTT连接URL，格式: protocol://host:port（不包含topic）",
                "topic": "MQTT订阅主题，独立配置",
                "示例": [
                    "mqtt://127.0.0.1:1883",
                    "ws://10.100.10.121:8083",
                    "mqtts://example.com:8883"
                ],
                "说明": "也可以使用分离格式：host、port、topic分别配置（向后兼容）"
            }
        },
        "web": {
            "username": "admin",
            "password": "admin123",
            "_comment": {
                "username": "Web界面登录用户名",
                "password": "Web界面登录密码",
                "说明": "建议修改默认密码以确保安全"
            }
        },
        "printer": {
            "name": None,
            "ip": None,
            "port": 9100,
            "device": None,
            "language": "zpl",
            "_comment": {
                "name": "打印机名称 (Windows/CUPS)",
                "ip": "打印机IP地址（网络打印，所有平台通用）",
                "port": "网络打印端口（默认9100）",
                "device": "设备路径 (Linux USB，如/dev/usb/lp0)",
                "language": "打印机语言: zpl(直通) | tspl(自动转换) | null=自动检测",
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

