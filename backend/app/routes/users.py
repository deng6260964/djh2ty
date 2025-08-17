from flask import Blueprint, jsonify, request
from app.utils.permissions import (
    require_auth, admin_required, teacher_required, 
    require_permission, Permission, PermissionManager
)
from app.models.user import User
from app.database import db
from app.utils.password_manager import PasswordManager
from sqlalchemy import or_
import logging

logger = logging.getLogger(__name__)
users_bp = Blueprint('users', __name__)

@users_bp.route('', methods=['GET'])
@require_auth
@require_permission(Permission.USER_READ)
def get_users(current_user):
    """获取用户列表"""
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 100)  # 限制最大每页数量
        role = request.args.get('role')
        search = request.args.get('search')
        is_active = request.args.get('is_active')
        
        # 构建查询
        query = User.query
        
        # 角色过滤
        if role:
            query = query.filter(User.role == role)
        
        # 状态过滤
        if is_active is not None:
            is_active_bool = is_active.lower() in ['true', '1', 'yes']
            query = query.filter(User.is_active == is_active_bool)
        
        # 搜索过滤（姓名或邮箱）
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    User.name.ilike(search_pattern),
                    User.email.ilike(search_pattern)
                )
            )
        
        # 权限控制：非管理员只能查看激活的用户
        if current_user.role != 'admin':
            query = query.filter(User.is_active == True)
        
        # 分页查询
        pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        users = pagination.items
        
        return jsonify({
            'success': True,
            'data': {
                'users': [user.to_dict() for user in users],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': pagination.total,
                    'pages': pagination.pages,
                    'has_next': pagination.has_next,
                    'has_prev': pagination.has_prev
                }
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting users: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'Failed to retrieve users'
        }), 500

