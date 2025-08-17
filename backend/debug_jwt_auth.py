#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试JWT认证和权限验证问题
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token, decode_token
import json
from datetime import datetime, timedelta

# 导入应用配置
from config.config import Config
from app.database import db
from app.models.user import User
from app.utils.permissions import Permission, PermissionManager

def create_test_app():
    """创建测试应用"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # 初始化数据库
    db.init_app(app)
    
    # 初始化JWT
    jwt = JWTManager(app)
    
    return app

def test_jwt_token_generation():
    """测试JWT token生成"""
    app = create_test_app()
    
    with app.app_context():
        # 创建测试用户数据
        user_data = {
            'id': 1,
            'email': 'admin@test.com',
            'role': 'admin',
            'is_active': True
        }
        
        # 生成JWT token
        token = create_access_token(
            identity=str(user_data['id']),
            additional_claims={
                'role': user_data['role'],
                'email': user_data['email'],
                'is_active': user_data['is_active']
            }
        )
        
        print(f"Generated JWT token: {token[:50]}...")
        
        # 解码token验证内容
        try:
            decoded = decode_token(token)
            print("\nDecoded token:")
            print(json.dumps(decoded, indent=2, default=str))
            
            # 检查claims
            print("\nToken claims:")
            print(f"Identity: {decoded.get('sub')}")
            print(f"Role: {decoded.get('role')}")
            print(f"Email: {decoded.get('email')}")
            print(f"Is Active: {decoded.get('is_active')}")
            
            return token, decoded
            
        except Exception as e:
            print(f"Error decoding token: {e}")
            return None, None

def test_permission_check():
    """测试权限检查"""
    print("\n=== Testing Permission Check ===")
    
    # 测试不同角色的权限
    roles = ['admin', 'teacher', 'student']
    permission = Permission.PRACTICE_VIEW_STATS
    
    for role in roles:
        has_perm = PermissionManager.has_permission(role, permission)
        print(f"Role '{role}' has permission '{permission.value}': {has_perm}")

def test_database_user_creation():
    """测试数据库用户创建"""
    app = create_test_app()
    
    with app.app_context():
        try:
            # 创建所有表
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
            
            print(f"\n=== Database User Created ===")
            print(f"User ID: {admin_user.id}")
            print(f"User Email: {admin_user.email}")
            print(f"User Role: {admin_user.role}")
            print(f"User Role Type: {type(admin_user.role)}")
            print(f"User Is Active: {admin_user.is_active}")
            
            # 查询用户验证
            queried_user = db.session.query(User).filter_by(id=admin_user.id).first()
            if queried_user:
                print(f"\nQueried User:")
                print(f"ID: {queried_user.id}")
                print(f"Email: {queried_user.email}")
                print(f"Role: {queried_user.role}")
                print(f"Is Active: {queried_user.is_active}")
            else:
                print("User not found in database!")
                
            return admin_user
            
        except Exception as e:
            print(f"Error creating user: {e}")
            return None
        finally:
            db.session.remove()
            db.drop_all()

def main():
    """主函数"""
    print("=== JWT Authentication Debug ===")
    
    # 测试权限检查
    test_permission_check()
    
    # 测试JWT token生成
    token, decoded = test_jwt_token_generation()
    
    # 测试数据库用户创建
    user = test_database_user_creation()
    
    print("\n=== Debug Complete ===")

if __name__ == '__main__':
    main()