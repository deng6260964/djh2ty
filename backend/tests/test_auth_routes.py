import pytest
import json
from datetime import datetime, timedelta
from app.database import db
from app.models.user import User
from app.utils.auth import hash_password, verify_password
from flask_jwt_extended import decode_token

class TestAuthRoutes:
    """认证路由测试类"""
    
    def test_register_success(self, client):
        """测试用户注册成功"""
        response = client.post('/api/auth/register', json={
            'email': 'newuser@example.com',
            'name': 'New User',
            'password': 'StrongPass123!',
            'role': 'student'
        })
        
        assert response.status_code == 201
        data = response.get_json()
        assert 'access_token' in data
        assert 'refresh_token' in data
        assert data['user']['email'] == 'newuser@example.com'
        assert data['user']['name'] == 'New User'
        assert data['user']['role'] == 'student'
        
        # 验证用户已创建
        with client.application.app_context():
            user = User.query.filter_by(email='newuser@example.com').first()
            assert user is not None
            assert user.is_active is True
    
    def test_register_duplicate_email(self, client, test_user):
        """测试重复邮箱注册"""
        response = client.post('/api/auth/register', json={
            'email': test_user.email,
            'name': 'Another User',
            'password': 'StrongPass123!',
            'role': 'student'
        })
        
        assert response.status_code == 409
        data = response.get_json()
        assert data['code'] == 'EMAIL_EXISTS'
    
    def test_register_weak_password(self, client):
        """测试弱密码注册"""
        response = client.post('/api/auth/register', json={
            'email': 'weakpass@example.com',
            'name': 'Weak Pass User',
            'password': '123',
            'role': 'student'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['code'] == 'WEAK_PASSWORD'
        assert 'validation_errors' in data
    
    def test_register_missing_fields(self, client):
        """测试缺少必填字段"""
        response = client.post('/api/auth/register', json={
            'email': 'incomplete@example.com'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['code'] == 'MISSING_FIELDS'
    
    def test_login_success(self, client, test_user):
        """测试登录成功"""
        response = client.post('/api/auth/login', json={
            'email': test_user.email,
            'password': 'TestPass123!'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'access_token' in data
        assert 'refresh_token' in data
        assert data['user']['email'] == test_user.email
    
    def test_login_invalid_credentials(self, client, test_user):
        """测试无效凭据登录"""
        response = client.post('/api/auth/login', json={
            'email': test_user.email,
            'password': 'WrongPass123!'
        })
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['code'] == 'INVALID_CREDENTIALS'
    
    def test_login_nonexistent_user(self, client):
        """测试不存在用户登录"""
        response = client.post('/api/auth/login', json={
            'email': 'nonexistent@example.com',
            'password': 'TestPass123!'
        })
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['code'] == 'INVALID_CREDENTIALS'
    
    def test_login_inactive_user(self, client):
        """测试非活跃用户登录"""
        with client.application.app_context():
            user = User(
                email='inactive@example.com',
                name='Inactive User',
                password_hash=hash_password('TestPass123!'),
                role='student',
                is_active=False,
                created_at=datetime.utcnow()
            )
            db.session.add(user)
            db.session.commit()
        
        response = client.post('/api/auth/login', json={
            'email': 'inactive@example.com',
            'password': 'TestPass123!'
        })
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['code'] == 'ACCOUNT_INACTIVE'
    
    def test_refresh_token_success(self, client, test_user):
        """测试刷新token成功"""
        # 先登录获取refresh token
        login_response = client.post('/api/auth/login', json={
            'email': test_user.email,
            'password': 'TestPass123!'
        })
        
        assert login_response.status_code == 200, f"Login failed: {login_response.get_json()}"
        refresh_token = login_response.get_json()['refresh_token']
        
        # 使用refresh token获取新的access token
        response = client.post('/api/auth/refresh', 
                             json={},  # 使用JSON body而不是headers
                             headers={'Authorization': f'Bearer {refresh_token}'})
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'access_token' in data
    
    def test_get_current_user_success(self, client, auth_headers):
        """测试获取当前用户信息成功"""
        response = client.get('/api/auth/me', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['email'] == auth_headers['test_user_email']
        assert data['name'] == 'Auth Test User'
        assert 'active_sessions' in data
    
    def test_get_current_user_unauthorized(self, client):
        """测试未授权获取用户信息"""
        response = client.get('/api/auth/me')
        
        assert response.status_code == 401
    
    def test_logout_success(self, client, auth_headers):
        """测试登出成功"""
        response = client.post('/api/auth/logout', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'message' in data
    
    def test_logout_all_success(self, client, auth_headers):
        """测试登出所有设备成功"""
        response = client.post('/api/auth/logout-all', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'message' in data
    
    def test_get_user_sessions(self, client, auth_headers):
        """测试获取用户会话列表"""
        response = client.get('/api/auth/sessions', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'sessions' in data
        assert 'total_count' in data
        assert isinstance(data['sessions'], list)
    
    def test_change_password_success(self, client, auth_headers):
        """测试修改密码成功"""
        response = client.post('/api/auth/change-password', 
                             headers=auth_headers,
                             json={
                                 'current_password': auth_headers['test_user_password'],
                                 'new_password': 'NewStrongPass123!'
                             })
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'message' in data
    
    def test_change_password_wrong_current(self, client, auth_headers):
        """测试当前密码错误"""
        response = client.post('/api/auth/change-password', 
                             headers=auth_headers,
                             json={
                                 'current_password': 'WrongOldPass123!',
                                 'new_password': 'NewStrongPass123!'
                             })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['code'] == 'INVALID_CURRENT_PASSWORD'
    
    def test_change_password_weak_new(self, client, auth_headers):
        """测试新密码太弱"""
        response = client.post('/api/auth/change-password', 
                             headers=auth_headers,
                             json={
                                 'current_password': auth_headers['test_user_password'],
                                 'new_password': '123'
                             })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['code'] == 'WEAK_PASSWORD'
    
    def test_change_password_same_password(self, client, auth_headers):
        """测试新密码与当前密码相同"""
        response = client.post('/api/auth/change-password', 
                             headers=auth_headers,
                             json={
                                 'current_password': auth_headers['test_user_password'],
                                 'new_password': auth_headers['test_user_password']
                             })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['code'] == 'SAME_PASSWORD'
    
    def test_validate_token_success(self, client, auth_headers):
        """测试验证token成功"""
        response = client.post('/api/auth/validate-token', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['valid'] is True
    
    def test_validate_token_invalid(self, client):
        """测试验证无效token"""
        response = client.post('/api/auth/validate-token', 
                             headers={'Authorization': 'Bearer invalid_token'})
        
        assert response.status_code == 401  # JWT decode error