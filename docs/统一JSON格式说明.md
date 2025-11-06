# 统一JSON格式说明

## 概述

为了简化数据处理和提高代码可维护性，所有打印数据现在使用**统一的JSON格式**。

## 统一格式定义

```json
{
  "print_type": "label | escpos",
  "format": "zpl | structured | raw",
  "content": "内容（字符串或对象）",
  "encoding": "gb2312"  // 可选，仅format为raw时使用
}
```

### 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `print_type` | string | ✅ | 打印机类型：`label`（标签）或 `escpos`（小票） |
| `format` | string | ✅ | 数据格式：`zpl`、`structured`、`raw` |
| `content` | string/object | ✅ | 打印内容，类型取决于format |
| `encoding` | string | ❌ | 编码方式（仅raw格式），默认`gb2312` |

## 格式类型详解

### 1. ZPL格式 (format: "zpl")

**适用于**：标签打印机，直接使用ZPL命令

**content类型**：字符串

**示例**：

```json
{
  "print_type": "label",
  "format": "zpl",
  "content": "^XA^FO50,50^A0N,40,40^FD你好世界^FS^FO50,120^A0N,30,30^FDHello^FS^XZ"
}
```

**特点**：
- 直接发送ZPL命令到打印机
- 支持中文（自动转换为图像）
- 最灵活，可以完全控制打印布局

### 2. 结构化格式 (format: "structured")

**适用于**：标签和小票打印，由系统自动生成打印命令

**content类型**：对象

#### 2.1 标签打印 (print_type: "label")

```json
{
  "print_type": "label",
  "format": "structured",
  "content": {
    "title": "产品标签",
    "fields": [
      {"label": "名称", "value": "电子元件", "font_size": 28},
      {"label": "编号", "value": "SN-001", "font_size": 25}
    ],
    "barcode": "SN001",
    "qrcode": "SN001"
  }
}
```

**content字段**：
- `title`: 标题文本
- `fields`: 字段数组，每个字段包含：
  - `label`: 字段标签
  - `value`: 字段值
  - `font_size`: 字体大小
- `barcode`: 条形码内容（可选）
- `qrcode`: 二维码内容（可选）

#### 2.2 小票打印 (print_type: "escpos")

```json
{
  "print_type": "escpos",
  "format": "structured",
  "content": {
    "title": "销售小票",
    "items": [
      {"name": "商品A", "qty": 2, "price": 15.50},
      {"name": "商品B", "qty": 1, "price": 30.00}
    ],
    "total": 61.00,
    "footer": "谢谢惠顾!"
  }
}
```

**content字段**：
- `title`: 小票标题
- `items`: 商品列表数组，每个商品包含：
  - `name`: 商品名称
  - `qty`: 数量
  - `price`: 单价
- `total`: 总计
- `footer`: 页脚文本（可选）

**特点**：
- 简单易用，无需了解底层命令
- 系统自动处理布局和格式
- 适合标准化的打印需求

### 3. 原始格式 (format: "raw")

**适用于**：ESC/POS小票打印机，发送原始文本

**content类型**：字符串

**示例**：

```json
{
  "print_type": "escpos",
  "format": "raw",
  "content": "SIZE 60 mm, 40 mm\nGAP 1 mm, 0 mm\nCLS\nTEXT 20,10,\"TSS24.BF2\",0,1,1,\"容器类型\"\nTEXT 240,60,\"TSS24.BF2\",0,1,2,\"二次库区托盘\"\nPRINT 1\n",
  "encoding": "gb2312"
}
```

**特点**：
- 发送原始文本到打印机
- 支持任意文本内容（包括ZPL命令、TSC命令等）
- 需要指定编码（推荐`gb2312`或`gbk`）
- 最灵活，但需要了解打印机命令

## 向后兼容

系统**完全向后兼容旧格式**，会自动转换：

| 旧格式 | 自动转换为 |
|--------|-----------|
| `{"zpl_code": "..."}` | `{"format": "zpl", "content": "..."}` |
| `{"raw_text": "..."}` | `{"format": "raw", "content": "..."}` |
| `{"fields": [...]}` | `{"format": "structured", "content": {...}}` |

**示例**：

```json
// 旧格式（仍然支持）
{
  "print_type": "label",
  "zpl_code": "^XA^FO50,50^A0N,40,40^FDTest^FS^XZ"
}

// 自动转换为新格式
{
  "print_type": "label",
  "format": "zpl",
  "content": "^XA^FO50,50^A0N,40,40^FDTest^FS^XZ"
}
```

## 使用场景对照表

| 场景 | 推荐格式 | print_type | format |
|------|---------|------------|---------|
| 简单标签打印 | 结构化 | label | structured |
| 复杂标签布局 | ZPL | label | zpl |
| 标准小票打印 | 结构化 | escpos | structured |
| 原始文本打印 | 原始 | escpos | raw |
| ZPL命令文本 | 原始 | escpos | raw |

## 完整示例

### 示例1：简单中文标签

