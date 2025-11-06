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
    
    # 切换到项目根目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    os.chdir(project_root)
    
    print("=" * 70)
    print(f"开始打包应用")
    print("=" * 70)
    print(f"平台: {system}")
    print(f"架构: {machine}")
    print(f"Python: {sys.version.split()[0]}")
    print(f"项目根目录: {project_root}")
    print("=" * 70)
    print()
    
    # 清理旧的构建文件
    clean_build_dirs()
    
    # 根据平台设置路径分隔符
    path_sep = ';' if system == 'windows' else ':'
    
    # 构建命令 - 单文件模式
    cmd = [
        'pyinstaller',
        '--clean',
        '--noconfirm',
        '--onefile',  # 打包成单个文件
        '--console',  # 显示控制台
        '--name=label-printing-server',
        '--distpath=dist',  # 指定输出目录为dist
        '--workpath=build',  # 指定工作目录为build
        # 使用collect-all收集整个包及其所有依赖
        '--collect-all=paho',
        '--collect-all=PIL',
        '--collect-all=fastapi',
        '--collect-all=starlette',
        '--collect-all=uvicorn',
        '--collect-all=jinja2',
        '--collect-all=markupsafe',  # Jinja2 的关键依赖
        '--copy-metadata=paho-mqtt',
        '--copy-metadata=fastapi',
        '--copy-metadata=starlette',
        '--copy-metadata=uvicorn',
        # Jinja2 的包名是 "Jinja2"（大写），但为了兼容性，我们移除 copy-metadata
        # '--copy-metadata=Jinja2',  # 移除，因为可能导致问题
        # MQTT相关
        '--hidden-import=paho.mqtt.client',
        '--hidden-import=paho.mqtt.publish',
        '--hidden-import=paho.mqtt.subscribe',
        # 图像处理
        '--hidden-import=PIL.Image',
        '--hidden-import=PIL.ImageDraw',
        '--hidden-import=PIL.ImageFont',
        # FastAPI和Starlette
        '--hidden-import=fastapi',
        '--hidden-import=fastapi.responses',
        '--hidden-import=fastapi.staticfiles',
        '--hidden-import=fastapi.templating',
        '--hidden-import=fastapi.security',
        '--hidden-import=starlette',
        '--hidden-import=starlette.applications',
        '--hidden-import=starlette.routing',
        '--hidden-import=starlette.responses',
        '--hidden-import=starlette.staticfiles',
        '--hidden-import=starlette.templating',
        '--hidden-import=starlette.middleware',
        '--hidden-import=starlette.middleware.cors',
        # Uvicorn
        '--hidden-import=uvicorn',
        '--hidden-import=uvicorn.logging',
        '--hidden-import=uvicorn.loops',
        '--hidden-import=uvicorn.loops.auto',
        '--hidden-import=uvicorn.protocols',
        '--hidden-import=uvicorn.protocols.http',
        '--hidden-import=uvicorn.protocols.http.auto',
        '--hidden-import=uvicorn.protocols.websockets',
        '--hidden-import=uvicorn.protocols.websockets.auto',
        '--hidden-import=uvicorn.lifespan',
        '--hidden-import=uvicorn.lifespan.on',
        # Jinja2模板引擎（完整支持）
        '--hidden-import=jinja2',
        '--hidden-import=jinja2.ext',
        '--hidden-import=jinja2.loaders',
        '--hidden-import=jinja2.runtime',
        '--hidden-import=jinja2.compiler',
        '--hidden-import=jinja2.filters',
        '--hidden-import=jinja2.tests',
        '--hidden-import=jinja2.nodes',
        '--hidden-import=jinja2.parser',
        '--hidden-import=jinja2.lexer',
        '--hidden-import=jinja2.environment',
        '--hidden-import=jinja2.utils',
        '--hidden-import=jinja2.debug',
        '--hidden-import=jinja2.exceptions',
        # MarkupSafe (Jinja2 依赖)
        '--hidden-import=markupsafe',
        '--hidden-import=markupsafe._speedups',
        # Pydantic
        '--hidden-import=pydantic',
        '--hidden-import=pydantic.fields',
        '--hidden-import=pydantic.main',
        # 其他依赖
        '--hidden-import=email.mime',
        '--hidden-import=email.mime.multipart',
        '--hidden-import=email.mime.text',
        '--hidden-import=anyio',
        '--hidden-import=h11',
        '--hidden-import=httptools',
        '--hidden-import=websockets',
        # 项目模块路径
        '--paths=.',
        '--paths=src',
    ]
    
    # 添加数据文件（使用正确的路径分隔符）
    print("\n检查数据文件...")
    if os.path.exists('templates'):
        cmd.append(f'--add-data=templates{path_sep}templates')
        print("  ✓ 将包含 templates 目录")
    else:
        print("  ⚠ templates 目录不存在，跳过")
    
    if os.path.exists('static'):
        cmd.append(f'--add-data=static{path_sep}static')
        print("  ✓ 将包含 static 目录")
    else:
        print("  ⓘ static 目录不存在，跳过（可选）")
    
    # 添加入口文件
    cmd.append('app.py')
    
    # Windows特定的隐藏导入
    if system == 'Windows':
        cmd.extend([
            '--hidden-import=win32print',
            '--hidden-import=win32ui',
            '--hidden-import=win32con',
            '--hidden-import=pywintypes',
        ])
    
    print("执行打包命令:")
    print(" ".join(cmd))
    print()
    
    try:
        subprocess.check_call(cmd)
        print("\n" + "=" * 70)
        print("[SUCCESS] 打包成功！")
        print("=" * 70)
        
        # 检查输出文件
        exe_name = 'label-printing-server.exe' if system == 'Windows' else 'label-printing-server'
        exe_path = f'dist/{exe_name}'
        
        if os.path.exists(exe_path):
            print(f"\n✓ 可执行文件已生成: {exe_path}")
            file_size = os.path.getsize(exe_path) / (1024 * 1024)  # MB
            print(f"  文件大小: {file_size:.2f} MB")
        else:
            print(f"\n⚠ 警告: 未找到预期的输出文件 {exe_path}")
        
        print(f"\n输出目录: dist/")
        
        print("\n打包内容:")
        if os.path.exists('dist'):
            for item in os.listdir('dist'):
                item_path = os.path.join('dist', item)
                if os.path.isfile(item_path):
                    size = os.path.getsize(item_path) / (1024 * 1024)
                    print(f"  {item} ({size:.2f} MB)")
                elif os.path.isdir(item_path):
                    print(f"  {item}/")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print("\n" + "=" * 70)
        print(f"[ERROR] 打包失败: {e}")
        print("=" * 70)
        return False


