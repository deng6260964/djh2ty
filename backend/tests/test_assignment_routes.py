import pytest
import json
import tempfile
import os
from datetime import datetime, timedelta
from app.database import db
from app.models.user import User
from app.models.course import Course, CourseEnrollment
from app.models.homework import Homework
from app.models.homework_submission import HomeworkSubmission
from app.models.file import File
from app.utils.auth import hash_password
import uuid

class TestAssignmentRoutes:
    """作业管理路由测试类"""
    
    @pytest.fixture
    def setup_course_and_users(self, client):
        """设置测试课程和用户"""
        with client.application.app_context():
            # 创建教师用户
            teacher_email = f'teacher_{uuid.uuid4().hex[:8]}@example.com'
            # 直接使用bcrypt进行密码哈希，避免密码强度验证
            import bcrypt
            teacher_password_hash = bcrypt.hashpw('TeacherPass123!'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            teacher = User(
                email=teacher_email,
                name='Test Teacher',
                password_hash=teacher_password_hash,
                role='teacher',
                is_active=True,
                created_at=datetime.utcnow()
            )
            db.session.add(teacher)

            # 创建学生用户
            student_email = f'student_{uuid.uuid4().hex[:8]}@example.com'
            student_password_hash = bcrypt.hashpw('StudentPass123!'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            student = User(
                email=student_email,
                name='Test Student',
                password_hash=student_password_hash,
                role='student',
                is_active=True,
                created_at=datetime.utcnow()
            )
            db.session.add(student)
            
            # 先提交用户数据以获取ID
            db.session.commit()
            
            # 重新获取用户对象以避免DetachedInstanceError
            teacher = db.session.get(User, teacher.id)
            student = db.session.get(User, student.id)
            
            # 创建课程
            course = Course(
                name='Test Course',
                description='Test Course Description',
                course_type='one_to_many',
                max_students=30,
                teacher_id=teacher.id,
                is_active=True,
                created_at=datetime.utcnow()
            )
            db.session.add(course)
            db.session.commit()  # 先提交课程以获取ID
            
            # 重新获取course对象以避免DetachedInstanceError
            course = db.session.get(Course, course.id)
            
            # 学生选课
            enrollment = CourseEnrollment(
                student_id=student.id,
                course_id=course.id,
                enrolled_at=datetime.utcnow()
            )
            db.session.add(enrollment)
            
            db.session.commit()
            
            # 获取认证token
            teacher_login = client.post('/api/auth/login', json={
                'email': teacher_email,
                'password': 'TeacherPass123!'
            })
            assert teacher_login.status_code == 200, f"Teacher login failed: {teacher_login.get_json()}"
            teacher_data = teacher_login.get_json()
            teacher_token = teacher_data['access_token']
            
            student_login = client.post('/api/auth/login', json={
                'email': student_email,
                'password': 'StudentPass123!'
            })
            assert student_login.status_code == 200, f"Student login failed: {student_login.get_json()}"
            student_data = student_login.get_json()
            student_token = student_data['access_token']
            
            return {
                'teacher_id': teacher.id,
                'student_id': student.id,
                'course_id': course.id,
                'teacher_headers': {'Authorization': f'Bearer {teacher_token}'},
                'student_headers': {'Authorization': f'Bearer {student_token}'}
            }
    
    def test_create_assignment_success(self, client, setup_course_and_users):
        """测试创建作业成功"""
        setup = setup_course_and_users
        
        assignment_data = {
            'title': 'New Assignment',
            'description': 'Assignment description',
            'course_id': setup['course_id'],
            'due_date': (datetime.utcnow() + timedelta(days=7)).isoformat(),
            'max_score': 100,
            'homework_type': 'writing',
            'is_published': True
        }
        
        # 解码JWT token查看内容
        import jwt
        teacher_token = setup['teacher_headers']['Authorization'].replace('Bearer ', '')
        try:
            decoded_token = jwt.decode(teacher_token, options={"verify_signature": False})
            print(f"DEBUG: Decoded teacher token: {decoded_token}")
            print(f"DEBUG: Token user_id (from 'user_id'): {decoded_token.get('user_id')}")
            print(f"DEBUG: Token user_id (from 'sub'): {decoded_token.get('sub')}")
            print(f"DEBUG: Expected teacher_id: {setup['teacher_id']}")
            print(f"DEBUG: Course_id: {setup['course_id']}")
        except Exception as e:
            print(f"DEBUG: Error decoding token: {e}")
        
        print(f"DEBUG: Sending POST request to /api/assignments/ with data: {assignment_data}")
        print(f"DEBUG: Headers: {setup['teacher_headers']}")
        print(f"DEBUG: Teacher token: {teacher_token[:50]}...")
        response = client.post('/api/assignments/', json=assignment_data, headers=setup['teacher_headers'])
        print(f"DEBUG: Response status: {response.status_code}")
        print(f"DEBUG: Response data: {response.get_json()}")
        
        assert response.status_code == 201
        data = response.get_json()
        assert 'message' in data
        assignment = data['assignment']
        assert assignment['title'] == assignment_data['title']
        assert assignment['course_id'] == assignment_data['course_id']
        assert assignment['teacher_id'] == setup['teacher_id']
    
    def test_create_assignment_unauthorized(self, client, setup_course_and_users):
        """测试学生创建作业失败"""
        setup = setup_course_and_users
        
        assignment_data = {
            'title': 'Unauthorized Assignment',
            'description': 'Should not be created',
            'course_id': setup['course_id'],
            'due_date': (datetime.utcnow() + timedelta(days=7)).isoformat(),
            'max_score': 100
        }
        
        response = client.post('/api/assignments/', json=assignment_data, headers=setup['student_headers'])
        
        assert response.status_code == 403
        data = response.get_json()
        assert 'error' in data
    
    def test_get_assignments_list(self, client, setup_course_and_users):
        """测试获取作业列表"""
        setup = setup_course_and_users
        
        # 创建测试作业
        with client.application.app_context():
            assignment = Homework(
                title='Test Assignment List',
                description='Test Description',
                course_id=setup['course_id'],
                teacher_id=setup['teacher_id'],
                due_date=datetime.utcnow() + timedelta(days=7),
                max_score=100,
                homework_type='writing',
                is_published=True,
                created_at=datetime.utcnow()
            )
            db.session.add(assignment)
            db.session.commit()
        
        # 教师获取作业列表
        response = client.get('/api/assignments/', headers=setup['teacher_headers'])
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'assignments' in data
        assert len(data['assignments']) > 0
    
    def test_get_assignment_detail(self, client, setup_course_and_users):
        """测试获取作业详情"""
        setup = setup_course_and_users
        
        # 创建测试作业
        with client.application.app_context():
            assignment = Homework(
                title='Test Assignment Detail',
                description='Test Description Detail',
                course_id=setup['course_id'],
                teacher_id=setup['teacher_id'],
                due_date=datetime.utcnow() + timedelta(days=7),
                max_score=100,
                homework_type='writing',
                is_published=True,
                created_at=datetime.utcnow()
            )
            db.session.add(assignment)
            db.session.commit()
            assignment_id = assignment.id
        
        response = client.get(f'/api/assignments/{assignment_id}', headers=setup['teacher_headers'])
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['id'] == assignment_id
        assert data['title'] == 'Test Assignment Detail'
    
    def test_update_assignment_success(self, client, setup_course_and_users):
        """测试更新作业成功"""
        setup = setup_course_and_users
        
        # 创建测试作业
        with client.application.app_context():
            assignment = Homework(
                title='Original Title',
                description='Original Description',
                course_id=setup['course_id'],
                teacher_id=setup['teacher_id'],
                due_date=datetime.utcnow() + timedelta(days=7),
                max_score=100,
                homework_type='writing',
                is_published=False,
                created_at=datetime.utcnow()
            )
            db.session.add(assignment)
            db.session.commit()
            assignment_id = assignment.id
        
        update_data = {
            'title': 'Updated Title',
            'description': 'Updated Description',
            'max_score': 120,
            'is_published': True
        }
        
        response = client.put(f'/api/assignments/{assignment_id}', json=update_data, headers=setup['teacher_headers'])
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'message' in data
        assignment = data['assignment']
        assert assignment['title'] == 'Updated Title'
        assert assignment['max_score'] == 120
        assert assignment['is_published'] is True
    
    def test_delete_assignment_success(self, client, setup_course_and_users):
        """测试删除作业成功"""
        setup = setup_course_and_users
        
        # 创建测试作业
        with client.application.app_context():
            assignment = Homework(
                title='To Be Deleted',
                description='Will be deleted',
                course_id=setup['course_id'],
                teacher_id=setup['teacher_id'],
                due_date=datetime.utcnow() + timedelta(days=7),
                max_score=100,
                homework_type='writing',
                is_published=False,
                created_at=datetime.utcnow()
            )
            db.session.add(assignment)
            db.session.commit()
            assignment_id = assignment.id
        
        response = client.delete(f'/api/assignments/{assignment_id}', headers=setup['teacher_headers'])
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'message' in data
        
        # 验证作业已删除
        with client.application.app_context():
            deleted_assignment = Homework.query.get(assignment_id)
            assert deleted_assignment is None
    
    def test_submit_assignment_success(self, client, setup_course_and_users):
        """测试提交作业成功"""
        setup = setup_course_and_users
        
        # 创建测试作业
        with client.application.app_context():
            assignment = Homework(
                title='Submit Test Assignment',
                description='Test submission',
                course_id=setup['course_id'],
                teacher_id=setup['teacher_id'],
                due_date=datetime.utcnow() + timedelta(days=7),
                max_score=100,
                homework_type='writing',
                is_published=True,
                created_at=datetime.utcnow()
            )
            db.session.add(assignment)
            db.session.commit()
            assignment_id = assignment.id
        
        submission_data = {
            'content': 'This is my assignment submission',
            'action': 'submit'
        }
        
        print(f"[TEST DEBUG] 发送请求到: /api/assignments/{assignment_id}/submissions")
        print(f"[TEST DEBUG] 请求数据: {submission_data}")
        print(f"[TEST DEBUG] 请求头: {setup['student_headers']}")
        response = client.post(f'/api/assignments/{assignment_id}/submissions', json=submission_data, headers=setup['student_headers'])
        print(f"[TEST DEBUG] 响应状态码: {response.status_code}")
        print(f"[TEST DEBUG] 响应数据: {response.get_json()}")
        
        assert response.status_code == 201
        data = response.get_json()
        assert 'message' in data
        submission = data['submission']
        assert submission['content'] == submission_data['content']
        assert submission['student_id'] == setup['student_id']
    
    def test_submit_assignment_overdue(self, client, setup_course_and_users):
        """测试提交逾期作业"""
        setup = setup_course_and_users
        
        # 创建逾期作业
        with client.application.app_context():
            assignment = Homework(
                title='Overdue Assignment',
                description='This assignment is overdue',
                course_id=setup['course_id'],
                teacher_id=setup['teacher_id'],
                due_date=datetime.utcnow() - timedelta(days=1),  # 昨天截止
                max_score=100,
                homework_type='writing',
                is_published=True,
                created_at=datetime.utcnow()
            )
            db.session.add(assignment)
            db.session.commit()
            assignment_id = assignment.id
        
        submission_data = {
            'content': 'Late submission',
            'action': 'submit'
        }
        
        print(f"[TEST DEBUG] 发送逾期提交请求到: /api/assignments/{assignment_id}/submissions")
        print(f"[TEST DEBUG] 请求数据: {submission_data}")
        print(f"[TEST DEBUG] 请求头: {setup['student_headers']}")
        response = client.post(f'/api/assignments/{assignment_id}/submissions', json=submission_data, headers=setup['student_headers'])
        print(f"[TEST DEBUG] 响应状态码: {response.status_code}")
        print(f"[TEST DEBUG] 响应数据: {response.get_json()}")
        
        # 添加调试信息
        if response.status_code != 201:
            error_msg = f"Expected 201, got {response.status_code}. Response: {response.get_json()}"
            assert False, error_msg
        
        assert response.status_code == 201
        data = response.get_json()
        assert 'message' in data
        submission = data['submission']
        print(f"[TEST DEBUG] 提交结果: is_late={submission.get('is_late')}")
        assert submission['is_late'] is True
    
    def test_grade_assignment_success(self, client, setup_course_and_users):
        """测试批改作业成功"""
        setup = setup_course_and_users
        
        # 创建作业和提交
        with client.application.app_context():
            assignment = Homework(
                title='Grade Test Assignment',
                description='Test grading',
                course_id=setup['course_id'],
                teacher_id=setup['teacher_id'],
                due_date=datetime.utcnow() + timedelta(days=7),
                max_score=100,
                homework_type='writing',
                is_published=True,
                created_at=datetime.utcnow()
            )
            db.session.add(assignment)
            db.session.commit()
            
            submission = HomeworkSubmission(
                homework_id=assignment.id,
                student_id=setup['student_id'],
                content='Student submission content',
                status='submitted',
                submitted_at=datetime.utcnow()
            )
            db.session.add(submission)
            db.session.commit()
            assignment_id = assignment.id
            submission_id = submission.id
        
        grade_data = {
            'score': 85,
            'feedback': 'Good work, but could be improved'
        }
        
        response = client.post(f'/api/assignments/{assignment_id}/submissions/{submission_id}/grade', json=grade_data, headers=setup['teacher_headers'])
        
        # 详细的错误信息
        if response.status_code != 200:
            error_msg = f"Expected 200, got {response.status_code}. Response: {response.get_json()}"
            assert False, error_msg
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'message' in data
        submission = data['submission']
        assert submission['score'] == 85
        assert submission['feedback'] == grade_data['feedback']
        assert submission['graded_at'] is not None
    
    def test_get_assignment_statistics(self, client, setup_course_and_users):
        """测试获取作业统计"""
        setup = setup_course_and_users
        
        # 创建作业和提交
        with client.application.app_context():
            assignment = Homework(
                title='Statistics Test Assignment',
                description='Test statistics',
                course_id=setup['course_id'],
                teacher_id=setup['teacher_id'],
                due_date=datetime.utcnow() + timedelta(days=7),
                max_score=100,
                homework_type='writing',
                is_published=True,
                created_at=datetime.utcnow()
            )
            db.session.add(assignment)
            db.session.commit()
            
            submission = HomeworkSubmission(
                homework_id=assignment.id,
                student_id=setup['student_id'],
                content='Student submission',
                submitted_at=datetime.utcnow(),
                score=90,
                graded_at=datetime.utcnow()
            )
            db.session.add(submission)
            db.session.commit()
            assignment_id = assignment.id
        
        response = client.get(f'/api/assignments/{assignment_id}/statistics', headers=setup['teacher_headers'])
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'message' in data
        stats = data['statistics']
        assert 'total_submissions' in stats
        assert 'graded_submissions' in stats
        assert 'average_score' in stats
        assert stats['total_submissions'] == 1
        assert stats['graded_submissions'] == 1
    
    def test_get_assignments_overview_statistics(self, client, setup_course_and_users):
        """测试获取作业总览统计"""
        setup = setup_course_and_users
        
        # 创建多个作业
        with client.application.app_context():
            for i in range(3):
                assignment = Homework(
                    title=f'Overview Test Assignment {i+1}',
                    description=f'Test overview {i+1}',
                    course_id=setup['course_id'],
                    teacher_id=setup['teacher_id'],
                    due_date=datetime.utcnow() + timedelta(days=7),
                    max_score=100,
                    homework_type='writing',
                    is_published=i < 2,  # 前两个发布，最后一个草稿
                    created_at=datetime.utcnow()
                )
                db.session.add(assignment)
            db.session.commit()
        
        response = client.get('/api/assignments/statistics/overview', headers=setup['teacher_headers'])
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'message' in data
        stats = data['statistics']
        assert 'assignments_overview' in stats
        overview = stats['assignments_overview']
        assert 'total_assignments' in overview
        assert 'published_assignments' in overview
        assert 'draft_assignments' in overview
        assert overview['total_assignments'] >= 3
        assert overview['published_assignments'] >= 2
        assert overview['draft_assignments'] >= 1
    
    def test_file_upload_with_assignment(self, client, setup_course_and_users):
        """测试作业文件上传"""
        setup = setup_course_and_users
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write('Test assignment file content')
            temp_file_path = f.name
        
        try:
            # 上传文件
            with open(temp_file_path, 'rb') as f:
                response = client.post('/api/files/upload', 
                    data={
                        'file': (f, 'assignment.txt'),
                        'category': 'homework_attachment'
                    },
                    headers=setup['teacher_headers']
                )
            
            assert response.status_code == 201
            data = response.get_json()
            assert 'message' in data
            file_info = data['file']
            file_id = file_info['id']
            
            # 创建带文件的作业
            assignment_data = {
                'title': 'Assignment with File',
                'description': 'Assignment with attached file',
                'course_id': setup['course_id'],
                'due_date': (datetime.utcnow() + timedelta(days=7)).isoformat(),
                'max_score': 100,
                'homework_type': 'writing',
                'is_published': True,
                'attachment_files': [file_id]
            }
            
            response = client.post('/api/assignments', json=assignment_data, headers=setup['teacher_headers'])
            
            assert response.status_code == 201
            data = response.get_json()
            assert 'message' in data
            assignment = data['assignment']
            assert 'attachment_files' in assignment
            
        finally:
            # 清理临时文件
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)