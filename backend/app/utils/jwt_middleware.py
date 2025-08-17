from flask import jsonify, current_app
from flask_jwt_extended import (
    JWTManager, create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt, verify_jwt_in_request,
    decode_token
)
from datetime import datetime, timedelta
from app.models.user import User
from app.database import db
import logging

logger = logging.getLogger(__name__)

class JWTMiddleware:
    """JWT认证中间件"""
    
    def __init__(self, app=None):
        self.app = app
        self.blacklisted_tokens = set()  # 简单的黑名单实现，生产环境建议使用Redis
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """初始化JWT中间件"""
        self.app = app
        
        # 配置JWT错误处理
        @app.jwt.expired_token_loader
        def expired_token_callback(jwt_header, jwt_payload):
            logger.warning(f"Expired token access attempt from user {jwt_payload.get('sub')}")
            return jsonify({
                'error': 'Token has expired',
                'message': 'Please refresh your token or login again'
            }), 401
        
        @app.jwt.invalid_token_loader
        def invalid_token_callback(error):
            logger.warning(f"Invalid token access attempt: {error}")
            return jsonify({
                'error': 'Invalid token',
                'message': 'Please provide a valid token'
            }), 401
        
        @app.jwt.unauthorized_loader
        def missing_token_callback(error):
            logger.info(f"Missing token access attempt: {error}")
            return jsonify({
                'error': 'Authorization token required',
                'message': 'Please provide a valid token'
            }), 401
        
        @app.jwt.revoked_token_loader
        def revoked_token_callback(jwt_header, jwt_payload):
            logger.warning(f"Revoked token access attempt from user {jwt_payload.get('sub')}")
            return jsonify({
                'error': 'Token has been revoked',
                'message': 'Please login again'
            }), 401
        
        @app.jwt.token_in_blocklist_loader
        def check_if_token_revoked(jwt_header, jwt_payload):
            """检查token是否在黑名单中"""
            jti = jwt_payload['jti']
            return jti in self.blacklisted_tokens
        
        # 移除additional_claims_loader，避免与手动添加的claims冲突
        # 所有claims都在generate_tokens方法中手动添加
        
        @app.jwt.user_identity_loader
        def user_identity_lookup(user):
            """用户身份加载器"""
            if isinstance(user, User):
                return user.id
            return user
        
        @app.jwt.user_lookup_loader
        def user_lookup_callback(_jwt_header, jwt_data):
            """用户查找回调"""
            identity = jwt_data["sub"]
            try:
                user_id = int(identity)
                # 使用merge确保用户对象在当前会话中
                user = User.query.filter_by(id=user_id).one_or_none()
                if user:
                    from app.database import db
                    return db.session.merge(user)
                return None
            except (ValueError, TypeError):
                return None
    
    def generate_tokens(self, user):
        """生成访问令牌和刷新令牌"""
        try:
            # 检查用户是否激活
            if not user.is_active:
                raise ValueError("User account is deactivated")
            
            # 生成访问令牌
            access_token = create_access_token(
                identity=str(user.id),
                additional_claims={
                    'role': user.role,
                    'email': user.email,
                    'is_active': user.is_active
                }
            )
            
            # 生成刷新令牌
            refresh_token = create_refresh_token(
                identity=str(user.id)
            )
            
            logger.info(f"Tokens generated for user {user.email} (ID: {user.id})")
            
            return {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'expires_in': current_app.config['JWT_ACCESS_TOKEN_EXPIRES'].total_seconds()
            }
        
        except Exception as e:
            logger.error(f"Error generating tokens for user {user.email}: {str(e)}")
            raise
    
    def refresh_access_token(self, current_user_id):
        """刷新访问令牌"""
        try:
            user_id = int(current_user_id)
            user = db.session.query(User).filter_by(id=user_id).first()
            if not user:
                raise ValueError("User not found")
            
            if not user.is_active:
                raise ValueError("User account is deactivated")
            
            # 生成新的访问令牌
            new_access_token = create_access_token(
                identity=str(user.id),
                additional_claims={
                    'role': user.role,
                    'email': user.email,
                    'is_active': user.is_active
                }
            )
            
            logger.info(f"Access token refreshed for user {user.email} (ID: {user.id})")
            
            return {
                'access_token': new_access_token,
                'expires_in': current_app.config['JWT_ACCESS_TOKEN_EXPIRES'].total_seconds()
            }
        
        except Exception as e:
            logger.error(f"Error refreshing token for user ID {current_user_id}: {str(e)}")
            raise
    
    def revoke_token(self, jti):
        """撤销token（添加到黑名单）"""
        try:
            self.blacklisted_tokens.add(jti)
            logger.info(f"Token revoked: {jti}")
        except Exception as e:
            logger.error(f"Error revoking token {jti}: {str(e)}")
            raise
    
    def get_current_user(self):
        """获取当前认证用户"""
        try:
            verify_jwt_in_request()
            current_user_id = get_jwt_identity()
            user_id = int(current_user_id)
            user = db.session.query(User).filter_by(id=user_id).first()
            
            if not user:
                logger.warning(f"User not found for ID: {current_user_id}")
                return None
            
            if not user.is_active:
                logger.warning(f"Inactive user access attempt: {user.email}")
                return None
            
            return user
        
        except Exception as e:
            logger.error(f"Error getting current user: {str(e)}")
            return None
    
    def validate_token_claims(self, required_role=None):
        """验证token声明"""
        try:
            verify_jwt_in_request()
            claims = get_jwt()
            
            # 检查用户是否激活
            if not claims.get('is_active', False):
                logger.warning(f"Inactive user token used: {claims.get('email')}")
                return False
            
            # 检查角色权限
            if required_role:
                user_role = claims.get('role')
                if user_role != required_role:
                    logger.warning(f"Insufficient permissions: required {required_role}, got {user_role}")
                    return False
            
            return True
        
        except Exception as e:
            logger.error(f"Error validating token claims: {str(e)}")
            return False

# 创建全局实例
jwt_middleware = JWTMiddleware()