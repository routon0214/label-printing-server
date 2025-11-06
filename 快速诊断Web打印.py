#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速诊断Web打印问题
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.core.printer import ZebraPrinter


def test_simple_zpl():
    """测试最简单的ZPL"""
    print("="*70)
    print("测试1: 最简单的ZPL（纯英文）")
    print("="*70)
    
    simple_zpl = "^XA^FO50,50^A0N,50,50^FDTest^FS^XZ"
    
    print(f"ZPL: {simple_zpl}")
    print(f"长度: {len(simple_zpl)} 字符")
    print()
    
    printer = ZebraPrinter(printer_name="ZD888")
    success = printer.print_label(simple_zpl)
    
    if success:
        print("[OK] 测试1通过 - 基础功能正常")
        return True
    else:
        print("[ERROR] 测试1失败 - 基础功能有问题")
        return False


def test_medium_zpl():
    """测试中等复杂度ZPL"""
    print("\n" + "="*70)
    print("测试2: 中等复杂度ZPL（英文+条形码）")
    print("="*70)
    
    medium_zpl = """^XA
^FO50,50^A0N,40,40^FDMedium Test^FS
^FO50,100^A0N,30,30^FDBarcode Below^FS
^FO50,150^BCN,80,Y,N,N^FD123456^FS
^XZ"""
    
    print(f"ZPL长度: {len(medium_zpl)} 字符")
    print(f"开头: {medium_zpl[:30]}")
    print(f"结尾: {medium_zpl[-30:]}")
    print()
    
    printer = ZebraPrinter(printer_name="ZD888")
    success = printer.print_label(medium_zpl)
    
    if success:
        print("[OK] 测试2通过 - 复杂ZPL正常")
        return True
    else:
        print("[ERROR] 测试2失败")
        return False


def test_chinese_image_zpl():
    """测试包含中文图像的ZPL"""
    print("\n" + "="*70)
    print("测试3: 包含中文图像的ZPL")
    print("="*70)
    
    from src.core.zpl_generator import ZPLGenerator
    
    data = {
        "title": "测试",
        "fields": [
            {"label": "产品", "value": "A", "font_size": 20}  # 减小字体
        ]
    }
    
    print("生成ZPL...")
    generator = ZPLGenerator()
    zpl_code = generator.generate_label_zpl(data)
    
    print(f"ZPL长度: {len(zpl_code)} 字符")
    print(f"包含^GFA: {'是' if '^GFA' in zpl_code else '否'}")
    
    # 保存
    with open('data/test_chinese_small.zpl', 'w', encoding='utf-8') as f:
        f.write(zpl_code)
    print("已保存: data/test_chinese_small.zpl")
    print()
    
    printer = ZebraPrinter(printer_name="ZD888")
    success = printer.print_label(zpl_code)
    
    if success:
        print("[OK] 测试3通过 - 中文图像ZPL正常")
        return True
    else:
        print("[ERROR] 测试3失败")
        return False


