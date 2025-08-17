#!/usr/bin/env python3
"""
调试会话管理问题
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

import requests
import json
from datetime import datetime, timedelta
from app import create_app
from app.models import User
from app.utils.session_manager import session_manager
from app.extensions import db
from flask_jwt_extended import create_access_token, create_refresh_token, decode_token

def debug_session_management():
    """调试会话管理"""
    app = create_app()
    
    with app.app_context():
        # 清理数据库
        db.drop_all()
        db.create_all()
        
        # 创建测试用户
        test_user = User(
            email='test@example.com',
            username='testuser',
            role='student',
            is_active=True
        )
        test_user.set_password('password123')
        db.session.add(test_user)
        db.session.commit()
        
        print(f"Created test user: {test_user.email} (ID: {test_user.id})")
        
        # 创建tokens
        access_token = create_access_token(identity=test_user.id)
        refresh_token = create_refresh_token(identity=test_user.id)
        
        print(f"Created access token: {access_token[:50]}...")
        print(f"Created refresh token: {refresh_token[:50]}...")
        
        # 解码tokens获取JTI
        access_claims = decode_token(access_token)
        refresh_claims = decode_token(refresh_token)
        
        access_jti = access_claims['jti']
        refresh_jti = refresh_claims['jti']
        
        print(f"Access token JTI: {access_jti}")
        print(f"Refresh token JTI: {refresh_jti}")
        print(f"Access token expires: {datetime.fromtimestamp(access_claims['exp'])}")
        print(f"Refresh token expires: {datetime.fromtimestamp(refresh_claims['exp'])}")
        
        # 模拟登录过程中的会话创建
        with app.test_request_context('/', headers={'User-Agent': 'Test Client'}):
            # 创建access token会话
            access_session = session_manager.create_session(test_user, access_jti)
            print(f"\nCreated access session:")
            print(f"  Session ID: {access_session.session_id}")
            print(f"  User ID: {access_session.user_id}")
            print(f"  Login time: {access_session.login_time}")
            print(f"  Expires at: {access_session.expires_at}")
            print(f"  Status: {access_session.status}")
            
            # 创建refresh token会话
            refresh_session = session_manager.create_session(test_user, refresh_jti)
            print(f"\nCreated refresh session:")
            print(f"  Session ID: {refresh_session.session_id}")
            print(f"  User ID: {refresh_session.user_id}")
            print(f"  Login time: {refresh_session.login_time}")
            print(f"  Expires at: {refresh_session.expires_at}")
            print(f"  Status: {refresh_session.status}")
            
            # 检查会话是否过期
            print(f"\nCurrent time: {datetime.utcnow()}")
            print(f"Access session expired: {session_manager._is_session_expired(access_session)}")
            print(f"Refresh session expired: {session_manager._is_session_expired(refresh_session)}")
            
            # 验证会话
            print(f"\nValidating sessions:")
            access_valid = session_manager.validate_session(access_jti)
            refresh_valid = session_manager.validate_session(refresh_jti)
            print(f"Access session valid: {access_valid}")
            print(f"Refresh session valid: {refresh_valid}")
            
            # 检查活跃会话
            print(f"\nActive sessions count: {len(session_manager.active_sessions)}")
            for sid, sinfo in session_manager.active_sessions.items():
                print(f"  Session {sid}: User {sinfo.user_id}, Status {sinfo.status}, Expires {sinfo.expires_at}")

if __name__ == '__main__':
    debug_session_management()