def create_readme():
    """创建发布说明"""
    system, machine = get_platform_info()
    dist_dir = "dist"
    
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
    dist_dir = "dist"
    
    if not os.path.exists(dist_dir):
        return
    
    # 创建必要的目录
    os.makedirs(f"{dist_dir}/config", exist_ok=True)
    os.makedirs(f"{dist_dir}/data/logs", exist_ok=True)
    os.makedirs(f"{dist_dir}/data/failed_labels", exist_ok=True)
    
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
        exe_name = 'label-printing-server.exe' if system == 'Windows' else 'label-printing-server'
        print("\n" + "=" * 70)
        print("打包完成！")
        print("=" * 70)
        print(f"\n可执行文件位置: dist/{exe_name}")
        print(f"平台: {system} {machine}")
        print("\n下一步:")
        print("  1. [推荐] 验证依赖是否完整:")
        print("     python scripts/verify_dependencies.py")
        print("  2. 测试可执行文件:")
        print(f"     cd dist && {exe_name}")
        print("  3. 配置打印机:")
        print("     编辑 dist/config/printer_config.json")
        print("  4. 访问Web界面:")
        print("     http://127.0.0.1:5000")
        print("\n如果遇到 'jinja2 must be installed' 错误:")
        print("  检查上面的打包日志，确保所有模块都被正确包含")
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

