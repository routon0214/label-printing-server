# TSC打印机使用说明

## 打印机类型识别

您的打印机是 **TSC（台半）品牌标签打印机**，使用 **TSPL（TSC Printer Language）** 命令语言。

**不是** Zebra ZPL 打印机！

## 重要发现

✅ **原始TSPL格式可以正常打印**
- 文件：`data/print_text_original.zpl`
- 包含中文TEXT命令和TSS24.BF2字体
- 可以直接使用，无需转换

❌ **转换后的ZPL格式无法打印**
- 文件：`data/print_text_ready.zpl`  
- 使用ZPL标准命令（^XA, ^FO, ^GFA）
- TSC打印机无法识别

## TSPL vs ZPL 对比

### TSPL (TSC打印机)
```tspl
SIZE 60 mm, 40 mm
GAP 1 mm, 0 mm
DIRECTION 1,0
CLS
TEXT 20,10,"TSS24.BF2",0,1,1,"容器类型"
QRCODE 20,60,L,10,A,0,M2,S6,"ECKQ"
TEXT 240,60,"TSS24.BF2",0,1,2,"二次库区托盘"
PRINT 1
```

**特点**:
- 支持中文字体：TSS24.BF2
- 命令：SIZE, GAP, TEXT, QRCODE, PRINT
- 可以直接打印中文，无需转换图像

### ZPL (Zebra打印机)
```zpl
^XA
^PW800
^LL600
^FO20,10^A0N,25,25^FD测试^FS
^XZ
```

**特点**:
- 命令以 ^ 开头
- 不支持中文字体
- 中文需要转换为图像（^GFA命令）

## Web界面使用

### 方法1: 文件上传
1. 访问: http://127.0.0.1:5000
2. 登录 (admin/admin)
3. 上传文件: `data/print_text_original.zpl`
4. 选择打印类型: **Label (ZPL)** *(虽然标记为ZPL，但实际支持TSPL)*

### 方法2: JSON数据
使用Web界面的"TSPL标签示例"：

```json
{
  "print_type": "label",
  "zpl_code": "SIZE 60 mm, 40 mm\nGAP 1 mm, 0 mm\nDIRECTION 1,0\nREFERENCE 0,0\nOFFSET 0 mm\nCLS\nTEXT 20,10,\"TSS24.BF2\",0,1,1,\"容器类型\"\nQRCODE 20,60,L,10,A,0,M2,S6,\"ECKQ\"\nTEXT 240,60,\"TSS24.BF2\",0,1,2,\"二次库区托盘\"\nTEXT 240,120,\"TSS24.BF2\",0,1,2,\"编号:ECKQ\"\nTEXT 240,170,\"TSS24.BF2\",0,1,2,\"尺寸:null*0*null\"\nTEXT 240,220,\"TSS24.BF2\",0,1,2,\"载重:0\"\nPRINT 1\n"
}
```

### 方法3: MQTT发送
```python
import paho.mqtt.publish as publish
import json

tspl_code = """SIZE 60 mm, 40 mm
GAP 1 mm, 0 mm
DIRECTION 1,0
REFERENCE 0,0
OFFSET 0 mm
CLS
TEXT 20,10,"TSS24.BF2",0,1,1,"容器类型"
QRCODE 20,60,L,10,A,0,M2,S6,"ECKQ"
TEXT 240,60,"TSS24.BF2",0,1,2,"二次库区托盘"
TEXT 240,120,"TSS24.BF2",0,1,2,"编号:ECKQ"
TEXT 240,170,"TSS24.BF2",0,1,2,"尺寸:null*0*null"
TEXT 240,220,"TSS24.BF2",0,1,2,"载重:0"
PRINT 1
"""

message = {
    'print_type': 'label',
    'zpl_code': tspl_code
}

publish.single(
    'zebra/print',
    json.dumps(message, ensure_ascii=False),
    hostname='10.100.10.121',
    port=1883
)
```

## 打印机配置

确保 `config/printer_config.json` 中的打印机设置正确：

```json
{
  "printers": [
    {
      "name": "ZT411",
      "types": ["label"],
      "ip": null,
      "port": 9100,
      "device": null,
      "default": false,
      "_comment": "TSC标签打印机 - 使用TSPL语言"
    }
  ]
}
```

## 常见问题

### Q1: 为什么打印机名称是"ZT411"但实际是TSC打印机？
A: 配置文件中的名称只是标识符，系统会通过名称模糊匹配到实际的TSC打印机。

### Q2: 中文会乱码吗？
A: 不会！TSC打印机支持 TSS24.BF2 中文字体，可以直接打印中文。

### Q3: 需要转换中文为图像吗？
A: **不需要**！这是TSC打印机的优势，直接支持中文TEXT命令。

### Q4: 转换工具还有用吗？
A: 
- `convert_zpl_chinese.py` - **不要用于TSC打印机**
- 只适用于真正的Zebra ZPL打印机

### Q5: 如何验证打印机类型？
A: 
1. 查看打印机面板或外壳标签
2. 检查打印机驱动名称
3. 测试：发送TSPL命令看是否能打印

## 文件说明

### 可用文件
- ✅ `data/print_text.txt` - 原始TSPL代码（带转义）
- ✅ `data/print_text_original.zpl` - 格式化后的TSPL代码（可直接打印）

### 不要使用的文件
- ❌ `data/print_text_ready.zpl` - 转换后的ZPL格式（TSC打印机不支持）
- ❌ `data/print_text_fixed.zpl` - 其他转换格式

## TSPL命令参考

### 基本命令
- `SIZE width, height` - 设置标签尺寸
- `GAP gap, offset` - 设置间距
- `DIRECTION direction` - 打印方向
- `CLS` - 清除缓冲区
- `PRINT qty` - 打印

### 文本命令
```
TEXT x, y, "font", rotation, x_mult, y_mult, "content"
```
- x, y: 位置坐标
- font: 字体名称（TSS24.BF2 = 中文字体）
- rotation: 旋转角度
- x_mult, y_mult: 宽度和高度倍数
- content: 文本内容

### 二维码命令
```
QRCODE x, y, ECC, width, mode, rotation, model, mask, "data"
```

## 总结

✅ **TSC打印机最简单**：
- 直接使用原始TSPL代码
- 不需要任何转换
- 中文完美支持

❌ **不要**：
- 转换为ZPL格式
- 将中文转换为图像
- 使用标准ZPL命令

🎉 **您的打印已经是对的，无需修复！**

