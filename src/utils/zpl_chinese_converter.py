#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZPL中文转换模块
自动检测ZPL代码中的中文并转换为图像
"""

import re
from src.utils.image_utils import text_to_image_zpl


def has_chinese(text):
    """检查文本是否包含中文"""
    return bool(re.search(r'[\u4e00-\u9fff]', text))


def convert_zpl_chinese_to_image(zpl_code):
    """
    自动检测并转换ZPL代码中的中文为图像
    
    支持多种ZPL格式:
    1. 标准ZPL: ^FO...^FD中文^FS
    2. 直接文本: 任何中文字符
    
    Args:
        zpl_code: 原始ZPL代码
        
    Returns:
        转换后的ZPL代码
    """
    # 检查是否包含中文
    if not has_chinese(zpl_code):
        print("  ZPL代码不包含中文，无需转换")
        return zpl_code
    
    print("  检测到ZPL代码包含中文，开始转换...")
    
    lines = zpl_code.split('\n')
    converted_lines = []
    conversion_count = 0
    
    for line in lines:
        # 检查是否包含中文
        if not has_chinese(line):
            converted_lines.append(line)
            continue
        
        # 尝试匹配 ^FD...^FS 格式（ZPL文本命令）
        fd_pattern = r'(\^F[OW]\d+,\d+.*?\^A[^F]*?\^FD)([^^]+?)(\^FS)'
        match = re.search(fd_pattern, line)
        
        if match:
            prefix = match.group(1)  # ^FO...^FD
            text = match.group(2)     # 文本内容
            suffix = match.group(3)   # ^FS
            
            if has_chinese(text):
                print(f"  转换中文文本: {text[:30]}{'...' if len(text) > 30 else ''}")
                
                # 提取位置信息
                pos_match = re.search(r'\^F[OW](\d+),(\d+)', prefix)
                if pos_match:
                    x, y = pos_match.groups()
                    
                    # 转换为图像
                    hex_data, width, height, bpr, total = text_to_image_zpl(text, font_size=30)
                    
                    if hex_data:
                        # 生成图像命令
                        image_cmd = f"^FO{x},{y}^GFA,{total},{total},{bpr},{hex_data}^FS"
                        converted_lines.append(image_cmd)
                        conversion_count += 1
                        continue
            
        # 如果没有匹配到标准格式但包含中文，保留原样但添加警告
        if has_chinese(line) and not line.strip().startswith('//'):
            print(f"  警告: 包含中文但无法自动转换的行: {line[:50]}...")
        
        converted_lines.append(line)
    
    result = '\n'.join(converted_lines)
    
    if conversion_count > 0:
        print(f"  [OK] 成功转换 {conversion_count} 处中文文本为图像")
    else:
        print("  [WARNING] 未能转换任何中文文本，可能格式不标准")
    
    return result


def detect_and_convert_zpl(zpl_code):
    """
    智能检测并转换ZPL代码
    
    Args:
        zpl_code: 原始ZPL代码（可能包含中文）
        
    Returns:
        tuple: (converted_zpl, was_converted)
            converted_zpl: 转换后的ZPL代码
            was_converted: 是否进行了转换
    """
    if not has_chinese(zpl_code):
        return zpl_code, False
    
    print("\n" + "="*60)
    print("ZPL中文自动转换")
    print("="*60)
    
    converted = convert_zpl_chinese_to_image(zpl_code)
    
    print("="*60)
    print()
    
    return converted, True

