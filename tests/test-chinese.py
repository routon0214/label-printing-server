#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZT411 中文打印测试 - 简化版
直接打印中文标签，无需多余选择
"""

import sys
from io import BytesIO


def text_to_image_zpl(text, font_size=30):
    """
    将中文文本转换为ZPL图像命令
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # 尝试使用系统中文字体
        font = None
        font_paths = [
            'C:/Windows/Fonts/msyh.ttc',      # 微软雅黑
            'C:/Windows/Fonts/simhei.ttf',    # 黑体
            'C:/Windows/Fonts/simsun.ttc',    # 宋体
            'C:/Windows/Fonts/simkai.ttf',    # 楷体
        ]
        
        for font_path in font_paths:
            try:
                font = ImageFont.truetype(font_path, font_size)
                print(f"使用字体: {font_path}")
                break
            except:
                continue
        
        if font is None:
            print("警告：未找到中文字体，使用默认字体")
            font = ImageFont.load_default()
        
        # 创建临时图像测量文本大小
        temp_img = Image.new('RGB', (1, 1), 'white')
        draw = ImageDraw.Draw(temp_img)
        
        # 获取文本边界
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # 添加边距
        padding = 10
        img_width = text_width + padding * 2
        img_height = text_height + padding * 2
        
        print(f"文本 '{text}' 尺寸: {img_width}x{img_height}")
        
        # 创建黑白图像
        image = Image.new('1', (img_width, img_height), 1)  # 1=白色背景
        draw = ImageDraw.Draw(image)
        
        # 绘制黑色文字
        draw.text((padding, padding - bbox[1]), text, font=font, fill=0)  # 0=黑色
        
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
                        if pixels[x + bit, y] == 0:  # 黑色像素
                            byte_val |= (1 << (7 - bit))
                row_bytes.append(byte_val)
            hex_data.append(''.join([f'{b:02X}' for b in row_bytes]))
        
        hex_string = ''.join(hex_data)
        total_bytes = len(hex_string) // 2
        
        return hex_string, img_width, img_height, bytes_per_row, total_bytes
        
    except ImportError:
        print("\n" + "="*60)
        print("错误：需要安装 Pillow 库来支持中文!")
        print("请运行以下命令安装：")
        print("  pip install Pillow")
        print("="*60 + "\n")
        return None, 0, 0, 0, 0
    except Exception as e:
        print(f"文本转图像失败: {e}")
        import traceback
        traceback.print_exc()
        return None, 0, 0, 0, 0


def create_chinese_test_label():
    """
    创建中文测试标签
    """
    print("\n正在生成中文标签...")
    
    zpl_parts = []
    zpl_parts.append("^XA")  # 标签开始
    zpl_parts.append("^PW800")  # 标签宽度
    zpl_parts.append("^LL600")  # 标签长度
    
    y_pos = 40
    
    # 1. 标题
    print("\n生成: 标题")
    hex_data, w, h, bpr, total = text_to_image_zpl("中文打印测试", font_size=45)
    if hex_data:
        zpl_parts.append(f"^FO50,{y_pos}^GFA,{total},{total},{bpr},{hex_data}^FS")
        y_pos += h + 15
    
    # 分隔线
    zpl_parts.append(f"^FO50,{y_pos}^GB700,3,3^FS")
    y_pos += 20
    
    # 2. 产品名称
    print("生成: 产品名称")
    hex_data, w, h, bpr, total = text_to_image_zpl("产品名称：精密电子元件", font_size=28)
    if hex_data:
        zpl_parts.append(f"^FO50,{y_pos}^GFA,{total},{total},{bpr},{hex_data}^FS")
        y_pos += h + 12
    
    # 3. 产品型号
    print("生成: 产品型号")
    hex_data, w, h, bpr, total = text_to_image_zpl("型号：ZX-2024-PRO", font_size=25)
    if hex_data:
        zpl_parts.append(f"^FO50,{y_pos}^GFA,{total},{total},{bpr},{hex_data}^FS")
        y_pos += h + 12
    
    # 4. 序列号（英文数字）
    zpl_parts.append(f"^FO50,{y_pos}^A0N,22,22^FDSN: 20251015-001^FS")
    y_pos += 35
    
    # 5. 生产日期
    print("生成: 生产日期")
    hex_data, w, h, bpr, total = text_to_image_zpl("日期：2025-10-15", font_size=25)
    if hex_data:
        zpl_parts.append(f"^FO50,{y_pos}^GFA,{total},{total},{bpr},{hex_data}^FS")
        y_pos += h + 12
    
    # 6. 质检员
    print("生成: 质检员")
    hex_data, w, h, bpr, total = text_to_image_zpl("质检：李四", font_size=25)
    if hex_data:
        zpl_parts.append(f"^FO50,{y_pos}^GFA,{total},{total},{bpr},{hex_data}^FS")
        y_pos += h + 20
    
    # 7. 条形码
    zpl_parts.append(f"^FO50,{y_pos}^BY2,3,70^BCN,70,N,N,N^FD20251015001^FS")
    
    # 8. 二维码
    zpl_parts.append(f"^FO550,{y_pos - 50}^BQN,2,5^FDQA,20251015001^FS")
    
    # 9. 二维码说明
    print("生成: 扫码提示")
    hex_data, w, h, bpr, total = text_to_image_zpl("扫码查询", font_size=20)
    if hex_data:
        zpl_parts.append(f"^FO560,{y_pos + 80}^GFA,{total},{total},{bpr},{hex_data}^FS")
    
    zpl_parts.append("^XZ")  # 标签结束
    
    print("\n标签生成完成!")
    return '\n'.join(zpl_parts)


