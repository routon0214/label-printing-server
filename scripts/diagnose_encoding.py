#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
编码问题诊断工具
用于检查系统字体、编码支持和打印配置
"""

import sys
import os
import platform

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

def print_section(title):
    """打印章节标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def check_system_info():
    """检查系统信息"""
    print_section("系统信息")
    print(f"操作系统: {platform.system()} {platform.release()}")
    print(f"架构: {platform.machine()}")
    print(f"Python版本: {sys.version}")
    print(f"Python编码: {sys.getdefaultencoding()}")
    print(f"文件系统编码: {sys.getfilesystemencoding()}")
    
    if sys.platform == 'win32':
        print(f"控制台输出编码: {sys.stdout.encoding}")
        print(f"控制台错误编码: {sys.stderr.encoding}")

def check_pillow():
    """检查Pillow库"""
    print_section("Pillow库检查")
    try:
        from PIL import Image, ImageDraw, ImageFont
        import PIL
        print(f"✓ Pillow已安装")
        print(f"  版本: {PIL.__version__}")
        
        # 测试基本功能
        img = Image.new('1', (100, 100), 1)
        print(f"✓ 图像创建功能正常")
        
        return True
    except ImportError as e:
        print(f"✗ Pillow未安装: {e}")
        print(f"  安装命令: pip install Pillow")
        return False

