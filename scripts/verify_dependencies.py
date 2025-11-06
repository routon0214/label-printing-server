#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
打包依赖验证脚本
用于检查打包后的程序是否包含所有必要的依赖
"""

import sys

def check_imports():
    """检查关键模块是否可以导入"""
    results = []
    
    # 关键依赖列表
    dependencies = [
        ('paho.mqtt.client', 'MQTT客户端'),
        ('PIL', 'Pillow图像处理'),
        ('fastapi', 'FastAPI框架'),
        ('starlette', 'Starlette ASGI'),
        ('uvicorn', 'Uvicorn服务器'),
        ('jinja2', 'Jinja2模板引擎'),
        ('markupsafe', 'MarkupSafe (Jinja2依赖)'),
        ('pydantic', 'Pydantic数据验证'),
        ('anyio', 'AnyIO异步库'),
        ('h11', 'HTTP/1.1协议'),
    ]
    
    print("="*70)
    print(" "*20 + "依赖检查")
    print("="*70)
    print()
    
    all_ok = True
    
    for module_name, description in dependencies:
        try:
            __import__(module_name)
            status = "[OK] OK"
            results.append((module_name, description, True))
        except ImportError as e:
            status = f"[ERROR] FAIL: {e}"
            results.append((module_name, description, False))
            all_ok = False
        
        print(f"{status:12} {module_name:30} ({description})")
    
    print()
    print("="*70)
    
    if all_ok:
        print("[OK] 所有依赖检查通过！")
        print("="*70)
        return 0
    else:
        print("[ERROR] 发现缺失的依赖！")
        print("="*70)
        print()
        print("失败的依赖:")
        for module_name, description, ok in results:
            if not ok:
                print(f"  - {module_name} ({description})")
        print()
        print("建议:")
        print("  1. 重新运行打包脚本: python scripts\\build.py")
        print("  2. 检查打包日志中的错误")
        print("  3. 确保所有依赖已安装: pip install -r requirements.txt")
        print("="*70)
        return 1

def check_jinja2_detailed():
    """详细检查 Jinja2"""
    print("\n" + "="*70)
    print(" "*20 + "Jinja2 详细检查")
    print("="*70)
    print()
    
    try:
        import jinja2
        print(f"[OK] Jinja2 已导入")
        print(f"  版本: {jinja2.__version__}")
        print(f"  路径: {jinja2.__file__}")
        
        # 检查关键子模块
        submodules = [
            'jinja2.ext',
            'jinja2.loaders',
            'jinja2.runtime',
            'jinja2.environment',
        ]
        
        print("\n  子模块检查:")
        for submodule in submodules:
            try:
                __import__(submodule)
                print(f"    [OK] {submodule}")
            except ImportError as e:
                print(f"    [ERROR] {submodule}: {e}")
        
        # 尝试创建一个简单的模板
        print("\n  功能测试:")
        try:
            from jinja2 import Template
            template = Template("Hello {{ name }}!")
            result = template.render(name="World")
            print(f"    [OK] 模板渲染: {result}")
        except Exception as e:
            print(f"    [ERROR] 模板渲染失败: {e}")
        
        print("\n[OK] Jinja2 检查完成")
        return True
        
    except ImportError as e:
        print(f"[ERROR] Jinja2 导入失败: {e}")
        print("\n这是打包中最常见的问题！")
        print("解决方法:")
        print("  1. 确保打包脚本包含以下配置:")
        print("     --collect-all=jinja2")
        print("     --collect-all=markupsafe")
        print("     --hidden-import=jinja2")
        print("     --hidden-import=markupsafe")
        print("  2. 重新打包程序")
        return False

if __name__ == '__main__':
    print("\n依赖验证工具")
    print("用于检查打包后的程序是否包含所有必要的依赖\n")
    
    # 基础依赖检查
    exit_code = check_imports()
    
    # Jinja2 详细检查
    jinja2_ok = check_jinja2_detailed()
    
    if exit_code != 0 or not jinja2_ok:
        print("\n" + "="*70)
        print("[WARNING] 警告：发现问题，打包的程序可能无法正常运行")
        print("="*70)
        input("\n按回车键退出...")
        sys.exit(1)
    else:
        print("\n" + "="*70)
        print("[OK] 所有检查通过！打包的程序应该可以正常运行")
        print("="*70)
        input("\n按回车键退出...")
        sys.exit(0)

