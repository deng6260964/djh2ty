#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库验证脚本
验证数据库表创建和模型关系正确性
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import User, Course, Homework, Question, QuestionBank, File, CourseEnrollment, HomeworkSubmission

def verify_database():
    """验证数据库结构和数据"""
    app = create_app()
    
    with app.app_context():
        print("=" * 50)
        print("数据库验证报告")
        print("=" * 50)
        
        # 验证表结构
        print("\n1. 数据库表结构:")
        tables = [table.name for table in db.metadata.tables.values()]
        print(f"总表数: {len(tables)}")
        for table in sorted(tables):
            print(f"  - {table}")
        
        # 验证用户数据
        print("\n2. 用户数据:")
        users = User.query.all()
        print(f"总用户数: {len(users)}")
        for user in users:
            print(f"  - {user.name} ({user.email}) - {user.role}")
        
        # 验证课程数据
        print("\n3. 课程数据:")
        courses = Course.query.all()
        print(f"总课程数: {len(courses)}")
        for course in courses:
            print(f"  - {course.name} (教师: {course.teacher.name})")
            print(f"    描述: {course.description[:50]}...")
            print(f"    类型: {course.course_type}, 最大学生数: {course.max_students}")
            print(f"    状态: {'活跃' if course.is_active else '非活跃'}")
        
        # 验证选课数据
        print("\n4. 选课数据:")
        enrollments = CourseEnrollment.query.all()
        print(f"总选课记录数: {len(enrollments)}")
        for enrollment in enrollments:
            print(f"  - {enrollment.student.name} 选修 {enrollment.course.name} (状态: {'活跃' if enrollment.is_active else '非活跃'})")
            print(f"    选课时间: {enrollment.enrolled_at.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 验证题库数据
        print("\n5. 题库数据:")
        question_banks = QuestionBank.query.all()
        print(f"总题库数: {len(question_banks)}")
        for bank in question_banks:
            print(f"  - {bank.name} (题目数: {len(bank.questions)})")
            print(f"    分类: {bank.category}, 难度: {bank.difficulty_level}")
        
        # 验证题目数据
        print("\n6. 题目数据:")
        questions = Question.query.all()
        print(f"总题目数: {len(questions)}")
        for question in questions:
            print(f"  - {question.title} (类型: {question.question_type}, 分值: {question.points})")
        
        # 验证作业数据
        print("\n7. 作业数据:")
        homeworks = Homework.query.all()
        print(f"总作业数: {len(homeworks)}")
        for hw in homeworks:
            print(f"  - {hw.title} (课程: {hw.course.name})")
            print(f"    类型: {hw.homework_type}, 最高分: {hw.max_score}")
            print(f"    截止时间: {hw.due_date.strftime('%Y-%m-%d %H:%M:%S')}, 状态: {'已发布' if hw.is_published else '未发布'}")
        
        # 验证作业提交数据
        print("\n8. 作业提交数据:")
        submissions = HomeworkSubmission.query.all()
        print(f"总提交数: {len(submissions)}")
        for submission in submissions:
            print(f"  - {submission.student.name} 提交 {submission.homework.title}")
            print(f"    状态: {submission.status}, 分数: {submission.score or '未评分'}")
        
        # 验证文件数据
        print("\n9. 文件数据:")
        files = File.query.all()
        print(f"总文件数: {len(files)}")
        for file in files:
            print(f"  - {file.original_filename} (类型: {file.file_category})")
            print(f"    大小: {file.get_human_readable_size()}, 上传者: {file.uploader.name}")
        
        # 验证模型关系
        print("\n10. 模型关系验证:")
        print("检查外键关系...")
        
        # 检查课程-教师关系
        for course in courses:
            if course.teacher:
                print(f"  ✓ 课程 '{course.name}' 正确关联教师 '{course.teacher.name}'")
            else:
                print(f"  ✗ 课程 '{course.name}' 缺少教师关联")
        
        # 检查作业-课程关系
        for homework in homeworks:
            if homework.course:
                print(f"  ✓ 作业 '{homework.title}' 正确关联课程 '{homework.course.name}'")
            else:
                print(f"  ✗ 作业 '{homework.title}' 缺少课程关联")
        
        # 检查题目-题库关系
        for question in questions:
            if question.question_bank:
                print(f"  ✓ 题目 '{question.title}' 正确关联题库 '{question.question_bank.name}'")
            else:
                print(f"  ✗ 题目 '{question.title}' 缺少题库关联")
        
        print("\n=" * 50)
        print("验证完成！")
        print("=" * 50)

if __name__ == '__main__':
    verify_database()