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
├── config/                         # 配置文件目录（运行时配置）
│   ├── printer_config.json         # 配置文件 ⭐
│   ├── printer_config_example.json # 配置示例
│   └── ...
├── src/                            # 源代码目录
│   ├── config/                     # 配置管理模块
│   │   ├── config.py               # 配置管理代码
│   ├── core/                       # 核心功能模块
│   │   ├── printer.py              # 打印机控制
│   │   ├── mqtt_client.py          # MQTT客户端
│   │   ├── zpl_generator.py        # ZPL代码生成
│   │   ├── pdf_printer.py          # PDF打印
│   │   └── escpos_printer.py       # ESC/POS打印
│   └── utils/                      # 工具模块
│       ├── font_utils.py           # 字体工具
│       ├── image_utils.py          # 图像处理
│       └── fuzzy_match.py          # 模糊匹配
├── scripts/                        # 脚本目录
│   ├── build.py                    # 构建脚本
│   └── tools/                      # 工具脚本
├── tests/                          # 测试模块
│   ├── test_mqtt_send.py           # MQTT测试
│   └── ...
├── docs/                           # 文档目录
├── data/                           # 运行时数据目录
│   ├── logs/                       # 日志目录
│   └── failed_labels/             # 失败标签保存目录
├── requirements.txt                # 依赖管理
└── README.md                       # 项目说明
```

## 🚀 快速开始

> **💡 推荐方式：**使用自动化初始化脚本，一键完成环境配置！

### 方式一：自动初始化（推荐）⭐

使用初始化脚本自动完成所有配置：

**Windows 系统：**
```cmd
# 双击运行或命令行执行
init.bat
```

**Linux/Mac 系统：**
```bash
chmod +x init.sh
./init.sh
```

**自动完成：**
- ✅ 创建虚拟环境
- ✅ 安装所有依赖（使用阿里云镜像，速度快！）
- ✅ 创建目录结构
- ✅ 生成配置文件

**启动服务：**
```cmd
# Windows
start.bat

# Linux/Mac
./start.sh
```

📖 详细说明请查看：[快速开始.md](快速开始.md) 或 [项目初始化说明.md](项目初始化说明.md)

---

### 方式二：手动安装

#### 1. 安装依赖

```bash
pip install -r requirements.txt
```

#### 2. 配置打印机

编辑 `config/printer_config.json`：

**方式1：使用URL格式（推荐）**
```json
{
  "mqtt": {
    "url": "mqtt://127.0.0.1:1883",
    "topic": "zebra/print",
    "username": null,
    "password": null
  },
  "printer": {
    "name": "ZT411"
  }
}
```

**方式2：使用分离格式（向后兼容）**
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

**支持的URL格式：**
- `mqtt://127.0.0.1:1883` - 标准MQTT
- `ws://10.100.10.121:8083/mqtt` - WebSocket MQTT（带路径）
- `tcp://10.100.10.121:1883` - TCP MQTT（不带路径）
- `mqtts://example.com:8883` - SSL MQTT

**注意：** 
- URL中可以包含路径（如 `/mqtt`），路径会保留但不会用作topic
- Topic需要单独配置，不受URL路径影响

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

### 快速入门
- ⚡ [快速开始.md](快速开始.md) - 5分钟快速上手指南
- 🔧 [项目初始化说明.md](项目初始化说明.md) - init.py 详细说明
- 🚀 [启动脚本使用说明.md](启动脚本使用说明.md) - start 脚本详细说明

### 功能文档
- [MQTT打印机使用说明](docs/MQTT打印机-README.md)
- [MQTT打印说明](docs/MQTT打印说明.md)
- [WEB服务使用说明](docs/WEB服务使用说明.md)
- [打印机模糊搜索说明](docs/打印机模糊搜索说明.md)
- [打印机优先级选择说明](docs/打印机优先级选择说明.md)

### 部署文档
- [完整部署指南](docs/完整部署指南.md)
- [跨平台部署指南](docs/跨平台部署指南.md)
- [BUILD.md](docs/BUILD.md) - 打包可执行文件

### 故障排除
- [故障排除_打印乱码](docs/故障排除_打印乱码.md)
- [打印乱码_解决方案](打印乱码_解决方案.md)

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
- **src/config/**: 配置管理模块，处理配置文件加载
- **src/core/**: 核心业务逻辑
  - `printer.py`: 打印机控制，支持多平台
  - `mqtt_client.py`: MQTT消息接收和处理
  - `zpl_generator.py`: ZPL标签代码生成
  - `pdf_printer.py`: PDF文档打印
  - `escpos_printer.py`: ESC/POS热敏打印
- **src/utils/**: 通用工具函数
  - `font_utils.py`: 字体路径获取
  - `image_utils.py`: 文本转图像
  - `fuzzy_match.py`: 模糊匹配算法
- **scripts/**: 构建和工具脚本
- **tests/**: 测试脚本和测试数据
- **docs/**: 项目文档
- **data/**: 运行时数据（日志、失败的标签等）

### 添加新功能

1. 在 `src/` 目录下的对应模块中添加功能
2. 更新对应模块的 `__init__.py` 导出
3. 在 `app.py` 中集成
4. 添加相应的测试脚本到 `tests/` 目录

## 📅 更新日期

2026-06-26

### v2.0 更新 (2026-06-26)

- 🎨 **可视化标签设计器**: 集成 vue-print-designer，支持拖拽设计标签模板
- 🖨️ **TSPL 打印机适配**: 支持 得利 DL-825T (300 DPI)，ZPL→TSPL 自动转换
- 📐 **设计器坐标映射**: 完善 px→mm→dots 坐标转换，所见即所得
- 🔤 **中文打印支持**: TSS24.BF2 中文字体 + 英文内置字体
- 📋 **打印模板管理**: CRUD API，模板保存/加载/删除
- 🔗 **WPS 多维表格集成**: 一键打印，关联字段 ID→名称自动映射
- 🎯 **多行文本**: 支持 \n 换行，2 项/行自动排版
- 🛠️ **打印代理**: 本地拉取云端任务，支持 USB/网络打印机

### 模板变量命名规则

| 模板变量 | WPS 字段 | 说明 |
|---------|---------|------|
| `@barcode` | 订单编号 | 条码字段 |
| `@客户名称` | 客户名称 | 自动映射 ID→名称 |
| `@产品名称` | 标题字段 | 自动提取 |
| 其他 | 同名列 | 直接匹配 |

## 📄 许可证

MIT License

## 👨‍💻 贡献

欢迎提交Issue和Pull Request！