def check_fonts():
    """检查中文字体"""
    print_section("中文字体检查")
    
    try:
        from src.utils.font_utils import get_font_paths
        font_paths = get_font_paths()
        
        print(f"当前系统: {platform.system()}")
        print(f"搜索字体路径: {len(font_paths)} 个")
        print()
        
        found_fonts = []
        for font_path in font_paths:
            exists = os.path.exists(font_path)
            status = "✓" if exists else "✗"
            print(f"{status} {font_path}")
            if exists:
                found_fonts.append(font_path)
        
        print()
        if found_fonts:
            print(f"✓ 找到 {len(found_fonts)} 个可用字体")
            
            # 测试加载字体
            try:
                from PIL import ImageFont
                font = ImageFont.truetype(found_fonts[0], 30)
                print(f"✓ 字体加载测试成功: {os.path.basename(found_fonts[0])}")
                return True
            except Exception as e:
                print(f"✗ 字体加载测试失败: {e}")
                return False
        else:
            print(f"✗ 未找到任何中文字体")
            print()
            print("解决方案:")
            if platform.system() == 'Windows':
                print("  1. 确保 C:/Windows/Fonts/ 目录下有中文字体")
                print("  2. 推荐字体: 微软雅黑 (msyh.ttc), 黑体 (simhei.ttf)")
            elif platform.system() == 'Linux':
                print("  Ubuntu/Debian: sudo apt-get install fonts-wqy-zenhei fonts-wqy-microhei")
                print("  CentOS/RHEL: sudo yum install wqy-zenhei-fonts wqy-microhei-fonts")
            return False
            
    except Exception as e:
        print(f"✗ 字体检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_chinese_conversion():
    """测试中文转换"""
    print_section("中文文本转换测试")
    
    try:
        from src.utils.image_utils import text_to_image_zpl
        
        test_texts = [
            "测试",
            "中文打印",
            "产品名称：精密电子元件",
        ]
        
        all_success = True
        for text in test_texts:
            print(f"\n测试文本: '{text}'")
            hex_data, w, h, bpr, total = text_to_image_zpl(text, font_size=30)
            
            if hex_data:
                print(f"  ✓ 转换成功")
                print(f"    尺寸: {w}x{h}px")
                print(f"    数据: {total} bytes")
                print(f"    十六进制前20字符: {hex_data[:20]}...")
            else:
                print(f"  ✗ 转换失败")
                all_success = False
        
        return all_success
        
    except Exception as e:
        print(f"✗ 转换测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_printer_config():
    """检查打印机配置"""
    print_section("打印机配置检查")
    
    try:
        from src.config import ConfigManager
        
        config_file = 'config/printer_config.json'
        if not os.path.exists(config_file):
            print(f"✗ 配置文件不存在: {config_file}")
            return False
        
        print(f"✓ 配置文件存在: {config_file}")
        
        config_manager = ConfigManager(config_file)
        config = config_manager.load()
        
        # 检查MQTT配置
        mqtt_config = config.get('mqtt', {})
        print(f"\nMQTT配置:")
        print(f"  URL: {mqtt_config.get('url', '未配置')}")
        print(f"  主题: {mqtt_config.get('topic', '未配置')}")
        
        # 检查打印机配置
        printer_config = config.get('printer', {})
        printers_config = config.get('printers', [])
        
        print(f"\n打印机配置:")
        if printers_config:
            print(f"  找到 {len(printers_config)} 台打印机")
            for i, p in enumerate(printers_config, 1):
                print(f"  {i}. 名称: {p.get('name', '未设置')}")
                print(f"     类型: {', '.join(p.get('types', []))}")
                print(f"     IP: {p.get('ip', '未设置')}")
        else:
            print(f"  默认打印机:")
            print(f"    名称: {printer_config.get('name', '未设置')}")
            print(f"    IP: {printer_config.get('ip', '未设置')}")
            print(f"    设备: {printer_config.get('device', '未设置')}")
        
        return True
        
    except Exception as e:
        print(f"✗ 配置检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def generate_test_label():
    """生成测试标签"""
    print_section("生成测试标签")
    
    try:
        from src.core.zpl_generator import ZPLGenerator
        
        label_data = {
            "title": "编码测试标签",
            "fields": [
                {"label": "产品名称", "value": "测试产品", "font_size": 28},
                {"label": "序列号", "value": "TEST-2025-001", "font_size": 25},
            ],
            "barcode": "TEST2025001"
        }
        
        print("生成测试标签...")
        generator = ZPLGenerator()
        zpl_code = generator.generate_label_zpl(label_data)
        
        if zpl_code and len(zpl_code) > 0:
            print(f"\n✓ 标签生成成功")
            print(f"  ZPL代码长度: {len(zpl_code)} 字符")
            print(f"  包含图像命令: {'是' if '^GFA' in zpl_code else '否'}")
            
            # 保存到文件
            output_file = "test_encoding_label.zpl"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(zpl_code)
            print(f"  已保存到: {output_file}")
            
            # 显示前500字符
            print(f"\n  ZPL代码预览（前500字符）:")
            print("  " + "-" * 66)
            preview = zpl_code[:500].replace('\n', '\n  ')
            print(f"  {preview}...")
            print("  " + "-" * 66)
            
            return True
        else:
            print(f"✗ 标签生成失败")
            return False
            
    except Exception as e:
        print(f"✗ 标签生成失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("=" * 70)
    print(" " * 20 + "编码问题诊断工具")
    print("=" * 70)
    
    results = {
        "系统信息": True,
        "Pillow库": False,
        "中文字体": False,
        "文本转换": False,
        "打印机配置": False,
        "测试标签": False
    }
    
    # 1. 系统信息
    check_system_info()
    
    # 2. Pillow检查
    results["Pillow库"] = check_pillow()
    
    # 3. 字体检查
    results["中文字体"] = check_fonts()
    
    # 4. 文本转换测试
    if results["Pillow库"] and results["中文字体"]:
        results["文本转换"] = test_chinese_conversion()
    else:
        print_section("中文文本转换测试")
        print("⊘ 跳过测试（Pillow或字体未就绪）")
    
    # 5. 打印机配置
    results["打印机配置"] = check_printer_config()
    
    # 6. 生成测试标签
    if results["Pillow库"] and results["中文字体"]:
        results["测试标签"] = generate_test_label()
    else:
        print_section("生成测试标签")
        print("⊘ 跳过测试（Pillow或字体未就绪）")
    
    # 总结
    print_section("诊断结果汇总")
    for name, status in results.items():
        status_icon = "✓" if status else "✗"
        print(f"{status_icon} {name}: {'正常' if status else '异常'}")
    
    print()
    all_pass = all(results.values())
    if all_pass:
        print("✓ 所有检查通过！系统配置正常。")
        print()
        print("如果仍然出现乱码，请检查:")
        print("  1. 上传的文件编码是否为UTF-8")
        print("  2. 打印机是否支持接收UTF-8编码的数据")
        print("  3. 使用生成的 test_encoding_label.zpl 进行测试")
    else:
        print("✗ 发现问题，请根据上述信息进行修复。")
        print()
        print("常见问题:")
        print("  1. 如果Pillow未安装: pip install Pillow")
        print("  2. 如果缺少中文字体，请根据上述提示安装")
        print("  3. 如果配置文件异常，请检查 config/printer_config.json")
    
    print()
    input("按回车键退出...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用户中断")
    except Exception as e:
        print(f"\n诊断工具运行失败: {e}")
        import traceback
        traceback.print_exc()
        input("\n按回车键退出...")

