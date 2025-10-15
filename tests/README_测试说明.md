# MQTT 打印测试说明

## 测试脚本概览

### 1. 自动测试脚本（推荐）⭐

**文件**: `test_auto_print.py`

**功能**: 快速测试所有打印类型，无需用户确认

**支持格式**:
- ZPL 标签
- PDF 文档
- TXT 文本
- ESC/POS 小票

**使用方法**:
```bash
# 确保打印服务已启动
python app.py

# 在另一个终端运行测试
python tests/test_auto_print.py
```

**特点**:
- ✅ 全自动执行
- ✅ 快速测试
- ✅ 无需创建文件
- ✅ 实时显示结果

---

### 2. 完整格式测试脚本

**文件**: `test_multi_format_mqtt.py`

**功能**: 创建并测试多种文件格式

**支持格式**:
- PDF 文档
- TXT 文本文件
- ZPL 标签代码
- ESC/POS 小票数据
- JPG 图片
- DOC/RTF 文档

**使用方法**:
```bash
# 安装可选依赖（用于创建PDF和图片）
pip install reportlab Pillow

# 运行测试
python tests/test_multi_format_mqtt.py
```

**特点**:
- ✅ 创建实际文件
- ✅ 测试文件转base64
- ✅ 需要用户确认
- ✅ 保存测试文件供后续使用

---

## 消息格式说明

### ZPL 标签打印

**方式1: 直接发送 ZPL 代码**（推荐）
```json
{
  "print_type": "label",
  "zpl_code": "^XA^FO50,50^A0N,50,50^FDHello^FS^XZ"
}
```

**方式2: 自动生成 ZPL**
```json
{
  "print_type": "label",
  "text": "Hello World",
  "width": 100,
  "height": 50
}
```

### PDF 文档打印

**方式1: Base64 编码**
```json
{
  "print_type": "pdf",
  "pdf_data": "JVBERi0xLjQKJeLjz9MKMSAwIG9iag..."
}
```

**方式2: 文件路径**（仅服务器本地）
```json
{
  "print_type": "pdf",
  "pdf_file": "/path/to/document.pdf"
}
```

### TXT 文本打印

```json
{
  "print_type": "pdf",
  "pdf_data": "base64编码的文本内容"
}
```

注意: 文本文件也通过 PDF 打印机处理（会被识别为文本格式）

### ESC/POS 小票打印

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

### JPG 图片打印

```json
{
  "print_type": "pdf",
  "pdf_data": "base64编码的JPG图片"
}
```

注意: 图片会被检测并正确处理

---

## 文件类型检测

系统会自动检测 base64 数据的文件类型：

| 文件类型 | 识别标志 | 处理方式 |
|---------|---------|---------|
| PDF | `%PDF` | SumatraPDF 打印 |
| DOCX | `PK\x03\x04` | 转换后打印 |
| DOC | `\xd0\xcf\x11\xe0` | 转换后打印 |
| TXT | UTF-8 文本 | 文本打印 |
| JPG | JPEG 标志 | 图片打印 |
| PNG | PNG 标志 | 图片打印 |

---

## 测试流程

### 第一步：启动打印服务

```bash
python app.py
```

**预期输出**:
```
======================================================================
                    打印机MQTT服务
======================================================================
MQTT服务器: 10.100.10.121:1883
订阅主题: zebra/print
----------------------------------------------------------------------
已配置的打印机:

  [1] ZT411 ⭐ 专用
      设备: ZDesigner ZT411-300dpi ZPL
      支持格式: label(ZPL)

  [2] KONICA 🔄 备选
      设备: 自动检测
      支持格式: label(ZPL), pdf, receipt(ESC/POS)
      说明: 当找不到专用打印机时使用
...
服务已启动，等待打印任务...
```

### 第二步：运行测试脚本

**快速测试**:
```bash
python tests/test_auto_print.py
```

**完整测试**:
```bash
python tests/test_multi_format_mqtt.py
```

