#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试文件上传API的脚本
"""

import requests
import tempfile
import os
import json
import sys
sys.path.append('.')
from app import create_app, db
from app.models.user import User
from app.utils.auth import hash_password
import uuid

def debug_file_upload():
    """调试文件上传API"""
    print("正在调试文件上传API...")
    
    # 创建应用上下文并创建测试用户到开发数据库
    app = create_app('development')  # 使用开发环境配置
    with app.app_context():
        # 创建测试用户到开发数据库
        unique_email = f'debug_user_{uuid.uuid4().hex[:8]}@example.com'
        
        # 检查用户是否已存在
        existing_user = User.query.filter_by(email=unique_email).first()
        if not existing_user:
            user = User(
                email=unique_email,
                name='Debug User',
                password_hash=hash_password('TestPass123!'),
                role='student',
                is_active=True
            )
            db.session.add(user)
            db.session.commit()
            print(f"创建测试用户: {unique_email}")
        else:
            print(f"用户已存在: {unique_email}")
    
    base_url = 'http://localhost:5000'
    
    # 登录获取token
    login_data = {
        'email': unique_email,
        'password': 'TestPass123!'
    }
    
    print("正在登录...")
    response = requests.post(f'{base_url}/api/auth/login', json=login_data)
    print(f"登录响应状态码: {response.status_code}")
    print(f"登录响应数据: {response.json()}")
    
    if response.status_code != 200:
        print("登录失败")
        return
    
    token = response.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    
    # 2. 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write('Test file content for debugging')
        temp_file_path = f.name
    
    try:
        # 3. 上传文件
        print("\n正在上传文件...")
        with open(temp_file_path, 'rb') as f:
            files = {'file': ('test.txt', f, 'text/plain')}
            data = {'category': 'homework_attachment'}
            
            response = requests.post(
                f'{base_url}/api/files/upload',
                files=files,
                data=data,
                headers=headers
            )
        
        print(f"文件上传响应状态码: {response.status_code}")
        print(f"文件上传响应数据: {response.text}")
        
        if response.status_code == 201:
            print("文件上传成功!")
            file_data = response.json()
            print(f"文件信息: {json.dumps(file_data, indent=2, ensure_ascii=False)}")
        else:
            print(f"文件上传失败: {response.status_code}")
            try:
                error_data = response.json()
                print(f"错误信息: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            except:
                print(f"原始响应: {response.text}")
    
    finally:
        # 清理临时文件
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

if __name__ == '__main__':
    debug_file_upload()