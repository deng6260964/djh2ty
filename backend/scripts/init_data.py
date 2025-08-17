#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始数据脚本
创建管理员用户和示例数据
"""

import sys
import os
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import (
    User, Course, CourseEnrollment, Homework, HomeworkSubmission,
    Question, QuestionBank, File
)

def create_initial_users():
    """创建初始用户"""
    print("创建初始用户...")
    
    # 管理员用户
    admin = User(
        email='admin@example.com',
        name='系统管理员',
        password_hash=generate_password_hash('admin123'),
        role='admin',
        phone='13800138000',
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    # 教师用户
    teacher1 = User(
        email='teacher1@example.com',
        name='张老师',
        password_hash=generate_password_hash('teacher123'),
        role='teacher',
        phone='13800138001',
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    teacher2 = User(
        email='teacher2@example.com',
        name='李老师',
        password_hash=generate_password_hash('teacher123'),
        role='teacher',
        phone='13800138002',
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    # 学生用户
    student1 = User(
        email='student1@example.com',
        name='王小明',
        password_hash=generate_password_hash('student123'),
        role='student',
        phone='13800138003',
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    student2 = User(
        email='student2@example.com',
        name='李小红',
        password_hash=generate_password_hash('student123'),
        role='student',
        phone='13800138004',
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    student3 = User(
        email='student3@example.com',
        name='张小华',
        password_hash=generate_password_hash('student123'),
        role='student',
        phone='13800138005',
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    users = [admin, teacher1, teacher2, student1, student2, student3]
    for user in users:
        db.session.add(user)
    
    db.session.commit()
    print(f"创建了 {len(users)} 个用户")
    return users

def create_initial_courses(users):
    """创建初始课程"""
    print("创建初始课程...")
    
    # 获取教师
    teacher1 = next(u for u in users if u.email == 'teacher1@example.com')
    teacher2 = next(u for u in users if u.email == 'teacher2@example.com')
    
    # 创建课程
    course1 = Course(
        name='英语口语基础班',
        description='适合初学者的英语口语课程，重点培养日常对话能力',
        course_type='one_to_many',
        max_students=10,
        schedule='周一、周三、周五 19:00-20:30',
        teacher_id=teacher1.id,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    course2 = Course(
        name='商务英语一对一',
        description='针对职场人士的商务英语培训，提升商务沟通能力',
        course_type='one_to_one',
        max_students=1,
        schedule='根据学员时间安排',
        teacher_id=teacher2.id,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    course3 = Course(
        name='雅思写作强化班',
        description='雅思写作技巧训练，提高写作分数',
        course_type='one_to_many',
        max_students=8,
        schedule='周二、周四 20:00-21:30',
        teacher_id=teacher1.id,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    courses = [course1, course2, course3]
    for course in courses:
        db.session.add(course)
    
    db.session.commit()
    print(f"创建了 {len(courses)} 个课程")
    return courses

def create_course_enrollments(users, courses):
    """创建课程选课记录"""
    print("创建课程选课记录...")
    
    # 获取学生
    students = [u for u in users if u.role == 'student']
    
    enrollments = []
    
    # 学生1选择口语基础班和雅思写作班
    enrollments.append(CourseEnrollment(
        course_id=courses[0].id,  # 英语口语基础班
        student_id=students[0].id,
        enrolled_at=datetime.utcnow(),
        is_active=True
    ))
    
    enrollments.append(CourseEnrollment(
        course_id=courses[2].id,  # 雅思写作强化班
        student_id=students[0].id,
        enrolled_at=datetime.utcnow(),
        is_active=True
    ))
    
    # 学生2选择商务英语一对一
    enrollments.append(CourseEnrollment(
        course_id=courses[1].id,  # 商务英语一对一
        student_id=students[1].id,
        enrolled_at=datetime.utcnow(),
        is_active=True
    ))
    
    # 学生3选择口语基础班
    enrollments.append(CourseEnrollment(
        course_id=courses[0].id,  # 英语口语基础班
        student_id=students[2].id,
        enrolled_at=datetime.utcnow(),
        is_active=True
    ))
    
    for enrollment in enrollments:
        db.session.add(enrollment)
    
    db.session.commit()
    print(f"创建了 {len(enrollments)} 个选课记录")
    return enrollments

def create_question_banks(users):
    """创建题库"""
    print("创建题库...")
    
    # 获取教师
    teacher1 = next(u for u in users if u.email == 'teacher1@example.com')
    teacher2 = next(u for u in users if u.email == 'teacher2@example.com')
    
    # 创建题库
    bank1 = QuestionBank(
        name='英语口语基础题库',
        description='包含日常对话、发音练习等基础口语题目',
        category='口语',
        difficulty_level='beginner',
        created_by=teacher1.id,
        is_public=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    bank2 = QuestionBank(
        name='商务英语题库',
        description='商务场景对话、邮件写作等题目',
        category='商务英语',
        difficulty_level='intermediate',
        created_by=teacher2.id,
        is_public=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    bank3 = QuestionBank(
        name='雅思写作题库',
        description='雅思Task1和Task2写作题目',
        category='雅思写作',
        difficulty_level='advanced',
        created_by=teacher1.id,
        is_public=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    banks = [bank1, bank2, bank3]
    for bank in banks:
        db.session.add(bank)
    
    db.session.commit()
    print(f"创建了 {len(banks)} 个题库")
    return banks

def create_sample_questions(users, question_banks):
    """创建示例题目"""
    print("创建示例题目...")
    
    teacher1 = next(u for u in users if u.email == 'teacher1@example.com')
    teacher2 = next(u for u in users if u.email == 'teacher2@example.com')
    
    questions = []
    
    # 口语基础题库的题目
    questions.append(Question(
        question_bank_id=question_banks[0].id,
        question_type='speaking',
        title='自我介绍',
        content='请用英语进行1-2分钟的自我介绍，包括姓名、年龄、爱好等信息。',
        points=10,
        difficulty_level='beginner',
        tags='自我介绍,口语基础',
        created_by=teacher1.id,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    ))
    
    questions.append(Question(
        question_bank_id=question_banks[0].id,
        question_type='multiple_choice',
        title='日常问候语选择',
        content='在早上见到朋友时，最合适的问候语是？',
        options='A. Good evening\nB. Good morning\nC. Good night\nD. Goodbye',
        correct_answer='B',
        explanation='早上见面应该说Good morning',
        points=5,
        difficulty_level='beginner',
        tags='问候语,日常对话',
        created_by=teacher1.id,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    ))
    
    # 商务英语题库的题目
    questions.append(Question(
        question_bank_id=question_banks[1].id,
        question_type='essay',
        title='商务邮件写作',
        content='请写一封商务邮件，向客户介绍公司的新产品。邮件应包括产品特点、优势和联系方式。',
        points=20,
        difficulty_level='intermediate',
        tags='商务邮件,写作',
        created_by=teacher2.id,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    ))
    
    # 雅思写作题库的题目
    questions.append(Question(
        question_bank_id=question_banks[2].id,
        question_type='essay',
        title='雅思Task2议论文',
        content='Some people think that children should be taught to compete, while others believe that children should be taught to cooperate. Discuss both views and give your opinion.',
        points=25,
        difficulty_level='advanced',
        tags='雅思写作,议论文,Task2',
        created_by=teacher1.id,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    ))
    
    for question in questions:
        db.session.add(question)
    
    db.session.commit()
    print(f"创建了 {len(questions)} 个题目")
    return questions

def create_sample_homeworks(users, courses):
    """创建示例作业"""
    print("创建示例作业...")
    
    teacher1 = next(u for u in users if u.email == 'teacher1@example.com')
    teacher2 = next(u for u in users if u.email == 'teacher2@example.com')
    
    homeworks = []
    
    # 口语基础班作业
    homeworks.append(Homework(
        title='第一周口语练习',
        description='练习基本的自我介绍和日常问候语',
        course_id=courses[0].id,  # 英语口语基础班
        teacher_id=teacher1.id,
        homework_type='speaking',
        max_score=100,
        due_date=datetime.utcnow() + timedelta(days=7),
        instructions='请录制一段2-3分钟的视频，包含自我介绍和与朋友的问候对话',
        is_published=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    ))
    
    # 商务英语作业
    homeworks.append(Homework(
        title='商务邮件写作练习',
        description='练习撰写正式的商务邮件',
        course_id=courses[1].id,  # 商务英语一对一
        teacher_id=teacher2.id,
        homework_type='writing',
        max_score=100,
        due_date=datetime.utcnow() + timedelta(days=5),
        instructions='请写一封向新客户介绍公司服务的邮件，要求格式正确，语言专业',
        is_published=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    ))
    
    # 雅思写作作业
    homeworks.append(Homework(
        title='雅思Task1图表描述',
        description='练习描述图表数据',
        course_id=courses[2].id,  # 雅思写作强化班
        teacher_id=teacher1.id,
        homework_type='writing',
        max_score=100,
        due_date=datetime.utcnow() + timedelta(days=3),
        instructions='根据提供的柱状图，写一篇150字以上的描述文章',
        is_published=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    ))
    
    for homework in homeworks:
        db.session.add(homework)
    
    db.session.commit()
    print(f"创建了 {len(homeworks)} 个作业")
    return homeworks

def main():
    """主函数"""
    print("开始初始化数据...")
    
    # 创建应用上下文
    app = create_app()
    with app.app_context():
        # 检查是否已有数据
        if User.query.first():
            print("数据库中已存在数据，跳过初始化")
            return
        
        try:
            # 创建初始数据
            users = create_initial_users()
            courses = create_initial_courses(users)
            enrollments = create_course_enrollments(users, courses)
            question_banks = create_question_banks(users)
            questions = create_sample_questions(users, question_banks)
            homeworks = create_sample_homeworks(users, courses)
            
            print("\n初始化数据完成！")
            print("="*50)
            print("登录信息：")
            print("管理员: admin@example.com / admin123")
            print("教师1: teacher1@example.com / teacher123")
            print("教师2: teacher2@example.com / teacher123")
            print("学生1: student1@example.com / student123")
            print("学生2: student2@example.com / student123")
            print("学生3: student3@example.com / student123")
            print("="*50)
            
        except Exception as e:
            print(f"初始化数据时出错: {e}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    main()