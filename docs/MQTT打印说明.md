# 斑马打印机MQTT标签打印系统

通过MQTT接收标签数据并自动打印到ZT411斑马打印机，支持中文。

## 功能特点

- ✅ 通过MQTT接收打印任务
- ✅ 自动查找ZT411打印机
- ✅ 支持中文（自动转换为图像）
- ✅ JSON格式数据
- ✅ 支持条形码和二维码
- ✅ 自动重连
- ✅ 失败任务自动保存

## 文件说明

| 文件 | 说明 |
|------|------|
| `zebra_mqtt_printer.py` | 主程序（MQTT订阅和打印） |
| `printer_config.json` | 配置文件 |
| `test_mqtt_send.py` | 测试发送脚本 |

## 快速开始

### 1. 安装依赖

```bash
pip install paho-mqtt Pillow pywin32
```

或使用 requirements.txt：

```bash
pip install -r requirements.txt
```

### 2. 配置

编辑 `printer_config.json`：

```json
{
  "mqtt": {
    "host": "127.0.0.1",        // MQTT服务器地址
    "port": 1883,                // MQTT端口
    "topic": "zebra/print",      // 订阅主题
    "username": null,            // 用户名（可选）
    "password": null             // 密码（可选）
  },
  "printer": {
    "name": null                 // null表示自动查找ZT411
  }
}
```

### 3. 启动服务

```bash
python zebra_mqtt_printer.py
```

启动后会显示：

```
============================================================
斑马打印机MQTT服务
============================================================
MQTT服务器: 127.0.0.1:1883
订阅主题: zebra/print
打印机: ZDesigner ZT411-300dpi
============================================================

正在连接MQTT服务器...
✓ 已连接到MQTT服务器: 127.0.0.1:1883
✓ 订阅主题: zebra/print
服务已启动，等待打印任务...
```

### 4. 发送测试

打开新的命令行窗口，运行：

```bash
python test_mqtt_send.py
```

## MQTT消息格式

### JSON格式

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
      "label": "产品型号",
      "value": "ZX-2024-PRO",
      "font_size": 25
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

### 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `title` | string | 否 | 标签标题 |
| `fields` | array | 否 | 字段列表 |
| `fields[].label` | string | 否 | 字段标签 |
| `fields[].value` | string | 是 | 字段值 |
| `fields[].font_size` | int | 否 | 字体大小（默认25） |
| `barcode` | string | 否 | 条形码内容 |
| `qrcode` | string | 否 | 二维码内容 |

## 使用示例

### Python发送

```python
import paho.mqtt.client as mqtt
import json

# 连接MQTT
client = mqtt.Client()
client.connect("127.0.0.1", 1883, 60)

# 标签数据
label = {
    "title": "产品标签",
    "fields": [
        {"label": "产品", "value": "测试产品", "font_size": 28},
        {"label": "编号", "value": "12345", "font_size": 25}
    ],
    "barcode": "12345",
    "qrcode": "12345"
}

# 发送
client.publish("zebra/print", json.dumps(label, ensure_ascii=False))
client.disconnect()
```

### Node.js发送

```javascript
const mqtt = require('mqtt');
const client = mqtt.connect('mqtt://127.0.0.1:1883');

client.on('connect', () => {
    const label = {
        title: "产品标签",
        fields: [
            {label: "产品", value: "测试产品", font_size: 28},
            {label: "编号", value: "12345", font_size: 25}
        ],
        barcode: "12345",
        qrcode: "12345"
    };
    
    client.publish('zebra/print', JSON.stringify(label));
    client.end();
});
```

### MQTT工具发送

使用 MQTT.fx、MQTTX 等工具：

1. 连接到 MQTT 服务器
2. 主题：`zebra/print`
3. 消息：上面的JSON格式

## 中文支持

程序会自动检测中文字符并转换为图像：

- **包含中文**：自动转换为图像（支持任意中文）
- **纯英文数字**：直接使用ZPL字体（更快速）

### 字体大小建议

- **标题**：35-45
- **主要内容**：25-30
- **次要内容**：18-22

## 配置说明

### MQTT配置

```json
{
  "mqtt": {
    "host": "mqtt.example.com",
    "port": 1883,
    "topic": "factory/printer/zebra",
    "username": "printer",
    "password": "secret123"
  }
}
```

### 打印机配置

```json
{
  "printer": {
    "name": "ZDesigner ZT411-300dpi"
  }
}
```

设置为 `null` 时自动查找ZT411打印机。

## 运行模式

### 前台运行

```bash
python zebra_mqtt_printer.py
```

按 `Ctrl+C` 停止。

### 后台运行（Windows）

创建批处理文件 `start_printer.bat`：

```batch
@echo off
start /B python zebra_mqtt_printer.py > printer.log 2>&1
```

### Windows服务

可以使用 `nssm` 或 `pywin32` 将程序安装为Windows服务。

## 故障排查

### 未找到打印机

1. 检查打印机是否开机
2. 检查USB连接
3. 在配置文件中指定完整打印机名称

### MQTT连接失败

1. 检查服务器地址和端口
2. 检查防火墙设置
3. 验证用户名密码（如果需要）

### 中文显示乱码

1. 确认已安装 Pillow：`pip install Pillow`
2. 检查Windows是否有中文字体
3. 查看日志中的"使用字体"信息

### 打印失败

打印失败时，ZPL代码会自动保存到 `failed_label_时间戳.zpl` 文件。

## 性能优化

- 中文转换需要1-2秒，这是正常的
- 纯英文数字打印更快（不需要图像转换）
- ZT411-300dpi可以快速处理图像数据

## 生产环境部署

1. **配置文件**：根据实际环境修改配置
2. **日志记录**：可以重定向输出到日志文件
3. **监控**：建议添加心跳检测和告警
4. **备份**：定期备份配置文件

## 扩展功能

程序支持扩展，可以添加：

- 多打印机支持
- 打印队列管理
- 打印历史记录
- Web管理界面
- 数据库集成

## 技术支持

如有问题，请提供：

- 错误信息
- 配置文件内容
- Python版本
- 打印机型号

## 更新日期

2025-10-15

