#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZPL中文转换工具
将ZPL文件中的中文TEXT命令转换为图像命令
"""

import re
import os
import sys

# 添加src路径
sys.path.insert(0, os.path.dirname(__file__))
from src.utils.image_utils import text_to_image_zpl

def has_chinese(text):
    """检查文本是否包含中文"""
    return bool(re.search(r'[\u4e00-\u9fff]', text))

def convert_zpl_chinese(zpl_code):
    """
    转换ZPL代码中的中文TEXT命令为图像命令
    
    Args:
        zpl_code: 原始ZPL代码
        
    Returns:
        转换后的ZPL代码
    """
    print("="*70)
    print("ZPL中文转换")
    print("="*70)
    print()
    
    lines = zpl_code.split('\n')
    converted_lines = []
    conversion_count = 0
    
    for i, line in enumerate(lines, 1):
        # 匹配TEXT命令: TEXT x,y,"font",rotation,width,height,"text"
        # 支持转义引号: \"
        text_match = re.match(r'TEXT\s+(\d+),(\d+),\\"([^"]+)\\",(\d+),(\d+),(\d+),\\"([^"]*)\\', line)
        
        if text_match:
            x, y, font, rotation, w_mult, h_mult, text = text_match.groups()
            
            if has_chinese(text):
                print(f"第{i}行: 发现中文TEXT命令")
                print(f"  位置: ({x}, {y})")
                print(f"  字体: {font}")
                print(f"  文本: {text}")
                
                # 估算字体大小（基于高度倍数）
                font_size = int(h_mult) * 20  # 粗略估算
                
                # 转换为图像
                hex_data, width, height, bpr, total = text_to_image_zpl(text, font_size=font_size)
                
                if hex_data:
                    # 生成ZPL图像命令
                    # ^FO{x},{y}^GFA,{total},{total},{bytes_per_row},{hex_data}^FS
                    image_cmd = f"^FO{x},{y}^GFA,{total},{total},{bpr},{hex_data}^FS"
                    converted_lines.append(image_cmd)
                    conversion_count += 1
                    print(f"  转换成功: {width}x{height}px")
                else:
                    print(f"  转换失败，保留原命令")
                    # 转换为ZPL格式的TEXT命令
                    zpl_text = f"^FO{x},{y}^A0N,{font_size},{font_size}^FD{text}^FS"
                    converted_lines.append(zpl_text)
                
                print()
            else:
                # 无中文，转换为ZPL格式但保持原样
                font_size = int(h_mult) * 20
                zpl_text = f"^FO{x},{y}^A0N,{font_size},{font_size}^FD{text}^FS"
                converted_lines.append(zpl_text)
        else:
            # 检查是否是其他ZPL命令或需要转换的格式
            line_upper = line.strip().upper()
            
            # 处理常见的ZPL格式命令
            if line_upper.startswith('SIZE'):
                # SIZE 60 mm, 40 mm -> ^PW{width}
                size_match = re.search(r'SIZE\s+(\d+)\s*mm,\s*(\d+)\s*mm', line, re.IGNORECASE)
                if size_match:
                    width_mm, height_mm = size_match.groups()
                    # 转换为dots (203dpi: 1mm ≈ 8 dots)
                    width_dots = int(float(width_mm) * 8)
                    height_dots = int(float(height_mm) * 8)
                    converted_lines.append(f"^PW{width_dots}")
                    converted_lines.append(f"^LL{height_dots}")
                else:
                    converted_lines.append(line)
            elif line_upper.startswith('DIRECTION'):
                # DIRECTION 1,0 -> ^POI (倒置打印)
                direction_match = re.search(r'DIRECTION\s+(\d+)', line, re.IGNORECASE)
                if direction_match and direction_match.group(1) == '1':
                    converted_lines.append("^POI")  # Print orientation inverted
            elif line_upper.startswith('GAP') or line_upper.startswith('OFFSET') or line_upper.startswith('REFERENCE'):
                # 这些可以忽略或转换
                pass
            elif line_upper.startswith('CLS'):
                # CLS -> ^XA (开始)
                if not any('^XA' in l for l in converted_lines):
                    converted_lines.insert(0, "^XA")
            elif line_upper.startswith('PRINT'):
                # PRINT 1 -> ^XZ (结束)
                converted_lines.append("^XZ")
            elif line_upper.startswith('QRCODE'):
                # QRCODE x,y,L,10,A,0,M2,S6,"data"
                qr_match = re.match(r'QRCODE\s+(\d+),(\d+),[^,]+,[^,]+,[^,]+,[^,]+,[^,]+,S(\d+),"([^"]*)"', line, re.IGNORECASE)
                if qr_match:
                    x, y, size, data = qr_match.groups()
                    # 转换为ZPL二维码
                    converted_lines.append(f"^FO{x},{y}^BQN,2,{size}^FDQA,{data}^FS")
                else:
                    converted_lines.append(f"// 未转换: {line}")
            elif line.strip() and not line.strip().startswith('//'):
                # 其他非空行，可能已经是ZPL格式
                if line.strip().startswith('^'):
                    converted_lines.append(line)
                else:
                    converted_lines.append(f"// {line}")
    
    # 确保有开始和结束标记
    if not any('^XA' in l for l in converted_lines):
        converted_lines.insert(0, "^XA")
    if not any('^XZ' in l for l in converted_lines):
        converted_lines.append("^XZ")
    
    print("="*70)
    print(f"转换完成！")
    print(f"  处理行数: {len(lines)}")
    print(f"  转换的中文TEXT命令: {conversion_count} 个")
    print("="*70)
    print()
    
    return '\n'.join(converted_lines)

def main():
    """主函数"""
    import sys
    
    if len(sys.argv) < 2:
        print("用法:")
        print("  python convert_zpl_chinese.py <输入文件> [输出文件]")
        print()
        print("示例:")
        print("  python convert_zpl_chinese.py data/print_text.txt")
        print("  python convert_zpl_chinese.py data/print_text.txt output.zpl")
        print()
        print("如果不指定输出文件，将生成 <输入文件>_converted.zpl")
        return
    
    input_file = sys.argv[1]
    
    if not os.path.exists(input_file):
        print(f"错误: 文件不存在: {input_file}")
        return
    
    # 确定输出文件
    if len(sys.argv) >= 3:
        output_file = sys.argv[2]
    else:
        base_name = os.path.splitext(input_file)[0]
        output_file = f"{base_name}_converted.zpl"
    
    print(f"输入文件: {input_file}")
    print(f"输出文件: {output_file}")
    print()
    
    # 读取输入文件
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            zpl_code = f.read()
    except UnicodeDecodeError:
        # 尝试其他编码
        try:
            with open(input_file, 'r', encoding='gbk') as f:
                zpl_code = f.read()
            print("注意: 使用GBK编码读取文件")
        except:
            print("错误: 无法读取文件，编码不支持")
            return
    
    # 转换
    converted_zpl = convert_zpl_chinese(zpl_code)
    
    # 保存输出
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(converted_zpl)
    
    print(f"已保存到: {output_file}")
    print()
    print("现在可以:")
    print(f"  1. 通过Web界面上传: http://127.0.0.1:5000")
    print(f"  2. 或直接测试: python -c \"from src.core.printer import ZebraPrinter; p = ZebraPrinter('ZT411'); p.print_label(open('{output_file}').read())\"")

if __name__ == '__main__':
    main()

