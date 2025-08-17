#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试500错误的简化脚本
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app
from app.models.user import User
from app.models.course import Course
from app.models.question import Question, QuestionBank
from app.models.practice import Practice
from app.models.practice_question import PracticeQuestion
from app.models.practice_session import PracticeSession
from app.models.practice_answer import PracticeAnswer
from app.database import db
from flask_jwt_extended import create_access_token
import json

def test_500_error():
    """测试500错误"""
    app = create_app('testing')
    
    with app.app_context():
        try:
            # 创建所有表
            db.create_all()
            
            # 创建测试数据
            admin_user = User(
                name='admin_test',
                email='admin@test.com',
                password_hash='hashed_password',
                role='admin',
                is_active=True
            )
            
            student_user = User(
                name='student_test',
                email='student@test.com',
                password_hash='hashed_password',
                role='student',
                is_active=True
            )
            
            db.session.add(admin_user)
            db.session.add(student_user)
            db.session.commit()
            
            # 创建课程
            course = Course(
                name='测试课程',
                description='测试课程描述',
                course_type='one_to_many',
                teacher_id=admin_user.id,
                is_active=True
            )
            db.session.add(course)
            db.session.commit()
            
            # 创建题库
            question_bank = QuestionBank(
                name='测试题库',
                description='测试题库描述',
                category='语法',
                difficulty_level='beginner',
                created_by=admin_user.id,
                is_public=True
            )
            db.session.add(question_bank)
            db.session.commit()
            
            # 创建题目
            question = Question(
                question_bank_id=question_bank.id,
                question_type='multiple_choice',
                title='测试题目',
                content='这是一个测试题目',
                options='{"A": "选项A", "B": "选项B", "C": "选项C", "D": "选项D"}',
                correct_answer='A',
                difficulty_level='beginner',
                created_by=admin_user.id
            )
            db.session.add(question)
            db.session.commit()
            
            # 创建练习
            practice = Practice(
                title='测试练习',
                description='这是一个测试练习',
                creator_id=admin_user.id,
                status='published'
            )
            db.session.add(practice)
            db.session.commit()
            
            # 创建练习题目关联
            practice_question = PracticeQuestion(
            practice_id=practice.id,
            question_id=question.id,
            order_index=1
        )
            db.session.add(practice_question)
            db.session.commit()
            
            # 生成JWT token
            admin_token = create_access_token(
                identity=str(admin_user.id),
                additional_claims={
                    'role': admin_user.role,
                    'email': admin_user.email,
                    'is_active': admin_user.is_active
                }
            )
            
            # 测试客户端
            client = app.test_client()
            
            print("测试获取练习统计...")
            response = client.get(
                f'/api/practices/{practice.id}/statistics',
                headers={'Authorization': f'Bearer {admin_token}'}
            )
            print(f"状态码: {response.status_code}")
            if response.status_code != 200:
                print(f"错误响应: {response.get_json()}")
                print(f"错误数据: {response.get_data(as_text=True)}")
            else:
                print(f"成功响应: {response.get_json()}")
                
        except Exception as e:
            print(f"测试过程中发生错误: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # 清理数据库
            db.session.rollback()
            db.drop_all()

if __name__ == '__main__':
    test_500_error()