@users_bp.route('/<int:user_id>', methods=['GET'])
@require_auth
@require_permission(Permission.USER_READ)
def get_user(user_id, current_user):
    """获取用户详情"""
    try:
        # 查找用户
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'error': 'USER_NOT_FOUND',
                'message': 'User not found'
            }), 404
        
        # 权限检查：非管理员只能查看自己的信息或激活用户的信息
        if current_user.role != 'admin':
            if user.id != current_user.id and not user.is_active:
                return jsonify({
                    'success': False,
                    'error': 'ACCESS_DENIED',
                    'message': 'Access denied'
                }), 403
        
        return jsonify({
            'success': True,
            'data': {
                'user': user.to_dict()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting user {user_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'Failed to retrieve user'
        }), 500

@users_bp.route('', methods=['POST'])
@require_auth
@require_permission(Permission.USER_CREATE)
def create_user(current_user):
    """创建新用户"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'INVALID_INPUT',
                'message': 'No data provided'
            }), 400
        
        # 验证必填字段
        required_fields = ['email', 'name', 'password', 'role']
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return jsonify({
                'success': False,
                'error': 'MISSING_FIELDS',
                'message': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400
        
        # 验证邮箱格式
        email = data['email'].strip().lower()
        if '@' not in email or '.' not in email:
            return jsonify({
                'success': False,
                'error': 'INVALID_EMAIL',
                'message': 'Invalid email format'
            }), 400
        
        # 检查邮箱是否已存在
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({
                'success': False,
                'error': 'EMAIL_EXISTS',
                'message': 'Email already exists'
            }), 409
        
        # 验证角色
        valid_roles = ['admin', 'teacher', 'student']
        if data['role'] not in valid_roles:
            return jsonify({
                'success': False,
                'error': 'INVALID_ROLE',
                'message': f'Invalid role. Must be one of: {", ".join(valid_roles)}'
            }), 400
        
        # 验证密码强度
        password = data['password']
        if len(password) < 8:
            return jsonify({
                'success': False,
                'error': 'WEAK_PASSWORD',
                'message': 'Password must be at least 8 characters long'
            }), 400
        
        # 创建新用户
        password_hash = PasswordManager.hash_password(password)
        new_user = User(
            email=email,
            name=data['name'].strip(),
            password_hash=password_hash,
            role=data['role'],
            avatar_url=data.get('avatar_url'),
            phone=data.get('phone'),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        logger.info(f"User created: {new_user.email} by {current_user.email}")
        
        return jsonify({
            'success': True,
            'data': {
                'user': new_user.to_dict()
            },
            'message': 'User created successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating user: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'Failed to create user'
        }), 500

@users_bp.route('/<int:user_id>', methods=['PUT'])
@require_auth
@require_permission(Permission.USER_UPDATE)
def update_user(user_id, current_user):
    """更新用户信息"""
    try:
        # 查找用户
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'error': 'USER_NOT_FOUND',
                'message': 'User not found'
            }), 404
        
        # 权限检查：非管理员只能更新自己的信息
        if current_user.role != 'admin' and user.id != current_user.id:
            return jsonify({
                'success': False,
                'error': 'ACCESS_DENIED',
                'message': 'You can only update your own profile'
            }), 403
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'INVALID_INPUT',
                'message': 'No data provided'
            }), 400
        
        # 更新邮箱（如果提供）
        if 'email' in data:
            new_email = data['email'].strip().lower()
            if new_email != user.email:
                # 验证邮箱格式
                if '@' not in new_email or '.' not in new_email:
                    return jsonify({
                        'success': False,
                        'error': 'INVALID_EMAIL',
                        'message': 'Invalid email format'
                    }), 400
                
                # 检查邮箱是否已存在
                existing_user = User.query.filter_by(email=new_email).first()
                if existing_user:
                    return jsonify({
                        'success': False,
                        'error': 'EMAIL_EXISTS',
                        'message': 'Email already exists'
                    }), 409
                
                user.email = new_email
        
        # 更新姓名
        if 'name' in data:
            user.name = data['name'].strip()
        
        # 更新角色（仅管理员可以修改）
        if 'role' in data:
            if current_user.role != 'admin':
                return jsonify({
                    'success': False,
                    'error': 'ACCESS_DENIED',
                    'message': 'Only administrators can change user roles'
                }), 403
            
            valid_roles = ['admin', 'teacher', 'student']
            if data['role'] not in valid_roles:
                return jsonify({
                    'success': False,
                    'error': 'INVALID_ROLE',
                    'message': f'Invalid role. Must be one of: {", ".join(valid_roles)}'
                }), 400
            
            user.role = data['role']
        
        # 更新头像URL
        if 'avatar_url' in data:
            user.avatar_url = data['avatar_url']
        
        # 更新电话
        if 'phone' in data:
            user.phone = data['phone']
        
        # 更新激活状态（仅管理员可以修改）
        if 'is_active' in data:
            if current_user.role != 'admin':
                return jsonify({
                    'success': False,
                    'error': 'ACCESS_DENIED',
                    'message': 'Only administrators can change user status'
                }), 403
            
            user.is_active = bool(data['is_active'])
        
        db.session.commit()
        
        logger.info(f"User updated: {user.email} by {current_user.email}")
        
        return jsonify({
            'success': True,
            'data': {
                'user': user.to_dict()
            },
            'message': 'User updated successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating user {user_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'Failed to update user'
        }), 500

@users_bp.route('/<int:user_id>', methods=['DELETE'])
@require_auth
@require_permission(Permission.USER_DELETE)
def delete_user(user_id, current_user):
    """删除用户（软删除）"""
    try:
        # 查找用户
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'error': 'USER_NOT_FOUND',
                'message': 'User not found'
            }), 404
        
        # 防止删除自己
        if user.id == current_user.id:
            return jsonify({
                'success': False,
                'error': 'CANNOT_DELETE_SELF',
                'message': 'You cannot delete your own account'
            }), 400
        
        # 软删除：设置为非激活状态
        user.is_active = False
        db.session.commit()
        
        logger.info(f"User deactivated: {user.email} by {current_user.email}")
        
        return jsonify({
            'success': True,
            'message': 'User deactivated successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting user {user_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'Failed to delete user'
        }), 500

@users_bp.route('/<int:user_id>/role', methods=['PUT'])
@require_auth
@admin_required
def update_user_role(user_id, current_user):
    """更新用户角色（仅管理员）"""
    try:
        # 查找用户
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'error': 'USER_NOT_FOUND',
                'message': 'User not found'
            }), 404
        
        data = request.get_json()
        if not data or 'role' not in data:
            return jsonify({
                'success': False,
                'error': 'INVALID_INPUT',
                'message': 'Role is required'
            }), 400
        
        # 验证角色
        valid_roles = ['admin', 'teacher', 'student']
        new_role = data['role']
        if new_role not in valid_roles:
            return jsonify({
                'success': False,
                'error': 'INVALID_ROLE',
                'message': f'Invalid role. Must be one of: {", ".join(valid_roles)}'
            }), 400
        
        old_role = user.role
        user.role = new_role
        db.session.commit()
        
        logger.info(f"User role updated: {user.email} from {old_role} to {new_role} by {current_user.email}")
        
        return jsonify({
            'success': True,
            'data': {
                'user': user.to_dict(),
                'old_role': old_role,
                'new_role': new_role
            },
            'message': 'User role updated successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating user role {user_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'Failed to update user role'
        }), 500

@users_bp.route('/<int:user_id>/status', methods=['PUT'])
@require_auth
@admin_required
def update_user_status(user_id, current_user):
    """更新用户状态（激活/停用）"""
    try:
        # 查找用户
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'error': 'USER_NOT_FOUND',
                'message': 'User not found'
            }), 404
        
        # 防止停用自己
        if user.id == current_user.id:
            return jsonify({
                'success': False,
                'error': 'CANNOT_DEACTIVATE_SELF',
                'message': 'You cannot deactivate your own account'
            }), 400
        
        data = request.get_json()
        if not data or 'is_active' not in data:
            return jsonify({
                'success': False,
                'error': 'INVALID_INPUT',
                'message': 'is_active status is required'
            }), 400
        
        old_status = user.is_active
        new_status = bool(data['is_active'])
        user.is_active = new_status
        db.session.commit()
        
        status_text = 'activated' if new_status else 'deactivated'
        logger.info(f"User {status_text}: {user.email} by {current_user.email}")
        
        return jsonify({
            'success': True,
            'data': {
                'user': user.to_dict(),
                'old_status': old_status,
                'new_status': new_status
            },
            'message': f'User {status_text} successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating user status {user_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'Failed to update user status'
        }), 500

@users_bp.route('/<int:user_id>/permissions', methods=['GET'])
@require_auth
def get_user_permissions(user_id, current_user):
    """获取用户权限列表"""
    try:
        # 查找用户
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'error': 'USER_NOT_FOUND',
                'message': 'User not found'
            }), 404
        
        # 权限检查：只能查看自己的权限或管理员可以查看所有用户权限
        if current_user.role != 'admin' and user.id != current_user.id:
            return jsonify({
                'success': False,
                'error': 'ACCESS_DENIED',
                'message': 'You can only view your own permissions'
            }), 403
        
        # 获取用户权限
        permissions = PermissionManager.get_user_permissions(user.role)
        permission_list = [perm.value for perm in permissions]
        
        return jsonify({
            'success': True,
            'data': {
                'user_id': user.id,
                'role': user.role,
                'permissions': permission_list
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting user permissions {user_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'Failed to retrieve user permissions'
        }), 500

@users_bp.route('/roles', methods=['GET'])
@require_auth
def get_available_roles(current_user):
    """获取可用角色列表"""
    try:
        roles = [
            {
                'value': 'admin',
                'label': 'Administrator',
                'description': 'Full system access and user management'
            },
            {
                'value': 'teacher',
                'label': 'Teacher',
                'description': 'Course and assignment management'
            },
            {
                'value': 'student',
                'label': 'Student',
                'description': 'Course participation and assignment submission'
            }
        ]
        
        return jsonify({
            'success': True,
            'data': {
                'roles': roles
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting available roles: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'Failed to retrieve available roles'
        }), 500

@users_bp.route('/stats', methods=['GET'])
@require_auth
@admin_required
def get_user_stats(current_user):
    """获取用户统计信息（仅管理员）"""
    try:
        # 总用户数
        total_users = User.query.count()
        
        # 激活用户数
        active_users = User.query.filter_by(is_active=True).count()
        
        # 按角色统计
        admin_count = User.query.filter_by(role='admin', is_active=True).count()
        teacher_count = User.query.filter_by(role='teacher', is_active=True).count()
        student_count = User.query.filter_by(role='student', is_active=True).count()
        
        # 最近注册用户（最近7天）
        from datetime import datetime, timedelta
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_registrations = User.query.filter(User.created_at >= week_ago).count()
        
        return jsonify({
            'success': True,
            'data': {
                'total_users': total_users,
                'active_users': active_users,
                'inactive_users': total_users - active_users,
                'role_distribution': {
                    'admin': admin_count,
                    'teacher': teacher_count,
                    'student': student_count
                },
                'recent_registrations': recent_registrations
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting user stats: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'Failed to retrieve user statistics'
        }), 500

@users_bp.route('/validate/email', methods=['POST'])
def validate_email():
    """验证邮箱格式和唯一性"""
    try:
        data = request.get_json()
        if not data or 'email' not in data:
            return jsonify({
                'success': False,
                'error': 'INVALID_INPUT',
                'message': 'Email is required'
            }), 400
        
        email = data['email'].strip().lower()
        
        # 邮箱格式验证
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return jsonify({
                'success': False,
                'error': 'INVALID_EMAIL_FORMAT',
                'message': 'Invalid email format'
            }), 400
        
        # 检查邮箱是否已存在
        existing_user = User.query.filter_by(email=email).first()
        is_available = existing_user is None
        
        # 如果是更新操作，检查是否是当前用户的邮箱
        user_id = data.get('user_id')
        if user_id and existing_user and existing_user.id == int(user_id):
            is_available = True
        
        return jsonify({
            'success': True,
            'data': {
                'email': email,
                'is_valid_format': True,
                'is_available': is_available,
                'message': 'Email is available' if is_available else 'Email is already taken'
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error validating email: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'Failed to validate email'
        }), 500

@users_bp.route('/validate/password', methods=['POST'])
def validate_password():
    """验证密码强度"""
    try:
        data = request.get_json()
        if not data or 'password' not in data:
            return jsonify({
                'success': False,
                'error': 'INVALID_INPUT',
                'message': 'Password is required'
            }), 400
        
        password = data['password']
        
        # 密码强度检查
        validation_result = {
            'is_valid': True,
            'score': 0,
            'requirements': {
                'min_length': len(password) >= 8,
                'has_uppercase': any(c.isupper() for c in password),
                'has_lowercase': any(c.islower() for c in password),
                'has_digit': any(c.isdigit() for c in password),
                'has_special': any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password)
            },
            'suggestions': []
        }
        
        # 计算分数
        for requirement, passed in validation_result['requirements'].items():
            if passed:
                validation_result['score'] += 20
        
        # 生成建议
        if not validation_result['requirements']['min_length']:
            validation_result['suggestions'].append('Password must be at least 8 characters long')
        if not validation_result['requirements']['has_uppercase']:
            validation_result['suggestions'].append('Password must contain at least one uppercase letter')
        if not validation_result['requirements']['has_lowercase']:
            validation_result['suggestions'].append('Password must contain at least one lowercase letter')
        if not validation_result['requirements']['has_digit']:
            validation_result['suggestions'].append('Password must contain at least one digit')
        if not validation_result['requirements']['has_special']:
            validation_result['suggestions'].append('Password must contain at least one special character')
        
        # 判断是否有效（至少满足4个要求）
        passed_requirements = sum(validation_result['requirements'].values())
        validation_result['is_valid'] = passed_requirements >= 4
        
        # 强度等级
        if validation_result['score'] >= 80:
            strength = 'Strong'
        elif validation_result['score'] >= 60:
            strength = 'Medium'
        else:
            strength = 'Weak'
        
        validation_result['strength'] = strength
        
        return jsonify({
            'success': True,
            'data': validation_result
        }), 200
        
    except Exception as e:
        logger.error(f"Error validating password: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'Failed to validate password'
        }), 500

@users_bp.route('/validate/username', methods=['POST'])
def validate_name():
    """验证用户名格式和唯一性"""
    try:
        data = request.get_json()
        if not data or 'name' not in data:
            return jsonify({
                'success': False,
                'error': 'INVALID_INPUT',
                'message': 'Name is required'
            }), 400
        
        name = data['name'].strip()
        
        # 用户名格式验证
        validation_result = {
            'is_valid': True,
            'requirements': {
                'min_length': len(name) >= 2,
                'max_length': len(name) <= 50,
                'valid_characters': all(c.isalnum() or c in ' -_.' for c in name),
                'not_empty': bool(name.strip())
            },
            'suggestions': []
        }
        
        # 生成建议
        if not validation_result['requirements']['min_length']:
            validation_result['suggestions'].append('Name must be at least 2 characters long')
        if not validation_result['requirements']['max_length']:
            validation_result['suggestions'].append('Name must be no more than 50 characters long')
        if not validation_result['requirements']['valid_characters']:
            validation_result['suggestions'].append('Name can only contain letters, numbers, spaces, hyphens, underscores, and dots')
        if not validation_result['requirements']['not_empty']:
            validation_result['suggestions'].append('Name cannot be empty')
        
        # 判断是否有效
        validation_result['is_valid'] = all(validation_result['requirements'].values())
        
        # 检查用户名是否已存在（可选）
        check_uniqueness = data.get('check_uniqueness', False)
        if check_uniqueness and validation_result['is_valid']:
            existing_user = User.query.filter_by(name=name).first()
            is_available = existing_user is None
            
            # 如果是更新操作，检查是否是当前用户的名称
            user_id = data.get('user_id')
            if user_id and existing_user and existing_user.id == int(user_id):
                is_available = True
            
            validation_result['is_available'] = is_available
            if not is_available:
                validation_result['suggestions'].append('This name is already taken')
        
        return jsonify({
            'success': True,
            'data': validation_result
        }), 200
        
    except Exception as e:
        logger.error(f"Error validating name: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'Failed to validate name'
        }), 500

@users_bp.route('/validate/phone', methods=['POST'])
def validate_phone():
    """验证手机号格式"""
    try:
        data = request.get_json()
        if not data or 'phone' not in data:
            return jsonify({
                'success': False,
                'error': 'INVALID_INPUT',
                'message': 'Phone number is required'
            }), 400
        
        phone = data['phone'].strip()
        
        # 手机号格式验证（支持中国大陆手机号）
        import re
        phone_pattern = r'^1[3-9]\d{9}$'
        is_valid_format = bool(re.match(phone_pattern, phone))
        
        validation_result = {
            'is_valid': is_valid_format,
            'phone': phone,
            'suggestions': []
        }
        
        if not is_valid_format:
            validation_result['suggestions'].append('Please enter a valid Chinese mobile phone number (11 digits starting with 1)')
        
        # 检查手机号是否已存在（可选）
        check_uniqueness = data.get('check_uniqueness', False)
        if check_uniqueness and is_valid_format:
            existing_user = User.query.filter_by(phone=phone).first()
            is_available = existing_user is None
            
            # 如果是更新操作，检查是否是当前用户的手机号
            user_id = data.get('user_id')
            if user_id and existing_user and existing_user.id == int(user_id):
                is_available = True
            
            validation_result['is_available'] = is_available
            if not is_available:
                validation_result['suggestions'].append('This phone number is already registered')
        
        return jsonify({
            'success': True,
            'data': validation_result
        }), 200
        
    except Exception as e:
        logger.error(f"Error validating phone: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'Failed to validate phone number'
        }), 500