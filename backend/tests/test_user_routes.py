import pytest
import json
from datetime import datetime
from app.database import db
from app.models.user import User
# UserRole enum removed - using string values directly
from app.utils.auth import hash_password

class TestUserRoutes:
    """用户管理路由测试类"""
    
    def test_get_users_success(self, client, admin_user):
        """测试获取用户列表成功"""
        # 创建管理员认证头
        login_response = client.post('/api/auth/login', json={
            'email': admin_user.email,
            'password': 'SuperUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        response = client.get('/api/users', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'users' in data['data']
        assert 'pagination' in data['data']
        assert isinstance(data['data']['users'], list)
        assert data['data']['pagination']['total'] >= 1
    
    def test_get_users_with_filters(self, client, admin_user):
        """测试带过滤条件的用户列表"""
        login_response = client.post('/api/auth/login', json={
            'email': admin_user.email,
            'password': 'SuperUser123!'
        })
        assert login_response.status_code == 200
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # 测试角色过滤
        response = client.get('/api/users?role=admin&page=1&per_page=10', headers=headers)
        
        print(f"Response status: {response.status_code}")
        print(f"Response data: {response.get_json()}")
        print(f"Headers sent: {headers}")
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'users' in data['data']
        for user in data['data']['users']:
            assert user['role'] == 'admin'
    
    def test_get_users_unauthorized(self, client):
        """测试未授权访问用户列表"""
        import uuid
        
        # 使用注册API创建一个student用户
        unique_email = f'test_unauthorized_{uuid.uuid4().hex[:8]}@example.com'
        password = 'TestPass123!'
        
        # 注册用户
        register_response = client.post('/api/auth/register', json={
            'email': unique_email,
            'name': 'Test Unauthorized User',
            'password': password,
            'role': 'student'
        })
        
        assert register_response.status_code == 201, f"Registration failed: {register_response.get_json()}"
        
        # 从注册响应中获取token（注册后自动登录）
        token = register_response.get_json()['access_token']
        
        # 使用student角色的token访问用户列表（应该被拒绝）
        response = client.get('/api/users', headers={
            'Authorization': f'Bearer {token}'
        })
        
        assert response.status_code == 403
        data = response.get_json()
        assert data['success'] is False
        assert data['error'] == 'INSUFFICIENT_PERMISSIONS'
    
    def test_get_user_by_id_success(self, client, admin_user, test_user):
        """测试根据ID获取用户成功"""
        login_response = client.post('/api/auth/login', json={
            'email': admin_user.email,
            'password': 'SuperUser123!'
        })
        
        assert login_response.status_code == 200, f"Login failed: {login_response.get_json()}"
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        response = client.get(f'/api/users/{test_user.id}', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        user_info = data['data']['user']
        assert user_info['id'] == test_user.id
        assert user_info['email'] == test_user.email
        assert user_info['name'] == test_user.name
    
    def test_get_user_by_id_not_found(self, client, admin_user):
        """测试获取不存在的用户"""
        login_response = client.post('/api/auth/login', json={
            'email': admin_user.email,
            'password': 'SuperUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        response = client.get('/api/users/99999', headers=headers)
        
        assert response.status_code == 404
        data = response.get_json()
        assert data['success'] is False
        assert data['error'] == 'USER_NOT_FOUND'
    
    def test_create_user_success(self, client, admin_user):
        """测试创建用户成功"""
        login_response = client.post('/api/auth/login', json={
            'email': admin_user.email,
            'password': 'SuperUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        user_data = {
            'email': 'newuser@example.com',
            'name': 'New User',
            'password': 'NewUserPass123!',
            'role': 'student',
            'phone': '+1234567890'
        }
        
        response = client.post('/api/users', json=user_data, headers=headers)
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True
        user_info = data['data']['user']
        assert user_info['email'] == user_data['email']
        assert user_info['name'] == user_data['name']
        assert user_info['role'] == user_data['role']
        assert 'password_hash' not in user_info  # 确保密码不在响应中
        
        # 验证用户已创建
        with client.application.app_context():
            user = User.query.filter_by(email=user_data['email']).first()
            assert user is not None
            assert user.is_active is True
    
    def test_create_user_duplicate_email(self, client, admin_user, test_user):
        """测试创建重复邮箱用户"""
        login_response = client.post('/api/auth/login', json={
            'email': admin_user.email,
            'password': 'SuperUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        user_data = {
            'email': test_user.email,  # 使用已存在的邮箱
            'name': 'Duplicate User',
            'password': 'DuplicatePass123!',
            'role': 'student'
        }
        
        response = client.post('/api/users', json=user_data, headers=headers)
        
        assert response.status_code == 409
        data = response.get_json()
        assert data['success'] is False
        assert data['error'] == 'EMAIL_EXISTS'
    
    def test_create_user_invalid_role(self, client, admin_user):
        """测试创建用户时使用无效角色"""
        login_response = client.post('/api/auth/login', json={
            'email': admin_user.email,
            'password': 'SuperUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        user_data = {
            'email': 'invalidrole@example.com',
            'name': 'Invalid Role User',
            'password': 'InvalidRolePass123!',
            'role': 'invalid_role'
        }
        
        response = client.post('/api/users', json=user_data, headers=headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert data['error'] == 'INVALID_ROLE'
    
    def test_create_user_weak_password(self, client, admin_user):
        """测试创建用户时使用弱密码"""
        login_response = client.post('/api/auth/login', json={
            'email': admin_user.email,
            'password': 'SuperUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        user_data = {
            'email': 'weakpass@example.com',
            'name': 'Weak Pass User',
            'password': '123',
            'role': 'student'
        }
        
        response = client.post('/api/users', json=user_data, headers=headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert data['error'] == 'WEAK_PASSWORD'
    
    def test_update_user_success(self, client, admin_user, test_user):
        """测试更新用户成功"""
        login_response = client.post('/api/auth/login', json={
            'email': admin_user.email,
            'password': 'SuperUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        update_data = {
            'name': 'Updated Name',
            'phone': '+9876543210'
        }
        
        response = client.put(f'/api/users/{test_user.id}', json=update_data, headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['user']['name'] == update_data['name']
        assert data['data']['user']['phone'] == update_data['phone']
        
        # 验证数据库中的更新
        with client.application.app_context():
            updated_user = User.query.get(test_user.id)
            assert updated_user.name == update_data['name']
            assert updated_user.phone == update_data['phone']
    
    def test_update_user_not_found(self, client, admin_user):
        """测试更新不存在的用户"""
        login_response = client.post('/api/auth/login', json={
            'email': admin_user.email,
            'password': 'SuperUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        update_data = {'name': 'Updated Name'}
        
        response = client.put('/api/users/99999', json=update_data, headers=headers)
        
        assert response.status_code == 404
        data = response.get_json()
        assert data['success'] is False
        assert data['error'] == 'USER_NOT_FOUND'
    
    def test_delete_user_success(self, client, admin_user):
        """测试删除用户成功（软删除）"""
        # 先创建一个用户用于删除
        with client.application.app_context():
            user_to_delete = User(
                email='todelete@example.com',
                name='To Delete User',
                password_hash=hash_password('DeletePass123!'),
                role='student',
                created_at=datetime.utcnow()
            )
            db.session.add(user_to_delete)
            db.session.commit()
            user_id = user_to_delete.id
        
        login_response = client.post('/api/auth/login', json={
            'email': admin_user.email,
            'password': 'SuperUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        response = client.delete(f'/api/users/{user_id}', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'message' in data
        
        # 验证用户被软删除（is_active = False）
        with client.application.app_context():
            deleted_user = User.query.get(user_id)
            assert deleted_user is not None  # 用户仍存在
            assert deleted_user.is_active is False  # 但已被停用
    
    def test_delete_user_not_found(self, client, admin_user):
        """测试删除不存在的用户"""
        login_response = client.post('/api/auth/login', json={
            'email': admin_user.email,
            'password': 'SuperUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        response = client.delete('/api/users/99999', headers=headers)
        
        assert response.status_code == 404
        data = response.get_json()
        assert data['success'] is False
        assert data['error'] == 'USER_NOT_FOUND'
    
    def test_update_user_role_success(self, client, admin_user, test_user):
        """测试更新用户角色成功"""
        login_response = client.post('/api/auth/login', json={
            'email': admin_user.email,
            'password': 'SuperUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        role_data = {'role': 'teacher'}
        
        response = client.put(f'/api/users/{test_user.id}/role', json=role_data, headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['user']['role'] == 'teacher'
        
        # 验证数据库中的更新
        with client.application.app_context():
            updated_user = User.query.get(test_user.id)
            assert updated_user.role == 'teacher'
    
    def test_update_user_role_invalid(self, client, admin_user, test_user):
        """测试更新用户角色为无效角色"""
        login_response = client.post('/api/auth/login', json={
            'email': admin_user.email,
            'password': 'SuperUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        role_data = {'role': 'invalid_role'}
        
        response = client.put(f'/api/users/{test_user.id}/role', json=role_data, headers=headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert data['error'] == 'INVALID_ROLE'
    
    def test_update_user_status_success(self, client, admin_user, test_user):
        """测试更新用户状态成功"""
        login_response = client.post('/api/auth/login', json={
            'email': admin_user.email,
            'password': 'SuperUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        status_data = {'is_active': False}
        
        response = client.put(f'/api/users/{test_user.id}/status', json=status_data, headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['user']['is_active'] is False
        
        # 验证数据库中的更新
        with client.application.app_context():
            updated_user = User.query.get(test_user.id)
            assert updated_user.is_active is False
    
    def test_get_user_permissions_success(self, client, admin_user, test_user):
        """测试获取用户权限列表成功"""
        login_response = client.post('/api/auth/login', json={
            'email': admin_user.email,
            'password': 'SuperUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        response = client.get(f'/api/users/{test_user.id}/permissions', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'permissions' in data['data']
        assert isinstance(data['data']['permissions'], list)
    
    def test_get_available_roles_success(self, client, admin_user):
        """测试获取可用角色列表成功"""
        login_response = client.post('/api/auth/login', json={
            'email': admin_user.email,
            'password': 'SuperUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        response = client.get('/api/users/roles', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'roles' in data['data']
        assert isinstance(data['data']['roles'], list)
        assert len(data['data']['roles']) > 0
        
        # 验证包含预期的角色
        role_values = [role['value'] for role in data['data']['roles']]
        assert 'admin' in role_values
        assert 'teacher' in role_values
        assert 'student' in role_values
    
    def test_get_user_stats_success(self, client, admin_user):
        """测试获取用户统计信息成功"""
        login_response = client.post('/api/auth/login', json={
            'email': admin_user.email,
            'password': 'SuperUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        response = client.get('/api/users/stats', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'total_users' in data['data']
        assert 'active_users' in data['data']
        assert 'inactive_users' in data['data']
        assert 'role_distribution' in data['data']
        assert isinstance(data['data']['role_distribution'], dict)
    
    def test_validate_email_success(self, client):
        """测试邮箱格式验证成功"""
        response = client.post('/api/users/validate/email', json={
            'email': 'valid@example.com'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['is_valid_format'] is True
        assert data['data']['is_available'] is True
    
    def test_validate_email_invalid_format(self, client):
        """测试邮箱格式无效"""
        response = client.post('/api/users/validate/email', json={
            'email': 'invalid-email'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'INVALID_EMAIL_FORMAT' in data['error']
    
    def test_validate_email_already_exists(self, client, test_user):
        """测试邮箱已存在"""
        response = client.post('/api/users/validate/email', json={
            'email': test_user.email
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['is_valid_format'] is True
        assert data['data']['is_available'] is False
    
    def test_validate_password_success(self, client):
        """测试密码强度验证成功"""
        response = client.post('/api/users/validate/password', json={
            'password': 'StrongPass123!'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['is_valid'] is True
        assert data['data']['strength'] == 'Strong'
        assert data['data']['score'] == 100
    
    def test_validate_password_weak(self, client):
        """测试弱密码"""
        response = client.post('/api/users/validate/password', json={
            'password': '123'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['is_valid'] is False
        assert data['data']['strength'] == 'Weak'
        assert len(data['data']['suggestions']) > 0
    
    def test_validate_username_success(self, client):
        """测试用户名验证成功"""
        response = client.post('/api/users/validate/username', json={
            'name': 'validuser123'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['is_valid'] is True
        assert len(data['data']['suggestions']) == 0
    
    def test_validate_username_invalid_format(self, client):
        """测试用户名格式无效"""
        response = client.post('/api/users/validate/username', json={
            'name': 'a'  # 太短
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['is_valid'] is False
        assert len(data['data']['suggestions']) > 0
    
    def test_validate_phone_success(self, client):
        """测试手机号验证成功"""
        response = client.post('/api/users/validate/phone', json={
            'phone': '13812345678'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['is_valid'] is True
        assert len(data['data']['suggestions']) == 0
    
    def test_validate_phone_invalid_format(self, client):
        """测试手机号格式无效"""
        response = client.post('/api/users/validate/phone', json={
            'phone': '123'  # 格式无效
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['is_valid'] is False
        assert len(data['data']['suggestions']) > 0
    
    def test_validate_phone_already_exists(self, client, test_user):
        """测试手机号已存在"""
        # 先给测试用户设置手机号
        with client.application.app_context():
            user = User.query.get(test_user.id)
            user.phone = '13812345678'
            db.session.commit()
        
        response = client.post('/api/users/validate/phone', json={
            'phone': '13812345678',
            'check_uniqueness': True
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['is_valid'] is True
        assert data['data']['is_available'] is False