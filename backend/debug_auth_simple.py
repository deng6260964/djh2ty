#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的JWT认证调试脚本
用于测试权限装饰器的具体行为
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.database import db
from app.models.user import User
from flask_jwt_extended import create_access_token
import json

def test_auth_decorators():
    """测试认证装饰器"""
    app = create_app('testing')
    
    with app.app_context():
        # 创建数据库表
        db.create_all()
        
        # 创建测试用户
        admin_user = User(
            name='admin_test',
            email='admin@test.com',
            password_hash='hashed_password',
            role='admin'
        )
        db.session.add(admin_user)
        db.session.commit()
        
        # 生成JWT token
        token = create_access_token(
            identity=str(admin_user.id),
            additional_claims={
                'role': admin_user.role,
                'email': admin_user.email,
                'is_active': admin_user.is_active
            }
        )
        
        print(f"Generated token: {token[:50]}...")
        
        # 测试API调用
        client = app.test_client()
        
        # 测试无token访问
        print("\n=== 测试无token访问 ===")
        response = client.get('/api/practices/1/statistics')
        print(f"Status: {response.status_code}")
        print(f"Response: {response.get_json()}")
        
        # 测试有token访问
        print("\n=== 测试有token访问 ===")
        response = client.get(
            '/api/practices/1/statistics',
            headers={'Authorization': f'Bearer {token}'}
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.get_json()}")
        
        # 测试错误token
        print("\n=== 测试错误token ===")
        response = client.get(
            '/api/practices/1/statistics',
            headers={'Authorization': 'Bearer invalid_token'}
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.get_json()}")
        
        # 清理
        db.drop_all()

if __name__ == '__main__':
    test_auth_decorators()