### 第三步：查看结果

**服务端日志**:
```
============================================================
收到打印任务
主题: zebra/print
数据: {
  "print_type": "label",
  "zpl_code": "^XA..."
}
类型: ZPL标签打印
  使用: 标签专用打印机
  ZPL来源: 直接提供
✓ ZPL标签打印成功
============================================================
```

**客户端输出**:
```
【1/4】测试 ZPL 标签打印
------------------------------------------------------------
  ZPL 标签: ✓ 已发送

【2/4】测试 PDF 文档打印
------------------------------------------------------------
  PDF 文档: ✓ 已发送
...
```

---

## 常见问题

### Q1: 测试脚本连接不上 MQTT

**检查**:
1. MQTT 服务器地址是否正确
2. 打印服务是否已启动
3. 防火墙是否阻止连接

**解决**:
```bash
# 检查配置
cat config/printer_config.json

# 测试 MQTT 连接
pip install paho-mqtt
python -c "import paho.mqtt.client as mqtt; c=mqtt.Client(); c.connect('10.100.10.121', 1883)"
```

### Q2: 打印任务发送成功但没有输出

**检查**:
1. 查看服务端日志的错误信息
2. 确认打印机是否在线
3. 检查打印机是否有纸张

### Q3: PDF 打印失败

**常见原因**:
1. SumatraPDF 未安装或路径不正确
2. 打印机名称不匹配
3. PDF 文件损坏

**解决**:
```bash
# 运行诊断工具
python tests/check_sumatra_pdf.py
python tests/diagnose_pdf_print.py
```

### Q4: 中文打印乱码

**PDF/文档打印**:
- 确保文件使用 UTF-8 编码
- PDF 需要嵌入中文字体

**ZPL 标签打印**:
- 斑马打印机需要下载中文字体
- 或使用图片方式打印中文

---

## 性能测试

### 测试打印速度

```python
import time

start = time.time()
# 发送100个打印任务
for i in range(100):
    client.publish(topic, json.dumps(message))
end = time.time()

print(f"发送100个任务耗时: {end-start:.2f}秒")
print(f"平均速度: {100/(end-start):.1f}个/秒")
```

### 测试并发打印

```bash
# 同时运行多个测试脚本
python tests/test_auto_print.py &
python tests/test_auto_print.py &
python tests/test_auto_print.py &
wait
```

---

## 扩展测试

### 自定义测试消息

创建 `custom_test.json`:
```json
{
  "print_type": "label",
  "zpl_code": "^XA^FO50,50^A0N,80,80^FD你的文本^FS^XZ"
}
```

发送:
```bash
mosquitto_pub -h 10.100.10.121 -t zebra/print -f custom_test.json
```

### 批量测试

创建 `batch_test.sh`:
```bash
#!/bin/bash
for i in {1..10}; do
  python tests/test_auto_print.py
  sleep 2
done
```

---

## 测试清单

### 基本功能测试

- [ ] ZPL 标签打印
- [ ] PDF 文档打印
- [ ] TXT 文本打印
- [ ] ESC/POS 小票打印

### 高级功能测试

- [ ] 图片打印（JPG/PNG）
- [ ] Word 文档打印（DOC/DOCX）
- [ ] 中文内容打印
- [ ] 大文件打印（>1MB）

### 异常处理测试

- [ ] 打印机离线
- [ ] 无效的 ZPL 代码
- [ ] 损坏的 PDF 文件
- [ ] 网络中断
- [ ] MQTT 断开重连

### 性能测试

- [ ] 连续打印 100 个任务
- [ ] 并发 10 个客户端
- [ ] 大文件传输（10MB PDF）

---

## 相关文档

- [打印机优先级选择说明](../docs/打印机优先级选择说明.md)
- [SumatraPDF 配置说明](../docs/SumatraPDF配置说明.md)
- [PDF 打印错误码修复说明](../docs/PDF打印错误码1修复说明.md)

