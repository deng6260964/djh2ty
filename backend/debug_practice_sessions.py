#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试练习会话API的脚本
"""

import sys
import os
import traceback
import json
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.database import db
from app.models.user import User
from app.models.course import Course
from app.models.question import Question, QuestionBank
from app.models.practice import Practice
from app.models.practice_question import PracticeQuestion
from app.utils.jwt_middleware import JWTMiddleware

def debug_start_practice():
    """调试开始练习功能"""
    app = create_app()
    
    with app.app_context():
        try:
            # 创建数据库表
            db.create_all()
            
            # 创建测试用户
            student_user = User(
                name="student",
                email="student@test.com",
                password_hash="hashed_password",
                role="student"
            )
            teacher_user = User(
                name="teacher",
                email="teacher@test.com",
                password_hash="hashed_password",
                role="teacher"
            )
            
            db.session.add(student_user)
            db.session.add(teacher_user)
            db.session.commit()
            
            # 创建测试课程
            course = Course(
                name="Test Course",
                description="Test Description",
                course_type="one_to_many",
                teacher_id=teacher_user.id
            )
            db.session.add(course)
            db.session.commit()
            
            # 创建测试题库
            question_bank = QuestionBank(
                name="Test Question Bank",
                description="Test Description",
                category="test",
                difficulty_level="beginner",
                created_by=teacher_user.id
            )
            db.session.add(question_bank)
            db.session.commit()
            
            # 创建测试题目
            question = Question(
                question_bank_id=question_bank.id,
                question_type="multiple_choice",
                title="Test Question",
                content="Test question content?",
                correct_answer="A",
                points=10,
                difficulty_level="beginner",
                created_by=teacher_user.id
            )
            db.session.add(question)
            db.session.commit()
            
            # 创建测试练习
            practice = Practice(
                title="Test Practice",
                description="Test practice description",
                course_id=course.id,
                creator_id=teacher_user.id,
                status="published",
                settings={"time_limit": 60, "show_answer": True}
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
            
            print(f"创建的数据:")
            print(f"- 练习ID: {practice.id}")
            print(f"- 题目ID: {question.id}")
            print(f"- 练习题目关联ID: {practice_question.id}")
            
            # 生成JWT token
            jwt_middleware = JWTMiddleware()
            student_tokens = jwt_middleware.generate_tokens(student_user)
            student_token = student_tokens['access_token']
            
            # 测试客户端
            with app.test_client() as client:
                # 测试开始练习
                headers = {'Authorization': f'Bearer {student_token}'}
                data = {'practice_id': practice.id}
                
                print(f"\n发送请求:")
                print(f"- URL: /api/practice-sessions/")
                print(f"- Headers: {headers}")
                print(f"- Data: {data}")
                
                response = client.post(
                    '/api/practice-sessions/',
                    headers=headers,
                    json=data
                )
                
                print(f"\n响应结果:")
                print(f"- 状态码: {response.status_code}")
                print(f"- 响应数据: {response.get_json()}")
                
                if response.status_code != 201:
                    print(f"\n错误详情:")
                    print(f"- 响应文本: {response.get_data(as_text=True)}")
                    
        except Exception as e:
            print(f"\n发生错误: {str(e)}")
            print(f"错误类型: {type(e).__name__}")
            print(f"错误堆栈:")
            traceback.print_exc()
        finally:
            # 清理数据库
            db.session.remove()
            db.drop_all()

if __name__ == '__main__':
    debug_start_practice()