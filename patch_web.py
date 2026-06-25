import re

with open(r'e:\WPS\Label\label-printing-server\web_app.py', 'r', encoding='utf-8') as f:
    content = f.read()

insertion = """

def _verify_api_key(api_key_from_body, request):
    \"\"\"认证：body api_key 或 header token 任一匹配即通过\"\"\"
    global config_manager
    if config_manager is None:
        config_manager = ConfigManager('config/printer_config.json')
    config = config_manager.load()
    expected = config.get('web', {}).get('api_token', '')
    if not expected:
        return True
    if api_key_from_body == expected:
        return True
    token = request.headers.get('X-API-Token', '')
    if token == expected:
        return True
    auth = request.headers.get('Authorization', '')
    if auth.startswith('Bearer ') and auth[7:] == expected:
        return True
    return False
"""

old = '\n\n\ndef allowed_file(filename):'
new = insertion + '\ndef allowed_file(filename):'

if old in content:
    content = content.replace(old, new, 1)
    with open(r'e:\WPS\Label\label-printing-server\web_app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('SUCCESS')
else:
    print('FAIL: pattern not found')
