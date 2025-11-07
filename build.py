#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
打包脚本 - 目录模式
1. 检查并修复 Python 环境
2. 检查并安装依赖（从 requirements.txt）
3. 创建自定义 PyInstaller hook
4. 使用目录模式打包
5. 验证打包结果
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


def print_section(title):
    """打印分节标题"""
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)


def get_venv_python():
    """获取虚拟环境 .venv 的 Python 路径（如果存在）"""
    venv_path = os.path.join(os.getcwd(), '.venv')
    
    if os.path.exists(venv_path):
        # 根据平台确定 Python 可执行文件路径
        if sys.platform == 'win32':
            venv_python = os.path.join(venv_path, 'Scripts', 'python.exe')
        else:
            venv_python = os.path.join(venv_path, 'bin', 'python')
        
        if os.path.exists(venv_python):
            return venv_python
    
    return None


def parse_requirements():
    """从 requirements.txt 解析依赖"""
    requirements_file = 'requirements.txt'
    
    if not os.path.exists(requirements_file):
        print(f"[WARNING] 未找到 {requirements_file}，使用默认依赖列表")
        return []
    
    deps = []
    system = platform.system().lower()
    
    with open(requirements_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # 跳过注释和空行
            if not line or line.startswith('#'):
                continue
            
            # 处理平台特定依赖
            if ';' in line:
                parts = line.split(';')
                dep_line = parts[0].strip()
                condition = parts[1].strip() if len(parts) > 1 else ''
                
                # 检查条件是否匹配当前平台
                if 'sys_platform' in condition:
                    if 'win32' in condition and system == 'windows':
                        deps.append(dep_line)
                    elif 'linux' in condition and system == 'linux':
                        deps.append(dep_line)
                else:
                    # 无条件限制，添加
                    deps.append(dep_line)
            else:
                # 普通依赖
                deps.append(line)
    
    # 提取包名（去除版本号）
    package_names = []
    for dep in deps:
        # 处理格式如: package>=1.0.0, package[extra]>=1.0.0
        dep = dep.split('>=')[0].split('==')[0].split('<')[0].split('>')[0].strip()
        # 处理 extras: package[extra] -> package
        if '[' in dep:
            dep = dep.split('[')[0]
        package_names.append(dep)
    
    return package_names


def check_python_environment():
    """检查 Python 环境"""
    print_section("步骤 1/5: 检查 Python 环境")
    
    print(f"Python 版本: {sys.version}")
    print(f"Python 路径: {sys.executable}")
    print(f"平台: {platform.platform()}")
    
    # 检查是否在虚拟环境中
    in_venv = hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )
    
    # 检测 .venv 目录
    venv_path = os.path.join(os.getcwd(), '.venv')
    venv_exists = os.path.exists(venv_path)
    
    if in_venv:
        print(f"✓ 当前在虚拟环境中: {sys.prefix}")
    else:
        if venv_exists:
            print(f"⚠ 检测到 .venv 目录，但当前未激活虚拟环境")
            print(f"  建议先激活虚拟环境:")
            if sys.platform == 'win32':
                print(f"    .venv\\Scripts\\activate")
            else:
                print(f"    source .venv/bin/activate")
            print(f"  或者直接运行此脚本，脚本会使用当前 Python 环境")
        else:
            print("当前不在虚拟环境中（使用系统 Python）")
    
    return True


