#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
打印机Web服务 - FastAPI版本
提供Web界面用于文件上传和打印测试，同时保留MQTT接收功能
支持基础认证登录
"""

import sys
import os
import platform
import threading
import base64
import tempfile
import json
import datetime
import time
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, Request, HTTPException, Depends, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import uvicorn
import re

# Windows 控制台编码修复
if sys.platform == 'win32':
    import io
    try:
        if sys.stdout.encoding != 'utf-8':
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        if sys.stderr.encoding != 'utf-8':
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass

# 添加项目根目录和src目录到路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))


def get_resource_path(relative_path):
    """获取资源文件的绝对路径（兼容打包后的环境）"""
    if getattr(sys, 'frozen', False):
        # 打包后的路径：优先使用可执行文件所在目录（用于用户可修改的文件）
        # templates/static 等只读资源使用 _MEIPASS
        base_path = os.path.dirname(sys.executable)
    else:
        # 开发环境路径
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


def get_internal_resource_path(relative_path):
    """获取内部资源文件的绝对路径（打包后在 _internal 目录）"""
    if getattr(sys, 'frozen', False):
        # 打包后的内部资源路径 (templates, static 等)
        base_path = sys._MEIPASS
    else:
        # 开发环境路径
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


from src.config import ConfigManager, create_default_config
from src.core import LabelPrintMQTT
from src.core.printer import ZebraPrinter
from src.core.pdf_printer import PDFPrinter
from src.core.escpos_printer import ESCPOSPrinter
from src.core.zpl_generator import ZPLGenerator
from src.utils.zpl_chinese_converter import detect_and_convert_zpl
from src.utils.log_manager import LogManager
from src.utils.print_queue import get_print_queue

# 创建FastAPI应用
app = FastAPI(title="打印机Web服务", description="支持文件上传和MQTT接收的打印服务")

# 日志管理器
log_manager = LogManager(log_dir='data/logs', retention_days=7)

# 打印队列
print_queue = None

# FastAPI启动事件 - 自动启动MQTT客户端
@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    global config_manager, print_queue
    
    # 确保目录存在
    ensure_directories()
    
    # 检查配置文件
    config_file = 'config/printer_config.json'
    if not os.path.exists(config_file):
        print(f"配置文件不存在，正在创建默认配置...")
        create_default_config(config_file)
    
    # 初始化配置管理器（如果还未初始化）
    if config_manager is None:
        config_manager = ConfigManager(config_file)
    
    # 初始化打印队列
    print("\n" + "="*70)
    print("初始化打印队列...")
    print("="*70)
    print_queue = get_print_queue()
    print("打印队列已启动")
    
    # 清理过期日志
    print("\n" + "="*70)
    print("清理过期日志...")
    print("="*70)
    deleted_count = log_manager.clean_old_logs()
    print(f"已清理 {deleted_count} 个过期日志文件")
    
    # 启动MQTT客户端
    print("\n" + "="*70)
    print("应用启动事件 - 自动启动MQTT客户端")
    print("="*70)
    start_mqtt_client()
    
    # 启动日志清理定时任务
    import asyncio
    asyncio.create_task(scheduled_log_cleanup())

# FastAPI关闭事件 - 停止MQTT客户端
@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行"""
    global print_queue
    
    print("\n" + "="*70)
    print("应用关闭事件")
    print("="*70)
    
    # 停止打印队列
    if print_queue:
        print("停止打印队列...")
        print_queue.stop()
    
    # 停止MQTT客户端
    print("停止MQTT客户端...")
    stop_mqtt_client()

# 静态文件和模板（兼容打包后的环境）
# 这些是只读资源，使用 _internal 目录
static_dir = get_internal_resource_path('static')
templates_dir = get_internal_resource_path('templates')

if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
else:
    print(f"[WARNING] 静态文件目录不存在: {static_dir}")

if os.path.exists(templates_dir):
    templates = Jinja2Templates(directory=templates_dir)
else:
    print(f"[WARNING] 模板目录不存在: {templates_dir}")
    templates = None

# 基础认证
security = HTTPBasic()

# 全局变量
mqtt_client = None
mqtt_thread = None
config_manager = None
zpl_generator = ZPLGenerator()

# 允许的文件扩展名
ALLOWED_EXTENSIONS = {
    'zpl': 'label',
    'txt': 'escpos',
    'pdf': 'pdf',
    'json': 'label'  # JSON格式的标签数据
}

# Web认证配置（默认用户名密码，可以从配置文件读取）
WEB_USERNAME = os.getenv('WEB_USERNAME', 'admin')
WEB_PASSWORD = os.getenv('WEB_PASSWORD', 'admin123')


def ensure_directories():
    """确保所有必要的目录存在"""
    directories = [
        'config',
        'data/logs',
        'data/failed_labels',
        'data/uploads',
        'data/print_queue',
        'templates',
        'static'
    ]
    
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
        except Exception as e:
            print(f"警告：无法创建目录 {directory}: {e}")


def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    """验证用户凭证"""
    global config_manager
    
    # 尝试从配置文件读取用户名密码
    if config_manager is None:
        config_manager = ConfigManager('config/printer_config.json')
    
    config = config_manager.load()
    web_config = config.get('web', {})
    
    username = web_config.get('username', WEB_USERNAME)
    password = web_config.get('password', WEB_PASSWORD)
    
    if credentials.username != username or credentials.password != password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def secure_filename(filename):
    """
    安全的文件名处理函数（替代werkzeug的secure_filename）
    移除或替换文件名中的不安全字符
    """
    # 保留文件名和扩展名
    if '.' in filename:
        name, ext = filename.rsplit('.', 1)
    else:
        name, ext = filename, ''
    
    # 移除不安全字符，只保留字母、数字、下划线、连字符和点
    name = re.sub(r'[^\w\-_.]', '_', name)
    
    # 移除连续的下划线
    name = re.sub(r'_+', '_', name)
    
    # 移除开头和结尾的下划线和连字符
    name = name.strip('_-')
    
    # 如果名称为空，使用默认名称
    if not name:
        name = 'file'
    
    # 重新组合文件名
    if ext:
        return f"{name}.{ext}"
    return name


