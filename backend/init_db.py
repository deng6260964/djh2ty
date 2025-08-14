#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库初始化脚本
创建所有必要的数据库表结构
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.database import Database
from models.user import User
from models.course import Course
from models.question import Question
from models.homework import Homework, HomeworkAnswer
from models.exam import Exam, ExamAnswer
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta

def init_database():
    """初始化数据库表结构"""
    print("开始初始化数据库...")
    
    # 创建数据库连接
    db = Database()
    
    try:
        # 创建所有表
        print("创建用户表...")
        User.create_table()
        
        print("创建课程表...")
        Course.create_table()
        
        print("创建题目表...")
        Question.create_table()
        
        print("创建作业表...")
        Homework.create_table()
        HomeworkAnswer.create_table()
        
        print("创建考试表...")
        Exam.create_table()
        ExamAnswer.create_table()
        
        print("数据库表创建完成！")
        
        # 创建初始数据
        create_initial_data()
        
        print("数据库初始化完成！")
        
    except Exception as e:
        print(f"数据库初始化失败: {e}")
        raise

def create_initial_data():
    """创建初始测试数据"""
    print("创建初始测试数据...")
    
    # 创建测试教师
    teacher = User({
        'phone': '13800138001',
        'name': '张老师',
        'role': 'teacher',
        'email': 'teacher@example.com',
        'status': 'active'
    })
    teacher.set_password('123456')
    teacher.save()
    teacher_id = teacher.id
    print(f"创建教师用户: {teacher.name} (ID: {teacher_id})")
    
    # 创建测试学生
    students = [
        {
            'phone': '13800138002',
            'name': '李小明',
            'role': 'student',
            'email': 'student1@example.com',
            'status': 'active'
        },
        {
            'phone': '13800138003',
            'name': '王小红',
            'role': 'student',
            'email': 'student2@example.com',
            'status': 'active'
        },
        {
            'phone': '13800138004',
            'name': '刘小强',
            'role': 'student',
            'email': 'student3@example.com',
            'status': 'active'
        }
    ]
    
    student_ids = []
    for student_data in students:
        student = User(student_data)
        student.set_password('123456')
        student.save()
        student_ids.append(student.id)
        print(f"创建学生用户: {student.name} (ID: {student.id})")
    
    # 创建示例课程
    now = datetime.now()
    courses = [
        {
            'teacher_id': teacher_id,
            'title': '英语语法基础课程',
            'subject': '英语',
            'level': '初级',
            'start_time': (now + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'),
            'end_time': (now + timedelta(days=1, hours=2)).strftime('%Y-%m-%d %H:%M:%S'),
            'location': '在线教室A',
            'max_students': 10,
            'description': '学习英语基础语法知识，包括时态、语态、句型结构等',
            'status': 'active'
        },
        {
            'teacher_id': teacher_id,
            'title': '英语口语练习课程',
            'subject': '英语',
            'level': '中级',
            'start_time': (now + timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S'),
            'end_time': (now + timedelta(days=2, hours=1, minutes=30)).strftime('%Y-%m-%d %H:%M:%S'),
            'location': '在线教室B',
            'max_students': 8,
            'description': '提高英语口语表达能力，练习日常对话',
            'status': 'active'
        },
        {
            'teacher_id': teacher_id,
            'title': '数学基础课程',
            'subject': '数学',
            'level': '初级',
            'start_time': (now + timedelta(days=3)).strftime('%Y-%m-%d %H:%M:%S'),
            'end_time': (now + timedelta(days=3, hours=1)).strftime('%Y-%m-%d %H:%M:%S'),
            'location': '在线教室C',
            'max_students': 15,
            'description': '数学基础知识学习，包括四则运算、分数、小数等',
            'status': 'active'
        }
    ]
    
    course_ids = []
    for course_data in courses:
        course = Course(course_data)
        course.save()
        course_ids.append(course.id)
        print(f"创建课程: {course.title} (ID: {course.id})")
    
    # 创建示例题目
    questions_data = [
        {
            'teacher_id': teacher.id,
            'title': '动词be的用法',
            'content': 'What is the correct form of the verb "to be" for "I"?',
            'question_type': 'single_choice',
            'difficulty': 'easy',
            'category': '语法',
            'options': '["am", "is", "are", "be"]',
            'correct_answer': 'am',
            'explanation': '"I" always takes "am" as the form of "to be".',
            'points': 1,
            'estimated_time': 30
        },
        {
            'teacher_id': teacher.id,
            'title': '水果词汇识别',
            'content': 'Which of the following are fruits?',
            'question_type': 'multiple_choice',
            'difficulty': 'medium',
            'category': '词汇',
            'options': '["apple", "carrot", "banana", "potato"]',
            'correct_answer': '["apple", "banana"]',
            'explanation': 'Apple and banana are fruits, while carrot and potato are vegetables.',
            'points': 2,
            'estimated_time': 45
        },
        {
            'teacher_id': teacher.id,
            'title': '语法正误判断',
            'content': 'The sentence "She go to school" is grammatically correct.',
            'question_type': 'true_false',
            'difficulty': 'easy',
            'category': '语法',
            'options': '["True", "False"]',
            'correct_answer': 'False',
            'explanation': 'The correct form should be "She goes to school".',
            'points': 1,
            'estimated_time': 20
        }
    ]
    
    question_ids = []
    for question_data in questions_data:
        question = Question(question_data)
        question.save()
        question_ids.append(question.id)
        print(f"创建题目: {question.title} (ID: {question.id})")
    
    # 创建示例作业
    homework_data = {
        'teacher_id': teacher.id,
        'student_id': student.id,
        'title': '英语语法练习',
        'description': '完成以下语法练习题',
        'question_ids': question_ids[:2],  # 使用前两个题目
        'total_points': 3,
        'due_date': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S'),
        'status': 'assigned'
    }
    homework = Homework(homework_data)
    homework.save()
    print(f"创建作业: {homework.title}")

    # 创建示例考试
    exam_data = {
        'teacher_id': teacher.id,
        'student_id': student.id,
        'title': '期中英语测试',
        'description': '期中考试，包含语法和词汇',
        'question_ids': question_ids,  # 使用所有题目
        'total_points': 4,
        'start_time': (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d %H:%M:%S'),
        'end_time': (datetime.now() + timedelta(days=3, hours=2)).strftime('%Y-%m-%d %H:%M:%S'),
        'duration': 120,
        'status': 'scheduled'
    }
    exam = Exam(exam_data)
    exam.save()
    print(f"创建考试: {exam.title}")
    
    print("初始测试数据创建完成！")
    print("\n登录信息:")
    print("教师账号: 13800138001 / 123456")
    print("学生账号: 13800138002 / 123456")
    print("学生账号: 13800138003 / 123456")
    print("学生账号: 13800138004 / 123456")

if __name__ == '__main__':
    init_database()