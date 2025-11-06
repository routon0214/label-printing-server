#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一键修复ZPL中文乱码
集成编码修复和中文转换功能
"""

import sys
import os

def one_click_fix(input_file):
    """
    一键修复ZPL文件的中文乱码问题
    
    处理步骤:
    1. 修复文件编码
    2. 格式化换行符
    3. 转换中文为图像
    """
    
    print("="*70)
    print("一键修复ZPL中文乱码")
    print("="*70)
    print(f"输入文件: {input_file}")
    print()
    
    # 检查文件是否存在
    if not os.path.exists(input_file):
        print(f"[错误] 文件不存在: {input_file}")
        return False
    
    # 生成中间文件名
    base_name = os.path.splitext(input_file)[0]
    step1_file = f"{base_name}_step1_encoding.zpl"
    step2_file = f"{base_name}_step2_formatted.zpl"
    final_file = f"{base_name}_fixed.zpl"
    
    try:
        # 步骤1: 修复编码
        print("[步骤1/3] 修复文件编码...")
        from fix_zpl_encoding import fix_encoding
        if not fix_encoding(input_file, step1_file):
            print("[错误] 编码修复失败")
            return False
        print("  [OK] 编码修复完成")
        print()
        
        # 步骤2: 格式化换行符
        print("[步骤2/3] 格式化换行符...")
        with open(step1_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 替换\n为真正的换行符
        formatted_content = content.replace('\\n', '\n')
        
        with open(step2_file, 'w', encoding='utf-8') as f:
            f.write(formatted_content)
        
        print("  [OK] 换行符格式化完成")
        print()
        
        # 步骤3: 转换中文为图像
        print("[步骤3/3] 转换中文为图像...")
        from convert_zpl_chinese import convert_zpl_chinese
        
        with open(step2_file, 'r', encoding='utf-8') as f:
            zpl_code = f.read()
        
        converted_zpl = convert_zpl_chinese(zpl_code)
        
        with open(final_file, 'w', encoding='utf-8') as f:
            f.write(converted_zpl)
        
        print()
        print("="*70)
        print("[完成] ZPL文件修复成功！")
        print("="*70)
        print()
        print(f"修复后的文件: {final_file}")
        print()
        print("下一步操作:")
        print(f"  1. Web界面上传: http://127.0.0.1:5000")
        print(f"  2. 直接测试打印:")
        print(f"     python -c \"from src.core.printer import ZebraPrinter; p = ZebraPrinter('ZT411'); p.print_label(open('{final_file}').read())\"")
        print()
        print("  3. MQTT发送:")
        print(f"     (使用修复后的文件: {final_file})")
        print()
        
        # 清理中间文件（可选）
        cleanup = input("是否删除中间临时文件？(y/n，默认n): ").strip().lower()
        if cleanup == 'y':
            try:
                if os.path.exists(step1_file):
                    os.remove(step1_file)
                if os.path.exists(step2_file):
                    os.remove(step2_file)
                print("  [OK] 临时文件已清理")
            except Exception as e:
                print(f"  [警告] 清理临时文件失败: {e}")
        else:
            print(f"  [保留] 临时文件:")
            print(f"    - {step1_file} (编码修复后)")
            print(f"    - {step2_file} (换行符格式化后)")
        
        print()
        print("="*70)
        print("[成功] 所有步骤完成！")
        print("="*70)
        
        return True
        
    except Exception as e:
        print(f"\n[错误] 处理失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("="*70)
        print("一键修复ZPL中文乱码")
        print("="*70)
        print()
        print("用法:")
        print("  python 一键修复ZPL中文.py <ZPL文件>")
        print()
        print("示例:")
        print("  python 一键修复ZPL中文.py data/print_text.txt")
        print()
        print("功能:")
        print("  1. 自动修复文件编码问题（UTF-8/GBK/GB2312）")
        print("  2. 格式化换行符")
        print("  3. 将中文TEXT命令转换为图像")
        print()
        print("输出:")
        print("  生成 <原文件名>_fixed.zpl 可直接打印的文件")
        print()
        print("="*70)
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    success = one_click_fix(input_file)
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()

