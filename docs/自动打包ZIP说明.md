# 自动打包ZIP功能说明

## 功能概述

现在所有的构建脚本在编译完成后都会自动创建ZIP压缩包，方便部署和分发。

## 更新的脚本

### 1. `scripts/fix_and_build.py`
- 终极打包解决方案脚本
- 编译完成后自动创建ZIP包
- 生成两个版本：
  - `dist/label-printing-server.zip` - 标准版本（覆盖旧版本）
  - `dist/label-printing-server_{platform}_{timestamp}.zip` - 带时间戳的备份版本

### 2. `scripts/build_dir_mode.py`
- 目录模式打包脚本
- 编译完成后自动创建ZIP包
- 适用于需要查看包含文件的场景

### 3. `scripts/build.py`
- 跨平台打包脚本
- 编译完成后自动创建ZIP包
- 单文件模式打包

## ZIP包内容

ZIP包包含完整的dist目录内容：

### 目录模式 (build_dir_mode.py, fix_and_build.py)
```
label-printing-server/
├── label-printing-server.exe (或 label-printing-server)
├── _internal/
│   ├── 所有依赖库
│   └── Python运行时
├── templates/
├── static/
├── config/
└── data/
```

### 单文件模式 (build.py)
```
dist/
├── label-printing-server.exe (或 label-printing-server)
├── config/
│   └── printer_config_example.json
├── data/
│   ├── logs/
│   └── failed_labels/
└── README.txt
```

## 使用方法

### 1. 运行构建脚本

**Windows:**
```batch
python scripts\fix_and_build.py
# 或
python scripts\build_dir_mode.py
# 或
python scripts\build.py
```

**Linux:**
```bash
python3 scripts/fix_and_build.py
# 或
python3 scripts/build_dir_mode.py
# 或
python3 scripts/build.py
```

### 2. 查找ZIP包

编译完成后，在 `dist/` 目录下会自动生成：
- `label-printing-server.zip` - 标准版本
- `label-printing-server_{platform}_{timestamp}.zip` - 带时间戳的备份

例如：
```
dist/
├── label-printing-server/          # 编译输出目录
├── label-printing-server.zip       # 标准ZIP包
└── label-printing-server_windows_20251106_115300.zip  # 备份ZIP包
```

### 3. 部署ZIP包

1. 将ZIP包复制到目标机器
2. 解压到任意目录
3. 进入解压目录
4. 运行程序：
   - Windows: `label-printing-server.exe`
   - Linux: `./label-printing-server`

## ZIP包特点

### 优势
- ✅ **便于分发**：单个文件，方便传输
- ✅ **完整性**：包含所有必要的文件和依赖
- ✅ **版本管理**：带时间戳的备份便于版本追踪
- ✅ **压缩**：减小文件大小，节省存储空间

### 文件大小
- 目录模式：通常 80-150 MB（压缩后）
- 单文件模式：通常 60-100 MB（压缩后）

## 技术实现

### 关键代码
```python
import zipfile
from datetime import datetime

def create_zip_package():
    """将打包好的程序压缩成zip文件"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    system_name = platform.system().lower()
    
    # 创建两个版本的ZIP
    zip_filename_simple = 'dist/label-printing-server.zip'
    zip_filename = f'dist/label-printing-server_{system_name}_{timestamp}.zip'
    
    with zipfile.ZipFile(zip_filename_simple, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # 遍历并压缩文件
        for root, dirs, files in os.walk(dist_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, 'dist')
                zipf.write(file_path, arcname)
    
    # 创建备份
    shutil.copy2(zip_filename_simple, zip_filename)
```

### 压缩格式
- 使用 `ZIP_DEFLATED` 压缩算法
- 跨平台兼容
- 标准ZIP格式，支持所有解压工具

## 故障排查

### ZIP创建失败
如果看到 "✗ 创建ZIP失败" 消息：
1. 检查 `dist/` 目录是否存在
2. 确保有足够的磁盘空间
3. 检查文件权限

### ZIP包损坏
如果解压时出错：
1. 使用带时间戳的备份版本
2. 重新运行构建脚本
3. 检查磁盘空间和权限

## 更新日期

2025-11-06

## 相关文档

- [BUILD.md](BUILD.md) - 构建说明
- [跨平台部署指南.md](跨平台部署指南.md) - 部署指南