def fix_dependencies():
    """修复依赖 - 从 requirements.txt 读取"""
    print_section("步骤 2/5: 修复依赖")
    
    # 从 requirements.txt 读取依赖
    deps = parse_requirements()
    
    if not deps:
        print("[WARNING] 无法从 requirements.txt 读取依赖，使用默认列表")
        deps = [
            'jinja2',
            'markupsafe',
            'fastapi',
            'starlette',
            'uvicorn',
            'paho-mqtt',
            'pillow',
            'python-multipart',
            'pyinstaller',
        ]
        # 根据平台添加特定依赖
        if sys.platform == 'win32':
            deps.append('pywin32')
        elif sys.platform == 'linux':
            deps.append('pycups')
    
    print(f"从 requirements.txt 读取到 {len(deps)} 个依赖包")
    print("检查依赖...")
    
    missing = []
    installed = []
    
    for dep in deps:
        # 转换为导入名（paho-mqtt -> paho.mqtt, python-multipart -> 不需要导入检查）
        import_name = dep.replace('-', '_').lower()
        
        # 跳过不需要导入检查的包
        skip_check = ['pyinstaller', 'python-multipart']
        if any(skip in dep.lower() for skip in skip_check):
            installed.append(dep)
            print(f"  [OK] {dep} (跳过导入检查)")
            continue
        
        try:
            # 特殊处理一些包的导入名
            if dep == 'paho-mqtt':
                __import__('paho.mqtt')
            elif dep == 'pywin32':
                __import__('win32print')
            elif dep == 'pycups':
                __import__('cups')
            else:
                __import__(import_name)
            print(f"  [OK] {dep}")
            installed.append(dep)
        except ImportError:
            print(f"  [ERROR] {dep} - 缺失")
            missing.append(dep)
    
    if missing:
        print(f"\n发现 {len(missing)} 个缺失的依赖，正在从 requirements.txt 安装...")
        try:
            # 确定使用的 Python 可执行文件
            python_exe = sys.executable
            venv_python = get_venv_python()
            if venv_python:
                # 检查是否在虚拟环境中
                in_venv = hasattr(sys, 'real_prefix') or (
                    hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
                )
                if not in_venv:
                    python_exe = venv_python
            
            # 直接从 requirements.txt 安装所有依赖
            subprocess.check_call([
                python_exe, '-m', 'pip', 'install', 
                '-r', 'requirements.txt',
                '--upgrade'
            ])
            print("  [OK] 所有依赖安装成功")
        except subprocess.CalledProcessError as e:
            print(f"  [ERROR] 依赖安装失败: {e}")
            return False
    else:
        print(f"\n所有依赖已安装 ({len(installed)} 个)")
    
    return True


def create_pyinstaller_hook():
    """创建自定义 PyInstaller hook"""
    print_section("步骤 3/5: 创建自定义 Hook")
    
    hook_dir = 'build_hooks'
    os.makedirs(hook_dir, exist_ok=True)
    
    # Hook for Jinja2
    hook_jinja2 = os.path.join(hook_dir, 'hook-jinja2.py')
    with open(hook_jinja2, 'w', encoding='utf-8') as f:
        f.write("""# PyInstaller hook for Jinja2
from PyInstaller.utils.hooks import collect_all, collect_submodules

# 收集所有 Jinja2 内容
datas, binaries, hiddenimports = collect_all('jinja2')

# 确保所有子模块都被包含
hiddenimports += collect_submodules('jinja2')
hiddenimports += collect_submodules('markupsafe')

# 显式添加关键模块
hiddenimports += [
    'jinja2',
    'jinja2.ext',
    'jinja2.loaders',
    'jinja2.runtime',
    'jinja2.compiler',
    'jinja2.filters',
    'jinja2.tests',
    'jinja2.nodes',
    'jinja2.parser',
    'jinja2.lexer',
    'jinja2.environment',
    'jinja2.utils',
    'jinja2.debug',
    'jinja2.exceptions',
    'jinja2.bccache',
    'jinja2.optimizer',
    'jinja2.visitor',
    'markupsafe',
    'markupsafe._native',
]
""")
    
    print(f"  [OK] 创建 {hook_jinja2}")
    
    # Hook for Starlette
    hook_starlette = os.path.join(hook_dir, 'hook-starlette.py')
    with open(hook_starlette, 'w', encoding='utf-8') as f:
        f.write("""# PyInstaller hook for Starlette
from PyInstaller.utils.hooks import collect_all, collect_submodules

datas, binaries, hiddenimports = collect_all('starlette')
hiddenimports += collect_submodules('starlette')
""")
    
    print(f"  [OK] 创建 {hook_starlette}")
    
    return hook_dir


