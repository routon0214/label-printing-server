# 统一JSON格式设计

## 新的统一格式

```json
{
  "print_type": "label",      // 打印机类型: "label" 或 "escpos"
  "format": "zpl",            // 数据格式: "zpl", "structured", "raw"
  "content": {...}            // 统一的内容字段
}
```

## 格式说明

### 1. 标签打印 (print_type: "label")

#### format: "zpl" - 直接ZPL代码
```json
{
  "print_type": "label",
  "format": "zpl",
  "content": "^XA^FO50,50^A0N,40,40^FD你好世界^FS^XZ"
}
```

#### format: "structured" - 结构化数据（自动生成ZPL）
```json
{
  "print_type": "label",
  "format": "structured",
  "content": {
    "title": "产品标签",
    "fields": [
      {"label": "名称", "value": "电子元件", "font_size": 28}
    ],
    "barcode": "SN001",
    "qrcode": "SN001"
  }
}
```

### 2. 小票打印 (print_type: "escpos")

#### format: "structured" - 结构化数据
```json
{
  "print_type": "escpos",
  "format": "structured",
  "content": {
    "title": "销售小票",
    "items": [
      {"name": "商品A", "qty": 2, "price": 15.50}
    ],
    "total": 61.00,
    "footer": "谢谢惠顾!"
  }
}
```

#### format: "raw" - 原始文本
```json
{
  "print_type": "escpos",
  "format": "raw",
  "content": "测试打印\n商品A  15.00\n总计:  45.00\n",
  "encoding": "gb2312"
}
```

## 兼容性

向后兼容旧格式：
- `zpl_code` → 自动识别为 `format: "zpl"`
- `raw_text` → 自动识别为 `format: "raw"`
- 有 `fields` → 自动识别为 `format: "structured"`

