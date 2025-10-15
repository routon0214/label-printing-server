# -*- mode: python ; coding: utf-8 -*-

"""
PyInstaller 配置文件
用于打包斑马打印机MQTT标签打印服务
"""

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# 收集所有数据文件
datas = [
    ('config/printer_config_example.json', 'config'),
]

# 收集所有子模块
hiddenimports = [
    'paho.mqtt.client',
    'PIL',
    'PIL.Image',
    'PIL.ImageDraw',
    'PIL.ImageFont',
]

# Windows特定导入
if sys.platform == 'win32':
    hiddenimports.extend([
        'win32print',
        'win32ui',
        'win32con',
        'pywintypes',
    ])

# Linux特定导入
if sys.platform == 'linux':
    hiddenimports.extend([
        'cups',
    ])

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='label-printing-server',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

# 对于Linux，创建可执行文件
if sys.platform == 'linux':
    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name='label-printing-server',
    )

