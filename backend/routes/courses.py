from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import json

from models.course import Course
from models.user import User
from models.database import db

courses_bp = Blueprint('courses', __name__, url_prefix='/api/courses')

def validate_datetime(date_string):
    """验证日期时间格式"""
    try:
        datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        return True
    except ValueError:
        return False

@courses_bp.route('', methods=['GET'])
@jwt_required()
def get_courses():
    """获取课程列表"""
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
        
        # 验证日期格式
        if start_date and not validate_datetime(start_date):
            return jsonify({
                'success': False,
                'message': '开始日期格式不正确',
                'code': 'INVALID_START_DATE'
            }), 400
        
        if end_date and not validate_datetime(end_date):
            return jsonify({
                'success': False,
                'message': '结束日期格式不正确',
                'code': 'INVALID_END_DATE'
            }), 400
        
        # 根据用户角色获取课程
        if user.role == 'teacher':
            courses = Course.get_by_teacher(user_id, status, start_date, end_date)
        else:
            courses = Course.get_by_student(user_id, status, start_date, end_date)
        
        # 分页处理
        total = len(courses)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_courses = courses[start_idx:end_idx]
        
        # 获取详细信息
        course_list = []
        for course in paginated_courses:
            course_detail = Course.get_course_with_details(course.id)
            if course_detail:
                course_list.append(course_detail.to_dict())
        
        return jsonify({
            'success': True,
            'data': {
                'courses': course_list,
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
            'message': f'获取课程列表失败: {str(e)}',
            'code': 'GET_COURSES_ERROR'
        }), 500

@courses_bp.route('/<int:course_id>', methods=['GET'])
@jwt_required()
def get_course(course_id):
    """获取课程详情"""
    try:
        user_id = get_jwt_identity()
        user = User.find_by_id(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        course = Course.get_course_with_details(course_id)
        if not course:
            return jsonify({
                'success': False,
                'message': '课程不存在',
                'code': 'COURSE_NOT_FOUND'
            }), 404
        
        # 检查权限
        if user.role == 'teacher' and course.teacher_id != user_id:
            return jsonify({
                'success': False,
                'message': '无权访问此课程',
                'code': 'ACCESS_DENIED'
            }), 403
        
        if user.role == 'student' and course.student_id != user_id:
            return jsonify({
                'success': False,
                'message': '无权访问此课程',
                'code': 'ACCESS_DENIED'
            }), 403
        
        return jsonify({
            'success': True,
            'data': {
                'course': course.to_dict()
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取课程详情失败: {str(e)}',
            'code': 'GET_COURSE_ERROR'
        }), 500

@courses_bp.route('', methods=['POST'])
@jwt_required()
def create_course():
    """创建课程"""
    try:
        user_id = get_jwt_identity()
        user = User.find_by_id(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        # 只有教师可以创建课程
        if user.role != 'teacher':
            return jsonify({
                'success': False,
                'message': '只有教师可以创建课程',
                'code': 'PERMISSION_DENIED'
            }), 403
        
        data = request.get_json()
        
        # 验证必填字段（适配前端课程管理）
        required_fields = ['name', 'grade']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'{field}不能为空',
                    'code': 'MISSING_FIELD'
                }), 400
        
        # 创建课程（适配课程管理模式）
        course = Course(
            teacher_id=user_id,
            student_id=None,  # 课程管理模式下不绑定特定学生
            title=data['name'],  # 使用name作为title
            description=data.get('description', ''),
            start_time=None,  # 课程管理模式下不设置具体时间
            end_time=None,
            location='',
            notes=f"年级: {data['grade']}, 科目: {data.get('subject', 'English')}",
            status='active',  # 课程管理模式下默认为active
            grade=data['grade'],
            subject=data.get('subject', 'English')
        )
        course.save()
        
        return jsonify({
            'success': True,
            'message': '课程创建成功',
            'data': course.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'创建课程失败: {str(e)}',
            'code': 'CREATE_COURSE_ERROR'
        }), 500

@courses_bp.route('/<int:course_id>', methods=['PUT'])
@jwt_required()
def update_course(course_id):
    """更新课程"""
    try:
        user_id = get_jwt_identity()
        user = User.find_by_id(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        course = Course.find_by_id(course_id)
        if not course:
            return jsonify({
                'success': False,
                'message': '课程不存在',
                'code': 'COURSE_NOT_FOUND'
            }), 404
        
        # 只有教师可以更新课程，且只能更新自己的课程
        if user.role != 'teacher' or course.teacher_id != user_id:
            return jsonify({
                'success': False,
                'message': '无权修改此课程',
                'code': 'PERMISSION_DENIED'
            }), 403
        
        # 已完成或已取消的课程不能修改
        if course.status in ['completed', 'cancelled']:
            return jsonify({
                'success': False,
                'message': '已完成或已取消的课程不能修改',
                'code': 'COURSE_IMMUTABLE'
            }), 400
        
        data = request.get_json()
        
        # 更新允许的字段
        if 'title' in data and data['title']:
            course.title = data['title']
        
        if 'description' in data:
            course.description = data['description']
        
        if 'location' in data:
            course.location = data['location']
        
        if 'notes' in data:
            course.notes = data['notes']
        
        # 更新时间（需要验证）
        if 'start_time' in data or 'end_time' in data:
            start_time = data.get('start_time', course.start_time)
            end_time = data.get('end_time', course.end_time)
            
            if not validate_datetime(start_time) or not validate_datetime(end_time):
                return jsonify({
                    'success': False,
                    'message': '时间格式不正确',
                    'code': 'INVALID_DATETIME'
                }), 400
            
            if start_time >= end_time:
                return jsonify({
                    'success': False,
                    'message': '开始时间必须早于结束时间',
                    'code': 'INVALID_TIME_RANGE'
                }), 400
            
            course.start_time = start_time
            course.end_time = end_time
        
        # 保存更新
        course.save()
        
        # 获取详细信息
        course_detail = Course.get_course_with_details(course.id)
        
        return jsonify({
            'success': True,
            'message': '课程更新成功',
            'data': {
                'course': course_detail.to_dict() if course_detail else course.to_dict()
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'更新课程失败: {str(e)}',
            'code': 'UPDATE_COURSE_ERROR'
        }), 500

@courses_bp.route('/<int:course_id>', methods=['DELETE'])
@jwt_required()
def delete_course(course_id):
    """删除课程"""
    try:
        user_id = get_jwt_identity()
        user = User.find_by_id(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        course = Course.find_by_id(course_id)
        if not course:
            return jsonify({
                'success': False,
                'message': '课程不存在',
                'code': 'COURSE_NOT_FOUND'
            }), 404
        
        # 只有教师可以删除课程，且只能删除自己的课程
        if user.role != 'teacher' or course.teacher_id != user_id:
            return jsonify({
                'success': False,
                'message': '无权删除此课程',
                'code': 'PERMISSION_DENIED'
            }), 403
        
        # 已开始的课程不能删除，只能取消
        if course.status == 'in_progress':
            return jsonify({
                'success': False,
                'message': '正在进行的课程不能删除，请先取消课程',
                'code': 'COURSE_IN_PROGRESS'
            }), 400
        
        # 删除课程
        course.delete()
        
        return jsonify({
            'success': True,
            'message': '课程删除成功'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'删除课程失败: {str(e)}',
            'code': 'DELETE_COURSE_ERROR'
        }), 500

@courses_bp.route('/<int:course_id>/start', methods=['POST'])
@jwt_required()
def start_course(course_id):
    """开始课程"""
    try:
        user_id = get_jwt_identity()
        user = User.find_by_id(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        course = Course.find_by_id(course_id)
        if not course:
            return jsonify({
                'success': False,
                'message': '课程不存在',
                'code': 'COURSE_NOT_FOUND'
            }), 404
        
        # 只有教师可以开始课程
        if user.role != 'teacher' or course.teacher_id != user_id:
            return jsonify({
                'success': False,
                'message': '无权开始此课程',
                'code': 'PERMISSION_DENIED'
            }), 403
        
        # 开始课程
        if course.start():
            course_detail = Course.get_course_with_details(course.id)
            return jsonify({
                'success': True,
                'message': '课程已开始',
                'data': {
                    'course': course_detail.to_dict() if course_detail else course.to_dict()
                }
            })
        else:
            return jsonify({
                'success': False,
                'message': '无法开始课程，请检查课程状态和时间',
                'code': 'CANNOT_START_COURSE'
            }), 400
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'开始课程失败: {str(e)}',
            'code': 'START_COURSE_ERROR'
        }), 500

@courses_bp.route('/<int:course_id>/complete', methods=['POST'])
@jwt_required()
def complete_course(course_id):
    """完成课程"""
    try:
        user_id = get_jwt_identity()
        user = User.find_by_id(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        course = Course.find_by_id(course_id)
        if not course:
            return jsonify({
                'success': False,
                'message': '课程不存在',
                'code': 'COURSE_NOT_FOUND'
            }), 404
        
        # 只有教师可以完成课程
        if user.role != 'teacher' or course.teacher_id != user_id:
            return jsonify({
                'success': False,
                'message': '无权完成此课程',
                'code': 'PERMISSION_DENIED'
            }), 403
        
        data = request.get_json() or {}
        summary = data.get('summary', '')
        
        # 完成课程
        if course.complete(summary):
            course_detail = Course.get_course_with_details(course.id)
            return jsonify({
                'success': True,
                'message': '课程已完成',
                'data': {
                    'course': course_detail.to_dict() if course_detail else course.to_dict()
                }
            })
        else:
            return jsonify({
                'success': False,
                'message': '无法完成课程，请检查课程状态',
                'code': 'CANNOT_COMPLETE_COURSE'
            }), 400
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'完成课程失败: {str(e)}',
            'code': 'COMPLETE_COURSE_ERROR'
        }), 500

@courses_bp.route('/<int:course_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_course(course_id):
    """取消课程"""
    try:
        user_id = get_jwt_identity()
        user = User.find_by_id(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        course = Course.find_by_id(course_id)
        if not course:
            return jsonify({
                'success': False,
                'message': '课程不存在',
                'code': 'COURSE_NOT_FOUND'
            }), 404
        
        # 只有教师可以取消课程
        if user.role != 'teacher' or course.teacher_id != user_id:
            return jsonify({
                'success': False,
                'message': '无权取消此课程',
                'code': 'PERMISSION_DENIED'
            }), 403
        
        data = request.get_json() or {}
        reason = data.get('reason', '')
        
        # 取消课程
        if course.cancel(reason):
            course_detail = Course.get_course_with_details(course.id)
            return jsonify({
                'success': True,
                'message': '课程已取消',
                'data': {
                    'course': course_detail.to_dict() if course_detail else course.to_dict()
                }
            })
        else:
            return jsonify({
                'success': False,
                'message': '无法取消课程，请检查课程状态',
                'code': 'CANNOT_CANCEL_COURSE'
            }), 400
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'取消课程失败: {str(e)}',
            'code': 'CANCEL_COURSE_ERROR'
        }), 500

@courses_bp.route('/upcoming', methods=['GET'])
@jwt_required()
def get_upcoming_courses():
    """获取即将到来的课程"""
    try:
        user_id = get_jwt_identity()
        user = User.find_by_id(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        limit = int(request.args.get('limit', 10))
        
        # 根据用户角色获取即将到来的课程
        if user.role == 'teacher':
            courses = Course.get_upcoming_courses_by_teacher(user_id, limit)
        else:
            courses = Course.get_upcoming_courses_by_student(user_id, limit)
        
        # 获取详细信息
        course_list = []
        for course in courses:
            course_detail = Course.get_course_with_details(course.id)
            if course_detail:
                course_list.append(course_detail.to_dict())
        
        return jsonify({
            'success': True,
            'data': {
                'courses': course_list
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取即将到来的课程失败: {str(e)}',
            'code': 'GET_UPCOMING_COURSES_ERROR'
        }), 500