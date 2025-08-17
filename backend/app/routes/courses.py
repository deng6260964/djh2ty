from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.database import db

courses_bp = Blueprint('courses', __name__)

@courses_bp.route('/', methods=['GET'])
@jwt_required()
def get_courses():
    """获取课程列表"""
    # TODO: 实现课程列表获取逻辑
    return jsonify({'message': 'Courses endpoint - to be implemented'}), 200

@courses_bp.route('/<int:course_id>', methods=['GET'])
@jwt_required()
def get_course(course_id):
    """获取课程详情"""
    # TODO: 实现课程详情获取逻辑
    return jsonify({'message': f'Course {course_id} endpoint - to be implemented'}), 200