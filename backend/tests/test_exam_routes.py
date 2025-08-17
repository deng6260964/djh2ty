import pytest
import json
from datetime import datetime, timedelta
from app.database import db
from app.models.user import User
from app.models.exam import Exam, ExamQuestion, ExamSubmission
from app.models.question import QuestionBank, Question
from app.models.course import Course
from app.utils.auth import hash_password
import uuid

class TestExamRoutes:
    """考试管理路由测试类"""
    
    def test_get_exams_success(self, client, admin_user):
        """测试获取考试列表成功"""
        # 创建管理员认证头
        login_response = client.post('/api/auth/login', json={
            'email': admin_user.email,
            'password': 'SuperUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        response = client.get('/api/exams', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'exams' in data['data']
        assert 'pagination' in data['data']
        assert isinstance(data['data']['exams'], list)
    
    def test_get_exams_with_filters(self, client, teacher_user):
        """测试带过滤条件的考试列表"""
        login_response = client.post('/api/auth/login', json={
            'email': teacher_user.email,
            'password': 'EduUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # 创建测试课程和考试
        with client.application.app_context():
            course = Course(
                name='Test Course',
                description='Test Description',
                course_type='one_to_many',
                teacher_id=teacher_user.id,
                created_at=datetime.utcnow()
            )
            db.session.add(course)
            db.session.commit()
            
            exam = Exam(
                title='Test Exam',
                description='Test Description',
                course_id=course.id,
                created_by=teacher_user.id,
                start_time=datetime.utcnow() + timedelta(days=1),
                end_time=datetime.utcnow() + timedelta(days=2),
                duration_minutes=60,
                total_points=100,
                status='draft',
                created_at=datetime.utcnow()
            )
            db.session.add(exam)
            db.session.commit()
        
        # 测试状态过滤
        response = client.get('/api/exams?status=draft&page=1&per_page=10', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'exams' in data['data']
        for exam in data['data']['exams']:
            assert exam['status'] == 'draft'
    
    def test_get_exam_by_id_success(self, client, teacher_user):
        """测试根据ID获取考试成功"""
        login_response = client.post('/api/auth/login', json={
            'email': teacher_user.email,
            'password': 'EduUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # 创建测试课程和考试
        with client.application.app_context():
            course = Course(
                name='Test Course Detail',
                description='Test Description',
                course_type='one_to_many',
                teacher_id=teacher_user.id,
                created_at=datetime.utcnow()
            )
            db.session.add(course)
            db.session.commit()
            
            exam = Exam(
                title='Test Exam Detail',
                description='Test Description Detail',
                course_id=course.id,
                created_by=teacher_user.id,
                start_time=datetime.utcnow() + timedelta(days=1),
                end_time=datetime.utcnow() + timedelta(days=2),
                duration_minutes=90,
                total_points=150,
                status='published',
                created_at=datetime.utcnow()
            )
            db.session.add(exam)
            db.session.commit()
            exam_id = exam.id
        
        response = client.get(f'/api/exams/{exam_id}', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        exam_info = data['data']['exam']
        assert exam_info['id'] == exam_id
        assert exam_info['title'] == 'Test Exam Detail'
        assert exam_info['duration_minutes'] == 90
        assert exam_info['status'] == 'published'
    
    def test_get_exam_by_id_not_found(self, client, teacher_user):
        """测试获取不存在的考试"""
        login_response = client.post('/api/auth/login', json={
            'email': teacher_user.email,
            'password': 'EduUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        response = client.get('/api/exams/99999', headers=headers)
        
        assert response.status_code == 404
        data = response.get_json()
        assert data['success'] is False
        assert data['error'] == 'EXAM_NOT_FOUND'
    
    def test_create_exam_success(self, client, teacher_user):
        """测试创建考试成功"""
        login_response = client.post('/api/auth/login', json={
            'email': teacher_user.email,
            'password': 'EduUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # 创建测试课程
        with client.application.app_context():
            course = Course(
                name='Test Course for Exam',
                description='Test Description',
                course_type='one_to_many',
                teacher_id=teacher_user.id,
                created_at=datetime.utcnow()
            )
            db.session.add(course)
            db.session.commit()
            course_id = course.id
        
        exam_data = {
            'title': 'New Exam',
            'description': 'New Exam Description',
            'course_id': course_id,
            'start_time': (datetime.utcnow() + timedelta(days=1)).isoformat(),
            'end_time': (datetime.utcnow() + timedelta(days=2)).isoformat(),
            'duration_minutes': 120,
            'total_points': 200,
            'passing_score': 120,
            'max_attempts': 2,
            'shuffle_questions': True,
            'show_results_immediately': False,
            'allow_review': True
        }
        
        response = client.post('/api/exams', json=exam_data, headers=headers)
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True
        exam_info = data['data']['exam']
        assert exam_info['title'] == exam_data['title']
        assert exam_info['description'] == exam_data['description']
        assert exam_info['course_id'] == exam_data['course_id']
        assert exam_info['duration_minutes'] == exam_data['duration_minutes']
        assert exam_info['created_by'] == teacher_user.id
        assert exam_info['status'] == 'draft'
        
        # 验证考试已创建
        with client.application.app_context():
            exam = Exam.query.filter_by(title=exam_data['title']).first()
            assert exam is not None
    
    def test_create_exam_missing_fields(self, client, teacher_user):
        """测试创建考试时缺少必填字段"""
        login_response = client.post('/api/auth/login', json={
            'email': teacher_user.email,
            'password': 'EduUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        exam_data = {
            'description': 'Missing Title Description'
            # 缺少title字段
        }
        
        response = client.post('/api/exams', json=exam_data, headers=headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert data['error'] == 'MISSING_REQUIRED_FIELDS'
    
    def test_update_exam_success(self, client, teacher_user):
        """测试更新考试成功"""
        login_response = client.post('/api/auth/login', json={
            'email': teacher_user.email,
            'password': 'EduUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # 创建测试课程和考试
        with client.application.app_context():
            course = Course(
                name='Test Course',
                description='Test Description',
                course_type='one_to_many',
                teacher_id=teacher_user.id,
                created_at=datetime.utcnow()
            )
            db.session.add(course)
            db.session.commit()
            
            exam = Exam(
                title='Original Exam',
                description='Original Description',
                course_id=course.id,
                created_by=teacher_user.id,
                start_time=datetime.utcnow() + timedelta(days=1),
                end_time=datetime.utcnow() + timedelta(days=2),
                duration_minutes=60,
                total_points=100,
                status='draft',
                created_at=datetime.utcnow()
            )
            db.session.add(exam)
            db.session.commit()
            exam_id = exam.id
        
        update_data = {
            'title': 'Updated Exam',
            'description': 'Updated Description',
            'duration_minutes': 90,
            'total_points': 150,
            'passing_score': 90
        }
        
        response = client.put(f'/api/exams/{exam_id}', json=update_data, headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        exam_info = data['data']['exam']
        assert exam_info['title'] == update_data['title']
        assert exam_info['description'] == update_data['description']
        assert exam_info['duration_minutes'] == update_data['duration_minutes']
        assert exam_info['total_points'] == update_data['total_points']
    
    def test_update_exam_permission_denied(self, client, teacher_user, test_user):
        """测试更新他人考试权限被拒绝"""
        # 创建另一个用户的考试
        with client.application.app_context():
            course = Course(
                name='Other User Course',
                description='Other User Description',
                course_type='one_to_many',
                teacher_id=test_user.id,
                created_at=datetime.utcnow()
            )
            db.session.add(course)
            db.session.commit()
            
            exam = Exam(
                title='Other User Exam',
                description='Other User Description',
                course_id=course.id,
                created_by=test_user.id,  # 其他用户创建
                start_time=datetime.utcnow() + timedelta(days=1),
                end_time=datetime.utcnow() + timedelta(days=2),
                duration_minutes=60,
                total_points=100,
                status='draft',
                created_at=datetime.utcnow()
            )
            db.session.add(exam)
            db.session.commit()
            exam_id = exam.id
        
        # 教师用户尝试更新
        login_response = client.post('/api/auth/login', json={
            'email': teacher_user.email,
            'password': 'EduUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        update_data = {'title': 'Unauthorized Update'}
        
        response = client.put(f'/api/exams/{exam_id}', json=update_data, headers=headers)
        
        assert response.status_code == 403
        data = response.get_json()
        assert data['success'] is False
        assert data['error'] == 'PERMISSION_DENIED'
    
    def test_delete_exam_success(self, client, teacher_user):
        """测试删除考试成功"""
        login_response = client.post('/api/auth/login', json={
            'email': teacher_user.email,
            'password': 'EduUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # 创建测试课程和考试
        with client.application.app_context():
            course = Course(
                name='Test Course',
                description='Test Description',
                course_type='one_to_many',
                teacher_id=teacher_user.id,
                created_at=datetime.utcnow()
            )
            db.session.add(course)
            db.session.commit()
            
            exam = Exam(
                title='To Delete Exam',
                description='To Delete Description',
                course_id=course.id,
                created_by=teacher_user.id,
                start_time=datetime.utcnow() + timedelta(days=1),
                end_time=datetime.utcnow() + timedelta(days=2),
                duration_minutes=60,
                total_points=100,
                status='draft',
                created_at=datetime.utcnow()
            )
            db.session.add(exam)
            db.session.commit()
            exam_id = exam.id
        
        response = client.delete(f'/api/exams/{exam_id}', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['message'] == 'Exam deleted successfully'
        
        # 验证考试已删除
        with client.application.app_context():
            exam = Exam.query.get(exam_id)
            assert exam is None

class TestExamQuestionRoutes:
    """考试题目管理路由测试类"""
    
    def test_get_exam_questions_success(self, client, teacher_user):
        """测试获取考试题目列表成功"""
        login_response = client.post('/api/auth/login', json={
            'email': teacher_user.email,
            'password': 'EduUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # 创建测试数据
        with client.application.app_context():
            # 创建课程
            course = Course(
                name='Test Course',
                description='Test Description',
                course_type='one_to_many',
                teacher_id=teacher_user.id,
                created_at=datetime.utcnow()
            )
            db.session.add(course)
            db.session.commit()
            
            # 创建考试
            exam = Exam(
                title='Test Exam',
                description='Test Description',
                course_id=course.id,
                created_by=teacher_user.id,
                start_time=datetime.utcnow() + timedelta(days=1),
                end_time=datetime.utcnow() + timedelta(days=2),
                duration_minutes=60,
                total_points=100,
                status='draft',
                created_at=datetime.utcnow()
            )
            db.session.add(exam)
            db.session.commit()
            exam_id = exam.id
            
            # 创建题库和题目
            question_bank = QuestionBank(
                name='Test Bank',
                description='Test Description',
                category='math',
                difficulty_level='intermediate',
                is_public=True,
                created_by=teacher_user.id,
                created_at=datetime.utcnow()
            )
            db.session.add(question_bank)
            db.session.commit()
            
            question = Question(
                question_bank_id=question_bank.id,
                question_type='multiple_choice',
                title='Test Question',
                content='What is 1+1?',
                options=json.dumps(['1', '2', '3', '4']),
                correct_answer='2',
                explanation='1+1 equals 2',
                points=10,
                difficulty_level='beginner',
                tags='math,basic',
                created_by=teacher_user.id,
                created_at=datetime.utcnow()
            )
            db.session.add(question)
            db.session.commit()
            
            # 添加题目到考试
            exam_question = ExamQuestion(
                exam_id=exam.id,
                question_id=question.id,
                points=10,
                order_index=1
            )
            db.session.add(exam_question)
            db.session.commit()
        
        response = client.get(f'/api/exams/{exam_id}/questions', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'questions' in data['data']
        assert isinstance(data['data']['questions'], list)
        assert len(data['data']['questions']) == 1
    
    def test_add_question_to_exam_success(self, client, teacher_user):
        """测试添加题目到考试成功"""
        login_response = client.post('/api/auth/login', json={
            'email': teacher_user.email,
            'password': 'EduUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # 创建测试数据
        with client.application.app_context():
            # 创建课程
            course = Course(
                name='Test Course',
                description='Test Description',
                course_type='one_to_many',
                teacher_id=teacher_user.id,
                created_at=datetime.utcnow()
            )
            db.session.add(course)
            db.session.commit()
            
            # 创建考试
            exam = Exam(
                title='Test Exam',
                description='Test Description',
                course_id=course.id,
                created_by=teacher_user.id,
                start_time=datetime.utcnow() + timedelta(days=1),
                end_time=datetime.utcnow() + timedelta(days=2),
                duration_minutes=60,
                total_points=100,
                status='draft',
                created_at=datetime.utcnow()
            )
            db.session.add(exam)
            db.session.commit()
            exam_id = exam.id
            
            # 创建题库和题目
            question_bank = QuestionBank(
                name='Test Bank',
                description='Test Description',
                category='math',
                difficulty_level='intermediate',
                is_public=True,
                created_by=teacher_user.id,
                created_at=datetime.utcnow()
            )
            db.session.add(question_bank)
            db.session.commit()
            
            question = Question(
                question_bank_id=question_bank.id,
                question_type='multiple_choice',
                title='Test Question',
                content='What is 2+2?',
                options=json.dumps(['2', '3', '4', '5']),
                correct_answer='4',
                explanation='2+2 equals 4',
                points=10,
                difficulty_level='beginner',
                tags='math,addition',
                created_by=teacher_user.id,
                created_at=datetime.utcnow()
            )
            db.session.add(question)
            db.session.commit()
            question_id = question.id
        
        question_data = {
            'question_id': question_id,
            'points': 15,
            'order_index': 1
        }
        
        response = client.post(f'/api/exams/{exam_id}/questions', json=question_data, headers=headers)
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True
        assert data['message'] == 'Question added to exam successfully'
        
        # 验证题目已添加到考试
        with client.application.app_context():
            exam_question = ExamQuestion.query.filter_by(
                exam_id=exam_id, 
                question_id=question_id
            ).first()
            assert exam_question is not None
            assert exam_question.points == 15
    
    def test_remove_question_from_exam_success(self, client, teacher_user):
        """测试从考试中移除题目成功"""
        login_response = client.post('/api/auth/login', json={
            'email': teacher_user.email,
            'password': 'EduUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # 创建测试数据
        with client.application.app_context():
            # 创建课程
            course = Course(
                name='Test Course',
                description='Test Description',
                course_type='one_to_many',
                teacher_id=teacher_user.id,
                created_at=datetime.utcnow()
            )
            db.session.add(course)
            db.session.commit()
            
            # 创建考试
            exam = Exam(
                title='Test Exam',
                description='Test Description',
                course_id=course.id,
                created_by=teacher_user.id,
                start_time=datetime.utcnow() + timedelta(days=1),
                end_time=datetime.utcnow() + timedelta(days=2),
                duration_minutes=60,
                total_points=100,
                status='draft',
                created_at=datetime.utcnow()
            )
            db.session.add(exam)
            db.session.commit()
            exam_id = exam.id
            
            # 创建题库和题目
            question_bank = QuestionBank(
                name='Test Bank',
                description='Test Description',
                category='math',
                difficulty_level='intermediate',
                is_public=True,
                created_by=teacher_user.id,
                created_at=datetime.utcnow()
            )
            db.session.add(question_bank)
            db.session.commit()
            
            question = Question(
                question_bank_id=question_bank.id,
                question_type='multiple_choice',
                title='Test Question',
                content='What is 3+3?',
                options=json.dumps(['4', '5', '6', '7']),
                correct_answer='6',
                explanation='3+3 equals 6',
                points=10,
                difficulty_level='beginner',
                tags='math,addition',
                created_by=teacher_user.id,
                created_at=datetime.utcnow()
            )
            db.session.add(question)
            db.session.commit()
            question_id = question.id
            
            # 添加题目到考试
            exam_question = ExamQuestion(
                exam_id=exam.id,
                question_id=question.id,
                points=10,
                order_index=1
            )
            db.session.add(exam_question)
            db.session.commit()
        
        response = client.delete(f'/api/exams/{exam_id}/questions/{question_id}', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['message'] == 'Question removed from exam successfully'
        
        # 验证题目已从考试中移除
        with client.application.app_context():
            exam_question = ExamQuestion.query.filter_by(
                exam_id=exam_id, 
                question_id=question_id
            ).first()
            assert exam_question is None
    
    def test_add_question_to_published_exam_fails(self, client, teacher_user):
        """测试向已发布考试添加题目失败"""
        login_response = client.post('/api/auth/login', json={
            'email': teacher_user.email,
            'password': 'EduUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # 创建测试数据
        with client.application.app_context():
            # 创建课程
            course = Course(
                name='Test Course',
                description='Test Description',
                course_type='one_to_many',
                teacher_id=teacher_user.id,
                created_at=datetime.utcnow()
            )
            db.session.add(course)
            db.session.commit()
            
            # 创建已发布的考试
            exam = Exam(
                title='Published Exam',
                description='Published Description',
                course_id=course.id,
                created_by=teacher_user.id,
                start_time=datetime.utcnow() + timedelta(days=1),
                end_time=datetime.utcnow() + timedelta(days=2),
                duration_minutes=60,
                total_points=100,
                status='published',  # 已发布状态
                created_at=datetime.utcnow()
            )
            db.session.add(exam)
            db.session.commit()
            exam_id = exam.id
            
            # 创建题库和题目
            question_bank = QuestionBank(
                name='Test Bank',
                description='Test Description',
                category='math',
                difficulty_level='intermediate',
                is_public=True,
                created_by=teacher_user.id,
                created_at=datetime.utcnow()
            )
            db.session.add(question_bank)
            db.session.commit()
            
            question = Question(
                question_bank_id=question_bank.id,
                question_type='multiple_choice',
                title='Test Question',
                content='What is 4+4?',
                options=json.dumps(['6', '7', '8', '9']),
                correct_answer='8',
                explanation='4+4 equals 8',
                points=10,
                difficulty_level='beginner',
                tags='math,addition',
                created_by=teacher_user.id,
                created_at=datetime.utcnow()
            )
            db.session.add(question)
            db.session.commit()
            question_id = question.id
        
        question_data = {
            'question_id': question_id,
            'points': 15,
            'order_index': 1
        }
        
        response = client.post(f'/api/exams/{exam_id}/questions', json=question_data, headers=headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert data['error'] == 'EXAM_NOT_EDITABLE'


class TestOnlineExamRoutes:
    """在线考试API测试类"""
    
    def test_start_exam_success(self, client, test_user):
        """测试学生开始考试成功"""
        login_response = client.post('/api/auth/login', json={
            'email': test_user.email,
            'password': 'TestUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # 创建测试数据
        with client.application.app_context():
            # 创建课程
            course = Course(
                name='Test Course',
                description='Test Description',
                course_type='one_to_many',
                teacher_id=test_user.id,
                created_at=datetime.utcnow()
            )
            db.session.add(course)
            db.session.commit()
            
            # 创建考试（进行中状态）
            exam = Exam(
                title='Online Test Exam',
                description='Online Test Description',
                course_id=course.id,
                created_by=test_user.id,
                start_time=datetime.utcnow() - timedelta(minutes=30),  # 已开始
                end_time=datetime.utcnow() + timedelta(hours=2),      # 未结束
                duration_minutes=120,
                total_points=100,
                status='published',
                created_at=datetime.utcnow()
            )
            db.session.add(exam)
            db.session.commit()
            exam_id = exam.id
            
            # 创建题库和题目
            question_bank = QuestionBank(
                name='Test Bank',
                description='Test Description',
                category='math',
                difficulty_level='intermediate',
                is_public=True,
                created_by=test_user.id,
                created_at=datetime.utcnow()
            )
            db.session.add(question_bank)
            db.session.commit()
            
            question = Question(
                question_bank_id=question_bank.id,
                question_type='multiple_choice',
                title='Test Question',
                content='What is 2+2?',
                options=json.dumps(['2', '3', '4', '5']),
                correct_answer='4',
                explanation='2+2 equals 4',
                points=10,
                difficulty_level='beginner',
                tags='math,addition',
                created_by=test_user.id,
                created_at=datetime.utcnow()
            )
            db.session.add(question)
            db.session.commit()
            
            # 添加题目到考试
            exam_question = ExamQuestion(
                exam_id=exam.id,
                question_id=question.id,
                points=10,
                order_index=1
            )
            db.session.add(exam_question)
            db.session.commit()
        
        response = client.get(f'/api/exams/{exam_id}/start', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'submission' in data['data']
        assert 'questions' in data['data']
        assert data['data']['submission']['exam_id'] == exam_id
        assert data['data']['submission']['user_id'] == test_user.id
        assert data['data']['submission']['status'] == 'in_progress'
        
        # 验证提交记录已创建
        with client.application.app_context():
            submission = ExamSubmission.query.filter_by(
                exam_id=exam_id, 
                user_id=test_user.id
            ).first()
            assert submission is not None
            assert submission.status == 'in_progress'
    
    def test_start_exam_not_started(self, client, test_user):
        """测试开始未开始的考试失败"""
        login_response = client.post('/api/auth/login', json={
            'email': test_user.email,
            'password': 'TestUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # 创建未开始的考试
        with client.application.app_context():
            course = Course(
                name='Test Course',
                description='Test Description',
                course_type='one_to_many',
                teacher_id=test_user.id,
                created_at=datetime.utcnow()
            )
            db.session.add(course)
            db.session.commit()
            
            exam = Exam(
                title='Future Exam',
                description='Future Description',
                course_id=course.id,
                created_by=test_user.id,
                start_time=datetime.utcnow() + timedelta(hours=1),  # 未开始
                end_time=datetime.utcnow() + timedelta(hours=3),
                duration_minutes=120,
                total_points=100,
                status='published',
                created_at=datetime.utcnow()
            )
            db.session.add(exam)
            db.session.commit()
            exam_id = exam.id
        
        response = client.get(f'/api/exams/{exam_id}/start', headers=headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert data['error'] == 'EXAM_NOT_STARTED'
    
    def test_submit_exam_success(self, client, test_user):
        """测试提交考试成功"""
        login_response = client.post('/api/auth/login', json={
            'email': test_user.email,
            'password': 'TestUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # 创建测试数据
        with client.application.app_context():
            course = Course(
                name='Test Course',
                description='Test Description',
                course_type='one_to_many',
                teacher_id=test_user.id,
                created_at=datetime.utcnow()
            )
            db.session.add(course)
            db.session.commit()
            
            exam = Exam(
                title='Submit Test Exam',
                description='Submit Test Description',
                course_id=course.id,
                created_by=test_user.id,
                start_time=datetime.utcnow() - timedelta(minutes=30),
                end_time=datetime.utcnow() + timedelta(hours=2),
                duration_minutes=120,
                total_points=100,
                status='published',
                created_at=datetime.utcnow()
            )
            db.session.add(exam)
            db.session.commit()
            exam_id = exam.id
            
            # 创建题库和题目
            question_bank = QuestionBank(
                name='Test Bank',
                description='Test Description',
                category='math',
                difficulty_level='intermediate',
                is_public=True,
                created_by=test_user.id,
                created_at=datetime.utcnow()
            )
            db.session.add(question_bank)
            db.session.commit()
            
            question = Question(
                question_bank_id=question_bank.id,
                question_type='multiple_choice',
                title='Test Question',
                content='What is 5+5?',
                options=json.dumps(['8', '9', '10', '11']),
                correct_answer='10',
                explanation='5+5 equals 10',
                points=10,
                difficulty_level='beginner',
                tags='math,addition',
                created_by=test_user.id,
                created_at=datetime.utcnow()
            )
            db.session.add(question)
            db.session.commit()
            question_id = question.id
            
            # 添加题目到考试
            exam_question = ExamQuestion(
                exam_id=exam.id,
                question_id=question.id,
                points=10,
                order_index=1
            )
            db.session.add(exam_question)
            db.session.commit()
            
            # 创建考试提交记录
            submission = ExamSubmission(
                exam_id=exam.id,
                user_id=test_user.id,
                status='in_progress',
                started_at=datetime.utcnow(),
                answers=json.dumps({}),
                score=0,
                total_points=100
            )
            db.session.add(submission)
            db.session.commit()
        
        # 提交答案
        answers_data = {
            'answers': {
                str(question_id): '10'
            }
        }
        
        response = client.post(f'/api/exams/{exam_id}/submit', json=answers_data, headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'submission' in data['data']
        assert data['data']['submission']['status'] == 'submitted'
        assert data['data']['submission']['score'] == 10  # 正确答案得分
        
        # 验证提交记录已更新
        with client.application.app_context():
            submission = ExamSubmission.query.filter_by(
                exam_id=exam_id, 
                user_id=test_user.id
            ).first()
            assert submission is not None
            assert submission.status == 'submitted'
            assert submission.score == 10
    
    def test_get_exam_submission_success(self, client, test_user):
        """测试获取考试提交状态成功"""
        login_response = client.post('/api/auth/login', json={
            'email': test_user.email,
            'password': 'TestUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # 创建测试数据
        with client.application.app_context():
            course = Course(
                name='Test Course',
                description='Test Description',
                course_type='one_to_many',
                teacher_id=test_user.id,
                created_at=datetime.utcnow()
            )
            db.session.add(course)
            db.session.commit()
            
            exam = Exam(
                title='Status Test Exam',
                description='Status Test Description',
                course_id=course.id,
                created_by=test_user.id,
                start_time=datetime.utcnow() - timedelta(minutes=30),
                end_time=datetime.utcnow() + timedelta(hours=2),
                duration_minutes=120,
                total_points=100,
                status='published',
                created_at=datetime.utcnow()
            )
            db.session.add(exam)
            db.session.commit()
            exam_id = exam.id
            
            # 创建考试提交记录
            submission = ExamSubmission(
                exam_id=exam.id,
                user_id=test_user.id,
                status='in_progress',
                started_at=datetime.utcnow() - timedelta(minutes=10),
                answers=json.dumps({'1': 'answer1'}),
                score=0,
                total_points=100
            )
            db.session.add(submission)
            db.session.commit()
        
        response = client.get(f'/api/exams/{exam_id}/submission', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'submission' in data['data']
        assert 'time_remaining' in data['data']
        assert 'progress' in data['data']
        assert data['data']['submission']['exam_id'] == exam_id
        assert data['data']['submission']['user_id'] == test_user.id
        assert data['data']['submission']['status'] == 'in_progress'
    
    def test_save_question_answer_success(self, client, test_user):
        """测试保存单题答案成功"""
        login_response = client.post('/api/auth/login', json={
            'email': test_user.email,
            'password': 'TestUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # 创建测试数据
        with client.application.app_context():
            course = Course(
                name='Test Course',
                description='Test Description',
                course_type='one_to_many',
                teacher_id=test_user.id,
                created_at=datetime.utcnow()
            )
            db.session.add(course)
            db.session.commit()
            
            exam = Exam(
                title='Answer Test Exam',
                description='Answer Test Description',
                course_id=course.id,
                created_by=test_user.id,
                start_time=datetime.utcnow() - timedelta(minutes=30),
                end_time=datetime.utcnow() + timedelta(hours=2),
                duration_minutes=120,
                total_points=100,
                status='published',
                created_at=datetime.utcnow()
            )
            db.session.add(exam)
            db.session.commit()
            exam_id = exam.id
            
            # 创建题库和题目
            question_bank = QuestionBank(
                name='Test Bank',
                description='Test Description',
                category='math',
                difficulty_level='intermediate',
                is_public=True,
                created_by=test_user.id,
                created_at=datetime.utcnow()
            )
            db.session.add(question_bank)
            db.session.commit()
            
            question = Question(
                question_bank_id=question_bank.id,
                question_type='multiple_choice',
                title='Test Question',
                content='What is 6+6?',
                options=json.dumps(['10', '11', '12', '13']),
                correct_answer='12',
                explanation='6+6 equals 12',
                points=10,
                difficulty_level='beginner',
                tags='math,addition',
                created_by=test_user.id,
                created_at=datetime.utcnow()
            )
            db.session.add(question)
            db.session.commit()
            question_id = question.id
            
            # 添加题目到考试
            exam_question = ExamQuestion(
                exam_id=exam.id,
                question_id=question.id,
                points=10,
                order_index=1
            )
            db.session.add(exam_question)
            db.session.commit()
            
            # 创建考试提交记录
            submission = ExamSubmission(
                exam_id=exam.id,
                user_id=test_user.id,
                status='in_progress',
                started_at=datetime.utcnow(),
                answers=json.dumps({}),
                score=0,
                total_points=100
            )
            db.session.add(submission)
            db.session.commit()
        
        # 保存单题答案
        answer_data = {
            'question_id': question_id,
            'answer': '12'
        }
        
        response = client.post(f'/api/exams/{exam_id}/answers', json=answer_data, headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'submission' in data['data']
        assert 'progress' in data['data']
        
        # 验证答案已保存
        with client.application.app_context():
            submission = ExamSubmission.query.filter_by(
                exam_id=exam_id, 
                user_id=test_user.id
            ).first()
            assert submission is not None
            answers = json.loads(submission.answers)
            assert str(question_id) in answers
            assert answers[str(question_id)] == '12'
    
    def test_get_exam_time_remaining_success(self, client, test_user):
        """测试获取考试剩余时间成功"""
        login_response = client.post('/api/auth/login', json={
            'email': test_user.email,
            'password': 'TestUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # 创建测试数据
        with client.application.app_context():
            course = Course(
                name='Test Course',
                description='Test Description',
                course_type='one_to_many',
                teacher_id=test_user.id,
                created_at=datetime.utcnow()
            )
            db.session.add(course)
            db.session.commit()
            
            exam = Exam(
                title='Time Test Exam',
                description='Time Test Description',
                course_id=course.id,
                created_by=test_user.id,
                start_time=datetime.utcnow() - timedelta(minutes=30),
                end_time=datetime.utcnow() + timedelta(hours=2),
                duration_minutes=120,
                total_points=100,
                status='published',
                created_at=datetime.utcnow()
            )
            db.session.add(exam)
            db.session.commit()
            exam_id = exam.id
            
            # 创建考试提交记录
            submission = ExamSubmission(
                exam_id=exam.id,
                user_id=test_user.id,
                status='in_progress',
                started_at=datetime.utcnow() - timedelta(minutes=10),
                answers=json.dumps({}),
                score=0,
                total_points=100
            )
            db.session.add(submission)
            db.session.commit()
        
        response = client.get(f'/api/exams/{exam_id}/time-remaining', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'time_remaining_minutes' in data['data']
        assert 'status' in data['data']
        assert data['data']['status'] == 'in_progress'
        assert data['data']['time_remaining_minutes'] > 0
        assert data['data']['time_remaining_minutes'] <= 120
    
    def test_submit_exam_already_submitted(self, client, test_user):
        """测试重复提交考试失败"""
        login_response = client.post('/api/auth/login', json={
            'email': test_user.email,
            'password': 'TestUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # 创建测试数据
        with client.application.app_context():
            course = Course(
                name='Test Course',
                description='Test Description',
                course_type='one_to_many',
                teacher_id=test_user.id,
                created_at=datetime.utcnow()
            )
            db.session.add(course)
            db.session.commit()
            
            exam = Exam(
                title='Duplicate Submit Test Exam',
                description='Duplicate Submit Test Description',
                course_id=course.id,
                created_by=test_user.id,
                start_time=datetime.utcnow() - timedelta(minutes=30),
                end_time=datetime.utcnow() + timedelta(hours=2),
                duration_minutes=120,
                total_points=100,
                status='published',
                created_at=datetime.utcnow()
            )
            db.session.add(exam)
            db.session.commit()
            exam_id = exam.id
            
            # 创建已提交的考试提交记录
            submission = ExamSubmission(
                exam_id=exam.id,
                user_id=test_user.id,
                status='submitted',
                started_at=datetime.utcnow() - timedelta(minutes=30),
                submitted_at=datetime.utcnow() - timedelta(minutes=10),
                answers=json.dumps({'1': 'answer1'}),
                score=80,
                total_points=100
            )
            db.session.add(submission)
            db.session.commit()
        
        # 尝试重复提交
        answers_data = {
            'answers': {
                '1': 'new_answer'
            }
        }
        
        response = client.post(f'/api/exams/{exam_id}/submit', json=answers_data, headers=headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert data['error'] == 'EXAM_ALREADY_SUBMITTED'
    
    def test_submit_exam_time_expired(self, client, test_user):
        """测试考试时间已过期提交失败"""
        login_response = client.post('/api/auth/login', json={
            'email': test_user.email,
            'password': 'TestUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # 创建测试数据
        with client.application.app_context():
            course = Course(
                name='Test Course',
                description='Test Description',
                course_type='one_to_many',
                teacher_id=test_user.id,
                created_at=datetime.utcnow()
            )
            db.session.add(course)
            db.session.commit()
            
            exam = Exam(
                title='Expired Test Exam',
                description='Expired Test Description',
                course_id=course.id,
                created_by=test_user.id,
                start_time=datetime.utcnow() - timedelta(hours=3),
                end_time=datetime.utcnow() - timedelta(hours=1),
                duration_minutes=120,
                total_points=100,
                status='published',
                created_at=datetime.utcnow()
            )
            db.session.add(exam)
            db.session.commit()
            exam_id = exam.id
            
            # 创建考试提交记录
            submission = ExamSubmission(
                exam_id=exam.id,
                user_id=test_user.id,
                status='in_progress',
                started_at=datetime.utcnow() - timedelta(hours=2),
                answers=json.dumps({}),
                score=0,
                total_points=100
            )
            db.session.add(submission)
            db.session.commit()
        
        # 尝试提交已过期的考试
        answers_data = {
            'answers': {
                '1': 'answer'
            }
        }
        
        response = client.post(f'/api/exams/{exam_id}/submit', json=answers_data, headers=headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert data['error'] == 'EXAM_TIME_EXPIRED'
    
    def test_save_question_answer_invalid_question(self, client, test_user):
        """测试保存无效题目答案失败"""
        login_response = client.post('/api/auth/login', json={
            'email': test_user.email,
            'password': 'TestUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # 创建测试数据
        with client.application.app_context():
            course = Course(
                name='Test Course',
                description='Test Description',
                course_type='one_to_many',
                teacher_id=test_user.id,
                created_at=datetime.utcnow()
            )
            db.session.add(course)
            db.session.commit()
            
            exam = Exam(
                title='Invalid Question Test Exam',
                description='Invalid Question Test Description',
                course_id=course.id,
                created_by=test_user.id,
                start_time=datetime.utcnow() - timedelta(minutes=30),
                end_time=datetime.utcnow() + timedelta(hours=2),
                duration_minutes=120,
                total_points=100,
                status='published',
                created_at=datetime.utcnow()
            )
            db.session.add(exam)
            db.session.commit()
            exam_id = exam.id
            
            # 创建考试提交记录
            submission = ExamSubmission(
                exam_id=exam.id,
                user_id=test_user.id,
                status='in_progress',
                started_at=datetime.utcnow(),
                answers=json.dumps({}),
                score=0,
                total_points=100
            )
            db.session.add(submission)
            db.session.commit()
        
        # 尝试保存不存在题目的答案
        answer_data = {
            'question_id': 99999,  # 不存在的题目ID
            'answer': 'some answer'
        }
        
        response = client.post(f'/api/exams/{exam_id}/answers', json=answer_data, headers=headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert data['error'] == 'QUESTION_NOT_IN_EXAM'
    
    def test_get_exam_submission_not_found(self, client, test_user):
        """测试获取不存在的考试提交状态失败"""
        login_response = client.post('/api/auth/login', json={
            'email': test_user.email,
            'password': 'TestUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # 创建测试数据
        with client.application.app_context():
            course = Course(
                name='Test Course',
                description='Test Description',
                course_type='one_to_many',
                teacher_id=test_user.id,
                created_at=datetime.utcnow()
            )
            db.session.add(course)
            db.session.commit()
            
            exam = Exam(
                title='No Submission Test Exam',
                description='No Submission Test Description',
                course_id=course.id,
                created_by=test_user.id,
                start_time=datetime.utcnow() - timedelta(minutes=30),
                end_time=datetime.utcnow() + timedelta(hours=2),
                duration_minutes=120,
                total_points=100,
                status='published',
                created_at=datetime.utcnow()
            )
            db.session.add(exam)
            db.session.commit()
            exam_id = exam.id
        
        # 尝试获取不存在的提交记录
        response = client.get(f'/api/exams/{exam_id}/submission', headers=headers)
        
        assert response.status_code == 404
        data = response.get_json()
        assert data['success'] is False
        assert data['error'] == 'SUBMISSION_NOT_FOUND'
    
    def test_get_exam_time_remaining_not_found(self, client, test_user):
        """测试获取不存在考试的剩余时间失败"""
        login_response = client.post('/api/auth/login', json={
            'email': test_user.email,
            'password': 'TestUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # 尝试获取不存在考试的剩余时间
        response = client.get('/api/exams/99999/time-remaining', headers=headers)
        
        assert response.status_code == 404
        data = response.get_json()
        assert data['success'] is False
        assert data['error'] == 'EXAM_NOT_FOUND'