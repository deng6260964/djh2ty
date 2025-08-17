import unittest
import json
from datetime import datetime, timedelta
from app import create_app
from app.database import db
from app.models.user import User
from app.models.course import Course
from app.models.practice import Practice
from app.models.practice_session import PracticeSession
from app.models.practice_answer import PracticeAnswer
from app.models.question import Question, QuestionBank
from app.models.practice_question import PracticeQuestion
from app.utils.jwt_middleware import JWTMiddleware


class PracticeSessionsTestCase(unittest.TestCase):
    def setUp(self):
        """测试前的设置"""
        self.app = create_app("testing")
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # 创建数据库表
        db.create_all()
        
        # 创建测试用户
        self.admin_user = User(
            name="admin",
            email="admin@test.com",
            role="admin",
            password_hash="hashed_password"
        )
        
        self.teacher_user = User(
            name="teacher",
            email="teacher@test.com",
            role="teacher",
            password_hash="hashed_password"
        )
        
        self.student_user = User(
            name="student",
            email="student@test.com",
            role="student",
            password_hash="hashed_password"
        )
        
        db.session.add_all([self.admin_user, self.teacher_user, self.student_user])
        db.session.commit()
        
        # 创建测试课程
        self.course = Course(
            name="Test Course",
            description="Test Description",
            course_type="one_to_many",
            teacher_id=self.teacher_user.id
        )
        db.session.add(self.course)
        db.session.commit()
        
        # 创建测试题库
        self.question_bank = QuestionBank(
            name="Test Question Bank",
            description="Test Description",
            category="test",
            difficulty_level="beginner",
            created_by=self.teacher_user.id
        )
        
        db.session.add(self.question_bank)
        db.session.commit()
        
        # 创建测试题目
        self.question = Question(
            question_bank_id=self.question_bank.id,
            question_type="multiple_choice",
            title="Test Question",
            content="Test question content?",
            correct_answer="A",
            points=10,
            difficulty_level="beginner",
            created_by=self.teacher_user.id
        )
        db.session.add(self.question)
        db.session.commit()
        
        # 创建测试练习
        self.practice = Practice(
            title="Test Practice",
            description="Test practice description",
            course_id=self.course.id,
            creator_id=self.teacher_user.id,
            settings={"time_limit": 60, "show_answer": True}
        )
        db.session.add(self.practice)
        db.session.commit()
        
        # 创建练习题目关联
        self.practice_question = PracticeQuestion(
            practice_id=self.practice.id,
            question_id=self.question.id,
            order_index=1
        )
        db.session.add(self.practice_question)
        db.session.commit()
        
        # 生成JWT tokens
        jwt_middleware = JWTMiddleware()
        admin_tokens = jwt_middleware.generate_tokens(self.admin_user)
        teacher_tokens = jwt_middleware.generate_tokens(self.teacher_user)
        student_tokens = jwt_middleware.generate_tokens(self.student_user)
        
        self.admin_token = admin_tokens['access_token']
        self.teacher_token = teacher_tokens['access_token']
        self.student_token = student_tokens['access_token']
    
    def tearDown(self):
        """测试后的清理"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def get_auth_headers(self, token):
        """获取认证头"""
        return {'Authorization': f'Bearer {token}'}
    
    def test_start_practice_session_success(self):
        """测试成功开始练习会话"""
        response = self.client.post(
            f'/api/practice-sessions/{self.practice.id}/start',
            headers=self.get_auth_headers(self.student_token)
        )
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn('session_id', data)
        self.assertEqual(data['practice_id'], self.practice.id)
        self.assertEqual(data['status'], 'active')
        self.assertIn('questions', data)
    
    def test_start_practice_session_not_found(self):
        """测试开始不存在的练习会话"""
        response = self.client.post(
            '/api/practice-sessions/999/start',
            headers=self.get_auth_headers(self.student_token)
        )
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Practice not found')
    
    def test_start_practice_session_already_active(self):
        """测试开始已有活跃会话的练习"""
        # 先创建一个活跃会话
        session = PracticeSession(
            practice_id=self.practice.id,
            user_id=self.student_user.id,
            status='active'
        )
        db.session.add(session)
        db.session.commit()
        
        response = self.client.post(
            f'/api/practice-sessions/{self.practice.id}/start',
            headers=self.get_auth_headers(self.student_token)
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'You already have an active session for this practice')
    
    def test_get_session_status_success(self):
        """测试成功获取会话状态"""
        # 先创建一个会话
        session = PracticeSession(
            practice_id=self.practice.id,
            user_id=self.student_user.id,
            status='active'
        )
        db.session.add(session)
        db.session.commit()
        
        response = self.client.get(
            f'/api/practice-sessions/{session.id}',
            headers=self.get_auth_headers(self.student_token)
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['session_id'], session.id)
        self.assertEqual(data['status'], 'active')
        self.assertEqual(data['practice_id'], self.practice.id)
    
    def test_get_session_status_not_found(self):
        """测试获取不存在的会话状态"""
        response = self.client.get(
            '/api/practice-sessions/999',
            headers=self.get_auth_headers(self.student_token)
        )
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Practice session not found')
    
    def test_get_session_status_unauthorized(self):
        """测试获取其他用户的会话状态"""
        # 创建其他用户的会话
        session = PracticeSession(
            practice_id=self.practice.id,
            user_id=self.teacher_user.id,
            status='active'
        )
        db.session.add(session)
        db.session.commit()
        
        response = self.client.get(
            f'/api/practice-sessions/{session.id}',
            headers=self.get_auth_headers(self.student_token)
        )
        
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Access denied')
    
    def test_pause_practice_session_success(self):
        """测试成功暂停练习会话"""
        # 先创建一个活跃会话
        session = PracticeSession(
            practice_id=self.practice.id,
            user_id=self.student_user.id,
            status='active'
        )
        db.session.add(session)
        db.session.commit()
        
        response = self.client.put(
            f'/api/practice-sessions/{session.id}/pause',
            headers=self.get_auth_headers(self.student_token)
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'paused')
        
        # 验证数据库中的状态
        updated_session = PracticeSession.query.get(session.id)
        self.assertEqual(updated_session.status, 'paused')
        self.assertIsNotNone(updated_session.paused_at)
    
    def test_pause_practice_session_invalid_status(self):
        """测试暂停非活跃状态的会话"""
        # 创建已完成的会话
        session = PracticeSession(
            practice_id=self.practice.id,
            user_id=self.student_user.id,
            status='completed'
        )
        db.session.add(session)
        db.session.commit()
        
        response = self.client.put(
            f'/api/practice-sessions/{session.id}/pause',
            headers=self.get_auth_headers(self.student_token)
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Can only pause active sessions')
    
    def test_resume_practice_session_success(self):
        """测试成功恢复练习会话"""
        # 先创建一个暂停的会话
        session = PracticeSession(
            practice_id=self.practice.id,
            user_id=self.student_user.id,
            status='paused',
            paused_at=datetime.utcnow()
        )
        db.session.add(session)
        db.session.commit()
        
        response = self.client.put(
            f'/api/practice-sessions/{session.id}/resume',
            headers=self.get_auth_headers(self.student_token)
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'active')
        
        # 验证数据库中的状态
        updated_session = PracticeSession.query.get(session.id)
        self.assertEqual(updated_session.status, 'active')
        self.assertIsNone(updated_session.paused_at)
    
    def test_resume_practice_session_invalid_status(self):
        """测试恢复非暂停状态的会话"""
        # 创建活跃的会话
        session = PracticeSession(
            practice_id=self.practice.id,
            user_id=self.student_user.id,
            status='active'
        )
        db.session.add(session)
        db.session.commit()
        
        response = self.client.put(
            f'/api/practice-sessions/{session.id}/resume',
            headers=self.get_auth_headers(self.student_token)
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Can only resume paused sessions')
    
    def test_complete_practice_session_success(self):
        """测试成功完成练习会话"""
        # 先创建一个活跃会话
        session = PracticeSession(
            practice_id=self.practice.id,
            user_id=self.student_user.id,
            status='active'
        )
        db.session.add(session)
        db.session.commit()
        
        response = self.client.put(
            f'/api/practice-sessions/{session.id}/complete',
            headers=self.get_auth_headers(self.student_token)
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'completed')
        
        # 验证数据库中的状态
        updated_session = PracticeSession.query.get(session.id)
        self.assertEqual(updated_session.status, 'completed')
        self.assertIsNotNone(updated_session.completed_at)
    
    def test_complete_practice_session_invalid_status(self):
        """测试完成非活跃/暂停状态的会话"""
        # 创建已完成的会话
        session = PracticeSession(
            practice_id=self.practice.id,
            user_id=self.student_user.id,
            status='completed'
        )
        db.session.add(session)
        db.session.commit()
        
        response = self.client.put(
            f'/api/practice-sessions/{session.id}/complete',
            headers=self.get_auth_headers(self.student_token)
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Can only complete active or paused sessions')
    
    def test_unauthorized_access(self):
        """测试未授权访问"""
        response = self.client.post(f'/api/practice-sessions/{self.practice.id}/start')
        self.assertEqual(response.status_code, 401)
        
        response = self.client.get('/api/practice-sessions/1')
        self.assertEqual(response.status_code, 401)
        
        response = self.client.put('/api/practice-sessions/1/pause')
        self.assertEqual(response.status_code, 401)
        
        response = self.client.put('/api/practice-sessions/1/resume')
        self.assertEqual(response.status_code, 401)
        
        response = self.client.put('/api/practice-sessions/1/complete')
        self.assertEqual(response.status_code, 401)


if __name__ == '__main__':
    unittest.main()