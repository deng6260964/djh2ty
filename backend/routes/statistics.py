from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import User, Course, Question, Homework, Exam
from datetime import datetime, timedelta

statistics_bp = Blueprint('statistics', __name__, url_prefix='/api/statistics')

@statistics_bp.route('/teaching', methods=['GET'])
@jwt_required()
def get_teaching_statistics():
    """获取教师教学统计信息"""
    try:
        user_id = get_jwt_identity()
        user = User.find_by_id(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        if user.role != 'teacher':
            return jsonify({
                'success': False,
                'message': '权限不足，只有教师可以查看教学统计',
                'code': 'PERMISSION_DENIED'
            }), 403
        
        # 获取学生总数（该教师的学生）
        courses = Course.get_by_teacher(user_id)
        student_ids = set()
        for course in courses:
            if course.student_id:
                student_ids.add(course.student_id)
        total_students = len(student_ids)
        
        # 获取课程总数
        total_courses = len(courses)
        
        # 获取题目总数
        questions = Question.get_by_teacher(user_id)
        total_questions = len(questions)
        
        # 获取作业总数
        homeworks = Homework.get_by_teacher(user_id)
        total_assignments = len(homeworks)
        
        # 获取待批改数量（作业和考试）
        pending_grading = 0
        for homework in homeworks:
            if homework.status == 'submitted':
                pending_grading += 1
        
        # 获取考试统计
         exams = Exam.query.filter_by(teacher_id=current_user.id).all()
         for exam in exams:
             if exam.status == 'submitted':
                 pending_grading += 1
        
        # 计算增长率（简化处理，实际应该与历史数据对比）
        student_growth = 5.2  # 模拟数据
        course_growth = 3.8
        homework_growth = 7.1
        score_growth = 2.3
        
        # 计算平均分
        all_scores = []
        for homework in homeworks:
            if homework.status == 'graded' and homework.score is not None and homework.total_points:
                all_scores.append((homework.score / homework.total_points) * 100)
        
        for exam in exams:
            if exam.status == 'graded' and exam.score is not None and exam.total_points:
                all_scores.append((exam.score / exam.total_points) * 100)
        
        average_score = round(sum(all_scores) / len(all_scores), 1) if all_scores else 0
        
        # 活跃度统计（简化处理）
        daily_active_students = max(1, total_students // 3)
        weekly_active_students = max(1, total_students // 2)
        monthly_active_students = max(1, int(total_students * 0.8))
        
        # 成绩分布
        excellent = len([s for s in all_scores if s >= 90])
        good = len([s for s in all_scores if 80 <= s < 90])
        pass_count = len([s for s in all_scores if 60 <= s < 80])
        fail = len([s for s in all_scores if s < 60])
        
        return jsonify({
            'success': True,
            'message': '获取教学统计成功',
            'data': {
                'total_students': total_students,
                'total_courses': total_courses,
                'total_questions': total_questions,
                'total_homeworks': total_assignments,
                'total_exams': len(exams),
                'pending_grading': pending_grading,
                'student_growth': student_growth,
                'course_growth': course_growth,
                'homework_growth': homework_growth,
                'score_growth': score_growth,
                'average_score': average_score,
                'daily_active_students': daily_active_students,
                'weekly_active_students': weekly_active_students,
                'monthly_active_students': monthly_active_students,
                'average_online_time': 45,  # 模拟数据
                'completed_homeworks': len([h for h in homeworks if h.status == 'graded']),
                'pending_homeworks': len([h for h in homeworks if h.status == 'submitted']),
                'completed_exams': len([e for e in exams if e.status == 'graded']),
                'course_completion_rate': 75,  # 模拟数据
                'score_distribution': {
                    'excellent': excellent,
                    'good': good,
                    'pass': pass_count,
                    'fail': fail
                },
                'subject_scores': [  # 模拟数据
                    {'name': '数学', 'average_score': 85},
                    {'name': '语文', 'average_score': 78},
                    {'name': '英语', 'average_score': 82}
                ],
                'score_trend': [  # 模拟数据
                    {'date': '2024-01-01', 'score': 75},
                    {'date': '2024-01-08', 'score': 78},
                    {'date': '2024-01-15', 'score': 82},
                    {'date': '2024-01-22', 'score': 85}
                ],
                'time_distribution': {
                    'morning': 25,
                    'afternoon': 35,
                    'evening': 30,
                    'night': 10
                },
                'device_stats': {
                    'mobile': 60,
                    'tablet': 25,
                    'desktop': 15
                },
                'average_study_duration': 45,
                'continuous_study_days': 15,
                'homework_on_time_rate': 85,
                'exam_participation_rate': 92,
                'student_ranking': [],  # 实际应该查询学生成绩排名
                'course_ranking': [],   # 实际应该查询课程热度排名
                'question_ranking': []  # 实际应该查询题目正确率排名
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取教学统计失败: {str(e)}',
            'code': 'INTERNAL_ERROR'
        }), 500

@statistics_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard_statistics():
    """获取仪表板统计信息"""
    try:
        user_id = get_jwt_identity()
        user = User.find_by_id(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        if user.role == 'teacher':
            # 教师统计
            courses = Course.get_by_teacher(user_id)
            questions = Question.get_by_teacher(user_id)
            homeworks = Homework.get_by_teacher(user_id)
            exams = Exam.get_by_teacher(user_id)
            
            # 学生数量
            student_ids = set()
            for course in courses:
                if course.student_id:
                    student_ids.add(course.student_id)
            
            return jsonify({
                'success': True,
                'data': {
                    'totalStudents': len(student_ids),
                    'totalCourses': len(courses),
                    'totalQuestions': len(questions),
                    'totalHomeworks': len(homeworks),
                    'totalExams': len(exams),
                    'pendingGrading': len([h for h in homeworks if h.status == 'submitted']) + 
                                    len([e for e in exams if e.status == 'submitted'])
                }
            })
        
        elif user.role == 'student':
            # 学生统计
            courses = Course.get_by_student(user_id)
            homeworks = Homework.get_by_student(user_id)
            exams = Exam.get_by_student(user_id)
            
            # 计算平均分
            graded_homeworks = [h for h in homeworks if h.status == 'graded' and h.score is not None]
            graded_exams = [e for e in exams if e.status == 'graded' and e.score is not None]
            
            total_score = 0
            total_count = 0
            
            for homework in graded_homeworks:
                if homework.total_points and homework.total_points > 0:
                    total_score += (homework.score / homework.total_points) * 100
                    total_count += 1
            
            for exam in graded_exams:
                if exam.total_points and exam.total_points > 0:
                    total_score += (exam.score / exam.total_points) * 100
                    total_count += 1
            
            average_score = round(total_score / total_count, 1) if total_count > 0 else 0
            
            return jsonify({
                'success': True,
                'data': {
                    'totalCourses': len(courses),
                    'totalHomeworks': len(homeworks),
                    'totalExams': len(exams),
                    'averageScore': average_score,
                    'completedHomeworks': len([h for h in homeworks if h.status in ['submitted', 'graded']]),
                    'completedExams': len([e for e in exams if e.status in ['submitted', 'graded']]),
                    'studyDays': 30  # 简化处理，实际应该计算学习天数
                }
            })
        
        else:
            return jsonify({
                'success': False,
                'message': '未知用户角色',
                'code': 'INVALID_ROLE'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取统计信息失败: {str(e)}',
            'code': 'INTERNAL_ERROR'
        }), 500