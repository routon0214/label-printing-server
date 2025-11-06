#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZPL中文转换工具
将ZPL TEXT命令中的中文自动转换为图像命令
"""

import sys
import os
import re

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

from src.utils.image_utils import text_to_image_zpl


def has_chinese(text):
    """检查文本是否包含中文"""
    return any('\u4e00' <= char <= '\u9fff' for char in text)


def parse_text_command(line):
    """
    解析ZPL TEXT命令
    TEXT x,y,"font",rotation,xmul,ymul,"text"
    返回: (x, y, font, rotation, xmul, ymul, text)
    """
    # 匹配TEXT命令: TEXT 20,10,"TSS24.BF2",0,1,1,"容器类型"
    pattern = r'TEXT\s+(\d+),(\d+),"([^"]+)",(\d+),(\d+),(\d+),"([^"]*)"'
    match = re.search(pattern, line)
    
    if match:
        return {
            'x': int(match.group(1)),
            'y': int(match.group(2)),
            'font': match.group(3),
            'rotation': int(match.group(4)),
            'xmul': int(match.group(5)),
            'ymul': int(match.group(6)),
            'text': match.group(7)
        }
    return None


def convert_text_to_image(parsed, font_size=30):
    """将TEXT命令转换为图像命令"""
    text = parsed['text']
    x = parsed['x']
    y = parsed['y']
    
    # 根据字体倍数调整字号
    ymul = parsed['ymul']
    font_size = font_size * ymul
    
    print(f"  转换: '{text}' (字号: {font_size})")
    
    # 转换为图像
    hex_data, w, h, bpr, total = text_to_image_zpl(text, font_size=font_size)
    
    if not hex_data:
        print(f"  ✗ 转换失败")
        return None
    
    # 生成GFA命令
    # ^FO x,y ^GFA,total,total,bpr,hex_data ^FS
    gfa_cmd = f"^FO{x},{y}^GFA,{total},{total},{bpr},{hex_data}^FS"
    
    return gfa_cmd


def convert_zpl_file(input_file, output_file=None):
    """
    转换ZPL文件中的中文TEXT命令
    
    Args:
        input_file: 输入ZPL文件
        output_file: 输出文件（可选，默认为 input_converted.zpl）
    """
    print("="*70)
    print("ZPL中文转换工具")
    print("="*70)
    
    # 读取文件
    if not os.path.exists(input_file):
        print(f"✗ 文件不存在: {input_file}")
        return False
    
    print(f"\n读取文件: {input_file}")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"文件大小: {len(content)} 字符")
    
    # 处理转义的换行符
    content = content.replace('\\n', '\n')
    
    # 分割成命令行
    lines = content.split('\n')
    print(f"命令行数: {len(lines)}")
    
    # 转换
    converted_lines = []
    converted_count = 0
    
    print("\n开始转换...")
    print("-"*70)
    
    for i, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
        
        # 检查是否是TEXT命令
        if line.startswith('TEXT'):
            parsed = parse_text_command(line)
            
            if parsed and has_chinese(parsed['text']):
                print(f"\n[{i}] TEXT命令包含中文:")
                print(f"  原命令: {line[:60]}...")
                
                # 转换为图像
                gfa_cmd = convert_text_to_image(parsed, font_size=28)
                
                if gfa_cmd:
                    converted_lines.append(gfa_cmd)
                    converted_count += 1
                    print(f"  ✓ 已转换为图像")
                else:
                    # 转换失败，保留原命令
                    converted_lines.append(line)
                    print(f"  ✗ 保留原命令")
            else:
                # 没有中文，保留原命令
                converted_lines.append(line)
        else:
            # 其他命令，直接保留
            converted_lines.append(line)
    
    print("-"*70)
    print(f"\n转换完成: {converted_count} 个TEXT命令")
    
    # 生成输出文件名
    if not output_file:
        base, ext = os.path.splitext(input_file)
        output_file = f"{base}_converted{ext}"
    
    # 保存
    output_content = '\n'.join(converted_lines)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(output_content)
    
    print(f"\n✓ 已保存到: {output_file}")
    print(f"文件大小: {len(output_content)} 字符")
    
    # 显示预览
    print("\n" + "="*70)
    print("转换后的ZPL代码预览（前800字符）:")
    print("-"*70)
    print(output_content[:800])
    if len(output_content) > 800:
        print("...")
    print("-"*70)
    
    return True


def main():
    """主函数"""
    print("ZPL中文转换工具\n")
    
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else None
    else:
        # 交互式输入
        input_file = input("请输入ZPL文件路径 (默认: data/print_text.txt): ").strip()
        if not input_file:
            input_file = "data/print_text.txt"
        
        output_file = input("输出文件名 (默认自动生成): ").strip()
        if not output_file:
            output_file = None
    
    try:
        success = convert_zpl_file(input_file, output_file)
        
        if success:
            print("\n" + "="*70)
            print("✓ 转换成功！")
            print("="*70)
            print("\n下一步:")
            print("  1. 通过Web界面上传转换后的文件")
            print("  2. 或直接发送到打印机测试")
        else:
            print("\n✗ 转换失败")
    
    except Exception as e:
        print(f"\n✗ 转换出错: {e}")
        import traceback
        traceback.print_exc()
    
    input("\n按回车键退出...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用户中断")
    except Exception as e:
        print(f"\n程序错误: {e}")
        import traceback
        traceback.print_exc()
        input("\n按回车键退出...")