def get_print_type_from_filename(filename):
    """根据文件名推断打印类型"""
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    return ALLOWED_EXTENSIONS.get(ext, 'label')


def stop_mqtt_client():
    """停止MQTT客户端"""
    global mqtt_client, mqtt_thread
    import time
    
    if mqtt_client:
        try:
            # 使用客户端的stop方法正常停止
            print("正在停止MQTT客户端...")
            mqtt_client.stop()
            # 等待一下确保断开操作完成
            time.sleep(0.5)
        except Exception as e:
            print(f"停止MQTT客户端时出错: {e}")
    
    # 等待线程结束
    if mqtt_thread and mqtt_thread.is_alive():
        print("等待MQTT线程结束...")
        mqtt_thread.join(timeout=5)
        if mqtt_thread.is_alive():
            print("[WARNING] MQTT线程未能在5秒内停止")
        else:
            print("[OK] MQTT线程已结束")
    
    # 额外等待确保资源释放
    time.sleep(0.5)
    
    mqtt_client = None
    mqtt_thread = None


def start_mqtt_client():
    """在后台线程中启动MQTT客户端"""
    global mqtt_client, mqtt_thread, config_manager
    import time
    
    print("\n" + "="*70)
    print("开始启动MQTT客户端...")
    print("="*70)
    
    # 先停止旧的客户端（如果存在）
    if mqtt_client or mqtt_thread:
        print("检测到旧的MQTT客户端，正在停止...")
        stop_mqtt_client()
        print("[OK] 旧客户端已停止")
        # 等待一下确保资源完全释放
        time.sleep(1)
    
    try:
        # 确保config_manager已初始化
        print("\n[步骤1] 加载配置文件...")
        if config_manager is None:
            print("  初始化配置管理器...")
            config_manager = ConfigManager('config/printer_config.json')
            print("  [OK] 配置管理器已初始化")
        else:
            print("  [OK] 配置管理器已存在")
        
        # 重新加载配置（确保使用最新配置）
        print("  重新加载配置...")
        config = config_manager.load()
        print(f"  [OK] 配置已重新加载")
        
        print("\n[步骤2] 解析MQTT配置...")
        mqtt_config = config_manager.get_mqtt_config()
        print(f"  MQTT配置:")
        print(f"    主机: {mqtt_config.get('host', '127.0.0.1')}")
        print(f"    端口: {mqtt_config.get('port', 1883)}")
        print(f"    协议: {mqtt_config.get('protocol', 'mqtt')}")
        print(f"    主题: {mqtt_config.get('topic', 'zebra/print')}")
        if mqtt_config.get('url'):
            print(f"    URL: {mqtt_config.get('url')}")
        if mqtt_config.get('username'):
            print(f"    用户名: {mqtt_config.get('username')}")
        
        printers_config = config.get('printers', [])
        printer_config = config.get('printer')
        print(f"  [OK] 找到 {len(printers_config)} 个打印机配置")
        
        # 创建MQTT客户端
        print("\n[步骤3] 创建MQTT客户端实例...")
        mqtt_client = LabelPrintMQTT(
            broker_host=mqtt_config.get('host', '127.0.0.1'),
            broker_port=mqtt_config.get('port', 1883),
            topic=mqtt_config.get('topic', 'zebra/print'),
            username=mqtt_config.get('username'),
            password=mqtt_config.get('password'),
            protocol=mqtt_config.get('protocol'),
            url=mqtt_config.get('url'),
            client_id=mqtt_config.get('client_id'),  # 如果为None，会自动生成随机ID
            printer_config=printer_config,
            printers_config=printers_config
        )
        print("  [OK] MQTT客户端实例已创建")
        
        # 在后台线程中启动
        print("\n[步骤4] 启动后台线程...")
        mqtt_thread = threading.Thread(target=mqtt_client.start, daemon=True, name="MQTT-Client-Thread")
        mqtt_thread.start()
        print(f"  [OK] 后台线程已启动 (线程ID: {mqtt_thread.ident})")
        print(f"  [OK] 线程状态: {'运行中' if mqtt_thread.is_alive() else '已停止'}")
        
        # 等待一下确保客户端开始连接
        time.sleep(0.5)
        
        print("\n" + "="*70)
        print("[OK] MQTT客户端已在后台启动")
        print("="*70)
        return True
        
    except Exception as e:
        print("\n" + "="*70)
        print(f"[ERROR] MQTT客户端启动失败")
        print("="*70)
        print(f"错误信息: {e}")
        import traceback
        traceback.print_exc()
        print("="*70)
        return False


def normalize_print_data(data):
    """
    将打印数据标准化为统一格式
    
    旧格式自动转换为新格式：
    - zpl_code → format: "zpl", content: zpl_code
    - raw_text → format: "raw", content: raw_text
    - fields → format: "structured", content: {fields, ...}
    
    兼容字段名：printType (驼峰) 和 print_type (下划线)
    
    Args:
        data: 打印数据字典
        
    Returns:
        标准化后的数据字典
    """
    # 确保输入是字典类型
    if not isinstance(data, dict):
        raise ValueError(f"打印数据必须是字典对象，当前类型为: {type(data).__name__}")
    
    # 统一字段名：将 printType 转换为 print_type
    if 'printType' in data and 'print_type' not in data:
        data['print_type'] = data.pop('printType')
    
    # 如果已经是新格式（包含format和content字段），验证后返回
    if 'format' in data and 'content' in data:
        # 验证content不为None
        if data.get('content') is None:
            raise ValueError(f"新格式数据的content字段不能为空 (format: {data.get('format')})")
        return data
    
    print_type = data.get('print_type', 'label')
    
    # 向后兼容：转换旧格式
    if 'zpl_code' in data:
        # 旧格式: zpl_code
        return {
            'print_type': print_type,
            'format': 'zpl',
            'content': data['zpl_code']
        }
    
    elif 'raw_text' in data:
        # 旧格式: raw_text
        raw_text = data.get('raw_text')
        if raw_text is None:
            raise ValueError("raw_text字段不能为空")
        
        return {
            'print_type': print_type,
            'format': 'raw',
            'content': raw_text,
            'encoding': data.get('encoding', 'gb2312')
        }
    
    elif 'fields' in data or 'title' in data or 'items' in data:
        # 旧格式: 结构化数据
        content = {}
        # 复制所有字段到content（除了print_type）
        for key, value in data.items():
            if key != 'print_type' and key != 'printType':
                content[key] = value
        
        return {
            'print_type': print_type,
            'format': 'structured',
            'content': content
        }
    
    # 无法识别的格式，原样返回
    return data


