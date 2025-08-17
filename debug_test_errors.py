#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试测试错误脚本
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app
from app.models.user import User
from app.models.course import Course
from app.models.question import Question
from app.models.practice import Practice
from app.models.practice_question import PracticeQuestion
from app.models.practice_session import PracticeSession
from app.models.practice_answer import PracticeAnswer
from app.database import db
from flask_jwt_extended import create_access_token
import json

def test_practice_statistics():
    """测试练习统计API"""
    app = create_app('testing')
    
    with app.app_context():
        # 创建数据库表
        db.create_all()
        
        try:
            # 创建测试数据
            admin_user = User(
                name='admin_test',
                email='admin@test.com',
                password_hash='hashed_password',
                role='admin',
                is_active=True
            )
            db.session.add(admin_user)
            db.session.commit()
            
            # 生成JWT token
            additional_claims = {
                'role': 'admin',
                'email': 'admin@test.com',
                'is_active': True
            }
            admin_token = create_access_token(
                identity=str(admin_user.id),
                additional_claims=additional_claims
            )
            
            # 创建测试客户端
            client = app.test_client()
            
            # 测试获取练习统计
            print("测试获取练习统计...")
            response = client.get(
                '/api/practices/1/statistics',
                headers={'Authorization': f'Bearer {admin_token}'}
            )
            
            print(f"状态码: {response.status_code}")
            print(f"响应: {response.get_json()}")
            
            if response.status_code != 200:
                print(f"错误: {response.get_data(as_text=True)}")
            
            # 测试获取用户个人统计
            print("\n测试获取用户个人统计...")
            response = client.get(
                f'/api/users/{admin_user.id}/practice-statistics',
                headers={'Authorization': f'Bearer {admin_token}'}
            )
            
            print(f"状态码: {response.status_code}")
            print(f"响应: {response.get_json()}")
            
            if response.status_code != 200:
                print(f"错误: {response.get_data(as_text=True)}")
                
        except Exception as e:
            print(f"测试过程中发生错误: {str(e)}")
            import traceback
            traceback.print_exc()
        
        finally:
            # 清理数据库
            db.drop_all()

if __name__ == '__main__':
    test_practice_statistics()