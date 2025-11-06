#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图像处理工具模块
提供文本转图像和ZPL格式转换功能
"""

import os
from .font_utils import get_font_paths


def text_to_image_zpl(text, font_size=30):
    """
    将中文文本转换为ZPL图像命令（跨平台）
    
    Args:
        text: 要转换的文本
        font_size: 字体大小
        
    Returns:
        tuple: (hex_string, width, height, bytes_per_row, total_bytes)
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # 尝试加载中文字体
        font = None
        font_paths = get_font_paths()
        font_loaded = None
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    font = ImageFont.truetype(font_path, font_size)
                    font_loaded = font_path
                    print(f"  使用字体: {os.path.basename(font_path)}")
                    break
                except Exception as e:
                    print(f"  字体加载失败 {font_path}: {e}")
                    continue
        
        if font is None:
            print("  警告：未找到中文字体，使用默认字体（可能无法正确显示中文）")
            print(f"  尝试的字体路径: {', '.join([os.path.basename(p) for p in font_paths])}")
            font = ImageFont.load_default()
        
        # 创建临时图像测量文本大小
        temp_img = Image.new('RGB', (1, 1), 'white')
        draw = ImageDraw.Draw(temp_img)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # 添加边距
        padding = 8
        img_width = text_width + padding * 2
        img_height = text_height + padding * 2
        
        # 创建黑白图像
        image = Image.new('1', (img_width, img_height), 1)
        draw = ImageDraw.Draw(image)
        draw.text((padding, padding - bbox[1]), text, font=font, fill=0)
        
        # 转换为ZPL十六进制
        width, height = image.size
        bytes_per_row = (width + 7) // 8
        
        hex_data = []
        pixels = image.load()
        
        for y in range(height):
            row_bytes = []
            for x in range(0, width, 8):
                byte_val = 0
                for bit in range(8):
                    if x + bit < width:
                        if pixels[x + bit, y] == 0:
                            byte_val |= (1 << (7 - bit))
                row_bytes.append(byte_val)
            hex_data.append(''.join([f'{b:02X}' for b in row_bytes]))
        
        hex_string = ''.join(hex_data)
        total_bytes = len(hex_string) // 2
        
        print(f"  文本转换成功: '{text[:20]}{'...' if len(text) > 20 else ''}' -> {img_width}x{img_height}px ({total_bytes} bytes)")
        
        return hex_string, img_width, img_height, bytes_per_row, total_bytes
        
    except ImportError:
        print("[ERROR] 错误：需要安装 Pillow 库支持中文: pip install Pillow")
        print("  安装命令: pip install Pillow")
        return None, 0, 0, 0, 0
    except Exception as e:
        print(f"[ERROR] 文本转图像失败: {e}")
        import traceback
        traceback.print_exc()
        return None, 0, 0, 0, 0

