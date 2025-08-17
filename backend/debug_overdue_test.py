#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from app import create_app
from app.database import db
from app.models.user import User
from app.models.course import Course, CourseEnrollment
from app.models.homework import Homework
from app.models.homework_submission import HomeworkSubmission
from app.utils.jwt_middleware import JWTMiddleware
from app.utils.auth import hash_password
import json

def test_overdue_submission():
    """测试逾期提交功能"""
    app = create_app()
    
    with app.app_context():
        # 清理现有数据
        db.session.query(HomeworkSubmission).delete()
        db.session.query(Homework).delete()
        db.session.query(CourseEnrollment).delete()
        db.session.query(Course).delete()
        db.session.query(User).delete()
        db.session.commit()
        
        # 创建测试用户
        teacher = User(
            name='Test Teacher',
            email='teacher@test.com',
            password_hash=hash_password('SuperSecure@Pass2024!'),
            role='teacher'
        )
        db.session.add(teacher)
        
        student = User(
            name='Test Student',
            email='student@test.com',
            password_hash=hash_password('SuperSecure@Pass2024!'),
            role='student'
        )
        db.session.add(student)
        
        db.session.commit()
        
        # 创建课程
        course = Course(
            name='Test Course',
            description='Test Description',
            course_type='one_to_many',
            teacher_id=teacher.id,
            max_students=1,
            is_active=True
        )
        db.session.add(course)
        db.session.commit()
        
        # 学生选课
        enrollment = CourseEnrollment(
            student_id=student.id,
            course_id=course.id,
            is_active=True
        )
        db.session.add(enrollment)
        
        # 创建逾期作业
        assignment = Homework(
            title='Overdue Assignment',
            description='This assignment is overdue',
            course_id=course.id,
            teacher_id=teacher.id,
            due_date=datetime.utcnow() - timedelta(days=1),  # 昨天截止
            max_score=100,
            homework_type='writing',
            is_published=True,
            created_at=datetime.utcnow()
        )
        db.session.add(assignment)
        db.session.commit()
        
        print(f"作业截止时间: {assignment.due_date}")
        print(f"当前时间: {datetime.utcnow()}")
        print(f"作业是否逾期: {assignment.due_date < datetime.utcnow()}")
        
        # 生成JWT token
        jwt_middleware = JWTMiddleware()
        tokens = jwt_middleware.generate_tokens(student)
        token = tokens['access_token']
        
        # 创建测试客户端
        client = app.test_client()
        
        # 准备提交数据
        submission_data = {
            'content': 'Late submission',
            'action': 'submit'
        }
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        print(f"\n发送提交请求...")
        print(f"URL: /api/assignments/{assignment.id}/submissions")
        print(f"数据: {submission_data}")
        
        # 发送提交请求
        response = client.post(
            f'/api/assignments/{assignment.id}/submissions',
            json=submission_data,
            headers=headers
        )
        
        print(f"\n响应状态码: {response.status_code}")
        print(f"响应数据: {response.get_json()}")
        
        if response.status_code == 201:
            data = response.get_json()
            submission = data['submission']
            print(f"\n提交成功!")
            print(f"is_late: {submission.get('is_late')}")
            print(f"submitted_at: {submission.get('submitted_at')}")
            
            # 验证数据库中的记录
            db_submission = HomeworkSubmission.query.filter_by(
                homework_id=assignment.id,
                student_id=student.id
            ).first()
            
            if db_submission:
                print(f"\n数据库中的记录:")
                print(f"status: {db_submission.status}")
                print(f"submitted_at: {db_submission.submitted_at}")
                print(f"is_late: {db_submission.is_late}")
                print(f"作业截止时间: {db_submission.homework.due_date}")
                
                # 手动调用submit方法测试
                print(f"\n手动测试submit方法:")
                print(f"调用前状态: {db_submission.status}")
                manual_result = db_submission.submit()
                print(f"submit()返回结果: {manual_result}")
                print(f"调用后状态: {db_submission.status}")
                print(f"调用后submitted_at: {db_submission.submitted_at}")
                db.session.commit()
                
                # 重新查询验证
                db_submission_after = HomeworkSubmission.query.filter_by(
                    homework_id=assignment.id,
                    student_id=student.id
                ).first()
                print(f"\n重新查询后的记录:")
                print(f"status: {db_submission_after.status}")
                print(f"submitted_at: {db_submission_after.submitted_at}")
                print(f"is_late: {db_submission_after.is_late}")
        else:
            print(f"提交失败: {response.get_json()}")

if __name__ == '__main__':
    test_overdue_submission()