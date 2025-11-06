#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多格式 MQTT 打印测试
测试各种文件格式：PDF、DOC、PPT、TXT、JPG、ZPL、ESC/POS
"""

import sys
import os
import json
import base64
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def create_test_files():
    """创建测试文件"""
    print("="*70)
    print("创建测试文件")
    print("="*70)
    
    test_files = {}
    
    # 1. 创建测试文本文件
    print("\n1. 创建 TXT 文件...")
    txt_content = """打印测试文档
=============

这是一个文本文件打印测试。

测试内容：
1. 中文字符测试
2. English character test
3. 数字测试：123456
4. 符号测试：!@#$%^&*()

打印时间：{time}
""".format(time=time.strftime("%Y-%m-%d %H:%M:%S"))
    
    txt_file = "test_document.txt"
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write(txt_content)
    test_files['txt'] = txt_file
    print(f"   [OK] 创建: {txt_file}")
    
    # 2. 创建测试 PDF 文件
    print("\n2. 创建 PDF 文件...")
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        
        pdf_file = "test_multi_format.pdf"
        c = canvas.Canvas(pdf_file, pagesize=A4)
        
        # 尝试注册中文字体
        try:
            pdfmetrics.registerFont(TTFont('SimSun', 'C:/Windows/Fonts/simsun.ttc'))
            c.setFont("SimSun", 16)
        except:
            c.setFont("Helvetica", 16)
        
        c.drawString(100, 750, "Multi-Format Print Test")
        c.setFont("Helvetica", 12)
        c.drawString(100, 720, "Document Type: PDF")
        c.drawString(100, 700, f"Created: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        c.drawString(100, 680, "This is a test PDF document for MQTT printing.")
        c.save()
        
        test_files['pdf'] = pdf_file
        print(f"   [OK] 创建: {pdf_file}")
    except ImportError:
        print("   [WARNING] reportlab 未安装，使用现有 PDF 文件")
        if os.path.exists("test_document_simple.pdf"):
            test_files['pdf'] = "test_document_simple.pdf"
            print(f"   [OK] 使用: test_document_simple.pdf")
    
    # 3. 创建 ZPL 标签代码
    print("\n3. 创建 ZPL 标签...")
    zpl_content = """^XA
