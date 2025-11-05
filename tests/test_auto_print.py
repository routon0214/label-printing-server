#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动打印测试（无需确认）
快速测试各种格式的打印功能
"""

import sys
import os
import json
import base64
import time

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

from src.config import ConfigManager


def test_label_print(client, topic):
    """测试标签打印"""
    print("\n【1/4】测试 ZPL 标签打印")
    print("-"*60)
    
    # 直接使用 ZPL 代码
    zpl_code = """^XA
^FO50,50^A0N,50,50^FDMQTT Test^FS
^FO50,120^A0N,30,30^FDLabel Print^FS
^FO50,160^A0N,25,25^FDTime: {time}^FS
^FO50,200^BCN,100,Y,N,N^FD123456789^FS
^XZ""".format(time=time.strftime("%H:%M:%S"))
    
    message = {
        "print_type": "label",
        "zpl_code": zpl_code
    }
    
    result = client.publish(topic, json.dumps(message))
    print(f"  ZPL 标签: {'✓ 已发送' if result.rc == 0 else '✗ 失败'}")
    time.sleep(1)
    return result.rc == 0


def test_pdf_print(client, topic):
    """测试 PDF 打印"""
    print("\n【2/4】测试 PDF 文档打印")
    print("-"*60)
    
    # 使用现有 PDF 文件或创建简单 PDF
    pdf_file = "tests/test_document_simple.pdf"
    
    if os.path.exists(pdf_file):
        with open(pdf_file, 'rb') as f:
            pdf_base64 = base64.b64encode(f.read()).decode('utf-8')
        
        message = {
            "print_type": "pdf",
            "pdf_data": pdf_base64
        }
        
        result = client.publish(topic, json.dumps(message))
        print(f"  PDF 文档: {'✓ 已发送' if result.rc == 0 else '✗ 失败'}")
        time.sleep(1)
        return result.rc == 0
    else:
        print(f"  ⚠ 未找到测试 PDF: {pdf_file}")
        return False


def test_txt_print(client, topic):
    """测试文本打印"""
    print("\n【3/4】测试 TXT 文本打印")
    print("-"*60)
    
    # 创建简单文本
    txt_content = f"""
MQTT 打印测试
============

类型: 文本文件
时间: {time.strftime("%Y-%m-%d %H:%M:%S")}

这是一个测试文本文件。
This is a test text file.
数字: 1234567890
"""
    
    txt_base64 = base64.b64encode(txt_content.encode('utf-8')).decode('utf-8')
    
    message = {
        "print_type": "pdf",  # 文本通过 PDF 打印机处理
        "pdf_data": txt_base64
    }
    
    result = client.publish(topic, json.dumps(message))
    print(f"  TXT 文本: {'✓ 已发送' if result.rc == 0 else '✗ 失败'}")
    time.sleep(1)
    return result.rc == 0


def test_receipt_print(client, topic):
    """测试小票打印"""
    print("\n【4/4】测试 ESC/POS 小票打印")
    print("-"*60)
    
    message = {
        "print_type": "receipt",
        "title": "MQTT 测试小票",
        "items": [
            {"name": "商品A", "price": 10.00, "qty": 2},
            {"name": "商品B", "price": 15.50, "qty": 1}
        ],
        "total": 35.50,
        "time": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    result = client.publish(topic, json.dumps(message))
    print(f"  ESC/POS 小票: {'✓ 已发送' if result.rc == 0 else '✗ 失败'}")
    time.sleep(1)
    return result.rc == 0


def main():
    """主函数"""
    print("="*60)
    print(" " * 15 + "MQTT 打印自动测试")
    print("="*60)
    
    # 加载配置
    try:
        config_manager = ConfigManager('config/printer_config.json')
        config = config_manager.load()
        mqtt_config = config.get('mqtt', {})
        broker_host = mqtt_config.get('host', '127.0.0.1')
        broker_port = mqtt_config.get('port', 1883)
        topic = mqtt_config.get('topic', 'zebra/print')
    except Exception as e:
        print(f"✗ 加载配置失败: {e}")
        broker_host = '127.0.0.1'
        broker_port = 1883
        topic = 'zebra/print'
    
    print(f"\nMQTT 服务器: {broker_host}:{broker_port}")
    print(f"主题: {topic}")
    print(f"\n⚠ 请确保打印服务已启动: python app.py\n")
    
    # 连接 MQTT
    try:
        import paho.mqtt.client as mqtt
        
        client = mqtt.Client()
        print("正在连接 MQTT...")
        client.connect(broker_host, broker_port, 60)
        print("✓ MQTT 连接成功\n")
        
        # 执行测试
        results = []
        results.append(("ZPL 标签", test_label_print(client, topic)))
        results.append(("PDF 文档", test_pdf_print(client, topic)))
        results.append(("TXT 文本", test_txt_print(client, topic)))
        results.append(("ESC/POS 小票", test_receipt_print(client, topic)))
        
        client.disconnect()
        
        # 显示结果
        print("\n" + "="*60)
        print("测试结果汇总")
        print("="*60)
        
        success_count = 0
        for test_name, success in results:
            status = "✓ 成功" if success else "✗ 失败"
            print(f"  {test_name:15s} {status}")
            if success:
                success_count += 1
        
        print("-"*60)
        print(f"总计: {success_count}/{len(results)} 通过")
        print("="*60)
        
        print("\n提示:")
        print("  1. 检查打印服务日志查看处理结果")
        print("  2. 确认打印机是否有输出")
        print("  3. 不同类型可能使用不同打印机")
        
        return 0 if success_count == len(results) else 1
        
    except ImportError:
        print("✗ 错误：需要安装 paho-mqtt")
        print("  运行: pip install paho-mqtt")
        return 1
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())

