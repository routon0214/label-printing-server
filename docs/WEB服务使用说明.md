# Web服务使用说明（FastAPI版本）

## 概述

打印机服务现在使用FastAPI框架，提供Web界面用于文件上传和打印测试，同时保留MQTT消息接收功能。所有页面都需要基础认证登录。

## 启动方式

直接运行主程序即可启动Web服务：

```bash
python app.py
```

启动后，访问地址：`http://127.0.0.1:5000`

## 登录认证

### 默认凭证

- **用户名**: `admin`
- **密码**: `admin123`

### 修改凭证

在配置文件 `config/printer_config.json` 中修改：

```json
{
  "web": {
    "username": "your_username",
    "password": "your_password"
  }
}
```

**注意**: 建议修改默认密码以确保安全！

### 认证方式

使用HTTP Basic Authentication（基础认证）。访问Web界面时，浏览器会自动弹出登录对话框，输入用户名和密码即可。

## 功能特性

### 1. 文件上传打印

- **支持的文件格式**：
  - `.zpl` - ZPL标签文件
  - `.pdf` - PDF文档
  - `.txt` - 文本文件（ESC/POS小票）
  - `.json` - JSON格式的标签数据

- **打印类型**：
  - 自动检测（根据文件扩展名）
  - ZPL标签打印
  - PDF文档打印
  - ESC/POS小票打印

### 2. JSON数据打印

可以直接发送JSON格式的打印数据，支持：
- ZPL标签数据
- PDF数据（base64编码）
- ESC/POS小票数据（结构化或原始文本）

### 3. MQTT接收功能

Web服务启动后，MQTT客户端会在后台自动启动，继续接收MQTT消息并打印。

## 使用示例

### 上传ZPL文件打印

1. 访问 `http://127.0.0.1:5000`，使用用户名和密码登录
2. 点击"选择文件"，选择一个`.zpl`文件
3. 选择打印类型为"ZPL标签打印"（或保持"自动检测"）
4. 点击"上传并打印"

### 上传PDF文件打印

1. 登录后，点击"选择文件"，选择一个`.pdf`文件
2. 选择打印类型为"PDF文档打印"
3. 点击"上传并打印"

### 发送JSON数据打印

在"JSON数据打印"区域，输入JSON数据，例如：

```json
{
  "print_type": "label",
  "zpl_code": "^XA^FO20,10^A0N,25,25^FD测试标签^FS^XZ"
}
```

然后点击"发送打印"。

## API接口

所有API接口都需要基础认证。

### POST /api/print

文件上传打印接口

**请求格式**：`multipart/form-data`
- `file`: 文件
- `print_type`: 打印类型（可选，自动检测）

**认证**: HTTP Basic Auth

**响应**：
```json
{
  "success": true,
  "message": "打印任务已发送",
  "print_type": "label"
}
```

### POST /api/print/raw

JSON数据打印接口

**请求格式**：`application/json`

**认证**: HTTP Basic Auth

**响应**：
```json
{
  "success": true,
  "message": "打印任务已发送"
}
```

### GET /api/status

获取服务状态

**认证**: HTTP Basic Auth

**响应**：
```json
{
  "mqtt": {
    "status": "running",
    "host": "127.0.0.1",
    "port": 1883,
    "topic": "zebra/print"
  },
  "printers": {
    "count": 2,
    "configs": [...]
  }
}
```

### GET /api/config

获取配置信息（密码会被隐藏）

**认证**: HTTP Basic Auth

## 注意事项

1. **文件大小限制**：最大支持50MB的文件上传
2. **MQTT服务**：Web服务启动时，MQTT客户端会自动在后台启动
3. **打印机配置**：使用与MQTT服务相同的配置文件 `config/printer_config.json`
4. **上传文件**：上传的文件会临时保存在 `data/uploads` 目录，打印完成后自动删除
5. **安全**：所有API和页面都需要基础认证，建议修改默认密码

## 故障排除

### Web服务无法启动

- 检查是否安装了FastAPI：`pip install fastapi uvicorn jinja2 python-multipart`
- 检查端口5000是否被占用
- 查看控制台错误信息

### 无法登录

- 检查配置文件中的用户名和密码
- 确认使用的是HTTP Basic Auth（浏览器会自动弹出登录框）
- 清除浏览器缓存和Cookie后重试

### MQTT服务未启动

- 检查MQTT配置是否正确
- 查看Web界面上的MQTT状态显示
- 检查控制台日志

### 打印失败

- 检查打印机配置是否正确
- 确认打印机已连接并可用
- 查看Web界面的错误提示信息

## 技术栈

- **Web框架**: FastAPI
- **服务器**: Uvicorn
- **模板引擎**: Jinja2
- **认证方式**: HTTP Basic Authentication
