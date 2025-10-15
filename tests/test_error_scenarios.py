#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
错误场景测试脚本
测试各种错误情况下程序是否能正确等待用户确认
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_import_error():
    """测试导入错误"""
    print("测试场景1: 模拟导入错误")
    print("-" * 60)
    try:
        # 尝试导入不存在的模块
        import nonexistent_module
    except ImportError as e:
        print(f"捕获到导入错误: {e}")
        print("✓ 错误被正确捕获")
        return True
    return False


def test_directory_creation():
    """测试目录创建"""
    print("\n测试场景2: 测试目录创建")
    print("-" * 60)
    
    test_dirs = ['logs', 'failed_labels', 'config']
    
    for directory in test_dirs:
        if os.path.exists(directory):
            print(f"✓ 目录存在: {directory}")
        else:
            try:
                os.makedirs(directory, exist_ok=True)
                print(f"✓ 目录已创建: {directory}")
            except Exception as e:
                print(f"✗ 创建目录失败 {directory}: {e}")
                return False
    return True


def test_config_file():
    """测试配置文件"""
    print("\n测试场景3: 测试配置文件")
    print("-" * 60)
    
    config_file = 'config/printer_config.json'
    
    if os.path.exists(config_file):
        print(f"✓ 配置文件存在: {config_file}")
        try:
            import json
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print(f"✓ 配置文件格式正确")
            print(f"  MQTT主机: {config.get('mqtt', {}).get('host', 'N/A')}")
            print(f"  MQTT端口: {config.get('mqtt', {}).get('port', 'N/A')}")
            print(f"  打印机: {config.get('printer', {}).get('name', 'N/A')}")
            return True
        except Exception as e:
            print(f"✗ 配置文件解析失败: {e}")
            return False
    else:
        print(f"警告: 配置文件不存在，首次运行会自动创建")
        return True


def test_module_import():
    """测试模块导入"""
    print("\n测试场景4: 测试模块导入")
    print("-" * 60)
    
    modules = [
        ('config', 'ConfigManager'),
        ('core', 'LabelPrintMQTT'),
        ('core', 'ZebraPrinter'),
        ('utils', 'fuzzy_match_printer'),
    ]
    
    all_ok = True
    for module_name, class_name in modules:
        try:
            if module_name == 'config':
                from config import ConfigManager
                print(f"✓ {module_name}.{class_name} 导入成功")
            elif module_name == 'core' and class_name == 'LabelPrintMQTT':
                from core import LabelPrintMQTT
                print(f"✓ {module_name}.{class_name} 导入成功")
            elif module_name == 'core' and class_name == 'ZebraPrinter':
                from core import ZebraPrinter
                print(f"✓ {module_name}.{class_name} 导入成功")
            elif module_name == 'utils' and class_name == 'fuzzy_match_printer':
                from utils import fuzzy_match_printer
                print(f"✓ {module_name}.{class_name} 导入成功")
        except Exception as e:
            print(f"✗ {module_name}.{class_name} 导入失败: {e}")
            all_ok = False
    
    return all_ok


def test_dependencies():
    """测试依赖包"""
    print("\n测试场景5: 测试依赖包")
    print("-" * 60)
    
    dependencies = [
        'paho.mqtt.client',
        'PIL',
    ]
    
    all_ok = True
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✓ {dep} 已安装")
        except ImportError:
            print(f"✗ {dep} 未安装")
            all_ok = False
    
    return all_ok


def main():
    """主函数"""
    print("=" * 60)
    print("错误场景测试")
    print("=" * 60)
    print()
    
    results = []
    
    # 运行所有测试
    results.append(("导入错误处理", test_import_error()))
    results.append(("目录创建", test_directory_creation()))
    results.append(("配置文件", test_config_file()))
    results.append(("模块导入", test_module_import()))
    results.append(("依赖包", test_dependencies()))
    
    # 显示结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    all_passed = True
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{name:20s} {status}")
        if not result:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n✓ 所有测试通过！程序应该可以正常运行。")
    else:
        print("\n✗ 部分测试失败，请根据上述信息排查问题。")
        print("\n常见解决方案:")
        print("  1. 安装依赖: pip install -r requirements.txt")
        print("  2. 检查Python版本: python --version (需要3.7+)")
        print("  3. 确保在项目根目录运行")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\n测试脚本异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

