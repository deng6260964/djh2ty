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
        user_id = int(get_jwt_identity())
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
        
        # 获取学生详细信息（简化版本）
        student_details = []
        for student in paginated_students:
            student_dict = student.to_dict()
            
            # 简化统计信息，避免调用不存在的方法
            try:
                # 获取课程统计 - 通过course_students表
                course_query = '''
                    SELECT COUNT(*) as total FROM course_students 
                    WHERE student_id = ? AND status = 'enrolled'
                '''
                course_result = db.execute_query(course_query, (student.id,))
                course_count = course_result[0]['total'] if course_result else 0
                
                student_dict['statistics'] = {
                    'courses': {
                        'total': course_count,
                        'completed': 0,
                        'scheduled': 0,
                        'in_progress': course_count
                    },
                    'homeworks': {
                        'total': 0,
                        'completed': 0,
                        'pending': 0,
                        'submitted': 0
                    },
                    'exams': {
                        'total': 0,
                        'completed': 0,
                        'scheduled': 0,
                        'in_progress': 0
                    }
                }
            except Exception as e:
                # 如果统计失败，使用默认值
                student_dict['statistics'] = {
                    'courses': {'total': 0, 'completed': 0, 'scheduled': 0, 'in_progress': 0},
                    'homeworks': {'total': 0, 'completed': 0, 'pending': 0, 'submitted': 0},
                    'exams': {'total': 0, 'completed': 0, 'scheduled': 0, 'in_progress': 0}
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
        user_id = int(get_jwt_identity())
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
        
        # 简化详细统计信息
        try:
            # 获取课程信息 - 通过course_students表
            course_query = '''
                SELECT c.*, cs.enrollment_date, cs.status as enrollment_status
                FROM courses c
                JOIN course_students cs ON c.id = cs.course_id
                WHERE cs.student_id = ? AND cs.status = 'enrolled'
                ORDER BY c.start_time ASC
            '''
            course_results = db.execute_query(course_query, (student_id,))
            course_details = [dict(row) for row in course_results] if course_results else []
            
            student_dict['details'] = {
                'courses': course_details,
                'homeworks': [],  # 暂时为空，避免调用不存在的方法
                'exams': [],      # 暂时为空，避免调用不存在的方法
                'performance': {
                    'homework_avg_score': 0,
                    'exam_avg_score': 0,
                    'overall_progress': 0
                }
            }
        except Exception as e:
            # 如果获取详细信息失败，使用默认值
            student_dict['details'] = {
                'courses': [],
                'homeworks': [],
                'exams': [],
                'performance': {
                    'homework_avg_score': 0,
                    'exam_avg_score': 0,
                    'overall_progress': 0
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
        user_id = int(get_jwt_identity())
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
        user_id = int(get_jwt_identity())
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

@students_bp.route('', methods=['POST'])
@jwt_required()
def create_student():
    """创建学生"""
    try:
        print(f"[DEBUG] 开始创建学生")
        user_id = int(get_jwt_identity())
        user = User.find_by_id(user_id)
        
        if not user:
            print(f"[ERROR] 用户不存在 - user_id: {user_id}")
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        # 只有教师可以创建学生
        if user.role != 'teacher':
            print(f"[ERROR] 权限不足 - user_id: {user_id}, role: {user.role}")
            return jsonify({
                'success': False,
                'message': '只有教师可以创建学生',
                'code': 'PERMISSION_DENIED'
            }), 403
        
        data = request.get_json()
        print(f"[DEBUG] 接收到创建学生数据: {data.get('name', 'N/A')}, {data.get('phone', 'N/A')}")
        
        # 验证必填字段
        required_fields = ['name', 'phone', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'缺少必填字段: {field}',
                    'code': 'MISSING_REQUIRED_FIELD'
                }), 400
        
        # 检查手机号是否已存在
        existing_user = User.find_by_phone(data['phone'])
        if existing_user:
            print(f"[ERROR] 手机号已存在 - phone: {data['phone']}")
            return jsonify({
                'success': False,
                'message': '手机号已存在',
                'code': 'PHONE_EXISTS'
            }), 400
        
        # 创建学生用户
        print(f"[DEBUG] 开始创建学生用户")
        student_data = {
            'name': data['name'],
            'phone': data['phone'],
            'password': data['password'],
            'role': 'student',
            'email': data.get('email', ''),
            'avatar': data.get('avatar', ''),
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        student = User.create(student_data)
        print(f"[DEBUG] 学生创建成功 - student_id: {student.id}, name: {student.name}")
        
        return jsonify({
            'success': True,
            'message': '学生创建成功',
            'data': {
                'student': student.to_dict()
            }
        })
        
    except Exception as e:
        print(f"[ERROR] 创建学生失败 - error: {str(e)}")
        import traceback
        print(f"[ERROR] 详细错误信息: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'message': f'创建学生失败: {str(e)}',
            'code': 'CREATE_STUDENT_ERROR'
        }), 500

@students_bp.route('/<int:student_id>', methods=['PUT'])
@jwt_required()
def update_student(student_id):
    """更新学生信息"""
    try:
        print(f"[DEBUG] 开始更新学生信息 - student_id: {student_id}")
        user_id = int(get_jwt_identity())
        user = User.find_by_id(user_id)
        
        if not user:
            print(f"[ERROR] 用户不存在 - user_id: {user_id}")
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        # 只有教师可以更新学生信息，或者学生更新自己的信息
        if user.role == 'student' and user.id != student_id:
            print(f"[ERROR] 权限不足 - user_id: {user_id}, role: {user.role}, target_student_id: {student_id}")
            return jsonify({
                'success': False,
                'message': '无权修改此学生信息',
                'code': 'ACCESS_DENIED'
            }), 403
        
        student = User.find_by_id(student_id)
        if not student or student.role != 'student':
            print(f"[ERROR] 学生不存在 - student_id: {student_id}")
            return jsonify({
                'success': False,
                'message': '学生不存在',
                'code': 'STUDENT_NOT_FOUND'
            }), 404
        
        data = request.get_json()
        print(f"[DEBUG] 接收到更新数据 - student: {student.name}, data: {list(data.keys()) if data else 'None'}")
        
        # 如果更新手机号，检查是否已存在
        if 'phone' in data and data['phone'] != student.phone:
            existing_user = User.find_by_phone(data['phone'])
            if existing_user:
                print(f"[ERROR] 手机号已存在 - phone: {data['phone']}")
                return jsonify({
                    'success': False,
                    'message': '手机号已存在',
                    'code': 'PHONE_EXISTS'
                }), 400
        
        # 更新学生信息
        print(f"[DEBUG] 开始更新学生信息")
        update_data = {
            'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 允许更新的字段
        allowed_fields = ['name', 'phone', 'email', 'avatar']
        for field in allowed_fields:
            if field in data:
                update_data[field] = data[field]
        
        # 如果是教师或学生更新自己的密码
        if 'password' in data and (user.role == 'teacher' or user.id == student_id):
            update_data['password'] = data['password']
        
        print(f"[DEBUG] 更新字段: {list(update_data.keys())}")
        student.update(update_data)
        print(f"[DEBUG] 学生信息更新成功 - student_id: {student_id}")
        
        return jsonify({
            'success': True,
            'message': '学生信息更新成功',
            'data': {
                'student': student.to_dict()
            }
        })
        
    except Exception as e:
        print(f"[ERROR] 更新学生信息失败 - student_id: {student_id}, error: {str(e)}")
        import traceback
        print(f"[ERROR] 详细错误信息: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'message': f'更新学生信息失败: {str(e)}',
            'code': 'UPDATE_STUDENT_ERROR'
        }), 500

@students_bp.route('/<int:student_id>', methods=['DELETE'])
@jwt_required()
def delete_student(student_id):
    """删除学生"""
    try:
        print(f"[DEBUG] 开始删除学生 - student_id: {student_id}")
        user_id = int(get_jwt_identity())
        user = User.find_by_id(user_id)
        
        if not user:
            print(f"[ERROR] 用户不存在 - user_id: {user_id}")
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        # 只有教师可以删除学生
        if user.role != 'teacher':
            print(f"[ERROR] 权限不足 - user_id: {user_id}, role: {user.role}")
            return jsonify({
                'success': False,
                'message': '只有教师可以删除学生',
                'code': 'PERMISSION_DENIED'
            }), 403
        
        student = User.find_by_id(student_id)
        if not student or student.role != 'student':
            print(f"[ERROR] 学生不存在 - student_id: {student_id}")
            return jsonify({
                'success': False,
                'message': '学生不存在',
                'code': 'STUDENT_NOT_FOUND'
            }), 404
        
        print(f"[DEBUG] 找到学生 - name: {student.name}, id: {student.id}")
        
        # 删除学生相关的关联数据
        try:
            print(f"[DEBUG] 开始删除学生关联数据")
            
            # 删除课程关联
            print(f"[DEBUG] 删除课程关联数据")
            db.execute_update('DELETE FROM course_students WHERE student_id = ?', (student_id,))
            
            # 删除作业答案
            print(f"[DEBUG] 删除作业答案数据")
            db.execute_update('DELETE FROM homework_answers WHERE student_id = ?', (student_id,))
            
            # 删除考试答案
            print(f"[DEBUG] 删除考试答案数据")
            db.execute_update('DELETE FROM exam_answers WHERE student_id = ?', (student_id,))
            
            # 删除学生用户
            print(f"[DEBUG] 删除学生用户记录")
            student.delete()
            
            print(f"[DEBUG] 学生删除成功 - student_id: {student_id}")
            
        except Exception as e:
            print(f"[ERROR] 删除学生关联数据失败 - student_id: {student_id}, error: {str(e)}")
            print(f"[ERROR] 详细错误信息: {repr(e)}")
            import traceback
            print(f"[ERROR] 错误堆栈: {traceback.format_exc()}")
            return jsonify({
                'success': False,
                'message': f'删除学生关联数据失败: {str(e)}',
                'code': 'DELETE_STUDENT_DATA_ERROR'
            }), 500
        
        return jsonify({
            'success': True,
            'message': '学生删除成功'
        })
        
    except Exception as e:
        print(f"[ERROR] 删除学生失败 - student_id: {student_id}, error: {str(e)}")
        print(f"[ERROR] 详细错误信息: {repr(e)}")
        import traceback
        print(f"[ERROR] 错误堆栈: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'message': f'删除学生失败: {str(e)}',
            'code': 'DELETE_STUDENT_ERROR'
        }), 500

@students_bp.route('/<int:student_id>/progress', methods=['GET'])
@jwt_required()
def get_student_progress(student_id):
    """获取学生学习进度"""
    try:
        print(f"[DEBUG] 获取学生进度 - student_id: {student_id}")
        user_id = int(get_jwt_identity())
        user = User.find_by_id(user_id)
        
        if not user:
            print(f"[ERROR] 用户不存在 - user_id: {user_id}")
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        # 只有教师可以查看学生进度，或者学生查看自己的进度
        if user.role == 'student' and user.id != student_id:
            print(f"[ERROR] 权限不足 - user_id: {user_id}, role: {user.role}, target_student_id: {student_id}")
            return jsonify({
                'success': False,
                'message': '无权查看此学生进度',
                'code': 'ACCESS_DENIED'
            }), 403
        
        student = User.find_by_id(student_id)
        if not student or student.role != 'student':
            print(f"[ERROR] 学生不存在 - student_id: {student_id}")
            return jsonify({
                'success': False,
                'message': '学生不存在',
                'code': 'STUDENT_NOT_FOUND'
            }), 404
        
        print(f"[DEBUG] 开始获取学生进度数据 - student: {student.name}")
        
        # 获取课程进度
        try:
            print(f"[DEBUG] 开始获取课程进度")
            from models.course_student import CourseStudent
            course_enrollments = CourseStudent.get_by_student(student_id)
            print(f"[DEBUG] 找到课程注册记录: {len(course_enrollments)}")
            
            courses = []
            for enrollment in course_enrollments:
                course = Course.find_by_id(enrollment.course_id)
                if course:
                    courses.append(course)
            
            print(f"[DEBUG] 有效课程数量: {len(courses)}")
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
        except Exception as e:
            print(f"[ERROR] 获取课程进度失败: {str(e)}")
            course_progress = {
                'total': 0, 'completed': 0, 'in_progress': 0, 
                'scheduled': 0, 'cancelled': 0, 'completion_rate': 0
            }
            courses = []
        
        # 获取作业进度
        try:
            print(f"[DEBUG] 开始获取作业进度")
            homeworks = Homework.get_by_student(student_id)
            print(f"[DEBUG] 找到作业数量: {len(homeworks)}")
            
            homework_progress = {
                'total': len(homeworks),
                'pending': len([h for h in homeworks if h.status == 'assigned']),
                'submitted': len([h for h in homeworks if h.status == 'submitted']),
                'graded': len([h for h in homeworks if h.status == 'graded'])
            }
            homework_progress['completion_rate'] = round(
                (homework_progress['submitted'] + homework_progress['graded']) / homework_progress['total'] * 100, 2
            ) if homework_progress['total'] > 0 else 0
        except Exception as e:
            print(f"[ERROR] 获取作业进度失败: {str(e)}")
            homework_progress = {
                'total': 0, 'pending': 0, 'submitted': 0, 
                'graded': 0, 'completion_rate': 0
            }
            homeworks = []
        
        # 获取考试进度
        try:
            print(f"[DEBUG] 开始获取考试进度")
            exams = Exam.get_by_student(student_id)
            print(f"[DEBUG] 找到考试数量: {len(exams)}")
            
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
        except Exception as e:
            print(f"[ERROR] 获取考试进度失败: {str(e)}")
            exam_progress = {
                'total': 0, 'scheduled': 0, 'in_progress': 0, 
                'completed': 0, 'graded': 0, 'completion_rate': 0
            }
            exams = []
        
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
        try:
            print(f"[DEBUG] 开始获取最近活动")
            recent_activities = []
            
            # 添加最近的课程活动
            if courses:
                recent_courses = sorted([c for c in courses if hasattr(c, 'updated_at') and c.updated_at], 
                                      key=lambda x: x.updated_at, reverse=True)[:5]
                for course in recent_courses:
                    recent_activities.append({
                        'type': 'course',
                        'id': course.id,
                        'title': course.title,
                        'status': course.status,
                        'updated_at': course.updated_at
                    })
            
            # 添加最近的作业活动
            if homeworks:
                recent_homeworks = sorted([h for h in homeworks if hasattr(h, 'updated_at') and h.updated_at], 
                                        key=lambda x: x.updated_at, reverse=True)[:5]
                for homework in recent_homeworks:
                    recent_activities.append({
                        'type': 'homework',
                        'id': homework.id,
                        'title': homework.title,
                        'status': homework.status,
                        'updated_at': homework.updated_at
                    })
            
            # 添加最近的考试活动
            if exams:
                recent_exams = sorted([e for e in exams if hasattr(e, 'updated_at') and e.updated_at], 
                                    key=lambda x: x.updated_at, reverse=True)[:5]
                for exam in recent_exams:
                    recent_activities.append({
                        'type': 'exam',
                        'id': exam.id,
                        'title': exam.title,
                        'status': exam.status,
                        'updated_at': exam.updated_at
                    })
            
            # 按时间排序最近活动
            recent_activities = sorted([a for a in recent_activities if a.get('updated_at')], 
                                     key=lambda x: x['updated_at'], reverse=True)[:10]
            print(f"[DEBUG] 最近活动数量: {len(recent_activities)}")
        except Exception as e:
            print(f"[ERROR] 获取最近活动失败: {str(e)}")
            recent_activities = []
        
        print(f"[DEBUG] 学生进度获取成功 - student_id: {student_id}")
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
        print(f"[ERROR] 获取学生进度失败 - student_id: {student_id}, error: {str(e)}")
        import traceback
        print(f"[ERROR] 详细错误信息: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'message': f'获取学生进度失败: {str(e)}',
            'code': 'GET_STUDENT_PROGRESS_ERROR'
        }), 500