#!/usr/bin/env python3
"""Update Nginx config to add WPS print proxy"""
import shutil

config_path = '/etc/nginx/sites-enabled/iot.klxzdh.com.conf'
backup_path = config_path + '.bak.20260625'

# Backup
shutil.copy(config_path, backup_path)
print(f'Backup: {backup_path}')

with open(config_path, 'r') as f:
    content = f.read()

# 1. On port 80: Add /api/print/ before the return 301
port80_insert = '''    # ========== 标签打印服务 (WPS 一键打印) ==========
    location /api/print/ {
        proxy_pass http://127.0.0.1:8090/api/print/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_connect_timeout 30s;
        proxy_read_timeout 30s;
    }

'''
content = content.replace(
    '    location /.well-known/acme-challenge/ {\n        root /var/www/html;\n    }\n\n    location / {\n        return 301 https://$host$request_uri;\n    }',
    port80_insert + '    location /.well-known/acme-challenge/ {\n        root /var/www/html;\n    }\n\n    location / {\n        return 301 https://$host$request_uri;\n    }'
)

# 2. On port 443: Add /api/print/ before /api/load-template
port443_insert = '''    # ========== 标签打印服务 (WPS 一键打印) ==========
    location /api/print/ {
        proxy_pass http://127.0.0.1:8090/api/print/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_connect_timeout 30s;
        proxy_read_timeout 30s;
    }

    # ========== 标签打印 API ========== 
'''
content = content.replace(
    '    # ========== 标签打印 API ========== \n    location /api/load-template {',
    port443_insert + '    location /api/load-template {'
)

with open(config_path, 'w') as f:
    f.write(content)

print('Nginx config updated successfully')
