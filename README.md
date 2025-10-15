# 斑马打印机MQTT标签打印服务

一个跨平台的标签打印服务，通过MQTT接收标签数据并自动打印到斑马打印机（ZT411等型号），支持中文。

## ⭐ 特性

- ✅ **跨平台支持**：Windows、Linux (AMD64/ARM)
- ✅ **中文支持**：自动将中文转换为图像
- ✅ **智能模糊搜索**：打印机名称支持模糊匹配
- ✅ **多种连接方式**：USB、网络、CUPS
- ✅ **MQTT消息队列**：稳定可靠
- ✅ **JSON格式数据**：易于集成
- ✅ **支持条形码/二维码**
- ✅ **模块化架构**：易于维护和扩展

## 📁 项目结构

```
label-printing-server/
├── app.py                          # 主入口文件 ⭐
├── config/                         # 配置模块
│   ├── __init__.py
│   ├── config.py                   # 配置管理
│   └── printer_config.json         # 配置文件
├── core/                           # 核心功能模块
│   ├── __init__.py
│   ├── printer.py                  # 打印机控制
│   ├── mqtt_client.py              # MQTT客户端
│   └── zpl_generator.py            # ZPL代码生成
├── utils/                          # 工具模块
│   ├── __init__.py
│   ├── font_utils.py               # 字体工具
│   ├── image_utils.py              # 图像处理
│   └── fuzzy_match.py              # 模糊匹配
├── tests/                          # 测试模块
│   ├── test_mqtt_send.py           # MQTT测试
│   ├── test-chinese.py             # 中文测试
│   └── test-zt411.py               # 打印机测试
├── docs/                           # 文档目录
│   ├── MQTT打印机-README.md
│   ├── MQTT打印说明.md
│   ├── 打印机模糊搜索说明.md
│   └── 跨平台部署指南.md
├── logs/                           # 日志目录
├── failed_labels/                  # 失败标签保存目录
├── requirements.txt                # 依赖管理
└── README.md                       # 项目说明
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置打印机

编辑 `config/printer_config.json`：

```json
{
  "mqtt": {
    "host": "127.0.0.1",
    "port": 1883,
    "topic": "zebra/print"
  },
  "printer": {
    "name": "ZT411"
  }
}
```

### 3. 启动服务

```bash
python app.py
```

或使用启动脚本：

**Windows:**
```batch
start.bat
```

**Linux:**
```bash
chmod +x start.sh
./start.sh
```

## 📝 配置说明

### 简化配置（推荐）

无需完整打印机名称，使用关键词即可：

```json
{
  "printer": {
    "name": "ZT411"
  }
}
```

程序会自动匹配到 `ZDesigner ZT411-300dpi`

### 网络打印机

```json
{
  "printer": {
    "ip": "192.168.1.100",
    "port": 9100
  }
}
```

### 更多配置选项

查看 [docs/打印机模糊搜索说明.md](docs/打印机模糊搜索说明.md)

## 📡 MQTT消息格式

发送到主题 `zebra/print` 的JSON消息：

```json
{
  "title": "产品标签",
  "fields": [
    {
      "label": "产品名称",
      "value": "精密电子元件",
      "font_size": 28
    },
    {
      "label": "序列号",
      "value": "SN20251015001",
      "font_size": 22
    }
  ],
  "barcode": "SN20251015001",
  "qrcode": "SN20251015001"
}
```

## 🧪 测试

### 发送测试消息

```bash
cd tests
python test_mqtt_send.py
```

### 测试中文打印

```bash
cd tests
python test-chinese.py
```

## 🌍 平台支持

### Windows
- USB打印机（win32print）- 支持模糊搜索
- 网络打印机（socket）

### Linux
- CUPS打印（pycups）- 支持模糊搜索
- USB设备（/dev/usb/lp0）
- 网络打印机（socket）

### ARM（树莓派等）
- 完全支持Linux所有功能

## 📖 详细文档

- [MQTT打印机使用说明](docs/MQTT打印机-README.md)
- [MQTT打印说明](docs/MQTT打印说明.md)
- [打印机模糊搜索说明](docs/打印机模糊搜索说明.md)
- [跨平台部署指南](docs/跨平台部署指南.md)

## 🐛 故障排查

### 中文显示乱码

```bash
# 确认安装Pillow
pip install Pillow

# Linux安装中文字体
sudo apt-get install fonts-wqy-zenhei
```

### 找不到打印机

程序会显示所有可用打印机，然后使用模糊搜索或完整名称配置。

### 模块导入错误

确保在项目根目录运行：

```bash
python app.py
```

## 📊 系统架构

```
┌─────────────┐
│  应用系统    │ 发送JSON数据
└──────┬──────┘
       │ MQTT
       ↓
┌───────────────────────────────┐
│ app.py (主入口)                │
│  ├── config (配置管理)         │
│  ├── core (核心功能)           │
│  │   ├── mqtt_client          │
│  │   ├── zpl_generator        │
│  │   └── printer              │
│  └── utils (工具函数)          │
└──────┬────────────────────────┘
       │
       ├──→ Windows (USB/Network)
       ├──→ Linux CUPS
       ├──→ Linux USB (/dev/usb/lp0)
       └──→ Network (All Platforms)
       │
       ↓
┌─────────────┐
│ 斑马打印机   │
│  ZT411      │
└─────────────┘
```

## 🔧 开发说明

### 项目架构

- **app.py**: 主入口，负责启动服务
- **config/**: 配置管理模块，处理配置文件加载
- **core/**: 核心业务逻辑
  - `printer.py`: 打印机控制，支持多平台
  - `mqtt_client.py`: MQTT消息接收和处理
  - `zpl_generator.py`: ZPL标签代码生成
- **utils/**: 通用工具函数
  - `font_utils.py`: 字体路径获取
  - `image_utils.py`: 文本转图像
  - `fuzzy_match.py`: 模糊匹配算法

### 添加新功能

1. 在对应模块中添加功能
2. 更新 `__init__.py` 导出
3. 在 `app.py` 中集成

## 📅 更新日期

2025-10-15

## 📄 许可证

MIT License

## 👨‍💻 贡献

欢迎提交Issue和Pull Request！

