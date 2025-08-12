from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.course_management import CourseManagement
from models.user import User

course_management_bp = Blueprint('course_management', __name__)

@course_management_bp.route('/api/course-management', methods=['GET'])
@jwt_required()
def get_courses():
    """获取课程列表"""
    try:
        current_user_id = get_jwt_identity()
        user = User.find_by_id(current_user_id)
        
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        
        if user.role == 'teacher':
            # 教师只能看到自己的课程
            courses = CourseManagement.get_by_teacher(current_user_id)
        else:
            # 学生或管理员可以看到所有活跃课程
            courses = CourseManagement.get_all_active()
        
        return jsonify({
            'success': True,
            'data': [course.to_dict() for course in courses]
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'获取课程列表失败: {str(e)}'}), 500

@course_management_bp.route('/api/course-management', methods=['POST'])
@jwt_required()
def create_course():
    """创建课程"""
    try:
        current_user_id = get_jwt_identity()
        user = User.find_by_id(current_user_id)
        
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        
        if user.role != 'teacher':
            return jsonify({'error': '只有教师可以创建课程'}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({'error': '请求数据不能为空'}), 400
        
        # 验证必填字段
        required_fields = ['name', 'grade']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'缺少必填字段: {field}'}), 400
        
        # 创建课程
        course = CourseManagement(
            teacher_id=current_user_id,
            name=data.get('name'),
            description=data.get('description', ''),
            grade=data.get('grade'),
            subject=data.get('subject', 'English'),
            status='active'
        )
        
        course.save()
        
        return jsonify({
            'success': True,
            'message': '课程创建成功',
            'data': course.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'error': f'创建课程失败: {str(e)}'}), 500

@course_management_bp.route('/api/course-management/<int:course_id>', methods=['GET'])
@jwt_required()
def get_course(course_id):
    """获取课程详情"""
    try:
        current_user_id = get_jwt_identity()
        user = User.find_by_id(current_user_id)
        
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        
        course = CourseManagement.find_by_id(course_id)
        if not course:
            return jsonify({'error': '课程不存在'}), 404
        
        # 权限检查：教师只能查看自己的课程
        if user.role == 'teacher' and course.teacher_id != current_user_id:
            return jsonify({'error': '无权限访问此课程'}), 403
        
        return jsonify({
            'success': True,
            'data': course.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'获取课程详情失败: {str(e)}'}), 500

@course_management_bp.route('/api/course-management/<int:course_id>', methods=['PUT'])
@jwt_required()
def update_course(course_id):
    """更新课程"""
    try:
        current_user_id = get_jwt_identity()
        user = User.find_by_id(current_user_id)
        
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        
        if user.role != 'teacher':
            return jsonify({'error': '只有教师可以更新课程'}), 403
        
        course = CourseManagement.find_by_id(course_id)
        if not course:
            return jsonify({'error': '课程不存在'}), 404
        
        # 权限检查：教师只能更新自己的课程
        if course.teacher_id != current_user_id:
            return jsonify({'error': '无权限更新此课程'}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({'error': '请求数据不能为空'}), 400
        
        # 更新课程信息
        if 'name' in data:
            course.name = data['name']
        if 'description' in data:
            course.description = data['description']
        if 'grade' in data:
            course.grade = data['grade']
        if 'subject' in data:
            course.subject = data['subject']
        if 'status' in data:
            course.status = data['status']
        
        course.save()
        
        return jsonify({
            'success': True,
            'message': '课程更新成功',
            'data': course.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'更新课程失败: {str(e)}'}), 500

@course_management_bp.route('/api/course-management/<int:course_id>', methods=['DELETE'])
@jwt_required()
def delete_course(course_id):
    """删除课程"""
    try:
        current_user_id = get_jwt_identity()
        user = User.find_by_id(current_user_id)
        
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        
        if user.role != 'teacher':
            return jsonify({'error': '只有教师可以删除课程'}), 403
        
        course = CourseManagement.find_by_id(course_id)
        if not course:
            return jsonify({'error': '课程不存在'}), 404
        
        # 权限检查：教师只能删除自己的课程
        if course.teacher_id != current_user_id:
            return jsonify({'error': '无权限删除此课程'}), 403
        
        course.delete()
        
        return jsonify({
            'success': True,
            'message': '课程删除成功'
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'删除课程失败: {str(e)}'}), 500