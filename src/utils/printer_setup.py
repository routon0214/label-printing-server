#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
打印机配置向导模块
提供交互式菜单用于自动识别和配置打印机
"""

import platform
import json
import os


def get_available_printers():
    """
    获取系统中所有可用的打印机
    
    Returns:
        list: 打印机名称列表
    """
    printers = []
    system = platform.system()
    
    try:
        if system == 'Windows':
            try:
                import win32print
                printer_list = win32print.EnumPrinters(2)  # PRINTER_ENUM_LOCAL | PRINTER_ENUM_CONNECTIONS
                printers = [p[2] for p in printer_list]
            except ImportError:
                print("警告: 需要安装 pywin32 库才能检测Windows打印机")
            except Exception as e:
                print(f"获取Windows打印机列表失败: {e}")
        
        elif system == 'Linux':
            try:
                import cups
                conn = cups.Connection()
                printer_dict = conn.getPrinters()
                printers = list(printer_dict.keys())
            except ImportError:
                print("警告: 需要安装 pycups 库才能检测Linux打印机")
            except Exception as e:
                print(f"获取Linux打印机列表失败: {e}")
    
    except Exception as e:
        print(f"获取打印机列表时出错: {e}")
    
    return printers


def detect_printer_type(printer_name):
    """
    根据打印机名称自动检测打印机类型
    
    Args:
        printer_name: 打印机名称
        
    Returns:
        str: 打印机类型建议 ('label', 'pdf', 'receipt', '*')
    """
    name_lower = printer_name.lower()
    
    # 标签打印机关键词
    label_keywords = ['zebra', 'zt', 'zt411', 'zd', 'zdesigner', 'label', '标签']
    if any(keyword in name_lower for keyword in label_keywords):
        return 'label'
    
    # 热敏打印机关键词
    receipt_keywords = ['thermal', 'receipt', 'escpos', 'pos', '热敏', '小票', 'deli', 'epson']
    if any(keyword in name_lower for keyword in receipt_keywords):
        return 'receipt'
    
    # PDF打印机关键词（激光、喷墨等）
    pdf_keywords = ['hp', 'canon', 'epson', 'brother', 'konica', 'minolta', 'xerox', 'laser', 'inkjet']
    if any(keyword in name_lower for keyword in pdf_keywords):
        return 'pdf'
    
    # 默认通用
    return '*'


def print_printer_menu(printers):
    """
    显示打印机选择菜单
    
    Args:
        printers: 打印机列表
        
    Returns:
        int: 用户选择的索引，-1表示取消
    """
    if not printers:
        print("\n未找到可用打印机")
        return -1
    
    print("\n" + "=" * 70)
    print(" " * 20 + "可用打印机列表")
    print("=" * 70)
    
    for idx, printer in enumerate(printers, 1):
        printer_type = detect_printer_type(printer)
        type_desc = {
            'label': '标签打印机',
            'pdf': 'PDF打印机',
            'receipt': '热敏打印机',
            '*': '通用打印机'
        }.get(printer_type, '未知类型')
        
        print(f"  [{idx}] {printer}")
        print(f"      类型: {type_desc}")
    
    print("=" * 70)
    print("  [0] 跳过，不添加打印机")
    print("=" * 70)
    
    while True:
        try:
            choice = input("\n请选择要添加的打印机编号 (0-{}): ".format(len(printers)))
            choice = int(choice)
            
            if choice == 0:
                return -1
            elif 1 <= choice <= len(printers):
                return choice - 1
            else:
                print(f"无效选择，请输入 0-{len(printers)} 之间的数字")
        except ValueError:
            print("请输入有效的数字")
        except KeyboardInterrupt:
            print("\n\n取消操作")
            return -1


def select_printer_types():
    """
    选择打印机支持的打印类型
    
    Returns:
        list: 打印类型列表，如 ['label', 'pdf'] 或 ['*']
    """
    print("\n" + "=" * 70)
    print(" " * 20 + "选择打印机类型")
    print("=" * 70)
    print("  支持的打印类型:")
    print("  [1] label    - 标签打印（ZPL）")
    print("  [2] pdf      - PDF文档打印")
    print("  [3] receipt  - 小票打印（ESC/POS）")
    print("  [4] *        - 通用打印机（支持所有类型）")
    print("=" * 70)
    print("提示: 可以多选，用逗号分隔，如: 1,2 或直接回车使用默认类型")
    print("=" * 70)
    
    while True:
        try:
            choice = input("\n请选择类型 (直接回车使用默认类型): ").strip()
            
            if not choice:
                return None  # 返回None表示使用默认类型
            
            types = []
            for num in choice.split(','):
                num = num.strip()
                if num == '1':
                    types.append('label')
                elif num == '2':
                    types.append('pdf')
                elif num == '3':
                    types.append('receipt')
                elif num == '4':
                    return ['*']  # 通用打印机
                else:
                    print(f"无效选择: {num}")
                    raise ValueError
            
            if types:
                return types
            else:
                print("请至少选择一个类型")
        
        except ValueError:
            continue
        except KeyboardInterrupt:
            print("\n\n取消操作")
            return None


def add_printer_to_config(config_file, printer_name, printer_types=None, is_default=False):
    """
    将打印机添加到配置文件
    
    Args:
        config_file: 配置文件路径
        printer_name: 打印机名称
        printer_types: 打印机类型列表，如果为None则自动检测
        is_default: 是否为默认打印机
        
    Returns:
        bool: 是否成功
    """
    try:
        # 读取现有配置
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
        else:
            config = {}
        
        # 确保printers数组存在
        if 'printers' not in config:
            config['printers'] = []
        
        # 检查是否已存在
        for printer in config['printers']:
            if printer.get('name') == printer_name:
                print(f"\n警告: 打印机 '{printer_name}' 已存在于配置中")
                overwrite = input("是否覆盖? (y/n): ").strip().lower()
                if overwrite != 'y':
                    return False
                # 移除旧的配置
                config['printers'] = [p for p in config['printers'] if p.get('name') != printer_name]
                break
        
        # 如果没有指定类型，自动检测
        if printer_types is None:
            printer_types = [detect_printer_type(printer_name)]
        
        # 创建打印机配置
        printer_config = {
            "name": printer_name,
            "types": printer_types,
            "ip": None,
            "port": 9100,
            "device": None,
            "default": is_default
        }
        
        # 如果设置为默认，取消其他打印机的默认标记
        if is_default:
            for printer in config['printers']:
                printer['default'] = False
        
        # 添加到配置
        config['printers'].append(printer_config)
        
        # 保存配置
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        return True
        
    except Exception as e:
        print(f"添加打印机到配置失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def printer_setup_wizard(config_file='config/printer_config.json'):
    """
    打印机配置向导
    
    Args:
        config_file: 配置文件路径
        
    Returns:
        bool: 是否成功完成配置
    """
    print("\n" + "=" * 70)
    print(" " * 20 + "打印机配置向导")
    print("=" * 70)
    
    # 扫描打印机
    print("\n正在扫描可用打印机...")
    printers = get_available_printers()
    
    if not printers:
        print("\n未找到可用打印机")
        print("您可以:")
        print("  1. 检查打印机是否已连接")
        print("  2. 检查打印机驱动是否已安装")
        print("  3. 稍后手动编辑配置文件添加打印机")
        return False
    
    print(f"\n找到 {len(printers)} 台可用打印机")
    
    # 显示菜单并选择
    selected_idx = print_printer_menu(printers)
    
    if selected_idx == -1:
        print("\n已取消添加打印机")
        return False
    
    selected_printer = printers[selected_idx]
    print(f"\n已选择: {selected_printer}")
    
    # 自动检测类型
    detected_type = detect_printer_type(selected_printer)
    type_desc = {
        'label': '标签打印机',
        'pdf': 'PDF打印机',
        'receipt': '热敏打印机',
        '*': '通用打印机'
    }.get(detected_type, '未知类型')
    
    print(f"检测到的类型: {type_desc}")
    
    # 询问是否使用默认类型
    use_default = input(f"\n使用检测到的类型 '{detected_type}'? (y/n, 默认y): ").strip().lower()
    
    if use_default == 'n':
        printer_types = select_printer_types()
        if printer_types is None:
            printer_types = [detected_type]
    else:
        printer_types = [detected_type]
    
    # 询问是否设为默认打印机
    is_default = False
    if len(printers) == 1 or input("\n是否设为默认打印机? (y/n, 默认n): ").strip().lower() == 'y':
        is_default = True
    
    # 添加到配置
    print(f"\n正在添加打印机到配置...")
    if add_printer_to_config(config_file, selected_printer, printer_types, is_default):
        print(f"✓ 成功添加打印机: {selected_printer}")
        print(f"  类型: {printer_types}")
        if is_default:
            print(f"  已设为默认打印机")
        return True
    else:
        print(f"✗ 添加打印机失败")
        return False

