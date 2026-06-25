#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模板渲染器模块
将 vue-print-designer 保存的模板 JSON 转换为 ZPL 代码

设计器坐标单位: mm
ZPL 坐标单位: dots (203 DPI, 1mm ≈ 8 dots)
转换公式: dots = mm * 203 / 25.4
"""

import json
import os
from typing import Dict, Any, Optional, List
from src.utils.image_utils import text_to_image_zpl


# 203 DPI 转换常量
DPI = 203
MM_TO_DOTS = DPI / 25.4  # ≈ 7.99 dots/mm


def mm_to_dots(mm_val: float) -> int:
    """毫米转 ZPL 点数"""
    return round(mm_val * MM_TO_DOTS)


def pt_to_dots(pt_val: float) -> int:
    """字体磅数(pts)转 ZPL 点数"""
    return round(pt_val * DPI / 72.0)  # 1pt = 1/72 inch


def contains_chinese(text: str) -> bool:
    """判断文本是否包含中文字符"""
    for ch in text:
        if '\u4e00' <= ch <= '\u9fff' or '\u3000' <= ch <= '\u303f' or '\uff00' <= ch <= '\uffef':
            return True
    return False


class TemplateRenderer:
    """将设计器模板渲染为 ZPL 代码"""

    # 支持的元素类型
    ELEMENT_TYPES = {'text', 'barcode', 'qrcode', 'line', 'rect', 'image'}

    def __init__(self, template_data: Dict[str, Any]):
        """
        初始化渲染器

        Args:
            template_data: 模板完整数据 (包含 id, name, data 字段)
        """
        self.template = template_data
        self.template_data = template_data.get('data', {})
        self.name = template_data.get('name', '未命名模板')
        self.id = template_data.get('id', '')

    def render(self, variables: Dict[str, str]) -> str:
        """
        将模板 + 变量渲染为 ZPL 代码

        Args:
            variables: 变量键值对，如 {"产品名称": "精密元件", "型号": "ZX-2024"}

        Returns:
            ZPL 代码字符串
        """
        pages = self.template_data.get('pages', [])
        canvas_size = self.template_data.get('canvasSize', {})
        unit = self.template_data.get('unit', 'mm')

        if not pages:
            raise ValueError("模板中没有页面数据")

        # 计算标签尺寸(dots)
        canvas_w_mm = canvas_size.get('width', 100)
        canvas_h_mm = canvas_size.get('height', 100)
        label_width = mm_to_dots(canvas_w_mm)
        label_height = mm_to_dots(canvas_h_mm)

        zpl_parts = ["^XA"]
        zpl_parts.append(f"^PW{label_width}")
        zpl_parts.append(f"^LL{label_height}")

        # 渲染每页中的每个元素
        for page in pages:
            elements = page.get('elements', [])
            for element in elements:
                el_type = element.get('type', '')
                if el_type not in self.ELEMENT_TYPES:
                    continue

                # 跳过不可打印元素
                if not element.get('printable', True):
                    continue

                zpl = self._render_element(element, variables, unit)
                if zpl:
                    zpl_parts.append(zpl)

        zpl_parts.append("^XZ")
        return '\n'.join(zpl_parts)

    def _resolve_variable(self, content: str, variables: Dict[str, str]) -> str:
        """替换 @变量名 为实际值"""
        if not content or not content.startswith('@'):
            return content
        var_name = content[1:]  # 去掉 @ 前缀
        return variables.get(var_name, content)

    def _render_element(self, element: Dict, variables: Dict, unit: str) -> Optional[str]:
        """渲染单个元素"""
        el_type = element.get('type', '')

        handlers = {
            'text': self._render_text,
            'barcode': self._render_barcode,
            'qrcode': self._render_qrcode,
            'line': self._render_line,
            'rect': self._render_rect,
            'image': self._render_image,
        }

        handler = handlers.get(el_type)
        if handler:
            return handler(element, variables, unit)
        return None

    def _render_text(self, element: Dict, variables: Dict, unit: str) -> Optional[str]:
        """渲染文本元素"""
        x = mm_to_dots(element.get('x', 0))
        y = mm_to_dots(element.get('y', 0))
        content = element.get('content', '')
        style = element.get('style', {})

        # 替换变量
        text = self._resolve_variable(content, variables)

        if not text:
            return None

        # 获取字体大小(pts) 转为 dots
        font_size_pt = style.get('fontSize', 14)
        font_size_dots = pt_to_dots(font_size_pt)

        if contains_chinese(text):
            # 中文使用 GFA 图像方式
            hex_data, w, h, bpr, total = text_to_image_zpl(text, font_size=font_size_dots)
            if hex_data:
                return f"^FO{x},{y}^GFA,{total},{total},{bpr},{hex_data}^FS"
            return None
        else:
            # 纯英文/数字使用内置字体
            return f"^FO{x},{y}^A0N,{font_size_dots},{font_size_dots}^FD{text}^FS"

    def _render_barcode(self, element: Dict, variables: Dict, unit: str) -> Optional[str]:
        """渲染条码元素"""
        x = mm_to_dots(element.get('x', 0))
        y = mm_to_dots(element.get('y', 0))
        content = element.get('content', '')
        style = element.get('style', {})

        # 替换变量
        barcode_data = self._resolve_variable(content, variables)

        if not barcode_data:
            return None

        # 条码参数
        width_mm = element.get('width', 50)
        height_mm = element.get('height', 10)
        barcode_w_dots = mm_to_dots(width_mm)
        barcode_h_dots = mm_to_dots(height_mm)

        # 确保最小尺寸
        if barcode_h_dots < 30:
            barcode_h_dots = 30

        barcode_type = element.get('barcodeType', style.get('barcodeType', 'code128'))

        # ^BY 条码默认参数: 窄条宽度, 宽窄比, 高度
        zpl = f"^FO{x},{y}"
        zpl += f"^BY2,3.0,{barcode_h_dots}"

        if barcode_type == 'code128' or barcode_type == '':
            zpl += f"^BCN,{barcode_h_dots},N,N,N"
        elif barcode_type == 'code39':
            zpl += f"^B3N,N,{barcode_h_dots},N"
        elif barcode_type == 'ean13':
            zpl += f"^BEN,{barcode_h_dots},N,N"
        else:
            # 默认 code128
            zpl += f"^BCN,{barcode_h_dots},N,N,N"

        zpl += f"^FD{barcode_data}^FS"
        return zpl

    def _render_qrcode(self, element: Dict, variables: Dict, unit: str) -> Optional[str]:
        """渲染二维码元素"""
        x = mm_to_dots(element.get('x', 0))
        y = mm_to_dots(element.get('y', 0))
        content = element.get('content', '')

        # 替换变量
        qr_data = self._resolve_variable(content, variables)

        if not qr_data:
            return None

        # QR 码放大倍数，根据元素宽度计算
        width_mm = element.get('width', 30)
        # 大约每 4 dots 一个模块，QR 码约 25 模块宽
        magnification = max(2, min(10, mm_to_dots(width_mm) // 25))

        return f"^FO{x},{y}^BQN,2,{magnification}^FDQA,{qr_data}^FS"

    def _render_line(self, element: Dict, variables: Dict, unit: str) -> Optional[str]:
        """渲染线段元素"""
        x = mm_to_dots(element.get('x', 0))
        y = mm_to_dots(element.get('y', 0))
        width_mm = element.get('width', 1)
        height_mm = element.get('height', 1)

        w = max(1, mm_to_dots(width_mm))
        h = max(1, mm_to_dots(height_mm))

        # 线段：宽度或高度为线条粗细
        thickness = 2  # 默认线条粗细

        return f"^FO{x},{y}^GB{w},{h},{thickness}^FS"

    def _render_rect(self, element: Dict, variables: Dict, unit: str) -> Optional[str]:
        """渲染矩形元素（空心框）"""
        x = mm_to_dots(element.get('x', 0))
        y = mm_to_dots(element.get('y', 0))
        width_mm = element.get('width', 30)
        height_mm = element.get('height', 20)

        w = max(1, mm_to_dots(width_mm))
        h = max(1, mm_to_dots(height_mm))

        border_thickness = max(1, pt_to_dots(element.get('style', {}).get('borderWidth', 1)))

        return f"^FO{x},{y}^GB{w},{h},{border_thickness}^FS"

    def _render_image(self, element: Dict, variables: Dict, unit: str) -> Optional[str]:
        """渲染图片元素（内置图片数据）"""
        x = mm_to_dots(element.get('x', 0))
        y = mm_to_dots(element.get('y', 0))

        # 图片数据可能以多种形式存储
        image_data = element.get('imageData', element.get('data', ''))
        if not image_data:
            print(f"[模板渲染] 图片元素缺少图片数据，跳过")
            return None

        # 如果有 GFA 格式数据，直接使用
        gfa_data = element.get('gfaData', '')
        if gfa_data:
            total = gfa_data.get('total', 0)
            bpr = gfa_data.get('bytesPerRow', 0)
            hex_str = gfa_data.get('hex', '')
            if hex_str:
                return f"^FO{x},{y}^GFA,{total},{total},{bpr},{hex_str}^FS"

        print(f"[模板渲染] 图片元素暂不支持自动转换，跳过")
        return None

    @staticmethod
    def extract_variables(template_data: Dict[str, Any]) -> List[str]:
        """
        从模板数据中提取所有变量名

        Args:
            template_data: 模板完整数据

        Returns:
            变量名列表（不含 @ 前缀）
        """
        ext = template_data.get('ext', {})
        available_vars = ext.get('availableVariables', [])

        if available_vars:
            return [v.get('id', '') for v in available_vars if v.get('id')]

        # 回退：从元素 content 中扫描 @变量名
        data = template_data.get('data', {})
        pages = data.get('pages', [])
        vars_set = set()

        for page in pages:
            for element in page.get('elements', []):
                content = element.get('content', '')
                if content.startswith('@'):
                    vars_set.add(content[1:])

        return list(vars_set)
