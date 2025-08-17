#!/usr/bin/env python3
import pytest
from app import create_app, db
from app.models import User
from app.utils.auth import hash_password
import uuid
import json

def test_login_debug():
    """调试登录问题"""
    app = create_app('testing')
    
    with app.test_client() as client:
        with app.app_context():
            # 创建数据库表
            db.create_all()
            
            # 创建测试用户
            unique_email = f'debug_user_{uuid.uuid4().hex[:8]}@example.com'
            password = 'TestPass123!'
            password_hash = hash_password(password)
            
            print(f"Creating user with email: {unique_email}")
            print(f"Password: {password}")
            print(f"Password hash: {password_hash}")
            
            user = User(
                email=unique_email,
                name='Debug User',
                password_hash=password_hash,
                role='student',
                is_active=True
            )
            db.session.add(user)
            db.session.commit()
            
            # 验证用户已保存
            saved_user = User.query.filter_by(email=unique_email).first()
            print(f"User saved: {saved_user is not None}")
            if saved_user:
                print(f"Saved user email: {saved_user.email}")
                print(f"Saved user active: {saved_user.is_active}")
                print(f"Saved user role: {saved_user.role}")
                print(f"Saved password hash: {saved_user.password_hash}")
                
                # 验证密码
                from app.utils.auth import verify_password
                password_valid = verify_password(password, saved_user.password_hash)
                print(f"Password verification: {password_valid}")
            
            # 尝试登录
            print("\nAttempting login...")
            login_data = {
                'email': unique_email,
                'password': password
            }
            
            response = client.post('/api/auth/login', 
                                 data=json.dumps(login_data),
                                 content_type='application/json')
            
            print(f"Login response status: {response.status_code}")
            print(f"Login response data: {response.get_json()}")
            
            if response.status_code == 200:
                print("Login successful!")
                return True
            else:
                print("Login failed!")
                return False

if __name__ == '__main__':
    success = test_login_debug()
    print(f"\nTest result: {'PASS' if success else 'FAIL'}")