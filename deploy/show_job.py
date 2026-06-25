import json, re

f = '/www/label-print-server/data/pending_jobs/job_20260625_162139_ed78f0.json'
d = json.load(open(f))
print('Title:', d.get('title'))
print('Barcode:', d.get('barcode'))
print('Fields_count:', d.get('fields_count'))
print('File_size:', len(json.dumps(d)), 'chars')
print()

zpl = d.get('zpl_code', '')

# 只显示 ^FO 坐标和非全零的 GFA
blocks = re.split(r'(\^FO\d+,\d+)', zpl)
for i, b in enumerate(blocks):
    if b.startswith('^FO'):
        next_block = blocks[i+1] if i+1 < len(blocks) else ''
        # 检查是否是非零GFA（即有实际内容的图像）
        gfa = re.search(r'\^GFA,\d+,\d+,\d+,([0-9A-F]+)\^FS', next_block)
        fd = re.search(r'\^FD(.+?)\^FS', next_block)
        if gfa:
            hex_data = gfa.group(1)
            has_content = hex_data.strip('0')
            if has_content:
                # 有内容的图像 - 显示摘要
                print(b, f'[IMAGE {len(hex_data)//2} bytes]')
            else:
                print(b, '[BLANK IMAGE]')
        elif fd:
            print(b, fd.group(1)[:100])
