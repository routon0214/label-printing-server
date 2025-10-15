#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模糊匹配工具模块
提供打印机名称模糊搜索功能
"""

import re


def fuzzy_match_printer(printer_name, search_pattern):
    """
    模糊匹配打印机名称
    
    Args:
        printer_name: 打印机名称
        search_pattern: 搜索模式（支持通配符和正则）
        
    Returns:
        int: 匹配分数（0-100），越高越匹配
    """
    if not search_pattern or not printer_name:
        return 0
    
    printer_lower = printer_name.lower()
    pattern_lower = search_pattern.lower()
    
    # 1. 完全匹配 - 100分
    if printer_lower == pattern_lower:
        return 100
    
    # 2. 开头匹配 - 90分
    if printer_lower.startswith(pattern_lower):
        return 90
    
    # 3. 包含关键词 - 根据位置给分
    if pattern_lower in printer_lower:
        # 越靠前分数越高
        pos = printer_lower.index(pattern_lower)
        score = 80 - (pos * 2)
        return max(score, 60)
    
    # 4. 分词匹配 - 检查是否包含所有关键词
    pattern_words = re.findall(r'\w+', pattern_lower)
    if pattern_words:
        matches = sum(1 for word in pattern_words if word in printer_lower)
        if matches == len(pattern_words):
            return 50 + (matches * 5)
        elif matches > 0:
            return 30 + (matches * 5)
    
    # 5. 模糊字符匹配 - 检查字符顺序
    pattern_chars = [c for c in pattern_lower if c.isalnum()]
    printer_chars = [c for c in printer_lower if c.isalnum()]
    
    if not pattern_chars:
        return 0
    
    matched = 0
    p_idx = 0
    for char in printer_chars:
        if p_idx < len(pattern_chars) and char == pattern_chars[p_idx]:
            matched += 1
            p_idx += 1
    
    if matched == len(pattern_chars):
        ratio = matched / len(printer_chars)
        return int(ratio * 40)
    
    return 0


def find_best_printer(printers, search_pattern):
    """
    从打印机列表中查找最匹配的打印机
    
    Args:
        printers: 打印机列表或字典
        search_pattern: 搜索模式
        
    Returns:
        str: 最匹配的打印机名称，未找到返回None
    """
    if not printers or not search_pattern:
        return None
    
    # 如果是字典（CUPS），转换为列表
    if isinstance(printers, dict):
        printer_list = list(printers.keys())
    else:
        printer_list = printers
    
    # 计算每个打印机的匹配分数
    scores = []
    for printer in printer_list:
        score = fuzzy_match_printer(printer, search_pattern)
        if score > 0:
            scores.append((printer, score))
    
    # 按分数排序
    scores.sort(key=lambda x: x[1], reverse=True)
    
    # 返回最高分
    if scores and scores[0][1] >= 30:  # 最低30分才认为匹配
        return scores[0][0]
    
    return None


def fuzzy_search_printer(search_pattern):
    """
    在系统中搜索打印机（自动获取打印机列表）
    
    Args:
        search_pattern: 搜索模式
        
    Returns:
        str: 最匹配的打印机名称，未找到返回None
    """
    if not search_pattern:
        return None
    
    try:
        import platform
        system = platform.system()
        
        if system == 'Windows':
            try:
                import win32print
                # 获取所有打印机
                printers = [p[2] for p in win32print.EnumPrinters(2)]
                return find_best_printer(printers, search_pattern)
            except ImportError:
                return None
        
        elif system == 'Linux':
            try:
                import cups
                conn = cups.Connection()
                printers = conn.getPrinters()
                return find_best_printer(printers, search_pattern)
            except:
                return None
        
        return None
        
    except Exception:
        return None
