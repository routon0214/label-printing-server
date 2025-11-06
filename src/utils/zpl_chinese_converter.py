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
    1. 标准ZPL: ^FO...^A...^FD中文^FS
    2. 单行ZPL: ^XA^FO20,10^A0N,25,25^FD测试^FS^XZ
    
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
    
    conversion_count = 0
    
    # 匹配 ^FO...^A...^FD中文^FS 模式
    # 支持单行和多行ZPL
    pattern = r'(\^FO\d+,\d+)(\^A[^\^]*?)(\^FD)([^\^]+?)(\^FS)'
    
    def replace_chinese(match):
        nonlocal conversion_count
        fo_pos = match.group(1)  # ^FO20,10
        a_font = match.group(2)   # ^A0N,25,25
        fd_start = match.group(3) # ^FD
        text = match.group(4)      # 测试标签
        fs_end = match.group(5)    # ^FS
        
        # 只转换包含中文的文本
        if not has_chinese(text):
            return match.group(0)  # 保持原样
        
        print(f"  转换中文文本: {text[:30]}{'...' if len(text) > 30 else ''}")
        
        # 提取位置
        pos_match = re.search(r'\^FO(\d+),(\d+)', fo_pos)
        if not pos_match:
            return match.group(0)
        
        x, y = pos_match.groups()
        
        # 转换为图像
        hex_data, width, height, bpr, total = text_to_image_zpl(text, font_size=30)
        
        if hex_data:
            conversion_count += 1
            # 生成图像命令（保持^XA和其他命令的位置）
            return f"^FO{x},{y}^GFA,{total},{total},{bpr},{hex_data}^FS"
        else:
            # 转换失败，保持原样
            return match.group(0)
    
    # 执行替换
    converted_zpl = re.sub(pattern, replace_chinese, zpl_code)
    
    if conversion_count > 0:
        print(f"  [OK] 成功转换 {conversion_count} 处中文文本为图像")
    else:
        print("  [WARNING] 未能转换任何中文文本，可能格式不标准")
    
    return converted_zpl


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

