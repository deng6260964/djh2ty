#!/usr/bin/env python3
"""
调试用户ID分配问题的脚本
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.database import db
from app.models.user import User
from app.utils.auth import hash_password
from datetime import datetime
import uuid

def debug_user_creation():
    """调试用户创建和ID分配"""
    app = create_app('testing')
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'JWT_SECRET_KEY': 'test-secret-key',
        'SECRET_KEY': 'test-secret-key',
        'WTF_CSRF_ENABLED': False
    })
    
    with app.app_context():
        db.create_all()
        
        print("=== 模拟测试场景 ===")
        
        # 模拟第一个测试创建用户（类似test_user fixture）
        user1_email = f'test_user_{uuid.uuid4().hex[:8]}@example.com'
        user1 = User(
            email=user1_email,
            name='Test User 1',
            password_hash=hash_password('TestPass123!'),
            role='student',
            is_active=True,
            created_at=datetime.utcnow()
        )
        db.session.add(user1)
        db.session.commit()
        print(f"User 1 created: ID={user1.id}, Email={user1.email}")
        
        # 模拟第二个测试创建用户（类似auth_headers fixture）
        user2_email = f'auth_test_{uuid.uuid4().hex[:8]}@example.com'
        user2 = User(
            email=user2_email,
            name='Auth Test User',
            password_hash=hash_password('TestPass123!'),
            role='student',
            is_active=True,
            created_at=datetime.utcnow()
        )
        db.session.add(user2)
        db.session.commit()
        print(f"User 2 created: ID={user2.id}, Email={user2.email}")
        
        # 模拟数据库清理
        print("\n=== 模拟数据库清理 ===")
        for table in reversed(db.metadata.sorted_tables):
            db.session.execute(table.delete())
        db.session.commit()
        
        # 重置SQLite的自增ID计数器
        try:
            result = db.session.execute(db.text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='sqlite_sequence'"
            )).fetchone()
            if result:
                db.session.execute(db.text("DELETE FROM sqlite_sequence"))
                db.session.commit()
                print("sqlite_sequence 已重置")
        except Exception as e:
            print(f"重置sqlite_sequence失败: {e}")
        
        # 清理SQLAlchemy的Identity Map缓存
        db.session.expunge_all()
        
        # 再次创建用户，看看ID是否重置
        print("\n=== 清理后重新创建用户 ===")
        user3_email = f'new_test_{uuid.uuid4().hex[:8]}@example.com'
        user3 = User(
            email=user3_email,
            name='New Test User',
            password_hash=hash_password('TestPass123!'),
            role='student',
            is_active=True,
            created_at=datetime.utcnow()
        )
        db.session.add(user3)
        db.session.commit()
        print(f"User 3 created: ID={user3.id}, Email={user3.email}")
        
        # 检查所有用户
        print("\n=== 当前数据库中的所有用户 ===")
        all_users = User.query.all()
        for user in all_users:
            print(f"ID={user.id}, Email={user.email}, Name={user.name}")

if __name__ == '__main__':
    debug_user_creation()