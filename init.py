#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Label Printing Server - 项目初始化脚本

功能：
- 检查 Python 版本
- 创建虚拟环境
- 安装项目依赖（使用阿里云镜像）
- 创建必要的目录结构
- 生成默认配置文件
- 验证系统环境

作者：Label Printing Server
日期：2025-11-06
"""

import sys
import os
import subprocess
import platform
import shutil
import json
from pathlib import Path


class ProjectInitializer:
    """项目初始化器"""
    
    # 颜色代码（用于终端输出）
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    def __init__(self):
        self.project_root = Path(__file__).parent.absolute()
        self.venv_path = self.project_root / 'venv'
        self.is_windows = platform.system() == 'Windows'
        self.python_cmd = 'python' if self.is_windows else 'python3'
        self.pip_cmd = 'pip' if self.is_windows else 'pip3'
        
    def colorize(self, text, color):
        """给文本添加颜色"""
        if self.is_windows:
            # Windows 下可能不支持颜色，返回纯文本
            return text
        return f"{color}{text}{self.RESET}"
    
    def print_banner(self):
        """打印初始化横幅"""
        print()
        print("=" * 70)
        print(self.colorize(" " * 15 + "Label Printing Server - 项目初始化", self.BOLD + self.BLUE))
        print("=" * 70)
        print(f"系统: {platform.system()} {platform.machine()}")
        print(f"Python: {sys.version.split()[0]}")
        print(f"项目路径: {self.project_root}")
        print("=" * 70)
        print()
    
    def print_step(self, step_num, total_steps, message):
        """打印步骤信息"""
        print(self.colorize(f"\n[{step_num}/{total_steps}] {message}", self.BOLD))
        print("-" * 70)
    
    def print_success(self, message):
        """打印成功信息"""
        print(self.colorize(f"[OK] {message}", self.GREEN))
    
    def print_warning(self, message):
        """打印警告信息"""
        print(self.colorize(f"[WARNING] {message}", self.YELLOW))
    
    def print_error(self, message):
        """打印错误信息"""
        print(self.colorize(f"[ERROR] {message}", self.RED))
    
    def check_python_version(self):
        """检查 Python 版本"""
        self.print_step(1, 7, "检查 Python 版本")
        
        min_version = (3, 7)
        current_version = sys.version_info[:2]
        
        print(f"当前 Python 版本: {sys.version.split()[0]}")
        print(f"最低要求版本: {min_version[0]}.{min_version[1]}")
        
        if current_version < min_version:
            self.print_error(f"Python 版本过低，需要 {min_version[0]}.{min_version[1]} 或更高版本")
            return False
        
        self.print_success(f"Python 版本检查通过")
        return True
    
    def check_venv_module(self):
        """检查 venv 模块是否可用"""
        try:
            import venv
            return True
        except ImportError:
            self.print_warning("venv 模块不可用")
            if not self.is_windows:
                print("请安装: sudo apt install python3-venv  (Ubuntu/Debian)")
            return False
    
    def create_virtual_environment(self):
        """创建虚拟环境"""
        self.print_step(2, 7, "创建虚拟环境")
        
        if self.venv_path.exists():
            self.print_warning(f"虚拟环境已存在: {self.venv_path}")
            response = input("是否删除并重新创建？(y/N): ").strip().lower()
            if response == 'y':
                self.print_warning("正在删除旧的虚拟环境...")
                shutil.rmtree(self.venv_path)
            else:
                self.print_success("保留现有虚拟环境")
                return True
        
        if not self.check_venv_module():
            return False
        
        print(f"正在创建虚拟环境: {self.venv_path}")
        try:
            cmd = [sys.executable, '-m', 'venv', str(self.venv_path)]
            subprocess.run(cmd, check=True)
            self.print_success("虚拟环境创建成功")
            return True
        except subprocess.CalledProcessError as e:
            self.print_error(f"虚拟环境创建失败: {e}")
            return False
    
    def get_venv_python(self):
        """获取虚拟环境中的 Python 路径"""
        if self.is_windows:
            return self.venv_path / 'Scripts' / 'python.exe'
        else:
            return self.venv_path / 'bin' / 'python'
    
    def get_venv_pip(self):
        """获取虚拟环境中的 pip 路径"""
        if self.is_windows:
            return self.venv_path / 'Scripts' / 'pip.exe'
        else:
            return self.venv_path / 'bin' / 'pip'
    
    def upgrade_pip(self):
        """升级 pip 到最新版本"""
        self.print_step(3, 7, "升级 pip")
        
        pip_path = self.get_venv_pip()
        if not pip_path.exists():
            self.print_error("找不到虚拟环境中的 pip")
            return False
        
        print("正在升级 pip（使用阿里云镜像）...")
        try:
            cmd = [
                str(self.get_venv_python()),
                '-m',
                'pip',
                'install',
                '--upgrade',
                'pip',
                '-i', 'https://mirrors.aliyun.com/pypi/simple/'
            ]
            subprocess.run(cmd, check=True)
            self.print_success("pip 升级成功")
            return True
        except subprocess.CalledProcessError as e:
            self.print_warning(f"pip 升级失败: {e}")
            return True  # 非致命错误，继续执行
    
    def install_dependencies(self):
        """安装项目依赖"""
        self.print_step(4, 7, "安装项目依赖")
        
        requirements_file = self.project_root / 'requirements.txt'
        if not requirements_file.exists():
            self.print_error(f"找不到 requirements.txt: {requirements_file}")
            return False
        
        pip_path = self.get_venv_pip()
        if not pip_path.exists():
            self.print_error("找不到虚拟环境中的 pip")
            return False
        
        print("正在安装依赖（使用阿里云镜像）...")
        print("这可能需要几分钟，请耐心等待...")
        print()
        
        try:
            cmd = [
                str(pip_path),
                'install',
                '-r', str(requirements_file),
                '-i', 'https://mirrors.aliyun.com/pypi/simple/',
                '--trusted-host', 'mirrors.aliyun.com'
            ]
            subprocess.run(cmd, check=True)
            self.print_success("依赖安装完成")
            return True
        except subprocess.CalledProcessError as e:
            self.print_error(f"依赖安装失败: {e}")
            return False
    
    def create_directory_structure(self):
        """创建必要的目录结构"""
        self.print_step(5, 7, "创建目录结构")
        
        directories = [
            'data',
            'data/logs',
            'data/uploads',
            'data/failed_labels',
            'config',
            'static',
            'templates',
        ]
        
        for dir_path in directories:
            full_path = self.project_root / dir_path
            if not full_path.exists():
                full_path.mkdir(parents=True, exist_ok=True)
                print(f"  创建目录: {dir_path}")
            else:
                print(f"  目录已存在: {dir_path}")
        
        self.print_success("目录结构创建完成")
        return True
    
    def create_config_files(self):
        """创建配置文件"""
        self.print_step(6, 7, "创建配置文件")
        
        config_file = self.project_root / 'config' / 'printer_config.json'
        example_file = self.project_root / 'config' / 'printer_config_example.json'
        
        if config_file.exists():
            self.print_warning(f"配置文件已存在: {config_file}")
            return True
        
        if example_file.exists():
            print(f"从示例文件创建配置: {example_file.name}")
            shutil.copy(example_file, config_file)
            self.print_success(f"配置文件创建成功: {config_file.name}")
        else:
            # 创建默认配置
            print("示例文件不存在，创建默认配置...")
            default_config = {
                "mqtt": {
                    "url": "mqtt://127.0.0.1:1883",
                    "topic": "zebra/print",
                    "username": None,
                    "password": None,
                    "client_id": None
                },
                "web": {
                    "username": "admin",
                    "password": "admin"
                },
                "printers": [
                    {
                        "name": "ZT411",
                        "types": ["label"],
                        "ip": None,
                        "port": 9100,
                        "device": None,
                        "default": True,
                        "_comment": "斑马标签打印机 - 请根据实际情况修改"
                    }
                ]
            }
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            
            self.print_success(f"默认配置文件创建成功: {config_file.name}")
        
        self.print_warning("[WARNING] 请根据实际情况修改配置文件:")
        print(f"  - MQTT 连接信息")
        print(f"  - Web 界面登录密码")
        print(f"  - 打印机配置")
        print(f"  配置文件位置: {config_file}")
        
        return True
    
    def verify_installation(self):
        """验证安装"""
        self.print_step(7, 7, "验证安装")
        
        python_path = self.get_venv_python()
        if not python_path.exists():
            self.print_error("找不到虚拟环境中的 Python")
            return False
        
        # 检查关键依赖
        required_packages = [
            'paho.mqtt.client',
            'PIL',
            'fastapi',
            'uvicorn',
            'jinja2'
        ]
        
        all_ok = True
        for package in required_packages:
            try:
                cmd = [str(python_path), '-c', f'import {package}']
                subprocess.run(cmd, check=True, capture_output=True)
                print(f"  [OK] {package}")
            except subprocess.CalledProcessError:
                print(f"  [ERROR] {package} - 导入失败")
                all_ok = False
        
        if all_ok:
            self.print_success("所有依赖验证通过")
        else:
            self.print_warning("部分依赖验证失败，可能需要重新安装")
        
        return all_ok
    
    def print_next_steps(self):
        """打印后续步骤"""
        print()
        print("=" * 70)
        print(self.colorize("🎉 初始化完成！", self.BOLD + self.GREEN))
        print("=" * 70)
        print()
        print(self.colorize("后续步骤:", self.BOLD))
        print()
        print("1. 配置打印机:")
        print(f"   编辑文件: {self.project_root / 'config' / 'printer_config.json'}")
        print()
        print("2. 启动服务:")
        if self.is_windows:
            print("   双击运行: start.bat")
            print("   或命令行: .\\start.bat")
        else:
            print("   运行命令: ./start.sh")
            print("   (首次需要: chmod +x start.sh)")
        print()
        print("3. 访问 Web 界面:")
        print("   http://localhost:5000")
        print("   默认账号: admin / admin")
        print()
        print("4. 查看文档:")
        print("   - README.md - 项目说明")
        print("   - docs/完整部署指南.md - 部署指南")
        print("   - docs/WEB服务使用说明.md - 使用说明")
        print("   - 启动脚本使用说明.md - 启动脚本说明")
        print()
        print("=" * 70)
        print()
    
    def run(self):
        """运行初始化流程"""
        self.print_banner()
        
        steps = [
            self.check_python_version,
            self.create_virtual_environment,
            self.upgrade_pip,
            self.install_dependencies,
            self.create_directory_structure,
            self.create_config_files,
            self.verify_installation,
        ]
        
        for step in steps:
            if not step():
                self.print_error("\n初始化失败，请查看错误信息并解决后重试")
                return False
        
        self.print_next_steps()
        return True


def main():
    """主函数"""
    # Windows 控制台编码修复
    if sys.platform == 'win32':
        import io
        try:
            # 设置控制台代码页为 UTF-8
            os.system('chcp 65001 >nul 2>&1')
            if sys.stdout.encoding != 'utf-8':
                sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
            if sys.stderr.encoding != 'utf-8':
                sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
        except:
            pass
    
    initializer = ProjectInitializer()
    
    try:
        success = initializer.run()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n初始化已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

