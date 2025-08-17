from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token, jwt_required, 
    get_jwt_identity, get_jwt
)
from app.database import db
from app.models.user import User
from app.utils.jwt_middleware import JWTMiddleware
from app.utils.permissions import require_auth, UserRole
from app.utils.auth import hash_password, verify_password, PasswordManager
from app.utils.logger import logger_manager
from datetime import datetime, timedelta
import uuid

# 获取logger实例
logger = logger_manager.get_logger('auth')

# 导入全局会话管理器实例
from app import session_manager

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        data = request.get_json()
        
        # 验证输入数据
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({
                'error': 'Email and password are required',
                'code': 'MISSING_CREDENTIALS'
            }), 400
        
        # 查找用户
        user = User.query.filter_by(email=data['email']).first()
        
        if not user:
            logger.warning(f"Login attempt with non-existent email: {data['email']}")
            return jsonify({
                'error': 'Invalid credentials',
                'code': 'INVALID_CREDENTIALS'
            }), 401
        
        # 检查用户是否激活
        if not user.is_active:
            logger.warning(f"Login attempt with inactive user: {user.email}")
            return jsonify({
                'error': 'Account is inactive',
                'code': 'ACCOUNT_INACTIVE'
            }), 401
        
        # 验证密码
        if not verify_password(data['password'], user.password_hash):
            logger.warning(f"Failed login attempt for user: {user.email}")
            return jsonify({
                'error': 'Invalid credentials',
                'code': 'INVALID_CREDENTIALS'
            }), 401
        
        # 生成JWT tokens
        jwt_middleware = JWTMiddleware()
        tokens = jwt_middleware.generate_tokens(user)
        
        # 从access_token中解析jti
        import jwt as jwt_lib
        decoded = jwt_lib.decode(
            tokens['access_token'],
            options={"verify_signature": False}
        )
        jti = decoded['jti']
        
        # 创建会话
        session_info = session_manager.create_session(
            user=user,
            jti=jti
        )
        
        # 更新用户最后登录时间
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"Successful login for user: {user.email}")
        
        return jsonify({
            'access_token': tokens['access_token'],
            'refresh_token': tokens['refresh_token'],
            'expires_in': tokens['expires_in'],
            'user': {
                'id': user.id,
                'email': user.email,
                'name': user.name,
                'role': user.role,
                'avatar_url': user.avatar_url
            },
            'session': {
                'session_id': session_info.session_id,
                'expires_at': session_info.expires_at.isoformat()
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'code': 'INTERNAL_ERROR'
        }), 500

@auth_bp.route('/register', methods=['POST'])
def register():
    """用户注册"""
    try:
        data = request.get_json()
        
        # 验证输入数据
        required_fields = ['email', 'password', 'name', 'role']
        if not data or not all(field in data for field in required_fields):
            return jsonify({
                'error': 'All fields are required',
                'code': 'MISSING_FIELDS',
                'required_fields': required_fields
            }), 400
        
        # 验证邮箱格式
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, data['email']):
            return jsonify({
                'error': 'Invalid email format',
                'code': 'INVALID_EMAIL'
            }), 400
        
        # 检查邮箱是否已存在
        if User.query.filter_by(email=data['email']).first():
            return jsonify({
                'error': 'Email already exists',
                'code': 'EMAIL_EXISTS'
            }), 409
        
        # 验证角色
        valid_roles = [role.value for role in UserRole]
        if data['role'] not in valid_roles:
            return jsonify({
                'error': 'Invalid role',
                'code': 'INVALID_ROLE',
                'valid_roles': valid_roles
            }), 400
        
        # 验证密码强度
        password_manager = PasswordManager()
        validation_result = password_manager.validate_password_strength(data['password'])
        
        if not validation_result['is_valid']:
            return jsonify({
                'error': 'Password does not meet requirements',
                'code': 'WEAK_PASSWORD',
                'validation_errors': validation_result['errors'],
                'requirements': password_manager.generate_password_requirements()
            }), 400
        
        # 创建用户
        user = User(
            email=data['email'],
            name=data['name'],
            role=data['role'],
            password_hash=hash_password(data['password']),
            phone=data.get('phone'),
            avatar_url=data.get('avatar_url'),
            is_active=True
        )
        
        db.session.add(user)
        db.session.commit()
        
        # 注册成功后自动登录用户
        jwt_middleware = JWTMiddleware()
        tokens = jwt_middleware.generate_tokens(user)
        
        # 从access_token中解析jti
        import jwt as jwt_lib
        decoded = jwt_lib.decode(
            tokens['access_token'],
            options={"verify_signature": False}
        )
        jti = decoded['jti']
        
        # 创建会话
        session_info = session_manager.create_session(
            user=user,
            jti=jti
        )
        
        logger.info(f"New user registered and logged in: {user.email} with role {user.role}")
        
        return jsonify({
            'message': 'User created successfully',
            'access_token': tokens['access_token'],
            'refresh_token': tokens['refresh_token'],
            'expires_in': tokens['expires_in'],
            'user': {
                'id': user.id,
                'email': user.email,
                'name': user.name,
                'role': user.role
            }
        }), 201
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Registration error: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'code': 'INTERNAL_ERROR'
        }), 500

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """刷新访问令牌"""
    try:
        current_user_id = get_jwt_identity()
        jwt_data = get_jwt()
        
        # 验证用户是否存在且激活
        user = User.query.get(current_user_id)
        if not user or not user.is_active:
            return jsonify({
                'error': 'User not found or inactive',
                'code': 'USER_INACTIVE'
            }), 401
        
        # 验证用户是否有活跃会话 (确保user_id是int类型)
        user_id_int = int(current_user_id) if isinstance(current_user_id, str) else current_user_id
        user_sessions = session_manager.get_user_sessions(user_id_int)
        if not user_sessions:
            return jsonify({
                'error': 'NO_ACTIVE_SESSION',
                'message': '没有找到活跃会话'
            }), 401
        
        # 生成新的访问令牌
        jwt_middleware = JWTMiddleware()
        new_access_token = jwt_middleware.refresh_access_token(current_user_id)
        
        logger.info(f"Token refreshed for user: {user.email}")
        
        return jsonify({
            'access_token': new_access_token['access_token'],
            'expires_in': new_access_token['expires_in']
        }), 200
    
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'code': 'INTERNAL_ERROR'
        }), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """用户登出"""
    try:
        jwt_data = get_jwt()
        session_id = jwt_data.get('jti')
        
        # 撤销会话
        session_manager.revoke_session(session_id)
        
        # 将token加入黑名单
        jwt_middleware = JWTMiddleware()
        jwt_middleware.revoke_token(session_id)
        
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if user:
            logger.info(f"User logged out: {user.email}")
        
        return jsonify({
            'message': 'Successfully logged out'
        }), 200
    
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'code': 'INTERNAL_ERROR'
        }), 500

