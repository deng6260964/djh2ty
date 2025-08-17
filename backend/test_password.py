#!/usr/bin/env python3
from app import create_app
from app.models import User
from app.utils.auth import hash_password, verify_password
from app import db

app = create_app('testing')

with app.app_context():
    # 创建数据库表
    db.create_all()
    print('Testing password verification:')
    password = 'TestPass123!'
    hashed = hash_password(password)
    print(f'Original password: {password}')
    print(f'Hash: {hashed}')
    print(f'Verify result: {verify_password(password, hashed)}')
    
    # 测试创建用户和验证
    test_email = 'test@example.com'
    user = User(
        email=test_email,
        name='Test User',
        password_hash=hashed,
        role='student',
        is_active=True
    )
    db.session.add(user)
    db.session.commit()
    
    # 验证用户密码
    saved_user = User.query.filter_by(email=test_email).first()
    if saved_user:
        print(f'User found: {saved_user.email}')
        print(f'Password verification: {verify_password(password, saved_user.password_hash)}')
    else:
        print('User not found')