def get_printer_instance(print_type, printer_config=None):
    """
    根据打印类型获取打印机实例
    
    Args:
        print_type: 打印类型 ('label', 'pdf', 'receipt', 'escpos')
        printer_config: 打印机配置（可选）
        
    Returns:
        打印机实例
    """
    global config_manager
    if config_manager is None:
        config_manager = ConfigManager('config/printer_config.json')
    config = config_manager.load()
    printers_config = config.get('printers', [])
    
    # 如果提供了打印机配置，使用它
    if printer_config:
        if print_type == 'label':
            return ZebraPrinter(
                printer_name=printer_config.get('name'),
                printer_ip=printer_config.get('ip'),
                printer_port=printer_config.get('port', 9100),
                device_path=printer_config.get('device')
            )
        elif print_type == 'pdf':
            return PDFPrinter(printer_name=printer_config.get('name'))
        elif print_type in ['receipt', 'escpos']:
            return ESCPOSPrinter(
                printer_ip=printer_config.get('ip'),
                printer_port=printer_config.get('port', 9100),
                printer_name=printer_config.get('name'),
                device_path=printer_config.get('device')
            )
    
    # 否则从配置中查找
    # 优先查找专用打印机
    for printer_cfg in printers_config:
        types = printer_cfg.get('types', [])
        if print_type in types:
            if print_type == 'label':
                return ZebraPrinter(
                    printer_name=printer_cfg.get('name'),
                    printer_ip=printer_cfg.get('ip'),
                    printer_port=printer_cfg.get('port', 9100),
                    device_path=printer_cfg.get('device')
                )
            elif print_type == 'pdf':
                return PDFPrinter(printer_name=printer_cfg.get('name'))
            elif print_type in ['receipt', 'escpos']:
                return ESCPOSPrinter(
                    printer_ip=printer_cfg.get('ip'),
                    printer_port=printer_cfg.get('port', 9100),
                    printer_name=printer_cfg.get('name'),
                    device_path=printer_cfg.get('device')
                )
    
    # 查找通用打印机（types: ["*"]）
    for printer_cfg in printers_config:
        types = printer_cfg.get('types', [])
        if '*' in types:
            if print_type == 'label':
                return ZebraPrinter(
                    printer_name=printer_cfg.get('name'),
                    printer_ip=printer_cfg.get('ip'),
                    printer_port=printer_cfg.get('port', 9100),
                    device_path=printer_cfg.get('device')
                )
            elif print_type == 'pdf':
                return PDFPrinter(printer_name=printer_cfg.get('name'))
            elif print_type in ['receipt', 'escpos']:
                return ESCPOSPrinter(
                    printer_ip=printer_cfg.get('ip'),
                    printer_port=printer_cfg.get('port', 9100),
                    printer_name=printer_cfg.get('name'),
                    device_path=printer_cfg.get('device')
                )
    
    # 使用默认配置
    printer_config = config.get('printer', {})
    if print_type == 'label':
        return ZebraPrinter(
            printer_name=printer_config.get('name'),
            printer_ip=printer_config.get('ip'),
            printer_port=printer_config.get('port', 9100),
            device_path=printer_config.get('device')
        )
    elif print_type == 'pdf':
        return PDFPrinter(printer_name=printer_config.get('name'))
    elif print_type in ['receipt', 'escpos']:
        return ESCPOSPrinter(
            printer_ip=printer_config.get('ip'),
            printer_port=printer_config.get('port', 9100),
            printer_name=printer_config.get('name'),
            device_path=printer_config.get('device')
        )
    
    return None