@auth_bp.route('/logout-all', methods=['POST'])
@jwt_required()
def logout_all():
    """登出所有设备"""
    try:
        current_user_id = get_jwt_identity()
        jwt_data = get_jwt()
        current_session_id = jwt_data.get('jti')
        
        # 撤销用户的所有会话（除了当前会话）
        revoked_count = session_manager.revoke_user_sessions(
            current_user_id, 
            exclude_session=current_session_id
        )
        
        user = User.query.get(current_user_id)
        if user:
            logger.info(f"User {user.email} logged out from {revoked_count} devices")
        
        return jsonify({
            'message': f'Successfully logged out from {revoked_count} devices'
        }), 200
    
    except Exception as e:
        logger.error(f"Logout all error: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'code': 'INTERNAL_ERROR'
        }), 500

@auth_bp.route('/me', methods=['GET'])
@require_auth
def get_current_user(current_user):
    """获取当前用户信息"""
    try:
        # 获取用户会话信息
        user_sessions = session_manager.get_user_sessions(current_user.id)
        
        return jsonify({
            'id': current_user.id,
            'email': current_user.email,
            'name': current_user.name,
            'role': current_user.role,
            'avatar_url': current_user.avatar_url,
            'phone': current_user.phone,
            'is_active': current_user.is_active,
            'created_at': current_user.created_at.isoformat(),
            'updated_at': current_user.updated_at.isoformat() if current_user.updated_at else None,
            'active_sessions': len(user_sessions)
        }), 200
    
    except Exception as e:
        logger.error(f"Get current user error: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'code': 'INTERNAL_ERROR'
        }), 500

