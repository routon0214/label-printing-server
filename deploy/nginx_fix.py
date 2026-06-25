conf = open('/etc/nginx/sites-enabled/iot.klxzdh.com.conf', 'r').read()
snippet = open('/tmp/nginx_snippet.conf', 'r').read()

# Insert snippet before the first "location /wps-api/" block
old = '    location /wps-api/ {'
new = snippet + '\n' + old
conf = conf.replace(old, new, 1)

open('/etc/nginx/sites-enabled/iot.klxzdh.com.conf', 'w').write(conf)
print('DONE')
