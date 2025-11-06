# MQTT协议支持说明

## 支持的协议

本系统完整支持以下所有MQTT连接协议：

### 1. 标准MQTT (TCP)

**协议**: `mqtt://` 或 `tcp://`

**说明**: 标准MQTT协议，使用TCP传输层

**示例**:
- `mqtt://127.0.0.1:1883`
- `tcp://10.100.10.121:1883`

**默认端口**: 1883

**特点**:
- 最常用的MQTT连接方式
- 性能好，延迟低
- 适合局域网环境

---

### 2. MQTT over SSL/TLS

**协议**: `mqtts://`

**说明**: MQTT协议通过SSL/TLS加密传输

**示例**:
- `mqtts://example.com:8883`

**默认端口**: 8883

**特点**:
- 数据加密传输，安全性高
- 适合公网环境
- 需要有效的SSL证书（或使用自签名证书）

---

### 3. WebSocket (HTTP)

**协议**: `ws://`

**说明**: 通过WebSocket传输MQTT协议，基于HTTP

**示例**:
- `ws://10.100.10.121:8083/mqtt`
- `ws://example.com:80/mqtt`

**默认端口**: 80

**路径**: URL中的路径部分（如 `/mqtt`）会用作WebSocket连接路径

**特点**:
- 可以穿透防火墙和代理
- 适合Web应用集成
- 支持HTTP代理

---

### 4. WebSocket Secure (HTTPS)

**协议**: `wss://`

**说明**: 通过加密的WebSocket传输MQTT协议，基于HTTPS

**示例**:
- `wss://10.100.10.121/mqtt` (默认443端口)
- `wss://example.com:443/mqtt`

**默认端口**: 443

**路径**: URL中的路径部分（如 `/mqtt`）会用作WebSocket连接路径

**特点**:
- 加密传输，安全性高
- 可以穿透防火墙和代理
- 适合安全要求高的Web应用

---

## 协议对比

| 协议 | 传输层 | SSL/TLS | 默认端口 | 适用场景 |
|------|--------|---------|----------|----------|
| `mqtt://` | TCP | ❌ | 1883 | 局域网，内网 |
| `tcp://` | TCP | ❌ | 1883 | 同mqtt:// |
| `mqtts://` | TCP | ✅ | 8883 | 公网，需要加密 |
| `ws://` | WebSocket | ❌ | 80 | 穿透防火墙，Web应用 |
| `wss://` | WebSocket | ✅ | 443 | 安全Web应用 |

---

## 配置示例

### 配置文件格式

```json
{
  "mqtt": {
    "url": "ws://10.100.10.121:8083/mqtt",
    "topic": "zebra/print",
    "username": null,
    "password": null
  }
}
```

### 各协议配置示例

#### 标准MQTT
```json
{
  "mqtt": {
    "url": "mqtt://127.0.0.1:1883",
    "topic": "zebra/print"
  }
}
```

#### TCP连接（等同于mqtt://）
```json
{
  "mqtt": {
    "url": "tcp://10.100.10.121:1883",
    "topic": "zebra/print"
  }
}
```

#### WebSocket连接
```json
{
  "mqtt": {
    "url": "ws://10.100.10.121:8083/mqtt",
    "topic": "zebra/print"
  }
}
```

#### WebSocket Secure连接
```json
{
  "mqtt": {
    "url": "wss://10.100.10.121/mqtt",
    "topic": "zebra/print"
  }
}
```

#### MQTT over SSL/TLS
```json
{
  "mqtt": {
    "url": "mqtts://example.com:8883",
    "topic": "zebra/print"
  }
}
```

---

## 注意事项

### 1. 端口配置

- 如果URL中未指定端口，系统会根据协议自动使用默认端口
- 如果URL中指定了端口，则使用指定的端口

### 2. WebSocket路径

- WebSocket连接需要指定路径（如 `/mqtt`）
- 路径必须与MQTT服务器的WebSocket配置匹配
- 如果URL中没有路径，默认使用 `/mqtt`

### 3. SSL/TLS证书

- `mqtts://` 和 `wss://` 需要SSL/TLS证书
- 如果使用自签名证书，系统会自动尝试不验证证书模式（仅用于测试）
- 生产环境建议使用有效的SSL证书

### 4. 主题配置

- 主题（topic）需要单独配置，不从URL路径提取
- URL中的路径部分仅用于WebSocket连接路径

---

## 测试工具

使用以下工具测试各协议连接：

```bash
# 测试所有协议解析
python tests/test_all_protocols.py

# 测试WebSocket连接
python tests/test_websocket_mqtt.py ws://10.100.10.121:8083/mqtt zebra/print

# 测试MQTT连接
python tests/test_mqtt_connection.py
```

---

## 常见问题

### Q: wss://连接失败怎么办？

**A**: 检查以下几点：
1. 服务器是否支持WebSocket
2. WebSocket路径是否正确（如 `/mqtt`）
3. SSL证书是否有效
4. 防火墙是否允许443端口

### Q: mqtts://连接失败怎么办？

**A**: 检查以下几点：
1. 服务器是否启用了SSL/TLS
2. 端口是否正确（默认8883）
3. SSL证书配置是否正确
4. 如果是自签名证书，系统会自动尝试不验证证书模式

### Q: ws://连接超时怎么办？

**A**: 检查以下几点：
1. WebSocket路径是否正确
2. 服务器地址和端口是否正确
3. 防火墙是否允许连接
4. 查看日志文件获取详细错误信息

---

## 日志文件

所有连接过程都会记录到日志文件：
- 位置: `data/logs/mqtt_client_YYYYMMDD.log`
- 包含: 连接尝试、成功/失败、错误信息等

查看日志可以帮助诊断连接问题。

