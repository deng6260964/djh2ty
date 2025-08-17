#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手动测试在线考试API功能
由于pytest-flask与Flask 3.0.0版本不兼容，使用此脚本进行功能验证
"""

import sys
import os
import json
import requests
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.user import User
from app.models.course import Course
from app.models.exam import Exam, ExamSubmission, ExamQuestion
from app.models.question import QuestionBank, Question
from app.utils.auth import hash_password

def setup_test_data():
    """设置测试数据"""
    print("设置测试数据...")
    
    # 清理可能存在的测试数据
    # 先删除依赖的数据
    ExamSubmission.query.delete()
    ExamQuestion.query.delete()
    Exam.query.delete()
    Question.query.delete()
    QuestionBank.query.delete()
    Course.query.delete()
    
    existing_student = User.query.filter_by(email='student@test.com').first()
    if existing_student:
        db.session.delete(existing_student)
    
    existing_teacher = User.query.filter_by(email='teacher@test.com').first()
    if existing_teacher:
        db.session.delete(existing_teacher)
    
    db.session.commit()
    
    # 创建测试用户
    test_user = User(
        name='test_student',
        email='student@test.com',
        password_hash=hash_password('StrongP@ssw0rd2024'),
        role='student',
        created_at=datetime.utcnow()
    )
    db.session.add(test_user)
    
    teacher_user = User(
        name='test_teacher',
        email='teacher@test.com',
        password_hash=hash_password('StrongP@ssw0rd2024'),
        role='teacher',
        created_at=datetime.utcnow()
    )
    db.session.add(teacher_user)
    db.session.commit()
    
    # 创建课程
    course = Course(
        name='测试课程',
        description='在线考试测试课程',
        course_type='one_to_many',
        teacher_id=teacher_user.id,
        created_at=datetime.utcnow()
    )
    db.session.add(course)
    db.session.commit()
    
    # 创建题库
    question_bank = QuestionBank(
        name='测试题库',
        description='在线考试测试题库',
        category='编程',
        difficulty_level='intermediate',
        created_by=teacher_user.id,
        created_at=datetime.utcnow()
    )
    db.session.add(question_bank)
    db.session.commit()
    
    # 创建题目
    question1 = Question(
        question_bank_id=question_bank.id,
        question_type='multiple_choice',
        title='Python特点选择题',
        content='以下哪个是Python的特点？',
        options=json.dumps({
            'A': '面向对象',
            'B': '解释型语言',
            'C': '跨平台',
            'D': '以上都是'
        }),
        correct_answer='D',
        points=10,
        difficulty_level='intermediate',
        created_by=teacher_user.id,
        created_at=datetime.utcnow()
    )
    db.session.add(question1)
    
    question2 = Question(
        question_bank_id=question_bank.id,
        question_type='multiple_choice',
        title='Python数据类型选择题',
        content='Python中哪些是可变数据类型？',
        options=json.dumps({
            'A': 'list',
            'B': 'tuple',
            'C': 'dict',
            'D': 'set'
        }),
        correct_answer='A,C,D',
        points=15,
        difficulty_level='intermediate',
        created_by=teacher_user.id,
        created_at=datetime.utcnow()
    )
    db.session.add(question2)
    db.session.commit()
    
    # 创建考试
    exam = Exam(
        title='Python基础测试',
        description='测试Python基础知识',
        course_id=course.id,
        created_by=teacher_user.id,
        start_time=datetime.utcnow() - timedelta(minutes=30),
        end_time=datetime.utcnow() + timedelta(hours=2),
        duration_minutes=60,
        total_points=25,
        status='published',
        allowed_students=str(test_user.id),
        created_at=datetime.utcnow()
    )
    db.session.add(exam)
    db.session.commit()
    
    # 添加题目到考试
    exam_question1 = ExamQuestion(
        exam_id=exam.id,
        question_id=question1.id,
        points=10,
        order_index=1,
        is_required=True,
        created_at=datetime.utcnow()
    )
    exam_question2 = ExamQuestion(
        exam_id=exam.id,
        question_id=question2.id,
        points=15,
        order_index=2,
        is_required=True,
        created_at=datetime.utcnow()
    )
    db.session.add(exam_question1)
    db.session.add(exam_question2)
    db.session.commit()
    
    return {
        'student': test_user,
        'teacher': teacher_user,
        'course': course,
        'exam': exam,
        'questions': [question1, question2]
    }

def get_auth_token(app, email, password):
    """获取认证令牌"""
    with app.test_client() as client:
        response = client.post('/api/auth/login', json={
            'email': email,
            'password': password
        })
        if response.status_code == 200:
            return response.get_json()['access_token']
        else:
            print(f"登录失败: {response.get_json()}")
            return None

def test_online_exam_apis(app, test_data):
    """测试在线考试API"""
    print("\n开始测试在线考试API...")
    
    # 获取学生认证令牌
    token = get_auth_token(app, test_data['student'].email, 'StrongP@ssw0rd2024')
    if not token:
        print("无法获取认证令牌")
        return False
    
    headers = {'Authorization': f'Bearer {token}'}
    exam_id = test_data['exam'].id
    
    with app.test_client() as client:
        # 测试1: 开始考试
        print("\n1. 测试开始考试接口...")
        response = client.get(f'/api/exams/{exam_id}/start', headers=headers)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.get_json()
            print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
            print("✓ 开始考试接口测试通过")
        else:
            print(f"✗ 开始考试接口测试失败: {response.get_json()}")
            return False
        
        # 测试2: 保存单题答案
        print("\n2. 测试保存单题答案接口...")
        question_id = test_data['questions'][0].id
        answer_data = {
            'question_id': question_id,
            'answer': 'D'
        }
        response = client.post(f'/api/exams/{exam_id}/answers', json=answer_data, headers=headers)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.get_json()
            print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
            print("✓ 保存单题答案接口测试通过")
        else:
            print(f"✗ 保存单题答案接口测试失败: {response.get_json()}")
            return False
        
        # 测试3: 获取考试提交状态
        print("\n3. 测试获取考试提交状态接口...")
        response = client.get(f'/api/exams/{exam_id}/submission', headers=headers)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.get_json()
            print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
            print("✓ 获取考试提交状态接口测试通过")
        else:
            print(f"✗ 获取考试提交状态接口测试失败: {response.get_json()}")
            return False
        
        # 测试4: 获取考试剩余时间
        print("\n4. 测试获取考试剩余时间接口...")
        response = client.get(f'/api/exams/{exam_id}/time-remaining', headers=headers)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.get_json()
            print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
            print("✓ 获取考试剩余时间接口测试通过")
        else:
            print(f"✗ 获取考试剩余时间接口测试失败: {response.get_json()}")
            return False
        
        # 测试5: 提交考试
        print("\n5. 测试提交考试接口...")
        submit_data = {
            'answers': {
                str(test_data['questions'][0].id): 'D',
                str(test_data['questions'][1].id): ['A', 'C', 'D']
            }
        }
        response = client.post(f'/api/exams/{exam_id}/submit', json=submit_data, headers=headers)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.get_json()
            print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
            print("✓ 提交考试接口测试通过")
        else:
            print(f"✗ 提交考试接口测试失败: {response.get_json()}")
            return False
    
    return True

def main():
    """主函数"""
    print("开始在线考试API功能验证...")
    
    # 创建应用
    app = create_app()
    
    with app.app_context():
        # 创建数据库表
        db.create_all()
        
        # 设置测试数据
        test_data = setup_test_data()
        
        # 测试API
        success = test_online_exam_apis(app, test_data)
        
        if success:
            print("\n🎉 所有在线考试API测试通过！")
            print("\n测试总结:")
            print("- ✓ 开始考试接口")
            print("- ✓ 保存单题答案接口")
            print("- ✓ 获取考试提交状态接口")
            print("- ✓ 获取考试剩余时间接口")
            print("- ✓ 提交考试接口")
            return True
        else:
            print("\n❌ 部分测试失败，请检查实现")
            return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)