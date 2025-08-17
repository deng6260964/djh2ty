#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
练习会话API简单测试脚本
测试所有练习会话相关的API接口
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.user import User
from app.models.course import Course
from app.models.question import Question, QuestionBank
from app.models.practice import Practice
from app.models.practice_question import PracticeQuestion
from app.models.practice_session import PracticeSession
from app.utils.jwt_middleware import JWTMiddleware
from datetime import datetime
import uuid
import json

def test_practice_sessions_api():
    """测试练习会话API的所有功能"""
    
    app = create_app()
    
    with app.app_context():
        # 清理数据库
        db.drop_all()
        db.create_all()
        
        try:
            # 1. 创建测试数据
            print("\n=== 创建测试数据 ===")
            
            # 创建用户
            student = User(
                email='student@test.com',
                name='Test Student',
                password_hash='hashed_password',
                role='student',
                is_active=True
            )
            
            teacher = User(
                email='teacher@test.com',
                name='Test Teacher',
                password_hash='hashed_password',
                role='teacher',
                is_active=True
            )
            
            db.session.add_all([student, teacher])
            db.session.commit()
            
            # 创建课程
            course = Course(
                name='Test Course',
                description='Test course description',
                course_type='one_to_many',
                teacher_id=teacher.id,
                is_active=True
            )
            db.session.add(course)
            db.session.commit()
            
            # 创建题库
            question_bank = QuestionBank(
                name='Test Question Bank',
                description='Test question bank',
                category='test',
                difficulty_level='beginner',
                created_by=teacher.id,
                is_public=True
            )
            db.session.add(question_bank)
            db.session.flush()  # 获取question_bank.id
            
            # 创建题目
            question = Question(
                question_bank_id=question_bank.id,
                title='Test Question',
                content='What is 2+2?',
                question_type='multiple_choice',
                options='{"A": "3", "B": "4", "C": "5", "D": "6"}',
                correct_answer='B',
                difficulty_level='beginner',
                created_by=teacher.id
            )
            db.session.add(question)
            db.session.commit()
            
            # 创建练习
            practice = Practice(
                title='Test Practice',
                description='Test practice description',
                creator_id=teacher.id,
                course_id=course.id,
                status='published',
                settings={'time_limit': 60, 'show_answer': True}
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
            
            print(f"✓ 创建用户: {student.email}, {teacher.email}")
            print(f"✓ 创建课程: {course.name}")
            print(f"✓ 创建题目: {question.title}")
            print(f"✓ 创建练习: {practice.title}")
            
            # 2. 生成JWT令牌
            jwt_middleware = JWTMiddleware()
            student_tokens = jwt_middleware.generate_tokens(student)
            student_token = student_tokens['access_token']
            
            headers = {
                'Authorization': f'Bearer {student_token}',
                'Content-Type': 'application/json'
            }
            
            # 3. 测试开始练习会话
            print("\n=== 测试开始练习会话 ===")
            with app.test_client() as client:
                response = client.post(
                    '/api/practice-sessions/',
                    headers=headers,
                    json={'practice_id': practice.id}
                )
                
                print(f"状态码: {response.status_code}")
                if response.status_code == 201:
                    data = response.get_json()
                    session_id = data['data']['session_id']
                    print(f"✓ 成功开始练习会话: {session_id}")
                    print(f"  练习: {data['data']['practice']['title']}")
                    print(f"  题目数: {len(data['data']['questions'])}")
                else:
                    print(f"✗ 开始练习失败: {response.get_json()}")
                    return False
            
            # 4. 测试获取会话状态
            print("\n=== 测试获取会话状态 ===")
            with app.test_client() as client:
                response = client.get(
                    f'/api/practice-sessions/{session_id}',
                    headers=headers
                )
                
                print(f"状态码: {response.status_code}")
                if response.status_code == 200:
                    data = response.get_json()
                    print(f"✓ 成功获取会话状态")
                    print(f"  状态: {data['data']['status']}")
                    print(f"  当前题目索引: {data['data']['current_question_index']}")
                    print(f"  总题目数: {data['data']['total_questions']}")
                else:
                    print(f"✗ 获取会话状态失败: {response.get_json()}")
                    return False
            
            # 5. 测试暂停练习会话
            print("\n=== 测试暂停练习会话 ===")
            with app.test_client() as client:
                response = client.put(
                    f'/api/practice-sessions/{session_id}/pause',
                    headers=headers
                )
                
                print(f"状态码: {response.status_code}")
                if response.status_code == 200:
                    data = response.get_json()
                    print(f"✓ 成功暂停练习会话")
                    print(f"  状态: {data['data']['status']}")
                    print(f"  暂停时间: {data['data']['paused_at']}")
                else:
                    print(f"✗ 暂停练习失败: {response.get_json()}")
                    return False
            
            # 6. 测试恢复练习会话
            print("\n=== 测试恢复练习会话 ===")
            with app.test_client() as client:
                response = client.put(
                    f'/api/practice-sessions/{session_id}/resume',
                    headers=headers
                )
                
                print(f"状态码: {response.status_code}")
                if response.status_code == 200:
                    data = response.get_json()
                    print(f"✓ 成功恢复练习会话")
                    print(f"  状态: {data['data']['status']}")
                    print(f"  恢复时间: {data['data']['resumed_at']}")
                else:
                    print(f"✗ 恢复练习失败: {response.get_json()}")
                    return False
            
            # 7. 测试完成练习会话
            print("\n=== 测试完成练习会话 ===")
            with app.test_client() as client:
                response = client.put(
                    f'/api/practice-sessions/{session_id}/complete',
                    headers=headers
                )
                
                print(f"状态码: {response.status_code}")
                if response.status_code == 200:
                    data = response.get_json()
                    print(f"✓ 成功完成练习会话")
                    print(f"  状态: {data['data']['status']}")
                    print(f"  完成时间: {data['data']['completed_at']}")
                    print(f"  得分: {data['data']['score']}")
                    print(f"  正确答案数: {data['data']['correct_answers']}/{data['data']['total_questions']}")
                else:
                    print(f"✗ 完成练习失败: {response.get_json()}")
                    return False
            
            # 8. 测试重复开始练习（应该创建新会话）
            print("\n=== 测试重复开始练习 ===")
            with app.test_client() as client:
                response = client.post(
                    '/api/practice-sessions/',
                    headers=headers,
                    json={'practice_id': practice.id}
                )
                
                print(f"状态码: {response.status_code}")
                if response.status_code == 201:
                    data = response.get_json()
                    new_session_id = data['data']['session_id']
                    print(f"✓ 成功创建新的练习会话: {new_session_id}")
                    print(f"  新会话ID与原会话ID不同: {new_session_id != session_id}")
                else:
                    print(f"✗ 重复开始练习失败: {response.get_json()}")
                    return False
            
            print("\n=== 所有测试通过! ===")
            return True
            
        except Exception as e:
            print(f"\n✗ 测试过程中发生错误: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        
        finally:
            # 清理数据库
            db.session.rollback()
            db.drop_all()

if __name__ == '__main__':
    success = test_practice_sessions_api()
    if success:
        print("\n🎉 练习会话API测试全部通过!")
        sys.exit(0)
    else:
        print("\n❌ 练习会话API测试失败!")
        sys.exit(1)