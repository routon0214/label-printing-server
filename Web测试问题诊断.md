# Web测试问题诊断

## 问题现象

- ✅ 测试脚本 `test_zd888_chinese.py` **能正常打印**
- ❌ Web界面打印 **不行**
- 🔸 打印机灯**闪烁一下** - 说明接收到数据但无法处理

## 可能原因

### 原因1: ZPL格式问题 (最可能)

**现象**: 打印机灯闪烁表示收到数据但ZPL格式不正确

**可能情况**:
- ZPL代码不完整（缺少^XA或^XZ）
- 图像数据格式错误
- 特殊字符编码问题

**诊断方法**:
```bash
# 运行对比测试
python 对比测试Web和脚本.py

# 步骤:
# 1. 选择 1 - 测试直接打印（应该成功）
# 2. 选择 2 - 模拟Web流程（看是否成功）
# 3. 选择 3 - 对比文件（找出差异）
```

### 原因2: Web传输过程中数据损坏

**现象**: Web发送的ZPL与本地生成的不同

**诊断方法**:
1. 启动Web服务: `python web_app.py`
2. 通过Web界面测试
3. 查看控制台输出的调试信息:
```
[DEBUG] ZPL已保存到: data/debug_web_json_*.zpl
[DEBUG] ZPL长度: XXXX 字符
[DEBUG] ZPL开头: ^XA...
[DEBUG] ZPL结尾: ...^XZ
```
4. 使用对比工具检查:
```bash
python 对比测试Web和脚本.py
# 选择 4 - 检查Web调试文件
```

### 原因3: 打印机内存限制

**现象**: 大的ZPL文件打印机无法处理

**ZD888特点**:
- 桌面型打印机
- 203dpi（较低分辨率）
- 内存相对较小

**解决方法**:
- 减小字体大小
- 减少内容
- 简化标签

---

## 立即诊断步骤

### 步骤1: 启动Web服务（开启调试）

```bash
python web_app.py
```

**观察启动信息**:
```
[OK] 匹配到: ZDesigner ZD888-203dpi ZPL
[OK] 标签打印（专用） -> ZD888
```

### 步骤2: 通过Web测试简单中文

1. 访问: http://127.0.0.1:5000
2. 登录: admin/admin
3. JSON数据打印，输入:

```json
{
  "print_type": "label",
  "title": "测试",
  "fields": [
    {"label": "产品", "value": "元件A", "font_size": 25}
  ]
}
```

4. 点击"发送打印"

### 步骤3: 查看控制台调试输出

**应该看到**:
```
[INFO] 从JSON数据生成ZPL...
生成标签: 测试
  使用字体: msyh.ttc
  文本转换成功: '测试' -> XXxYYpx
  ...
[DEBUG] ZPL已保存到: data/debug_web_json_20251106_HHMMSS.zpl
[DEBUG] ZPL长度: XXXX 字符
[DEBUG] ZPL开头: ^XA^PW800^LL600...
[DEBUG] ZPL结尾: ...^XZ
[OK] Windows打印成功: ZDesigner ZD888-203dpi ZPL
```

**关键检查**:
- ✅ 是否有"使用字体"和"文本转换成功"
- ✅ ZPL开头是否为 `^XA`
- ✅ ZPL结尾是否为 `^XZ`
- ✅ 是否显示"Windows打印成功"

### 步骤4: 对比调试文件

```bash
python 对比测试Web和脚本.py
# 选择 4 - 检查Web调试文件
```

查看Web生成的ZPL:
- 格式是否正确
- 是否完整（有^XA和^XZ）
- 是否包含^GFA图像数据

### 步骤5: 手动测试调试文件

如果Web生成的ZPL文件存在，尝试用测试脚本打印它:

```python
# 在Python交互式环境
from src.core.printer import ZebraPrinter

# 读取Web生成的ZPL
with open('data/debug_web_json_20251106_XXXXXX.zpl', 'r') as f:
    web_zpl = f.read()

# 打印
p = ZebraPrinter(printer_name="ZD888")
p.print_label(web_zpl)
```

**如果这个能打印**:
→ 说明Web生成的ZPL是正确的
→ 问题在Web服务器到打印机的传输

**如果这个也不能打印**:
→ Web生成的ZPL有问题
→ 需要对比ZPL差异

---

## 快速修复建议

### 修复1: 减小ZPL大小

修改 `data/test_samples/zd888_chinese_simple.json`:

```json
{
  "print_type": "label",
  "title": "测试",
  "fields": [
    {"label": "产品", "value": "元件A", "font_size": 20}
  ]
}
```

注意 `font_size` 从25改为20，生成的图像会更小。

### 修复2: 使用最简单的测试

通过Web界面JSON打印，使用超简单数据:

```json
{
  "print_type": "label",
  "zpl_code": "^XA^FO50,50^A0N,40,40^FDTest^FS^XZ"
}
```

**如果这个能打印**:
→ 基础功能正常
→ 逐步增加复杂度

**如果这个也不行**:
→ Web到打印机的通道有问题
→ 检查Web应用代码

### 修复3: 检查ZPL编码

在 `src/core/printer.py` 的 `_print_windows` 方法中:

```python
# 第278行
win32print.WritePrinter(printer_handle, zpl_code.encode('utf-8'))
```

确认使用的是UTF-8编码。

---

## 对比检查表

| 检查项 | 测试脚本 | Web应用 | 状态 |
|--------|----------|---------|------|
| ZPL生成 | ✅ 正常 | ❓ 待确认 | 查看debug文件 |
| 中文转换 | ✅ 正常 | ❓ 待确认 | 查看控制台 |
| 打印发送 | ✅ 正常 | ❌ 失败 | 需诊断 |
| ZPL格式 | ✅ 正确 | ❓ 待确认 | 对比文件 |

---

## 下一步行动

### 立即执行:

1. **启动Web服务**（如果未启动）:
```bash
python web_app.py
```

2. **通过Web测试**并观察控制台输出

3. **运行对比工具**:
```bash
python 对比测试Web和脚本.py
```

4. **提供以下信息**:
   - 控制台的完整调试输出
   - `data/debug_web_*.zpl` 文件的内容预览
   - 对比结果

---

## 调试模式已启用

现在Web应用会：
- ✅ 保存所有发送的ZPL到 `data/debug_web_*.zpl`
- ✅ 显示详细的调试信息
- ✅ 记录ZPL长度和内容预览

**每次Web测试都会生成调试文件，可以用于分析！**