def print_to_zt411(zpl_code):
    """
    发送到ZT411打印机
    """
    try:
        import win32print
        
        # 获取打印机列表
        printers = [printer[2] for printer in win32print.EnumPrinters(2)]
        
        # 查找ZT411打印机
        zt411_printer = None
        for printer in printers:
            if "ZT411" in printer or "zt411" in printer.lower():
                zt411_printer = printer
                break
        
        # 如果没找到ZT411，显示列表让用户选择
        if not zt411_printer:
            print("\n未自动找到ZT411打印机，请选择：")
            for i, printer in enumerate(printers, 1):
                print(f"{i}. {printer}")
            
            choice = input("\n请输入打印机编号: ").strip()
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(printers):
                    zt411_printer = printers[idx]
        
        if not zt411_printer:
            print("错误：未选择打印机")
            return False
        
        print(f"\n使用打印机: {zt411_printer}")
        
        # 打开打印机
        printer_handle = win32print.OpenPrinter(zt411_printer)
        
        # 开始打印作业
        job_info = ("Chinese Label Test", None, "RAW")
        win32print.StartDocPrinter(printer_handle, 1, job_info)
        win32print.StartPagePrinter(printer_handle)
        
        # 发送ZPL命令
        print("正在发送打印命令...")
        win32print.WritePrinter(printer_handle, zpl_code.encode('utf-8'))
        
        # 结束打印
        win32print.EndPagePrinter(printer_handle)
        win32print.EndDocPrinter(printer_handle)
        win32print.ClosePrinter(printer_handle)
        
        print("\n[OK] 打印命令已发送!")
        print("请检查打印机输出。")
        return True
        
    except ImportError:
        print("\n" + "="*60)
        print("错误：需要安装 pywin32 库!")
        print("请运行以下命令安装：")
        print("  pip install pywin32")
        print("="*60 + "\n")
        return False
    except Exception as e:
        print(f"\n[ERROR] 打印失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """
    主函数
    """
    print("=" * 70)
    print("ZT411 中文打印测试")
    print("=" * 70)
    
    # 生成中文标签
    zpl_code = create_chinese_test_label()
    
    if not zpl_code or "^GFA" not in zpl_code:
        print("\n错误：中文标签生成失败!")
        print("请确保已安装 Pillow 库: pip install Pillow")
        return
    
    # 显示ZPL代码（前500字符）
    print("\n" + "=" * 70)
    print("ZPL代码预览（前500字符）:")
    print("-" * 70)
    print(zpl_code[:500] + "...")
    print("-" * 70)
    print(f"总长度: {len(zpl_code)} 字符")
    
    # 确认打印
    print("\n" + "=" * 70)
    confirm = input("\n确认打印到ZT411? (y/n，默认y): ").strip().lower()
    
    if confirm == 'n':
        print("\n已取消打印")
        
        # 询问是否保存
        save = input("\n是否保存ZPL代码到文件? (y/n): ").strip().lower()
        if save == 'y':
            filename = "chinese_label.zpl"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(zpl_code)
            print(f"\n已保存到: {filename}")
        return
    
    # 打印
    success = print_to_zt411(zpl_code)
    
    if success:
        print("\n" + "=" * 70)
        print("测试完成!")
        print("=" * 70)
    else:
        # 保存到文件作为备选
        filename = "chinese_label.zpl"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(zpl_code)
        print(f"\nZPL代码已保存到: {filename}")
        print("您可以使用其他工具发送此文件到打印机")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n程序已取消")
    except Exception as e:
        print(f"\n发生错误: {e}")
        import traceback
        traceback.print_exc()

