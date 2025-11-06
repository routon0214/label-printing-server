#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复ZPL文件编码问题
"""

import sys

def fix_encoding(input_file, output_file=None):
    """修复文件编码"""
    
    if output_file is None:
        output_file = input_file.replace('.txt', '_fixed.zpl')
    
    print("="*70)
    print("ZPL文件编码修复")
    print("="*70)
    print(f"输入文件: {input_file}")
    print(f"输出文件: {output_file}")
    print()
    
    # 尝试不同的编码读取
    encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'latin1']
    
    content = None
    detected_encoding = None
    
    for encoding in encodings:
        try:
            with open(input_file, 'r', encoding=encoding) as f:
                test_content = f.read()
            
            # 检查是否包含乱码
            # 如果包含这些字符，说明是错误的编码
            if any(char in test_content for char in ['瀹', '櫒', '绫', '诲', '搴', '鎵', '洏']):
                print(f"  [跳过] {encoding} - 包含乱码字符")
                continue
            
            # 如果能读取并且看起来正常
            content = test_content
            detected_encoding = encoding
            print(f"  [成功] 使用编码: {encoding}")
            break
            
        except (UnicodeDecodeError, UnicodeError) as e:
            print(f"  [失败] {encoding} - {e}")
            continue
    
    if content is None:
        print()
        print("所有编码都失败了。尝试特殊修复...")
        print()
        
        # 读取原始字节
        with open(input_file, 'rb') as f:
            raw_data = f.read()
        
        # 尝试UTF-8解码，然后重新编码为正确的中文
        # 这个文件看起来是UTF-8被错误地当作GB2312/GBK编码了
        try:
            # 先用latin1读取（不会失败）
            with open(input_file, 'r', encoding='latin1') as f:
                wrong_content = f.read()
            
            # 找到所有乱码的中文部分并尝试修复
            # 已知的映射
            fix_map = {
                '瀹瑰櫒绫诲瀷': '容器类型',
                '浜屾搴撳尯鎵樼洏': '二次库区托盘',
                '缂栧彿': '编号',
                '灏哄': '尺寸',
                '杞介噸': '载重'
            }
            
            content = wrong_content
            for wrong, correct in fix_map.items():
                content = content.replace(wrong, correct)
            
            print("  [成功] 使用字符映射修复")
            detected_encoding = 'fixed_manually'
            
        except Exception as e:
            print(f"特殊修复也失败了: {e}")
            return False
    
    print()
    print("文件内容预览:")
    print("-"*70)
    for i, line in enumerate(content.split('\n')[:15], 1):
        if line.strip():
            print(f"{i:2}. {line}")
    print("-"*70)
    print()
    
    # 保存为UTF-8
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"[完成] 已保存到: {output_file}")
    print(f"       使用编码: UTF-8")
    print()
    print("下一步:")
    print(f"  1. 转换中文为图像: python convert_zpl_chinese.py {output_file}")
    print(f"  2. 或通过Web界面上传: http://127.0.0.1:5000")
    print("="*70)
    
    return True

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python fix_zpl_encoding.py <输入文件> [输出文件]")
        print()
        print("示例:")
        print("  python fix_zpl_encoding.py data/print_text.txt")
        print("  python fix_zpl_encoding.py data/print_text.txt output.zpl")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    fix_encoding(input_file, output_file)

