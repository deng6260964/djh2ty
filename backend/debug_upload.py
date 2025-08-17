#!/usr/bin/env python3
"""调试文件上传308重定向问题"""

import requests
import tempfile
import os
from app import create_app
from app.database import db
from app.models.user import User
from app.models.course import Course
from werkzeug.security import generate_password_hash
from datetime import datetime

def test_upload_debug():
    """调试文件上传问题"""
    app = create_app('testing')
    
    with app.test_client() as client:
        with app.app_context():
            # 创建测试数据
            db.create_all()
            
            # 直接测试文件上传，不需要登录
            # 创建一个模拟的Authorization头
            headers = {'Authorization': 'Bearer fake_token_for_testing'}
            
            # 跳过登录验证，直接测试URL重定向
            print("跳过登录，直接测试文件上传URL重定向问题")
            login_response = type('obj', (object,), {'status_code': 200, 'get_json': lambda: {'access_token': 'fake_token'}})()
            
            print(f"模拟登录状态码: {login_response.status_code}")
            
            # 创建临时文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write('Test file content for upload')
                temp_file_path = f.name
            
            try:
                # 测试 /api/files/upload (不带斜杠)
                print("\n=== 测试 /api/files/upload (不带斜杠) ===")
                with open(temp_file_path, 'rb') as f:
                    data = {
                        'file': (f, 'test.txt', 'text/plain'),
                        'assignment_id': '1'
                    }
                    response1 = client.post('/api/files/upload', 
                                           data=data, 
                                           headers=headers)
                
                print(f"状态码: {response1.status_code}")
                print(f"响应头: {dict(response1.headers)}")
                try:
                    print(f"响应数据: {response1.get_json()}")
                except:
                    print(f"响应文本: {response1.get_data(as_text=True)}")
                
                # 测试 /api/files/upload/ (带斜杠)
                print("\n=== 测试 /api/files/upload/ (带斜杠) ===")
                with open(temp_file_path, 'rb') as f:
                    data = {
                        'file': (f, 'test.txt', 'text/plain'),
                        'assignment_id': '1'
                    }
                    response2 = client.post('/api/files/upload/', 
                                           data=data, 
                                           headers=headers)
                
                print(f"状态码: {response2.status_code}")
                print(f"响应头: {dict(response2.headers)}")
                try:
                    print(f"响应数据: {response2.get_json()}")
                except:
                    print(f"响应文本: {response2.get_data(as_text=True)}")
                    
            finally:
                # 清理临时文件
                os.unlink(temp_file_path)

if __name__ == '__main__':
    test_upload_debug()