import requests
import tempfile
import os

# 创建临时文件
with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
    f.write('test content')
    temp_path = f.name

try:
    print('Testing file upload...')
    with open(temp_path, 'rb') as file:
        response = requests.post(
            'http://localhost:5000/api/files/upload',
            files={'file': file},
            data={'category': 'other'},
            headers={'Authorization': 'Bearer test'}
        )
    print(f'Status: {response.status_code}')
    print(f'Response: {response.text}')
finally:
    # 清理临时文件
    if os.path.exists(temp_path):
        os.unlink(temp_path)