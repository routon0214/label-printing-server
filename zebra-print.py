#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
斑马打印机打印标签示例
支持网络打印机和USB打印机两种方式
"""

import socket
import sys
from io import BytesIO


def text_to_image_zpl(text, font_size=30, dpi=300):
    """
    将中文文本转换为ZPL图像命令
    :param text: 要转换的文本
    :param font_size: 字体大小
    :param dpi: 打印机DPI（ZT411是300dpi）
    :return: ZPL图像命令和图像宽度、高度
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # 创建临时图像来测量文本大小
        temp_img = Image.new('1', (1, 1), 1)
        draw = ImageDraw.Draw(temp_img)
        
        # 尝试使用系统中文字体
        try:
            # Windows常见中文字体
            font_paths = [
                'C:/Windows/Fonts/msyh.ttc',  # 微软雅黑
                'C:/Windows/Fonts/simhei.ttf',  # 黑体
                'C:/Windows/Fonts/simsun.ttc',  # 宋体
                'C:/Windows/Fonts/simkai.ttf',  # 楷体
            ]
            font = None
            for font_path in font_paths:
                try:
                    font = ImageFont.truetype(font_path, font_size)
                    break
                except:
                    continue
            
            if font is None:
                # 使用默认字体
                font = ImageFont.load_default()
        except:
            font = ImageFont.load_default()
        
        # 获取文本边界框
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # 添加边距
        padding = 5
        img_width = text_width + padding * 2
        img_height = text_height + padding * 2
        
        # 创建图像（1位黑白）
        image = Image.new('1', (img_width, img_height), 1)  # 白色背景
        draw = ImageDraw.Draw(image)
        
        # 绘制文本（黑色）
        draw.text((padding, padding - bbox[1]), text, font=font, fill=0)
        
        # 转换为ZPL十六进制格式
        zpl_hex = image_to_zpl_hex(image)
        
        return zpl_hex, img_width, img_height
        
    except ImportError:
        print("警告：需要安装 Pillow 库来支持中文显示")
        print("请运行：pip install Pillow")
        return None, 0, 0
    except Exception as e:
        print(f"文本转图像失败：{e}")
        return None, 0, 0


def image_to_zpl_hex(image):
    """
    将PIL图像转换为ZPL十六进制格式
    :param image: PIL Image对象（必须是1位黑白图像）
    :return: ZPL十六进制字符串
    """
    # 确保是1位图像
    if image.mode != '1':
        image = image.convert('1')
    
    width, height = image.size
    
    # 计算每行需要的字节数（向上取整到8的倍数）
    bytes_per_row = (width + 7) // 8
    
    # 转换图像数据为十六进制
    hex_data = []
    pixels = image.load()
    
    for y in range(height):
        row_bytes = []
        for x in range(0, width, 8):
            byte = 0
            for bit in range(8):
                if x + bit < width:
                    # PIL中0是黑色，1是白色；ZPL中需要反转
                    pixel = pixels[x + bit, y]
                    if pixel == 0:  # 黑色
                        byte |= (1 << (7 - bit))
            row_bytes.append(byte)
        
        # 转换为十六进制字符串
        hex_line = ''.join([f'{b:02X}' for b in row_bytes])
        hex_data.append(hex_line)
    
    return ''.join(hex_data)


class ZebraPrinter:
    """斑马打印机类"""
    
    def __init__(self, printer_ip=None, printer_port=9100):
        """
        初始化打印机
        :param printer_ip: 打印机IP地址（网络打印机）
        :param printer_port: 打印机端口，默认9100
        """
        self.printer_ip = printer_ip
        self.printer_port = printer_port
    
    def print_via_network(self, zpl_code):
        """
        通过网络发送ZPL命令到打印机
        :param zpl_code: ZPL打印命令
        :return: 是否成功
        """
        try:
            # 创建socket连接
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            
            # 连接到打印机
            print(f"正在连接打印机 {self.printer_ip}:{self.printer_port}...")
            sock.connect((self.printer_ip, self.printer_port))
            
            # 发送ZPL命令
            print("发送打印命令...")
            sock.sendall(zpl_code.encode('utf-8'))
            
            # 关闭连接
            sock.close()
            print("打印命令发送成功！")
            return True
            
        except socket.timeout:
            print(f"错误：连接打印机超时")
            return False
        except socket.error as e:
            print(f"错误：连接打印机失败 - {e}")
            return False
        except Exception as e:
            print(f"错误：{e}")
            return False
    
    def print_via_usb(self, zpl_code, printer_name="ZDesigner"):
        """
        通过USB/本地打印机发送ZPL命令（Windows）
        :param zpl_code: ZPL打印命令
        :param printer_name: Windows中的打印机名称
        :return: 是否成功
        """
        try:
            import win32print
            import win32ui
            
            # 获取打印机句柄
            printer_handle = win32print.OpenPrinter(printer_name)
            
            # 开始打印作业
            job_info = ("Zebra Label", None, "RAW")
            job_id = win32print.StartDocPrinter(printer_handle, 1, job_info)
            win32print.StartPagePrinter(printer_handle)
            
            # 发送ZPL命令
            win32print.WritePrinter(printer_handle, zpl_code.encode('utf-8'))
            
            # 结束打印
            win32print.EndPagePrinter(printer_handle)
            win32print.EndDocPrinter(printer_handle)
            win32print.ClosePrinter(printer_handle)
            
            print("打印命令发送成功！")
            return True
            
        except ImportError:
            print("错误：需要安装 pywin32 库")
            print("请运行：pip install pywin32")
            return False
        except Exception as e:
            print(f"错误：{e}")
            return False