@app.get("/", response_class=HTMLResponse)
async def index(request: Request, username: str = Depends(verify_credentials)):
    """首页（需要认证）"""
    if templates is None:
        return HTMLResponse(
            content="<h1>错误：模板文件未找到</h1><p>请确保 templates 目录存在</p>",
            status_code=500
        )
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/print")
async def print_file(
    file: UploadFile = File(...),
    print_type: Optional[str] = Form(None),
    username: str = Depends(verify_credentials)
):
    """处理文件打印请求"""
    try:
        # 检查文件
        if not file.filename:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "未选择文件"}
            )
        
        # 获取打印类型
        if not print_type:
            print_type = get_print_type_from_filename(file.filename)
        else:
            print_type = print_type.lower()
        
        # 验证文件类型
        if not allowed_file(file.filename):
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": f'不支持的文件类型。支持的类型: {", ".join(ALLOWED_EXTENSIONS.keys())}'}
            )
        
        # 保存上传的文件
        filename = secure_filename(file.filename)
        filepath = os.path.join('data/uploads', filename)
        os.makedirs('data/uploads', exist_ok=True)
        
        with open(filepath, 'wb') as f:
            content = await file.read()
            f.write(content)
        
        # 读取文件内容
        with open(filepath, 'rb') as f:
            file_content = f.read()
        
        # 根据打印类型处理
        success = False
        error_msg = None
        
        if print_type == 'label':
            # ZPL标签打印
            if filename.endswith('.zpl'):
                # 尝试使用UTF-8解码，如果失败则尝试其他编码
                try:
                    zpl_code = file_content.decode('utf-8')
                except UnicodeDecodeError:
                    try:
                        zpl_code = file_content.decode('gbk')
                        print(f"警告: ZPL文件使用GBK编码解码")
                    except:
                        zpl_code = file_content.decode('utf-8', errors='replace')
                        print(f"警告: ZPL文件包含无法解码的字符，已替换")
            elif filename.endswith('.json'):
                # JSON格式的标签数据
                try:
                    data = json.loads(file_content.decode('utf-8'))
                    zpl_code = zpl_generator.generate_label_zpl(data)
                except UnicodeDecodeError:
                    error_msg = 'JSON文件编码错误，请确保使用UTF-8编码保存'
                    os.remove(filepath)
                    return JSONResponse(
                        status_code=400,
                        content={"success": False, "error": error_msg}
                    )
                except Exception as e:
                    error_msg = f'JSON解析失败: {e}'
                    os.remove(filepath)
                    return JSONResponse(
                        status_code=400,
                        content={"success": False, "error": error_msg}
                    )
            else:
                # 将文本内容作为ZPL代码
                try:
                    zpl_code = file_content.decode('utf-8')
                except UnicodeDecodeError:
                    try:
                        zpl_code = file_content.decode('gbk')
                        print(f"警告: 文件使用GBK编码解码")
                    except:
                        zpl_code = file_content.decode('utf-8', errors='replace')
                        print(f"警告: 文件包含无法解码的字符，已替换")
            
            printer = get_printer_instance('label')
            if not printer:
                os.remove(filepath)
                return JSONResponse(
                    status_code=400,
                    content={"success": False, "error": "未配置标签打印机"}
                )
            
            # 自动检测并转换ZPL中的中文
            zpl_code, was_converted = detect_and_convert_zpl(zpl_code)
            if was_converted:
                print("  [OK] ZPL中文已自动转换为图像")
            
            # 调试：保存实际发送的ZPL代码
            debug_file = f"data/debug_web_upload_{filename}"
            try:
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(zpl_code)
                print(f"  [DEBUG] ZPL已保存到: {debug_file}")
                print(f"  [DEBUG] ZPL长度: {len(zpl_code)} 字符")
                print(f"  [DEBUG] ZPL预览: {zpl_code[:100]}...")
            except Exception as debug_error:
                print(f"  [WARNING] 无法保存调试文件: {debug_error}")
            
            success = printer.print_label(zpl_code)
            if not success:
                error_msg = '标签打印失败'
        
        elif print_type == 'pdf':
            # PDF打印
            printer = get_printer_instance('pdf')
            if not printer:
                os.remove(filepath)
                return JSONResponse(
                    status_code=400,
                    content={"success": False, "error": "未配置PDF打印机"}
                )
            
            # 将文件内容编码为base64
            pdf_base64 = base64.b64encode(file_content).decode('utf-8')
            
            success = printer.print_pdf(pdf_base64, None)
            if not success:
                error_msg = 'PDF打印失败'
        
        elif print_type in ['receipt', 'escpos']:
            # ESC/POS小票打印
            printer = get_printer_instance('receipt')
            if not printer:
                os.remove(filepath)
                return JSONResponse(
                    status_code=400,
                    content={"success": False, "error": "未配置ESC/POS打印机"}
                )
            
            # 读取文本内容
            try:
                text_content = file_content.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    text_content = file_content.decode('gbk')
                    print(f"警告: 文件使用GBK编码解码")
                except:
                    text_content = file_content.decode('utf-8', errors='replace')
                    print(f"警告: 文件包含无法解码的字符，已替换")
            
            # 构建打印数据（统一格式：format + content）
            # 注意：ESC/POS打印机推荐使用 gb2312 编码以正确显示中文
            print_data = {
                'print_type': 'receipt',
                'format': 'raw',
                'content': text_content,
                'encoding': 'gb2312'  # 使用gb2312编码避免中文乱码
            }
            
            # 使用统一的打印队列处理
            print_queue = get_print_queue()
            task_id = print_queue.add_task(print_data, printer)
            print(f"  [OK] 打印任务已加入队列: {task_id}")
            success = True  # 队列处理是异步的，这里返回True表示任务已成功加入队列
        
        else:
            os.remove(filepath)
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": f'不支持的打印类型: {print_type}'}
            )
        
        # 清理临时文件
        try:
            os.remove(filepath)
        except:
            pass
        
        if success:
            return JSONResponse({
                "success": True,
                "message": f'{print_type.upper()}打印任务已发送',
                "print_type": print_type
            })
        else:
            return JSONResponse(
                status_code=500,
                content={"success": False, "error": error_msg or "打印失败"}
            )
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f'处理请求时出错: {str(e)}'}
        )


