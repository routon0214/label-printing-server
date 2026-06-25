#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
打印代理打包脚本 - 将 print_agent.py 打包成单个 .exe 文件
双击即可运行，无需安装 Python。

使用方法:
    python build_agent.py
    或
    python build_agent.py --onefile   (单个exe)
    python build_agent.py --onedir    (文件夹模式)
"""

import os
import sys
import platform
import shutil
import subprocess

# Windows 控制台编码修复
if sys.platform == 'win32':
    import io
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def ensure_dependencies():
    """确保依赖已安装"""
    print("=" * 60)
    print("  步骤 1/4: 检查依赖")
    print("=" * 60)
    
    # 检查 pyinstaller
    try:
        import PyInstaller
        print(f"  [OK] PyInstaller {PyInstaller.__version__}")
    except ImportError:
        print("  [WARN] PyInstaller 未安装，正在安装...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])
        print("  [OK] PyInstaller 安装完成")
    
    # 检查 requests
    try:
        import requests
        print(f"  [OK] requests")
    except ImportError:
        print("  [WARN] requests 未安装，正在安装...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'requests'])
    
    # 检查 pywin32
    try:
        import win32print
        print(f"  [OK] pywin32")
    except ImportError:
        print("  [WARN] pywin32 未安装，正在安装...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pywin32'])
    
    print()


def clean_build():
    """清理旧的构建文件"""
    print("=" * 60)
    print("  步骤 2/4: 清理旧构建")
    print("=" * 60)
    
    for path in ['build', 'dist/print-agent']:
        if os.path.exists(path):
            shutil.rmtree(path)
            print(f"  [OK] 已清理 {path}")
    
    for spec in ['print-agent.spec']:
        if os.path.exists(spec):
            os.remove(spec)
            print(f"  [OK] 已删除 {spec}")
    
    print()


def build(mode='onedir'):
    """执行打包"""
    print("=" * 60)
    print(f"  步骤 3/4: 打包 print_agent.py ({mode})")
    print("=" * 60)
    
    is_win = sys.platform == 'win32'
    path_sep = ';' if is_win else ':'
    
    # 基础打包参数
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--clean',
        '--noconfirm',
        f'--{mode}',
        '--console',
        '--name=print-agent',
        '--distpath=dist',
        '--workpath=build',
        # 添加项目路径
        '--paths=.',
        '--paths=src',
    ]
    
    if mode == 'onedir':
        cmd.append('--add-data=src;src')
    
    # 隐藏导入 - Windows 打印相关
    if is_win:
        cmd.extend([
            '--hidden-import=win32print',
            '--hidden-import=win32ui',
            '--hidden-import=win32con',
            '--hidden-import=pywintypes',
        ])
    
    # 项目内部模块
    cmd.extend([
        '--hidden-import=src',
        '--hidden-import=src.core',
        '--hidden-import=src.core.printer',
        '--hidden-import=src.utils',
        '--hidden-import=src.utils.fuzzy_match',
        '--hidden-import=src.utils.log_manager',
        '--hidden-import=src.utils.logger',
        '--hidden-import=requests',
        '--hidden-import=json',
    ])
    
    cmd.append('print_agent.py')
    
    print(f"  命令: pyinstaller --{mode} --name=print-agent print_agent.py")
    print()
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
        print("  [OK] 打包成功!")
        
        if mode == 'onefile':
            exe_path = 'dist/print-agent.exe' if is_win else 'dist/print-agent'
        else:
            exe_path = f'dist/print-agent/print-agent.exe' if is_win else f'dist/print-agent/print-agent'
        
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"  [OK] 输出: {exe_path} ({size_mb:.1f} MB)")
        else:
            print(f"  [WARN] 未找到输出文件: {exe_path}")
    except subprocess.CalledProcessError as e:
        print(f"  [ERROR] 打包失败!")
        if e.stderr:
            # 只显示最后20行
            lines = e.stderr.strip().split('\n')
            for line in lines[-20:]:
                print(f"    {line}")
        return False
    
    print()
    return True


def verify():
    """验证打包结果"""
    print("=" * 60)
    print("  步骤 4/4: 验证结果")
    print("=" * 60)
    
    dist_dir = 'dist/print-agent'
    exe_name = 'print-agent.exe' if sys.platform == 'win32' else 'print-agent'
    
    # 检查 onedir
    exe_path = os.path.join(dist_dir, exe_name)
    if os.path.exists(exe_path):
        size_mb = os.path.getsize(exe_path) / (1024 * 1024)
        print(f"  [OK] {dist_dir}/{exe_name} ({size_mb:.1f} MB)")
        print()
        print("=" * 60)
        print("  打包完成！")
        print("=" * 60)
        print()
        print("  使用方法:")
        print(f"    1. 将 dist/print-agent/ 文件夹复制到任意 Windows 电脑")
        print(f"    2. 编辑 print_agent.py 中的配置（需修改 PRINTER_NAME）")
        print(f"      注意: onedir 模式可以修改同目录下的 src/ 源码")
        print(f"    3. 双击 print-agent.exe 即可运行")
        print()
        print("  或者用 onefile 模式生成单个 exe:")
        print(f"    python build_agent.py --onefile")
        print("    (配置需编译前在 print_agent.py 中改好)")
        print()
    else:
        print(f"  [WARN] 未找到 {exe_path}")
        print(f"  dist/ 目录内容:")
        if os.path.exists('dist'):
            for item in os.listdir('dist'):
                print(f"    {item}")
    
    print()


def main():
    """主函数"""
    print()
    print("=" * 60)
    print("  打印代理 打包工具")
    print("=" * 60)
    print()
    
    # 解析参数
    mode = 'onedir'
    if '--onefile' in sys.argv:
        mode = 'onefile'
    elif '--onedir' in sys.argv:
        mode = 'onedir'
    
    print(f"  打包模式: {mode}")
    print(f"  平台: {platform.system()} {platform.machine()}")
    print()
    
    try:
        ensure_dependencies()
        clean_build()
        if not build(mode):
            return 1
        verify()
        return 0
    except KeyboardInterrupt:
        print("\n  用户取消")
        return 1
    except Exception as e:
        print(f"\n  [ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
