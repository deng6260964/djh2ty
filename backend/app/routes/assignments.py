from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.database import db

assignments_bp = Blueprint('assignments', __name__)

@assignments_bp.route('/', methods=['GET'])
@jwt_required()
def get_assignments():
    """获取作业列表"""
    # TODO: 实现作业列表获取逻辑
    return jsonify({'message': 'Assignments endpoint - to be implemented'}), 200

@assignments_bp.route('/<int:assignment_id>', methods=['GET'])
@jwt_required()
def get_assignment(assignment_id):
    """获取作业详情"""
    # TODO: 实现作业详情获取逻辑
    return jsonify({'message': f'Assignment {assignment_id} endpoint - to be implemented'}), 200