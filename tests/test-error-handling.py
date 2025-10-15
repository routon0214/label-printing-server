#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试错误处理和等待确认功能
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 70)
print("测试错误处理功能")
print("=" * 70)
print()

print("测试1: 正常执行后等待")
print("----------------------------------------------------------------------")

def wait_for_user_exit():
    """等待用户按键退出"""
    try:
        input("\n按回车键退出...")
    except:
        pass

def test_normal():
    print("程序正常执行...")
    print("所有功能运行正常")
    print("\n提示：正常情况下也会等待用户确认")
    wait_for_user_exit()

def test_error():
    print("\n测试2: 错误处理")
    print("----------------------------------------------------------------------")
    try:
        print("模拟一个错误...")
        raise Exception("这是一个测试错误")
    except Exception as e:
        print(f"\n捕获到错误: {e}")
        print("\n提示：错误发生后会等待用户确认")
        wait_for_user_exit()

# 选择测试
print("\n选择测试场景:")
print("1. 正常执行后等待")
print("2. 错误处理后等待")
print()

choice = input("请输入选项 (1 或 2): ").strip()

if choice == "1":
    test_normal()
elif choice == "2":
    test_error()
else:
    print("无效选项")
    wait_for_user_exit()

print("\n测试完成！")

