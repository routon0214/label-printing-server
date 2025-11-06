#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复Unicode特殊字符
将[OK]等Unicode字符替换为兼容的ASCII字符，避免在Windows控制台显示乱码
"""

import os
import glob

# 定义需要替换的字符
REPLACEMENTS = {
    '[OK]': '[OK]',
    '[ERROR]': '[ERROR]',
    '[WARNING]': '[WARNING]',
    '->': '->',
    'x': 'x',
    '...': '...',
}

# 需要处理的文件模式
FILE_PATTERNS = [
    'src/**/*.py',
    'tests/**/*.py',
    'scripts/**/*.py',
    'web_app.py',
    'app.py',
    'init.py',
]

def fix_file(file_path):
    """修复单个文件中的Unicode字符"""
    try:
        # 读取文件
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否需要修改
        original_content = content
        modified = False
        
        # 执行替换
        for old_char, new_char in REPLACEMENTS.items():
            if old_char in content:
                content = content.replace(old_char, new_char)
                modified = True
                count = original_content.count(old_char)
                print(f"  {file_path}: 替换 '{old_char}' -> '{new_char}' ({count} 处)")
        
        # 如果有修改，写回文件
        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        
        return False
    
    except Exception as e:
        print(f"  错误: {file_path}: {e}")
        return False

def main():
    """主函数"""
    print("=" * 70)
    print("修复Unicode特殊字符")
    print("=" * 70)
    print()
    
    # 收集所有需要处理的文件
    all_files = []
    for pattern in FILE_PATTERNS:
        files = glob.glob(pattern, recursive=True)
        all_files.extend(files)
    
    # 去重
    all_files = list(set(all_files))
    
    print(f"找到 {len(all_files)} 个Python文件")
    print()
    
    # 处理每个文件
    modified_count = 0
    for file_path in all_files:
        if fix_file(file_path):
            modified_count += 1
    
    print()
    print("=" * 70)
    print(f"完成！共修改 {modified_count} 个文件")
    print("=" * 70)

if __name__ == '__main__':
    main()

