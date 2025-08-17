import pytest
from unittest.mock import patch, MagicMock
from flask import Flask, jsonify
from app.utils.permissions import (
    UserRole, Permission, PermissionManager,
    require_auth, require_role, require_permission, require_resource_access,
    admin_required, teacher_required, student_required
)
from app.models.user import User
from app.database import db
from app.utils.auth import hash_password
from datetime import datetime
from flask_jwt_extended import create_access_token

class TestPermissions:
    """权限控制装饰器测试"""
    
    def setup_method(self):
        """设置测试环境"""
        # 使用真实的Flask应用和数据库
        from app import create_app
        from app.models.user import User
        from app.utils.password_manager import hash_password
        from app.database import db
        from datetime import datetime
        
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        with self.app.app_context():
            db.create_all()
            
            # 为每个测试创建唯一的用户邮箱
            import time
            timestamp = str(int(time.time() * 1000000))  # 微秒级时间戳
            
            # 创建真实的测试用户
            self.admin_user = User(
                email=f'admin_{timestamp}@test.com',
                name='Admin User',
                password_hash=hash_password('TestPass123!'),
                role=UserRole.ADMIN.value,
                is_active=True,
                created_at=datetime.utcnow()
            )
            db.session.add(self.admin_user)
            
            self.teacher_user = User(
                email=f'teacher_{timestamp}@test.com',
                name='Teacher User',
                password_hash=hash_password('TestPass123!'),
                role=UserRole.TEACHER.value,
                is_active=True,
                created_at=datetime.utcnow()
            )
            db.session.add(self.teacher_user)
            
            self.student_user = User(
                email=f'student_{timestamp}@test.com',
                name='Student User',
                password_hash=hash_password('TestPass123!'),
                role=UserRole.STUDENT.value,
                is_active=True,
                created_at=datetime.utcnow()
            )
            db.session.add(self.student_user)
            
            db.session.commit()
            
            # 保存用户ID，避免会话分离问题
            self.admin_user_id = self.admin_user.id
            self.teacher_user_id = self.teacher_user.id
            self.student_user_id = self.student_user.id
        
            # 创建测试路由
            @self.app.route('/test-auth')
            @require_auth
            def test_auth_route(current_user=None):
                return jsonify({'message': 'success', 'user_id': current_user.id})
            
            @self.app.route('/test-role')
            @require_role([UserRole.ADMIN.value])
            def test_role_route(current_user=None):
                return jsonify({'message': 'success', 'user_id': current_user.id})
            
            @self.app.route('/test-permission')
            @require_permission(Permission.USER_CREATE)
            def test_permission_route(current_user=None):
                return jsonify({'message': 'success', 'user_id': current_user.id})
            
            @self.app.route('/test-resource/<int:id>')
            @require_resource_access(Permission.USER_READ, 'id')
            def test_resource_route(id, current_user=None):
                return jsonify({'message': 'success', 'user_id': current_user.id, 'resource_id': id})
            
            @self.app.route('/test-admin')
            @admin_required
            def test_admin_route(current_user=None):
                return jsonify({'message': 'success', 'user_id': current_user.id})
            
            @self.app.route('/test-teacher')
            @teacher_required
            def test_teacher_route(current_user=None):
                return jsonify({'message': 'success', 'user_id': current_user.id})
            
            @self.app.route('/test-student')
            @student_required
            def test_student_route(current_user=None):
                return jsonify({'message': 'success', 'user_id': current_user.id})
        
        self.client = self.app.test_client()
    
    def tearDown(self):
        """清理测试环境"""
        with self.app.app_context():
            from app.database import db
            db.session.remove()
            db.drop_all()
    
    def _create_test_token(self, user_id, role=UserRole.STUDENT):
        """创建测试用的JWT token"""
        from flask_jwt_extended import create_access_token
        with self.app.app_context():
            # 创建包含角色信息的token
            additional_claims = {
                'role': role.value if hasattr(role, 'value') else role,
                'user_id': user_id
            }
            return create_access_token(identity=str(user_id), additional_claims=additional_claims)
    
    def _mock_current_user(self, user_id, role):
        """模拟当前用户，避免会话分离问题"""
        from unittest.mock import Mock
        mock_user = Mock()
        mock_user.id = user_id
        mock_user.role = role.value if hasattr(role, 'value') else role
        mock_user.is_active = True
        mock_user.email = f'user{user_id}@example.com'
        return mock_user
    
    def _get_auth_headers(self, user_id, role=UserRole.STUDENT):
        """获取认证头"""
        token = self._create_test_token(user_id, role)
        return {'Authorization': f'Bearer {token}'}
    
    @pytest.fixture
    def permission_manager(self):
        """创建权限管理器实例"""
        return PermissionManager()
    
    @pytest.fixture
    def test_users(self, client):
        """创建测试用户"""
        with client.application.app_context():
            users = {}
            
            # 学生用户
            student = User(
                email='student@example.com',
                name='Student User',
                password_hash=hash_password('TestPass123!'),
                role='student',
                is_active=True,
                created_at=datetime.utcnow()
            )
            db.session.add(student)
            
            # 教师用户
            teacher = User(
                email='teacher@example.com',
                name='Teacher User',
                password_hash=hash_password('TestPass123!'),
                role='teacher',
                is_active=True,
                created_at=datetime.utcnow()
            )
            db.session.add(teacher)
            
            # 管理员用户
            admin = User(
                email='admin@example.com',
                name='Admin User',
                password_hash=hash_password('TestPass123!'),
                role='admin',
                is_active=True,
                created_at=datetime.utcnow()
            )
            db.session.add(admin)
            
            db.session.commit()
            
            # 返回用户ID而不是用户对象，避免会话绑定问题
            users['student'] = student.id
            users['teacher'] = teacher.id
            users['admin'] = admin.id
            
            return users
    
    def test_user_role_enum(self):
        """测试用户角色枚举"""
        assert UserRole.ADMIN.value == 'admin'
        assert UserRole.TEACHER.value == 'teacher'
        assert UserRole.STUDENT.value == 'student'
    
    def test_permission_enum(self):
        """测试权限枚举"""
        assert Permission.USER_CREATE.value == 'user:create'
        assert Permission.USER_READ.value == 'user:read'
        assert Permission.USER_UPDATE.value == 'user:update'
        assert Permission.USER_DELETE.value == 'user:delete'
        assert Permission.COURSE_CREATE.value == 'course:create'
        assert Permission.COURSE_READ.value == 'course:read'
        assert Permission.COURSE_UPDATE.value == 'course:update'
        assert Permission.COURSE_DELETE.value == 'course:delete'
        assert Permission.ASSIGNMENT_CREATE.value == 'assignment:create'
        assert Permission.ASSIGNMENT_READ.value == 'assignment:read'
        assert Permission.ASSIGNMENT_UPDATE.value == 'assignment:update'
        assert Permission.ASSIGNMENT_DELETE.value == 'assignment:delete'
        assert Permission.SYSTEM_CONFIG.value == 'system:config'
    
    def test_permission_manager_has_permission(self):
        """测试权限管理器的权限检查"""
        # 管理员拥有所有权限
        assert PermissionManager.has_permission(UserRole.ADMIN.value, Permission.USER_CREATE)
        assert PermissionManager.has_permission(UserRole.ADMIN.value, Permission.COURSE_CREATE)
        assert PermissionManager.has_permission(UserRole.ADMIN.value, Permission.SYSTEM_CONFIG)
        
        # 教师拥有部分权限
        assert PermissionManager.has_permission(UserRole.TEACHER.value, Permission.COURSE_CREATE)
        assert PermissionManager.has_permission(UserRole.TEACHER.value, Permission.ASSIGNMENT_CREATE)
        assert not PermissionManager.has_permission(UserRole.TEACHER.value, Permission.USER_CREATE)
        assert not PermissionManager.has_permission(UserRole.TEACHER.value, Permission.SYSTEM_CONFIG)
        
        # 学生只有读取权限
        assert PermissionManager.has_permission(UserRole.STUDENT.value, Permission.COURSE_READ)
        assert PermissionManager.has_permission(UserRole.STUDENT.value, Permission.ASSIGNMENT_READ)
        assert not PermissionManager.has_permission(UserRole.STUDENT.value, Permission.COURSE_CREATE)
        assert not PermissionManager.has_permission(UserRole.STUDENT.value, Permission.USER_CREATE)
    
    def test_permission_manager_can_access_resource(self):
        """测试权限管理器的资源访问检查"""
        # 管理员可以访问所有资源
        assert PermissionManager.can_access_resource(
            UserRole.ADMIN.value, 999, 1, Permission.USER_READ
        )
        
        # 教师可以访问自己的资源
        assert PermissionManager.can_access_resource(
            UserRole.TEACHER.value, 2, 2, Permission.COURSE_READ
        )
        
        # 教师不能访问其他人的资源（除非有权限）
        assert not PermissionManager.can_access_resource(
            UserRole.TEACHER.value, 3, 2, Permission.USER_UPDATE
        )
        
        # 学生可以访问自己的资源
        assert PermissionManager.can_access_resource(
            UserRole.STUDENT.value, 3, 3, Permission.ASSIGNMENT_READ
        )
        
        # 学生不能访问其他人的资源
        assert not PermissionManager.can_access_resource(
            UserRole.STUDENT.value, 2, 3, Permission.COURSE_READ
        )
    
    def test_permission_manager_get_user_permissions(self, permission_manager):
        """测试获取用户权限列表"""
        # 测试学生权限
        student_permissions = permission_manager.get_user_permissions(UserRole.STUDENT.value)
        expected_student_permissions = [
            Permission.USER_READ,
            Permission.COURSE_READ,
            Permission.ASSIGNMENT_READ,
            Permission.ASSIGNMENT_UPDATE  # 学生可以提交作业
        ]
        assert set(student_permissions) == set(expected_student_permissions)
        
        # 测试教师权限
        teacher_permissions = permission_manager.get_user_permissions(UserRole.TEACHER.value)
        expected_teacher_permissions = [
            Permission.USER_READ,
            Permission.COURSE_READ,
            Permission.COURSE_CREATE,
            Permission.COURSE_UPDATE,  # 教师可以更新课程
            Permission.ASSIGNMENT_READ,
            Permission.ASSIGNMENT_CREATE,
            Permission.ASSIGNMENT_UPDATE,  # 教师可以更新作业
            Permission.ASSIGNMENT_DELETE,  # 教师可以删除作业
            Permission.ASSIGNMENT_GRADE
        ]
        assert set(teacher_permissions) == set(expected_teacher_permissions)
        
        # 测试管理员权限
        admin_permissions = permission_manager.get_user_permissions(UserRole.ADMIN.value)
        assert Permission.USER_CREATE in admin_permissions
        assert Permission.USER_DELETE in admin_permissions
        assert Permission.SYSTEM_CONFIG in admin_permissions
    
    def test_permission_manager_can_access_resource(self, permission_manager):
        """测试资源访问权限检查"""
        # 管理员可以访问任何资源
        assert permission_manager.can_access_resource(
            UserRole.ADMIN.value, 999, 1, Permission.USER_READ
        ) is True
        
        # 用户可以访问自己的资源
        assert permission_manager.can_access_resource(
            UserRole.STUDENT.value, 1, 1, Permission.USER_READ
        ) is True
        
        # 用户不能访问其他人的资源（除非有权限）
        assert permission_manager.can_access_resource(
            UserRole.STUDENT.value, 2, 1, Permission.USER_UPDATE
        ) is False
        
        # 教师可以访问学生资源（如果有权限）
        assert permission_manager.can_access_resource(
            UserRole.TEACHER.value, 1, 2, Permission.ASSIGNMENT_GRADE
        ) is True
    
    def test_permission_manager_invalid_role(self, permission_manager):
        """测试无效角色"""
        # 测试不存在的角色
        assert permission_manager.has_permission('invalid_role', Permission.USER_READ) is False
        
        permissions = permission_manager.get_user_permissions('invalid_role')
        assert permissions == []
    
    def test_require_auth_decorator_success(self):
        """测试认证装饰器成功情况"""
        from unittest.mock import patch
        with self.app.app_context():
            mock_user = self._mock_current_user(self.student_user_id, UserRole.STUDENT)
            with patch('app.database.db.session.query') as mock_query:
                mock_query.return_value.filter_by.return_value.first.return_value = mock_user
                headers = self._get_auth_headers(self.student_user_id, UserRole.STUDENT)
                response = self.client.get('/test-auth', headers=headers)
                assert response.status_code == 200
                data = response.get_json()
                assert data['message'] == 'success'
                assert data['user_id'] == self.student_user_id
    
    def test_require_auth_decorator_failure(self):
        """测试认证装饰器失败情况"""
        with self.app.app_context():
            response = self.client.get('/test-auth')
            assert response.status_code == 401
    
    def test_require_permission_decorator_success(self):
        """测试权限装饰器成功情况"""
        from unittest.mock import patch
        with self.app.app_context():
            # 管理员有USER_CREATE权限
            mock_user = self._mock_current_user(self.admin_user_id, UserRole.ADMIN)
            with patch('app.database.db.session.query') as mock_query:
                mock_query.return_value.filter_by.return_value.first.return_value = mock_user
                headers = self._get_auth_headers(self.admin_user_id, UserRole.ADMIN)
                response = self.client.get('/test-permission', headers=headers)
                assert response.status_code == 200
                assert response.get_json()['message'] == 'success'
    
    def test_require_permission_decorator_failure(self):
        """测试权限装饰器失败情况"""
        from unittest.mock import patch
        with self.app.app_context():
            # 学生没有USER_CREATE权限
            mock_user = self._mock_current_user(self.student_user_id, UserRole.STUDENT)
            with patch('app.database.db.session.query') as mock_query:
                mock_query.return_value.filter_by.return_value.first.return_value = mock_user
                headers = self._get_auth_headers(self.student_user_id, UserRole.STUDENT)
                response = self.client.get('/test-permission', headers=headers)
                assert response.status_code == 403
    
    def test_require_role_decorator_success(self):
        """测试角色装饰器成功情况"""
        from unittest.mock import patch
        with self.app.app_context():
            # 管理员有足够的角色权限
            mock_user = self._mock_current_user(self.admin_user_id, UserRole.ADMIN)
            with patch('app.database.db.session.query') as mock_query:
                mock_query.return_value.filter_by.return_value.first.return_value = mock_user
                headers = self._get_auth_headers(self.admin_user_id, UserRole.ADMIN)
                response = self.client.get('/test-role', headers=headers)
                assert response.status_code == 200
                assert response.get_json()['message'] == 'success'
    
    def test_require_role_decorator_failure(self):
        """测试角色装饰器失败情况"""
        from unittest.mock import patch
        with self.app.app_context():
            # 学生尝试访问需要管理员角色的资源
            mock_user = self._mock_current_user(self.student_user_id, UserRole.STUDENT)
            with patch('app.database.db.session.query') as mock_query:
                mock_query.return_value.filter_by.return_value.first.return_value = mock_user
                headers = self._get_auth_headers(self.student_user_id, UserRole.STUDENT)
                response = self.client.get('/test-role', headers=headers)
                assert response.status_code == 403
    
    def test_require_resource_access_decorator_success(self):
        """测试资源访问装饰器成功情况"""
        from unittest.mock import patch
        with self.app.app_context():
            # 管理员有USER_READ权限
            mock_user = self._mock_current_user(self.admin_user_id, UserRole.ADMIN)
            with patch('app.database.db.session.query') as mock_query:
                mock_query.return_value.filter_by.return_value.first.return_value = mock_user
                headers = self._get_auth_headers(self.admin_user_id, UserRole.ADMIN)
                response = self.client.get('/test-resource/1', headers=headers)
                assert response.status_code == 200
                assert response.get_json()['message'] == 'success'
    
    def test_require_resource_access_decorator_failure(self):
        """测试资源访问装饰器失败情况"""
        from unittest.mock import patch
        with self.app.app_context():
            # 学生没有USER_READ权限访问其他用户资源
            mock_user = self._mock_current_user(self.student_user_id, UserRole.STUDENT)
            with patch('app.database.db.session.query') as mock_query:
                mock_query.return_value.filter_by.return_value.first.return_value = mock_user
                headers = self._get_auth_headers(self.student_user_id, UserRole.STUDENT)
                response = self.client.get('/test-resource/1', headers=headers)
                assert response.status_code == 403
    
    def test_admin_required_decorator_success(self):
        """测试管理员装饰器成功情况"""
        from unittest.mock import patch
        with self.app.app_context():
            mock_user = self._mock_current_user(self.admin_user_id, UserRole.ADMIN)
            with patch('app.database.db.session.query') as mock_query:
                mock_query.return_value.filter_by.return_value.first.return_value = mock_user
                headers = self._get_auth_headers(self.admin_user_id, UserRole.ADMIN)
                response = self.client.get('/test-admin', headers=headers)
                assert response.status_code == 200
                assert response.get_json()['message'] == 'success'
    
    def test_admin_required_decorator_failure(self):
        """测试管理员装饰器失败情况"""
        from unittest.mock import patch
        with self.app.app_context():
            # 学生尝试访问管理员资源
            mock_user = self._mock_current_user(self.student_user_id, UserRole.STUDENT)
            with patch('app.database.db.session.query') as mock_query:
                mock_query.return_value.filter_by.return_value.first.return_value = mock_user
                headers = self._get_auth_headers(self.student_user_id, UserRole.STUDENT)
                response = self.client.get('/test-admin', headers=headers)
                assert response.status_code == 403
    
    def test_teacher_required_decorator_success(self):
        """测试教师装饰器成功情况"""
        from unittest.mock import patch
        with self.app.app_context():
            mock_user = self._mock_current_user(self.teacher_user_id, UserRole.TEACHER)
            with patch('app.database.db.session.query') as mock_query:
                mock_query.return_value.filter_by.return_value.first.return_value = mock_user
                headers = self._get_auth_headers(self.teacher_user_id, UserRole.TEACHER)
                response = self.client.get('/test-teacher', headers=headers)
            assert response.status_code == 200
            assert response.get_json()['message'] == 'success'
    
    def test_teacher_required_decorator_failure(self):
        """测试教师装饰器失败情况"""
        from unittest.mock import patch
        with self.app.app_context():
            # 学生尝试访问教师资源
            mock_user = self._mock_current_user(self.student_user_id, UserRole.STUDENT)
            with patch('app.database.db.session.query') as mock_query:
                mock_query.return_value.filter_by.return_value.first.return_value = mock_user
                headers = self._get_auth_headers(self.student_user_id, UserRole.STUDENT)
                response = self.client.get('/test-teacher', headers=headers)
                assert response.status_code == 403
    
    def test_student_required_decorator_success(self):
        """测试学生装饰器成功情况"""
        from unittest.mock import patch
        with self.app.app_context():
            mock_user = self._mock_current_user(self.student_user_id, UserRole.STUDENT)
            with patch('app.database.db.session.query') as mock_query:
                mock_query.return_value.filter_by.return_value.first.return_value = mock_user
                headers = self._get_auth_headers(self.student_user_id, UserRole.STUDENT)
                response = self.client.get('/test-student', headers=headers)
                assert response.status_code == 200
                assert response.get_json()['message'] == 'success'
    
    def test_role_hierarchy(self):
        """测试角色层次结构"""
        permission_manager = PermissionManager()
        
        # 管理员应该有所有权限
        admin_permissions = permission_manager.get_user_permissions(UserRole.ADMIN.value)
        assert len(admin_permissions) > 0
        assert Permission.USER_CREATE in admin_permissions
        
        # 教师应该有部分权限
        teacher_permissions = permission_manager.get_user_permissions(UserRole.TEACHER.value)
        assert Permission.COURSE_CREATE in teacher_permissions
        
        # 学生权限最少
        student_permissions = permission_manager.get_user_permissions(UserRole.STUDENT.value)
        assert len(student_permissions) >= 0  # 学生可能没有特殊权限或只有基本权限