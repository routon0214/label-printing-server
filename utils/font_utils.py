#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
字体工具模块
提供跨平台的中文字体路径获取功能
"""

import os
import platform


def get_font_paths():
    """
    获取系统中文字体路径（跨平台）
    
    Returns:
        list: 字体文件路径列表
    """
    system = platform.system()
    
    if system == 'Windows':
        return [
            'C:/Windows/Fonts/msyh.ttc',      # 微软雅黑
            'C:/Windows/Fonts/simhei.ttf',    # 黑体
            'C:/Windows/Fonts/simsun.ttc',    # 宋体
        ]
    elif system == 'Linux':
        return [
            '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',           # 文泉驿正黑
            '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',         # 文泉驿微米黑
            '/usr/share/fonts/truetype/arphic/uming.ttc',             # AR PL UMing
            '/usr/share/fonts/truetype/arphic/ukai.ttc',              # AR PL UKai
            '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', # Noto Sans CJK
            '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf', # Droid
        ]
    elif system == 'Darwin':  # macOS
        return [
            '/System/Library/Fonts/PingFang.ttc',
            '/Library/Fonts/Songti.ttc',
        ]
    else:
        return []

