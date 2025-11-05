#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZPL代码生成器模块
提供标签ZPL代码生成功能
"""

from src.utils.image_utils import text_to_image_zpl


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
        print(f"生成标签: {label_data.get('title', '未命名')}")
        
        zpl_parts = []
        zpl_parts.append("^XA")  # 开始
        zpl_parts.append("^PW800")  # 标签宽度
        zpl_parts.append("^LL600")  # 标签长度
        
        y_pos = 40
        
        # 标题
        title = label_data.get('title', '标签')
        if title:
            hex_data, w, h, bpr, total = text_to_image_zpl(title, font_size=40)
            if hex_data:
                zpl_parts.append(f"^FO50,{y_pos}^GFA,{total},{total},{bpr},{hex_data}^FS")
                y_pos += h + 15
        
        # 分隔线
        zpl_parts.append(f"^FO50,{y_pos}^GB700,3,3^FS")
        y_pos += 20
        
        # 字段内容
        fields = label_data.get('fields', [])
        for field in fields:
            label_text = field.get('label', '')
            value_text = field.get('value', '')
            font_size = field.get('font_size', 25)
            
            # 判断是否包含中文
            text = f"{label_text}：{value_text}" if label_text else value_text
            
            if any('\u4e00' <= char <= '\u9fff' for char in text):
                # 包含中文，使用图像方式
                hex_data, w, h, bpr, total = text_to_image_zpl(text, font_size=font_size)
                if hex_data:
                    zpl_parts.append(f"^FO50,{y_pos}^GFA,{total},{total},{bpr},{hex_data}^FS")
                    y_pos += h + 10
            else:
                # 纯英文数字，直接使用ZPL字体
                zpl_parts.append(f"^FO50,{y_pos}^A0N,{font_size},{font_size}^FD{text}^FS")
                y_pos += font_size + 10
        
        y_pos += 10
        
        # 条形码
        barcode = label_data.get('barcode')
        if barcode:
            zpl_parts.append(f"^FO50,{y_pos}^BY2,3,70^BCN,70,N,N,N^FD{barcode}^FS")
        
        # 二维码
        qrcode = label_data.get('qrcode')
        if qrcode:
            zpl_parts.append(f"^FO550,{y_pos - 30}^BQN,2,5^FDQA,{qrcode}^FS")
        
        zpl_parts.append("^XZ")  # 结束
        
        return '\n'.join(zpl_parts)

