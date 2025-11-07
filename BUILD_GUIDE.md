# 打包编译指南

## 支持的平台

本项目支持以下平台的编译：

- ✅ **Windows (AMD64)** - Windows 10/11 64位
- ✅ **Linux (AMD64)** - Ubuntu, Debian, CentOS 等（x86_64）
- ✅ **Linux (ARM64)** - Raspberry Pi, ARM 服务器等（aarch64）

## 快速开始

### 1. 准备环境

**所有平台通用要求：**
- Python 3.8+
- pip

**推荐使用虚拟环境：**
```bash
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 执行打包

```bash
python build.py
```

## 打包流程

脚本会自动执行以下步骤：

1. ✅ 检查 Python 环境
2. ✅ 检查并安装依赖（从 requirements.txt）
3. ✅ 创建自定义 PyInstaller Hook
4. ✅ 使用目录模式打包
5. ✅ 验证打包结果
6. ✅ 复制数据文件到根目录
7. ✅ 创建 ZIP 压缩包

## 平台特定说明

### Windows

**文件输出：**
```
dist/
├── label-printing-server/
│   ├── label-printing-server.exe    # 主程序
│   ├── _internal/                   # 依赖库
│   └── data/test_samples/           # 示例文件
└── label-printing-server_windows_YYYYMMDD_HHMMSS.zip
```

**运行：**
```cmd
cd dist\label-printing-server
label-printing-server.exe
```

### Linux (AMD64)

**环境准备：**
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3 python3-pip python3-venv

# CentOS/RHEL
sudo yum install python3 python3-pip
```

**文件输出：**
```
dist/
├── label-printing-server/
│   ├── label-printing-server        # 主程序
│   ├── _internal/                   # 依赖库
│   └── data/test_samples/           # 示例文件
└── label-printing-server_linux-amd64_YYYYMMDD_HHMMSS.zip
```

**运行：**
```bash
cd dist/label-printing-server
chmod +x label-printing-server
./label-printing-server
```

### Linux (ARM64)

**环境准备（Raspberry Pi 示例）：**
```bash
sudo apt-get update
sudo apt-get install python3 python3-pip python3-venv
```

**文件输出：**
```
dist/
├── label-printing-server/
│   ├── label-printing-server        # 主程序
│   ├── _internal/                   # 依赖库
│   └── data/test_samples/           # 示例文件
└── label-printing-server_linux-arm64_YYYYMMDD_HHMMSS.zip
```

**运行：**
```bash
cd dist/label-printing-server
chmod +x label-printing-server
./label-printing-server
```

## 输出文件说明

### 目录结构

```
dist/label-printing-server/
├── label-printing-server[.exe]      # 主程序可执行文件
├── _internal/                        # PyInstaller 内部文件（只读）
│   ├── templates/                    # HTML 模板
│   ├── static/                       # CSS/JS 静态文件
│   └── ...                           # Python 依赖库
├── data/
│   └── test_samples/                 # 测试示例文件（用户可修改）✓
│       ├── examples.json
│       ├── label_zpl_chinese.json
│       ├── label_zpl_english.json
│       └── ...
├── config/                           # 配置目录（运行时自动创建）
├── data/logs/                        # 日志目录（运行时自动创建）
└── data/uploads/                     # 上传目录（运行时自动创建）
```

### ZIP 包命名规则

- `label-printing-server_windows_YYYYMMDD_HHMMSS.zip`
- `label-printing-server_linux-amd64_YYYYMMDD_HHMMSS.zip`
- `label-printing-server_linux-arm64_YYYYMMDD_HHMMSS.zip`

同时会创建不带时间戳的版本（覆盖旧版本）：
- `label-printing-server_windows.zip`
- `label-printing-server_linux-amd64.zip`
- `label-printing-server_linux-arm64.zip`

## 跨平台编译

### 在 Windows 上编译 Linux 版本

**不推荐**，因为 PyInstaller 不支持跨平台编译。

推荐使用以下方式：
1. 使用 Docker 容器编译
2. 使用云服务器（如 AWS, Azure）
3. 使用 WSL2 (Windows Subsystem for Linux)

### 使用 Docker 编译

**Linux AMD64:**
```bash
docker run -it --rm -v $(pwd):/app python:3.9-slim bash
cd /app
pip install -r requirements.txt
python build.py
```

**Linux ARM64:**
```bash
docker run -it --rm --platform linux/arm64 -v $(pwd):/app python:3.9-slim bash
cd /app
pip install -r requirements.txt
python build.py
```

## 常见问题

### 1. 打包失败

**检查依赖：**
```bash
pip install -r requirements.txt --upgrade
```

**清理缓存：**
```bash
rm -rf build dist *.spec
python build.py
```

### 2. 运行时缺少模块

检查 `build.py` 中的 `--hidden-import` 配置，添加缺失的模块。

### 3. 平台特定问题

**Windows:**
- 确保安装了 `pywin32`: `pip install pywin32`

**Linux:**
- 确保安装了 CUPS 支持: `sudo apt-get install libcups2-dev`
- 确保安装了 `pycups`: `pip install pycups`

### 4. 示例文件不存在

打包脚本会自动复制 `data/test_samples` 到打包目录。如果缺失：
```bash
# 手动复制
cp -r data/test_samples dist/label-printing-server/data/
```

## 性能优化

### 减小包体积

1. 移除不需要的依赖
2. 使用 `--onefile` 模式（不推荐，因为启动较慢）
3. 排除不需要的模块

### 加快启动速度

- 使用 `--onedir` 模式（当前默认）
- 避免在启动时加载大型库

## 技术支持

如有问题，请检查：
1. Python 版本（需要 3.8+）
2. 所有依赖是否正确安装
3. 运行时日志（`data/logs/`）

## 版本历史

- **v1.0** - 支持 Windows/Linux AMD64/ARM64 平台编译
- 自动复制测试示例文件
- 生成平台特定的 ZIP 包