def create_simple_label():
    """
    创建一个简单的标签ZPL代码
    """
    zpl = """
^XA
^FO50,50^ADN,36,20^FD产品标签^FS
^FO50,100^GB700,3,3^FS
^FO50,120^ADN,18,10^FD产品名称：^FS
^FO200,120^ADN,18,10^FD测试产品A^FS
^FO50,150^ADN,18,10^FD产品编号：^FS
^FO200,150^ADN,18,10^FDPROD-12345^FS
^FO50,180^ADN,18,10^FD生产日期：^FS
^FO200,180^ADN,18,10^FD2025-10-15^FS
^FO50,220^BY3
^BCN,100,Y,N,N
^FD123456789012^FS
^XZ
"""
    return zpl.strip()


def create_qrcode_label():
    """
    创建一个带二维码的标签ZPL代码
    """
    zpl = """
^XA
^FO50,50^ADN,30,15^FD产品信息^FS
^FO50,100^GB600,2,2^FS
^FO50,120^ADN,18,10^FD产品：测试产品B^FS
^FO50,150^ADN,18,10^FD编号：PROD-67890^FS
^FO50,180^ADN,18,10^FD日期：2025-10-15^FS
^FO400,120^BQN,2,6
^FDQA,https://www.example.com/product/67890^FS
^FO400,320^ADN,14,7^FD扫描查看详情^FS
^XZ
"""
    return zpl.strip()


def create_address_label():
    """
    创建一个地址标签ZPL代码
    """
    zpl = """
^XA
^FO50,30^ADN,24,12^FD收件人信息^FS
^FO50,70^GB700,2,2^FS
^FO50,90^ADN,20,10^FD收件人：张三^FS
^FO50,120^ADN,20,10^FD电话：138-0000-0000^FS
^FO50,150^ADN,18,10^FD地址：北京市朝阳区某某街道^FS
^FO50,180^ADN,18,10^FD      某某小区1号楼101室^FS
^FO50,220^ADN,18,10^FD邮编：100000^FS
^FO50,270^BY2
^BCN,80,Y,N,N
^FD100000^FS
^XZ
"""
    return zpl.strip()


def create_zt411_high_res_label():
    """
    创建一个针对ZT411-300dpi优化的高分辨率标签
    适合打印精细内容，如小字体和详细信息
    """
    zpl = """
^XA
^PW800
^LL600
^FO50,30^A0N,40,40^FD高分辨率产品标签^FS
^FO50,80^GB700,3,3^FS
^FO50,100^A0N,25,25^FD产品名称：^FS
^FO200,100^A0N,25,25^FD精密电子元件^FS
^FO50,135^A0N,20,20^FD产品型号：^FS
^FO200,135^A0N,20,20^FDZX-2024-PRO^FS
^FO50,165^A0N,20,20^FD序列号：^FS
^FO200,165^A0N,20,20^FDSN20251015001^FS
^FO50,195^A0N,20,20^FD生产日期：^FS
^FO200,195^A0N,20,20^FD2025-10-15^FS
^FO50,225^A0N,20,20^FD质检员：^FS
^FO200,225^A0N,20,20^FD李四^FS
^FO50,270^BY2,3,120
^BCN,120,Y,N,N
^FDSN20251015001^FS
^FO550,270^BQN,2,5
^FDQA,SN20251015001^FS
^FO550,420^A0N,16,16^FD扫码查询^FS
^XZ
"""
    return zpl.strip()