@app.post("/api/print/raw")
async def print_raw(
    request: Request,
    username: str = Depends(verify_credentials)
):
    """处理原始数据打印请求（JSON格式）- 使用队列，支持单个对象或数组"""
    global print_queue
    
    try:
        data = await request.json()
        if not data:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "无效的JSON数据"}
            )
        
        # 初始化打印队列
        if print_queue is None:
            print_queue = get_print_queue()
        
        # 检测是否为数组格式
        is_array = isinstance(data, list)
        
        # 统一处理为数组格式
        data_list = data if is_array else [data]
        
        print(f"\n[打印请求]")
        print(f"  格式: {'数组' if is_array else '单个对象'}")
        print(f"  任务数量: {len(data_list)}")
        
        # 处理每个打印任务
        results = []
        task_ids = []
        errors = []
        
        for idx, item in enumerate(data_list):
            try:
                # 验证数据格式：必须是字典
                if not isinstance(item, dict):
                    error_msg = f'任务 {idx + 1} 的数据格式错误：必须是JSON对象，当前类型为 {type(item).__name__}'
                    print(f"    [ERROR] {error_msg}")
                    errors.append({"index": idx, "error": error_msg})
                    results.append({
                        "index": idx,
                        "success": False,
                        "error": error_msg
                    })
                    continue
                
                # 标准化数据格式（支持新旧格式）
                normalized_data = normalize_print_data(item)
                if not isinstance(normalized_data, dict):
                    error_msg = f'任务 {idx + 1} 标准化后格式错误：必须是字典对象'
                    print(f"    [ERROR] {error_msg}")
                    errors.append({"index": idx, "error": error_msg})
                    results.append({
                        "index": idx,
                        "success": False,
                        "error": error_msg
                    })
                    continue
                
                print_type = normalized_data.get('print_type', 'label').lower()
                data_format = normalized_data.get('format', 'structured')
                
                print(f"  [任务 {idx + 1}] 类型: {print_type}, 格式: {data_format}")
                
                # 获取打印机实例
                printer = get_printer_instance(print_type)
                if not printer:
                    error_msg = f'未配置{print_type}打印机'
                    print(f"    [ERROR] {error_msg}")
                    errors.append({"index": idx, "error": error_msg})
                    results.append({
                        "index": idx,
                        "success": False,
                        "error": error_msg
                    })
                    continue
                
                # 添加到打印队列
                task_id = print_queue.add_task(normalized_data, printer)
                task_ids.append(task_id)
                
                print(f"    [OK] 任务已加入队列: {task_id}")
                results.append({
                    "index": idx,
                    "success": True,
                    "task_id": task_id,
                    "print_type": print_type
                })
                
            except Exception as item_error:
                error_msg = f'处理任务 {idx + 1} 时出错: {str(item_error)}'
                print(f"    [ERROR] {error_msg}")
                import traceback
                traceback.print_exc()
                errors.append({"index": idx, "error": error_msg})
                results.append({
                    "index": idx,
                    "success": False,
                    "error": error_msg
                })
        
        # 统计结果
        success_count = len([r for r in results if r.get('success')])
        failed_count = len(errors)
        
        print(f"  [结果] 成功: {success_count}, 失败: {failed_count}")
        print(f"  [队列] 当前队列大小: {print_queue.get_status()['queue_size']}")
        
        # 返回结果
        if is_array:
            # 数组格式：返回详细的每个任务的结果
            return JSONResponse({
                "success": success_count > 0,
                "message": f'批量打印任务处理完成: 成功 {success_count} 个, 失败 {failed_count} 个',
                "total": len(data_list),
                "success_count": success_count,
                "failed_count": failed_count,
                "task_ids": task_ids,
                "results": results,
                "queue_size": print_queue.get_status()['queue_size']
            })
        else:
            # 单个对象格式：保持原有的返回格式
            if results and results[0].get('success'):
                return JSONResponse({
                    "success": True,
                    "message": f'{results[0].get("print_type", "").upper()}打印任务已加入队列',
                    "task_id": task_ids[0] if task_ids else None,
                    "queue_size": print_queue.get_status()['queue_size']
                })
            else:
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "error": errors[0]['error'] if errors else "处理任务失败"
                    }
                )
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f'处理请求时出错: {str(e)}'}
        )


@app.get("/api/status")
async def get_status(username: str = Depends(verify_credentials)):
    """获取服务状态"""
    global config_manager, mqtt_client, mqtt_thread, print_queue
    if config_manager is None:
        config_manager = ConfigManager('config/printer_config.json')
    config = config_manager.load()
    mqtt_config = config_manager.get_mqtt_config()
    printers_config = config.get('printers', [])
    
    # 检查MQTT连接状态
    mqtt_status = 'stopped'
    mqtt_error = None
    
    if mqtt_client and mqtt_thread and mqtt_thread.is_alive():
        # 优先使用客户端内部的连接状态标记
        if hasattr(mqtt_client, 'is_connected'):
            if mqtt_client.is_connected:
                mqtt_status = 'running'
            else:
                # 线程存活但未连接，可能是连接失败或正在连接
                if mqtt_client.client:
                    # 客户端对象已创建，可能是连接失败
                    mqtt_status = 'stopped'
                    if hasattr(mqtt_client, 'connection_error') and mqtt_client.connection_error:
                        mqtt_error = mqtt_client.connection_error
                else:
                    # 客户端对象未创建，可能是正在初始化
                    mqtt_status = 'connecting'
        else:
            # 如果没有连接状态标记，使用fallback检查
            if mqtt_client.client:
                try:
                    # 检查连接状态（is_connected()是paho-mqtt的方法）
                    if hasattr(mqtt_client.client, 'is_connected'):
                        if mqtt_client.client.is_connected():
                            mqtt_status = 'running'
                    else:
                        # 如果没有is_connected方法，检查_sock属性（内部状态）
                        if hasattr(mqtt_client.client, '_sock') and mqtt_client.client._sock:
                            mqtt_status = 'running'
                        elif hasattr(mqtt_client.client, '_state') and mqtt_client.client._state == 1:
                            # MQTT状态: 1 = connected
                            mqtt_status = 'running'
                        else:
                            # 线程存活但可能连接失败，标记为连接中
                            mqtt_status = 'connecting'
                except:
                    # 如果检查失败，假设未连接
                    mqtt_status = 'stopped'
            else:
                # 客户端存在但client对象未创建，可能是初始化失败
                mqtt_status = 'stopped'
    else:
        # 线程不存在或已停止
        mqtt_status = 'stopped'
    
    mqtt_info = {
        "status": mqtt_status,
        "host": mqtt_config.get('host', '127.0.0.1'),
        "port": mqtt_config.get('port', 1883),
        "topic": mqtt_config.get('topic', 'zebra/print'),
        "client_id": mqtt_config.get('client_id')  # 如果未配置则为None
    }
    
    # 如果客户端ID未配置，尝试从MQTT客户端实例获取（可能是自动生成的）
    if not mqtt_info["client_id"] and mqtt_client and hasattr(mqtt_client, 'client_id'):
        mqtt_info["client_id"] = mqtt_client.client_id
    
    if mqtt_error:
        mqtt_info["error"] = mqtt_error
    
    # 获取打印队列状态
    queue_status = {}
    if print_queue:
        queue_status = print_queue.get_status()
    
    return JSONResponse({
        "mqtt": mqtt_info,
        "printers": {
            "count": len(printers_config),
            "configs": printers_config
        },
        "queue": queue_status
    })


@app.get("/api/queue/status")
async def get_queue_status(username: str = Depends(verify_credentials)):
    """获取打印队列状态"""
    global print_queue
    try:
        if print_queue is None:
            return JSONResponse({
                "success": False,
                "error": "打印队列未初始化"
            })
        
        status = print_queue.get_status()
        return JSONResponse({
            "success": True,
            "status": status
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f'获取队列状态失败: {str(e)}'}
        )


