import pytest
import tempfile
import os
import uuid
from app import create_app
from app.database import db
from app.models.user import User
from app.utils.auth import hash_password
from datetime import datetime, timedelta

@pytest.fixture(scope='session')
def app():
    """创建测试应用实例"""
    # 创建临时数据库文件
    db_fd, db_path = tempfile.mkstemp()
    
    # 设置测试配置
    test_config = {
        'TESTING': True,
        'DEBUG': True,  # 启用调试模式
        'PROPAGATE_EXCEPTIONS': True,  # 传播异常
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'JWT_SECRET_KEY': 'jwt-secret-string',  # 与开发环境保持一致
        'JWT_ACCESS_TOKEN_EXPIRES': timedelta(hours=1),
        'JWT_REFRESH_TOKEN_EXPIRES': timedelta(days=1),
        'SECRET_KEY': 'dev-secret-key-change-in-production',  # 与开发环境保持一致
        'WTF_CSRF_ENABLED': False
    }
    
    # 创建应用
    app = create_app('testing')
    app.config.update(test_config)
    
    # 确保db绑定到应用
    app.db = db
    
    # 创建应用上下文
    with app.app_context():
        db.create_all()
        yield app
        
        # 清理
        db.drop_all()
    
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()

@pytest.fixture
def runner(app):
    """创建CLI运行器"""
    return app.test_cli_runner()

@pytest.fixture
def auth_headers(client):
    """创建认证用户并返回认证头部"""
    # 使用唯一的邮箱地址避免与其他测试冲突
    unique_email = f'auth_test_{uuid.uuid4().hex[:8]}@example.com'
    
    # 创建测试用户
    user = User(
        email=unique_email,
        name='Auth Test User',
        password_hash=hash_password('TestPass123!'),
        role='student',
        is_active=True,
        created_at=datetime.utcnow()
    )
    db.session.add(user)
    db.session.commit()
    
    # 登录获取token
    response = client.post('/api/auth/login', json={
        'email': unique_email,
        'password': 'TestPass123!'
    })
    
    assert response.status_code == 200, f"Login failed: {response.get_json()}"
    token = response.get_json()['access_token']
    
    return {
        'Authorization': f'Bearer {token}',
        'test_user_email': unique_email,  # 保存邮箱供测试使用
        'test_user_password': 'TestPass123!'  # 保存密码供测试使用
    }

@pytest.fixture
def test_user(client):
    """创建测试用户"""
    with client.application.app_context():
        # 使用唯一的邮箱地址避免与其他测试冲突
        unique_email = f'test_user_{uuid.uuid4().hex[:8]}@example.com'
        
        user = User(
            id=100,  # 使用固定的高ID避免与注册API创建的用户冲突
            email=unique_email,
            name='Test User',
            password_hash=hash_password('TestPass123!'),
            role='student',
            is_active=True,
            created_at=datetime.utcnow()
        )
        db.session.add(user)
        db.session.commit()
        # 刷新对象以确保所有属性都已加载
        db.session.refresh(user)
        # 创建一个简单的对象来存储用户信息，避免会话问题
        user_info = type('UserInfo', (), {
            'id': user.id,
            'email': user.email,
            'name': user.name,
            'role': user.role,
            'is_active': user.is_active
        })()
        return user_info

@pytest.fixture
def admin_user(client):
    """创建管理员用户"""
    with client.application.app_context():
        # 使用唯一的邮箱地址避免与其他测试冲突
        unique_email = f'admin_{uuid.uuid4().hex[:8]}@example.com'
        
        user = User(
            id=101,  # 使用固定的高ID避免与注册API创建的用户冲突
            email=unique_email,
            name='Admin User',
            password_hash=hash_password('SuperUser123!'),
            role='admin',
            is_active=True,
            created_at=datetime.utcnow()
        )
        db.session.add(user)
        db.session.commit()
        # 刷新对象以确保所有属性都已加载
        db.session.refresh(user)
        # 创建一个简单的对象来存储用户信息，避免会话问题
        user_info = type('UserInfo', (), {
            'id': user.id,
            'email': user.email,
            'name': user.name,
            'role': user.role,
            'is_active': user.is_active
        })()
        return user_info

@pytest.fixture
def teacher_user(client):
    """创建教师用户"""
    with client.application.app_context():
        # 使用唯一的邮箱地址避免与其他测试冲突
        unique_email = f'teacher_{uuid.uuid4().hex[:8]}@example.com'
        
        user = User(
            id=102,  # 使用固定的高ID避免与注册API创建的用户冲突
            email=unique_email,
            name='Teacher User',
            password_hash=hash_password('EduUser123!'),
            role='teacher',
            is_active=True,
            created_at=datetime.utcnow()
        )
        db.session.add(user)
        db.session.commit()
        # 刷新对象以确保所有属性都已加载
        db.session.refresh(user)
        # 创建一个简单的对象来存储用户信息，避免会话问题
        user_info = type('UserInfo', (), {
            'id': user.id,
            'email': user.email,
            'name': user.name,
            'role': user.role,
            'is_active': user.is_active
        })()
        return user_info

@pytest.fixture(autouse=True)
def clean_db(client):
    """每个测试前后清理数据库"""
    def _clean_database():
        """清理数据库的通用函数"""
        with client.application.app_context():
            try:
                # 关闭所有现有的数据库连接
                db.session.close()
                
                # 清理所有表数据，但保留表结构
                for table in reversed(db.metadata.sorted_tables):
                    db.session.execute(table.delete())
                db.session.commit()
                
                # 重置SQLite的自增ID计数器
                if 'sqlite' in str(db.engine.url):
                    try:
                        # 检查sqlite_sequence表是否存在
                        result = db.session.execute(db.text(
                            "SELECT name FROM sqlite_master WHERE type='table' AND name='sqlite_sequence'"
                        )).fetchone()
                        if result:
                            # 双重检查：确认表确实存在且可访问
                            try:
                                # 先尝试查询表结构，确保表可访问
                                db.session.execute(db.text("SELECT COUNT(*) FROM sqlite_sequence")).fetchone()
                                # 如果查询成功，则执行删除操作
                                db.session.execute(db.text("DELETE FROM sqlite_sequence"))
                                db.session.commit()
                            except Exception as inner_e:
                                # 如果表不可访问，记录警告但继续
                                print(f"Warning: sqlite_sequence table exists but not accessible: {inner_e}")
                                db.session.rollback()
                    except Exception as e:
                        # 如果sqlite_sequence操作失败，记录但不中断测试
                        print(f"Warning: Failed to reset sqlite_sequence: {e}")
                        db.session.rollback()
                
                # 清理JWT黑名单
                try:
                    from app.utils.jwt_middleware import jwt_middleware
                    jwt_middleware.blacklisted_tokens.clear()
                except Exception as e:
                    # 如果JWT黑名单清理失败，记录但不中断测试
                    print(f"Warning: Failed to clear JWT blacklist: {e}")
                
                # 清理SQLAlchemy的Identity Map缓存
                db.session.expunge_all()
                
                # 强制关闭会话并创建新的会话
                db.session.close()
                db.session.remove()
                
            except Exception as e:
                # 如果数据库清理失败，回滚并重新抛出异常
                db.session.rollback()
                raise e
    
    # 在测试前清理数据库
    _clean_database()
    
    yield
    
    # 在测试后也清理数据库
    _clean_database()