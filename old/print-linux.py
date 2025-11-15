import json
import os
import re
import subprocess
import tempfile

import paho.mqtt.client as mqtt
import redis
import cups

# 加载配置文件
def load_config(config_file="print.json"):
    with open(config_file, "r", encoding="utf-8") as f:
        return json.load(f)

def find_printers_by_keyword(keyword):
    """
    根据关键字模糊搜索打印机（Linux/CUPS 版）。
    :param keyword: 关键字（如 "deli"）
    :return: 匹配的打印机名称列表
    """
    matched_printers = []
    try:
        #列出所有打印机
        # 连接到 CUPS 服务器
        conn = cups.Connection()
        # 获取所有打印机
        printers = conn.getPrinters()

        for printer_name, printer_info in printers.items():
            if keyword.lower() in printer_name.lower():
                matched_printers.append(printer_name)

    except Exception as e:
        print(f"无法连接到 CUPS 打印系统: {e}")
        return []

    return matched_printers


def send_raw_command_to_printer(printer_name, raw_data):
    """
    向打印机发送原始指令（Linux/CUPS 版）
    :param printer_name: CUPS 中的打印机名称
    :param raw_data: 要打印的文本内容（字符串）
    """
    try:
        conn = cups.Connection()

        # 编码数据
        try:
            data_to_send = raw_data.encode('gb2312')
        except UnicodeEncodeError:
            data_to_send = raw_data.encode('gb2312', errors='replace')

        # 初始化命令
        init_sequence = b'\x1B\x40'        # ESC @ - 初始化
        charset_command = b'\x1B\x74\x0E'  # ESC t 14 - 简体中文

        full_data = init_sequence + charset_command + data_to_send

        # ✅ 正确做法：写入临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.prn') as f:
            f.write(full_data)
            temp_filename = f.name

        try:
            # ✅ 只传 4 个参数
            job_id = conn.printFile(
                printer_name,
                temp_filename,
                "Raw Print Job",
                {}  # options
            )
            print(f"✅ 打印任务已提交，任务 ID: {job_id}")
        finally:
            # 清理临时文件
            os.unlink(temp_filename)

    except cups.IPPError as e:
        print(f"❌ CUPS 打印失败: {e}")
    except Exception as e:
        print(f"❌ 发送失败: {e}")


# MQTT 回调函数
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("已连接到 MQTT 服务器")
        # 订阅主题
        topic = userdata["mqtt"]["topic"]
        client.subscribe(topic)
        print(f"已订阅主题: {topic}")
    else:
        print(f"连接失败，错误代码: {rc}")


CURRENT_PRINTER_NAME = ""

def on_message(client, userdata, msg):
    print(f"收到消息: {msg.topic} -> {msg.payload.decode('utf-8')}")

    printer_name = CURRENT_PRINTER_NAME
    # 将消息内容作为原始指令发送到打印机
    try:
        # 解码消息内容
        # raw_data = msg.payload.decode('utf-8')
        key = msg.payload.decode('utf-8')
        queue_key = "tpm-iot-protocol:devicePrintContent:"+key
        print("队列名称：", queue_key )
        if redis_client.llen(queue_key) == 0:
            print("队列为空")
            return
        # 从队列中获取元素（右侧弹出）
        while redis_client.llen(queue_key) > 0:
            raw_data = redis_client.rpop(queue_key)
            print("从队列中获取元素：", raw_data)

            print(f"解码后的原始指令: {raw_data}")
            raw_data = raw_data.replace("\\n", "\n").replace('\\"', '"')
            # 发送原始指令到打印机
            send_raw_command_to_printer(printer_name, raw_data)
    except Exception as e:
        print(f"处理消息时出错: {e}")


def test_cups():
    # test_cups.py
    try:
        import cups

        print("✅ 成功导入 cups")

        # 检查是否有 Connection
        if hasattr(cups, 'Connection'):
            print("✅ cups 模块包含 Connection")
            conn = cups.Connection()
            printers = conn.getPrinters()
            print("🖨️  打印机列表:", printers)
        else:
            print("❌ cups 模块缺少 Connection！")
            print("当前 cups 模块属性:", dir(cups))

    except Exception as e:
        print(f"❌ 错误: {type(e).__name__}: {e}")



# 主程序
if __name__ == "__main__":
    # 加载配置文件
    config = load_config()
    test_cups()

    # 获取打印机名称
    printer_name = config["printer"]["name"]
    printer_names =  find_printers_by_keyword(printer_name)
    if not printer_names:
      print("未找到打印机")
      #退出程序
      exit()
    else :
        CURRENT_PRINTER_NAME = printer_names[0]
        print("打印机名称：", CURRENT_PRINTER_NAME)

    # 创建 MQTT 客户端
    client = mqtt.Client(userdata=config)

    #config["redis"]填充到配置中

    # 创建 Redis 连接
    redis_client = redis.StrictRedis(
        # Redis 服务器地址
        host= config["redis"]["host"],
        # Redis 服务端口默认6379
        port=config["redis"]["port"],
        username=config["redis"]["username"],
        # 密码
        password=config["redis"]["password"],
        db= config["redis"]["db"],
        decode_responses=True  # 自动解码响应为字符串
    )
    #检查redis是否连接成功
    if redis_client.ping():
        print("Redis 连接成功")
    else:
        print("Redis 连接失败")

    # 设置回调函数
    client.on_connect = on_connect
    client.on_message = on_message

    # 连接到 MQTT 服务器
    broker = config["mqtt"]["broker"]
    port = config["mqtt"]["port"]
    client.connect(broker, port, 60)

    client.publish("/iot/platform/online", '{"id":"1746824890012405761"}')

    # 开始循环监听
    client.loop_forever()