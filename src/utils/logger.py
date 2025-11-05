#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志模块
提供统一的日志记录功能
"""

import os
import logging
import datetime
from logging.handlers import RotatingFileHandler


def setup_logger(name='label_printer', log_dir='data/logs', level=logging.INFO):
    """
    设置日志记录器
    
    Args:
        name: 日志记录器名称
        log_dir: 日志目录
        level: 日志级别
    
    Returns:
        logging.Logger: 配置好的日志记录器
    """
    # 确保日志目录存在
    os.makedirs(log_dir, exist_ok=True)
    
    # 创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 避免重复添加处理器
    if logger.handlers:
        return logger
    
    # 日志文件名（带日期）
    today = datetime.datetime.now().strftime('%Y%m%d')
    log_file = os.path.join(log_dir, f'{name}_{today}.log')
    
    # 文件处理器（自动轮转，最大10MB，保留5个文件）
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    
    # 日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


# 全局日志记录器
_logger = None


def get_logger(name='label_printer', log_dir='data/logs'):
    """获取全局日志记录器"""
    global _logger
    if _logger is None:
        _logger = setup_logger(name, log_dir)
    return _logger

