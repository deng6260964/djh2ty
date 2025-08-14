from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import json

from models.user import User
from models.exam import Exam, ExamAnswer
from models.question import Question
from models.database import db

exams_bp = Blueprint('exams', __name__, url_prefix='/api/exams')

def validate_datetime(date_string):
    """验证日期时间格式"""
    try:
        return datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        return None

def validate_exam_status(status):
    """验证考试状态"""
    valid_statuses = ['draft', 'scheduled', 'in_progress', 'completed', 'graded', 'cancelled']
    return status in valid_statuses

@exams_bp.route('', methods=['GET'])
@jwt_required()
def get_exams():
    """获取考试列表"""
    try:
        user_id = int(get_jwt_identity())
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
        if status and not validate_exam_status(status):
            return jsonify({
                'success': False,
                'message': '考试状态不正确',
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
        
        # 根据用户角色获取考试
        if user.role == 'teacher':
            exams = Exam.get_by_teacher(user_id, status, start_dt, end_dt)
        else:  # student
            exams = Exam.get_by_student(user_id, status, start_dt, end_dt)
        
        # 分页处理
        total = len(exams)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_exams = exams[start_idx:end_idx]
        
        # 获取详细信息
        exam_details = []
        for exam in paginated_exams:
            exam_detail = Exam.get_exam_with_details(exam.id)
            exam_details.append(exam_detail)
        
        return jsonify({
            'success': True,
            'data': {
                'exams': exam_details,
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
            'message': f'获取考试列表失败: {str(e)}',
            'code': 'GET_EXAMS_ERROR'
        }), 500

@exams_bp.route('/<int:exam_id>', methods=['GET'])
@jwt_required()
def get_exam(exam_id):
    """获取考试详情"""
    try:
        user_id = int(get_jwt_identity())
        user = User.find_by_id(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        exam = Exam.find_by_id(exam_id)
        if not exam:
            return jsonify({
                'success': False,
                'message': '考试不存在',
                'code': 'EXAM_NOT_FOUND'
            }), 404
        
        # 检查权限
        if user.role == 'teacher':
            if exam.teacher_id != user_id:
                return jsonify({
                    'success': False,
                    'message': '无权访问此考试',
                    'code': 'ACCESS_DENIED'
                }), 403
        else:  # student
            if exam.student_id != user_id:
                return jsonify({
                    'success': False,
                    'message': '无权访问此考试',
                    'code': 'ACCESS_DENIED'
                }), 403
        
        # 获取考试详情
        exam_detail = Exam.get_exam_with_details(exam_id)
        
        # 获取题目列表
        questions = Exam.get_exam_questions(exam_id)
        
        # 获取答案（如果是学生且已提交，或者是教师）
        answers = None
        if user.role == 'teacher' or exam.status in ['completed', 'graded']:
            answers = ExamAnswer.get_by_exam_id(exam_id)
        
        return jsonify({
            'success': True,
            'data': {
                'exam': exam_detail,
                'questions': [q.to_dict() for q in questions],
                'answers': [a.to_dict() for a in answers] if answers else None
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取考试详情失败: {str(e)}',
            'code': 'GET_EXAM_ERROR'
        }), 500

@exams_bp.route('', methods=['POST'])
@jwt_required()
def create_exam():
    """创建考试"""
    try:
        user_id = int(get_jwt_identity())
        user = User.find_by_id(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        # 只有教师可以创建考试
        if user.role != 'teacher':
            return jsonify({
                'success': False,
                'message': '只有教师可以创建考试',
                'code': 'PERMISSION_DENIED'
            }), 403
        
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['title', 'student_id', 'start_time', 'end_time', 'questions']
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
        
        # 验证时间
        start_time = validate_datetime(data['start_time'])
        if not start_time:
            return jsonify({
                'success': False,
                'message': '开始时间格式不正确',
                'code': 'INVALID_START_TIME'
            }), 400
        
        end_time = validate_datetime(data['end_time'])
        if not end_time:
            return jsonify({
                'success': False,
                'message': '结束时间格式不正确',
                'code': 'INVALID_END_TIME'
            }), 400
        
        # 验证时间逻辑
        if start_time >= end_time:
            return jsonify({
                'success': False,
                'message': '开始时间必须早于结束时间',
                'code': 'INVALID_TIME_RANGE'
            }), 400
        
        # 验证开始时间不能是过去时间
        if start_time <= datetime.now():
            return jsonify({
                'success': False,
                'message': '开始时间不能是过去时间',
                'code': 'PAST_START_TIME'
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
        
        # 计算考试时长
        duration = int((end_time - start_time).total_seconds() / 60)  # 分钟
        
        # 创建考试
        exam = Exam(
            teacher_id=user_id,
            student_id=data['student_id'],
            title=data['title'],
            description=data.get('description', ''),
            questions=json.dumps(questions),
            total_points=total_points,
            start_time=start_time.strftime('%Y-%m-%d %H:%M:%S'),
            end_time=end_time.strftime('%Y-%m-%d %H:%M:%S'),
            duration=duration,
            allow_review=data.get('allow_review', True),
            shuffle_questions=data.get('shuffle_questions', False),
            status='scheduled'
        )
        exam.save()
        
        return jsonify({
            'success': True,
            'message': '考试创建成功',
            'data': {
                'exam': exam.to_dict()
            }
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'创建考试失败: {str(e)}',
            'code': 'CREATE_EXAM_ERROR'
        }), 500

@exams_bp.route('/<int:exam_id>', methods=['PUT'])
@jwt_required()
def update_exam(exam_id):
    """更新考试"""
    try:
        user_id = int(get_jwt_identity())
        user = User.find_by_id(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        # 只有教师可以更新考试
        if user.role != 'teacher':
            return jsonify({
                'success': False,
                'message': '只有教师可以更新考试',
                'code': 'PERMISSION_DENIED'
            }), 403
        
        exam = Exam.find_by_id(exam_id)
        if not exam:
            return jsonify({
                'success': False,
                'message': '考试不存在',
                'code': 'EXAM_NOT_FOUND'
            }), 404
        
        # 检查权限
        if exam.teacher_id != user_id:
            return jsonify({
                'success': False,
                'message': '无权修改此考试',
                'code': 'ACCESS_DENIED'
            }), 403
        
        # 已开始、完成或取消的考试不能修改
        if exam.status in ['in_progress', 'completed', 'graded', 'cancelled']:
            return jsonify({
                'success': False,
                'message': '已开始、完成或取消的考试不能修改',
                'code': 'EXAM_IMMUTABLE'
            }), 400
        
        data = request.get_json()
        
        # 更新允许的字段
        if 'title' in data and data['title']:
            exam.title = data['title']
        
        if 'description' in data:
            exam.description = data['description']
        
        if 'start_time' in data:
            start_time = validate_datetime(data['start_time'])
            if not start_time:
                return jsonify({
                    'success': False,
                    'message': '开始时间格式不正确',
                    'code': 'INVALID_START_TIME'
                }), 400
            
            if start_time <= datetime.now():
                return jsonify({
                    'success': False,
                    'message': '开始时间不能是过去时间',
                    'code': 'PAST_START_TIME'
                }), 400
            
            exam.start_time = start_time.strftime('%Y-%m-%d %H:%M:%S')
        
        if 'end_time' in data:
            end_time = validate_datetime(data['end_time'])
            if not end_time:
                return jsonify({
                    'success': False,
                    'message': '结束时间格式不正确',
                    'code': 'INVALID_END_TIME'
                }), 400
            
            exam.end_time = end_time.strftime('%Y-%m-%d %H:%M:%S')
        
        # 验证时间逻辑
        start_time = datetime.strptime(exam.start_time, '%Y-%m-%d %H:%M:%S')
        end_time = datetime.strptime(exam.end_time, '%Y-%m-%d %H:%M:%S')
        if start_time >= end_time:
            return jsonify({
                'success': False,
                'message': '开始时间必须早于结束时间',
                'code': 'INVALID_TIME_RANGE'
            }), 400
        
        # 更新考试时长
        exam.duration = int((end_time - start_time).total_seconds() / 60)
        
        if 'allow_review' in data:
            exam.allow_review = data['allow_review']
        
        if 'shuffle_questions' in data:
            exam.shuffle_questions = data['shuffle_questions']
        
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
            
            exam.questions = json.dumps(questions)
            exam.total_points = total_points
        
        # 保存更新
        exam.save()
        
        return jsonify({
            'success': True,
            'message': '考试更新成功',
            'data': {
                'exam': exam.to_dict()
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'更新考试失败: {str(e)}',
            'code': 'UPDATE_EXAM_ERROR'
        }), 500

@exams_bp.route('/<int:exam_id>/start', methods=['POST'])
@jwt_required()
def start_exam(exam_id):
    """开始考试"""
    try:
        user_id = int(get_jwt_identity())
        user = User.find_by_id(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        # 只有学生可以开始考试
        if user.role != 'student':
            return jsonify({
                'success': False,
                'message': '只有学生可以开始考试',
                'code': 'PERMISSION_DENIED'
            }), 403
        
        exam = Exam.find_by_id(exam_id)
        if not exam:
            return jsonify({
                'success': False,
                'message': '考试不存在',
                'code': 'EXAM_NOT_FOUND'
            }), 404
        
        # 检查权限
        if exam.student_id != user_id:
            return jsonify({
                'success': False,
                'message': '无权参加此考试',
                'code': 'ACCESS_DENIED'
            }), 403
        
        # 检查考试状态
        if exam.status != 'scheduled':
            return jsonify({
                'success': False,
                'message': '考试状态不允许开始',
                'code': 'INVALID_EXAM_STATUS'
            }), 400
        
        # 检查考试时间
        start_time = datetime.strptime(exam.start_time, '%Y-%m-%d %H:%M:%S')
        end_time = datetime.strptime(exam.end_time, '%Y-%m-%d %H:%M:%S')
        now = datetime.now()
        
        if now < start_time:
            return jsonify({
                'success': False,
                'message': '考试尚未开始',
                'code': 'EXAM_NOT_STARTED'
            }), 400
        
        if now > end_time:
            return jsonify({
                'success': False,
                'message': '考试已结束',
                'code': 'EXAM_ENDED'
            }), 400
        
        # 开始考试
        exam.start()
        
        return jsonify({
            'success': True,
            'message': '考试开始成功',
            'data': {
                'exam': exam.to_dict(),
                'started_at': exam.started_at
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'开始考试失败: {str(e)}',
            'code': 'START_EXAM_ERROR'
        }), 500

@exams_bp.route('/<int:exam_id>/submit', methods=['POST'])
@jwt_required()
def submit_exam(exam_id):
    """提交考试"""
    try:
        user_id = int(get_jwt_identity())
        user = User.find_by_id(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        # 只有学生可以提交考试
        if user.role != 'student':
            return jsonify({
                'success': False,
                'message': '只有学生可以提交考试',
                'code': 'PERMISSION_DENIED'
            }), 403
        
        exam = Exam.find_by_id(exam_id)
        if not exam:
            return jsonify({
                'success': False,
                'message': '考试不存在',
                'code': 'EXAM_NOT_FOUND'
            }), 404
        
        # 检查权限
        if exam.student_id != user_id:
            return jsonify({
                'success': False,
                'message': '无权提交此考试',
                'code': 'ACCESS_DENIED'
            }), 403
        
        # 检查考试状态
        if exam.status != 'in_progress':
            return jsonify({
                'success': False,
                'message': '考试状态不允许提交',
                'code': 'INVALID_EXAM_STATUS'
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
        exam_answer = ExamAnswer(
            exam_id=exam_id,
            answers=json.dumps(answers)
        )
        exam_answer.save()
        
        # 提交考试
        exam.submit()
        
        return jsonify({
            'success': True,
            'message': '考试提交成功',
            'data': {
                'exam': exam.to_dict(),
                'submitted_at': exam.submitted_at
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'提交考试失败: {str(e)}',
            'code': 'SUBMIT_EXAM_ERROR'
        }), 500

@exams_bp.route('/<int:exam_id>/grade', methods=['POST'])
@jwt_required()
def grade_exam(exam_id):
    """批改考试"""
    try:
        user_id = int(get_jwt_identity())
        user = User.find_by_id(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        # 只有教师可以批改考试
        if user.role != 'teacher':
            return jsonify({
                'success': False,
                'message': '只有教师可以批改考试',
                'code': 'PERMISSION_DENIED'
            }), 403
        
        exam = Exam.find_by_id(exam_id)
        if not exam:
            return jsonify({
                'success': False,
                'message': '考试不存在',
                'code': 'EXAM_NOT_FOUND'
            }), 404
        
        # 检查权限
        if exam.teacher_id != user_id:
            return jsonify({
                'success': False,
                'message': '无权批改此考试',
                'code': 'ACCESS_DENIED'
            }), 403
        
        # 检查考试状态
        if exam.status != 'completed':
            return jsonify({
                'success': False,
                'message': '只能批改已提交的考试',
                'code': 'INVALID_EXAM_STATUS'
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
            if score < 0 or score > exam.total_points:
                return jsonify({
                    'success': False,
                    'message': f'分数必须在0-{exam.total_points}之间',
                    'code': 'INVALID_SCORE'
                }), 400
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'message': '分数格式不正确',
                'code': 'INVALID_SCORE_FORMAT'
            }), 400
        
        # 批改考试
        exam.grade(score, data.get('feedback', ''))
        
        return jsonify({
            'success': True,
            'message': '考试批改成功',
            'data': {
                'exam': exam.to_dict()
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'批改考试失败: {str(e)}',
            'code': 'GRADE_EXAM_ERROR'
        }), 500

@exams_bp.route('/<int:exam_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_exam(exam_id):
    """取消考试"""
    try:
        user_id = int(get_jwt_identity())
        user = User.find_by_id(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        # 只有教师可以取消考试
        if user.role != 'teacher':
            return jsonify({
                'success': False,
                'message': '只有教师可以取消考试',
                'code': 'PERMISSION_DENIED'
            }), 403
        
        exam = Exam.find_by_id(exam_id)
        if not exam:
            return jsonify({
                'success': False,
                'message': '考试不存在',
                'code': 'EXAM_NOT_FOUND'
            }), 404
        
        # 检查权限
        if exam.teacher_id != user_id:
            return jsonify({
                'success': False,
                'message': '无权取消此考试',
                'code': 'ACCESS_DENIED'
            }), 403
        
        # 已完成或已批改的考试不能取消
        if exam.status in ['completed', 'graded']:
            return jsonify({
                'success': False,
                'message': '已完成或已批改的考试不能取消',
                'code': 'EXAM_IMMUTABLE'
            }), 400
        
        data = request.get_json()
        reason = data.get('reason', '')
        
        # 取消考试
        exam.cancel(reason)
        
        return jsonify({
            'success': True,
            'message': '考试取消成功',
            'data': {
                'exam': exam.to_dict()
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'取消考试失败: {str(e)}',
            'code': 'CANCEL_EXAM_ERROR'
        }), 500

@exams_bp.route('/<int:exam_id>', methods=['DELETE'])
@jwt_required()
def delete_exam(exam_id):
    """删除考试"""
    try:
        user_id = int(get_jwt_identity())
        user = User.find_by_id(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        # 只有教师可以删除考试
        if user.role != 'teacher':
            return jsonify({
                'success': False,
                'message': '只有教师可以删除考试',
                'code': 'PERMISSION_DENIED'
            }), 403
        
        exam = Exam.find_by_id(exam_id)
        if not exam:
            return jsonify({
                'success': False,
                'message': '考试不存在',
                'code': 'EXAM_NOT_FOUND'
            }), 404
        
        # 检查权限
        if exam.teacher_id != user_id:
            return jsonify({
                'success': False,
                'message': '无权删除此考试',
                'code': 'ACCESS_DENIED'
            }), 403
        
        # 已开始的考试不能删除
        if exam.status in ['in_progress', 'completed', 'graded']:
            return jsonify({
                'success': False,
                'message': '已开始的考试不能删除',
                'code': 'EXAM_STARTED'
            }), 400
        
        # 删除考试
        exam.delete()
        
        return jsonify({
            'success': True,
            'message': '考试删除成功'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'删除考试失败: {str(e)}',
            'code': 'DELETE_EXAM_ERROR'
        }), 500

@exams_bp.route('/upcoming', methods=['GET'])
@jwt_required()
def get_upcoming_exams():
    """获取即将到来的考试"""
    try:
        user_id = int(get_jwt_identity())
        user = User.find_by_id(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        # 根据用户角色获取即将到来的考试
        if user.role == 'teacher':
            upcoming_exams = Exam.get_upcoming_exams_by_teacher(user_id)
        else:  # student
            upcoming_exams = Exam.get_upcoming_exams_by_student(user_id)
        
        # 获取详细信息
        exam_details = []
        for exam in upcoming_exams:
            exam_detail = Exam.get_exam_with_details(exam.id)
            exam_details.append(exam_detail)
        
        return jsonify({
            'success': True,
            'data': {
                'exams': exam_details,
                'count': len(exam_details)
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取即将到来的考试失败: {str(e)}',
            'code': 'GET_UPCOMING_EXAMS_ERROR'
        }), 500

@exams_bp.route('/in-progress', methods=['GET'])
@jwt_required()
def get_in_progress_exams():
    """获取正在进行的考试"""
    try:
        user_id = int(get_jwt_identity())
        user = User.find_by_id(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        # 根据用户角色获取正在进行的考试
        if user.role == 'teacher':
            in_progress_exams = Exam.get_in_progress_exams_by_teacher(user_id)
        else:  # student
            in_progress_exams = Exam.get_in_progress_exams_by_student(user_id)
        
        # 获取详细信息
        exam_details = []
        for exam in in_progress_exams:
            exam_detail = Exam.get_exam_with_details(exam.id)
            exam_details.append(exam_detail)
        
        return jsonify({
            'success': True,
            'data': {
                'exams': exam_details,
                'count': len(exam_details)
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取正在进行的考试失败: {str(e)}',
            'code': 'GET_IN_PROGRESS_EXAMS_ERROR'
        }), 500

@exams_bp.route('/statistics', methods=['GET'])
@jwt_required()
def get_exam_statistics():
    """获取考试统计信息"""
    try:
        user_id = int(get_jwt_identity())
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
                'message': '只有教师可以查看考试统计',
                'code': 'PERMISSION_DENIED'
            }), 403
        
        statistics = Exam.get_statistics(user_id)
        
        return jsonify({
            'success': True,
            'data': {
                'statistics': statistics
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取考试统计失败: {str(e)}',
            'code': 'GET_EXAM_STATISTICS_ERROR'
        }), 500

@exams_bp.route('/<int:exam_id>/submissions', methods=['GET'])
@jwt_required()
def get_exam_submissions(exam_id):
    """获取考试提交记录"""
    try:
        user_id = int(get_jwt_identity())
        user = User.find_by_id(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        # 只有教师可以查看考试提交记录
        if user.role != 'teacher':
            return jsonify({
                'success': False,
                'message': '只有教师可以查看考试提交记录',
                'code': 'PERMISSION_DENIED'
            }), 403
        
        exam = Exam.find_by_id(exam_id)
        if not exam:
            return jsonify({
                'success': False,
                'message': '考试不存在',
                'code': 'EXAM_NOT_FOUND'
            }), 404
        
        # 检查权限
        if exam.teacher_id != user_id:
            return jsonify({
                'success': False,
                'message': '无权查看此考试的提交记录',
                'code': 'ACCESS_DENIED'
            }), 403
        
        # 获取考试提交记录
        submissions = []
        
        # 获取学生信息
        student = User.find_by_id(exam.student_id)
        if student:
            submission = {
                'id': exam.id,
                'exam_id': exam.id,
                'student_id': exam.student_id,
                'student_name': student.username,
                'submitted_at': exam.submitted_at if hasattr(exam, 'submitted_at') and exam.submitted_at else None,
                'status': exam.status,
                'score': exam.score if hasattr(exam, 'score') else None,
                'feedback': exam.feedback if hasattr(exam, 'feedback') else None,
                'graded': exam.status == 'graded'
            }
            submissions.append(submission)
        
        return jsonify({
            'success': True,
            'data': {
                'submissions': submissions,
                'count': len(submissions)
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取考试提交记录失败: {str(e)}',
            'code': 'GET_EXAM_SUBMISSIONS_ERROR'
        }), 500