@auth_bp.route('/sessions', methods=['GET'])
@require_auth
def get_user_sessions(current_user):
    """获取用户的所有活跃会话"""
    try:
        jwt_data = get_jwt()
        current_session_id = jwt_data.get('jti')
        
        user_sessions = session_manager.get_user_sessions(current_user.id)
        
        sessions_data = []
        for session in user_sessions:
            sessions_data.append({
                'session_id': session.session_id,
                'ip_address': session.ip_address,
                'device_info': session.device_info,
                'location_info': session.location_info,
                'login_time': session.login_time.isoformat(),
                'last_activity': session.last_activity.isoformat(),
                'expires_at': session.expires_at.isoformat(),
                'is_current': session.session_id == current_session_id
            })
        
        return jsonify({
            'sessions': sessions_data,
            'total_count': len(sessions_data)
        }), 200
    
    except Exception as e:
        logger.error(f"Get user sessions error: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'code': 'INTERNAL_ERROR'
        }), 500

@auth_bp.route('/sessions/<session_id>', methods=['DELETE'])
@require_auth
def revoke_session(current_user, session_id):
    """撤销指定会话"""
    try:
        # 获取要撤销的会话信息
        session_info = session_manager.get_session(session_id)
        
        if not session_info:
            return jsonify({
                'error': 'Session not found',
                'code': 'SESSION_NOT_FOUND'
            }), 404
        
        # 检查会话是否属于当前用户
        if session_info.user_id != current_user.id:
            return jsonify({
                'error': 'Permission denied',
                'code': 'PERMISSION_DENIED'
            }), 403
        
        # 撤销会话
        success = session_manager.revoke_session(session_id)
        
        if success:
            return jsonify({
                'message': 'Session revoked successfully'
            }), 200
        else:
            return jsonify({
                'error': 'Failed to revoke session',
                'code': 'REVOKE_FAILED'
            }), 500
    
    except Exception as e:
        logger.error(f"Revoke session error: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'code': 'INTERNAL_ERROR'
        }), 500

@auth_bp.route('/change-password', methods=['POST'])
@require_auth
def change_password(current_user):
    """修改密码"""
    try:
        data = request.get_json()
        
        # 验证输入数据
        if not data or not data.get('current_password') or not data.get('new_password'):
            return jsonify({
                'error': 'Current password and new password are required',
                'code': 'MISSING_PASSWORDS'
            }), 400
        
        # 验证当前密码
        if not verify_password(data['current_password'], current_user.password_hash):
            return jsonify({
                'error': 'Current password is incorrect',
                'code': 'INVALID_CURRENT_PASSWORD'
            }), 400
        
        # 验证新密码强度
        password_manager = PasswordManager()
        validation_result = password_manager.validate_password_strength(data['new_password'])
        
        if not validation_result['is_valid']:
            return jsonify({
                'error': 'New password does not meet requirements',
                'code': 'WEAK_PASSWORD',
                'validation_errors': validation_result['errors'],
                'requirements': password_manager.generate_password_requirements()
            }), 400
        
        # 检查新密码是否与当前密码相同
        if verify_password(data['new_password'], current_user.password_hash):
            return jsonify({
                'error': 'New password must be different from current password',
                'code': 'SAME_PASSWORD'
            }), 400
        
        # 更新密码
        current_user.password_hash = hash_password(data['new_password'])
        current_user.updated_at = datetime.utcnow()
        db.session.commit()
        
        # 可选：撤销其他会话（强制重新登录）
        if data.get('logout_other_sessions', False):
            jwt_data = get_jwt()
            current_session_id = jwt_data.get('jti')
            session_manager.revoke_user_sessions(
                current_user.id, 
                exclude_session=current_session_id
            )
        
        logger.info(f"Password changed for user: {current_user.email}")
        
        return jsonify({
            'message': 'Password changed successfully'
        }), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Change password error: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'code': 'INTERNAL_ERROR'
        }), 500

@auth_bp.route('/validate-token', methods=['POST'])
@require_auth
def validate_token(current_user):
    """验证token有效性"""
    try:
        jwt_data = get_jwt()
        session_id = jwt_data.get('jti')
        
        # 验证会话
        is_valid = session_manager.validate_session(session_id)
        
        if is_valid:
            return jsonify({
                'valid': True,
                'message': 'Token is valid'
            }), 200
        else:
            return jsonify({
                'valid': False,
                'message': 'Token is invalid or expired'
            }), 401
    
    except Exception as e:
        logger.error(f"Validate token error: {str(e)}")
        return jsonify({
            'valid': False,
            'error': 'Internal server error',
            'code': 'INTERNAL_ERROR'
        }), 500