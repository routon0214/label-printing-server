#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZPL代码生成器模块
提供标签ZPL代码生成功能
"""

import json
import os
from src.utils.image_utils import text_to_image_zpl


def _load_template_config():
    """从配置文件中加载模板参数"""
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config', 'printer_config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
        return cfg.get('template', {})
    except Exception:
        return {}


class ZPLGenerator:
    """ZPL代码生成器"""
    
    @staticmethod
    def generate_label_zpl(label_data):
        """
        根据标签数据生成ZPL代码（支持中文）
        
        Args:
            label_data: 标签数据字典
                {
                    "title": "产品标签",
                    "fields": [
                        {"label": "产品名称", "value": "精密电子元件", "font_size": 28},
                        {"label": "产品型号", "value": "ZX-2024-PRO", "font_size": 25},
                        {"label": "序列号", "value": "SN20251015001", "font_size": 22},
                        {"label": "生产日期", "value": "2025-10-15", "font_size": 22}
                    ],
                    "barcode": "SN20251015001",
                    "qrcode": "SN20251015001"
                }
                
        Returns:
            str: ZPL代码字符串
        """
        config = _load_template_config()
        
        print(f"生成标签: {label_data.get('title', '未命名')}")
        
        # 读取配置参数（带默认值）
        label_width = config.get('label_width', 800)
        label_height = config.get('label_height', 600)
        margin_left = config.get('margin_left', 50)
        title_font_size = config.get('font_size_title', 40)
        field_font_size = config.get('font_size_field', 25)
        field_spacing = config.get('field_spacing', 10)
        separator_height = config.get('separator_height', 3)
        barcode_height = config.get('barcode_height', 70)
        barcode_narrow = config.get('barcode_narrow', 2)
        barcode_wide = config.get('barcode_wide', 3)
        show_separator = config.get('show_separator', True)
        
        zpl_parts = []
        zpl_parts.append("^XA")
        zpl_parts.append(f"^PW{label_width}")
        zpl_parts.append(f"^LL{label_height}")
        
        y_pos = 40
        sep_width = label_width - margin_left * 2
        
        # 标题
        title = label_data.get('title', '标签')
        if title:
            hex_data, w, h, bpr, total = text_to_image_zpl(title, font_size=title_font_size)
            if hex_data:
                zpl_parts.append(f"^FO{margin_left},{y_pos}^GFA,{total},{total},{bpr},{hex_data}^FS")
                y_pos += h + 15
        
        # 分隔线
        if show_separator:
            zpl_parts.append(f"^FO{margin_left},{y_pos}^GB{sep_width},{separator_height},{separator_height}^FS")
            y_pos += 20
        
        # 字段内容
        fields = label_data.get('fields', [])
        for field in fields:
            label_text = field.get('label', '')
            value_text = field.get('value', '')
            font_size = field.get('font_size', field_font_size)
            
            text = f"{label_text}：{value_text}" if label_text else value_text
            
            if any('\u4e00' <= char <= '\u9fff' for char in text):
                hex_data, w, h, bpr, total = text_to_image_zpl(text, font_size=font_size)
                if hex_data:
                    zpl_parts.append(f"^FO{margin_left},{y_pos}^GFA,{total},{total},{bpr},{hex_data}^FS")
                    y_pos += h + field_spacing
            else:
                zpl_parts.append(f"^FO{margin_left},{y_pos}^A0N,{font_size},{font_size}^FD{text}^FS")
                y_pos += font_size + field_spacing
        
        y_pos += 10
        
        # 条形码
        barcode = label_data.get('barcode')
        if barcode:
            zpl_parts.append(f"^FO{margin_left},{y_pos}^BY{barcode_narrow},{barcode_wide},{barcode_height}^BCN,{barcode_height},N,N,N^FD{barcode}^FS")
        
        # 二维码
        qrcode = label_data.get('qrcode')
        if qrcode:
            zpl_parts.append(f"^FO550,{y_pos - 30}^BQN,2,5^FDQA,{qrcode}^FS")
        
        zpl_parts.append("^XZ")
        
        return '\n'.join(zpl_parts)