def check_web_zpl():
    """检查Web生成的ZPL文件"""
    print("\n" + "="*70)
    print("检查Web调试文件")
    print("="*70)
    print()
    
    import glob
    
    debug_files = glob.glob('data/debug_web_*.zpl')
    
    if not debug_files:
        print("[提示] 未找到Web调试文件")
        print()
        print("请先通过Web界面测试:")
        print("  1. 启动: python web_app.py")
        print("  2. 访问: http://127.0.0.1:5000")
        print("  3. 登录: admin/admin")
        print("  4. 发送测试打印")
        print()
        print("然后重新运行此脚本")
        return
    
    print(f"找到 {len(debug_files)} 个Web调试文件")
    print()
    
    # 检查最新的
    latest = max(debug_files, key=os.path.getmtime)
    filename = os.path.basename(latest)
    
    print(f"最新文件: {filename}")
    
    with open(latest, 'r', encoding='utf-8') as f:
        web_zpl = f.read()
    
    print(f"  长度: {len(web_zpl)} 字符")
    
    # 格式检查
    print("\n格式检查:")
    
    checks = {
        "以^XA开头": web_zpl.strip().startswith('^XA'),
        "以^XZ结尾": web_zpl.strip().endswith('^XZ'),
        "包含^GFA": '^GFA' in web_zpl,
        "包含^FO": '^FO' in web_zpl
    }
    
    all_ok = True
    for check, result in checks.items():
        status = "[OK]" if result else "[ERROR]"
        print(f"  {status} {check}: {result}")
        if not result and check in ["以^XA开头", "以^XZ结尾"]:
            all_ok = False
    
    print()
    
    if not all_ok:
        print("[ERROR] ZPL格式不正确！")
        print()
        print("ZPL内容:")
        print("-" * 60)
        print(web_zpl[:200])
        print("...")
        print(web_zpl[-200:])
        print("-" * 60)
        return
    
    # 尝试打印这个文件
    print("尝试打印Web生成的ZPL...")
    printer = ZebraPrinter(printer_name="ZD888")
    success = printer.print_label(web_zpl)
    
    if success:
        print("[OK] Web生成的ZPL可以打印！")
        print()
        print("这说明:")
        print("  - Web生成的ZPL格式正确")
        print("  - 问题可能在Web界面到服务器的传输过程")
        print()
        print("建议:")
        print("  1. 检查浏览器F12开发者工具的Network标签")
        print("  2. 查看POST请求的数据是否完整")
        print("  3. 检查是否有JS错误")
    else:
        print("[ERROR] Web生成的ZPL也无法打印")
        print()
        print("这说明Web处理ZPL时有问题")


def main():
    """主函数"""
    print("\n" + "="*70)
    print("快速诊断Web打印问题")
    print("="*70)
    print()
    print("诊断策略:")
    print("  测试1: 最简单ZPL → 验证基础功能")
    print("  测试2: 中等ZPL → 验证复杂命令")
    print("  测试3: 中文ZPL → 验证图像转换")
    print("  检查: Web调试文件 → 对比差异")
    print()
    print("="*70)
    
    # 执行测试
    results = []
    
    # 测试1
    input("\n准备测试1: 最简单ZPL，按回车继续...")
    r1 = test_simple_zpl()
    results.append(("最简单ZPL", r1))
    
    if not r1:
        print("\n[严重] 基础测试失败，请检查打印机连接！")
        return
    
    # 测试2
    input("\n准备测试2: 中等ZPL，按回车继续...")
    r2 = test_medium_zpl()
    results.append(("中等ZPL", r2))
    
    # 测试3
    input("\n准备测试3: 中文图像ZPL，按回车继续...")
    r3 = test_chinese_image_zpl()
    results.append(("中文图像ZPL", r3))
    
    # 汇总
    print("\n" + "="*70)
    print("诊断结果汇总")
    print("="*70)
    
    for name, result in results:
        status = "[OK]" if result else "[ERROR]"
        print(f"  {status} {name}: {'通过' if result else '失败'}")
    
    print("="*70)
    print()
    
    all_pass = all(r for _, r in results)
    
    if all_pass:
        print("✅ 所有本地测试通过！")
        print()
        print("测试脚本能打印，说明:")
        print("  - ZPL代码生成正确")
        print("  - 中文转换正常")
        print("  - 打印机驱动正常")
        print()
        print("如果Web界面不能打印，问题在于:")
        print("  → Web应用处理流程")
        print("  → 数据传输过程")
        print()
        print("下一步:")
        print("  1. 启动Web服务: python web_app.py")
        print("  2. 通过Web界面测试")
        print("  3. 查看控制台调试输出")
        print("  4. 运行: python 对比测试Web和脚本.py")
        print("  5. 选择4检查Web调试文件")
    else:
        print("❌ 有测试失败")
        print()
        print("请先解决失败的测试项")
    
    # 检查Web调试文件
    print("\n" + "="*70)
    input("按回车检查Web调试文件...")
    check_web_zpl()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n已中断")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()

