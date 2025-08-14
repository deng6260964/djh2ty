from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import json

from models.course import Course
from models.course_student import CourseStudent
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
        user_id = int(get_jwt_identity())
        user = User.find_by_id(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        # 获取查询参数
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
            courses = Course.get_by_teacher(user_id, start_date, end_date)
        else:
            # 学生通过课程学生关联表获取课程
            enrollments = CourseStudent.get_by_student(user_id)
            course_ids = [e.course_id for e in enrollments]
            courses = []
            for course_id in course_ids:
                course = Course.find_by_id(course_id)
                if course:
                    courses.append(course)
        
        # 分页处理
        total = len(courses)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_courses = courses[start_idx:end_idx]
        
        # 转换为字典格式
        course_list = []
        for course in paginated_courses:
            course_dict = course.to_dict()
            # 添加报名人数信息
            course_dict['enrolled_count'] = CourseStudent.get_enrollment_count(course.id)
            course_list.append(course_dict)
        
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
        user_id = int(get_jwt_identity())
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
        
        # 检查权限
        if user.role == 'teacher' and course.teacher_id != user_id:
            return jsonify({
                'success': False,
                'message': '无权访问此课程',
                'code': 'ACCESS_DENIED'
            }), 403
        
        if user.role == 'student' and not CourseStudent.is_enrolled(course_id, user_id):
            return jsonify({
                'success': False,
                'message': '无权访问此课程',
                'code': 'ACCESS_DENIED'
            }), 403
        
        course_dict = course.to_dict()
        # 添加报名学生信息
        if user.role == 'teacher':
            enrollments = CourseStudent.get_by_course(course_id)
            course_dict['students'] = [e.to_dict() for e in enrollments]
        course_dict['enrolled_count'] = CourseStudent.get_enrollment_count(course_id)
        
        return jsonify({
            'success': True,
            'data': {
                'course': course_dict
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
        user_id = int(get_jwt_identity())
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
        
        # 验证必填字段
        required_fields = ['title', 'subject', 'level', 'start_time', 'end_time']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'{field}不能为空',
                    'code': 'MISSING_FIELD'
                }), 400
        
        # 验证时间格式
        if not validate_datetime(data['start_time']) or not validate_datetime(data['end_time']):
            return jsonify({
                'success': False,
                'message': '时间格式不正确',
                'code': 'INVALID_DATETIME'
            }), 400
        
        # 验证时间逻辑
        start_time = datetime.fromisoformat(data['start_time'].replace('Z', '+00:00'))
        end_time = datetime.fromisoformat(data['end_time'].replace('Z', '+00:00'))
        
        if start_time >= end_time:
            return jsonify({
                'success': False,
                'message': '开始时间必须早于结束时间',
                'code': 'INVALID_TIME_RANGE'
            }), 400
        
        # 创建课程
        course = Course(
            teacher_id=user_id,
            title=data['title'],
            subject=data['subject'],
            level=data['level'],
            start_time=data['start_time'],
            end_time=data['end_time'],
            location=data.get('location', ''),
            max_students=data.get('max_students', 30),
            description=data.get('description', ''),
            status='active'
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
        user_id = int(get_jwt_identity())
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
        
        data = request.get_json()
        
        # 更新允许的字段
        if 'title' in data and data['title']:
            course.title = data['title']
        
        if 'subject' in data and data['subject']:
            course.subject = data['subject']
        
        if 'level' in data and data['level']:
            course.level = data['level']
        
        if 'description' in data:
            course.description = data['description']
        
        if 'location' in data:
            course.location = data['location']
        
        if 'max_students' in data:
            course.max_students = data['max_students']
        
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
            
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            
            if start_dt >= end_dt:
                return jsonify({
                    'success': False,
                    'message': '开始时间必须早于结束时间',
                    'code': 'INVALID_TIME_RANGE'
                }), 400
            
            course.start_time = start_time
            course.end_time = end_time
        
        # 保存更新
        course.save()
        
        return jsonify({
            'success': True,
            'message': '课程更新成功',
            'data': {
                'course': course.to_dict()
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
        user_id = int(get_jwt_identity())
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
        
        # 删除课程（关联的学生记录会通过外键约束自动删除）
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

@courses_bp.route('/<int:course_id>/enroll', methods=['POST'])
@jwt_required()
def enroll_course(course_id):
    """报名课程"""
    try:
        user_id = int(get_jwt_identity())
        user = User.find_by_id(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        # 只有学生可以报名课程
        if user.role != 'student':
            return jsonify({
                'success': False,
                'message': '只有学生可以报名课程',
                'code': 'PERMISSION_DENIED'
            }), 403
        
        course = Course.find_by_id(course_id)
        if not course:
            return jsonify({
                'success': False,
                'message': '课程不存在',
                'code': 'COURSE_NOT_FOUND'
            }), 404
        
        # 检查是否已报名
        if CourseStudent.is_enrolled(course_id, user_id):
            return jsonify({
                'success': False,
                'message': '您已报名此课程',
                'code': 'ALREADY_ENROLLED'
            }), 400
        
        # 检查课程是否已满
        enrolled_count = CourseStudent.get_enrollment_count(course_id)
        if enrolled_count >= course.max_students:
            return jsonify({
                'success': False,
                'message': '课程已满，无法报名',
                'code': 'COURSE_FULL'
            }), 400
        
        # 创建报名记录
        enrollment = CourseStudent(
            course_id=course_id,
            student_id=user_id,
            enrollment_date=datetime.now().isoformat(),
            status='enrolled'
        )
        enrollment.save()
        
        return jsonify({
            'success': True,
            'message': '报名成功',
            'data': enrollment.to_dict()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'报名失败: {str(e)}',
            'code': 'ENROLL_ERROR'
        }), 500

@courses_bp.route('/<int:course_id>/drop', methods=['POST'])
@jwt_required()
def drop_course(course_id):
    """退课"""
    try:
        user_id = int(get_jwt_identity())
        user = User.find_by_id(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        # 只有学生可以退课
        if user.role != 'student':
            return jsonify({
                'success': False,
                'message': '只有学生可以退课',
                'code': 'PERMISSION_DENIED'
            }), 403
        
        # 检查是否已报名
        if not CourseStudent.is_enrolled(course_id, user_id):
            return jsonify({
                'success': False,
                'message': '您未报名此课程',
                'code': 'NOT_ENROLLED'
            }), 400
        
        # 查找报名记录并更新状态
        query = 'SELECT * FROM course_students WHERE course_id = ? AND student_id = ? AND status = "enrolled"'
        result = db.execute_query(query, (course_id, user_id))
        
        if result:
            enrollment = CourseStudent.from_dict(dict(result[0]))
            enrollment.status = 'dropped'
            enrollment.save()
            
            return jsonify({
                'success': True,
                'message': '退课成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '未找到报名记录',
                'code': 'ENROLLMENT_NOT_FOUND'
            }), 404
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'退课失败: {str(e)}',
            'code': 'DROP_ERROR'
        }), 500

@courses_bp.route('/<int:course_id>/enroll-students', methods=['POST'])
@jwt_required()
def enroll_students_to_course(course_id):
    """教师为学生批量报名课程"""
    try:
        user_id = int(get_jwt_identity())
        user = User.find_by_id(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        # 只有教师可以为学生报名
        if user.role != 'teacher':
            return jsonify({
                'success': False,
                'message': '只有教师可以为学生报名课程',
                'code': 'PERMISSION_DENIED'
            }), 403
        
        course = Course.find_by_id(course_id)
        if not course:
            return jsonify({
                'success': False,
                'message': '课程不存在',
                'code': 'COURSE_NOT_FOUND'
            }), 404
        
        # 检查教师是否有权限操作此课程
        if course.teacher_id != user_id:
            return jsonify({
                'success': False,
                'message': '无权为此课程报名学生',
                'code': 'PERMISSION_DENIED'
            }), 403
        
        data = request.get_json()
        student_ids = data.get('student_ids', [])
        
        if not student_ids:
            return jsonify({
                'success': False,
                'message': '请选择要报名的学生',
                'code': 'NO_STUDENTS_SELECTED'
            }), 400
        
        success_count = 0
        failed_students = []
        
        for student_id in student_ids:
            try:
                # 检查学生是否存在
                student = User.find_by_id(student_id)
                if not student or student.role != 'student':
                    failed_students.append({
                        'student_id': student_id,
                        'reason': '学生不存在或角色错误'
                    })
                    continue
                
                # 检查是否已报名
                if CourseStudent.is_enrolled(course_id, student_id):
                    failed_students.append({
                        'student_id': student_id,
                        'reason': '学生已报名此课程'
                    })
                    continue
                
                # 检查课程是否已满
                enrolled_count = CourseStudent.get_enrollment_count(course_id)
                if enrolled_count >= course.max_students:
                    failed_students.append({
                        'student_id': student_id,
                        'reason': '课程已满'
                    })
                    continue
                
                # 创建报名记录
                enrollment = CourseStudent(
                    course_id=course_id,
                    student_id=student_id,
                    enrollment_date=datetime.now().isoformat(),
                    status='enrolled'
                )
                enrollment.save()
                success_count += 1
                
            except Exception as e:
                failed_students.append({
                    'student_id': student_id,
                    'reason': f'报名失败: {str(e)}'
                })
        
        return jsonify({
            'success': True,
            'message': f'批量报名完成，成功: {success_count}人，失败: {len(failed_students)}人',
            'data': {
                'success_count': success_count,
                'failed_count': len(failed_students),
                'failed_students': failed_students
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'批量报名失败: {str(e)}',
            'code': 'BATCH_ENROLL_ERROR'
        }), 500

@courses_bp.route('/upcoming', methods=['GET'])
@jwt_required()
def get_upcoming_courses():
    """获取即将到来的课程"""
    try:
        user_id = int(get_jwt_identity())
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
            courses = Course.get_upcoming_courses(user_id, limit)
        else:
            # 学生获取已报名的即将到来的课程
            enrollments = CourseStudent.get_by_student(user_id)
            course_ids = [e.course_id for e in enrollments]
            courses = []
            for course_id in course_ids:
                course = Course.find_by_id(course_id)
                if course and course.start_time and datetime.fromisoformat(course.start_time.replace('Z', '+00:00')) > datetime.now():
                    courses.append(course)
            # 按开始时间排序并限制数量
            courses.sort(key=lambda x: x.start_time)
            courses = courses[:limit]
        
        # 转换为字典格式
        course_list = []
        for course in courses:
            course_dict = course.to_dict()
            course_dict['enrolled_count'] = CourseStudent.get_enrollment_count(course.id)
            course_list.append(course_dict)
        
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