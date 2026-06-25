#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模板管理器模块
管理打印模板的 CRUD 操作，与 vue-print-designer 的 API 规范兼容
"""

import os
import json
import time
import threading
from pathlib import Path
from typing import Optional, Dict, List, Any


class TemplateManager:
    """模板管理器 - 管理打印模板的持久化存储"""

    def __init__(self, template_dir: str = 'data/templates'):
        """
        初始化模板管理器
        
        Args:
            template_dir: 模板存储目录路径
        """
        self._template_dir = template_dir
        self._index_file = os.path.join(template_dir, 'index.json')
        self._lock = threading.Lock()

        # 确保目录存在
        os.makedirs(template_dir, exist_ok=True)

        # 确保索引文件存在
        if not os.path.exists(self._index_file):
            self._save_index([])

    def _load_index(self) -> List[Dict[str, Any]]:
        """加载模板索引"""
        try:
            with open(self._index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _save_index(self, index: List[Dict[str, Any]]):
        """保存模板索引"""
        with open(self._index_file, 'w', encoding='utf-8') as f:
            json.dump(index, f, ensure_ascii=False, indent=2)

    def _get_template_path(self, template_id: str) -> str:
        """获取模板文件路径"""
        # 安全处理 ID，防止路径遍历
        safe_id = "".join(c for c in template_id if c.isalnum() or c in "-_.")
        return os.path.join(self._template_dir, f"{safe_id}.json")

    def list_templates(self, include_data: bool = False) -> List[Dict[str, Any]]:
        """
        列出所有模板
        
        Args:
            include_data: 是否包含模板数据
        
        Returns:
            模板列表
        """
        with self._lock:
            index = self._load_index()

            if include_data:
                result = []
                for item in index:
                    template_id = item.get('id')
                    if template_id:
                        full_template = self.get_template(template_id)
                        if full_template:
                            result.append(full_template)
                        else:
                            # 文件丢失，返回索引信息
                            result.append(item)
                    else:
                        result.append(item)
                return result
            else:
                # 只返回基础信息
                return [
                    {
                        'id': item.get('id'),
                        'name': item.get('name'),
                        'updatedAt': item.get('updatedAt'),
                    }
                    for item in index
                    if item.get('id')
                ]

    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """
        获取单个模板的完整数据
        
        Args:
            template_id: 模板 ID
        
        Returns:
            模板数据，不存在则返回 None
        """
        file_path = self._get_template_path(template_id)
        if not os.path.exists(file_path):
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return None

    def upsert_template(self, template: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建或更新模板
        
        Args:
            template: 模板数据，必须包含 id, name, data 字段
        
        Returns:
            保存后的完整模板数据
        """
        template_id = template.get('id', '')
        if not template_id:
            raise ValueError("模板必须包含 id 字段")

        # 构建完整模板对象
        now = int(time.time() * 1000)  # 毫秒时间戳
        template_data = {
            'id': template_id,
            'name': template.get('name', '未命名模板'),
            'data': template.get('data', {}),
            'updatedAt': template.get('updatedAt', now),
            'permissions': template.get('permissions', None),
            'ext': template.get('ext', {}),
        }

        with self._lock:
            # 保存模板文件
            file_path = self._get_template_path(template_id)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(template_data, f, ensure_ascii=False, indent=2)

            # 更新索引
            index = self._load_index()
            found = False
            for i, item in enumerate(index):
                if item.get('id') == template_id:
                    index[i] = {
                        'id': template_id,
                        'name': template_data['name'],
                        'updatedAt': template_data['updatedAt'],
                    }
                    found = True
                    break

            if not found:
                index.append({
                    'id': template_id,
                    'name': template_data['name'],
                    'updatedAt': template_data['updatedAt'],
                })

            # 按更新时间排序（最新的在前）
            index.sort(key=lambda x: x.get('updatedAt', 0), reverse=True)
            self._save_index(index)

        return template_data

    def delete_template(self, template_id: str) -> bool:
        """
        删除模板
        
        Args:
            template_id: 模板 ID
        
        Returns:
            是否成功删除
        """
        with self._lock:
            # 删除模板文件
            file_path = self._get_template_path(template_id)
            deleted = False
            if os.path.exists(file_path):
                os.remove(file_path)
                deleted = True

            # 更新索引
            index = self._load_index()
            index = [item for item in index if item.get('id') != template_id]
            self._save_index(index)

            return deleted

    def get_template_count(self) -> int:
        """获取模板总数"""
        return len(self._load_index())

    def search_templates(self, keyword: str) -> List[Dict[str, Any]]:
        """
        按关键词搜索模板
        
        Args:
            keyword: 搜索关键词
        
        Returns:
            匹配的模板列表
        """
        keyword_lower = keyword.lower()
        templates = self.list_templates()
        return [
            t for t in templates
            if keyword_lower in t.get('name', '').lower()
            or keyword_lower in t.get('id', '').lower()
        ]
