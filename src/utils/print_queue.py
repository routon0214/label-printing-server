#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
打印队列管理模块
实现任务队列，避免并发打印冲突
"""

import os
import json
import time
import threading
import queue
import datetime
from typing import Dict, Any, Optional
from pathlib import Path


class PrintQueue:
    """打印队列管理器"""
    
    def __init__(self, queue_dir='data/print_queue', max_workers=1):
        """
        初始化打印队列
        
        Args:
            queue_dir: 队列文件存储目录
            max_workers: 最大并发打印数（建议1，避免冲突）
        """
        self.queue_dir = queue_dir
        self.max_workers = max_workers
        self.task_queue = queue.Queue()
        self.is_running = False
        self.worker_thread = None
        self.processed_count = 0
        self.failed_count = 0
        
        # 确保队列目录存在
        os.makedirs(queue_dir, exist_ok=True)
        
        print(f"[打印队列] 初始化完成")
        print(f"  队列目录: {queue_dir}")
        print(f"  并发数: {max_workers}")
    
    def start(self):
        """启动队列处理线程"""
        if self.is_running:
            print("[打印队列] 已在运行中")
            return
        
        self.is_running = True
        self.worker_thread = threading.Thread(
            target=self._worker,
            daemon=True,
            name="PrintQueueWorker"
        )
        self.worker_thread.start()
        print("[打印队列] 工作线程已启动")
    
    def stop(self):
        """停止队列处理"""
        if not self.is_running:
            return
        
        print("[打印队列] 正在停止...")
        self.is_running = False
        
        # 等待线程结束
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=5)
        
        print("[打印队列] 已停止")
        print(f"  已处理: {self.processed_count} 个任务")
        print(f"  失败: {self.failed_count} 个任务")
    
    def add_task(self, task_data: Dict[str, Any], printer_instance: Any) -> str:
        """
        添加打印任务到队列
        
        Args:
            task_data: 打印任务数据（包含print_type, format, content等）
            printer_instance: 打印机实例
            
        Returns:
            任务ID
        """
        # 生成任务ID
        task_id = self._generate_task_id()
        
        # 保存任务到文件
        task_file = self._save_task_file(task_id, task_data)
        
        # 添加到队列
        task_info = {
            'task_id': task_id,
            'task_file': task_file,
            'task_data': task_data,
            'printer': printer_instance,
            'created_at': datetime.datetime.now().isoformat()
        }
        
        self.task_queue.put(task_info)
        
        print(f"[打印队列] 任务已加入队列: {task_id}")
        print(f"  队列长度: {self.task_queue.qsize()}")
        
        return task_id
    
    def _generate_task_id(self) -> str:
        """生成任务ID"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        return f"task_{timestamp}"
    
    def _save_task_file(self, task_id: str, task_data: Dict[str, Any]) -> str:
        """
        保存任务到文件
        
        Args:
            task_id: 任务ID
            task_data: 任务数据
            
        Returns:
            任务文件路径
        """
        task_file = os.path.join(self.queue_dir, f"{task_id}.json")
        
        try:
            with open(task_file, 'w', encoding='utf-8') as f:
                json.dump(task_data, f, ensure_ascii=False, indent=2)
            
            print(f"[打印队列] 任务已保存: {task_file}")
            return task_file
        
        except Exception as e:
            print(f"[打印队列] 保存任务文件失败: {e}")
            return None
    
    def _delete_task_file(self, task_file: str):
        """
        删除任务文件
        
        Args:
            task_file: 任务文件路径
        """
        try:
            if task_file and os.path.exists(task_file):
                os.remove(task_file)
                print(f"[打印队列] 任务文件已删除: {os.path.basename(task_file)}")
        except Exception as e:
            print(f"[打印队列] 删除任务文件失败: {e}")
    
    def _worker(self):
        """队列处理工作线程"""
        print("[打印队列] 工作线程运行中...")
        
        while self.is_running:
            try:
                # 从队列获取任务（超时1秒）
                task_info = self.task_queue.get(timeout=1)
                
                task_id = task_info['task_id']
                task_file = task_info['task_file']
                task_data = task_info['task_data']
                printer = task_info['printer']
                
                print(f"\n{'='*70}")
                print(f"[打印队列] 开始处理任务: {task_id}")
                print(f"{'='*70}")
                
                # 执行打印
                success = self._execute_print(task_data, printer)
                
                # 更新统计
                self.processed_count += 1
                if not success:
                    self.failed_count += 1
                
                print(f"[打印队列] 任务完成: {task_id}")
                print(f"  结果: {'✓ 成功' if success else '✗ 失败'}")
                print(f"  已处理: {self.processed_count} | 失败: {self.failed_count}")
                print(f"{'='*70}\n")
                
                # 删除任务文件（不管成功与否）
                self._delete_task_file(task_file)
                
                # 标记任务完成
                self.task_queue.task_done()
            
            except queue.Empty:
                # 队列为空，继续等待
                continue
            
            except Exception as e:
                print(f"[打印队列] 处理任务时出错: {e}")
                import traceback
                traceback.print_exc()
    
    def _execute_print(self, task_data: Dict[str, Any], printer: Any) -> bool:
        """
        执行打印任务
        
        Args:
            task_data: 任务数据
            printer: 打印机实例
            
        Returns:
            是否成功
        """
        try:
            print_type = task_data.get('print_type', 'label').lower()
            data_format = task_data.get('format', 'structured')
            content = task_data.get('content')
            
            print(f"  打印类型: {print_type}")
            print(f"  数据格式: {data_format}")
            
            # 根据打印类型执行
            if print_type == 'label':
                return self._execute_label_print(data_format, content, printer, task_data)
            
            elif print_type in ['escpos', 'receipt']:
                return self._execute_escpos_print(data_format, content, printer, task_data)
            
            else:
                print(f"  [错误] 不支持的打印类型: {print_type}")
                return False
        
        except Exception as e:
            print(f"  [错误] 执行打印失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _execute_label_print(self, data_format: str, content: Any, 
                            printer: Any, task_data: Dict) -> bool:
        """执行标签打印"""
        try:
            # 导入需要的模块
            from src.utils.zpl_chinese_converter import detect_and_convert_zpl
            from src.core.zpl_generator import ZPLGenerator
            
            zpl_generator = ZPLGenerator()
            
            if data_format == 'zpl':
                # 直接ZPL代码
                zpl_code = content
                zpl_code, was_converted = detect_and_convert_zpl(zpl_code)
                if was_converted:
                    print("  [OK] ZPL中文已转换为图像")
            
            elif data_format == 'structured':
                # 结构化数据，生成ZPL
                print("  [INFO] 从结构化数据生成ZPL...")
                zpl_code = zpl_generator.generate_label_zpl(content)
            
            else:
                print(f"  [错误] 不支持的标签格式: {data_format}")
                return False
            
            print(f"  [INFO] ZPL代码长度: {len(zpl_code)} 字符")
            
            # 执行打印
            result = printer.print_label(zpl_code)
            return result
        
        except Exception as e:
            print(f"  [错误] 标签打印失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _execute_escpos_print(self, data_format: str, content: Any,
                             printer: Any, task_data: Dict) -> bool:
        """执行ESC/POS打印"""
        try:
            if data_format == 'raw':
                # 原始文本格式
                receipt_data = {
                    'raw_text': content,
                    'encoding': task_data.get('encoding', 'gb2312')
                }
            
            elif data_format == 'structured':
                # 结构化格式
                receipt_data = content
            
            else:
                print(f"  [错误] 不支持的小票格式: {data_format}")
                return False
            
            # 执行打印
            result = printer.print_receipt(receipt_data)
            return result
        
        except Exception as e:
            print(f"  [错误] ESC/POS打印失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取队列状态
        
        Returns:
            状态字典
        """
        return {
            'is_running': self.is_running,
            'queue_size': self.task_queue.qsize(),
            'processed_count': self.processed_count,
            'failed_count': self.failed_count,
            'success_rate': self._calculate_success_rate()
        }
    
    def _calculate_success_rate(self) -> float:
        """计算成功率"""
        if self.processed_count == 0:
            return 100.0
        
        success_count = self.processed_count - self.failed_count
        return round((success_count / self.processed_count) * 100, 2)
    
    def clear_queue(self):
        """清空队列（不推荐使用）"""
        while not self.task_queue.empty():
            try:
                task_info = self.task_queue.get_nowait()
                self._delete_task_file(task_info.get('task_file'))
                self.task_queue.task_done()
            except queue.Empty:
                break
        
        print("[打印队列] 队列已清空")


# 全局打印队列实例
_print_queue = None


def get_print_queue() -> PrintQueue:
    """获取全局打印队列实例"""
    global _print_queue
    if _print_queue is None:
        _print_queue = PrintQueue()
        _print_queue.start()
    return _print_queue

