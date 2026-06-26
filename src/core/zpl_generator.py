#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZPL代码生成器模块
提供标签ZPL代码生成功能，支持从设计师模板直接生成ZPL
"""

import json
import os
import re
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
    def _substitute_variables(text, variables):
        """替换文本中的 @变量名 为实际值"""
        if not variables or not text:
            return text
        result = str(text)
        for key, val in variables.items():
            result = result.replace('@' + key, str(val))
        return result

    @staticmethod
    def _extract_variables_from_element(el):
        """从元素中提取所有 @变量名"""
        vars_list = []
        content = el.get('content', '') or ''
        variable = el.get('variable', '') or ''
        data = el.get('data', '') or ''

        all_text = f"{content} {variable} {data}"
        matches = re.findall(r'@([\w\u4e00-\u9fff]+)', all_text)
        return list(set(matches))

    @staticmethod
    def generate_label_zpl_from_template(template_data, variables=None):
        """
        从设计师模板数据直接生成ZPL代码，完整保留位置坐标

        Args:
            template_data: 设计师模板完整数据
                {
                    "pages": [{
                        "elements": [
                            {"type": "text", "content": "...", "variable": "@name",
                             "style": {"left": 50, "top": 30, "width": 200, "height": 40, "fontSize": 14}},
                            {"type": "barcode", "data": "@sn",
                             "style": {"left": 50, "top": 100, "width": 400, "height": 80}},
                            {"type": "qrcode", "data": "fixed_value",
                             "style": {"left": 500, "top": 80, "width": 100, "height": 100}}
                        ]
                    }],
                    "canvasSize": {"width": 800, "height": 300}
                }
            variables: 变量值字典 {"name": "实际值", "sn": "SN123"}

        Returns:
            str: ZPL代码字符串
        """
        if variables is None:
            variables = {}

        config = _load_template_config()

        # 从模板数据获取画布尺寸
        canvas_size = template_data.get('canvasSize', {})
        label_width = canvas_size.get('width', 800)
        label_height = canvas_size.get('height', 600)

        zpl_parts = []
        zpl_parts.append("^XA")
        zpl_parts.append(f"^PW{int(label_width)}")
        zpl_parts.append(f"^LL{int(label_height)}")

        pages = template_data.get('pages', [])
        if not pages:
            zpl_parts.append("^XZ")
            return '\n'.join(zpl_parts)

        for page in pages:
            elements = page.get('elements', [])
            # 按 y 坐标排序确保绘制顺序正确
            sorted_elements = sorted(elements, key=lambda e: (e.get('style', {}).get('top', 0), e.get('style', {}).get('left', 0)))

            for el in sorted_elements:
                el_type = el.get('type', '')
                style = el.get('style', {})

                left = int(style.get('left', 0))
                top = int(style.get('top', 0))
                el_width = int(style.get('width', 200))
                el_height = int(style.get('height', 40))
                font_size = int(style.get('fontSize', 14))

                if el_type == 'text':
                    zpl = ZPLGenerator._generate_text_zpl(
                        el, left, top, el_width, el_height, font_size, variables
                    )
                    if zpl:
                        zpl_parts.append(zpl)

                elif el_type == 'barcode':
                    zpl = ZPLGenerator._generate_barcode_zpl(
                        el, left, top, el_width, el_height, variables
                    )
                    if zpl:
                        zpl_parts.append(zpl)

                elif el_type == 'qrcode':
                    zpl = ZPLGenerator._generate_qrcode_zpl(
                        el, left, top, el_width, el_height, variables
                    )
                    if zpl:
                        zpl_parts.append(zpl)

                elif el_type == 'line':
                    zpl = ZPLGenerator._generate_line_zpl(
                        el, left, top, el_width, el_height
                    )
                    if zpl:
                        zpl_parts.append(zpl)

                elif el_type in ('rect', 'circle'):
                    zpl = ZPLGenerator._generate_shape_zpl(
                        el, left, top, el_width, el_height
                    )
                    if zpl:
                        zpl_parts.append(zpl)

        zpl_parts.append("^XZ")
        return '\n'.join(zpl_parts)

    @staticmethod
    def _generate_text_zpl(el, left, top, width, height, font_size, variables):
        """生成文本元素的 ZPL 代码"""
        content = el.get('content', '') or ''
        variable = el.get('variable', '') or ''

        # 替换变量
        content = ZPLGenerator._substitute_variables(content, variables)
        variable = ZPLGenerator._substitute_variables(variable, variables)

        # 确定显示文本
        if variable:
            # 有变量绑定：显示内容中替换变量后的结果，或直接用变量值
            display_text = content if content else variable
        else:
            display_text = content

        if not display_text or not display_text.strip():
            return None

        display_text = display_text.strip()

        # 检查是否还有未替换的 @变量（无值的情况，使用变量名本身）
        display_text = re.sub(r'@([\w\u4e00-\u9fff]+)', r'\1', display_text)

        # 判断是否包含中文
        has_chinese = any('\u4e00' <= char <= '\u9fff' for char in display_text)

        if has_chinese:
            # 中文用图像方式
            hex_data, w, h, bpr, total = text_to_image_zpl(display_text, font_size=font_size)
            if hex_data:
                return f"^FO{left},{top}^GFA,{total},{total},{bpr},{hex_data}^FS"
        else:
            # 纯英文数字，使用内置字体
            # 将 CSS font-size 映射为 ZPL 字体大小（近似）
            zpl_font_size = max(18, min(120, int(font_size * 1.5)))
            return f"^FO{left},{top}^A0N,{zpl_font_size},{zpl_font_size}^FD{display_text}^FS"

        return None

    @staticmethod
    def _generate_barcode_zpl(el, left, top, width, height, variables):
        """生成条形码的 ZPL 代码（Code 128）"""
        data = el.get('data', '') or ''
        data = ZPLGenerator._substitute_variables(data, variables)

        if not data:
            return None

        # 根据元素高度计算条码参数
        barcode_height = max(30, min(200, int(height * 0.8)))
        narrow_bar = max(1, min(10, int(width / 200)))

        # Code 128 条码: ^BY(窄条宽,宽条比例,条码高)^BC(方向,高度,打印文本,打印文本在上,模式)
        return f"^FO{left},{top}^BY{narrow_bar},2,{barcode_height}^BCN,{barcode_height},N,N,N^FD{data}^FS"

    @staticmethod
    def _generate_qrcode_zpl(el, left, top, width, height, variables):
        """生成二维码的 ZPL 代码"""
        data = el.get('data', '') or ''
        data = ZPLGenerator._substitute_variables(data, variables)

        if not data:
            return None

        # QR码: ^BQ(方向,模型,放大系数)^FD(纠错级别)A,(数据)^FS
        qr_size = min(width, height)
        magnification = max(1, min(10, int(qr_size / 30)))

        return f"^FO{left},{top}^BQN,2,{magnification}^FDQA,{data}^FS"

    @staticmethod
    def _generate_line_zpl(el, left, top, width, height):
        """生成线条的 ZPL 代码"""
        line_width = max(1, height)
        line_length = max(1, width)
        return f"^FO{left},{top}^GB{line_length},{line_width},{line_width}^FS"

    @staticmethod
    def _generate_shape_zpl(el, left, top, width, height):
        """生成矩形/圆形的 ZPL 代码"""
        thickness = int(el.get('style', {}).get('borderWidth', 3))
        if el.get('type') == 'circle':
            # ZPL 没有原生圆形，用椭圆近似
            return f"^FO{left},{top}^GE{width},{height},{thickness}^FS"
        else:
            # 矩形 (Graphic Box)
            return f"^FO{left},{top}^GB{width},{height},{thickness}^FS"

    # ============================================================
    # 旧版兼容方法（接收结构化 JSON 数据）
    # ============================================================

    @staticmethod
    def generate_label_zpl(label_data):
        """
        根据标签数据生成ZPL代码（支持中文）- 旧版兼容

        Args:
            label_data: 标签数据字典
                {
                    "title": "产品标签",
                    "fields": [
                        {"label": "产品名称", "value": "精密电子元件", "font_size": 28},
                    ],
                    "barcode": "SN20251015001",
                    "qrcode": "SN20251015001"
                }

        Returns:
            str: ZPL代码字符串
        """
        config = _load_template_config()

        print(f"生成标签: {label_data.get('title', '未命名')}")

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

