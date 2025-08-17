import pytest
import json
import tempfile
import os
from datetime import datetime
from app.database import db
from app.models.user import User
from app.models.file import File
from app.utils.auth import hash_password
import uuid

class TestFileRoutes:
    """文件管理路由测试类"""
    
    @pytest.fixture
    def setup_user(self, client):
        """设置测试用户"""
        with client.application.app_context():
            # 创建测试用户
            user_email = f'fileuser_{uuid.uuid4().hex[:8]}@example.com'
            user = User(
                email=user_email,
                name='File Test User',
                password_hash=hash_password('FilePass123!'),
                role='student',
                is_active=True,
                created_at=datetime.utcnow()
            )
            db.session.add(user)
            db.session.commit()
            
            # 获取认证token
            login_response = client.post('/api/auth/login', json={
                'email': user_email,
                'password': 'FilePass123!'
            })
            token = login_response.get_json()['access_token']
            
            return {
                'user': user,
                'headers': {'Authorization': f'Bearer {token}'}
            }
    
    def test_upload_file_success(self, client, setup_user):
        """测试文件上传成功"""
        setup = setup_user
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write('Test file content for upload')
            temp_file_path = f.name
        
        try:
            with open(temp_file_path, 'rb') as f:
                response = client.post('/api/files/upload', 
                    data={
                        'file': (f, 'test_upload.txt'),
                        'file_category': 'assignment_attachment'
                    },
                    headers=setup['headers']
                )
            
            assert response.status_code == 201
            data = response.get_json()
            assert data['success'] is True
            file_info = data['data']['file']
            assert file_info['filename'] == 'test_upload.txt'
            assert file_info['file_category'] == 'assignment_attachment'
            assert file_info['uploader_id'] == setup['user'].id
            
        finally:
            # 清理临时文件
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
    
    def test_upload_file_invalid_type(self, client, setup_user):
        """测试上传不支持的文件类型"""
        setup = setup_user
        
        # 创建不支持的文件类型
        with tempfile.NamedTemporaryFile(mode='w', suffix='.exe', delete=False) as f:
            f.write('Invalid file content')
            temp_file_path = f.name
        
        try:
            with open(temp_file_path, 'rb') as f:
                response = client.post('/api/files/upload', 
                    data={
                        'file': (f, 'malicious.exe'),
                        'file_category': 'assignment_attachment'
                    },
                    headers=setup['headers']
                )
            
            assert response.status_code == 400
            data = response.get_json()
            assert data['success'] is False
            assert data['error'] == 'INVALID_FILE_TYPE'
            
        finally:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
    
    def test_upload_file_too_large(self, client, setup_user):
        """测试上传文件过大"""
        setup = setup_user
        
        # 创建大文件（模拟）
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            # 写入大量内容模拟大文件
            large_content = 'x' * (60 * 1024 * 1024)  # 60MB
            f.write(large_content)
            temp_file_path = f.name
        
        try:
            with open(temp_file_path, 'rb') as f:
                response = client.post('/api/files/upload', 
                    data={
                        'file': (f, 'large_file.txt'),
                        'file_category': 'assignment_attachment'
                    },
                    headers=setup['headers']
                )
            
            # 应该返回413或400错误
            assert response.status_code in [400, 413]
            
        finally:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
    
    def test_get_file_info_success(self, client, setup_user):
        """测试获取文件信息成功"""
        setup = setup_user
        
        # 先上传文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write('Test file for info retrieval')
            temp_file_path = f.name
        
        try:
            with open(temp_file_path, 'rb') as f:
                upload_response = client.post('/api/files/upload', 
                    data={
                        'file': (f, 'info_test.txt'),
                        'file_category': 'submission_file'
                    },
                    headers=setup['headers']
                )
            
            file_id = upload_response.get_json()['data']['file']['id']
            
            # 获取文件信息
            response = client.get(f'/api/files/{file_id}', headers=setup['headers'])
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            file_info = data['data']['file']
            assert file_info['id'] == file_id
            assert file_info['filename'] == 'info_test.txt'
            
        finally:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
    
    def test_get_file_info_not_found(self, client, setup_user):
        """测试获取不存在文件的信息"""
        setup = setup_user
        
        response = client.get('/api/files/99999', headers=setup['headers'])
        
        assert response.status_code == 404
        data = response.get_json()
        assert data['success'] is False
        assert data['error'] == 'FILE_NOT_FOUND'
    
    def test_get_file_info_unauthorized(self, client, setup_user):
        """测试获取其他用户文件信息失败"""
        setup = setup_user
        
        # 创建另一个用户的文件
        with client.application.app_context():
            other_user = User(
                email=f'other_{uuid.uuid4().hex[:8]}@example.com',
                name='Other User',
                password_hash=hash_password('OtherPass123!'),
                role='student',
                is_active=True,
                created_at=datetime.utcnow()
            )
            db.session.add(other_user)
            db.session.commit()
            
            other_file = File(
                filename='other_file.txt',
                stored_filename='stored_other_file.txt',
                file_path='/uploads/stored_other_file.txt',
                file_size=1024,
                file_type='text/plain',
                file_category='assignment_attachment',
                uploader_id=other_user.id,
                uploaded_at=datetime.utcnow()
            )
            db.session.add(other_file)
            db.session.commit()
            other_file_id = other_file.id
        
        response = client.get(f'/api/files/{other_file_id}', headers=setup['headers'])
        
        assert response.status_code == 403
        data = response.get_json()
        assert data['success'] is False
        assert data['error'] == 'PERMISSION_DENIED'
    
    def test_download_file_success(self, client, setup_user):
        """测试文件下载成功"""
        setup = setup_user
        
        # 先上传文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write('Test file for download')
            temp_file_path = f.name
        
        try:
            with open(temp_file_path, 'rb') as f:
                upload_response = client.post('/api/files/upload', 
                    data={
                        'file': (f, 'download_test.txt'),
                        'file_category': 'submission_file'
                    },
                    headers=setup['headers']
                )
            
            file_id = upload_response.get_json()['data']['file']['id']
            
            # 下载文件
            response = client.get(f'/api/files/{file_id}/download', headers=setup['headers'])
            
            assert response.status_code == 200
            assert response.headers['Content-Disposition'].startswith('attachment')
            
        finally:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
    
    def test_delete_file_success(self, client, setup_user):
        """测试删除文件成功"""
        setup = setup_user
        
        # 先上传文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write('Test file for deletion')
            temp_file_path = f.name
        
        try:
            with open(temp_file_path, 'rb') as f:
                upload_response = client.post('/api/files/upload', 
                    data={
                        'file': (f, 'delete_test.txt'),
                        'file_category': 'submission_file'
                    },
                    headers=setup['headers']
                )
            
            file_id = upload_response.get_json()['data']['file']['id']
            
            # 删除文件
            response = client.delete(f'/api/files/{file_id}', headers=setup['headers'])
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            
            # 验证文件已删除
            with client.application.app_context():
                deleted_file = File.query.get(file_id)
                assert deleted_file is None
            
        finally:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
    
    def test_delete_file_unauthorized(self, client, setup_user):
        """测试删除其他用户文件失败"""
        setup = setup_user
        
        # 创建另一个用户的文件
        with client.application.app_context():
            other_user = User(
                email=f'delete_other_{uuid.uuid4().hex[:8]}@example.com',
                name='Delete Other User',
                password_hash=hash_password('DeletePass123!'),
                role='student',
                is_active=True,
                created_at=datetime.utcnow()
            )
            db.session.add(other_user)
            db.session.commit()
            
            other_file = File(
                filename='other_delete_file.txt',
                stored_filename='stored_other_delete_file.txt',
                file_path='/uploads/stored_other_delete_file.txt',
                file_size=1024,
                file_type='text/plain',
                file_category='assignment_attachment',
                uploader_id=other_user.id,
                uploaded_at=datetime.utcnow()
            )
            db.session.add(other_file)
            db.session.commit()
            other_file_id = other_file.id
        
        response = client.delete(f'/api/files/{other_file_id}', headers=setup['headers'])
        
        assert response.status_code == 403
        data = response.get_json()
        assert data['success'] is False
        assert data['error'] == 'PERMISSION_DENIED'
    
    def test_get_my_files_list(self, client, setup_user):
        """测试获取用户文件列表"""
        setup = setup_user
        
        # 上传多个文件
        file_ids = []
        for i in range(3):
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(f'Test file content {i+1}')
                temp_file_path = f.name
            
            try:
                with open(temp_file_path, 'rb') as f:
                    upload_response = client.post('/api/files/upload', 
                        data={
                            'file': (f, f'list_test_{i+1}.txt'),
                            'file_category': 'submission_file'
                        },
                        headers=setup['headers']
                    )
                
                file_ids.append(upload_response.get_json()['data']['file']['id'])
                
            finally:
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
        
        # 获取文件列表
        response = client.get('/api/files/my-files', headers=setup['headers'])
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        files = data['data']['files']
        assert len(files) >= 3
        
        # 验证文件属于当前用户
        for file_info in files:
            assert file_info['uploader_id'] == setup['user'].id
    
    def test_get_my_files_with_category_filter(self, client, setup_user):
        """测试按类别过滤用户文件列表"""
        setup = setup_user
        
        # 上传不同类别的文件
        categories = ['assignment_attachment', 'submission_file']
        for i, category in enumerate(categories):
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(f'Test file for category {category}')
                temp_file_path = f.name
            
            try:
                with open(temp_file_path, 'rb') as f:
                    client.post('/api/files/upload', 
                        data={
                            'file': (f, f'category_test_{category}.txt'),
                            'file_category': category
                        },
                        headers=setup['headers']
                    )
                
            finally:
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
        
        # 按类别过滤
        response = client.get('/api/files/my-files?category=assignment_attachment', headers=setup['headers'])
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        files = data['data']['files']
        
        # 验证所有文件都是指定类别
        for file_info in files:
            assert file_info['file_category'] == 'assignment_attachment'