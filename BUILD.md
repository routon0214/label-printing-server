# 编译打包说明

## 🎯 快速开始

### Windows 平台打包

```batch
# 1. 安装打包工具
pip install pyinstaller

# 2. 执行打包（方式一：推荐）
build-windows.bat

# 或方式二：使用Python脚本
python build.py
```

### Linux 平台打包

```bash
# 1. 安装打包工具
pip3 install pyinstaller

# 2. 执行打包（方式一：推荐）
chmod +x build-linux.sh
./build-linux.sh

# 或方式二：使用Python脚本
python3 build.py
```

## 📦 输出结果

打包完成后，可执行文件位于：

```
dist/
├── windows-amd64/              # Windows 版本
│   ├── label-printing-server.exe
│   ├── config/
│   ├── logs/
│   ├── failed_labels/
│   └── README.txt
│
└── linux-x86_64/               # Linux 版本
    ├── label-printing-server/
    ├── config/
    ├── logs/
    ├── failed_labels/
    └── README.txt
```

## 🚀 使用打包后的程序

### Windows

```batch
cd dist\windows-amd64
label-printing-server.exe
```

### Linux

```bash
cd dist/linux-x86_64/label-printing-server
./label-printing-server
```

## 📋 打包文件清单

### 已创建的文件

1. **app.spec** - PyInstaller配置文件
2. **build.py** - 跨平台自动打包脚本
3. **build-windows.bat** - Windows打包批处理
4. **build-linux.sh** - Linux打包脚本
5. **docs/打包部署指南.md** - 详细打包文档

### 配置说明

所有打包配置都在 `app.spec` 文件中，包括：
- 数据文件打包
- 隐藏导入模块
- 平台特定配置
- 可执行文件设置

## 🔧 自定义打包

### 修改可执行文件名

编辑 `app.spec`：

```python
exe = EXE(
    ...
    name='your-custom-name',  # 修改这里
    ...
)
```

### 添加图标（Windows）

```python
exe = EXE(
    ...
    icon='icon.ico',  # 添加图标文件路径
    ...
)
```

### 添加额外的数据文件

```python
datas = [
    ('config/printer_config_example.json', 'config'),
    ('your_file.txt', '.'),  # 添加新文件
]
```

## 🎨 打包特性

- ✅ 自动检测平台（Windows/Linux/macOS）
- ✅ 自动识别架构（AMD64/ARM64/x86）
- ✅ 创建平台特定的输出目录
- ✅ 自动复制必要的配置文件
- ✅ 生成README说明文档
- ✅ 包含所有Python依赖
- ✅ 支持中文字体和图像处理
- ✅ 打包MQTT客户端和打印机驱动

## 📊 打包大小优化

典型打包大小：
- Windows: ~50-80 MB
- Linux: ~50-80 MB

优化建议：
1. 使用虚拟环境减少依赖
2. 排除不必要的模块
3. 启用UPX压缩

## 🐛 常见问题

### 1. 打包后找不到配置文件

**解决**: 配置文件会自动创建在可执行文件同级的 `config/` 目录

### 2. 杀毒软件误报

**解决**: 
- 添加到白名单
- 考虑代码签名

### 3. 缺少模块错误

**解决**: 在 `app.spec` 的 `hiddenimports` 中添加缺失的模块

## 📖 详细文档

查看完整文档：[docs/打包部署指南.md](docs/打包部署指南.md)

## 💡 提示

1. 首次打包建议在虚拟环境中进行
2. 打包前确保所有依赖已安装
3. 打包后务必在目标平台测试
4. 不同平台需要在对应平台上打包

## 📅 版本

- 版本: 1.0.0
- 更新日期: 2025-10-15

