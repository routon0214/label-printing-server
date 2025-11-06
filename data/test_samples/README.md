# 测试样本文件说明

## 文件清单

### 斑马打印机 (ZD888) 测试文件

#### 1. zd888_english.zpl
**类型**: ZPL文件  
**内容**: 纯英文标签  
**用途**: 验证基础打印功能  
**测试方法**: Web界面文件上传  
**预期**: 英文标签正常打印

#### 2. zd888_chinese_simple.json
**类型**: JSON数据  
**内容**: 简单中文标签（少量文字）  
**用途**: 验证中文图像转换功能  
**测试方法**: Web界面JSON打印  
**预期**: 中文清晰显示

**内容预览**:
```json
{
  "print_type": "label",
  "title": "测试标签",
  "fields": [
    {"label": "产品", "value": "元件A", "font_size": 25},
    {"label": "编号", "value": "NO-001", "font_size": 22}
  ],
  "barcode": "NO001"
}
```

#### 3. zd888_chinese_mixed.json
**类型**: JSON数据  
**内容**: 中英文混合标签  
**用途**: 验证混合语言打印  
**测试方法**: Web界面JSON打印  
**预期**: 中英文都正常显示

**内容预览**:
```json
{
  "print_type": "label",
  "title": "Product 产品标签",
  "fields": [
    {"label": "Name", "value": "Component-A", "font_size": 28},
    {"label": "名称", "value": "电子元件", "font_size": 28},
    ...
  ]
}
```

---

### 得力打印机 (ESC/POS) 测试文件

#### 4. escpos_chinese.json
**类型**: JSON数据  
**内容**: 中文销售小票（结构化格式）  
**用途**: 验证ESC/POS中文打印  
**测试方法**: Web界面JSON打印  
**预期**: 中文无乱码（GB2312编码）

**内容预览**:
```json
{
  "print_type": "escpos",
  "title": "销售小票",
  "items": [
    {"name": "商品A", "qty": 2, "price": 15.50},
    {"name": "Product B", "qty": 1, "price": 30.00}
  ],
  "total": 85.00,
  "footer": "谢谢惠顾 Thank you!"
}
```

#### 5. escpos_raw_text.json
**类型**: JSON数据  
**内容**: 原始文本格式小票  
**用途**: 验证原始文本打印  
**测试方法**: Web界面JSON打印  
**预期**: 中文正常

**内容预览**:
```json
{
  "print_type": "escpos",
  "raw_text": "测试打印 Test Print\n...",
  "encoding": "gb2312"
}
```

---

## 使用方法

### 通过Web界面测试

1. **启动服务**:
```bash
python web_app.py
# 或
启动并测试.bat
```

2. **访问**: http://127.0.0.1:5000

3. **测试ZPL文件**:
   - 文件上传 → 选择 `.zpl` 文件 → 打印类型: Label → 上传并打印

4. **测试JSON数据**:
   - JSON数据打印 → 复制 `.json` 文件内容 → 发送打印

### 通过命令行测试

```bash
# 交互式测试
python tests/test_chinese_printing.py

# ZD888专用测试
python tests/test_zd888_chinese.py
```

---

## 测试顺序建议

### 第一阶段: 基础功能
1. ✅ 纯英文 (`zd888_english.zpl`)
   - 确认打印机连接和驱动正常

### 第二阶段: 中文功能
2. ✅ 简单中文 (`zd888_chinese_simple.json`)
   - 确认中文转图像功能工作
   - **这是最关键的测试**

### 第三阶段: 复杂场景
3. ✅ 中英文混合 (`zd888_chinese_mixed.json`)
4. ✅ 直接ZPL代码（包含中文）

### 第四阶段: ESC/POS
5. ✅ 得力打印机测试

---

## 验证要点

### 斑马打印机中文打印验证

**控制台应该显示**:
```
生成标签: 测试标签
  使用字体: msyh.ttc
  文本转换成功: '测试标签' -> 120x45px (675 bytes)
  文本转换成功: '产品：元件A' -> 180x40px (900 bytes)
```

**关键标志**:
- ✅ "使用字体" - 表示找到中文字体
- ✅ "文本转换成功" - 表示图像生成成功
- ✅ "px" 和 "bytes" - 表示有实际图像数据

**如果没有看到这些**:
→ 中文没有被转换为图像
→ 检查 Pillow 安装: `pip install Pillow`

### 得力打印机中文打印验证

**控制台应该显示**:
```
  发送到ESC/POS打印机...
  使用GB2312编码
  [OK] ESC/POS网络打印成功
```

**关键标志**:
- ✅ "使用GB2312编码" - 正确的中文编码
- ✅ "打印成功" - 数据已发送

---

## 文件位置

```
data/test_samples/
├── zd888_english.zpl              # 纯英文ZPL
├── zd888_chinese_simple.json      # 简单中文JSON
├── zd888_chinese_mixed.json       # 中英混合JSON
├── escpos_chinese.json            # 中文小票（结构化）
├── escpos_raw_text.json           # 中文小票（原始文本）
└── README.md                      # 本文档
```

---

## 故障日志

如果测试失败，请记录：

1. **测试项**: 哪个测试失败了？
2. **现象**: 中文是空白、方块还是乱码？
3. **控制台输出**: 复制完整的控制台输出
4. **浏览器错误**: F12开发者工具中的错误信息

---

## 技术说明

### 中文处理流程

**斑马打印机 (ZPL)**:
```
中文文本 "测试"
    ↓
Pillow渲染为黑白图像
    ↓
转换为十六进制
    ↓
^GFA图像命令
    ↓
发送到打印机
```

**得力打印机 (ESC/POS)**:
```
中文文本 "测试"
    ↓
使用GB2312编码
    ↓
添加ESC t 14命令（设置字符集）
    ↓
发送到打印机
```

---

**所有测试文件已准备就绪！现在可以开始完整测试了！** ✅

