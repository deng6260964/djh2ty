#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
from app import create_app
from app.models import User
from app import db
from werkzeug.security import generate_password_hash
from datetime import datetime

def test_api_response():
    """测试API响应格式"""
    app = create_app()
    
    with app.test_client() as client:
        with app.app_context():
            # 创建测试用户
            test_user = User(
                name='test_teacher',
                email='test_teacher@example.com',
                password_hash=generate_password_hash('TestPass123!'),
                role='teacher',
                is_active=True,
                created_at=datetime.utcnow()
            )
            db.session.add(test_user)
            db.session.commit()
            
            # 登录获取token
            login_response = client.post('/api/auth/login', json={
                'email': 'test_teacher@example.com',
                'password': 'TestPass123!'
            })
            
            print(f"Login response status: {login_response.status_code}")
            print(f"Login response data: {login_response.get_json()}")
            
            if login_response.status_code == 200:
                access_token = login_response.get_json()['access_token']
                headers = {'Authorization': f'Bearer {access_token}'}
                
                # 测试获取题库列表
                response = client.get('/api/questions/banks', headers=headers)
                print(f"\nQuestion banks response status: {response.status_code}")
                print(f"Question banks response data: {response.get_json()}")
                print(f"Question banks response headers: {dict(response.headers)}")
                
                # 测试创建题库
                bank_data = {
                    'name': 'Test Bank',
                    'description': 'Test Description',
                    'category': 'math',
                    'difficulty_level': 'beginner',
                    'is_public': True
                }
                
                create_response = client.post('/api/questions/banks', json=bank_data, headers=headers)
                print(f"\nCreate bank response status: {create_response.status_code}")
                print(f"Create bank response data: {create_response.get_json()}")
                print(f"Create bank response headers: {dict(create_response.headers)}")

if __name__ == '__main__':
    test_api_response()