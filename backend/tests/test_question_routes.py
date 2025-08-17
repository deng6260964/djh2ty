import pytest
import json
from datetime import datetime
from app.database import db
from app.models.user import User
from app.models.question import QuestionBank, Question
from app.utils.auth import hash_password
import uuid

class TestQuestionBankRoutes:
    """题库管理路由测试类"""
    
    def test_get_question_banks_success(self, client, admin_user):
        """测试获取题库列表成功"""
        # 创建管理员认证头
        login_response = client.post('/api/auth/login', json={
            'email': admin_user.email,
            'password': 'SuperUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        response = client.get('/api/questions/banks', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'question_banks' in data['data']
        assert 'pagination' in data['data']
        assert isinstance(data['data']['question_banks'], list)
    
    def test_get_question_banks_with_filters(self, client, teacher_user):
        """测试带过滤条件的题库列表"""
        login_response = client.post('/api/auth/login', json={
            'email': teacher_user.email,
            'password': 'EduUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # 创建测试题库
        with client.application.app_context():
            question_bank = QuestionBank(
                name='Test Question Bank',
                description='Test Description',
                category='math',
                difficulty_level='intermediate',
                is_public=True,
                created_by=teacher_user.id,
                created_at=datetime.utcnow()
            )
            db.session.add(question_bank)
            db.session.commit()
        
        # 测试分类过滤
        response = client.get('/api/questions/banks?category=math&page=1&per_page=10', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'question_banks' in data['data']
        for bank in data['data']['question_banks']:
            assert bank['category'] == 'math'
    
    def test_get_question_bank_by_id_success(self, client, teacher_user):
        """测试根据ID获取题库成功"""
        login_response = client.post('/api/auth/login', json={
            'email': teacher_user.email,
            'password': 'EduUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # 创建测试题库
        with client.application.app_context():
            question_bank = QuestionBank(
                name='Test Question Bank Detail',
                description='Test Description Detail',
                category='english',
                difficulty_level='advanced',
                is_public=True,
                created_by=teacher_user.id,
                created_at=datetime.utcnow()
            )
            db.session.add(question_bank)
            db.session.commit()
            bank_id = question_bank.id
        
        response = client.get(f'/api/questions/banks/{bank_id}', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        bank_info = data['data']['question_bank']
        assert bank_info['id'] == bank_id
        assert bank_info['name'] == 'Test Question Bank Detail'
        assert bank_info['category'] == 'english'
    
    def test_get_question_bank_by_id_not_found(self, client, teacher_user):
        """测试获取不存在的题库"""
        login_response = client.post('/api/auth/login', json={
            'email': teacher_user.email,
            'password': 'EduUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        response = client.get('/api/questions/banks/99999', headers=headers)
        
        assert response.status_code == 404
        data = response.get_json()
        assert data['success'] is False
        assert data['error'] == 'QUESTION_BANK_NOT_FOUND'
    
    def test_create_question_bank_success(self, client, teacher_user):
        """测试创建题库成功"""
        login_response = client.post('/api/auth/login', json={
            'email': teacher_user.email,
            'password': 'EduUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        bank_data = {
            'name': 'New Question Bank',
            'description': 'New Question Bank Description',
            'category': 'grammar',
            'difficulty_level': 'beginner',
            'is_public': True
        }
        
        response = client.post('/api/questions/banks', json=bank_data, headers=headers)
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True
        bank_info = data['data']['question_bank']
        assert bank_info['name'] == bank_data['name']
        assert bank_info['description'] == bank_data['description']
        assert bank_info['category'] == bank_data['category']
        assert bank_info['created_by'] == teacher_user.id
        
        # 验证题库已创建
        with client.application.app_context():
            bank = QuestionBank.query.filter_by(name=bank_data['name']).first()
            assert bank is not None
    
    def test_create_question_bank_missing_fields(self, client, teacher_user):
        """测试创建题库时缺少必填字段"""
        login_response = client.post('/api/auth/login', json={
            'email': teacher_user.email,
            'password': 'EduUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        bank_data = {
            'description': 'Missing Name Description'
            # 缺少name字段
        }
        
        response = client.post('/api/questions/banks', json=bank_data, headers=headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert data['error'] == 'MISSING_REQUIRED_FIELDS'
    
    def test_update_question_bank_success(self, client, teacher_user):
        """测试更新题库成功"""
        login_response = client.post('/api/auth/login', json={
            'email': teacher_user.email,
            'password': 'EduUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # 创建测试题库
        with client.application.app_context():
            question_bank = QuestionBank(
                name='Original Bank',
                description='Original Description',
                category='grammar',
                difficulty_level='beginner',
                is_public=False,
                created_by=teacher_user.id,
                created_at=datetime.utcnow()
            )
            db.session.add(question_bank)
            db.session.commit()
            bank_id = question_bank.id
        
        update_data = {
            'name': 'Updated Bank',
            'description': 'Updated Description',
            'difficulty_level': 'advanced',
            'is_public': True
        }
        
        response = client.put(f'/api/questions/banks/{bank_id}', json=update_data, headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        bank_info = data['data']['question_bank']
        assert bank_info['name'] == update_data['name']
        assert bank_info['description'] == update_data['description']
        assert bank_info['difficulty_level'] == update_data['difficulty_level']
        assert bank_info['is_public'] == update_data['is_public']
    
    def test_update_question_bank_permission_denied(self, client, teacher_user, test_user):
        """测试更新他人题库权限被拒绝"""
        # 创建另一个用户的题库
        with client.application.app_context():
            question_bank = QuestionBank(
                name='Other User Bank',
                description='Other User Description',
                category='grammar',
                difficulty_level='beginner',
                is_public=False,
                created_by=test_user.id,  # 其他用户创建
                created_at=datetime.utcnow()
            )
            db.session.add(question_bank)
            db.session.commit()
            bank_id = question_bank.id
        
        # 教师用户尝试更新
        login_response = client.post('/api/auth/login', json={
            'email': teacher_user.email,
            'password': 'EduUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        update_data = {'name': 'Unauthorized Update'}
        
        response = client.put(f'/api/questions/banks/{bank_id}', json=update_data, headers=headers)
        
        assert response.status_code == 403
        data = response.get_json()
        assert data['success'] is False
        assert data['error'] == 'PERMISSION_DENIED'
    
    def test_delete_question_bank_success(self, client, teacher_user):
        """测试删除题库成功"""
        login_response = client.post('/api/auth/login', json={
            'email': teacher_user.email,
            'password': 'EduUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # 创建测试题库
        with client.application.app_context():
            question_bank = QuestionBank(
                name='To Delete Bank',
                description='To Delete Description',
                category='grammar',
                difficulty_level='beginner',
                is_public=False,
                created_by=teacher_user.id,
                created_at=datetime.utcnow()
            )
            db.session.add(question_bank)
            db.session.commit()
            bank_id = question_bank.id
        
        response = client.delete(f'/api/questions/banks/{bank_id}', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['message'] == 'Question bank deleted successfully'
        
        # 验证题库已删除
        with client.application.app_context():
            bank = QuestionBank.query.get(bank_id)
            assert bank is None

class TestQuestionRoutes:
    """题目管理路由测试类"""
    
    def test_get_questions_success(self, client, teacher_user):
        """测试获取题目列表成功"""
        login_response = client.post('/api/auth/login', json={
            'email': teacher_user.email,
            'password': 'EduUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # 创建测试题库和题目
        with client.application.app_context():
            question_bank = QuestionBank(
                name='Test Bank',
                description='Test Description',
                category='grammar',
                difficulty_level='beginner',
                is_public=True,
                created_by=teacher_user.id,
                created_at=datetime.utcnow()
            )
            db.session.add(question_bank)
            db.session.commit()
            bank_id = question_bank.id
            
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
        
        response = client.get(f'/api/questions/banks/{bank_id}/questions', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'questions' in data['data']
        assert 'pagination' in data['data']
        assert isinstance(data['data']['questions'], list)
    
    def test_create_question_success(self, client, teacher_user):
        """测试创建题目成功"""
        login_response = client.post('/api/auth/login', json={
            'email': teacher_user.email,
            'password': 'EduUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # 创建测试题库
        with client.application.app_context():
            question_bank = QuestionBank(
                name='Test Bank for Question',
                description='Test Description',
                category='grammar',
                difficulty_level='beginner',
                is_public=True,
                created_by=teacher_user.id,
                created_at=datetime.utcnow()
            )
            db.session.add(question_bank)
            db.session.commit()
            bank_id = question_bank.id
        
        question_data = {
            'question_bank_id': bank_id,
            'question_type': 'multiple_choice',
            'title': 'New Question',
            'content': 'What is 2+2?',
            'options': ['2', '3', '4', '5'],
            'correct_answer': '4',
            'explanation': '2+2 equals 4',
            'points': 10,
            'difficulty_level': 'beginner',
            'tags': 'math,addition'
        }
        
        response = client.post(f'/api/questions/banks/{bank_id}/questions', json=question_data, headers=headers)
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True
        question_info = data['data']['question']
        assert question_info['title'] == question_data['title']
        assert question_info['content'] == question_data['content']
        assert question_info['question_type'] == question_data['question_type']
        assert question_info['points'] == question_data['points']
    
    def test_create_question_invalid_type(self, client, teacher_user):
        """测试创建题目时使用无效类型"""
        login_response = client.post('/api/auth/login', json={
            'email': teacher_user.email,
            'password': 'EduUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # 创建测试题库
        with client.application.app_context():
            question_bank = QuestionBank(
                name='Test Bank',
                description='Test Description',
                category='grammar',
                difficulty_level='beginner',
                is_public=True,
                created_by=teacher_user.id,
                created_at=datetime.utcnow()
            )
            db.session.add(question_bank)
            db.session.commit()
            bank_id = question_bank.id
        
        question_data = {
            'question_bank_id': bank_id,
            'question_type': 'invalid_type',  # 无效类型
            'title': 'Invalid Question',
            'content': 'Invalid content',
            'points': 10
        }
        
        response = client.post(f'/api/questions/banks/{bank_id}/questions', json=question_data, headers=headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert data['error'] == 'INVALID_QUESTION_TYPE'
    
    def test_update_question_success(self, client, teacher_user):
        """测试更新题目成功"""
        login_response = client.post('/api/auth/login', json={
            'email': teacher_user.email,
            'password': 'EduUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # 创建测试题库和题目
        with client.application.app_context():
            question_bank = QuestionBank(
                name='Test Bank',
                description='Test Description',
                category='grammar',
                difficulty_level='beginner',
                is_public=True,
                created_by=teacher_user.id,
                created_at=datetime.utcnow()
            )
            db.session.add(question_bank)
            db.session.commit()
            
            question = Question(
                question_bank_id=question_bank.id,
                question_type='multiple_choice',
                title='Original Question',
                content='Original content',
                options=json.dumps(['A', 'B', 'C', 'D']),
                correct_answer='A',
                points=5,
                difficulty_level='beginner',
                created_by=teacher_user.id,
                created_at=datetime.utcnow()
            )
            db.session.add(question)
            db.session.commit()
            question_id = question.id
        
        update_data = {
            'title': 'Updated Question',
            'content': 'Updated content',
            'points': 15,
            'difficulty_level': 'intermediate'
        }
        
        response = client.put(f'/api/questions/questions/{question_id}', json=update_data, headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        question_info = data['data']['question']
        assert question_info['title'] == update_data['title']
        assert question_info['content'] == update_data['content']
        assert question_info['points'] == update_data['points']
        assert question_info['difficulty_level'] == update_data['difficulty_level']
    
    def test_delete_question_success(self, client, teacher_user):
        """测试删除题目成功"""
        login_response = client.post('/api/auth/login', json={
            'email': teacher_user.email,
            'password': 'EduUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # 创建测试题库和题目
        with client.application.app_context():
            question_bank = QuestionBank(
                name='Test Bank',
                description='Test Description',
                category='math',
                difficulty_level='beginner',
                is_public=True,
                created_by=teacher_user.id,
                created_at=datetime.utcnow()
            )
            db.session.add(question_bank)
            db.session.commit()
            
            question = Question(
                question_bank_id=question_bank.id,
                question_type='multiple_choice',
                title='To Delete Question',
                content='To delete content',
                options=json.dumps(['A', 'B', 'C', 'D']),
                correct_answer='A',
                points=10,
                difficulty_level='beginner',
                created_by=teacher_user.id,
                created_at=datetime.utcnow()
            )
            db.session.add(question)
            db.session.commit()
            question_id = question.id
        
        response = client.delete(f'/api/questions/questions/{question_id}', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['message'] == '题目删除成功'
        
        # 验证题目已删除
        with client.application.app_context():
            question = Question.query.get(question_id)
            assert question is None

class TestQuestionFunctionRoutes:
    """题库功能路由测试类"""
    
    def test_random_draw_questions_success(self, client, teacher_user):
        """测试随机抽题成功"""
        login_response = client.post('/api/auth/login', json={
            'email': teacher_user.email,
            'password': 'EduUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # 创建测试题库和多个题目
        with client.application.app_context():
            question_bank = QuestionBank(
                name='Random Draw Bank',
                description='Test Description',
                category='grammar',
                difficulty_level='beginner',
                is_public=True,
                created_by=teacher_user.id,
                created_at=datetime.utcnow()
            )
            db.session.add(question_bank)
            db.session.commit()
            
            # 创建多个题目
            for i in range(5):
                question = Question(
                    question_bank_id=question_bank.id,
                    question_type='multiple_choice',
                    title=f'Question {i+1}',
                    content=f'Content {i+1}',
                    options=json.dumps(['A', 'B', 'C', 'D']),
                    correct_answer='A',
                    points=10,
                    difficulty_level='beginner',
                    created_by=teacher_user.id,
                    created_at=datetime.utcnow()
                )
                db.session.add(question)
            db.session.commit()
            bank_id = question_bank.id
        
        draw_data = {
            'count': 3
        }
        
        response = client.post(f'/api/questions/banks/{bank_id}/random', json=draw_data, headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        questions = data['data']['questions']
        assert len(questions) == 3
        assert isinstance(questions, list)
    
    def test_generate_paper_success(self, client, teacher_user):
        """测试生成试卷成功"""
        login_response = client.post('/api/auth/login', json={
            'email': teacher_user.email,
            'password': 'EduUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # 创建测试题库和题目
        with client.application.app_context():
            question_bank = QuestionBank(
                name='Paper Generation Bank',
                description='Test Description',
                category='grammar',
                difficulty_level='beginner',
                is_public=True,
                created_by=teacher_user.id,
                created_at=datetime.utcnow()
            )
            db.session.add(question_bank)
            db.session.commit()
            
            # 创建不同类型的题目
            for i in range(3):
                question = Question(
                    question_bank_id=question_bank.id,
                    question_type='multiple_choice',
                    title=f'Single Choice {i+1}',
                    content=f'Content {i+1}',
                    options=json.dumps(['A', 'B', 'C', 'D']),
                    correct_answer='A',
                    points=10,
                    difficulty_level='beginner',
                    created_by=teacher_user.id,
                    created_at=datetime.utcnow()
                )
                db.session.add(question)
            
            for i in range(2):
                question = Question(
                    question_bank_id=question_bank.id,
                    question_type='essay',
                    title=f'Essay {i+1}',
                    content=f'Essay Content {i+1}',
                    points=20,
                    difficulty_level='intermediate',
                    created_by=teacher_user.id,
                    created_at=datetime.utcnow()
                )
                db.session.add(question)
            
            db.session.commit()
            bank_id = question_bank.id
        
        paper_data = {
            'title': 'Test Paper',
            'question_configs': [
                {
                    'bank_id': bank_id,
                    'question_type': 'multiple_choice',
                    'count': 2,
                    'difficulty': 'beginner'
                },
                {
                    'bank_id': bank_id,
                    'question_type': 'essay',
                    'count': 1,
                    'difficulty': 'intermediate'
                }
            ]
        }
        
        response = client.post('/api/questions/papers/generate', json=paper_data, headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        paper = data['data']['paper']
        assert 'questions' in paper
        assert 'total_points' in paper
        assert len(paper['questions']) == 3  # 2个单选 + 1个问答
        assert paper['total_points'] == 40  # 2*10 + 1*20
    
    def test_generate_paper_insufficient_questions(self, client, teacher_user):
        """测试生成试卷时题目数量不足"""
        login_response = client.post('/api/auth/login', json={
            'email': teacher_user.email,
            'password': 'EduUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # 创建测试题库但只有少量题目
        with client.application.app_context():
            question_bank = QuestionBank(
                name='Insufficient Bank',
                description='Test Description',
                category='grammar',
                difficulty_level='beginner',
                is_public=True,
                created_by=teacher_user.id,
                created_at=datetime.utcnow()
            )
            db.session.add(question_bank)
            db.session.commit()
            
            # 只创建1个题目
            question = Question(
                question_bank_id=question_bank.id,
                question_type='multiple_choice',
                title='Only Question',
                content='Only Content',
                options=json.dumps(['A', 'B', 'C', 'D']),
                correct_answer='A',
                points=10,
                difficulty_level='beginner',
                created_by=teacher_user.id,
                created_at=datetime.utcnow()
            )
            db.session.add(question)
            db.session.commit()
            bank_id = question_bank.id
        
        paper_data = {
            'title': 'Test Paper',
            'question_configs': [
                {
                    'bank_id': bank_id,
                    'question_type': 'multiple_choice',
                    'count': 5,  # 要求5个题目但只有1个
                    'difficulty': 'beginner'
                }
            ]
        }
        
        response = client.post('/api/questions/papers/generate', json=paper_data, headers=headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert data['error'] == 'INSUFFICIENT_QUESTIONS'
    
    def test_unauthorized_access(self, client):
        """测试未认证访问"""
        response = client.get('/api/questions/banks')
        
        assert response.status_code == 401
        data = response.get_json()
        assert 'error' in data
        assert data['error'] == 'Authorization token required'
    
    def test_student_access_private_bank(self, client, test_user, teacher_user):
        """测试学生访问私有题库被拒绝"""
        # 创建私有题库
        with client.application.app_context():
            question_bank = QuestionBank(
                name='Private Bank',
                description='Private Description',
                category='grammar',
                difficulty_level='beginner',
                is_public=False,  # 私有题库
                created_by=teacher_user.id,
                created_at=datetime.utcnow()
            )
            db.session.add(question_bank)
            db.session.commit()
            bank_id = question_bank.id
        
        # 学生用户尝试访问
        login_response = client.post('/api/auth/login', json={
            'email': test_user.email,
            'password': 'TestPass123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        response = client.get(f'/api/questions/banks/{bank_id}', headers=headers)
        
        assert response.status_code == 403
        data = response.get_json()
        assert data['success'] is False
        assert data['error'] == 'ACCESS_DENIED'