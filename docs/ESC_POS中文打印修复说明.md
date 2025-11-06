# ESC/POS中文打印修复说明

## 问题描述

在使用ESC/POS打印机打印中文内容时，出现中文乱码或显示不正确的问题。

## 问题原因

原代码在处理原始文本（`raw_text`）时，使用了 `codecs.decode(raw_text, 'unicode_escape')` 来处理转义字符，但这会导致中文字符被错误处理：

```python
# 错误的处理方式
raw_text = codecs.decode(raw_text, 'unicode_escape')  # 这会破坏中文字符
```

**原因分析**：
- JSON解析器在读取JSON文件时，已经自动处理了 `\n`、`\t` 等转义字符
- 再次使用 `unicode_escape` 解码会将中文字符错误地解释为转义序列
- 导致中文字符乱码或丢失

## 修复方案

### 1. 移除错误的二次解码

直接使用JSON解析后的原始文本，不需要再次处理转义字符：

```python
# 正确的处理方式
raw_text = receipt_data.get('raw_text', '')
# JSON解析器已经处理了转义字符，直接使用即可
```

### 2. 优化编码处理

改进编码错误处理，使用 `errors='ignore'` 而不是 `errors='replace'`：

```python
# 使用 gb2312/gbk 编码（最适合中文ESC/POS打印机）
text_bytes = raw_text.encode(encoding, errors='ignore')
```

### 3. 添加调试信息

增加详细的调试输出，便于排查问题：

```python
print(f"  原始文本长度: {len(raw_text)} 字符")
print(f"  原始文本预览: {raw_text[:100]}...")
print(f"  ✓ 使用编码: {encoding}")
print(f"  ✓ 编码后字节数: {len(text_bytes)}")
```

## 修复后的代码

修改文件：`src/core/escpos_printer.py`

```python
# 如果包含 raw_text 字段，直接打印原始文本
if 'raw_text' in receipt_data:
    raw_text = receipt_data.get('raw_text', '')
    encoding = receipt_data.get('encoding', 'gb2312')
    
    # 注意：JSON解析器已经处理了 \n, \t 等转义字符
    # 不需要再次解码，否则会破坏中文字符
    # 直接使用原始文本即可
    
    # 生成ESC/POS指令
    commands = bytearray()
    
    # 1. 初始化打印机
    commands.extend(self.CMD_INIT)
    
    # 2. 设置字符集为简体中文
    commands.extend(b'\x1B\x74\x0E')  # ESC t 14 (GB2312)
    
    # 3. 将文本转换为字节
    text_bytes = raw_text.encode(encoding, errors='ignore')
    commands.extend(text_bytes)
    
    # 4. 添加换行
    commands.extend(self.LF * 2)
    
    # 发送到打印机
    return self.send_commands(bytes(commands))
```

## 使用方法

### JSON格式

```json
{
  "print_type": "escpos",
  "raw_text": "SIZE 60 mm, 40 mm\nTEXT 20,10,\"TSS24.BF2\",0,1,1,\"容器类型\"\nTEXT 240,60,\"TSS24.BF2\",0,1,2,\"二次库区托盘\"\nTEXT 240,120,\"TSS24.BF2\",0,1,2,\"编号:ECKQ\"\nPRINT 1\n",
  "encoding": "gb2312"
}
```

**注意事项**：
- `\n` 在JSON中表示换行符，会被JSON解析器自动处理
- 中文内容可以直接写在JSON中，不需要特殊处理
- `encoding` 推荐使用 `gb2312` 或 `gbk`（最适合中文ESC/POS打印机）

### 测试示例

#### 示例1：ZPL命令（包含中文）

```json
{
  "print_type": "escpos",
  "raw_text": "SIZE 60 mm, 40 mm\nGAP 1 mm, 0 mm\nCLS\nTEXT 20,10,\"TSS24.BF2\",0,1,1,\"容器类型\"\nQRCODE 20,60,L,10,A,0,M2,S6,\"ECKQ\"\nTEXT 240,60,\"TSS24.BF2\",0,1,2,\"二次库区托盘\"\nTEXT 240,120,\"TSS24.BF2\",0,1,2,\"编号:ECKQ\"\nPRINT 1\n",
  "encoding": "gb2312"
}
```

#### 示例2：简单中文小票

```json
{
  "print_type": "escpos",
  "raw_text": "测试打印\n商品A  15.00\n商品B  30.00\n总计:  45.00\n谢谢!\n\n\n",
  "encoding": "gb2312"
}
```

#### 示例3：中英文混合

```json
{
  "print_type": "escpos",
  "raw_text": "Receipt 销售小票\n--------------------------------\nProduct A   x2   ¥15.50\nProduct B   x1   ¥30.00\n--------------------------------\nTotal 总计:      ¥61.00\nThank you! 谢谢惠顾!\n\n",
  "encoding": "gb2312"
}
```

## 测试

运行测试脚本验证修复：

```bash
# Windows
python tests\test_escpos_chinese_fix.py

# Linux
python3 tests/test_escpos_chinese_fix.py
```

## 技术细节

### ESC/POS字符集设置

```
ESC t n - 选择字符代码表
```

常用字符集：
- `n=0` (0x00) - ASCII
- `n=3` (0x03) - Windows-1252
- `n=14` (0x0E) - **GB2312（简体中文）**← 推荐
- `n=15` (0x0F) - Big5（繁体中文）

### 编码选择建议

| 编码 | 适用场景 | 优先级 |
|------|---------|--------|
| gb2312 | 简体中文ESC/POS打印机 | ⭐⭐⭐⭐⭐ 最推荐 |
| gbk | 扩展简体中文字符集 | ⭐⭐⭐⭐ |
| gb18030 | 完整中文字符集 | ⭐⭐⭐ |
| utf-8 | 通用编码（某些打印机不支持）| ⭐⭐ |

### JSON转义字符说明

在JSON中：
- `\n` → 换行符（Line Feed）
- `\t` → 制表符（Tab）
- `\"` → 双引号
- `\\` → 反斜杠
- `\r` → 回车符（Carriage Return）

这些转义字符在JSON解析时会被**自动处理**，代码中不需要再次解码。

## 相关文件

- 修复文件：`src/core/escpos_printer.py`
- 测试脚本：`tests/test_escpos_chinese_fix.py`
- 示例文件：
  - `data/test_samples/escpos_raw_text.json`
  - `data/test_samples/escpos_chinese.json`

## 更新日期

2025-11-06

## 参考资料

- [ESC/POS命令参考](https://reference.epson-biz.com/modules/ref_escpos/)
- [GB2312字符集标准](https://zh.wikipedia.org/wiki/GB_2312)

