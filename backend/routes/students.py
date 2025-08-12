from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import json

from models.user import User
from models.course import Course
from models.homework import Homework
from models.homework_answer import HomeworkAnswer
from models.exam import Exam
from models.exam_answer import ExamAnswer
from models.database import db

students_bp = Blueprint('students', __name__, url_prefix='/api/students')

@students_bp.route('', methods=['GET'])
@jwt_required()
def get_students():
    """获取学生列表"""
    try:
        user_id = get_jwt_identity()
        user = User.find_by_id(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        # 只有教师可以查看学生列表
        if user.role != 'teacher':
            return jsonify({
                'success': False,
                'message': '只有教师可以查看学生列表',
                'code': 'PERMISSION_DENIED'
            }), 403
        
        # 获取查询参数
        search = request.args.get('search', '')
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        
        # 获取所有学生
        students = User.get_all_students()
        
        # 搜索过滤
        if search:
            filtered_students = []
            for student in students:
                if (search.lower() in student.name.lower() or 
                    search in student.phone or 
                    (student.email and search.lower() in student.email.lower())):
                    filtered_students.append(student)
            students = filtered_students
        
        # 分页处理
        total = len(students)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_students = students[start_idx:end_idx]
        
        # 获取学生详细信息（包括统计数据）
        student_details = []
        for student in paginated_students:
            student_dict = student.to_dict()
            
            # 获取课程统计
            courses = Course.get_by_student(student.id)
            course_stats = {
                'total': len(courses),
                'completed': len([c for c in courses if c.status == 'completed']),
                'scheduled': len([c for c in courses if c.status == 'scheduled']),
                'in_progress': len([c for c in courses if c.status == 'in_progress'])
            }
            
            # 获取作业统计
            homeworks = Homework.get_by_student(student.id)
            homework_stats = {
                'total': len(homeworks),
                'completed': len([h for h in homeworks if h.status == 'graded']),
                'pending': len([h for h in homeworks if h.status == 'pending']),
                'submitted': len([h for h in homeworks if h.status == 'submitted'])
            }
            
            # 获取考试统计
            exams = Exam.get_by_student(student.id)
            exam_stats = {
                'total': len(exams),
                'completed': len([e for e in exams if e.status == 'graded']),
                'scheduled': len([e for e in exams if e.status == 'scheduled']),
                'in_progress': len([e for e in exams if e.status == 'in_progress'])
            }
            
            student_dict['statistics'] = {
                'courses': course_stats,
                'homeworks': homework_stats,
                'exams': exam_stats
            }
            
            student_details.append(student_dict)
        
        return jsonify({
            'success': True,
            'data': {
                'students': student_details,
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total': total,
                    'pages': (total + limit - 1) // limit
                }
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取学生列表失败: {str(e)}',
            'code': 'GET_STUDENTS_ERROR'
        }), 500

@students_bp.route('/<int:student_id>', methods=['GET'])
@jwt_required()
def get_student(student_id):
    """获取学生详情"""
    try:
        user_id = get_jwt_identity()
        user = User.find_by_id(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        # 只有教师可以查看学生详情，或者学生查看自己的详情
        if user.role == 'student' and user.id != student_id:
            return jsonify({
                'success': False,
                'message': '无权查看此学生信息',
                'code': 'ACCESS_DENIED'
            }), 403
        
        student = User.find_by_id(student_id)
        if not student or student.role != 'student':
            return jsonify({
                'success': False,
                'message': '学生不存在',
                'code': 'STUDENT_NOT_FOUND'
            }), 404
        
        student_dict = student.to_dict()
        
        # 获取详细统计信息
        # 课程信息
        courses = Course.get_by_student(student_id)
        course_details = []
        for course in courses:
            course_detail = Course.get_course_with_details(course.id)
            course_details.append(course_detail)
        
        # 作业信息
        homeworks = Homework.get_by_student(student_id)
        homework_details = []
        for homework in homeworks:
            homework_detail = Homework.get_homework_with_details(homework.id)
            homework_details.append(homework_detail)
        
        # 考试信息
        exams = Exam.get_by_student(student_id)
        exam_details = []
        for exam in exams:
            exam_detail = Exam.get_exam_with_details(exam.id)
            exam_details.append(exam_detail)
        
        # 计算平均分
        graded_homeworks = [h for h in homeworks if h.status == 'graded' and h.score is not None]
        homework_avg_score = sum([h.score for h in graded_homeworks]) / len(graded_homeworks) if graded_homeworks else 0
        
        graded_exams = [e for e in exams if e.status == 'graded' and e.score is not None]
        exam_avg_score = sum([e.score for e in graded_exams]) / len(graded_exams) if graded_exams else 0
        
        # 学习进度
        total_courses = len(courses)
        completed_courses = len([c for c in courses if c.status == 'completed'])
        progress = (completed_courses / total_courses * 100) if total_courses > 0 else 0
        
        student_dict['details'] = {
            'courses': course_details,
            'homeworks': homework_details,
            'exams': exam_details,
            'performance': {
                'homework_avg_score': round(homework_avg_score, 2),
                'exam_avg_score': round(exam_avg_score, 2),
                'overall_progress': round(progress, 2)
            }
        }
        
        return jsonify({
            'success': True,
            'data': {
                'student': student_dict
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取学生详情失败: {str(e)}',
            'code': 'GET_STUDENT_ERROR'
        }), 500

@students_bp.route('/<int:student_id>/performance', methods=['GET'])
@jwt_required()
def get_student_performance(student_id):
    """获取学生学习表现分析"""
    try:
        user_id = get_jwt_identity()
        user = User.find_by_id(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        # 只有教师可以查看学生表现，或者学生查看自己的表现
        if user.role == 'student' and user.id != student_id:
            return jsonify({
                'success': False,
                'message': '无权查看此学生表现',
                'code': 'ACCESS_DENIED'
            }), 403
        
        student = User.find_by_id(student_id)
        if not student or student.role != 'student':
            return jsonify({
                'success': False,
                'message': '学生不存在',
                'code': 'STUDENT_NOT_FOUND'
            }), 404
        
        # 获取时间范围参数
        days = int(request.args.get('days', 30))  # 默认30天
        start_date = datetime.now() - timedelta(days=days)
        
        # 获取课程表现
        courses = Course.get_by_student(student_id)
        recent_courses = [c for c in courses if datetime.strptime(c.created_at, '%Y-%m-%d %H:%M:%S') >= start_date]
        
        course_performance = {
            'total_courses': len(recent_courses),
            'completed_courses': len([c for c in recent_courses if c.status == 'completed']),
            'attendance_rate': 0
        }
        
        if course_performance['total_courses'] > 0:
            course_performance['attendance_rate'] = round(
                course_performance['completed_courses'] / course_performance['total_courses'] * 100, 2
            )
        
        # 获取作业表现
        homeworks = Homework.get_by_student(student_id)
        recent_homeworks = [h for h in homeworks if datetime.strptime(h.created_at, '%Y-%m-%d %H:%M:%S') >= start_date]
        
        graded_homeworks = [h for h in recent_homeworks if h.status == 'graded' and h.score is not None]
        homework_scores = [h.score for h in graded_homeworks]
        
        homework_performance = {
            'total_homeworks': len(recent_homeworks),
            'submitted_homeworks': len([h for h in recent_homeworks if h.status in ['submitted', 'graded']]),
            'graded_homeworks': len(graded_homeworks),
            'avg_score': round(sum(homework_scores) / len(homework_scores), 2) if homework_scores else 0,
            'max_score': max(homework_scores) if homework_scores else 0,
            'min_score': min(homework_scores) if homework_scores else 0,
            'submission_rate': 0
        }
        
        if homework_performance['total_homeworks'] > 0:
            homework_performance['submission_rate'] = round(
                homework_performance['submitted_homeworks'] / homework_performance['total_homeworks'] * 100, 2
            )
        
        # 获取考试表现
        exams = Exam.get_by_student(student_id)
        recent_exams = [e for e in exams if datetime.strptime(e.created_at, '%Y-%m-%d %H:%M:%S') >= start_date]
        
        graded_exams = [e for e in recent_exams if e.status == 'graded' and e.score is not None]
        exam_scores = [e.score for e in graded_exams]
        
        exam_performance = {
            'total_exams': len(recent_exams),
            'completed_exams': len([e for e in recent_exams if e.status in ['completed', 'graded']]),
            'graded_exams': len(graded_exams),
            'avg_score': round(sum(exam_scores) / len(exam_scores), 2) if exam_scores else 0,
            'max_score': max(exam_scores) if exam_scores else 0,
            'min_score': min(exam_scores) if exam_scores else 0,
            'completion_rate': 0
        }
        
        if exam_performance['total_exams'] > 0:
            exam_performance['completion_rate'] = round(
                exam_performance['completed_exams'] / exam_performance['total_exams'] * 100, 2
            )
        
        # 学习趋势分析（按周统计）
        weekly_stats = []
        for i in range(4):  # 最近4周
            week_start = datetime.now() - timedelta(weeks=i+1)
            week_end = datetime.now() - timedelta(weeks=i)
            
            week_homeworks = [h for h in homeworks if 
                            h.status == 'graded' and h.score is not None and
                            week_start <= datetime.strptime(h.updated_at, '%Y-%m-%d %H:%M:%S') <= week_end]
            
            week_exams = [e for e in exams if 
                         e.status == 'graded' and e.score is not None and
                         week_start <= datetime.strptime(e.updated_at, '%Y-%m-%d %H:%M:%S') <= week_end]
            
            week_homework_avg = sum([h.score for h in week_homeworks]) / len(week_homeworks) if week_homeworks else 0
            week_exam_avg = sum([e.score for e in week_exams]) / len(week_exams) if week_exams else 0
            
            weekly_stats.append({
                'week': f'第{4-i}周',
                'homework_avg': round(week_homework_avg, 2),
                'exam_avg': round(week_exam_avg, 2),
                'homework_count': len(week_homeworks),
                'exam_count': len(week_exams)
            })
        
        # 强弱项分析（基于题目分类）
        # 这里简化处理，实际应该根据题目分类统计
        strengths_weaknesses = {
            'strengths': [],  # 强项
            'weaknesses': []  # 弱项
        }
        
        return jsonify({
            'success': True,
            'data': {
                'student_id': student_id,
                'period_days': days,
                'course_performance': course_performance,
                'homework_performance': homework_performance,
                'exam_performance': exam_performance,
                'weekly_trends': weekly_stats,
                'strengths_weaknesses': strengths_weaknesses
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取学生表现分析失败: {str(e)}',
            'code': 'GET_STUDENT_PERFORMANCE_ERROR'
        }), 500

@students_bp.route('/statistics', methods=['GET'])
@jwt_required()
def get_students_statistics():
    """获取学生整体统计信息"""
    try:
        user_id = get_jwt_identity()
        user = User.find_by_id(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        # 只有教师可以查看整体统计
        if user.role != 'teacher':
            return jsonify({
                'success': False,
                'message': '只有教师可以查看学生统计',
                'code': 'PERMISSION_DENIED'
            }), 403
        
        # 获取所有学生
        students = User.get_all_students()
        total_students = len(students)
        
        # 活跃学生统计（最近30天有活动的学生）
        active_date = datetime.now() - timedelta(days=30)
        active_students = 0
        
        for student in students:
            if student.last_login_at:
                last_login = datetime.strptime(student.last_login_at, '%Y-%m-%d %H:%M:%S')
                if last_login >= active_date:
                    active_students += 1
        
        # 课程统计
        all_courses = []
        for student in students:
            courses = Course.get_by_student(student.id)
            all_courses.extend(courses)
        
        course_stats = {
            'total_courses': len(all_courses),
            'completed_courses': len([c for c in all_courses if c.status == 'completed']),
            'scheduled_courses': len([c for c in all_courses if c.status == 'scheduled']),
            'in_progress_courses': len([c for c in all_courses if c.status == 'in_progress'])
        }
        
        # 作业统计
        all_homeworks = []
        for student in students:
            homeworks = Homework.get_by_student(student.id)
            all_homeworks.extend(homeworks)
        
        graded_homeworks = [h for h in all_homeworks if h.status == 'graded' and h.score is not None]
        homework_scores = [h.score for h in graded_homeworks]
        
        homework_stats = {
            'total_homeworks': len(all_homeworks),
            'submitted_homeworks': len([h for h in all_homeworks if h.status in ['submitted', 'graded']]),
            'graded_homeworks': len(graded_homeworks),
            'avg_score': round(sum(homework_scores) / len(homework_scores), 2) if homework_scores else 0,
            'submission_rate': 0
        }
        
        if homework_stats['total_homeworks'] > 0:
            homework_stats['submission_rate'] = round(
                homework_stats['submitted_homeworks'] / homework_stats['total_homeworks'] * 100, 2
            )
        
        # 考试统计
        all_exams = []
        for student in students:
            exams = Exam.get_by_student(student.id)
            all_exams.extend(exams)
        
        graded_exams = [e for e in all_exams if e.status == 'graded' and e.score is not None]
        exam_scores = [e.score for e in graded_exams]
        
        exam_stats = {
            'total_exams': len(all_exams),
            'completed_exams': len([e for e in all_exams if e.status in ['completed', 'graded']]),
            'graded_exams': len(graded_exams),
            'avg_score': round(sum(exam_scores) / len(exam_scores), 2) if exam_scores else 0,
            'completion_rate': 0
        }
        
        if exam_stats['total_exams'] > 0:
            exam_stats['completion_rate'] = round(
                exam_stats['completed_exams'] / exam_stats['total_exams'] * 100, 2
            )
        
        # 学习活跃度分析
        activity_stats = {
            'total_students': total_students,
            'active_students': active_students,
            'activity_rate': round(active_students / total_students * 100, 2) if total_students > 0 else 0
        }
        
        # 成绩分布
        all_scores = homework_scores + exam_scores
        score_distribution = {
            'excellent': len([s for s in all_scores if s >= 90]),  # 优秀
            'good': len([s for s in all_scores if 80 <= s < 90]),  # 良好
            'average': len([s for s in all_scores if 70 <= s < 80]),  # 中等
            'poor': len([s for s in all_scores if s < 70])  # 较差
        }
        
        return jsonify({
            'success': True,
            'data': {
                'activity_stats': activity_stats,
                'course_stats': course_stats,
                'homework_stats': homework_stats,
                'exam_stats': exam_stats,
                'score_distribution': score_distribution
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取学生统计失败: {str(e)}',
            'code': 'GET_STUDENTS_STATISTICS_ERROR'
        }), 500

@students_bp.route('/<int:student_id>/progress', methods=['GET'])
@jwt_required()
def get_student_progress(student_id):
    """获取学生学习进度"""
    try:
        user_id = get_jwt_identity()
        user = User.find_by_id(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        # 只有教师可以查看学生进度，或者学生查看自己的进度
        if user.role == 'student' and user.id != student_id:
            return jsonify({
                'success': False,
                'message': '无权查看此学生进度',
                'code': 'ACCESS_DENIED'
            }), 403
        
        student = User.find_by_id(student_id)
        if not student or student.role != 'student':
            return jsonify({
                'success': False,
                'message': '学生不存在',
                'code': 'STUDENT_NOT_FOUND'
            }), 404
        
        # 获取课程进度
        courses = Course.get_by_student(student_id)
        course_progress = {
            'total': len(courses),
            'completed': len([c for c in courses if c.status == 'completed']),
            'in_progress': len([c for c in courses if c.status == 'in_progress']),
            'scheduled': len([c for c in courses if c.status == 'scheduled']),
            'cancelled': len([c for c in courses if c.status == 'cancelled'])
        }
        course_progress['completion_rate'] = round(
            course_progress['completed'] / course_progress['total'] * 100, 2
        ) if course_progress['total'] > 0 else 0
        
        # 获取作业进度
        homeworks = Homework.get_by_student(student_id)
        homework_progress = {
            'total': len(homeworks),
            'pending': len([h for h in homeworks if h.status == 'pending']),
            'submitted': len([h for h in homeworks if h.status == 'submitted']),
            'graded': len([h for h in homeworks if h.status == 'graded'])
        }
        homework_progress['completion_rate'] = round(
            (homework_progress['submitted'] + homework_progress['graded']) / homework_progress['total'] * 100, 2
        ) if homework_progress['total'] > 0 else 0
        
        # 获取考试进度
        exams = Exam.get_by_student(student_id)
        exam_progress = {
            'total': len(exams),
            'scheduled': len([e for e in exams if e.status == 'scheduled']),
            'in_progress': len([e for e in exams if e.status == 'in_progress']),
            'completed': len([e for e in exams if e.status == 'completed']),
            'graded': len([e for e in exams if e.status == 'graded'])
        }
        exam_progress['completion_rate'] = round(
            (exam_progress['completed'] + exam_progress['graded']) / exam_progress['total'] * 100, 2
        ) if exam_progress['total'] > 0 else 0
        
        # 整体学习进度
        total_tasks = course_progress['total'] + homework_progress['total'] + exam_progress['total']
        completed_tasks = (course_progress['completed'] + 
                          homework_progress['submitted'] + homework_progress['graded'] +
                          exam_progress['completed'] + exam_progress['graded'])
        
        overall_progress = {
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'completion_rate': round(completed_tasks / total_tasks * 100, 2) if total_tasks > 0 else 0
        }
        
        # 最近活动
        recent_activities = []
        
        # 添加最近的课程活动
        recent_courses = sorted(courses, key=lambda x: x.updated_at, reverse=True)[:5]
        for course in recent_courses:
            recent_activities.append({
                'type': 'course',
                'id': course.id,
                'title': course.title,
                'status': course.status,
                'updated_at': course.updated_at
            })
        
        # 添加最近的作业活动
        recent_homeworks = sorted(homeworks, key=lambda x: x.updated_at, reverse=True)[:5]
        for homework in recent_homeworks:
            recent_activities.append({
                'type': 'homework',
                'id': homework.id,
                'title': homework.title,
                'status': homework.status,
                'updated_at': homework.updated_at
            })
        
        # 添加最近的考试活动
        recent_exams = sorted(exams, key=lambda x: x.updated_at, reverse=True)[:5]
        for exam in recent_exams:
            recent_activities.append({
                'type': 'exam',
                'id': exam.id,
                'title': exam.title,
                'status': exam.status,
                'updated_at': exam.updated_at
            })
        
        # 按时间排序最近活动
        recent_activities = sorted(recent_activities, key=lambda x: x['updated_at'], reverse=True)[:10]
        
        return jsonify({
            'success': True,
            'data': {
                'student_id': student_id,
                'course_progress': course_progress,
                'homework_progress': homework_progress,
                'exam_progress': exam_progress,
                'overall_progress': overall_progress,
                'recent_activities': recent_activities
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取学生进度失败: {str(e)}',
            'code': 'GET_STUDENT_PROGRESS_ERROR'
        }), 500