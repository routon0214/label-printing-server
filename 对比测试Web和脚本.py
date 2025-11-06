#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对比测试Web和脚本的ZPL输出
找出差异
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.core.printer import ZebraPrinter
from src.core.zpl_generator import ZPLGenerator


def test_direct_print():
    """直接打印（模拟测试脚本）"""
    print("="*70)
    print("测试1: 直接打印（测试脚本方式）")
    print("="*70)
    print()
    
    # 生成简单中文标签
    data = {
        "title": "测试",
        "fields": [
            {"label": "产品", "value": "元件A", "font_size": 25}
        ]
    }
    
    print("生成ZPL...")
    generator = ZPLGenerator()
    zpl_code = generator.generate_label_zpl(data)
    
    print(f"ZPL长度: {len(zpl_code)} 字符")
    
    # 保存到文件
    with open('data/zpl_from_script.zpl', 'w', encoding='utf-8') as f:
        f.write(zpl_code)
    print("已保存: data/zpl_from_script.zpl")
    
    # 显示ZPL结构
    print("\nZPL结构分析:")
    print(f"  开始: {zpl_code[:20]}")
    print(f"  包含^GFA: {'是' if '^GFA' in zpl_code else '否'}")
    print(f"  结束: {zpl_code[-20:]}")
    
    # 打印
    confirm = input("\n是否直接打印测试? (y/n): ").strip().lower()
    if confirm == 'y':
        printer = ZebraPrinter(printer_name="ZD888")
        success = printer.print_label(zpl_code)
        print(f"结果: {'成功' if success else '失败'}")
        return success
    return None


def simulate_web_process():
    """模拟Web处理流程"""
    print("\n" + "="*70)
    print("测试2: 模拟Web处理流程")
    print("="*70)
    print()
    
    import json
    from src.utils.zpl_chinese_converter import detect_and_convert_zpl
    
    # 模拟Web接收的JSON数据
    json_data = {
        "print_type": "label",
        "title": "测试",
        "fields": [
            {"label": "产品", "value": "元件A", "font_size": 25}
        ]
    }
    
    print("步骤1: 解析JSON数据")
    print(f"  数据: {json.dumps(json_data, ensure_ascii=False)}")
    
    print("\n步骤2: 生成ZPL代码")
    generator = ZPLGenerator()
    zpl_code = generator.generate_label_zpl(json_data)
    print(f"  ZPL长度: {len(zpl_code)} 字符")
    
    print("\n步骤3: 检测并转换中文")
    zpl_code, was_converted = detect_and_convert_zpl(zpl_code)
    print(f"  是否转换: {was_converted}")
    print(f"  最终ZPL长度: {len(zpl_code)} 字符")
    
    # 保存到文件
    with open('data/zpl_from_web_simulation.zpl', 'w', encoding='utf-8') as f:
        f.write(zpl_code)
    print("  已保存: data/zpl_from_web_simulation.zpl")
    
    # 显示ZPL结构
    print("\nZPL结构分析:")
    print(f"  开始: {zpl_code[:20]}")
    print(f"  包含^GFA: {'是' if '^GFA' in zpl_code else '否'}")
    print(f"  结束: {zpl_code[-20:]}")
    
    # 打印
    confirm = input("\n是否模拟Web打印? (y/n): ").strip().lower()
    if confirm == 'y':
        printer = ZebraPrinter(printer_name="ZD888")
        success = printer.print_label(zpl_code)
        print(f"结果: {'成功' if success else '失败'}")
        return success
    return None


