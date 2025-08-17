#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
练习系统模型验证脚本
验证练习系统数据模型关系和级联删除功能
"""

import sys
import os
import uuid
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import (
    User, Course, Question, QuestionBank,
    Practice, PracticeQuestion, PracticeSession, PracticeAnswer
)

def create_test_data():
    """创建测试数据"""
    print("创建测试数据...")
    
    # 创建测试用户
    teacher = User.query.filter_by(role='teacher').first()
    student = User.query.filter_by(role='student').first()
    
    if not teacher:
        teacher = User(
            name="测试教师",
            email="teacher@test.com",
            role="teacher"
        )
        teacher.set_password("password123")
        db.session.add(teacher)
    
    if not student:
        student = User(
            name="测试学生",
            email="student@test.com",
            role="student"
        )
        student.set_password("password123")
        db.session.add(student)
    
    # 创建测试课程
    course = Course.query.first()
    if not course:
        course = Course(
            name="测试课程",
            description="用于练习系统测试的课程",
            teacher_id=teacher.id,
            course_type="regular",
            max_students=50
        )
        db.session.add(course)
    
    # 创建测试题库和题目
    question_bank = QuestionBank.query.first()
    if not question_bank:
        question_bank = QuestionBank(
            name="测试题库",
            description="用于练习系统测试的题库",
            category="programming",
            difficulty_level="medium",
            created_by=teacher.id
        )
        db.session.add(question_bank)
    
    # 创建测试题目
    questions = Question.query.limit(3).all()
    if len(questions) < 3:
        for i in range(3 - len(questions)):
            question = Question(
                title=f"测试题目{i+1}",
                content=f"这是第{i+1}道测试题目的内容",
                question_type="multiple_choice",
                options='{"A": "选项A", "B": "选项B", "C": "选项C", "D": "选项D"}',
                correct_answer="A",
                points=5,
                difficulty_level="beginner",
                created_by=teacher.id,
                question_bank_id=question_bank.id
            )
            db.session.add(question)
            questions.append(question)
    
    db.session.commit()
    return teacher, student, course, questions

def verify_practice_models():
    """验证练习系统模型"""
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("练习系统模型验证报告")
        print("=" * 60)
        
        # 创建测试数据
        teacher, student, course, questions = create_test_data()
        
        print("\n1. 创建练习测试:")
        # 创建练习
        practice = Practice(
            title="测试练习",
            description="这是一个测试练习",
            creator_id=teacher.id,
            course_id=course.id,
            status="published",
            settings={
                "time_limit": 60,
                "show_feedback": True,
                "allow_retry": True
            }
        )
        db.session.add(practice)
        db.session.commit()
        print(f"  ✓ 创建练习: {practice.title} (ID: {practice.id})")
        
        print("\n2. 添加练习题目测试:")
        # 添加题目到练习
        practice_questions = []
        for i, question in enumerate(questions):
            pq = PracticeQuestion(
                practice_id=practice.id,
                question_id=question.id,
                order_index=i + 1,
                settings={
                    "points": 10,
                    "time_limit": 20
                }
            )
            db.session.add(pq)
            practice_questions.append(pq)
        
        db.session.commit()
        print(f"  ✓ 添加了 {len(practice_questions)} 个题目到练习")
        
        print("\n3. 创建练习会话测试:")
        # 创建练习会话
        session = PracticeSession(
            practice_id=practice.id,
            user_id=student.id,
            status="in_progress",
            current_question_index=0,
            total_questions=len(practice_questions),
            answered_questions=0,
            correct_answers=0,
            started_at=datetime.utcnow(),
            last_activity_at=datetime.utcnow(),
            session_data={
                "start_time": datetime.utcnow().isoformat(),
                "user_agent": "test"
            }
        )
        db.session.add(session)
        db.session.commit()
        print(f"  ✓ 创建练习会话: {session.id}")
        
        print("\n4. 提交答案测试:")
        # 提交答案
        answers = []
        for i, pq in enumerate(practice_questions):
            answer = PracticeAnswer(
                practice_session_id=session.id,
                practice_question_id=pq.id,
                user_id=student.id,
                answer_content="A",
                is_correct=True,
                score=10.0,
                max_score=10.0,
                feedback="答案正确！",
                explanation="这是正确答案的解释",
                time_spent=15,
                submitted_at=datetime.utcnow(),
                answer_data={
                    "selected_option": "A",
                    "confidence": 0.8
                }
            )
            db.session.add(answer)
            answers.append(answer)
        
        db.session.commit()
        print(f"  ✓ 提交了 {len(answers)} 个答案")
        
        print("\n5. 模型关系验证:")
        
        # 验证Practice关系
        print("  Practice模型关系:")
        print(f"    - 创建者: {practice.creator.name}")
        print(f"    - 课程: {practice.course.name if practice.course else '无'}")
        print(f"    - 题目数量: {practice.get_question_count()}")
        print(f"    - 会话数量: {practice.get_session_count()}")
        print(f"    - 是否已发布: {practice.is_published()}")
        
        # 验证PracticeQuestion关系
        print("  PracticeQuestion模型关系:")
        for pq in practice_questions:
            print(f"    - 题目: {pq.question.title} (顺序: {pq.order_index})")
            print(f"    - 答案数量: {pq.get_answer_count()}")
        
        # 验证PracticeSession关系
        print("  PracticeSession模型关系:")
        print(f"    - 用户: {session.user.name}")
        print(f"    - 练习: {session.practice.title}")
        print(f"    - 进度: {session.get_progress_percentage():.1f}%")
        print(f"    - 准确率: {session.get_accuracy_percentage():.1f}%")
        print(f"    - 状态检查: 进行中={session.is_in_progress()}, 已完成={session.is_completed()}")
        
        # 验证PracticeAnswer关系
        print("  PracticeAnswer模型关系:")
        for answer in answers:
            print(f"    - 题目: {answer.practice_question.question.title}")
            print(f"    - 用户: {answer.user.name}")
            print(f"    - 得分百分比: {answer.get_score_percentage():.1f}%")
            print(f"    - 是否已答: {answer.is_answered()}, 是否已评分: {answer.is_graded()}")
        
        print("\n6. 级联删除测试:")
        
        # 测试级联删除
        print("  测试删除练习会话...")
        session_id = session.id
        answer_count_before = PracticeAnswer.query.filter_by(practice_session_id=session_id).count()
        print(f"    删除前答案数量: {answer_count_before}")
        
        db.session.delete(session)
        db.session.commit()
        
        answer_count_after = PracticeAnswer.query.filter_by(practice_session_id=session_id).count()
        print(f"    删除后答案数量: {answer_count_after}")
        print(f"    ✓ 级联删除{'成功' if answer_count_after == 0 else '失败'}")
        
        print("\n7. 查询方法测试:")
        
        # 测试静态查询方法
        print("  测试PracticeQuestion.get_by_practice_ordered():")
        ordered_questions = PracticeQuestion.get_by_practice_ordered(practice.id)
        print(f"    ✓ 获取到 {len(ordered_questions)} 个有序题目")
        
        print("  测试PracticeQuestion.get_max_order_index():")
        max_order = PracticeQuestion.get_max_order_index(practice.id)
        print(f"    ✓ 最大顺序索引: {max_order}")
        
        print("  测试PracticeSession.get_active_session():")
        # 创建新会话用于测试
        new_session = PracticeSession(
            practice_id=practice.id,
            user_id=student.id,
            status="in_progress",
            current_question_index=0,
            total_questions=len(practice_questions),
            answered_questions=0,
            correct_answers=0,
            started_at=datetime.utcnow(),
            last_activity_at=datetime.utcnow()
        )
        db.session.add(new_session)
        db.session.commit()
        
        active_session = PracticeSession.get_active_session(student.id, practice.id)
        print(f"    ✓ 获取活跃会话: {active_session.id if active_session else '无'}")
        
        print("\n8. 数据统计:")
        print(f"  - 练习总数: {Practice.query.count()}")
        print(f"  - 练习题目关联总数: {PracticeQuestion.query.count()}")
        print(f"  - 练习会话总数: {PracticeSession.query.count()}")
        print(f"  - 练习答案总数: {PracticeAnswer.query.count()}")
        
        print("\n" + "=" * 60)
        print("练习系统模型验证完成！")
        print("=" * 60)
        
        # 清理测试数据
        print("\n清理测试数据...")
        db.session.delete(practice)
        db.session.commit()
        print("✓ 测试数据清理完成")

if __name__ == '__main__':
    verify_practice_models()