@app.get("/api/config")
async def get_config(username: str = Depends(verify_credentials)):
    """获取配置信息"""
    global config_manager
    if config_manager is None:
        config_manager = ConfigManager('config/printer_config.json')
    config = config_manager.load()
    
    # 不返回密码等敏感信息
    safe_config = config.copy()
    if 'web' in safe_config and 'password' in safe_config['web']:
        safe_config['web']['password'] = '***'
    if 'mqtt' in safe_config and 'password' in safe_config['mqtt']:
        safe_config['mqtt']['password'] = '***'
    
    # 获取MQTT配置（如果topic为空且设置了platform_code，会自动生成）
    mqtt_config = config_manager.get_mqtt_config()
    
    # 更新MQTT配置中的topic（如果配置中没有topic或为空，使用自动生成的值）
    if 'mqtt' in safe_config:
        # 如果配置中有topic且不为空，使用配置中的topic（用户手动设置的）
        # 如果配置中没有topic或为空，使用自动生成的主题
        if safe_config['mqtt'].get('topic') and safe_config['mqtt']['topic'].strip():
            # 使用配置文件中保存的topic（用户手动设置的）
            pass  # 保持原值
        else:
            # 使用自动生成的主题
            safe_config['mqtt']['topic'] = mqtt_config.get('topic', 'zebra/print')
    
    return JSONResponse(safe_config)


@app.post("/api/config/save")
async def save_config(
    request: Request,
    username: str = Depends(verify_credentials)
):
    """保存配置信息"""
    global config_manager, mqtt_client
    try:
        if config_manager is None:
            config_manager = ConfigManager('config/printer_config.json')
        
        # 保存旧的MQTT配置用于比较
        old_config = config_manager.load()
        old_mqtt_config = config_manager.get_mqtt_config()
        old_platform_code = old_config.get('platform_code')
        
        data = await request.json()
        if not data:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "无效的配置数据"}
            )
        
        # 处理密码字段：如果密码是***，则保留原密码
        if 'web' in data and data['web'].get('password') == '***':
            if 'web' in old_config and 'password' in old_config['web']:
                data['web']['password'] = old_config['web']['password']
        
        if 'mqtt' in data and data['mqtt'].get('password') == '***':
            if 'mqtt' in old_config and 'password' in old_config['mqtt']:
                data['mqtt']['password'] = old_config['mqtt']['password']
        
        # 保存配置到文件
        config_file = 'config/printer_config.json'
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # 重新加载配置
        config_manager = ConfigManager(config_file)
        new_mqtt_config = config_manager.get_mqtt_config()
        new_platform_code = data.get('platform_code')
        
        # 检查MQTT配置是否改变（包括platform_code改变导致的topic变化）
        mqtt_changed = False
        if old_mqtt_config.get('url') != new_mqtt_config.get('url') or \
           old_mqtt_config.get('host') != new_mqtt_config.get('host') or \
           old_mqtt_config.get('port') != new_mqtt_config.get('port') or \
           old_mqtt_config.get('topic') != new_mqtt_config.get('topic') or \
           old_mqtt_config.get('username') != new_mqtt_config.get('username') or \
           old_mqtt_config.get('password') != new_mqtt_config.get('password') or \
           old_platform_code != new_platform_code:
            mqtt_changed = True
        
        # 如果修改了MQTT配置，需要重启MQTT客户端
        if mqtt_changed:
            print("检测到MQTT配置已更改，正在重启MQTT客户端...")
            # 在后台线程中重启MQTT客户端，避免阻塞Web响应
            def restart_mqtt():
                try:
                    start_mqtt_client()
                except Exception as e:
                    print(f"重启MQTT客户端时出错: {e}")
                    import traceback
                    traceback.print_exc()
            
            restart_thread = threading.Thread(target=restart_mqtt, daemon=True, name="MQTT-Restart-Thread")
            restart_thread.start()
            message = "配置已保存，MQTT客户端正在后台重启..."
        else:
            message = "配置已保存"
        
        return JSONResponse({
            "success": True,
            "message": message,
            "mqtt_restarted": mqtt_changed
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f'保存配置失败: {str(e)}'}
        )


@app.post("/api/config/import")
async def import_config(
    file: UploadFile = File(...),
    username: str = Depends(verify_credentials)
):
    """导入配置文件"""
    global config_manager
    try:
        if not file.filename.endswith('.json'):
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "只支持JSON格式的配置文件"}
            )
        
        # 读取上传的文件
        content = await file.read()
        config_data = json.loads(content.decode('utf-8'))
        
        # 验证配置格式
        if not isinstance(config_data, dict):
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "配置文件格式错误"}
            )
        
        # 保存配置
        config_file = 'config/printer_config.json'
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)
        
        # 重新加载配置
        config_manager = ConfigManager(config_file)
        
        return JSONResponse({
            "success": True,
            "message": "配置已导入",
            "config": config_data
        })
    
    except json.JSONDecodeError:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": "JSON格式错误"}
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f'导入配置失败: {str(e)}'}
        )


@app.get("/api/config/export")
async def export_config(username: str = Depends(verify_credentials)):
    """导出配置文件"""
    global config_manager
    try:
        if config_manager is None:
            config_manager = ConfigManager('config/printer_config.json')
        
        config = config_manager.load()
        
        return JSONResponse({
            "success": True,
            "config": config,
            "filename": "printer_config.json"
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f'导出配置失败: {str(e)}'}
        )


