# PDF 打印错误码 1 修复说明

## 问题描述

用户安装了 SumatraPDF 但打印时返回错误码 1：
```
⚠ SumatraPDF返回错误码: 1
```

## 根本原因

**问题1：SumatraPDF 路径检测不完整**
- 用户安装路径：`C:\Users\admin\AppData\Local\SumatraPDF\SumatraPDF.exe`
- 原程序只检查：`C:\Program Files\SumatraPDF\`

**问题2：打印机名称不精确**
- 配置文件中使用简短名称：`"KONICA"`
- SumatraPDF 需要完整名称：`"KONICA MINOLTA Universal PCL"`
- PDF 打印机未使用模糊匹配解析名称

## 修复方案

### 1. 添加用户本地安装路径支持 ✅

**修改文件**：`core/pdf_printer.py`

**添加的路径**：
```python
sumatra_paths = [
    r"C:\Program Files\SumatraPDF\SumatraPDF.exe",
    r"C:\Program Files (x86)\SumatraPDF\SumatraPDF.exe",
    os.path.join(user_profile, r"AppData\Local\SumatraPDF\SumatraPDF.exe"),  # 新增
    os.path.join(user_profile, r"AppData\Local\Programs\SumatraPDF\SumatraPDF.exe"),  # 新增
]
```

**效果**：
```
正在检查 SumatraPDF 路径...
  检查: C:\Program Files\SumatraPDF\SumatraPDF.exe
  检查: C:\Program Files (x86)\SumatraPDF\SumatraPDF.exe
  检查: C:\Users\admin\AppData\Local\SumatraPDF\SumatraPDF.exe
  ✓ 找到: C:\Users\admin\AppData\Local\SumatraPDF\SumatraPDF.exe
```

### 2. 实现打印机名称自动解析 ✅

**修改文件**：`core/pdf_printer.py`

**添加功能**：
```python
def _resolve_printer_name(self, printer_name):
    """解析打印机名称，支持模糊匹配"""
    from utils.fuzzy_match import fuzzy_search_printer
    
    matched_name = fuzzy_search_printer(printer_name)
    if matched_name:
        print(f"PDF打印机名称解析: '{printer_name}' → '{matched_name}'")
        return matched_name
    return printer_name
```

**效果**：
```
PDF打印机名称解析: 'KONICA' → 'KONICA MINOLTA Universal PCL'
```

### 3. 添加 fuzzy_search_printer 函数 ✅

**修改文件**：`utils/fuzzy_match.py`

**新增函数**：
```python
def fuzzy_search_printer(search_pattern):
    """在系统中搜索打印机（自动获取打印机列表）"""
    if system == 'Windows':
        import win32print
        printers = [p[2] for p in win32print.EnumPrinters(2)]
        return find_best_printer(printers, search_pattern)
```

## 测试结果

### 测试1：SumatraPDF 检测 ✅
```bash
python tests/check_sumatra_pdf.py
```
```
✓ 找到: C:\Users\admin\AppData\Local\SumatraPDF\SumatraPDF.exe
       大小: 8,246,744 字节 (7.86 MB)
✓ PDF 静默打印功能已就绪
```

### 测试2：打印机名称解析 ✅
```bash
python tests/test_pdf_printer_fix.py
```
```
✓ 'KONICA' 正确解析为 'KONICA MINOLTA Universal PCL'
✓ SumatraPDF 将使用完整的打印机名称
```

### 测试3：实际打印测试 ✅
```bash
python tests/diagnose_pdf_print.py
```
```
返回码: 0
标准输出:
PrintToDevice: printer: 'KONICA MINOLTA Universal PCL', file: '...'
PrintToDevice: finished ok
Finished printing, exitCode: 0
```

## 配置建议

### 推荐配置（使用简短名称）
```json
{
  "name": "KONICA",
  "types": ["pdf"],
  "_comment": "会自动匹配到 KONICA MINOLTA Universal PCL"
}
```

**优点**：
- 配置简洁
- 自动适配不同的打印机型号
- 支持模糊匹配

### 精确配置（使用完整名称）
```json
{
  "name": "KONICA MINOLTA Universal PCL",
  "types": ["pdf"],
  "_comment": "直接使用完整打印机名称"
}
```

**优点**：
- 无需模糊匹配
- 性能更好
- 更加精确

## SumatraPDF 命令详解

**完整命令**：
```bash
SumatraPDF.exe -print-to "打印机名称" -silent "文件路径"
```

**参数说明**：
- `-print-to "打印机名称"`: 指定目标打印机（需要精确匹配）
- `-silent`: 静默模式，不显示任何窗口
- `文件路径`: 要打印的 PDF 文件

**返回码**：
- `0`: 成功
- `1`: 失败（通常是打印机名称不匹配或文件不存在）

## 错误码说明

| 错误码 | 含义 | 解决方案 |
|--------|------|----------|
| 0 | 成功 | 无需处理 |
| 1 | 打印失败 | 检查打印机名称是否精确匹配 |
| 超时 | 命令超时 | 检查 SumatraPDF 是否正常运行 |

## 诊断工具

### 1. 检查 SumatraPDF 安装
```bash
python tests/check_sumatra_pdf.py
```

### 2. 诊断 PDF 打印问题
```bash
python tests/diagnose_pdf_print.py
```

### 3. 测试打印机名称解析
```bash
python tests/test_pdf_printer_fix.py
```

## 工作流程

```
接收 PDF 打印任务
         ↓
配置名称: "KONICA"
         ↓
模糊匹配解析
         ↓
实际名称: "KONICA MINOLTA Universal PCL"
         ↓
传递给 SumatraPDF
         ↓
SumatraPDF.exe -print-to "KONICA MINOLTA Universal PCL" -silent file.pdf
         ↓
打印成功 (返回码 0)
```

## 总结

✅ **已修复的问题**：
1. SumatraPDF 用户本地安装路径检测
2. 打印机名称自动解析（模糊匹配）
3. 详细的调试日志输出
4. 添加了完整的诊断工具

✅ **现在可以**：
1. 使用简短名称配置打印机
2. 自动检测用户本地安装的 SumatraPDF
3. 完全静默打印 PDF 文档
4. 快速诊断打印问题

## 更新时间

2025-10-15

## 相关文档

- [SumatraPDF 配置说明](./SumatraPDF配置说明.md)
- [配置升级说明](../config/printer_config_example.json)

