# Web界面完整测试流程

## 准备工作

### 1. 配置打印机 ✅
配置文件已更新：`config/printer_config.json`
- 斑马打印机: ZD888-203dpi
- PDF打印机: KONICA MINOLTA

### 2. 测试文件准备 ✅
已创建测试样本文件在 `data/test_samples/` 目录：

**斑马打印机测试**:
- `zd888_english.zpl` - 纯英文ZPL
- `zd888_chinese_simple.json` - 简单中文JSON
- `zd888_chinese_mixed.json` - 中英文混合JSON

**得力打印机测试**:
- `escpos_chinese.json` - 中文小票（结构化）
- `escpos_raw_text.json` - 中文小票（原始文本）

## 测试流程

### 第一步: 启动Web服务

```bash
# 方式1: 直接启动
python web_app.py

# 方式2: UTF-8模式启动（推荐）
start_utf8.bat

# 方式3: 标准启动脚本
start.bat
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

  [1] ZD888
      设备: ZDesigner ZD888-203dpi ZPL
      支持格式: label(ZPL)

  [2] KONICA MINOLTA Universal PCL
      设备: KONICA MINOLTA Universal PCL
      支持格式: pdf
======================================================================
...
[OK] MQTT服务已启动，等待打印任务...
```

### 第二步: 访问Web界面

1. 打开浏览器访问: **http://127.0.0.1:5000**

2. 输入登录信息:
   - 用户名: `admin`
   - 密码: `admin`

3. 应该看到打印服务主界面

### 第三步: 测试斑马打印机

#### 测试3.1: 纯英文 (文件上传)

1. 点击"📤 文件上传打印"标签页
2. 选择文件: `data/test_samples/zd888_english.zpl`
3. 打印类型选择: **Label (ZPL)**
4. 点击"上传并打印"

**预期结果**:
- ✅ 界面显示"上传成功"
- ✅ 控制台输出: `[OK] 网络打印成功` 或 `[OK] Windows打印成功`
- ✅ 打印机输出英文标签

**如果失败**: 检查打印机连接和驱动

---

#### 测试3.2: 简单中文 (JSON数据)

1. 点击"📝 JSON数据打印"标签页
2. 点击"TSPL标签示例"下方的"**加载示例**"按钮（第一个示例）
   - 或手动复制 `data/test_samples/zd888_chinese_simple.json` 的内容
3. 点击"发送打印"

**关键观察点** (控制台输出):
```
生成标签: 测试标签
  使用字体: msyh.ttc
  文本转换成功: '测试标签' -> 120x45px (...)
  文本转换成功: '产品：元件A' -> 180x40px (...)
[OK] Windows打印成功: ZDesigner ZD888-203dpi ZPL
```

**预期结果**:
- ✅ 界面显示"打印成功"
- ✅ 控制台显示"文本转换成功"（表示中文已转图像）
- ✅ 打印机输出标签，中文清晰可见

**如果中文是空白或方块**:
- 检查控制台是否有"使用字体: msyh.ttc"
- 确认已安装: `pip install Pillow`
- 运行诊断: `python scripts/diagnose_encoding.py`

---

#### 测试3.3: 中英文混合 (JSON数据)

1. 在"📝 JSON数据打印"标签页
2. 复制以下内容到输入框:

```json
{
  "print_type": "label",
  "title": "Product 产品",
  "fields": [
    {"label": "Name", "value": "Component-A", "font_size": 25},
    {"label": "名称", "value": "电子元件", "font_size": 25}
  ],
  "barcode": "TEST001"
}
```

3. 点击"发送打印"

**预期结果**:
- ✅ 英文和中文都能正常显示
- ✅ 条形码正常

---

#### 测试3.4: 直接ZPL代码 (包含中文)

1. 在"📝 JSON数据打印"标签页
2. 输入以下内容:

```json
{
  "print_type": "label",
  "zpl_code": "^XA^FO50,50^A0N,40,40^FD你好世界^FS^FO50,120^A0N,30,30^FDHello World^FS^XZ"
}
```

3. 点击"发送打印"

**关键观察点** (控制台):
```
[OK] JSON中的ZPL代码，中文已自动转换为图像
```

**预期结果**:
- ✅ "你好世界" 正常显示（已被自动转换为图像）
- ✅ "Hello World" 正常显示

---

### 第四步: 测试得力打印机 (ESC/POS)

#### 测试4.1: 中文小票（结构化）

1. 点击"📝 JSON数据打印"标签页
2. 点击"结构化小票示例"的"加载示例"按钮
3. 点击"发送打印"

**预期结果**:
- ✅ 中文标题和商品名正常显示
- ✅ 数字和金额正确
- ✅ 使用GB2312编码，无乱码

---

#### 测试4.2: 中文小票（原始文本）

1. 在"📝 JSON数据打印"标签页
2. 输入:

```json
{
  "print_type": "escpos",
  "raw_text": "测试打印\n商品A  15.00\n商品B  30.00\n总计:  45.00\n谢谢!\n\n\n",
  "encoding": "gb2312"
}
```

3. 点击"发送打印"

