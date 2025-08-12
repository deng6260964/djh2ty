from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import timedelta
import re

from models.user import User
from models.database import db

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

def validate_phone(phone):
    """验证手机号格式"""
    pattern = r'^1[3-9]\d{9}$'
    return re.match(pattern, phone) is not None

def validate_password(password):
    """验证密码强度"""
    if len(password) < 6:
        return False, "密码长度至少6位"
    if len(password) > 20:
        return False, "密码长度不能超过20位"
    return True, ""

@auth_bp.route('/register', methods=['POST'])
def register():
    """用户注册"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['phone', 'password', 'name', 'role']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'{field}不能为空',
                    'code': 'MISSING_FIELD'
                }), 400
        
        phone = data['phone'].strip()
        password = data['password']
        name = data['name'].strip()
        role = data['role']
        
        # 验证手机号格式
        if not validate_phone(phone):
            return jsonify({
                'success': False,
                'message': '手机号格式不正确',
                'code': 'INVALID_PHONE'
            }), 400
        
        # 验证密码强度
        is_valid, msg = validate_password(password)
        if not is_valid:
            return jsonify({
                'success': False,
                'message': msg,
                'code': 'INVALID_PASSWORD'
            }), 400
        
        # 验证角色
        if role not in ['teacher', 'student']:
            return jsonify({
                'success': False,
                'message': '角色必须是teacher或student',
                'code': 'INVALID_ROLE'
            }), 400
        
        # 检查手机号是否已存在
        existing_user = User.find_by_phone(phone)
        if existing_user:
            return jsonify({
                'success': False,
                'message': '该手机号已被注册',
                'code': 'PHONE_EXISTS'
            }), 400
        
        # 创建新用户
        user = User(
            phone=phone,
            name=name,
            role=role,
            avatar=data.get('avatar', ''),
            email=data.get('email', ''),
            status='active'
        )
        user.set_password(password)
        user.save()
        
        # 生成访问令牌
        access_token = create_access_token(
            identity=user.id,
            expires_delta=timedelta(days=7)
        )
        
        return jsonify({
            'success': True,
            'message': '注册成功',
            'data': {
                'user': user.to_dict(),
                'access_token': access_token
            }
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'注册失败: {str(e)}',
            'code': 'REGISTER_ERROR'
        }), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        if not data.get('phone') or not data.get('password'):
            return jsonify({
                'success': False,
                'message': '手机号和密码不能为空',
                'code': 'MISSING_CREDENTIALS'
            }), 400
        
        phone = data['phone'].strip()
        password = data['password']
        
        # 验证手机号格式
        if not validate_phone(phone):
            return jsonify({
                'success': False,
                'message': '手机号格式不正确',
                'code': 'INVALID_PHONE'
            }), 400
        
        # 查找用户
        user = User.find_by_phone(phone)
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        # 检查用户状态
        if user.status != 'active':
            return jsonify({
                'success': False,
                'message': '账户已被禁用',
                'code': 'ACCOUNT_DISABLED'
            }), 403
        
        # 验证密码
        if not user.check_password(password):
            return jsonify({
                'success': False,
                'message': '密码错误',
                'code': 'INVALID_PASSWORD'
            }), 401
        
        # 更新最后登录时间
        user.update_last_login()
        
        # 生成访问令牌
        access_token = create_access_token(
            identity=user.id,
            expires_delta=timedelta(days=7)
        )
        
        return jsonify({
            'success': True,
            'message': '登录成功',
            'data': {
                'user': user.to_dict(),
                'access_token': access_token
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'登录失败: {str(e)}',
            'code': 'LOGIN_ERROR'
        }), 500

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """获取用户信息"""
    try:
        user_id = get_jwt_identity()
        user = User.find_by_id(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        return jsonify({
            'success': True,
            'data': {
                'user': user.to_dict()
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取用户信息失败: {str(e)}',
            'code': 'GET_PROFILE_ERROR'
        }), 500

@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """更新用户信息"""
    try:
        user_id = get_jwt_identity()
        user = User.find_by_id(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        data = request.get_json()
        
        # 更新允许的字段
        if 'name' in data and data['name'].strip():
            user.name = data['name'].strip()
        
        if 'avatar' in data:
            user.avatar = data['avatar']
        
        if 'email' in data:
            user.email = data['email']
        
        # 保存更新
        user.save()
        
        return jsonify({
            'success': True,
            'message': '更新成功',
            'data': {
                'user': user.to_dict()
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'更新用户信息失败: {str(e)}',
            'code': 'UPDATE_PROFILE_ERROR'
        }), 500

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """修改密码"""
    try:
        user_id = get_jwt_identity()
        user = User.find_by_id(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        data = request.get_json()
        
        # 验证必填字段
        if not data.get('old_password') or not data.get('new_password'):
            return jsonify({
                'success': False,
                'message': '旧密码和新密码不能为空',
                'code': 'MISSING_PASSWORDS'
            }), 400
        
        old_password = data['old_password']
        new_password = data['new_password']
        
        # 验证旧密码
        if not user.check_password(old_password):
            return jsonify({
                'success': False,
                'message': '旧密码错误',
                'code': 'INVALID_OLD_PASSWORD'
            }), 401
        
        # 验证新密码强度
        is_valid, msg = validate_password(new_password)
        if not is_valid:
            return jsonify({
                'success': False,
                'message': msg,
                'code': 'INVALID_NEW_PASSWORD'
            }), 400
        
        # 检查新密码是否与旧密码相同
        if old_password == new_password:
            return jsonify({
                'success': False,
                'message': '新密码不能与旧密码相同',
                'code': 'SAME_PASSWORD'
            }), 400
        
        # 更新密码
        user.set_password(new_password)
        user.save()
        
        return jsonify({
            'success': True,
            'message': '密码修改成功'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'修改密码失败: {str(e)}',
            'code': 'CHANGE_PASSWORD_ERROR'
        }), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """用户登出"""
    try:
        # 在实际应用中，可以将token加入黑名单
        # 这里简单返回成功消息
        return jsonify({
            'success': True,
            'message': '登出成功'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'登出失败: {str(e)}',
            'code': 'LOGOUT_ERROR'
        }), 500