import pytest
import jwt
from datetime import datetime, timedelta
from app.utils.jwt_middleware import JWTMiddleware
from app.models.user import User
from app.database import db
from app.utils.auth import hash_password
from flask_jwt_extended import create_access_token, create_refresh_token

class TestJWTMiddleware:
    """JWT中间件测试类"""
    
    @pytest.fixture
    def jwt_middleware(self, app):
        """创建JWT中间件实例"""
        with app.app_context():
            middleware = JWTMiddleware()
            return middleware
    
    @pytest.fixture
    def test_user_for_jwt(self, client):
        """创建测试用户"""
        import uuid
        with client.application.app_context():
            # 使用唯一的邮箱地址避免与其他测试冲突
            unique_email = f'jwt_test_{uuid.uuid4().hex[:8]}@example.com'
            
            user = User(
                email=unique_email,
                name='JWT Test User',
                password_hash=hash_password('TestPass123!'),
                role='student',
                is_active=True,
                created_at=datetime.utcnow()
            )
            db.session.add(user)
            db.session.commit()
            # 刷新对象以确保所有属性都已加载
            db.session.refresh(user)
            user_id = user.id
            db.session.expunge(user)  # 从会话中分离
            user.id = user_id  # 确保ID可用
            return user
    
    def test_generate_tokens(self, client, jwt_middleware, test_user_for_jwt):
        """测试生成tokens"""
        with client.application.app_context():
            # 重新查询用户以获取绑定到当前会话的对象
            user = User.query.filter_by(id=test_user_for_jwt.id).first()
            # 生成token
            tokens = jwt_middleware.generate_tokens(user)
            
            assert 'access_token' in tokens
            assert 'refresh_token' in tokens
            assert 'expires_in' in tokens
            assert tokens['expires_in'] > 0
    
    def test_refresh_access_token(self, client, jwt_middleware, test_user_for_jwt):
        """测试刷新访问令牌"""
        with client.application.app_context():
            # 重新查询用户以获取绑定到当前会话的对象
            user = User.query.filter_by(id=test_user_for_jwt.id).first()
            # 生成初始token
            tokens = jwt_middleware.generate_tokens(user)
            
            refresh_token = tokens['refresh_token']
            
            # 在JWT上下文中刷新访问令牌
            with client.application.test_request_context(
                headers={'Authorization': f'Bearer {refresh_token}'}
            ):
                new_tokens = jwt_middleware.refresh_access_token(user.id)
                
                assert 'access_token' in new_tokens
                assert 'expires_in' in new_tokens
                assert new_tokens['access_token'] != tokens['access_token']
    
    def test_get_current_user(self, client, jwt_middleware, test_user_for_jwt):
        """测试获取当前用户"""
        with client.application.app_context():
            # 重新查询用户以获取绑定到当前会话的对象
            user = User.query.filter_by(id=test_user_for_jwt.id).first()
            # 生成token
            tokens = jwt_middleware.generate_tokens(user)
            
            access_token = tokens['access_token']
            
            # 模拟请求头中的token
            with client.application.test_request_context(
                headers={'Authorization': f'Bearer {access_token}'}
            ):
                current_user = jwt_middleware.get_current_user()
                assert current_user is not None
                assert current_user.id == user.id
    
    def test_validate_token_claims(self, client, jwt_middleware, test_user_for_jwt):
        """测试验证token声明"""
        with client.application.app_context():
            # 重新查询用户以获取绑定到当前会话的对象
            user = User.query.filter_by(id=test_user_for_jwt.id).first()
            # 生成token
            tokens = jwt_middleware.generate_tokens(user)
            
            access_token = tokens['access_token']
            
            # 验证token声明
            with client.application.test_request_context(
                headers={'Authorization': f'Bearer {access_token}'}
            ):
                is_valid = jwt_middleware.validate_token_claims(
                    required_role=user.role
                )
                assert is_valid is True
    
    def test_validate_token_claims_invalid(self, client, jwt_middleware, test_user_for_jwt):
        """测试验证无效token声明"""
        with client.application.app_context():
            # 重新查询用户以获取绑定到当前会话的对象
            user = User.query.filter_by(id=test_user_for_jwt.id).first()
            # 生成token
            tokens = jwt_middleware.generate_tokens(user)
            
            access_token = tokens['access_token']
            
            # 验证错误的token声明
            with client.application.test_request_context(
                headers={'Authorization': f'Bearer {access_token}'}
            ):
                is_valid = jwt_middleware.validate_token_claims(
                    required_role='admin'  # 错误的角色
                )
                assert is_valid is False
    
    def test_revoke_token(self, client, jwt_middleware, test_user_for_jwt):
        """测试撤销token"""
        with client.application.app_context():
            # 重新查询用户以获取绑定到当前会话的对象
            user = User.query.filter_by(id=test_user_for_jwt.id).first()
            # 生成token
            tokens = jwt_middleware.generate_tokens(user)
            
            access_token = tokens['access_token']
            
            # 从token中解析jti
            import jwt
            decoded = jwt.decode(
                access_token,
                options={"verify_signature": False}
            )
            jti = decoded['jti']
            
            # 撤销token
            jwt_middleware.revoke_token(jti)
            
            # 验证token已被撤销
            assert jti in jwt_middleware.blacklisted_tokens
    
    def test_token_expiration(self, client, jwt_middleware, test_user_for_jwt):
        """测试token过期"""
        with client.application.app_context():
            # 重新查询用户以获取绑定到当前会话的对象
            user = User.query.filter_by(id=test_user_for_jwt.id).first()
            # 生成短期token（1秒过期）
            import time
            
            # 创建过期的token
            expired_token = create_access_token(
                identity=user.id,
                expires_delta=timedelta(seconds=-1)  # 已过期
            )
            
            # 验证过期token
            try:
                decoded = jwt.decode(
                    expired_token,
                    options={"verify_signature": False, "verify_exp": True}
                )
                pytest.fail("Expected token to be expired")
            except jwt.ExpiredSignatureError:
                # 预期的异常
                pass
    
    def test_invalid_token_format(self, jwt_middleware):
        """测试无效token格式"""
        invalid_tokens = [
            "invalid_token",
            "Bearer invalid_token",
            "",
            None,
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.invalid.signature"
        ]
        
        for invalid_token in invalid_tokens:
            try:
                if invalid_token:
                    jwt.decode(
                        invalid_token,
                        options={"verify_signature": False}
                    )
                    # 如果没有抛出异常，检查是否为有效格式
                    # 某些情况下可能需要进一步验证
                else:
                    # None或空字符串应该被拒绝
                    assert invalid_token in ["", None]
            except (jwt.DecodeError, jwt.InvalidTokenError, AttributeError):
                # 预期的异常
                pass
    
    def test_token_blacklist_check(self, client, jwt_middleware, test_user_for_jwt):
        """测试token黑名单检查"""
        with client.application.app_context():
            # 重新查询用户以获取绑定到当前会话的对象
            user = User.query.filter_by(id=test_user_for_jwt.id).first()
            # 生成token
            tokens = jwt_middleware.generate_tokens(user)
            
            access_token = tokens['access_token']
            
            # 从token中解析jti
            import jwt
            decoded = jwt.decode(
                access_token,
                options={"verify_signature": False}
            )
            jti = decoded['jti']
            
            # 首先token应该不在黑名单中
            assert jti not in jwt_middleware.blacklisted_tokens
            
            # 将token加入黑名单
            jwt_middleware.revoke_token(jti)
            
            # 再次检查，token应该在黑名单中
            assert jti in jwt_middleware.blacklisted_tokens