# MQTT 打印快速参考

## 快速开始

### 1. 启动服务
```bash
python app.py
```

### 2. 发送测试
```bash
python tests/test_auto_print.py
```

---

## 消息格式速查

### ZPL 标签（直接发送）⭐ 推荐

```json
{
  "print_type": "label",
  "zpl_code": "^XA^FO50,50^A0N,50,50^FDHello^FS^XZ"
}
```

**Python 示例**:
```python
import paho.mqtt.client as mqtt
import json

client = mqtt.Client()
client.connect("10.100.10.121", 1883)

message = {
    "print_type": "label",
    "zpl_code": "^XA^FO50,50^A0N,50,50^FDTest^FS^XZ"
}

client.publish("zebra/print", json.dumps(message))
client.disconnect()
```

---

### PDF 文档（Base64）

```json
{
  "print_type": "pdf",
  "pdf_data": "JVBERi0xLjQKJe..."
}
```

**Python 示例**:
```python
import base64

with open("document.pdf", "rb") as f:
    pdf_base64 = base64.b64encode(f.read()).decode('utf-8')

message = {
    "print_type": "pdf",
    "pdf_data": pdf_base64
}

client.publish("zebra/print", json.dumps(message))
```

---

### 文本文件

```json
{
  "print_type": "pdf",
  "pdf_data": "VGVzdCB0ZXh0IGNvbnRlbnQ="
}
```

**Python 示例**:
```python
text = "测试文本内容\nTest Content"
text_base64 = base64.b64encode(text.encode('utf-8')).decode('utf-8')

message = {
    "print_type": "pdf",
    "pdf_data": text_base64
}

client.publish("zebra/print", json.dumps(message))
```

---

### ESC/POS 小票

```json
{
  "print_type": "receipt",
  "title": "测试小票",
  "items": [
    {"name": "商品A", "price": 10.00, "qty": 2}
  ],
  "total": 20.00
}
```

**Python 示例**:
```python
message = {
    "print_type": "receipt",
    "title": "销售小票",
    "items": [
        {"name": "商品A", "price": 10.00, "qty": 2},
        {"name": "商品B", "price": 15.50, "qty": 1}
    ],
    "total": 35.50
}

client.publish("zebra/print", json.dumps(message))
```

---

## 命令行工具

### 使用 mosquitto_pub

**发送 ZPL**:
```bash
mosquitto_pub -h 10.100.10.121 -t zebra/print -m '{
  "print_type": "label",
  "zpl_code": "^XA^FO50,50^A0N,50,50^FDTest^FS^XZ"
}'
```

**发送 PDF**:
```bash
# 先转换为 base64
base64 document.pdf > document.b64

# 创建消息文件
cat > message.json << EOF
{
  "print_type": "pdf",
  "pdf_data": "$(cat document.b64)"
}
EOF

# 发送
mosquitto_pub -h 10.100.10.121 -t zebra/print -f message.json
```

---

## Node.js 示例

### 安装依赖
```bash
npm install mqtt
```

### ZPL 打印
```javascript
const mqtt = require('mqtt');

const client = mqtt.connect('mqtt://10.100.10.121:1883');

client.on('connect', () => {
  const message = {
    print_type: 'label',
    zpl_code: '^XA^FO50,50^A0N,50,50^FDTest^FS^XZ'
  };
  
  client.publish('zebra/print', JSON.stringify(message));
  client.end();
});
```

### PDF 打印
```javascript
const fs = require('fs');

const pdfData = fs.readFileSync('document.pdf');
const pdfBase64 = pdfData.toString('base64');

const message = {
  print_type: 'pdf',
  pdf_data: pdfBase64
};

client.publish('zebra/print', JSON.stringify(message));
```

---

## 打印机选择逻辑

### 自动选择
系统会自动根据 `print_type` 选择打印机：

| print_type | 优先选择 | 备选 |
|-----------|---------|-----|
| label | 专用标签打印机 | 通用打印机 |
| pdf | 专用PDF打印机 | 通用打印机 |
| receipt | 专用小票打印机 | 通用打印机 |

### 手动指定（可选）
```json
{
  "print_type": "pdf",
  "pdf_data": "...",
  "printer": "KONICA MINOLTA Universal PCL"
}
```

---

## 错误处理

### 服务端日志示例

**成功**:
```
收到打印任务
类型: ZPL标签打印
  使用: 标签专用打印机
  ZPL来源: 直接提供
✓ ZPL标签打印成功
```

**失败**:
```
收到打印任务
类型: PDF文档打印
  使用: 通用打印机（备选）
⚠ SumatraPDF返回错误码: 1
✗ PDF打印失败
```

### 常见错误及解决

| 错误信息 | 原因 | 解决方案 |
|---------|------|---------|
| 未配置XX打印机 | 没有对应类型的打印机 | 配置专用或通用打印机 |
| SumatraPDF返回错误码: 1 | 打印机名称不匹配 | 检查打印机名称 |
| JSON解析失败 | 消息格式错误 | 检查 JSON 格式 |
| 连接失败 | MQTT服务器不可达 | 检查网络和服务器 |

---

## 性能优化

### 批量打印
```python
# 使用持久连接
client = mqtt.Client()
client.connect("10.100.10.121", 1883)

for i in range(100):
    message = {
        "print_type": "label",
        "zpl_code": f"^XA^FO50,50^A0N,50,50^FD{i}^FS^XZ"
    }
    client.publish("zebra/print", json.dumps(message))

client.disconnect()
```

### 异步发送
```python
import threading

def send_print_job(data):
    client = mqtt.Client()
    client.connect("10.100.10.121", 1883)
    client.publish("zebra/print", json.dumps(data))
    client.disconnect()

# 并发发送
threads = []
for i in range(10):
    t = threading.Thread(target=send_print_job, args=(message,))
    t.start()
    threads.append(t)

for t in threads:
    t.join()
```

---

## 调试技巧

### 1. 监听 MQTT 消息
```bash
mosquitto_sub -h 10.100.10.121 -t zebra/print -v
```

### 2. 测试连接
```bash
mosquitto_pub -h 10.100.10.121 -t test -m "hello"
```

### 3. 查看服务日志
```bash
python app.py 2>&1 | tee print_service.log
```

### 4. 诊断工具
```bash
# 检查 SumatraPDF
python tests/check_sumatra_pdf.py

# 诊断 PDF 打印
python tests/diagnose_pdf_print.py

# 测试打印机优先级
python tests/test_printer_priority.py
```

---

## 最佳实践

### ✅ 推荐做法

1. **使用持久连接** - 批量打印时复用连接
2. **错误处理** - 捕获并记录所有异常
3. **消息验证** - 发送前验证 JSON 格式
4. **Base64 编码** - 所有二进制数据使用 base64
5. **压缩大文件** - 超过 1MB 的文件考虑压缩

### ❌ 避免做法

1. **频繁连接断开** - 每次打印都建立新连接
2. **忽略错误** - 不检查返回结果
3. **发送原始二进制** - 直接发送二进制数据
4. **阻塞等待** - 同步等待打印完成
5. **无限重试** - 失败时无限重试

---

## 更多示例

查看完整测试脚本：
- `tests/test_auto_print.py` - 自动化测试
- `tests/test_multi_format_mqtt.py` - 多格式测试
- `tests/README_测试说明.md` - 详细测试文档

## 相关文档

- [打印机优先级选择说明](./打印机优先级选择说明.md)
- [SumatraPDF 配置说明](./SumatraPDF配置说明.md)
- [MQTT 打印说明](./MQTT打印说明.md)