def compare_files():
    """对比两个ZPL文件"""
    print("\n" + "="*70)
    print("对比ZPL文件")
    print("="*70)
    print()
    
    file1 = 'data/zpl_from_script.zpl'
    file2 = 'data/zpl_from_web_simulation.zpl'
    
    if not os.path.exists(file1) or not os.path.exists(file2):
        print("[ERROR] 请先运行测试1和测试2生成ZPL文件")
        return
    
    with open(file1, 'r', encoding='utf-8') as f:
        zpl1 = f.read()
    
    with open(file2, 'r', encoding='utf-8') as f:
        zpl2 = f.read()
    
    print(f"文件1 (测试脚本): {len(zpl1)} 字符")
    print(f"文件2 (Web模拟):  {len(zpl2)} 字符")
    print()
    
    if zpl1 == zpl2:
        print("[OK] 两个文件完全相同！")
        print("说明Web处理流程正确，问题可能在Web服务器传输或其他环节")
    else:
        print("[WARNING] 文件有差异！")
        print()
        print("差异分析:")
        
        # 检查长度
        if len(zpl1) != len(zpl2):
            print(f"  - 长度不同: {len(zpl1)} vs {len(zpl2)}")
        
        # 检查开头
        if zpl1[:100] != zpl2[:100]:
            print(f"  - 开头不同:")
            print(f"    文件1: {zpl1[:50]}")
            print(f"    文件2: {zpl2[:50]}")
        
        # 检查结尾
        if zpl1[-100:] != zpl2[-100:]:
            print(f"  - 结尾不同:")
            print(f"    文件1: {zpl1[-50:]}")
            print(f"    文件2: {zpl2[-50:]}")


def check_web_debug_files():
    """检查Web应用生成的调试文件"""
    print("\n" + "="*70)
    print("检查Web调试文件")
    print("="*70)
    print()
    
    import glob
    
    debug_files = glob.glob('data/debug_web_*.zpl')
    
    if not debug_files:
        print("[INFO] 没有找到Web调试文件")
        print()
        print("请通过Web界面测试一次，系统会自动保存调试文件")
        print("  1. 访问 http://127.0.0.1:5000")
        print("  2. 上传ZPL文件或发送JSON数据")
        print("  3. 查看 data/ 目录下的 debug_web_*.zpl 文件")
        return
    
    print(f"找到 {len(debug_files)} 个调试文件:")
    for i, filepath in enumerate(debug_files, 1):
        filename = os.path.basename(filepath)
        size = os.path.getsize(filepath)
        print(f"  {i}. {filename} ({size} 字节)")
    
    print()
    
    # 检查最新的文件
    latest = max(debug_files, key=os.path.getmtime)
    print(f"最新文件: {os.path.basename(latest)}")
    
    with open(latest, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"  长度: {len(content)} 字符")
    print(f"  开头: {content[:50]}")
    print(f"  结尾: {content[-50:]}")
    print(f"  包含^GFA: {'是' if '^GFA' in content else '否'}")
    print(f"  包含^XA: {'是' if '^XA' in content else '否'}")
    print(f"  包含^XZ: {'是' if '^XZ' in content else '否'}")
    
    # 验证ZPL格式
    print("\nZPL格式验证:")
    if not content.strip().startswith('^XA'):
        print("  [ERROR] ZPL不是以^XA开头")
    else:
        print("  [OK] 以^XA开头")
    
    if not content.strip().endswith('^XZ'):
        print("  [ERROR] ZPL不是以^XZ结尾")
    else:
        print("  [OK] 以^XZ结尾")
    
    # 尝试打印这个文件
    print()
    confirm = input("是否尝试打印这个调试文件? (y/n): ").strip().lower()
    if confirm == 'y':
        printer = ZebraPrinter(printer_name="ZD888")
        success = printer.print_label(content)
        if success:
            print("[OK] 打印命令已发送")
            print("\n如果这个能打印，说明Web生成的ZPL是正确的")
            print("问题可能在Web传输过程中")
        else:
            print("[ERROR] 打印失败")


def main():
    """主菜单"""
    while True:
        print("\n" + "="*70)
        print("对比测试：Web vs 测试脚本")
        print("="*70)
        print()
        print("选项:")
        print("  1. 测试直接打印 (测试脚本方式)")
        print("  2. 测试模拟Web流程")
        print("  3. 对比两个ZPL文件")
        print("  4. 检查Web调试文件")
        print()
        print("  建议顺序: 1 → 2 → 3")
        print("  如果已通过Web测试: 直接选4")
        print()
        print("  0. 退出")
        print()
        
        choice = input("请选择 (0-4): ").strip()
        
        if choice == '0':
            break
        elif choice == '1':
            test_direct_print()
        elif choice == '2':
            simulate_web_process()
        elif choice == '3':
            compare_files()
        elif choice == '4':
            check_web_debug_files()
        else:
            print("无效选项")
        
        input("\n按回车继续...")
    
    print("\n测试结束")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n已中断")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()

