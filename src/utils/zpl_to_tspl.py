#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZPL → TSPL 转换器
将 Zebra ZPL 指令转换为 TSC TSPL 指令（用于得力 DL-825T 等 TSC 打印机）

TSPL 参考: https://www.tscprinters.com/TC/tsc/_img/_Drive/tspl_tspl2_programming_0702.pdf

核心差异:
  ZPL 使用 dots (1/203 inch) 作为坐标单位
  TSPL 使用 dots (1/203 inch) 作为坐标单位 — 实际上两者坐标体系相同！
  但 TSPL SIZE 使用 mm
"""

import re
import io
import struct
import tempfile
import os

DPI = 203
DOTS_PER_MM = DPI / 25.4  # ≈ 7.992


class ZPLToTSPLConverter:
    """ZPL 指令 → TSPL 指令转换器"""

    # TSPL 字体映射
    FONT_MAP = {
        # (height_dots, width_dots) → (tspl_font_name, x_mul, y_mul)
        # ZPL ^A0N,h,w → TSPL TEXT x,y,"font",0,xmul,ymul,"text"
    }

    # TSPL 条码类型映射
    BARCODE_MAP = {
        'BC': '128',      # Code 128
        'B3': '39',       # Code 39
        'BE': 'EAN13',    # EAN-13
        'BY': '128',      # default
    }

    def __init__(self, label_width_mm=100, label_height_mm=80, gap_mm=2, density=8):
        """
        Args:
            label_width_mm: 标签宽度 (mm)，默认 100
            label_height_mm: 标签高度 (mm)，默认 80
            gap_mm: 标签间距 (mm)，默认 2
            density: 打印浓度 (1-15)，默认 8
        """
        self.label_width_mm = label_width_mm
        self.label_height_mm = label_height_mm
        self.gap_mm = gap_mm
        self.density = density
        self._temp_files = []

    def convert(self, zpl_code: str) -> bytes:
        """
        将 ZPL 代码转换为 TSPL 指令

        Args:
            zpl_code: ZPL 指令字符串

        Returns:
            TSPL 指令的 bytes（GBK 编码，可直接发送到 TSC 打印机）
        """
        self._temp_files = []
        try:
            tspl_lines = self._parse_and_convert(zpl_code)
            return ('\r\n'.join(tspl_lines) + '\r\n').encode('gbk', errors='replace')
        finally:
            self._cleanup_temp_files()

    def _parse_and_convert(self, zpl_code: str) -> list:
        """解析 ZPL 并生成 TSPL 行"""
        zpl = zpl_code.strip()
        lines = []

        # ── 计算坐标缩放比例 ──
        # ZPL 模板设计尺寸可能不同于物理标签尺寸，需要缩放
        pw_match = re.search(r'\^PW(\d+)', zpl)
        ll_match = re.search(r'\^LL(\d+)', zpl)
        design_w_dots = int(pw_match.group(1)) if pw_match else int(self.label_width_mm * DOTS_PER_MM)
        design_h_dots = int(ll_match.group(1)) if ll_match else int(self.label_height_mm * DOTS_PER_MM)
        physical_w_dots = int(self.label_width_mm * DOTS_PER_MM)
        physical_h_dots = int(self.label_height_mm * DOTS_PER_MM)
        self._scale_x = physical_w_dots / design_w_dots
        self._scale_y = physical_h_dots / design_h_dots

        # ── TSPL 头部 ──
        # 使用构造参数中的物理标签尺寸
        lines.append(f'SIZE {self.label_width_mm} mm, {self.label_height_mm} mm')
        lines.append(f'GAP {self.gap_mm} mm, 0 mm')
        lines.append('CLS')
        # 注意：不添加 DENSITY/SPEED/DIRECTION/REFERENCE
        # 得力 825T 使用出厂默认即可正常打印

        # ── 按 ^FO/^FT 分割成字段块 ──
        # 使用 ^FS 作为字段结束标志
        fields = self._split_zpl_fields(zpl)

        for field in fields:
            tspl_cmd = self._convert_field(field)
            if tspl_cmd:
                lines.append(tspl_cmd)

        # ── TSPL 尾部 ──
        lines.append('PRINT 1,1')
        # 注意：不添加 END，得力 825T 不需要

        return lines

    def _split_zpl_fields(self, zpl_code: str) -> list:
        """将 ZPL 按 ^FS 分割成字段"""
        # 移除 ^XA / ^XZ
        zpl = re.sub(r'\^XA|\^XZ', '', zpl_code)
        zpl = re.sub(r'\^PW\d+|\^LL\d+', '', zpl)

        # 按 ^FS 分割
        parts = zpl.split('^FS')
        fields = []
        for p in parts:
            p = p.strip()
            if p:
                fields.append(p)
        return fields

    def _convert_field(self, field: str) -> str:
        """转换单个 ZPL 字段为 TSPL 指令"""
        # 条码
        bc_match = re.search(r'\^(B[CE3Y]\w*),?\s*(.*)', field)
        if bc_match:
            return self._convert_barcode(bc_match.group(1), bc_match.group(2), field)

        # QR 码
        bq_match = re.search(r'\^BQ(N)?,(\d+),(\d+)', field)
        if bq_match:
            return self._convert_qrcode(field, bq_match)

        # GFA 图像（中文文本渲染的位图）
        gfa_match = re.search(r'\^GFA,(\d+),(\d+),(\d+),([0-9A-Fa-f,]+)', field)
        if gfa_match:
            return self._convert_gfa_image(field, gfa_match)

        # 图形框 / 线条
        gb_match = re.search(r'\^GB(\d+),(\d+),(\d+)', field)
        if gb_match:
            w = int(gb_match.group(1))
            h = int(gb_match.group(2))
            t = int(gb_match.group(3))
            x, y = self._get_position(field)
            if w == t or h == t:  # 线条
                return f'BAR {x},{y},{x + w},{y + h}'
            else:
                return f'BOX {x},{y},{w},{h},{t}'

        # 文本
        text_data = self._extract_text_data(field)
        if text_data:
            return self._convert_text(field, text_data)

        return ''

    def _get_position(self, field: str) -> tuple:
        """提取位置坐标 (x, y)，并缩放到物理标签尺寸"""
        # ^FO{x},{y}
        fo_match = re.search(r'\^FO(\d+),(\d+)', field)
        if fo_match:
            x = int(fo_match.group(1))
            y = int(fo_match.group(2))
            return (int(x * self._scale_x), int(y * self._scale_y))

        # ^FT{x},{y}
        ft_match = re.search(r'\^FT(\d+),(\d+)', field)
        if ft_match:
            x = int(ft_match.group(1))
            y = int(ft_match.group(2))
            return (int(x * self._scale_x), int(y * self._scale_y))

        return (10, 10)

    def _extract_text_data(self, field: str) -> str:
        """提取 ^FD 中的文本"""
        fd_match = re.search(r'\^FD(.+)', field)
        if fd_match:
            text = fd_match.group(1).strip()
            # 移除末尾可能的 ZPL 指令碎片
            text = re.sub(r'\^[A-Z0-9].*$', '', text)
            return text
        return ''

    def _extract_font_info(self, field: str) -> tuple:
        """提取字体信息 (height_dots, width_dots)，并缩放到物理标签"""
        # ^A0N,h,w 或 ^A0,h,w
        a_match = re.search(r'\^A0N?,?(\d+),?(\d+)?', field)
        if a_match:
            h = int(a_match.group(1)) if a_match.group(1) else 24
            w = int(a_match.group(2)) if a_match.group(2) else int(h * 0.6)
            return (max(8, int(h * self._scale_y)), max(6, int(w * self._scale_x)))
        return (24, 16)

    def _convert_text(self, field: str, text: str) -> str:
        """转换文本字段"""
        x, y = self._get_position(field)
        font_h, font_w = self._extract_font_info(field)

        # 检测是否包含中文
        has_chinese = bool(re.search(r'[\u4e00-\u9fff]', text))

        if has_chinese:
            # 使用 TSC 中文字体 TSS24.BF2
            # TEXT x,y,"font",rotation,xmul,ymul,"text"
            x_mul = max(1, font_w // 16)
            y_mul = max(1, font_h // 24)
            # 转义双引号
            text_escaped = text.replace('"', '""')
            return f'TEXT {x},{y},"TSS24.BF2",0,{x_mul},{y_mul},"{text_escaped}"'
        else:
            # 选择最接近的 TSPL 内置字体
            font_name, x_mul, y_mul = self._choose_builtin_font(font_h, font_w)
            text_escaped = text.replace('"', '""')
            return f'TEXT {x},{y},"{font_name}",0,{x_mul},{y_mul},"{text_escaped}"'

    def _choose_builtin_font(self, h_dots: int, w_dots: int) -> tuple:
        """选择最接近的 TSPL 内置字体"""
        # TSPL 内置字体:
        # "1": 8×12  dots,  "2": 12×20 dots,  "3": 16×24 dots
        # "4": 24×32 dots,  "5": 32×48 dots
        fonts = {
            '1': (8, 12),
            '2': (12, 20),
            '3': (16, 24),
            '4': (24, 32),
            '5': (32, 48),
        }

        best_name = '3'
        best_score = float('inf')

        for name, (fh, fw) in fonts.items():
            x_mul = max(1, round(w_dots / fw))
            y_mul = max(1, round(h_dots / fh))
            total_h = y_mul * fh
            total_w = x_mul * fw
            score = abs(total_h - h_dots) + abs(total_w - w_dots)
            if score < best_score:
                best_score = score
                best_name = name
                best_x = x_mul
                best_y = y_mul

        # 避免乘数过大
        best_y = min(best_y, 10)
        best_x = min(best_x, 10)

        return (best_name, best_x, best_y)

    def _convert_barcode(self, bc_type: str, bc_params: str, field: str) -> str:
        """转换条码"""
        x, y = self._get_position(field)

        # 提取条码高度
        h_match = re.search(r'(\d+)', bc_params)
        height = int(h_match.group(1)) if h_match else 50
        height = max(20, int(height * self._scale_y))  # 缩放到物理标签

        # 提取条码数据
        fd_match = re.search(r'\^FD([^\\^]+)', field)
        data = fd_match.group(1).strip() if fd_match else ''

        # 映射条码类型
        tspl_type = self.BARCODE_MAP.get(bc_type[:2], '128')

        # 窄/宽比例
        narrow = 2
        wide = 4

        # BARCODE x,y,"type",height,readable,rotation,narrow,wide,"data"
        return f'BARCODE {x},{y},"{tspl_type}",{height},1,0,{narrow},{wide},"{data}"'

    def _convert_qrcode(self, field: str, bq_match) -> str:
        """转换 QR 码"""
        x, y = self._get_position(field)

        # ^BQN,2,10 → orientation=N, model=2, magnification=10
        ecc = 'M'  # 简化处理
        cell_size = int(bq_match.group(3)) if bq_match.group(3) else 5

        # 提取数据（ZPL QR 码 ^FD 格式: QA,<data> 或 MM,<data>）
        fd_match = re.search(r'\^FD[A-Z]{0,2},?\s*(.+)', field)
        data = fd_match.group(1).strip() if fd_match else ''

        # TSPL QRCODE 数据需要在双引号内，内部双引号需转义为 ""
        data_escaped = data.replace('"', '""')

        # QRCODE x,y,ECC,cellWidth,mode,rotation,"data"
        return f'QRCODE {x},{y},{ecc},{cell_size},M,0,"{data_escaped}"'

    def _convert_gfa_image(self, field: str, gfa_match) -> str:
        """将 ZPL ^GFA 图像转换为 TSPL DOWNLOAD + PUTBMP 指令
        
        DL-825T 不支持 TSPL BITMAP 命令，必须使用 DOWNLOAD + PUTBMP
        """
        x, y = self._get_position(field)

        byte_count = int(gfa_match.group(1))
        bytes_per_row = int(gfa_match.group(2))
        row_count = int(gfa_match.group(3))
        hex_data = gfa_match.group(4)

        # ZPL GFA 数据格式：hex 压缩（Z64）
        # 每行用逗号分隔，行内可能有大写字母开头的压缩编码
        raw_rows = self._decode_gfa_rows(hex_data, bytes_per_row)

        if not raw_rows:
            return ''
        # 浏览器生成的 GFA 可能省略尾部全零行，补齐
        # 但若补齐后总数据量超过 500KB，说明 GFA 参数有误，跳过补齐
        total_padded_bytes = row_count * bytes_per_row
        if len(raw_rows) < row_count and total_padded_bytes <= 500000:
            while len(raw_rows) < row_count:
                raw_rows.append(b'\x00' * bytes_per_row)
        else:
            # GFA 参数可能不准确（如异常大的尺寸），使用实际解码行数
            row_count = len(raw_rows)

        # 构建完整位图数据（用于尺寸计算，非实际传输）
        all_bytes = b''
        for row in raw_rows[:row_count]:
            if len(row) < bytes_per_row:
                row = row + b'\x00' * (bytes_per_row - len(row))
            all_bytes += row[:bytes_per_row]

        # TSPL DOWNLOAD + PUTBMP（DL-825T 不支持 BITMAP）
        # 关键限制：打印机每个作业只能有 1 个 DOWNLOAD 图像在内存
        # 解决：复用同一文件名 "IMG"，每块 DOWNLOAD→PUTBMP 后覆盖
        MAX_HEX_PER_DL = 50000  # 每次 DOWNLOAD 最大 hex 字符数
        max_rows = max(1, MAX_HEX_PER_DL // (bytes_per_row * 2))
        cmds = []

        for start_row in range(0, row_count, max_rows):
            end_row = min(start_row + max_rows, row_count)
            sub_rows = raw_rows[start_row:end_row]
            sub_height = end_row - start_row

            sub_bytes = b''
            for row in sub_rows:
                if len(row) < bytes_per_row:
                    row = row + b'\x00' * (bytes_per_row - len(row))
                sub_bytes += row[:bytes_per_row]

            hex_encoded = sub_bytes.hex().upper()
            # 所有块复用同一个文件名，避免内存耗尽
            download_cmd = f'DOWNLOAD "IMG",{bytes_per_row},{sub_height},{hex_encoded}'
            sub_y = y + start_row
            putbmp_cmd = f'PUTBMP {x},{sub_y},"IMG"'
            cmds.append(download_cmd)
            cmds.append(putbmp_cmd)

        return '\r\n'.join(cmds)

    def _decode_gfa_rows(self, hex_data: str, bytes_per_row: int) -> list:
        """解码 ZPL GFA 数据为原始字节行
        
        自动检测编码格式：
        - 浏览器生成的 GFA 为纯十六进制（含逗号分隔行）
        - ZPL 原生生成的 GFA 可能使用 Z64 压缩（大写字母 G-Y 为压缩标记）
        
        当数据为连续十六进制（无逗号分隔）时，按 bytes_per_row 分割成多行。
        """
        rows_raw = hex_data.split(',')
        decoded_rows = []

        for row_str in rows_raw:
            row_str = row_str.strip()
            if not row_str:
                continue

            # 检测：如果包含 G-Y（排除纯十六进制 A-F），则为 Z64 压缩
            has_z64 = any(c in row_str for c in 'GHIJKLMNOPQRSTUVWY')

            if has_z64:
                row_data = self._decode_z64_row(row_str, bytes_per_row)
            else:
                # 浏览器生成的 GFA：连续十六进制（可能跨越所有行）
                row_data = self._decode_raw_hex_full(row_str)

            if row_data:
                decoded_rows.append(row_data)

        # 如果只有一行数据但长度超过 bytes_per_row，按行分割
        if len(decoded_rows) == 1 and len(decoded_rows[0]) > bytes_per_row:
            full_data = decoded_rows[0]
            decoded_rows = []
            for offset in range(0, len(full_data), bytes_per_row):
                chunk = full_data[offset:offset + bytes_per_row]
                decoded_rows.append(chunk)

        return decoded_rows

    def _decode_raw_hex_full(self, row_str: str) -> bytes:
        """纯十六进制原始数据解码（不限长度，全部解码）"""
        row_bytes = bytearray()
        i = 0
        while i + 1 < len(row_str):
            try:
                byte_val = int(row_str[i:i + 2], 16)
                row_bytes.append(byte_val)
                i += 2
            except (ValueError, IndexError):
                i += 1
        return bytes(row_bytes)

    def _decode_z64_row(self, row_str: str, bytes_per_row: int) -> bytes:
        """Z64 压缩格式解码"""
        row_bytes = bytearray()
        i = 0
        while i < len(row_str) and len(row_bytes) < bytes_per_row:
            if 'A' <= row_str[i] <= 'Z' and i + 1 < len(row_str):
                repeat_char = row_str[i]
                i += 1
                # 读取后续的十六进制数字作为重复次数
                repeat_hex = ''
                while i < len(row_str) and row_str[i] not in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' and row_str[i] != ',':
                    val = row_str[i]
                    if val in '0123456789ABCDEF':
                        repeat_hex += val
                        i += 1
                    else:
                        break
                if repeat_hex:
                    repeat_count = int(repeat_hex, 16)
                    if repeat_char == 'G':
                        row_bytes.extend(b'\x00' * repeat_count)
                    elif repeat_char == 'H':
                        row_bytes.extend(b'\xFF' * repeat_count)
                    else:
                        byte_val = ord(repeat_char) - ord('G')
                        if 0 <= byte_val <= 255:
                            row_bytes.extend(bytes([byte_val]) * repeat_count)
                else:
                    byte_val = ord(repeat_char) - ord('G')
                    if 0 <= byte_val <= 255:
                        row_bytes.append(byte_val)
            elif row_str[i] in '0123456789abcdefABCDEF' and i + 1 < len(row_str) and row_str[i + 1] in '0123456789abcdefABCDEF':
                try:
                    byte_val = int(row_str[i:i + 2], 16)
                    row_bytes.append(byte_val)
                    i += 2
                except (ValueError, IndexError):
                    i += 1
            else:
                i += 1
        return bytes(row_bytes)

    def _cleanup_temp_files(self):
        """清理临时文件"""
        for path in self._temp_files:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except:
                pass


def zpl_to_tspl(zpl_code: str, label_w_mm=60, label_h_mm=40, gap_mm=2) -> bytes:
    """便捷函数：ZPL → TSPL"""
    converter = ZPLToTSPLConverter(
        label_width_mm=label_w_mm,
        label_height_mm=label_h_mm,
        gap_mm=gap_mm
    )
    return converter.convert(zpl_code)
