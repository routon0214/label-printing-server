#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成修复后的ZPL文件"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from src.utils.image_utils import text_to_image_zpl

print("正在生成修复后的ZPL文件...")

zpl_parts = []
zpl_parts.append("^XA")  # 开始
zpl_parts.append("^PW480")  # 标签宽度
zpl_parts.append("^LL320")  # 标签长度

# 1. 容器类型
print("转换: 容器类型")
hex_data, w, h, bpr, total = text_to_image_zpl("容器类型", 30)
if hex_data:
    zpl_parts.append(f"^FO20,10^GFA,{total},{total},{bpr},{hex_data}^FS")

# 2. 二维码
zpl_parts.append("^FO20,60^BQN,2,5^FDQA,ECKQ^FS")

# 3. 二次库区托盘
print("转换: 二次库区托盘")
hex_data, w, h, bpr, total = text_to_image_zpl("二次库区托盘", 36)
if hex_data:
    zpl_parts.append(f"^FO240,60^GFA,{total},{total},{bpr},{hex_data}^FS")

# 4. 编号
print("转换: 编号:ECKQ")
hex_data, w, h, bpr, total = text_to_image_zpl("编号:ECKQ", 36)
if hex_data:
    zpl_parts.append(f"^FO240,120^GFA,{total},{total},{bpr},{hex_data}^FS")

# 5. 尺寸
print("转换: 尺寸:null*0*null")
hex_data, w, h, bpr, total = text_to_image_zpl("尺寸:null*0*null", 36)
if hex_data:
    zpl_parts.append(f"^FO240,170^GFA,{total},{total},{bpr},{hex_data}^FS")

# 6. 载重
print("转换: 载重:0")
hex_data, w, h, bpr, total = text_to_image_zpl("载重:0", 36)
if hex_data:
    zpl_parts.append(f"^FO240,220^GFA,{total},{total},{bpr},{hex_data}^FS")

zpl_parts.append("^XZ")  # 结束

# 保存
output_file = "data/print_text_fixed.zpl"
zpl_code = '\n'.join(zpl_parts)

with open(output_file, 'w', encoding='utf-8') as f:
    f.write(zpl_code)

print(f"\n✓ 已生成: {output_file}")
print(f"  文件大小: {len(zpl_code)} 字符")
print(f"  命令数: {len(zpl_parts)}")
print("\n请通过Web界面上传此文件进行打印测试")

