#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志管理模块
提供日志查询、过滤和清理功能
"""

import os
import glob
import datetime
from typing import List, Dict, Optional


class LogManager:
    """日志管理器"""
    
    def __init__(self, log_dir='data/logs', retention_days=7):
        """
        初始化日志管理器
        
        Args:
            log_dir: 日志目录
            retention_days: 日志保留天数
        """
        self.log_dir = log_dir
        self.retention_days = retention_days
        os.makedirs(log_dir, exist_ok=True)
    
    def get_log_files(self) -> List[str]:
        """
        获取所有日志文件列表
        
        Returns:
            日志文件路径列表（按修改时间降序）
        """
        pattern = os.path.join(self.log_dir, '*.log')
        log_files = glob.glob(pattern)
        
        # 按修改时间降序排序（最新的在前面）
        log_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        
        return log_files
    
    def read_logs(self, filename: Optional[str] = None, 
                  lines: int = 100, 
                  level: Optional[str] = None,
                  search: Optional[str] = None) -> List[Dict]:
        """
        读取日志内容
        
        Args:
            filename: 日志文件名（如果为None，读取最新的日志）
            lines: 读取的行数
            level: 过滤日志级别（ERROR, WARNING, INFO等）
            search: 搜索关键词
            
        Returns:
            日志条目列表，每条包含时间、级别、内容等信息
        """
        if filename:
            log_file = os.path.join(self.log_dir, filename)
        else:
            # 获取最新的日志文件
            log_files = self.get_log_files()
            if not log_files:
                return []
            log_file = log_files[0]
        
        if not os.path.exists(log_file):
            return []
        
        logs = []
        try:
            with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
                # 读取所有行
                all_lines = f.readlines()
                
                # 从后往前读取最近的行
                recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
                
                for line in recent_lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # 解析日志行
                    log_entry = self._parse_log_line(line)
                    
                    # 应用过滤条件
                    if level and log_entry.get('level') != level:
                        continue
                    
                    if search and search.lower() not in line.lower():
                        continue
                    
                    logs.append(log_entry)
        
        except Exception as e:
            print(f"读取日志文件失败: {e}")
            return []
        
        # 反转列表，使最新的日志在前面
        logs.reverse()
        return logs
    
    def _parse_log_line(self, line: str) -> Dict:
        """
        解析日志行
        
        Args:
            line: 日志行文本
            
        Returns:
            解析后的日志条目字典
        """
        # 标准格式: 2025-11-06 12:34:56 - logger_name - LEVEL - message
        parts = line.split(' - ', 3)
        
        if len(parts) >= 4:
            return {
                'timestamp': parts[0].strip(),
                'logger': parts[1].strip(),
                'level': parts[2].strip(),
                'message': parts[3].strip()
            }
        else:
            # 无法解析的行，作为普通消息处理
            return {
                'timestamp': '',
                'logger': '',
                'level': 'INFO',
                'message': line
            }
    
    def get_log_stats(self) -> Dict:
        """
        获取日志统计信息
        
        Returns:
            统计信息字典
        """
        log_files = self.get_log_files()
        
        stats = {
            'total_files': len(log_files),
            'total_size': 0,
            'files': []
        }
        
        for log_file in log_files:
            try:
                file_stat = os.stat(log_file)
                file_info = {
                    'name': os.path.basename(log_file),
                    'size': file_stat.st_size,
                    'modified': datetime.datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                }
                stats['files'].append(file_info)
                stats['total_size'] += file_stat.st_size
            except Exception as e:
                print(f"获取文件信息失败 {log_file}: {e}")
        
        return stats
    
    def clean_old_logs(self) -> int:
        """
        清理超过保留天数的日志文件
        
        Returns:
            删除的文件数量
        """
        if self.retention_days <= 0:
            return 0
        
        current_time = datetime.datetime.now()
        cutoff_time = current_time - datetime.timedelta(days=self.retention_days)
        
        log_files = self.get_log_files()
        deleted_count = 0
        
        for log_file in log_files:
            try:
                file_mtime = datetime.datetime.fromtimestamp(os.path.getmtime(log_file))
                
                if file_mtime < cutoff_time:
                    os.remove(log_file)
                    deleted_count += 1
                    print(f"已删除过期日志: {log_file}")
            
            except Exception as e:
                print(f"删除日志文件失败 {log_file}: {e}")
        
        return deleted_count
    
    def get_log_levels_count(self, filename: Optional[str] = None) -> Dict[str, int]:
        """
        统计不同日志级别的数量
        
        Args:
            filename: 日志文件名（如果为None，统计最新的日志）
            
        Returns:
            级别统计字典
        """
        logs = self.read_logs(filename=filename, lines=10000)  # 读取最近10000条
        
        level_counts = {
            'ERROR': 0,
            'WARNING': 0,
            'INFO': 0,
            'DEBUG': 0
        }
        
        for log in logs:
            level = log.get('level', 'INFO')
            if level in level_counts:
                level_counts[level] += 1
            else:
                level_counts['INFO'] += 1
        
        return level_counts

