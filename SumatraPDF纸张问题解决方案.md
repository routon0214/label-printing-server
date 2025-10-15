# SumatraPDF 纸张问题解决方案

## 问题分析

**现象**: 在没有安装 SumatraPDF 时打印正常，安装后出现"没有匹配到对应的纸张"错误

**原因**: 
- SumatraPDF 对纸张大小匹配要求非常严格
- 备用打印方案（Adobe Reader、Windows默认）更宽松，会自动适应

## 快速解决方案

### 方案1：临时禁用 SumatraPDF ⭐ 最简单

**操作**:
```
双击运行: 临时禁用SumatraPDF.bat
```

**原理**:
- 重命名 `SumatraPDF.exe` 为 `SumatraPDF.exe.disabled`
- 程序检测不到 SumatraPDF，自动使用备用方案
- 备用方案打印正常

**恢复**:
```
双击运行: 恢复SumatraPDF.bat
```

---

### 方案2：调整打印机设置

**KONICA 打印机设置**:

1. 打开打印首选项
   ```
   控制面板 → 设备和打印机 
   → KONICA MINOLTA Universal PCL
   → 右键 → 打印首选项
   ```

2. 设置以下选项:
   - ✅ **纸张大小**: A4 或 Letter
   - ✅ **缩放**: 适应纸张大小
   - ✅ **纸张处理**: 自动选择纸张来源
   - ✅ **高级** → **纸张/输出** → **纸张不匹配时继续**

3. 保存并测试

---

### 方案3：使用增强的自动回退

**已实现**: 代码已添加自动回退机制

当 SumatraPDF 打印失败时：
1. 先尝试指定打印机
2. 失败后尝试默认打印机
3. 再失败则自动尝试 Adobe Reader
4. 最后尝试 Windows 默认打印

**测试**:
```bash
python tests\test_auto_print.py
```

日志会显示:
```
使用SumatraPDF静默打印
⚠ SumatraPDF返回错误码: 1
  尝试回退方案：使用默认打印机...
  SumatraPDF 打印失败，尝试其他方案...
使用Adobe Reader静默打印...
✓ Adobe Reader静默打印已提交
```

---

## 对比测试

### 测试备用方案
```bash
python tests\test_without_sumatra.py
```

这会模拟禁用 SumatraPDF，测试备用方案是否正常。

---

## 长期解决方案

### 选项A：配置打印机正确的纸张设置

**推荐**: 这是最彻底的解决方案

1. 确保打印机驱动最新
2. 在打印首选项中:
   - 设置默认纸张: A4
   - 启用自动缩放
   - 禁用严格纸张检查

### 选项B：使用更宽松的PDF打印工具

不使用 SumatraPDF，而是：
- Adobe Acrobat Reader DC (更宽松)
- Windows 默认打印 (最宽松)

### 选项C：文档标准化

确保所有 PDF 文档：
- 使用标准纸张大小 (A4/Letter)
- 包含正确的页面设置
- 没有特殊的打印限制

---

## 检查当前状态

### 检查 SumatraPDF 是否启用
```bash
dir C:\Users\admin\AppData\Local\SumatraPDF\
```

**结果**:
- `SumatraPDF.exe` → 已启用
- `SumatraPDF.exe.disabled` → 已禁用

### 检查打印机设置
```bash
python tests\diagnose_paper_issue.py
```

### 测试打印
```bash
# 测试所有格式
python tests\test_auto_print.py

# 只测试 PDF
python tests\diagnose_pdf_print.py
```

---

## 决策流程图

```
是否需要 SumatraPDF 的高性能？
│
├─ 是 → 调整打印机设置（方案2）
│       ├─ 成功 → 完成
│       └─ 失败 → 临时禁用（方案1）
│
└─ 否 → 直接禁用（方案1）
        └─ 使用备用方案
```

---

## 推荐配置

### 情况1：需要高性能批量打印
- 保留 SumatraPDF
- 调整打印机设置启用自动适应
- 标准化文档格式

### 情况2：偶尔打印，追求稳定性
- 禁用 SumatraPDF
- 使用 Adobe Reader 或 Windows 默认
- 牺牲一点性能换取稳定性

### 情况3：混合环境
- 保留 SumatraPDF
- 启用自动回退（已实现）
- 失败时自动使用备用方案

---

## 常见问题

### Q: 禁用 SumatraPDF 后打印会变慢吗？
A: 会稍慢一些，但对于普通打印任务影响不大。批量打印可能会明显变慢。

### Q: 备用方案是什么？
A: 依次尝试：Adobe Reader → Windows 默认打印 → win32print RAW模式

### Q: 如何永久解决？
A: 调整打印机驱动设置，启用"适应纸张大小"和"纸张不匹配时继续"

### Q: 会影响标签打印吗？
A: 不会。标签打印使用 ZT411，与 SumatraPDF 无关。

---

## 相关命令

```bash
# 临时禁用 SumatraPDF
临时禁用SumatraPDF.bat

# 恢复 SumatraPDF
恢复SumatraPDF.bat

# 测试禁用效果
python tests\test_without_sumatra.py

# 诊断纸张问题
python tests\diagnose_paper_issue.py

# 完整测试
python tests\test_auto_print.py
```

---

## 总结

| 方案 | 优点 | 缺点 | 适用场景 |
|-----|------|------|---------|
| 禁用 SumatraPDF | 立即见效、最简单 | 性能稍慢 | 临时快速修复 |
| 调整打印机设置 | 彻底解决、性能好 | 需要权限、较复杂 | 长期使用 |
| 自动回退 | 无需操作、自动 | 首次打印会慢 | 生产环境 |

**推荐**: 先使用方案1临时解决，然后逐步实施方案2长期解决。

---

## 立即行动

1. **立即测试**: 运行 `临时禁用SumatraPDF.bat`
2. **验证效果**: 运行 `python tests\test_auto_print.py`
3. **如果成功**: 考虑调整打印机设置（长期方案）
4. **如果失败**: 运行完整诊断 `python tests\diagnose_paper_issue.py`

