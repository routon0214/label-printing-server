#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
跨平台打包脚本
自动检测平台并使用PyInstaller打包应用
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
    """清理构建目录"""
    dirs_to_clean = ['build', 'dist']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"清理目录: {dir_name}")
            shutil.rmtree(dir_name)


def install_dependencies():
    """安装打包依赖"""
    print("检查并安装依赖...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyinstaller>=6.0.0'])
        print("[OK] PyInstaller 已安装")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] 安装PyInstaller失败: {e}")
        return False
    return True


def build_executable():
    """构建可执行文件"""
    system, machine = get_platform_info()
    
    print("=" * 70)
    print(f"开始打包应用")
    print("=" * 70)
    print(f"平台: {system}")
    print(f"架构: {machine}")
    print(f"Python: {sys.version.split()[0]}")
    print("=" * 70)
    print()
    
    # 清理旧的构建文件
    clean_build_dirs()
    
    # 构建命令
    cmd = [
        'pyinstaller',
        '--clean',
        '--noconfirm',
        'app.spec'
    ]
    
    print("执行打包命令:")
    print(" ".join(cmd))
    print()
    
    try:
        subprocess.check_call(cmd)
        print("\n" + "=" * 70)
        print("[SUCCESS] 打包成功！")
        print("=" * 70)
        
        # 创建平台特定的输出目录
        dist_dir = f"dist/{system}-{machine}"
        if os.path.exists('dist/label-printing-server'):
            os.makedirs(dist_dir, exist_ok=True)
            
            # 移动文件到平台目录
            if system == 'windows':
                exe_name = 'label-printing-server.exe'
                if os.path.exists(f'dist/{exe_name}'):
                    shutil.move(f'dist/{exe_name}', f'{dist_dir}/{exe_name}')
            else:
                # Linux/Mac 目录结构
                if os.path.exists('dist/label-printing-server'):
                    if os.path.exists(dist_dir):
                        shutil.rmtree(dist_dir)
                    shutil.move('dist/label-printing-server', dist_dir)
            
            print(f"\n输出目录: {dist_dir}")
        
        print("\n打包内容:")
        if os.path.exists('dist'):
            for root, dirs, files in os.walk('dist'):
                level = root.replace('dist', '').count(os.sep)
                indent = ' ' * 2 * level
                print(f"{indent}{os.path.basename(root)}/")
                subindent = ' ' * 2 * (level + 1)
                for file in files[:10]:  # 只显示前10个文件
                    print(f"{subindent}{file}")
                if len(files) > 10:
                    print(f"{subindent}... 还有 {len(files) - 10} 个文件")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print("\n" + "=" * 70)
        print(f"[ERROR] 打包失败: {e}")
        print("=" * 70)
        return False


def create_readme():
    """创建发布说明"""
    system, machine = get_platform_info()
    dist_dir = f"dist/{system}-{machine}"
    
    readme_content = f"""# 斑马打印机MQTT标签打印服务

版本: 1.0.0
平台: {system} {machine}
构建日期: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 快速开始

### 1. 配置

首次运行会自动创建配置文件 `config/printer_config.json`

或手动创建配置文件：

```json
{{
  "mqtt": {{
    "host": "127.0.0.1",
    "port": 1883,
    "topic": "zebra/print"
  }},
  "printer": {{
    "name": "ZT411"
  }}
}}
```

### 2. 运行

"""
    
    if system == 'windows':
        readme_content += """Windows:
```
label-printing-server.exe
```
"""
    else:
        readme_content += """Linux/Mac:
```
chmod +x label-printing-server
./label-printing-server
```
"""
    
    readme_content += """
### 3. 测试

发送MQTT消息到主题 `zebra/print`：

```json
{
  "title": "产品标签",
  "fields": [
    {"label": "产品名称", "value": "测试产品", "font_size": 28}
  ]
}
```

## 注意事项

1. 确保MQTT服务器正在运行
2. 确保打印机已连接
3. Windows需要安装打印机驱动
4. Linux可能需要配置CUPS

## 目录结构

- config/ - 配置文件目录
- logs/ - 日志文件目录
- failed_labels/ - 失败的打印任务

## 故障排查

### 找不到打印机
程序会自动列出所有可用打印机，请在配置文件中使用正确的名称。

### MQTT连接失败
检查MQTT服务器地址和端口是否正确。

### 中文显示问题
确保系统已安装中文字体。

## 更多信息

访问项目主页：https://github.com/your-repo/label-printing-server
"""
    
    readme_file = os.path.join(dist_dir, 'README.txt')
    if os.path.exists(dist_dir):
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        print(f"\n[OK] 已创建 {readme_file}")


def copy_resources():
    """复制必要的资源文件到dist目录"""
    system, machine = get_platform_info()
    dist_dir = f"dist/{system}-{machine}"
    
    if not os.path.exists(dist_dir):
        return
    
    # 创建必要的目录
    os.makedirs(f"{dist_dir}/config", exist_ok=True)
    os.makedirs(f"{dist_dir}/logs", exist_ok=True)
    os.makedirs(f"{dist_dir}/failed_labels", exist_ok=True)
    
    # 复制配置示例文件
    if os.path.exists('config/printer_config_example.json'):
        shutil.copy('config/printer_config_example.json', f"{dist_dir}/config/")
        print(f"[OK] 已复制配置示例文件")
    
    print(f"[OK] 已创建必要的目录结构")


def wait_for_exit():
    """等待用户按键退出"""
    try:
        input("\n按回车键退出...")
    except:
        pass


def main():
    """主函数"""
    try:
        print("\n斑马打印机MQTT服务 - 打包工具\n")
        
        # 安装依赖
        if not install_dependencies():
            print("\n[ERROR] 依赖安装失败")
            wait_for_exit()
            return 1
        
        # 构建可执行文件
        if not build_executable():
            print("\n[ERROR] 打包失败，请检查上方错误信息")
            wait_for_exit()
            return 1
        
        # 复制资源文件
        copy_resources()
        
        # 创建README
        create_readme()
        
        system, machine = get_platform_info()
        print("\n" + "=" * 70)
        print("打包完成！")
        print("=" * 70)
        print(f"\n可执行文件位置: dist/{system}-{machine}/")
        print("\n提示:")
        print("  1. 测试可执行文件是否正常工作")
        print("  2. 配置 config/printer_config.json")
        print("  3. 运行程序并发送测试消息")
        print("\n" + "=" * 70)
        
        # 成功时也等待，让用户看到完成信息
        wait_for_exit()
        return 0
    
    except KeyboardInterrupt:
        print("\n\n[INFO] 用户取消打包")
        wait_for_exit()
        return 1
    except Exception as e:
        print("\n" + "=" * 70)
        print(f"[ERROR] 未预期的错误: {e}")
        print("=" * 70)
        import traceback
        traceback.print_exc()
        wait_for_exit()
        return 1


if __name__ == '__main__':
    sys.exit(main())