^FO50,50^A0N,50,50^FDMQTT Print Test^FS
^FO50,120^A0N,30,30^FDType: ZPL Label^FS
^FO50,160^A0N,25,25^FDTime: {time}^FS
^FO50,200^BCN,100,Y,N,N^FD123456789^FS
^XZ""".format(time=time.strftime("%Y-%m-%d %H:%M:%S"))
    
    zpl_file = "test_label.zpl"
    with open(zpl_file, 'w', encoding='utf-8') as f:
        f.write(zpl_content)
    test_files['zpl'] = zpl_file
    print(f"   [OK] 创建: {zpl_file}")
    
    # 4. 创建 ESC/POS 小票
    print("\n4. 创建 ESC/POS 小票数据...")
    # ESC/POS 命令（这里只是示例数据结构）
    escpos_data = {
        "title": "MQTT 打印测试小票",
        "items": [
            {"name": "商品A", "price": 10.00, "qty": 2},
            {"name": "商品B", "price": 15.50, "qty": 1},
            {"name": "商品C", "price": 8.00, "qty": 3}
        ],
        "total": 59.50,
        "time": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    test_files['escpos'] = escpos_data
    print(f"   [OK] 创建: ESC/POS 数据结构")
    
    # 5. 创建测试图片
    print("\n5. 创建 JPG 图片...")
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        img = Image.new('RGB', (400, 300), color='white')
        draw = ImageDraw.Draw(img)
        
        # 绘制边框
        draw.rectangle([(10, 10), (390, 290)], outline='black', width=2)
        
        # 添加文本
        draw.text((50, 50), "MQTT Print Test", fill='black')
        draw.text((50, 100), "Type: JPG Image", fill='black')
        draw.text((50, 150), f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}", fill='black')
        
        jpg_file = "test_image.jpg"
        img.save(jpg_file, 'JPEG')
        test_files['jpg'] = jpg_file
        print(f"   [OK] 创建: {jpg_file}")
    except ImportError:
        print("   [WARNING] PIL/Pillow 未安装，跳过图片创建")
    
    # 6. DOC/DOCX（这里我们创建 RTF 格式，兼容性更好）
    print("\n6. 创建 DOC 文件（RTF格式）...")
    rtf_content = r"""{{\rtf1\ansi
{{\fonttbl {{\f0 Times New Roman;}}}}
{{\colortbl;\red0\green0\blue0;}}\f0\fs24
\b MQTT Print Test - DOC Format\b0\par
\par
Type: RTF/DOC Document\par
Created: {time}\par
\par
This is a test document in RTF format.\par
It should be printable on most printers.\par
}}""".format(time=time.strftime("%Y-%m-%d %H:%M:%S"))
    
    doc_file = "test_document.rtf"
    with open(doc_file, 'w', encoding='utf-8') as f:
        f.write(rtf_content)
    test_files['doc'] = doc_file
    print(f"   [OK] 创建: {doc_file}")
    
    print("\n" + "="*70)
    print(f"[OK] 共创建 {len(test_files)} 个测试文件")
    print("="*70)
    
    return test_files


def file_to_base64(file_path):
    """将文件转换为 base64 编码"""
    with open(file_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')


def send_mqtt_test(test_files, broker_host='127.0.0.1', broker_port=1883, topic='zebra/print'):
    """通过 MQTT 发送测试文件"""
    try:
        import paho.mqtt.client as mqtt
        
        print("\n" + "="*70)
        print("通过 MQTT 发送打印测试")
        print("="*70)
        print(f"MQTT 服务器: {broker_host}:{broker_port}")
        print(f"主题: {topic}")
        
        # 连接 MQTT
        client = mqtt.Client()
        client.connect(broker_host, broker_port, 60)
        
        results = []
        
        # 测试1: TXT 文本文件
        if 'txt' in test_files:
            print("\n【测试1】发送 TXT 文本文件")
            print("-"*70)
            txt_base64 = file_to_base64(test_files['txt'])
            message = {
                "print_type": "pdf",  # 文本文件也通过 PDF 打印机处理
                "pdf_data": txt_base64,
                "description": "TXT文本文件测试"
            }
            result = client.publish(topic, json.dumps(message))
            print(f"  消息ID: {result.mid}")
            print(f"  状态: {'[OK] 已发送' if result.rc == 0 else '[ERROR] 发送失败'}")
            results.append(('TXT', result.rc == 0))
            time.sleep(2)
        
        # 测试2: PDF 文档
        if 'pdf' in test_files:
            print("\n【测试2】发送 PDF 文档")
            print("-"*70)
            pdf_base64 = file_to_base64(test_files['pdf'])
            message = {
                "print_type": "pdf",
                "pdf_data": pdf_base64,
                "description": "PDF文档测试"
            }
            result = client.publish(topic, json.dumps(message))
            print(f"  消息ID: {result.mid}")
            print(f"  状态: {'[OK] 已发送' if result.rc == 0 else '[ERROR] 发送失败'}")
            results.append(('PDF', result.rc == 0))
            time.sleep(2)
        
        # 测试3: ZPL 标签
        if 'zpl' in test_files:
            print("\n【测试3】发送 ZPL 标签")
            print("-"*70)
            with open(test_files['zpl'], 'r', encoding='utf-8') as f:
                zpl_code = f.read()
            message = {
                "print_type": "label",
                "zpl_code": zpl_code,
                "description": "ZPL标签测试"
            }
            result = client.publish(topic, json.dumps(message))
            print(f"  消息ID: {result.mid}")
            print(f"  状态: {'[OK] 已发送' if result.rc == 0 else '[ERROR] 发送失败'}")
            results.append(('ZPL', result.rc == 0))
            time.sleep(2)
        
        # 测试4: ESC/POS 小票
        if 'escpos' in test_files:
            print("\n【测试4】发送 ESC/POS 小票")
            print("-"*70)
            message = {
                "print_type": "receipt",
                "title": test_files['escpos']['title'],
                "items": test_files['escpos']['items'],
                "total": test_files['escpos']['total'],
                "description": "ESC/POS小票测试"
            }
            result = client.publish(topic, json.dumps(message))
            print(f"  消息ID: {result.mid}")
            print(f"  状态: {'[OK] 已发送' if result.rc == 0 else '[ERROR] 发送失败'}")
            results.append(('ESC/POS', result.rc == 0))
            time.sleep(2)
        
        # 测试5: JPG 图片（转换为 PDF 后打印）
        if 'jpg' in test_files:
            print("\n【测试5】发送 JPG 图片")
            print("-"*70)
            jpg_base64 = file_to_base64(test_files['jpg'])
            message = {
                "print_type": "pdf",
                "pdf_data": jpg_base64,  # 图片也可以通过 base64 发送
                "description": "JPG图片测试"
            }
            result = client.publish(topic, json.dumps(message))
            print(f"  消息ID: {result.mid}")
            print(f"  状态: {'[OK] 已发送' if result.rc == 0 else '[ERROR] 发送失败'}")
            results.append(('JPG', result.rc == 0))
            time.sleep(2)
        
        # 测试6: DOC/RTF 文档
        if 'doc' in test_files:
            print("\n【测试6】发送 DOC/RTF 文档")
            print("-"*70)
            doc_base64 = file_to_base64(test_files['doc'])
            message = {
                "print_type": "pdf",
                "pdf_data": doc_base64,
                "description": "DOC/RTF文档测试"
            }
            result = client.publish(topic, json.dumps(message))
            print(f"  消息ID: {result.mid}")
            print(f"  状态: {'[OK] 已发送' if result.rc == 0 else '[ERROR] 发送失败'}")
            results.append(('DOC', result.rc == 0))
            time.sleep(2)
        
        client.disconnect()
        
        # 显示测试结果
        print("\n" + "="*70)
        print("测试结果汇总")
        print("="*70)
        for format_type, success in results:
            status = "[OK] 已发送" if success else "[ERROR] 失败"
            print(f"  {format_type:12s} {status}")
        
        print("\n说明:")
        print("  1. 消息已发送到 MQTT 服务器")
        print("  2. 请查看打印服务端日志确认打印结果")
        print("  3. 检查打印机是否有输出")
        print("="*70)
        
        return all(success for _, success in results)
        
    except ImportError:
        print("[ERROR] 错误：需要安装 paho-mqtt")
        print("  运行: pip install paho-mqtt")
        return False
    except Exception as e:
        print(f"[ERROR] 发送失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("\n" + "="*70)
    print(" " * 15 + "多格式 MQTT 打印测试")
    print("="*70)
    
    # 加载配置
    try:
        from src.config import ConfigManager
        config_manager = ConfigManager('config/printer_config.json')
        config = config_manager.load()
        mqtt_config = config.get('mqtt', {})
        broker_host = mqtt_config.get('host', '127.0.0.1')
        broker_port = mqtt_config.get('port', 1883)
        topic = mqtt_config.get('topic', 'zebra/print')
    except:
        broker_host = '127.0.0.1'
        broker_port = 1883
        topic = 'zebra/print'
    
    print(f"\n目标服务器: {broker_host}:{broker_port}")
    print(f"MQTT 主题: {topic}")
    
    # 创建测试文件
    test_files = create_test_files()
    
    # 确认发送
    print("\n" + "="*70)
    print("准备发送测试")
    print("="*70)
    print(f"\n将创建的测试文件通过 MQTT 发送到打印服务器")
    print(f"请确保打印服务已启动: python app.py")
    print()

    
    # 发送测试
    success = send_mqtt_test(test_files, broker_host, broker_port, topic)
    
    print("\n" + "="*70)
    if success:
        print("[OK] 测试完成")
        print("\n后续步骤:")
        print("  1. 检查打印服务端日志输出")
        print("  2. 确认各个打印机是否有输出")
        print("  3. 验证打印内容是否正确")
    else:
        print("[ERROR] 测试失败，请检查错误信息")
    print("="*70)
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())