@app.get("/api/printers/scan")
async def scan_printers(username: str = Depends(verify_credentials)):
    """扫描系统打印机列表"""
    import platform
    system = platform.system()
    printers = []
    
    try:
        if system == 'Windows':
            try:
                import win32print
                default_printer = None
                try:
                    default_printer = win32print.GetDefaultPrinter()
                except:
                    pass
                
                for printer_info in win32print.EnumPrinters(2):
                    printer_name = printer_info[2]
                    printers.append({
                        'name': printer_name,
                        'is_default': printer_name == default_printer,
                        'type': 'windows'
                    })
                
            except ImportError:
                return JSONResponse({
                    "success": False,
                    "error": "需要安装 pywin32 库: pip install pywin32",
                    "printers": []
                })
            except Exception as e:
                return JSONResponse({
                    "success": False,
                    "error": f"获取Windows打印机列表失败: {str(e)}",
                    "printers": []
                })
        
        elif system == 'Linux':
            try:
                import cups
                conn = cups.Connection()
                cups_printers = conn.getPrinters()
                default_printer = conn.getDefault()
                
                for printer_name, printer_info in cups_printers.items():
                    printers.append({
                        'name': printer_name,
                        'is_default': printer_name == default_printer,
                        'type': 'cups',
                        'info': printer_info.get('printer-info', ''),
                        'location': printer_info.get('printer-location', '')
                    })
                
            except ImportError:
                return JSONResponse({
                    "success": False,
                    "error": "需要安装 pycups 库: pip install pycups",
                    "printers": []
                })
            except Exception as e:
                return JSONResponse({
                    "success": False,
                    "error": f"获取CUPS打印机列表失败: {str(e)}",
                    "printers": []
                })
        
        else:
            return JSONResponse({
                "success": False,
                "error": f"不支持的操作系统: {system}",
                "printers": []
            })
        
        return JSONResponse({
            "success": True,
            "printers": printers,
            "count": len(printers)
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f'扫描打印机失败: {str(e)}', "printers": []}
        )


async def scheduled_log_cleanup():
    """定时清理日志任务（每天凌晨3点执行）"""
    import asyncio
    while True:
        try:
            # 计算距离下次凌晨3点的时间
            now = datetime.datetime.now()
            tomorrow_3am = now.replace(hour=3, minute=0, second=0, microsecond=0)
            if now.hour >= 3:
                tomorrow_3am += datetime.timedelta(days=1)
            
            sleep_seconds = (tomorrow_3am - now).total_seconds()
            
            print(f"日志清理任务：下次执行时间 {tomorrow_3am.strftime('%Y-%m-%d %H:%M:%S')}")
            await asyncio.sleep(sleep_seconds)
            
            # 执行清理
            print("\n" + "="*70)
            print("执行定时日志清理任务...")
            print("="*70)
            deleted_count = log_manager.clean_old_logs()
            print(f"已清理 {deleted_count} 个过期日志文件")
            print("="*70)
        
        except Exception as e:
            print(f"日志清理任务出错: {e}")
            # 出错后等待1小时再试
            await asyncio.sleep(3600)


@app.get("/api/logs")
async def get_logs(
    filename: Optional[str] = None,
    lines: int = 100,
    level: Optional[str] = None,
    search: Optional[str] = None,
    username: str = Depends(verify_credentials)
):
    """
    获取日志内容
    
    Args:
        filename: 日志文件名（可选）
        lines: 返回的日志行数（默认100）
        level: 过滤日志级别（ERROR, WARNING, INFO等）
        search: 搜索关键词
    """
    try:
        logs = log_manager.read_logs(
            filename=filename,
            lines=lines,
            level=level,
            search=search
        )
        
        return JSONResponse({
            "success": True,
            "logs": logs,
            "count": len(logs)
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f'获取日志失败: {str(e)}'}
        )


@app.get("/api/logs/files")
async def get_log_files(username: str = Depends(verify_credentials)):
    """获取日志文件列表"""
    try:
        stats = log_manager.get_log_stats()
        return JSONResponse({
            "success": True,
            "stats": stats
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f'获取日志文件列表失败: {str(e)}'}
        )


@app.get("/api/logs/stats")
async def get_log_stats(
    filename: Optional[str] = None,
    username: str = Depends(verify_credentials)
):
    """获取日志统计信息"""
    try:
        level_counts = log_manager.get_log_levels_count(filename=filename)
        return JSONResponse({
            "success": True,
            "level_counts": level_counts
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f'获取日志统计失败: {str(e)}'}
        )


@app.post("/api/logs/clean")
async def clean_old_logs(username: str = Depends(verify_credentials)):
    """手动清理过期日志"""
    try:
        deleted_count = log_manager.clean_old_logs()
        return JSONResponse({
            "success": True,
            "message": f"已清理 {deleted_count} 个过期日志文件",
            "deleted_count": deleted_count
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f'清理日志失败: {str(e)}'}
        )


@app.get("/api/examples")
async def get_examples(username: str = Depends(verify_credentials)):
    """获取示例数据列表"""
    try:
        examples_file = get_resource_path('data/test_samples/examples.json')
        if not os.path.exists(examples_file):
            return JSONResponse(
                status_code=404,
                content={"success": False, "error": f"示例配置文件不存在: {examples_file}"}
            )
        
        with open(examples_file, 'r', encoding='utf-8') as f:
            examples_config = json.load(f)
        
        return JSONResponse({
            "success": True,
            "examples": examples_config.get('examples', [])
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f'获取示例列表失败: {str(e)}'}
        )


@app.get("/api/examples/{example_id}")
async def get_example_data(example_id: str, username: str = Depends(verify_credentials)):
    """获取指定示例的数据"""
    try:
        # 特殊处理：直接读取数组格式的示例文件
        if example_id == 'escpos_raw_text_list':
            file_path = get_resource_path('data/test_samples/escpos_raw_text_list.json')
            if not os.path.exists(file_path):
                return JSONResponse(
                    status_code=404,
                    content={"success": False, "error": f"示例文件不存在: {file_path}"}
                )
            
            # 读取文件内容（数组格式）
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return JSONResponse({
                "success": True,
                "example": {
                    "id": "escpos_raw_text_list",
                    "title": "ESC/POS批量打印（数组格式）",
                    "desc": f"包含 {len(data) if isinstance(data, list) else 1} 个打印任务的数组格式示例",
                    "category": "批量打印（数组格式）"
                },
                "data": data
            })
        
        # 读取示例配置
        examples_file = get_resource_path('data/test_samples/examples.json')
        if not os.path.exists(examples_file):
            return JSONResponse(
                status_code=404,
                content={"success": False, "error": f"示例配置文件不存在: {examples_file}"}
            )
        
        with open(examples_file, 'r', encoding='utf-8') as f:
            examples_config = json.load(f)
        
        # 查找指定的示例
        example = None
        for ex in examples_config.get('examples', []):
            if ex.get('id') == example_id:
                example = ex
                break
        
        if not example:
            return JSONResponse(
                status_code=404,
                content={"success": False, "error": f"示例 '{example_id}' 不存在"}
            )
        
        # 如果示例有直接的data字段，直接返回
        if example.get('data'):
            return JSONResponse({
                "success": True,
                "example": example,
                "data": example['data']
            })
        
        # 否则从文件读取
        file_name = example.get('file')
        if not file_name:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "示例未指定数据文件"}
            )
        
        file_path = get_resource_path(os.path.join('data/test_samples', file_name))
        if not os.path.exists(file_path):
            return JSONResponse(
                status_code=404,
                content={"success": False, "error": f"示例文件 '{file_name}' 不存在: {file_path}"}
            )
        
        # 读取文件内容（统一使用JSON格式）
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return JSONResponse({
            "success": True,
            "example": example,
            "data": data
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f'获取示例数据失败: {str(e)}'}
        )