**预期结果**:
- ✅ 所有中文正常显示
- ✅ 无乱码

---

## 完整测试检查表

### ✅ 斑马打印机 (ZD888) - ZPL

| 测试项 | 方法 | 文件/数据 | 预期 |
|--------|------|-----------|------|
| 纯英文 | 文件上传 | `zd888_english.zpl` | 英文正常 |
| 简单中文 | JSON | `zd888_chinese_simple.json` | 中文显示（图像） |
| 中英混合 | JSON | `zd888_chinese_mixed.json` | 两种语言都正常 |
| 直接ZPL+中文 | JSON | 包含中文的zpl_code | 自动转换中文 |

### ✅ 得力打印机 - ESC/POS

| 测试项 | 方法 | 文件/数据 | 预期 |
|--------|------|-----------|------|
| 结构化小票 | JSON | 页面示例 | 中文正常(GB2312) |
| 原始文本 | JSON | `escpos_raw_text.json` | 中文正常(GB2312) |

---

## 控制台日志关键信息

### 正常的斑马打印机日志应该包含:

```
[文件上传]
  ZPL代码不包含中文，无需转换
  [OK] Windows打印成功: ZDesigner ZD888-203dpi ZPL

[JSON中文打印]
  生成标签: 测试标签
    使用字体: msyh.ttc
    文本转换成功: '测试标签' -> 120x45px (675 bytes)
  [OK] Windows打印成功: ZDesigner ZD888-203dpi ZPL

[直接ZPL代码含中文]
  检测到ZPL代码包含中文，开始转换...
    转换中文文本: 你好世界
    [OK] 成功转换 1 处中文文本为图像
  [OK] JSON中的ZPL代码，中文已自动转换为图像
  [OK] Windows打印成功: ZDesigner ZD888-203dpi ZPL
```

### 正常的得力打印机日志应该包含:

```
  [OK] ESC/POS网络打印成功: 192.168.1.100:9100
```

---

## 故障排查

### 问题1: Web界面无法访问

**检查**:
```bash
# 查看是否启动
netstat -an | findstr 5000

# 查看防火墙
# Windows设置 -> 防火墙 -> 允许应用通过防火墙
```

### 问题2: 上传成功但不打印

**检查控制台输出**:
- 是否有错误信息？
- 打印机是否找到？
- 是否显示"打印成功"？

**解决方法**:
```bash
# 查看完整日志
查看日志.bat

# 或直接查看
Get-Content data/logs/mqtt_client_*.log -Tail 50 -Encoding UTF8
```

### 问题3: 中文转换失败

**检查**:
```bash
# 运行诊断
python scripts/diagnose_encoding.py

# 应该看到:
# [OK] Pillow已安装
# [OK] 找到 3 个可用字体
```

**如果失败**:
```bash
pip install Pillow
```

### 问题4: JSON解析错误

**常见原因**:
- JSON格式错误（缺少引号、逗号等）
- 编码不是UTF-8

**验证JSON**:
```bash
# Windows
Get-Content data/test_samples/zd888_chinese_simple.json | python -m json.tool

# 或在线工具
# https://jsonlint.com/
```

---

## 自动化测试脚本

我已经创建了自动化测试脚本，可以批量验证：

```bash
python tests/test_chinese_printing.py
```

选择 `3` (两者都测试)，会自动测试所有场景。

---

## 测试记录表

### 斑马打印机 (ZD888)

| 测试 | 方法 | 结果 | 备注 |
|------|------|------|------|
| 纯英文 | 文件上传 | ☐ 通过 ☐ 失败 | |
| 简单中文 | JSON | ☐ 通过 ☐ 失败 | 中文是否清晰？ |
| 中英混合 | JSON | ☐ 通过 ☐ 失败 | |
| 直接ZPL | JSON | ☐ 通过 ☐ 失败 | |

### 得力打印机 (ESC/POS)

| 测试 | 方法 | 结果 | 备注 |
|------|------|------|------|
| 结构化小票 | JSON | ☐ 通过 ☐ 失败 | |
| 原始文本 | JSON | ☐ 通过 ☐ 失败 | |

---

## 成功标准

### ✅ 全部通过表示:
1. Web应用正常运行
2. 打印机正确配置
3. 中文自动转换功能工作
4. 编码处理正确
5. 打印机驱动正常

### ❌ 如果失败:
1. 记录控制台完整输出
2. 记录浏览器F12开发者工具的错误
3. 提供失败的测试项和现象
4. 运行诊断工具获取详细信息

---

## 下一步

完成测试后：
1. ✅ 记录结果
2. ✅ 如果全部通过，可以开始正式使用
3. ❌ 如果有失败，根据故障排查步骤处理

---

## 快速命令参考

```bash
# 启动Web服务
python web_app.py

# 查看日志
查看日志.bat

# 诊断编码问题
python scripts/diagnose_encoding.py

# 测试打印机
python tests/test_chinese_printing.py

# 测试ZD888
python tests/test_zd888_chinese.py
```

---

**准备好了！现在可以启动Web服务并开始测试了！** 🚀

