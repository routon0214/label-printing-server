# SumatraPDF 静默打印配置说明

## 概述

本系统支持使用 SumatraPDF 进行 PDF 文档的静默打印。SumatraPDF 是一个轻量级、免费的 PDF 阅读器，支持完全静默打印模式。

## 安装位置

系统会自动检测以下路径的 SumatraPDF 安装：

1. `C:\Program Files\SumatraPDF\SumatraPDF.exe`（全局安装）
2. `C:\Program Files (x86)\SumatraPDF\SumatraPDF.exe`（32位全局安装）
3. `C:\Users\{用户名}\AppData\Local\SumatraPDF\SumatraPDF.exe`（用户本地安装）⭐
4. `C:\Users\{用户名}\AppData\Local\Programs\SumatraPDF\SumatraPDF.exe`（用户程序目录）

**注意**：最新版本的 SumatraPDF 安装器默认会安装到用户本地目录（路径3），程序已支持这种安装方式。

## 下载和安装

### 方法1：使用安装器（推荐）

1. 访问官网: https://www.sumatrapdfreader.org/
2. 下载最新版本的安装器
3. 运行安装器，按照默认选项安装即可
4. 安装完成后，程序会自动检测到

### 方法2：使用便携版

1. 下载 SumatraPDF 便携版
2. 解压到以下任意位置：
   - `C:\Program Files\SumatraPDF\`
   - `C:\Users\{你的用户名}\AppData\Local\SumatraPDF\`
3. 确保文件名为 `SumatraPDF.exe`

## 验证安装

运行检查脚本：

```bash
python tests/check_sumatra_pdf.py
```

成功的输出示例：

```
✓ 找到: C:\Users\admin\AppData\Local\SumatraPDF\SumatraPDF.exe
       大小: 8,246,744 字节 (7.86 MB)

✓ PDF 静默打印功能已就绪
```

## 测试打印

运行打印测试脚本：

```bash
python tests/test_sumatra_print.py
```

这会执行一次真实的打印测试，验证 SumatraPDF 是否能正常工作。

## 工作原理

当接收到 PDF 打印任务时，系统会：

1. 自动检测 SumatraPDF 安装位置
2. 使用以下命令进行静默打印：
   ```
   SumatraPDF.exe -print-to "打印机名称" -silent "文件路径"
   ```
3. 等待打印任务完成

## 命令行参数说明

- `-print-to <打印机名称>`: 指定目标打印机
- `-silent`: 静默模式，不显示任何窗口
- 文件路径: 要打印的 PDF 文件

## 支持的文件格式

SumatraPDF 支持以下格式的静默打印：

- PDF (.pdf)
- XPS (.xps, .oxps)
- DjVu (.djvu)
- CBZ/CBR (.cbz, .cbr) - 漫画书格式
- EPUB (.epub) - 电子书

## 常见问题

### Q: 为什么找不到 SumatraPDF？

**A**: 请确保：
1. SumatraPDF 已正确安装
2. 安装路径在支持的列表中
3. 文件名为 `SumatraPDF.exe`（大小写敏感）

运行 `python tests/check_sumatra_pdf.py` 查看详细检测信息。

### Q: 打印失败，返回错误码

**A**: 可能的原因：
1. 打印机名称不正确
2. 打印机离线或不可用
3. PDF 文件损坏
4. 打印机驱动程序问题

查看日志中的详细错误信息。

### Q: 可以打印到网络打印机吗？

**A**: 可以！只要在 Windows 系统中正确配置了网络打印机，SumatraPDF 就能识别并打印。

### Q: 需要管理员权限吗？

**A**: 不需要。用户本地安装的 SumatraPDF 可以正常工作。

## 备选方案

如果 SumatraPDF 不可用，系统会自动尝试以下备选方案：

1. Adobe Acrobat Reader DC
2. Notepad（仅文本文件）
3. win32print RAW 模式（仅文本和 ZPL）

## 性能对比

| 工具 | 速度 | 静默度 | 推荐度 |
|------|------|--------|--------|
| SumatraPDF | ⭐⭐⭐⭐⭐ | 完全静默 | ⭐⭐⭐⭐⭐ 推荐 |
| Adobe Reader | ⭐⭐⭐ | 可能弹窗 | ⭐⭐⭐ |
| Windows 默认 | ⭐⭐ | 可能弹窗 | ⭐⭐ |

## 更新日志

### v2.0 (2025-10-15)
- ✅ 支持用户本地安装路径检测
- ✅ 添加详细的路径检查日志
- ✅ 改进错误信息显示
- ✅ 添加命令执行日志

### v1.0
- 初始版本
- 支持基本的 SumatraPDF 检测和打印

