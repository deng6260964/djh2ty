#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试课程学生关联功能
"""

import sys
import os
# 确保在backend目录下运行
backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
os.chdir(backend_dir)
sys.path.append(backend_dir)

from models.database import db
from models.course_student import CourseStudent
from models.course import Course
from models.user import User
from datetime import datetime

def test_course_student_association():
    print("=== 测试课程学生关联功能 ===")
    
    # 1. 检查现有数据
    print("\n1. 检查现有数据:")
    courses = db.execute_query('SELECT id, title, teacher_id FROM courses ORDER BY created_at DESC LIMIT 3')
    print(f"找到 {len(courses)} 个课程:")
    for row in courses:
        course_dict = dict(row)
        print(f"  - ID: {course_dict['id']}, 标题: {course_dict['title']}, 教师ID: {course_dict['teacher_id']}")
    
    students = db.execute_query('SELECT id, name, role FROM users WHERE role = "student" ORDER BY created_at DESC LIMIT 3')
    print(f"\n找到 {len(students)} 个学生:")
    for row in students:
        student_dict = dict(row)
        print(f"  - ID: {student_dict['id']}, 姓名: {student_dict['name']}, 角色: {student_dict['role']}")
    
    # 2. 检查现有关联
    print("\n2. 检查现有课程学生关联:")
    associations = db.execute_query('''
        SELECT cs.*, u.name as student_name, c.title as course_title 
        FROM course_students cs 
        LEFT JOIN users u ON cs.student_id = u.id 
        LEFT JOIN courses c ON cs.course_id = c.id 
        ORDER BY cs.created_at DESC LIMIT 10
    ''')
    print(f"找到 {len(associations)} 条关联记录:")
    for row in associations:
        assoc_dict = dict(row)
        print(f"  - 课程: {assoc_dict.get('course_title', '未知')}, 学生: {assoc_dict.get('student_name', '未知')}, 状态: {assoc_dict.get('status', '未知')}")
    
    # 3. 如果有课程和学生，创建测试关联
    if courses and students:
        course_id = dict(courses[0])['id']
        student_id = dict(students[0])['id']
        
        print(f"\n3. 创建测试关联 (课程ID: {course_id}, 学生ID: {student_id}):")
        
        # 检查是否已存在关联
        existing = CourseStudent.is_enrolled(course_id, student_id)
        if existing:
            print("  - 关联已存在，跳过创建")
        else:
            # 创建新关联
            enrollment = CourseStudent(
                course_id=course_id,
                student_id=student_id,
                enrollment_date=datetime.now().isoformat(),
                status='enrolled'
            )
            enrollment.save()
            print(f"  - 创建关联成功，ID: {enrollment.id}")
        
        # 4. 验证关联
        print("\n4. 验证关联:")
        course_students = CourseStudent.get_by_course(course_id)
        print(f"  - 课程 {course_id} 的学生数量: {len(course_students)}")
        for student in course_students:
            print(f"    * 学生ID: {student.student_id}, 姓名: {getattr(student, 'student_name', '未知')}, 状态: {student.status}")
        
        student_courses = CourseStudent.get_by_student(student_id)
        print(f"  - 学生 {student_id} 的课程数量: {len(student_courses)}")
        for course in student_courses:
            print(f"    * 课程ID: {course.course_id}, 标题: {getattr(course, 'course_title', '未知')}, 状态: {course.status}")
    
    print("\n=== 测试完成 ===")

if __name__ == '__main__':
    test_course_student_association()