# 斑马打印机MQTT标签打印系统

通过MQTT接收标签数据并自动打印到斑马打印机（ZT411等型号），支持中文。

## ⭐ 特性

- ✅ **跨平台支持**：Windows、Linux (AMD64/ARM)
- ✅ **中文支持**：自动将中文转换为图像
- ✅ **智能模糊搜索**：打印机名称支持模糊匹配 🆕
- ✅ **多种连接方式**：USB、网络、CUPS
- ✅ **MQTT消息队列**：稳定可靠
- ✅ **JSON格式数据**：易于集成
- ✅ **支持条形码/二维码**
- ✅ **自动重连**
- ✅ **失败任务保存**

## 🚀 快速开始

### Windows

```batch
1. 双击运行: start.bat
2. 修改配置: printer_config.json
3. 发送测试: python test_mqtt_send.py
```

### Linux

```bash
chmod +x start.sh
./start.sh
```

### 手动启动

```bash
# 安装依赖
pip install paho-mqtt Pillow

# Windows额外依赖
pip install pywin32

# Linux额外依赖（可选）
pip install pycups

# 启动服务
python zebra_mqtt_printer.py
```

## 📝 配置文件 - 支持模糊搜索

### 简化配置（推荐）🆕

无需完整打印机名称，使用关键词即可：

```json
{
  "printer": {
    "name": "ZT411"
  }
}
```

程序会自动匹配到 `ZDesigner ZT411-300dpi`

### 更多示例

```json
// 使用型号
{"printer": {"name": "ZT411"}}

// 使用品牌
{"printer": {"name": "zebra"}}

// 使用系列
{"printer": {"name": "ZDesigner"}}

// 完整名称（完全匹配）
{"printer": {"name": "ZDesigner ZT411-300dpi"}}
```

查看详细说明：[打印机模糊搜索说明.md](打印机模糊搜索说明.md)

## 📡 MQTT消息格式

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

## 📁 文件说明

| 文件 | 说明 |
|------|------|
| `zebra_mqtt_printer.py` | 主程序（MQTT订阅和打印） |
| `printer_config.json` | 配置文件 |
| `printer_config_example.json` | 配置文件示例 |
| `test_mqtt_send.py` | 测试发送脚本 |
| `start.bat` | Windows启动脚本 |
| `start.sh` | Linux启动脚本 |
| `打印机模糊搜索说明.md` | 模糊搜索功能详解 🆕 |
| `跨平台部署指南.md` | 详细部署文档 |

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

## 🎯 模糊搜索功能

### 匹配规则

- **完全匹配**（100分）：`ZDesigner ZT411-300dpi`
- **开头匹配**（90分）：`ZDesigner` → `ZDesigner ZT411-300dpi`
- **包含匹配**（60-80分）：`ZT411` → `ZDesigner ZT411-300dpi`
- **分词匹配**（30-60分）：`zebra 411` → `Zebra ZT411`
- **字符顺序**（10-40分）：`z411` → `Zebra ZT411`

### 输出示例

```
模糊搜索打印机: 'ZT411'
  ✓ 匹配到: ZDesigner ZT411-300dpi (分数: 75)
```

详细说明：[打印机模糊搜索说明.md](打印机模糊搜索说明.md)

## 🐛 故障排查

### 中文显示乱码

```bash
# 确认安装Pillow
pip install Pillow

# Linux安装中文字体
sudo apt-get install fonts-wqy-zenhei
```

### 找不到打印机

程序会显示所有可用打印机：

```
发现 2 台打印机:
  1. Microsoft Print to PDF
  2. ZDesigner ZT411-300dpi
```

然后使用模糊搜索或完整名称配置。

### 模糊搜索未匹配

```json
// 使用更具体的关键词
{"printer": {"name": "ZT411"}}

// 或使用完整名称
{"printer": {"name": "ZDesigner ZT411-300dpi"}}

// 或使用自动检测
{"printer": {"name": null}}
```

## 📖 文档

- [打印机模糊搜索说明](打印机模糊搜索说明.md) - 模糊搜索功能详解 🆕
- [跨平台部署指南](跨平台部署指南.md) - 详细的平台部署说明
- [MQTT打印说明](MQTT打印说明.md) - MQTT使用和API文档

## 📊 系统架构

```
┌─────────────┐
│  应用系统    │ 发送JSON数据
└──────┬──────┘
       │ MQTT
       ↓
┌───────────────────────────────┐
│ zebra_mqtt_printer.py         │
│  - 接收MQTT消息                │
│  - 模糊搜索打印机 🆕           │
│  - 中文转图像                  │
│  - 生成ZPL代码                 │
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

## 📅 更新日期

2025-10-15

## 📄 许可证

MIT License