@app.post("/api/mqtt/send")
async def send_mqtt_message(
    request: Request,
    username: str = Depends(verify_credentials)
):
    """通过MQTT发送打印数据到云端"""
    global config_manager
    
    try:
        # 获取JSON数据
        data = await request.json()
        if not data:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "无效的JSON数据"}
            )
        
        # 确保config_manager已初始化
        if config_manager is None:
            config_manager = ConfigManager('config/printer_config.json')
        
        # 获取MQTT配置
        mqtt_config = config_manager.get_mqtt_config()
        broker_host = mqtt_config.get('host', '127.0.0.1')
        broker_port = mqtt_config.get('port', 1883)
        topic = mqtt_config.get('topic', 'zebra/print')
        mqtt_username = mqtt_config.get('username')
        mqtt_password = mqtt_config.get('password')
        protocol = mqtt_config.get('protocol', 'mqtt')
        url = mqtt_config.get('url')
        
        # 检查是否安装了paho-mqtt
        try:
            import paho.mqtt.client as mqtt
        except ImportError:
            return JSONResponse(
                status_code=500,
                content={"success": False, "error": "需要安装 paho-mqtt 库: pip install paho-mqtt"}
            )
        
        # 创建MQTT客户端（用于发送，不是接收）
        client_id = f"web_sender_{int(time.time())}"
        client = mqtt.Client(client_id=client_id)
        
        # 设置认证
        if mqtt_username and mqtt_password:
            client.username_pw_set(mqtt_username, mqtt_password)
        
        # 处理WebSocket协议
        if protocol in ['ws', 'wss']:
            transport = "websockets"
            client = mqtt.Client(client_id=client_id, transport=transport)
            if mqtt_username and mqtt_password:
                client.username_pw_set(mqtt_username, mqtt_password)
            
            # 设置WebSocket路径
            ws_path = '/mqtt'
            if url:
                try:
                    from urllib.parse import urlparse
                    parsed = urlparse(url)
                    if parsed.path:
                        ws_path = parsed.path
                except:
                    pass
            client.ws_set_options(path=ws_path)
        
        # 处理SSL/TLS
        if protocol in ['wss', 'mqtts']:
            try:
                client.tls_set()
            except:
                try:
                    import ssl
                    client.tls_set(cert_reqs=ssl.CERT_NONE)
                except:
                    pass
        
        # 连接MQTT服务器
        try:
            client.connect(broker_host, broker_port, 60)
            client.loop_start()
            
            # 等待连接建立
            timeout = 5
            start_time = time.time()
            while not client.is_connected() and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            if not client.is_connected():
                client.loop_stop()
                client.disconnect()
                return JSONResponse(
                    status_code=500,
                    content={"success": False, "error": f"无法连接到MQTT服务器 {broker_host}:{broker_port}"}
                )
            
            # 发送消息
            message_json = json.dumps(data, ensure_ascii=False)
            result = client.publish(topic, message_json, qos=0)
            
            # 等待消息发送完成
            result.wait_for_publish(timeout=2)
            
            # 断开连接
            client.loop_stop()
            client.disconnect()
            
            if result.rc == 0:
                print(f"\n[MQTT发送] 成功发送到 {broker_host}:{broker_port}/{topic}")
                print(f"  消息长度: {len(message_json)} 字节")
                return JSONResponse({
                    "success": True,
                    "message": f"数据已成功发送到MQTT服务器",
                    "mqtt_info": {
                        "host": broker_host,
                        "port": broker_port,
                        "topic": topic,
                        "message_id": result.mid
                    }
                })
            else:
                return JSONResponse(
                    status_code=500,
                    content={"success": False, "error": f"MQTT发送失败，错误码: {result.rc}"}
                )
        
        except Exception as conn_error:
            try:
                client.loop_stop()
                client.disconnect()
            except:
                pass
            return JSONResponse(
                status_code=500,
                content={"success": False, "error": f"MQTT连接失败: {str(conn_error)}"}
            )
    
    except json.JSONDecodeError:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": "JSON格式错误"}
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f'处理请求时出错: {str(e)}'}
        )


if __name__ == '__main__':
    # 确保目录存在
    ensure_directories()
    
    # 检查配置文件
    config_file = 'config/printer_config.json'
    if not os.path.exists(config_file):
        print(f"配置文件不存在，正在创建默认配置...")
        create_default_config(config_file)
    
    # 初始化配置管理器（如果还未初始化）
    if config_manager is None:
        config_manager = ConfigManager(config_file)
    
    # 启动MQTT客户端（后台）
    print("=" * 70)
    print(" " * 20 + "打印机Web服务")
    print("=" * 70)
    print(f"系统: {platform.system()} {platform.machine()}")
    print(f"Python: {sys.version.split()[0]}")
    print("=" * 70)
    print()
    
    start_mqtt_client()
    
    print("\n" + "=" * 70)
    print("Web服务启动中...")
    print("访问地址: http://127.0.0.1:5000")
    print("=" * 70)
    print()
    
    # 启动FastAPI应用
    try:
        uvicorn.run(app, host="0.0.0.0", port=5000, log_level="info")
    except KeyboardInterrupt:
        print("\n\nWeb服务已停止")
