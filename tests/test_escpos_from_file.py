#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从文件读取内容并发送ESC/POS打印测试
使用 data/print_text.txt 文件内容
"""

import json
import sys
import os

# 添加项目根目录和src目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

from src.config import ConfigManager
import paho.mqtt.client as mqtt


def get_mqtt_config():
    """从配置文件获取MQTT设置"""
    config_manager = ConfigManager('config/printer_config.json')
    config = config_manager.load()
    mqtt_config = config_manager.get_mqtt_config()
    return {
        'host': mqtt_config.get('host', '127.0.0.1'),
        'port': mqtt_config.get(1883, 1883),
        'topic': mqtt_config.get('topic', 'zebra/print'),
        'username': mqtt_config.get('username'),
        'password': mqtt_config.get('password')
    }


def read_print_text_file(file_path='data/print_text.txt'):
    """读取打印文本文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        return content
    except FileNotFoundError:
        print(f"错误: 文件不存在 {file_path}")
        return None
    except Exception as e:
        print(f"错误: 读取文件失败 {e}")
        return None


def parse_print_commands(text):
    """
    解析打印命令文本，提取信息
    
    Args:
        text: 打印命令文本
        
    Returns:
        dict: 解析后的打印数据
    """ 
    # 提取TEXT命令中的文本内容
    text_lines = []
    qrcode_data = None
    
    # 解析TEXT命令: TEXT 20,10,"TSS24.BF2",0,1,1,"容器类型"
    import re
    text_pattern = r'TEXT\s+\d+,\d+,"[^"]+",\d+,\d+,\d+,"([^"]+)"'
    text_matches = re.findall(text_pattern, text)
    if text_matches:
        text_lines = text_matches
    
    # 解析QRCODE命令: QRCODE 20,60,L,10,A,0,M2,S6,"ECKQ"
    qrcode_pattern = r'QRCODE\s+\d+,\d+,[^,]+,\d+,[^,]+,\d+,[^,]+,[^,]+,"([^"]+)"'
    qrcode_match = re.search(qrcode_pattern, text)
    if qrcode_match:
        qrcode_data = qrcode_match.group(1)
    
    return {
        'text_lines': text_lines,
        'qrcode': qrcode_data
    }


def create_escpos_receipt_data(text_content):
    """
    将文本内容转换为ESC/POS收据格式
    
    Args:
        text_content: 原始文本内容
        
    Returns:
        dict: ESC/POS打印数据
    """
    # 解析文本内容
    parsed = parse_print_commands(text_content)
    
    # 构建商品列表（将文本行转换为商品项）
    items = []
    title = parsed['text_lines'][0] if parsed['text_lines'] else "打印任务"
    
    # 将文本行转换为商品项
    for i, line in enumerate(parsed['text_lines'][1:], 1):
        # 尝试解析行内容
        if ':' in line:
            # 格式: "编号:ECKQ" -> 作为商品项
            parts = line.split(':', 1)
            if len(parts) == 2:
                items.append({
                    "name": parts[0].strip(),
                    "qty": 1,
                    "price": 0.0
                })
        else:
            # 普通文本行
            items.append({
                "name": line,
                "qty": 1,
                "price": 0.0
            })
    
    # 如果没有商品项，使用文本行
    if not items and parsed['text_lines']:
        for line in parsed['text_lines'][1:]:
            items.append({
                "name": line,
                "qty": 1,
                "price": 0.0
            })
    
    # 构建ESC/POS打印数据
    receipt_data = {
        "print_type": "escpos",  # ESC/POS打印类型
        "title": title,
        "items": items,
        "total": 0.0,
        "footer": f"二维码: {parsed['qrcode']}" if parsed['qrcode'] else "打印完成",
        "qrcode": parsed['qrcode']  # 如果有二维码，也可以包含
    }
    
    return receipt_data


