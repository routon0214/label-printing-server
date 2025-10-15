#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF打印测试脚本
测试通过MQTT发送PDF打印任务
"""

import json
import base64
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import load_config


def get_mqtt_config():
    """从配置文件获取MQTT设置"""
    config = load_config()
    mqtt_config = config.get('mqtt', {})
    return {
        'host': mqtt_config.get('host', '127.0.0.1'),
        'port': mqtt_config.get('port', 1883),
        'topic': mqtt_config.get('topic', 'zebra/print'),
        'username': mqtt_config.get('username'),
        'password': mqtt_config.get('password')
    }


def create_test_pdf():
    """创建一个真实的PDF文件"""
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import inch
        
        pdf_file = "test_document.pdf"
        c = canvas.Canvas(pdf_file, pagesize=A4)
        width, height = A4
        
        # 添加标题
        c.setFont("Helvetica-Bold", 20)
        c.drawString(100, height - 100, "MQTT Print Server - Test Document")
        
        # 添加副标题
        c.setFont("Helvetica", 14)
        c.drawString(100, height - 130, "PDF Document Printing Test")
        c.drawString(100, height - 150, "Generated: 2025-10-15")
        
        # 绘制分隔线
        c.line(100, height - 160, width - 100, height - 160)
        
        # 添加测试内容
        c.setFont("Helvetica", 11)
        y = height - 200
        
        c.drawString(100, y, "Document Information:")
        y -= 25
        c.drawString(120, y, "• File Type: PDF")
        y -= 20
        c.drawString(120, y, "• Encoding: Base64 for MQTT transmission")
        y -= 20
        c.drawString(120, y, "• Protocol: MQTT")
        y -= 20
        c.drawString(120, y, "• Test Date: 2025-10-15")
        
        y -= 40
        c.drawString(100, y, "Test Content:")
        y -= 25
        
        # 添加多行测试文本
        for i in range(1, 21):
            c.drawString(120, y, f"Line {i}: This is test content for PDF printing via MQTT server")
            y -= 18
            if y < 100:  # 换页
                c.showPage()
                c.setFont("Helvetica", 11)
                y = height - 100
        
        # 添加页脚
        c.setFont("Helvetica-Oblique", 9)
        c.drawString(100, 50, "MQTT Print Server - Supports Label and Document Printing")
        
        c.save()
        
        # 检查文件大小
        file_size = os.path.getsize(pdf_file)
        print(f"✓ 真实PDF文件已创建: {pdf_file}")
        print(f"  文件大小: {file_size:,} 字节 ({file_size/1024:.2f} KB)")
        return pdf_file
        
    except ImportError:
        print("警告: 未安装reportlab库")
        print("提示: pip install reportlab")
        print("\n使用备用方案：创建简单PDF...")
        
        # 手动创建一个最简单的PDF
        pdf_file = "test_document_simple.pdf"
        
        # 这是一个最小的PDF文件内容
        pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
/Resources <<
/Font <<
/F1 <<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
>>
>>
>>
endobj
4 0 obj
<<
/Length 100
>>
stream
BT
/F1 24 Tf
100 700 Td
(Test PDF Document) Tj
ET
BT
/F1 12 Tf
100 650 Td
(MQTT Print Server Test) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000317 00000 n
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
467
%%EOF
"""
        
        with open(pdf_file, 'wb') as f:
            f.write(pdf_content)
        
        file_size = os.path.getsize(pdf_file)
        print(f"✓ 简单PDF文件已创建: {pdf_file}")
        print(f"  文件大小: {file_size:,} 字节")
        return pdf_file


def encode_file_to_base64(file_path):
    """将文件编码为base64"""
    with open(file_path, 'rb') as f:
        file_data = f.read()
    
    # 显示文件信息
    print(f"  原始文件大小: {len(file_data):,} 字节")
    
    base64_data = base64.b64encode(file_data).decode('utf-8')
    print(f"  Base64编码后: {len(base64_data):,} 字符")
    print(f"  大小增加: {(len(base64_data) - len(file_data)) / len(file_data) * 100:.1f}%")
    
    return base64_data


