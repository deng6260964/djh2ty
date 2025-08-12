from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import json

from models.user import User
from models.homework import Homework, HomeworkAnswer
from models.question import Question
from models.database import db

homework_bp = Blueprint('homework', __name__, url_prefix='/api/homework')

def validate_datetime(date_string):
    """验证日期时间格式"""
    try:
        return datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        return None

def validate_homework_status(status):
    """验证作业状态"""
    valid_statuses = ['draft', 'published', 'completed', 'graded']
    return status in valid_statuses

@homework_bp.route('', methods=['GET'])
@jwt_required()
def get_homework_list():
    """获取作业列表"""
    try:
        user_id = get_jwt_identity()
        user = User.find_by_id(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        # 获取查询参数
        status = request.args.get('status')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        
        # 验证状态
        if status and not validate_homework_status(status):
            return jsonify({
                'success': False,
                'message': '作业状态不正确',
                'code': 'INVALID_STATUS'
            }), 400
        
        # 验证日期
        start_dt = None
        end_dt = None
        if start_date:
            start_dt = validate_datetime(start_date + ' 00:00:00')
            if not start_dt:
                return jsonify({
                    'success': False,
                    'message': '开始日期格式不正确',
                    'code': 'INVALID_START_DATE'
                }), 400
        
        if end_date:
            end_dt = validate_datetime(end_date + ' 23:59:59')
            if not end_dt:
                return jsonify({
                    'success': False,
                    'message': '结束日期格式不正确',
                    'code': 'INVALID_END_DATE'
                }), 400
        
        # 根据用户角色获取作业
        if user.role == 'teacher':
            homework_list = Homework.get_by_teacher(user_id, status, start_dt, end_dt)
        else:  # student
            homework_list = Homework.get_by_student(user_id, status, start_dt, end_dt)
        
        # 分页处理
        total = len(homework_list)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_homework = homework_list[start_idx:end_idx]
        
        # 获取详细信息
        homework_details = []
        for hw in paginated_homework:
            hw_detail = Homework.get_homework_with_details(hw.id)
            homework_details.append(hw_detail)
        
        return jsonify({
            'success': True,
            'data': {
                'homework': homework_details,
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
            'message': f'获取作业列表失败: {str(e)}',
            'code': 'GET_HOMEWORK_LIST_ERROR'
        }), 500

@homework_bp.route('/<int:homework_id>', methods=['GET'])
@jwt_required()
def get_homework(homework_id):
    """获取作业详情"""
    try:
        user_id = get_jwt_identity()
        user = User.find_by_id(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        homework = Homework.find_by_id(homework_id)
        if not homework:
            return jsonify({
                'success': False,
                'message': '作业不存在',
                'code': 'HOMEWORK_NOT_FOUND'
            }), 404
        
        # 检查权限
        if user.role == 'teacher':
            if homework.teacher_id != user_id:
                return jsonify({
                    'success': False,
                    'message': '无权访问此作业',
                    'code': 'ACCESS_DENIED'
                }), 403
        else:  # student
            if homework.student_id != user_id:
                return jsonify({
                    'success': False,
                    'message': '无权访问此作业',
                    'code': 'ACCESS_DENIED'
                }), 403
        
        # 获取作业详情
        homework_detail = Homework.get_homework_with_details(homework_id)
        
        # 获取题目列表
        questions = Homework.get_homework_questions(homework_id)
        
        # 获取答案（如果是学生且已提交，或者是教师）
        answers = None
        if user.role == 'teacher' or homework.status in ['completed', 'graded']:
            answers = HomeworkAnswer.get_by_homework_id(homework_id)
        
        return jsonify({
            'success': True,
            'data': {
                'homework': homework_detail,
                'questions': [q.to_dict() for q in questions],
                'answers': [a.to_dict() for a in answers] if answers else None
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取作业详情失败: {str(e)}',
            'code': 'GET_HOMEWORK_ERROR'
        }), 500

@homework_bp.route('', methods=['POST'])
@jwt_required()
def create_homework():
    """创建作业"""
    try:
        user_id = get_jwt_identity()
        user = User.find_by_id(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        # 只有教师可以创建作业
        if user.role != 'teacher':
            return jsonify({
                'success': False,
                'message': '只有教师可以创建作业',
                'code': 'PERMISSION_DENIED'
            }), 403
        
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['title', 'student_id', 'due_date', 'questions']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'{field}不能为空',
                    'code': 'MISSING_FIELD'
                }), 400
        
        # 验证学生是否存在
        student = User.find_by_id(data['student_id'])
        if not student or student.role != 'student':
            return jsonify({
                'success': False,
                'message': '学生不存在',
                'code': 'STUDENT_NOT_FOUND'
            }), 400
        
        # 验证截止时间
        due_date = validate_datetime(data['due_date'])
        if not due_date:
            return jsonify({
                'success': False,
                'message': '截止时间格式不正确',
                'code': 'INVALID_DUE_DATE'
            }), 400
        
        # 验证截止时间不能是过去时间
        if due_date <= datetime.now():
            return jsonify({
                'success': False,
                'message': '截止时间不能是过去时间',
                'code': 'PAST_DUE_DATE'
            }), 400
        
        # 验证题目列表
        questions = data['questions']
        if not isinstance(questions, list) or len(questions) == 0:
            return jsonify({
                'success': False,
                'message': '题目列表不能为空',
                'code': 'EMPTY_QUESTIONS'
            }), 400
        
        # 验证题目是否存在且属于该教师
        total_points = 0
        for question_id in questions:
            question = Question.find_by_id(question_id)
            if not question or question.teacher_id != user_id:
                return jsonify({
                    'success': False,
                    'message': f'题目 {question_id} 不存在或无权使用',
                    'code': 'INVALID_QUESTION'
                }), 400
            total_points += question.points
        
        # 创建作业
        homework = Homework(
            teacher_id=user_id,
            student_id=data['student_id'],
            title=data['title'],
            description=data.get('description', ''),
            questions=json.dumps(questions),
            total_points=total_points,
            due_date=due_date.strftime('%Y-%m-%d %H:%M:%S'),
            time_limit=data.get('time_limit'),
            allow_late_submission=data.get('allow_late_submission', False),
            status='published'
        )
        homework.save()
        
        return jsonify({
            'success': True,
            'message': '作业创建成功',
            'data': {
                'homework': homework.to_dict()
            }
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'创建作业失败: {str(e)}',
            'code': 'CREATE_HOMEWORK_ERROR'
        }), 500

@homework_bp.route('/<int:homework_id>', methods=['PUT'])
@jwt_required()
def update_homework(homework_id):
    """更新作业"""
    try:
        user_id = get_jwt_identity()
        user = User.find_by_id(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        # 只有教师可以更新作业
        if user.role != 'teacher':
            return jsonify({
                'success': False,
                'message': '只有教师可以更新作业',
                'code': 'PERMISSION_DENIED'
            }), 403
        
        homework = Homework.find_by_id(homework_id)
        if not homework:
            return jsonify({
                'success': False,
                'message': '作业不存在',
                'code': 'HOMEWORK_NOT_FOUND'
            }), 404
        
        # 检查权限
        if homework.teacher_id != user_id:
            return jsonify({
                'success': False,
                'message': '无权修改此作业',
                'code': 'ACCESS_DENIED'
            }), 403
        
        # 已完成或已批改的作业不能修改
        if homework.status in ['completed', 'graded']:
            return jsonify({
                'success': False,
                'message': '已完成或已批改的作业不能修改',
                'code': 'HOMEWORK_IMMUTABLE'
            }), 400
        
        data = request.get_json()
        
        # 更新允许的字段
        if 'title' in data and data['title']:
            homework.title = data['title']
        
        if 'description' in data:
            homework.description = data['description']
        
        if 'due_date' in data:
            due_date = validate_datetime(data['due_date'])
            if not due_date:
                return jsonify({
                    'success': False,
                    'message': '截止时间格式不正确',
                    'code': 'INVALID_DUE_DATE'
                }), 400
            
            if due_date <= datetime.now():
                return jsonify({
                    'success': False,
                    'message': '截止时间不能是过去时间',
                    'code': 'PAST_DUE_DATE'
                }), 400
            
            homework.due_date = due_date.strftime('%Y-%m-%d %H:%M:%S')
        
        if 'time_limit' in data:
            homework.time_limit = data['time_limit']
        
        if 'allow_late_submission' in data:
            homework.allow_late_submission = data['allow_late_submission']
        
        if 'questions' in data:
            questions = data['questions']
            if not isinstance(questions, list) or len(questions) == 0:
                return jsonify({
                    'success': False,
                    'message': '题目列表不能为空',
                    'code': 'EMPTY_QUESTIONS'
                }), 400
            
            # 验证题目是否存在且属于该教师
            total_points = 0
            for question_id in questions:
                question = Question.find_by_id(question_id)
                if not question or question.teacher_id != user_id:
                    return jsonify({
                        'success': False,
                        'message': f'题目 {question_id} 不存在或无权使用',
                        'code': 'INVALID_QUESTION'
                    }), 400
                total_points += question.points
            
            homework.questions = json.dumps(questions)
            homework.total_points = total_points
        
        # 保存更新
        homework.save()
        
        return jsonify({
            'success': True,
            'message': '作业更新成功',
            'data': {
                'homework': homework.to_dict()
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'更新作业失败: {str(e)}',
            'code': 'UPDATE_HOMEWORK_ERROR'
        }), 500

@homework_bp.route('/<int:homework_id>/submit', methods=['POST'])
@jwt_required()
def submit_homework(homework_id):
    """提交作业"""
    try:
        user_id = get_jwt_identity()
        user = User.find_by_id(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        # 只有学生可以提交作业
        if user.role != 'student':
            return jsonify({
                'success': False,
                'message': '只有学生可以提交作业',
                'code': 'PERMISSION_DENIED'
            }), 403
        
        homework = Homework.find_by_id(homework_id)
        if not homework:
            return jsonify({
                'success': False,
                'message': '作业不存在',
                'code': 'HOMEWORK_NOT_FOUND'
            }), 404
        
        # 检查权限
        if homework.student_id != user_id:
            return jsonify({
                'success': False,
                'message': '无权提交此作业',
                'code': 'ACCESS_DENIED'
            }), 403
        
        # 检查作业状态
        if homework.status != 'published':
            return jsonify({
                'success': False,
                'message': '作业状态不允许提交',
                'code': 'INVALID_HOMEWORK_STATUS'
            }), 400
        
        # 检查是否已过期
        due_date = datetime.strptime(homework.due_date, '%Y-%m-%d %H:%M:%S')
        now = datetime.now()
        if now > due_date and not homework.allow_late_submission:
            return jsonify({
                'success': False,
                'message': '作业已过期，不允许提交',
                'code': 'HOMEWORK_EXPIRED'
            }), 400
        
        data = request.get_json()
        
        # 验证答案
        if not data.get('answers'):
            return jsonify({
                'success': False,
                'message': '答案不能为空',
                'code': 'MISSING_ANSWERS'
            }), 400
        
        answers = data['answers']
        if not isinstance(answers, dict):
            return jsonify({
                'success': False,
                'message': '答案格式不正确',
                'code': 'INVALID_ANSWERS_FORMAT'
            }), 400
        
        # 保存答案
        homework_answer = HomeworkAnswer(
            homework_id=homework_id,
            answers=json.dumps(answers)
        )
        homework_answer.save()
        
        # 更新作业状态
        homework.submit()
        
        return jsonify({
            'success': True,
            'message': '作业提交成功',
            'data': {
                'homework': homework.to_dict(),
                'submitted_at': homework.submitted_at
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'提交作业失败: {str(e)}',
            'code': 'SUBMIT_HOMEWORK_ERROR'
        }), 500

@homework_bp.route('/<int:homework_id>/grade', methods=['POST'])
@jwt_required()
def grade_homework(homework_id):
    """批改作业"""
    try:
        user_id = get_jwt_identity()
        user = User.find_by_id(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        # 只有教师可以批改作业
        if user.role != 'teacher':
            return jsonify({
                'success': False,
                'message': '只有教师可以批改作业',
                'code': 'PERMISSION_DENIED'
            }), 403
        
        homework = Homework.find_by_id(homework_id)
        if not homework:
            return jsonify({
                'success': False,
                'message': '作业不存在',
                'code': 'HOMEWORK_NOT_FOUND'
            }), 404
        
        # 检查权限
        if homework.teacher_id != user_id:
            return jsonify({
                'success': False,
                'message': '无权批改此作业',
                'code': 'ACCESS_DENIED'
            }), 403
        
        # 检查作业状态
        if homework.status != 'completed':
            return jsonify({
                'success': False,
                'message': '只能批改已提交的作业',
                'code': 'INVALID_HOMEWORK_STATUS'
            }), 400
        
        data = request.get_json()
        
        # 验证分数
        if 'score' not in data:
            return jsonify({
                'success': False,
                'message': '分数不能为空',
                'code': 'MISSING_SCORE'
            }), 400
        
        try:
            score = float(data['score'])
            if score < 0 or score > homework.total_points:
                return jsonify({
                    'success': False,
                    'message': f'分数必须在0-{homework.total_points}之间',
                    'code': 'INVALID_SCORE'
                }), 400
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'message': '分数格式不正确',
                'code': 'INVALID_SCORE_FORMAT'
            }), 400
        
        # 批改作业
        homework.grade(score, data.get('feedback', ''))
        
        return jsonify({
            'success': True,
            'message': '作业批改成功',
            'data': {
                'homework': homework.to_dict()
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'批改作业失败: {str(e)}',
            'code': 'GRADE_HOMEWORK_ERROR'
        }), 500

@homework_bp.route('/<int:homework_id>', methods=['DELETE'])
@jwt_required()
def delete_homework(homework_id):
    """删除作业"""
    try:
        user_id = get_jwt_identity()
        user = User.find_by_id(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        # 只有教师可以删除作业
        if user.role != 'teacher':
            return jsonify({
                'success': False,
                'message': '只有教师可以删除作业',
                'code': 'PERMISSION_DENIED'
            }), 403
        
        homework = Homework.find_by_id(homework_id)
        if not homework:
            return jsonify({
                'success': False,
                'message': '作业不存在',
                'code': 'HOMEWORK_NOT_FOUND'
            }), 404
        
        # 检查权限
        if homework.teacher_id != user_id:
            return jsonify({
                'success': False,
                'message': '无权删除此作业',
                'code': 'ACCESS_DENIED'
            }), 403
        
        # 已提交的作业不能删除
        if homework.status in ['completed', 'graded']:
            return jsonify({
                'success': False,
                'message': '已提交的作业不能删除',
                'code': 'HOMEWORK_SUBMITTED'
            }), 400
        
        # 删除作业
        homework.delete()
        
        return jsonify({
            'success': True,
            'message': '作业删除成功'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'删除作业失败: {str(e)}',
            'code': 'DELETE_HOMEWORK_ERROR'
        }), 500

@homework_bp.route('/overdue', methods=['GET'])
@jwt_required()
def get_overdue_homework():
    """获取过期作业"""
    try:
        user_id = get_jwt_identity()
        user = User.find_by_id(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        # 只有教师可以查看过期作业
        if user.role != 'teacher':
            return jsonify({
                'success': False,
                'message': '只有教师可以查看过期作业',
                'code': 'PERMISSION_DENIED'
            }), 403
        
        overdue_homework = Homework.get_overdue_homework(user_id)
        
        # 获取详细信息
        homework_details = []
        for hw in overdue_homework:
            hw_detail = Homework.get_homework_with_details(hw.id)
            homework_details.append(hw_detail)
        
        return jsonify({
            'success': True,
            'data': {
                'homework': homework_details,
                'count': len(homework_details)
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取过期作业失败: {str(e)}',
            'code': 'GET_OVERDUE_HOMEWORK_ERROR'
        }), 500

@homework_bp.route('/<int:homework_id>/submissions', methods=['GET'])
@jwt_required()
def get_homework_submissions(homework_id):
    """获取作业提交列表"""
    try:
        user_id = get_jwt_identity()
        user = User.find_by_id(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        # 只有教师可以查看提交列表
        if user.role != 'teacher':
            return jsonify({
                'success': False,
                'message': '只有教师可以查看作业提交',
                'code': 'PERMISSION_DENIED'
            }), 403
        
        homework = Homework.find_by_id(homework_id)
        if not homework:
            return jsonify({
                'success': False,
                'message': '作业不存在',
                'code': 'HOMEWORK_NOT_FOUND'
            }), 404
        
        # 检查权限
        if homework.teacher_id != user_id:
            return jsonify({
                'success': False,
                'message': '无权查看此作业的提交',
                'code': 'ACCESS_DENIED'
            }), 403
        
        # 获取提交信息（这里简化为单个提交，实际可能需要支持多个学生）
        submissions = []
        if homework.status in ['completed', 'graded']:
            # 获取学生信息
            student = User.find_by_id(homework.student_id)
            submission = {
                'id': homework.id,  # 使用作业ID作为提交ID
                'student_id': homework.student_id,
                'student_name': student.username if student else '未知学生',
                'submitted_at': homework.submitted_at,
                'status': homework.status,
                'score': homework.score,
                'feedback': homework.feedback
            }
            submissions.append(submission)
        
        return jsonify({
            'success': True,
            'data': submissions
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取作业提交失败: {str(e)}',
            'code': 'GET_HOMEWORK_SUBMISSIONS_ERROR'
        }), 500

@homework_bp.route('/statistics', methods=['GET'])
@jwt_required()
def get_homework_statistics():
    """获取作业统计信息"""
    try:
        user_id = get_jwt_identity()
        user = User.find_by_id(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        # 只有教师可以查看统计信息
        if user.role != 'teacher':
            return jsonify({
                'success': False,
                'message': '只有教师可以查看作业统计',
                'code': 'PERMISSION_DENIED'
            }), 403
        
        statistics = Homework.get_statistics(user_id)
        
        return jsonify({
            'success': True,
            'data': {
                'statistics': statistics
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取作业统计失败: {str(e)}',
            'code': 'GET_HOMEWORK_STATISTICS_ERROR'
        }), 500