#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
目录模式打包脚本（更可靠）
使用目录模式而不是单文件模式，更容易调试依赖问题
"""

import os
import sys
import platform
import shutil
import subprocess
import zipfile
from datetime import datetime

# Windows 控制台编码修复
if sys.platform == 'win32':
    import io
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def get_platform_info():
    """获取平台信息"""
    system = platform.system()
    machine = platform.machine()
    
    if system == 'Windows':
        return 'windows', machine.lower()
    elif system == 'Linux':
        return 'linux', machine.lower()
    elif system == 'Darwin':
        return 'macos', machine.lower()
    else:
        return system.lower(), machine.lower()


def clean_build_dirs():
    """清理构建目录和旧的 spec 文件"""
    dirs_to_clean = ['build', 'dist/']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"清理目录: {dir_name}")
            shutil.rmtree(dir_name)
    
    # 清理旧的 spec 文件
    spec_files = ['label-printing-server.spec', 'app.spec']
    for spec_file in spec_files:
        if os.path.exists(spec_file):
            print(f"清理旧的spec文件: {spec_file}")
            os.remove(spec_file)


def build_executable():
    """构建可执行文件（目录模式）"""
    system, machine = get_platform_info()
    
    # 切换到项目根目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    os.chdir(project_root)
    
    print("=" * 70)
    print(f"开始打包应用（目录模式）")
    print("=" * 70)
    print(f"平台: {system}")
    print(f"架构: {machine}")
    print(f"Python: {sys.version.split()[0]}")
    print(f"项目根目录: {project_root}")
    print("=" * 70)
    print("\n[WARNING] 使用目录模式打包（更容易调试依赖问题）")
    print()
    
    # 清理旧的构建文件
    clean_build_dirs()
    
    # 根据平台设置路径分隔符
    path_sep = ';' if system == 'windows' else ':'
    
    # 构建命令 - 目录模式（不使用 --onefile）
    cmd = [
        'pyinstaller',
        '--clean',
        '--noconfirm',
        # '--onefile',  # ❌ 注释掉单文件模式
        '--onedir',     # ✅ 使用目录模式
        '--console',
        '--name=label-printing-server',
        '--distpath=dist',
        '--workpath=build',
        # 收集所有必要的包
        '--collect-all=paho',
        '--collect-all=PIL',
        '--collect-all=fastapi',
        '--collect-all=starlette',
        '--collect-all=uvicorn',
        '--collect-all=jinja2',
        '--collect-all=markupsafe',
        # 元数据（只保留确认可用的）
        '--copy-metadata=paho-mqtt',
        '--copy-metadata=fastapi',
        '--copy-metadata=starlette',
        '--copy-metadata=uvicorn',
        # MQTT
        '--hidden-import=paho.mqtt.client',
        '--hidden-import=paho.mqtt.publish',
        '--hidden-import=paho.mqtt.subscribe',
        # 图像
        '--hidden-import=PIL',
        '--hidden-import=PIL.Image',
        '--hidden-import=PIL.ImageDraw',
        '--hidden-import=PIL.ImageFont',
        # FastAPI
        '--hidden-import=fastapi',
        '--hidden-import=starlette',
        '--hidden-import=uvicorn',
        # Jinja2（完整）
        '--hidden-import=jinja2',
        '--hidden-import=markupsafe',
        # Pydantic
        '--hidden-import=pydantic',
        # 其他
        '--hidden-import=anyio',
        '--hidden-import=h11',
        '--hidden-import=httptools',
        '--hidden-import=websockets',
        '--paths=.',
        '--paths=src',
    ]
    
    # 添加数据文件
    print("\n检查数据文件...")
    if os.path.exists('templates'):
        cmd.append(f'--add-data=templates{path_sep}templates')
        print("  [OK] 将包含 templates 目录")
    else:
        print("  [WARNING] templates 目录不存在")
    
    if os.path.exists('static'):
        cmd.append(f'--add-data=static{path_sep}static')
        print("  [OK] 将包含 static 目录")
    
    # Windows特定
    if system == 'windows':
        cmd.extend([
            '--hidden-import=win32print',
            '--hidden-import=win32ui',
            '--hidden-import=win32con',
            '--hidden-import=pywintypes',
        ])
    
    # 添加入口文件
    cmd.append('app.py')
    
    print("\n执行打包命令:")
    print(" ".join(cmd))
    print()
    
    try:
        subprocess.check_call(cmd)
        print("\n" + "=" * 70)
        print("[SUCCESS] 打包成功！")
        print("=" * 70)
        
        # 检查输出目录
        dist_dir = 'dist/label-printing-server'
        if os.path.exists(dist_dir):
            print(f"\n[OK] 应用目录已生成: {dist_dir}/")
            
            # 列出目录内容
            print("\n目录内容:")
            for item in os.listdir(dist_dir):
                item_path = os.path.join(dist_dir, item)
                if os.path.isfile(item_path):
                    size = os.path.getsize(item_path) / (1024 * 1024)
                    if size > 1:  # 只显示大于1MB的文件
                        print(f"  {item} ({size:.2f} MB)")
                elif os.path.isdir(item_path):
                    print(f"  {item}/")
            
            # 创建启动脚本
            create_launch_script(system, dist_dir)
        
        return True
        
    except subprocess.CalledProcessError as e:
        print("\n" + "=" * 70)
        print(f"[ERROR] 打包失败: {e}")
        print("=" * 70)
        return False


def create_launch_script(system, dist_dir):
    """创建启动脚本"""
    if system == 'windows':
        # Windows 批处理文件
        script_path = os.path.join('dist', 'start.bat')
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write('@echo off\n')
            f.write('cd label-printing-server\n')
            f.write('label-printing-server.exe\n')
            f.write('pause\n')
        print(f"\n[OK] 启动脚本已创建: {script_path}")
    else:
        # Linux/Mac shell脚本
        script_path = os.path.join('dist', 'start.sh')
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write('#!/bin/bash\n')
            f.write('cd label-printing-server\n')
            f.write('./label-printing-server\n')
        os.chmod(script_path, 0o755)
        print(f"\n[OK] 启动脚本已创建: {script_path}")


def create_zip_package():
    """将打包好的程序压缩成zip文件"""
    print("\n" + "=" * 70)
    print("创建ZIP压缩包")
    print("=" * 70)
    
    dist_dir = 'dist/label-printing-server'
    
    if not os.path.exists(dist_dir):
        print("[ERROR] 找不到打包目录，无法创建ZIP")
        return False
    
    # 生成带时间戳的zip文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    system_name = platform.system().lower()
    zip_filename = f'dist/label-printing-server_{system_name}_{timestamp}.zip'
    
    # 也创建一个不带时间戳的版本（覆盖旧版本）
    zip_filename_simple = f'dist/label-printing-server.zip'
    
    print(f"\n正在压缩 {dist_dir} ...")
    
    try:
        # 创建zip文件
        with zipfile.ZipFile(zip_filename_simple, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # 遍历目录
            for root, dirs, files in os.walk(dist_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    # 计算相对路径
                    arcname = os.path.relpath(file_path, 'dist')
                    zipf.write(file_path, arcname)
                    
        # 复制一份带时间戳的
        shutil.copy2(zip_filename_simple, zip_filename)
        
        # 获取文件大小
        zip_size = os.path.getsize(zip_filename_simple) / (1024 * 1024)
        
        print(f"  [OK] 已创建: {zip_filename_simple} ({zip_size:.2f} MB)")
        print(f"  [OK] 备份版本: {zip_filename}")
        
        return True
        
    except Exception as e:
        print(f"  [ERROR] 创建ZIP失败: {e}")
        return False


def main():
    """主函数"""
    try:
        print("\n标签打印服务 - 目录模式打包工具\n")
        
        # 检查 PyInstaller
        try:
            import PyInstaller
            print(f"PyInstaller 版本: {PyInstaller.__version__}")
        except ImportError:
            print("安装 PyInstaller...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyinstaller>=6.0.0'])
        
        # 构建
        if not build_executable():
            print("\n[ERROR] 打包失败")
            input("\n按回车键退出...")
            return 1
        
        # 创建ZIP压缩包
        zip_created = create_zip_package()
        
        system, machine = get_platform_info()
        
        print("\n" + "=" * 70)
        print("打包完成！")
        print("=" * 70)
        print(f"\n应用目录: dist/label-printing-server/")
        print(f"平台: {system} {machine}")
        
        if zip_created:
            print(f"\nZIP压缩包: dist/label-printing-server.zip")
        
        print("\n下一步:")
        print("  1. [重要] 验证依赖:")
        print("     cd dist/label-printing-server")
        if system == 'windows':
            print("     label-printing-server.exe")
        else:
            print("     ./label-printing-server")
        print("\n  2. 或使用启动脚本:")
        if system == 'windows':
            print("     dist\\start.bat")
        else:
            print("     dist/start.sh")
        print("\n  3. 如果成功启动，访问:")
        print("     http://127.0.0.1:5000")
        
        if zip_created:
            print("\n  4. 部署ZIP包:")
            print("     dist/label-printing-server.zip")
        
        print("\n目录模式的优势:")
        print("  - 更容易调试依赖问题")
        print("  - 可以查看包含了哪些文件")
        print("  - 启动速度更快")
        print("=" * 70)
        
        input("\n按回车键退出...")
        return 0
    
    except KeyboardInterrupt:
        print("\n\n[INFO] 用户取消")
        input("\n按回车键退出...")
        return 1
    except Exception as e:
        print("\n" + "=" * 70)
        print(f"[ERROR] 错误: {e}")
        print("=" * 70)
        import traceback
        traceback.print_exc()
        input("\n按回车键退出...")
        return 1


if __name__ == '__main__':
    sys.exit(main())