def build_with_ultimate_config(hook_dir):
    """使用目录模式打包"""
    print_section("步骤 4/5: 开始打包（目录模式）")
    
    system = platform.system()
    path_sep = ';' if system == 'Windows' else ':'
    
    # 确定使用的 Python 可执行文件
    # 优先使用虚拟环境的 Python（如果存在且未激活）
    python_exe = sys.executable
    venv_python = get_venv_python()
    if venv_python and venv_python != sys.executable:
        # 检查是否在虚拟环境中
        in_venv = hasattr(sys, 'real_prefix') or (
            hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
        )
        if not in_venv:
            print(f"使用虚拟环境 Python: {venv_python}")
            python_exe = venv_python
    
    # 清理
    for dir_name in ['build', 'dist']:
        if os.path.exists(dir_name):
            print(f"清理 {dir_name}/")
            shutil.rmtree(dir_name)
    
    for spec_file in ['label-printing-server.spec', 'app.spec']:
        if os.path.exists(spec_file):
            os.remove(spec_file)
    
    # 打包配置 - 目录模式
    cmd = [
        python_exe, '-m', 'PyInstaller',
        '--clean',
        '--noconfirm',
        '--onedir',  # 目录模式
        '--console',
        '--name=label-printing-server',
        '--distpath=dist',
        '--workpath=build',
        # 使用自定义 hooks
        f'--additional-hooks-dir={hook_dir}',
        # 收集所有包（最激进的方式）
        '--collect-all=jinja2',
        '--collect-all=markupsafe',
        '--collect-all=fastapi',
        '--collect-all=starlette',
        '--collect-all=uvicorn',
        '--collect-all=paho',
        '--collect-all=PIL',
        '--collect-all=pydantic',
        '--collect-all=anyio',
        # 复制元数据
        '--copy-metadata=fastapi',
        '--copy-metadata=starlette',
        '--copy-metadata=uvicorn',
        '--copy-metadata=pydantic',
        # 隐藏导入（完整列表）
        '--hidden-import=jinja2',
        '--hidden-import=jinja2._compat',
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
        '--hidden-import=jinja2.bccache',
        '--hidden-import=jinja2.optimizer',
        '--hidden-import=jinja2.visitor',
        '--hidden-import=markupsafe',
        '--hidden-import=markupsafe._speedups',
        '--hidden-import=markupsafe._native',
        '--hidden-import=fastapi',
        '--hidden-import=fastapi.routing',
        '--hidden-import=fastapi.encoders',
        '--hidden-import=fastapi.exceptions',
        '--hidden-import=fastapi.dependencies',
        '--hidden-import=starlette',
        '--hidden-import=starlette.applications',
        '--hidden-import=starlette.routing',
        '--hidden-import=starlette.responses',
        '--hidden-import=starlette.requests',
        '--hidden-import=starlette.staticfiles',
        '--hidden-import=starlette.templating',
        '--hidden-import=starlette.middleware',
        '--hidden-import=starlette.middleware.cors',
        '--hidden-import=starlette.middleware.gzip',
        '--hidden-import=uvicorn',
        '--hidden-import=uvicorn.protocols',
        '--hidden-import=uvicorn.protocols.http',
        '--hidden-import=uvicorn.protocols.http.auto',
        '--hidden-import=uvicorn.protocols.websockets',
        '--hidden-import=uvicorn.protocols.websockets.auto',
        '--hidden-import=uvicorn.lifespan',
        '--hidden-import=uvicorn.lifespan.on',
        '--hidden-import=uvicorn.loops',
        '--hidden-import=uvicorn.loops.auto',
        '--hidden-import=paho.mqtt.client',
        '--hidden-import=PIL',
        '--hidden-import=PIL.Image',
        '--hidden-import=pydantic',
        '--hidden-import=pydantic.fields',
        '--hidden-import=anyio',
        '--hidden-import=h11',
        '--hidden-import=httptools',
        '--hidden-import=websockets',
        '--hidden-import=email.mime',
        # 路径
        '--paths=.',
        '--paths=src',
    ]
    
    # 添加数据文件
    if os.path.exists('templates'):
        cmd.append(f'--add-data=templates{path_sep}templates')
    if os.path.exists('static'):
        cmd.append(f'--add-data=static{path_sep}static')
    if os.path.exists('data/test_samples'):
        cmd.append(f'--add-data=data/test_samples{path_sep}data/test_samples')
    
    # Windows 特定
    if system == 'Windows':
        cmd.extend([
            '--hidden-import=win32print',
            '--hidden-import=win32ui',
            '--hidden-import=win32con',
        ])
    
    cmd.append('app.py')
    
    print("\n执行打包...")
    print(f"命令: {' '.join(cmd[:10])}...")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
        print("[OK] 打包成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] 打包失败")
        print(f"\n错误输出:\n{e.stderr}")
        return False