def create_zt411_asset_label():
    """
    创建一个资产标签（适合ZT411-300dpi）
    """
    zpl = """
^XA
^PW800
^LL400
^FO50,30^A0N,35,35^FD资产标签^FS
^FO50,75^GB700,2,2^FS
^FO50,90^A0N,22,22^FD资产名称：台式电脑^FS
^FO50,120^A0N,22,22^FD资产编号：IT-2025-0001^FS
^FO50,150^A0N,22,22^FD使用部门：技术部^FS
^FO50,180^A0N,22,22^FD责任人：王五^FS
^FO50,210^A0N,22,22^FD登记日期：2025-10-15^FS
^FO480,90^BQN,2,6
^FDQA,IT-2025-0001^FS
^XZ
"""
    return zpl.strip()


def create_chinese_label():
    """
    创建支持中文的产品标签（将中文转换为图像）
    """
    try:
        zpl_parts = ["^XA", "^PW800", "^LL600"]
        
        y_pos = 30
        
        # 标题
        title_hex, title_w, title_h = text_to_image_zpl("产品标签", font_size=40)
        if title_hex:
            bytes_per_row = (title_w + 7) // 8
            zpl_parts.append(f"^FO50,{y_pos}^GFA,{len(title_hex)//2},{len(title_hex)//2},{bytes_per_row},{title_hex}^FS")
            y_pos += title_h + 10
        
        # 分隔线
        zpl_parts.append(f"^FO50,{y_pos}^GB700,3,3^FS")
        y_pos += 15
        
        # 产品名称
        label1_hex, label1_w, label1_h = text_to_image_zpl("产品名称：精密电子元件", font_size=25)
        if label1_hex:
            bytes_per_row = (label1_w + 7) // 8
            zpl_parts.append(f"^FO50,{y_pos}^GFA,{len(label1_hex)//2},{len(label1_hex)//2},{bytes_per_row},{label1_hex}^FS")
            y_pos += label1_h + 10
        
        # 产品型号
        label2_hex, label2_w, label2_h = text_to_image_zpl("产品型号：ZX-2024-PRO", font_size=22)
        if label2_hex:
            bytes_per_row = (label2_w + 7) // 8
            zpl_parts.append(f"^FO50,{y_pos}^GFA,{len(label2_hex)//2},{len(label2_hex)//2},{bytes_per_row},{label2_hex}^FS")
            y_pos += label2_h + 10
        
        # 序列号（英文可以直接使用）
        zpl_parts.append(f"^FO50,{y_pos}^A0N,20,20^FD序列号: SN20251015001^FS")
        y_pos += 30
        
        # 生产日期
        label3_hex, label3_w, label3_h = text_to_image_zpl("生产日期：2025-10-15", font_size=22)
        if label3_hex:
            bytes_per_row = (label3_w + 7) // 8
            zpl_parts.append(f"^FO50,{y_pos}^GFA,{len(label3_hex)//2},{len(label3_hex)//2},{bytes_per_row},{label3_hex}^FS")
            y_pos += label3_h + 10
        
        # 质检员
        label4_hex, label4_w, label4_h = text_to_image_zpl("质检员：李四", font_size=22)
        if label4_hex:
            bytes_per_row = (label4_w + 7) // 8
            zpl_parts.append(f"^FO50,{y_pos}^GFA,{len(label4_hex)//2},{len(label4_hex)//2},{bytes_per_row},{label4_hex}^FS")
            y_pos += label4_h + 15
        
        # 条形码
        zpl_parts.append(f"^FO50,{y_pos}^BY2,3,80^BCN,80,Y,N,N^FDSN20251015001^FS")
        
        # 二维码
        zpl_parts.append(f"^FO550,{y_pos}^BQN,2,5^FDQA,SN20251015001^FS")
        
        # 扫码提示
        qr_label_hex, qr_label_w, qr_label_h = text_to_image_zpl("扫码查询", font_size=18)
        if qr_label_hex:
            bytes_per_row = (qr_label_w + 7) // 8
            zpl_parts.append(f"^FO550,{y_pos + 130}^GFA,{len(qr_label_hex)//2},{len(qr_label_hex)//2},{bytes_per_row},{qr_label_hex}^FS")
        
        zpl_parts.append("^XZ")
        
        return '\n'.join(zpl_parts)
        
    except Exception as e:
        print(f"创建中文标签失败：{e}")
        # 返回一个基本的英文标签作为备选
        return create_simple_label()


def list_available_printers():
    """列出系统中可用的打印机（Windows）"""
    try:
        import win32print
        
        printers = [printer[2] for printer in win32print.EnumPrinters(2)]
        print("\n系统中可用的打印机：")
        for i, printer in enumerate(printers, 1):
            default = win32print.GetDefaultPrinter()
            marker = " (默认)" if printer == default else ""
            print(f"{i}. {printer}{marker}")
        return printers
    except ImportError:
        print("需要安装 pywin32 库才能列出打印机")
        return []
    except Exception as e:
        print(f"获取打印机列表失败：{e}")
        return []