def test_escpos_from_file():
    """测试从文件读取并发送ESC/POS打印"""
    print("=" * 70)
    print(" " * 20 + "ESC/POS文件打印测试")
    print("=" * 70)
    
    # 读取文件
    file_path = 'data/print_text.txt'
    print(f"\n读取文件: {file_path}")
    text_content = read_print_text_file(file_path)
    
    if not text_content:
        print("[ERROR] 无法读取文件")
        return False
    
    print(f"[OK] 文件内容 ({len(text_content)} 字符):")
    print("-" * 70)
    print(text_content)
    print("-" * 70)
    
    # 解析并转换为ESC/POS格式
    print("\n解析文件内容...")
    receipt_data = create_escpos_receipt_data(text_content)
    
    print("\n转换后的ESC/POS数据:")
    print(json.dumps(receipt_data, ensure_ascii=False, indent=2))
    
    # 获取MQTT配置
    mqtt_cfg = get_mqtt_config()
    print(f"\nMQTT服务器: {mqtt_cfg['host']}:{mqtt_cfg['port']}")
    print(f"MQTT主题: {mqtt_cfg['topic']}")
    
    # 发送MQTT消息
    print("\n正在发送打印任务...")
    try:
        client = mqtt.Client()
        if mqtt_cfg['username'] and mqtt_cfg['password']:
            client.username_pw_set(mqtt_cfg['username'], mqtt_cfg['password'])
        
        client.connect(mqtt_cfg['host'], mqtt_cfg['port'], 60)
        result = client.publish(mqtt_cfg['topic'], json.dumps(receipt_data, ensure_ascii=False))
        client.disconnect()
        
        if result.rc == 0:
            print("[OK] 打印任务发送成功")
            print("\n提示: 请确保打印服务已启动，并且配置了ESC/POS打印机")
            return True
        else:
            print(f"[ERROR] 发送失败，错误码: {result.rc}")
            return False
            
    except Exception as e:
        print(f"[ERROR] 发送失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_raw_escpos():
    """测试发送原始文本内容（作为文本打印）"""
    print("\n" + "=" * 70)
    print(" " * 20 + "原始文本打印测试")
    print("=" * 70)
    
    # 读取文件
    file_path = 'data/print_text.txt'
    text_content = read_print_text_file(file_path)
    
    if not text_content:
        return False
    
    # 创建原始文本打印数据
    raw_data = {
        "print_type": "escpos",
        "raw_text": text_content,  # 直接发送原始文本
        "encoding": "utf-8"
    }
    
    print("\n发送原始文本内容...")
    print(f"文本长度: {len(text_content)} 字符")
    
    # 获取MQTT配置
    mqtt_cfg = get_mqtt_config()
    
    # 发送MQTT消息
    try:
        client = mqtt.Client()
        if mqtt_cfg['username'] and mqtt_cfg['password']:
            client.username_pw_set(mqtt_cfg['username'], mqtt_cfg['password'])
        
        client.connect(mqtt_cfg['host'], mqtt_cfg['port'], 60)
        result = client.publish(mqtt_cfg['topic'], json.dumps(raw_data, ensure_ascii=False))
        client.disconnect()
        
        if result.rc == 0:
            print("[OK] 原始文本打印任务发送成功")
            return True
        else:
            print(f"[ERROR] 发送失败，错误码: {result.rc}")
            return False
            
    except Exception as e:
        print(f"[ERROR] 发送失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("\n" + "=" * 70)
    print(" " * 15 + "ESC/POS文件打印测试工具")
    print("=" * 70)
    
    print("\n选择测试方式:")
    print("  [1] 解析文件内容并转换为ESC/POS格式（推荐）")
    print("  [2] 发送原始文本内容")
    print("  [0] 退出")
    
    try:
        choice = input("\n请选择 (0-2, 默认1): ").strip()
        if not choice:
            choice = '1'
        choice = int(choice)
        
        if choice == 0:
            print("退出")
            return
        elif choice == 1:
            test_escpos_from_file()
        elif choice == 2:
            test_raw_escpos()
        else:
            print("无效选择")
            
    except ValueError:
        print("请输入有效的数字")
    except KeyboardInterrupt:
        print("\n\n用户取消")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