def verify_build():
    """验证打包结果"""
    print_section("步骤 5/5: 验证打包结果")
    
    dist_dir = 'dist/label-printing-server'
    
    if not os.path.exists(dist_dir):
        print("[ERROR] 找不到打包目录")
        return False
    
    # 检查关键文件
    print("\n检查关键文件:")
    
    exe_name = 'label-printing-server.exe' if platform.system() == 'Windows' else 'label-printing-server'
    exe_path = os.path.join(dist_dir, exe_name)
    
    if os.path.exists(exe_path):
        print(f"  [OK] {exe_name}")
    else:
        print(f"  [ERROR] {exe_name} 缺失")
        return False
    
    # 检查 _internal 目录
    internal_dir = os.path.join(dist_dir, '_internal')
    if os.path.exists(internal_dir):
        print(f"  [OK] _internal/ 目录")
        
        # 检查 Jinja2
        jinja2_files = []
        for root, dirs, files in os.walk(internal_dir):
            for file in files:
                if 'jinja2' in file.lower() or 'jinja2' in root.lower():
                    jinja2_files.append(os.path.join(root, file))
        
        if jinja2_files:
            print(f"  [OK] 找到 {len(jinja2_files)} 个 Jinja2 相关文件")
        else:
            print(f"  [ERROR] 未找到 Jinja2 文件")
    
    # 检查 templates
    templates_dir = os.path.join(dist_dir, 'templates')
    if os.path.exists(templates_dir):
        print(f"  [OK] templates/ 目录")
    
    # 检查 test_samples
    test_samples_dir = os.path.join(dist_dir, 'data', 'test_samples')
    if os.path.exists(test_samples_dir):
        print(f"  [OK] data/test_samples/ 目录")
        # 检查关键文件
        examples_file = os.path.join(test_samples_dir, 'examples.json')
        if os.path.exists(examples_file):
            print(f"  [OK] examples.json")
        else:
            print(f"  [WARNING] examples.json 缺失")
    else:
        print(f"  [ERROR] data/test_samples/ 目录缺失")
    
    print("\n" + "=" * 70)
    print("验证完成")
    print("=" * 70)
    
    return True


def create_test_script():
    """创建测试脚本"""
    print("\n创建测试脚本...")
    
    test_script = 'dist/test_jinja2.py'
    with open(test_script, 'w', encoding='utf-8') as f:
        f.write("""#!/usr/bin/env python3
# 测试 Jinja2 是否可用
import sys
sys.path.insert(0, 'label-printing-server/_internal')

print("测试 Jinja2...")
try:
    import jinja2
    print(f"[OK] Jinja2 版本: {jinja2.__version__}")
    print(f"[OK] Jinja2 路径: {jinja2.__file__}")
    
    from jinja2 import Template
    t = Template("Hello {{ name }}!")
    result = t.render(name="World")
    print(f"[OK] 模板测试: {result}")
    
    print("\\n[OK] Jinja2 完全正常！")
except Exception as e:
    print(f"[ERROR] Jinja2 测试失败: {e}")
    import traceback
    traceback.print_exc()
""")
    
    print(f"  [OK] 创建 {test_script}")


def create_zip_package():
    """将打包好的程序压缩成zip文件"""
    print_section("创建ZIP压缩包")
    
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
    print("\n" + "=" * 70)
    print(" " * 20 + "打包脚本 - 目录模式")
    print("=" * 70)
    print("\n这个脚本将:")
    print("  1. 检查 Python 环境")
    print("  2. 检查并安装依赖（从 requirements.txt）")
    print("  3. 创建自定义 Hook")
    print("  4. 使用目录模式打包")
    print("  5. 验证打包结果")
    print()
    
    try:
        # 步骤 1: 检查环境
        if not check_python_environment():
            return 1
        
        # 步骤 2: 检查并安装依赖
        if not fix_dependencies():
            print("\n[ERROR] 依赖安装失败")
            return 1
        
        # 步骤 3: 创建 Hook
        hook_dir = create_pyinstaller_hook()
        
        # 步骤 4: 打包
        if not build_with_ultimate_config(hook_dir):
            print("\n[ERROR] 打包失败")
            return 1
        
        # 步骤 5: 验证
        if not verify_build():
            print("\n[WARNING] 验证发现问题")
        
        # 创建测试脚本
        create_test_script()
        
        # 创建ZIP压缩包
        zip_created = create_zip_package()
        
        print("\n" + "=" * 70)
        print("完成！")
        print("=" * 70)
        print("\n下一步:")
        print("  1. 运行程序:")
        if platform.system() == 'Windows':
            print("     cd dist\\label-printing-server")
            print("     label-printing-server.exe")
        else:
            print("     cd dist/label-printing-server")
            print("     ./label-printing-server")
        print("\n  2. 如果仍然失败，运行测试脚本:")
        print("     cd dist")
        print("     python test_jinja2.py")
        print("\n  3. 访问 Web 界面:")
        print("     http://127.0.0.1:5000")
        
        if zip_created:
            print("\n  4. 部署ZIP包:")
            print("     dist/label-printing-server.zip")
        
        print("=" * 70)
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n用户取消")
        return 1
    except Exception as e:
        print(f"\n[ERROR] 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())