def test_pdf_print_with_file_path():
    """测试方式1: 使用文件路径"""
    try:
        import paho.mqtt.client as mqtt
        
        # 获取配置
        mqtt_cfg = get_mqtt_config()
        
        # 创建测试PDF
        # pdf_file = "绿色建筑评分标准.pdf"
        pdf_file = create_test_pdf()
        
        # 注意：文件路径方式需要服务端能访问到该文件
        # 建议使用base64方式传输，或确保文件在共享位置
        
        # 编码为base64（推荐）
        print("\n编码PDF为base64...")
        pdf_base64 = encode_file_to_base64(pdf_file)
        
        # 准备MQTT消息
        message = {
            "print_type": "pdf",
            "pdf_data": pdf_base64,  # 使用base64编码（推荐）
            # "pdf_file": pdf_file,  # 或使用文件路径（需要服务端能访问）
            "printer": None  # None表示使用默认打印机
        }
        
        print("\n" + "=" * 60)
        print("测试方式1: 使用文件路径发送PDF打印任务")
        print("=" * 60)
        print(f"MQTT服务器: {mqtt_cfg['host']}:{mqtt_cfg['port']}")
        print(f"MQTT主题: {mqtt_cfg['topic']}")
        print(f"PDF文件: {pdf_file}")
        print(f"消息内容: {json.dumps(message, ensure_ascii=False, indent=2)}")
        
        # 连接MQTT并发送
        client = mqtt.Client()
        if mqtt_cfg['username'] and mqtt_cfg['password']:
            client.username_pw_set(mqtt_cfg['username'], mqtt_cfg['password'])
        
        client.connect(mqtt_cfg['host'], mqtt_cfg['port'], 60)
        
        result = client.publish(mqtt_cfg['topic'], json.dumps(message))
        
        if result.rc == 0:
            print("✓ MQTT消息发送成功")
        else:
            print(f"✗ MQTT消息发送失败: {result.rc}")
        
        client.disconnect()
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_pdf_print_with_base64():
    """测试方式2: 使用base64编码"""
    try:
        import paho.mqtt.client as mqtt
        
        # 获取配置
        mqtt_cfg = get_mqtt_config()
        
        # 创建测试PDF
        pdf_file = create_test_pdf()
        
        # 编码为base64
        print("\n编码PDF为base64...")
        pdf_base64 = encode_file_to_base64(pdf_file)
        print(f"✓ Base64长度: {len(pdf_base64)} 字符")
        
        # 准备MQTT消息
        message = {
            "print_type": "pdf",
            "pdf_data": pdf_base64,  # base64编码的PDF
            "printer": None
        }
        
        print("\n" + "=" * 60)
        print("测试方式2: 使用Base64编码发送PDF打印任务")
        print("=" * 60)
        print(f"MQTT服务器: {mqtt_cfg['host']}:{mqtt_cfg['port']}")
        print(f"MQTT主题: {mqtt_cfg['topic']}")
        print(f"原文件: {pdf_file}")
        print(f"Base64大小: {len(pdf_base64)} 字符")
        
        # 连接MQTT并发送
        client = mqtt.Client()
        if mqtt_cfg['username'] and mqtt_cfg['password']:
            client.username_pw_set(mqtt_cfg['username'], mqtt_cfg['password'])
        
        client.connect(mqtt_cfg['host'], mqtt_cfg['port'], 60)
        
        result = client.publish(mqtt_cfg['topic'], json.dumps(message))
        
        if result.rc == 0:
            print("✓ MQTT消息发送成功")
        else:
            print(f"✗ MQTT消息发送失败: {result.rc}")
        
        client.disconnect()
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("PDF打印测试")
    print("=" * 60)
    print()
    print("请选择测试方式:")
    print("1. 使用文件路径（推荐）")
    print("2. 使用Base64编码")
    print("3. 两种方式都测试")
    print()
    
    try:
        choice = input("请输入选项 (1-3): ").strip()
        
        if choice == '1':
            test_pdf_print_with_file_path()
        elif choice == '2':
            test_pdf_print_with_base64()
        elif choice == '3':
            test_pdf_print_with_file_path()
            print("\n等待3秒...\n")
            import time
            time.sleep(3)
            test_pdf_print_with_base64()
        else:
            print("无效的选项")
            return 1
        
        print("\n提示:")
        print("  1. 确保MQTT服务器正在运行")
        print("  2. 确保打印服务程序正在运行")
        print("  3. 检查打印服务的输出确认是否收到消息")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n测试已取消")
        return 0
    except Exception as e:
        print(f"\n测试失败: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