def main():
    """主函数"""
    print("=" * 60)
    print("斑马打印机打印标签示例")
    print("=" * 60)
    
    # 选择标签类型
    print("\n请选择要打印的标签类型：")
    print("1. 简单产品标签（带条形码）")
    print("2. 二维码标签")
    print("3. 地址标签")
    print("4. 高分辨率产品标签（ZT411优化）")
    print("5. 资产标签（ZT411优化）")
    print("6. 中文标签（图像方式，推荐）⭐")
    
    try:
        choice = input("\n请输入选项 (1-6): ").strip()
        
        if choice == "1":
            zpl_code = create_simple_label()
        elif choice == "2":
            zpl_code = create_qrcode_label()
        elif choice == "3":
            zpl_code = create_address_label()
        elif choice == "4":
            zpl_code = create_zt411_high_res_label()
        elif choice == "5":
            zpl_code = create_zt411_asset_label()
        elif choice == "6":
            print("\n正在生成中文标签...")
            zpl_code = create_chinese_label()
        else:
            print("无效的选项！")
            return
        
        print("\nZPL代码：")
        print("-" * 60)
        print(zpl_code)
        print("-" * 60)
        
        # 选择打印方式
        print("\n请选择打印方式：")
        print("1. 网络打印机（通过IP地址）")
        print("2. USB/本地打印机（Windows）")
        print("3. 仅生成ZPL代码（不打印）")
        
        method = input("\n请输入选项 (1-3): ").strip()
        
        if method == "1":
            # 网络打印机
            printer_ip = input("请输入打印机IP地址: ").strip()
            printer_port = input("请输入打印机端口 (默认9100): ").strip()
            
            if not printer_port:
                printer_port = 9100
            else:
                printer_port = int(printer_port)
            
            printer = ZebraPrinter(printer_ip, printer_port)
            printer.print_via_network(zpl_code)
            
        elif method == "2":
            # USB/本地打印机
            printers = list_available_printers()
            
            if not printers:
                print("\n未找到可用的打印机")
                return
            
            user_input = input("\n请输入打印机编号或名称（或按回车使用默认打印机）: ").strip()
            
            if not user_input:
                # 使用默认打印机
                try:
                    import win32print
                    printer_name = win32print.GetDefaultPrinter()
                    print(f"使用默认打印机: {printer_name}")
                except:
                    printer_name = "ZDesigner"
            elif user_input.isdigit():
                # 用户输入了数字，从列表中选择
                index = int(user_input) - 1
                if 0 <= index < len(printers):
                    printer_name = printers[index]
                    print(f"已选择: {printer_name}")
                else:
                    print(f"错误：无效的编号！请输入 1-{len(printers)} 之间的数字")
                    return
            else:
                # 用户直接输入了打印机名称
                printer_name = user_input
                print(f"使用打印机: {printer_name}")
            
            printer = ZebraPrinter()
            printer.print_via_usb(zpl_code, printer_name)
            
        elif method == "3":
            # 仅生成代码
            print("\nZPL代码已生成，您可以复制此代码到其他工具中使用")
            
            # 可选：保存到文件
            save = input("\n是否保存到文件？(y/n): ").strip().lower()
            if save == 'y':
                filename = input("请输入文件名 (默认: label.zpl): ").strip()
                if not filename:
                    filename = "label.zpl"
                
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(zpl_code)
                print(f"ZPL代码已保存到 {filename}")
        else:
            print("无效的选项！")
            
    except KeyboardInterrupt:
        print("\n\n程序已取消")
    except Exception as e:
        print(f"\n错误：{e}")


# 快速测试函数
def quick_test_network(ip_address="192.168.1.100", port=9100):
    """
    快速测试网络打印机
    直接调用此函数进行快速测试
    """
    print("快速测试模式 - 网络打印机")
    print(f"打印机: {ip_address}:{port}")
    
    zpl_code = create_simple_label()
    printer = ZebraPrinter(ip_address, port)
    return printer.print_via_network(zpl_code)


def quick_test_usb(printer_name="ZDesigner"):
    """
    快速测试USB打印机
    直接调用此函数进行快速测试
    """
    print("快速测试模式 - USB打印机")
    print(f"打印机: {printer_name}")
    
    zpl_code = create_simple_label()
    printer = ZebraPrinter()
    return printer.print_via_usb(zpl_code, printer_name)


if __name__ == "__main__":
    # 运行主程序（交互式）
    main()
    
    # 如果需要快速测试，可以取消注释下面的代码：
    # quick_test_network("192.168.1.100")  # 网络打印机测试
    # quick_test_usb("ZDesigner ZT411-300dpi")  # USB打印机测试（ZT411型号）