```json
{
  "print_type": "label",
  "format": "structured",
  "content": {
    "title": "测试标签",
    "fields": [
      {"label": "产品", "value": "元件A", "font_size": 25},
      {"label": "编号", "value": "NO-001", "font_size": 22}
    ],
    "barcode": "NO001"
  }
}
```

### 示例2：中英文混合标签

```json
{
  "print_type": "label",
  "format": "structured",
  "content": {
    "title": "Product 产品标签",
    "fields": [
      {"label": "Name", "value": "Component-A", "font_size": 28},
      {"label": "名称", "value": "电子元件", "font_size": 28},
      {"label": "Serial", "value": "SN-2025-001", "font_size": 25}
    ],
    "barcode": "SN2025001",
    "qrcode": "SN2025001"
  }
}
```

### 示例3：ZPL代码含中文

```json
{
  "print_type": "label",
  "format": "zpl",
  "content": "^XA^FO50,50^A0N,40,40^FD你好世界^FS^FO50,120^A0N,30,30^FDHello World^FS^XZ"
}
```

### 示例4：结构化小票

```json
{
  "print_type": "escpos",
  "format": "structured",
  "content": {
    "title": "销售小票",
    "items": [
      {"name": "商品A", "qty": 2, "price": 15.50},
      {"name": "商品B", "qty": 1, "price": 30.00}
    ],
    "total": 61.00,
    "footer": "谢谢惠顾 Thank you!"
  }
}
```

### 示例5：原始文本小票

```json
{
  "print_type": "escpos",
  "format": "raw",
  "content": "SIZE 60 mm, 40 mm\nGAP 1 mm, 0 mm\nCLS\nTEXT 20,10,\"TSS24.BF2\",0,1,1,\"容器类型\"\nTEXT 240,60,\"TSS24.BF2\",0,1,2,\"二次库区托盘\"\nPRINT 1\n",
  "encoding": "gb2312"
}
```

## API调用

### Web界面

1. 在"JSON数据打印"区域输入统一格式的JSON
2. 点击"发送打印"按钮
3. 系统自动识别格式并处理

### REST API

```bash
curl -X POST http://127.0.0.1:5000/api/print/raw \
  -H "Content-Type: application/json" \
  -u admin:admin123 \
  -d '{
    "print_type": "label",
    "format": "zpl",
    "content": "^XA^FO50,50^A0N,40,40^FDTest^FS^XZ"
  }'
```

### MQTT消息

```json
{
  "print_type": "label",
  "format": "structured",
  "content": {
    "title": "产品标签",
    "fields": [
      {"label": "名称", "value": "测试", "font_size": 28}
    ]
  }
}
```

## 优势

### 1. 统一性
- ✅ 所有打印数据使用相同的结构
- ✅ 一致的字段命名
- ✅ 易于理解和使用

### 2. 可扩展性
- ✅ 新增打印格式只需添加新的`format`类型
- ✅ 不影响现有代码
- ✅ 保持向后兼容

### 3. 可维护性
- ✅ 减少重复代码
- ✅ 统一的数据验证
- ✅ 更容易调试

### 4. 向后兼容
- ✅ 旧格式自动转换
- ✅ 不影响现有系统
- ✅ 平滑迁移

## 技术实现

### 数据标准化函数

```python
def normalize_print_data(data):
    """将打印数据标准化为统一格式"""
    
    # 如果已经是新格式，直接返回
    if 'format' in data and 'content' in data:
        return data
    
    # 向后兼容：自动转换旧格式
    if 'zpl_code' in data:
        return {
            'print_type': data.get('print_type', 'label'),
            'format': 'zpl',
            'content': data['zpl_code']
        }
    # ... 更多转换逻辑
```

### 示例文件

所有示例文件已更新为统一格式：
- `data/test_samples/label_chinese_simple.json`
- `data/test_samples/label_chinese_mixed.json`
- `data/test_samples/label_zpl_chinese.json`
- `data/test_samples/label_zpl_english.json`
- `data/test_samples/escpos_structured.json`
- `data/test_samples/escpos_raw.json`

## 迁移指南

### 从旧格式迁移

**不需要任何修改！** 系统自动兼容旧格式。

如果要使用新格式，按以下方式修改：

#### 1. ZPL打印

```json
// 旧格式
{"print_type": "label", "zpl_code": "..."}

// 新格式（推荐）
{"print_type": "label", "format": "zpl", "content": "..."}
```

#### 2. 结构化标签

```json
// 旧格式
{"print_type": "label", "title": "...", "fields": [...]}

// 新格式（推荐）
{"print_type": "label", "format": "structured", "content": {"title": "...", "fields": [...]}}
```

#### 3. 原始文本

```json
// 旧格式
{"print_type": "escpos", "raw_text": "...", "encoding": "gb2312"}

// 新格式（推荐）
{"print_type": "escpos", "format": "raw", "content": "...", "encoding": "gb2312"}
```

## 相关文档

- [示例数据管理说明.md](示例数据管理说明.md) - 示例文件管理
- [ESC_POS中文打印修复说明.md](ESC_POS中文打印修复说明.md) - ESC/POS打印
- [WEB服务使用说明.md](WEB服务使用说明.md) - Web接口使用

## 更新日期

2025-11-06

