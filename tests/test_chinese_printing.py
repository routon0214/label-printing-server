#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中英文打印综合测试
测试斑马打印机(ZPL)和得力打印机(ESC/POS)的中英文打印
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.core.printer import ZebraPrinter
from src.core.escpos_printer import ESCPOSPrinter
from src.core.zpl_generator import ZPLGenerator
from src.utils.zpl_chinese_converter import detect_and_convert_zpl


def test_zebra_printer():
    """测试斑马打印机的中英文打印"""
    print("="*70)
    print("测试1: 斑马打印机 (ZPL) - 中英文打印")
    print("="*70)
    print()
    
    # 创建打印机实例
    printer = ZebraPrinter(printer_name="ZT411")
    generator = ZPLGenerator()
    
    # 测试用例
    test_cases = [
        {
            "name": "纯英文测试",
            "data": {
                "title": "English Only Label",
                "fields": [
                    {"label": "Product", "value": "Electronic Component", "font_size": 28},
                    {"label": "Serial No", "value": "SN-2025-001", "font_size": 25},
                    {"label": "Date", "value": "2025-11-06", "font_size": 22}
                ],
                "barcode": "SN2025001"
            }
        },
        {
            "name": "纯中文测试",
            "data": {
                "title": "产品标签",
                "fields": [
                    {"label": "产品名称", "value": "精密电子元件", "font_size": 28},
                    {"label": "序列号", "value": "编号零零一", "font_size": 25},
                    {"label": "生产日期", "value": "二零二五年十一月六日", "font_size": 22}
                ],
                "barcode": "SN2025001"
            }
        },
        {
            "name": "中英文混合测试",
            "data": {
                "title": "Product Label 产品标签",
                "fields": [
                    {"label": "产品", "value": "Component-A型号", "font_size": 28},
                    {"label": "Serial", "value": "SN-零零一", "font_size": 25},
                    {"label": "日期", "value": "2025-11-06", "font_size": 22}
                ],
                "barcode": "SN2025001"
            }
        },
        {
            "name": "直接ZPL代码(纯英文)",
            "zpl": "^XA^FO50,50^A0N,40,40^FDHello World^FS^FO50,120^A0N,30,30^FDTest Label^FS^XZ",
            "is_zpl": True
        },
        {
            "name": "直接ZPL代码(包含中文)",
            "zpl": "^XA^FO50,50^A0N,40,40^FD你好世界^FS^FO50,120^A0N,30,30^FD测试标签^FS^XZ",
            "is_zpl": True
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n[测试 {i}/{len(test_cases)}] {test_case['name']}")
        print("-" * 60)
        
        try:
            if test_case.get('is_zpl'):
                # 直接ZPL代码
                zpl_code = test_case['zpl']
                print(f"原始ZPL: {zpl_code[:80]}...")
                
                # 自动检测并转换中文
                converted_zpl, was_converted = detect_and_convert_zpl(zpl_code)
                if was_converted:
                    print(f"[OK] 中文已转换为图像")
                else:
                    print(f"[OK] 无需转换")
                
                zpl_code = converted_zpl
            else:
                # 使用生成器
                print(f"生成ZPL标签...")
                zpl_code = generator.generate_label_zpl(test_case['data'])
            
            # 保存ZPL到文件（可选）
            filename = f"data/test_zebra_{i}_{test_case['name'].replace(' ', '_')}.zpl"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(zpl_code)
            print(f"ZPL已保存: {filename}")
            
            # 实际打印（需要确认）
            confirm = input(f"\n是否打印到斑马打印机? (y/n，默认n): ").strip().lower()
            if confirm == 'y':
                success = printer.print_label(zpl_code)
                if success:
                    print(f"[OK] 打印成功")
                    results.append((test_case['name'], 'SUCCESS'))
                else:
                    print(f"[ERROR] 打印失败")
                    results.append((test_case['name'], 'FAILED'))
            else:
                print(f"[SKIP] 已跳过实际打印")
                results.append((test_case['name'], 'SKIPPED'))
        
        except Exception as e:
            print(f"[ERROR] 测试失败: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_case['name'], 'ERROR'))
    
    print("\n" + "="*70)
    print("斑马打印机测试结果汇总")
    print("="*70)
    for name, result in results:
        status_mark = {
            'SUCCESS': '[OK]',
            'FAILED': '[ERROR]',
            'SKIPPED': '[SKIP]',
            'ERROR': '[ERROR]'
        }[result]
        print(f"  {status_mark} {name}: {result}")
    print("="*70)
    print()


def test_escpos_printer():
    """测试得力打印机(ESC/POS)的中英文打印"""
    print("="*70)
    print("测试2: 得力打印机 (ESC/POS) - 中英文打印")
    print("="*70)
    print()
    
    # 创建打印机实例
    printer = ESCPOSPrinter(printer_name="Deli")
    
    # 测试用例
    test_cases = [
        {
            "name": "纯英文小票",
            "data": {
                "title": "Sales Receipt",
                "items": [
                    {"name": "Product A", "qty": 2, "price": 10.00},
                    {"name": "Product B", "qty": 1, "price": 20.00}
                ],
                "total": 40.00,
                "footer": "Thank you!"
            }
        },
        {
            "name": "纯中文小票",
            "data": {
                "title": "销售收据",
                "items": [
                    {"name": "商品甲", "qty": 2, "price": 10.00},
                    {"name": "商品乙", "qty": 1, "price": 20.00}
                ],
                "total": 40.00,
                "footer": "谢谢惠顾！"
            }
        },
        {
            "name": "中英文混合小票",
            "data": {
                "title": "Sales Receipt 销售收据",
                "items": [
                    {"name": "Product-A 产品", "qty": 2, "price": 10.00},
                    {"name": "商品 Type-B", "qty": 1, "price": 20.00}
                ],
                "total": 40.00,
                "footer": "Thank you! 谢谢惠顾！"
            }
        },
        {
            "name": "原始文本(纯英文)",
            "data": {
                "raw_text": "Hello World\nTest Print\nEnglish Only\n\n\n",
                "encoding": "gb2312"
            }
        },
        {
            "name": "原始文本(纯中文)",
            "data": {
                "raw_text": "你好世界\n测试打印\n纯中文内容\n感谢惠顾\n\n\n",
                "encoding": "gb2312"
            }
        },
        {
            "name": "原始文本(中英混合)",
            "data": {
                "raw_text": "Hello 你好\nTest 测试\n商品A  10.00\nProduct B  20.00\nTotal 总计: 30.00\nThank you 谢谢!\n\n\n",
                "encoding": "gb2312"
            }
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n[测试 {i}/{len(test_cases)}] {test_case['name']}")
        print("-" * 60)
        
        try:
            data = test_case['data']
            
            # 显示数据预览
            if 'raw_text' in data:
                print(f"原始文本预览:")
                print(data['raw_text'][:100])
            else:
                print(f"标题: {data.get('title', 'N/A')}")
                print(f"项目数: {len(data.get('items', []))}")
            
            # 实际打印（需要确认）
            confirm = input(f"\n是否打印到得力打印机? (y/n，默认n): ").strip().lower()
            if confirm == 'y':
                success = printer.print_receipt(data)
                if success:
                    print(f"[OK] 打印成功")
                    results.append((test_case['name'], 'SUCCESS'))
                else:
                    print(f"[ERROR] 打印失败")
                    results.append((test_case['name'], 'FAILED'))
            else:
                print(f"[SKIP] 已跳过实际打印")
                results.append((test_case['name'], 'SKIPPED'))
        
        except Exception as e:
            print(f"[ERROR] 测试失败: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_case['name'], 'ERROR'))
    
    print("\n" + "="*70)
    print("得力打印机测试结果汇总")
    print("="*70)
    for name, result in results:
        status_mark = {
            'SUCCESS': '[OK]',
            'FAILED': '[ERROR]',
            'SKIPPED': '[SKIP]',
            'ERROR': '[ERROR]'
        }[result]
        print(f"  {status_mark} {name}: {result}")
    print("="*70)
    print()


def main():
    """主测试流程"""
    print("\n" + "="*70)
    print("中英文打印综合测试")
    print("="*70)
    print()
    print("本测试将测试以下场景:")
    print("  1. 斑马打印机 (ZPL) - 纯英文、纯中文、中英混合")
    print("  2. 得力打印机 (ESC/POS) - 纯英文、纯中文、中英混合")
    print()
    print("注意:")
    print("  - 斑马打印机：中文将自动转换为图像")
    print("  - 得力打印机：使用GB2312编码打印中文")
    print()
    
    # 选择测试
    print("请选择要测试的打印机:")
    print("  1. 斑马打印机 (ZPL)")
    print("  2. 得力打印机 (ESC/POS)")
    print("  3. 两者都测试")
    print("  0. 退出")
    
    choice = input("\n请输入选项 (0-3，默认3): ").strip() or '3'
    
    if choice == '0':
        print("已退出测试")
        return
    elif choice == '1':
        test_zebra_printer()
    elif choice == '2':
        test_escpos_printer()
    elif choice == '3':
        test_zebra_printer()
        print("\n" + "*"*70)
        print("切换到得力打印机测试")
        print("*"*70 + "\n")
        test_escpos_printer()
    else:
        print(f"无效选项: {choice}")
        return
    
    print("\n" + "="*70)
    print("所有测试完成！")
    print("="*70)
    print()
    print("生成的测试文件保存在 data/ 目录")
    print("日志文件在 data/logs/ 目录")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n测试已中断")
    except Exception as e:
        print(f"\n测试出错: {e}")
        import traceback
        traceback.print_exc()

