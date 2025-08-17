import unittest
import json
from datetime import datetime, timedelta
from app import create_app
from app.database import db
from app.models.user import User
from app.models.course import Course
from app.models.question import Question
from app.models.practice import Practice
from app.models.practice_question import PracticeQuestion
from app.models.practice_session import PracticeSession
from app.models.practice_answer import PracticeAnswer
from app.models.question import QuestionBank
from flask_jwt_extended import create_access_token

class TestPracticeStatistics(unittest.TestCase):
    """练习统计API测试"""
    
    def setUp(self):
        """测试前设置"""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        
        # 创建数据库表
        db.create_all()
        
        # 创建测试用户
        self.admin_user = User(
            name='admin_test',
            email='admin@test.com',
            password_hash='hashed_password',
            role='admin'
        )
        # 密码已在创建时设置
        
        self.teacher_user = User(
            name='teacher_test',
            email='teacher@test.com',
            password_hash='hashed_password',
            role='teacher'
        )
        # 密码已在创建时设置
        
        self.student_user = User(
            name='student_test',
            email='student@test.com',
            password_hash='hashed_password',
            role='student'
        )
        # 密码已在创建时设置
        
        db.session.add_all([self.admin_user, self.teacher_user, self.student_user])
        db.session.commit()
        
        # 创建测试课程
        self.course = Course(
            name='Test Course',
            description='Test Description',
            teacher_id=self.teacher_user.id,
            is_active=True,
            course_type='one_to_many'
        )
        db.session.add(self.course)
        db.session.commit()
        
        # 创建测试题库
        self.question_bank = QuestionBank(
            name='Test Question Bank',
            description='Test Description',
            category='test',
            difficulty_level='intermediate',
            is_public=True,
            created_by=self.teacher_user.id
        )
        db.session.add(self.question_bank)
        db.session.commit()
        
        # 创建测试题目
        self.questions = []
        for i in range(5):
            question = Question(
                question_bank_id=self.question_bank.id,
                title=f'Test Question {i+1}',
                content=f'Question content {i+1}',
                question_type='multiple_choice',
                difficulty_level='intermediate',
                correct_answer='A',
                options=json.dumps(['A', 'B', 'C', 'D']),
                explanation=f'Explanation {i+1}',
                created_by=self.teacher_user.id
            )
            self.questions.append(question)
        
        db.session.add_all(self.questions)
        db.session.commit()
        
        # 创建测试练习
        self.practice = Practice(
            title='Test Practice',
            description='Test Practice Description',
            course_id=self.course.id,
            creator_id=self.teacher_user.id,
            status='published',
            settings={
                'time_limit': 60,
                'max_attempts': 3
            }
        )
        db.session.add(self.practice)
        db.session.commit()
        
        # 创建练习题目关联
        for i, question in enumerate(self.questions):
            pq = PracticeQuestion(
                practice_id=self.practice.id,
                question_id=question.id,
                order_index=i
            )
            db.session.add(pq)
        
        db.session.commit()
        
        # 创建测试会话和答案
        self.session = PracticeSession(
            practice_id=self.practice.id,
            user_id=self.student_user.id,
            status='completed',
            started_at=datetime.utcnow() - timedelta(hours=1),
            completed_at=datetime.utcnow(),
            current_question_index=5,
            total_questions=5,
            answered_questions=5,
            correct_answers=3,
            total_time_spent=1800  # 30分钟
        )
        db.session.add(self.session)
        db.session.commit()
        
        # 创建答案记录
        practice_questions = PracticeQuestion.query.filter_by(practice_id=self.practice.id).all()
        for i, pq in enumerate(practice_questions):
            answer = PracticeAnswer(
                practice_session_id=self.session.id,
                practice_question_id=pq.id,
                user_id=self.student_user.id,
                answer_content='A' if i < 3 else 'B',  # 前3个正确，后2个错误
                is_correct=i < 3,
                time_spent=300 + i * 60,  # 递增时间
                submitted_at=datetime.utcnow() - timedelta(minutes=30-i*5)
            )
            db.session.add(answer)
        
        db.session.commit()
        
        # 生成JWT令牌 - 使用与jwt_middleware相同的格式
        self.admin_token = create_access_token(
            identity=str(self.admin_user.id),
            additional_claims={
                'role': self.admin_user.role,  # role字段已经是字符串
                'email': self.admin_user.email,
                'is_active': self.admin_user.is_active
            }
        )
        self.teacher_token = create_access_token(
            identity=str(self.teacher_user.id),
            additional_claims={
                'role': self.teacher_user.role,  # role字段已经是字符串
                'email': self.teacher_user.email,
                'is_active': self.teacher_user.is_active
            }
        )
        self.student_token = create_access_token(
            identity=str(self.student_user.id),
            additional_claims={
                'role': self.student_user.role,  # role字段已经是字符串
                'email': self.student_user.email,
                'is_active': self.student_user.is_active
            }
        )
    
    def tearDown(self):
        """测试后清理"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_get_practice_statistics_success(self):
        """测试获取练习统计报告成功"""
        response = self.client.get(
            f'/api/practices/{self.practice.id}/statistics',
            headers={'Authorization': f'Bearer {self.teacher_token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertTrue(data['success'])
        self.assertIn('data', data)
        
        stats = data['data']
        self.assertEqual(stats['practice_id'], str(self.practice.id))
        self.assertEqual(stats['practice_title'], 'Test Practice')
        self.assertEqual(stats['total_participants'], 1)
        self.assertEqual(stats['completion_rate'], 100.0)
        self.assertEqual(stats['average_score'], 60.0)
        self.assertGreater(stats['average_time'], 0)
        self.assertIsInstance(stats['time_analysis'], dict)
        self.assertIsInstance(stats['score_distribution'], list)
        self.assertIsInstance(stats['question_analysis'], list)
    
    def test_get_practice_statistics_not_found(self):
        """测试获取不存在练习的统计报告"""
        response = self.client.get(
            '/api/practices/999/statistics',
            headers={'Authorization': f'Bearer {self.teacher_token}'}
        )
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
    
    def test_get_practice_statistics_no_permission(self):
        """测试无权限获取练习统计报告"""
        response = self.client.get(
            f'/api/practices/{self.practice.id}/statistics',
            headers={'Authorization': f'Bearer {self.student_token}'}
        )
        
        self.assertEqual(response.status_code, 403)
    
    def test_get_user_practice_history_success(self):
        """测试获取用户练习历史成功"""
        response = self.client.get(
            f'/api/users/{self.student_user.id}/practice-history',
            headers={'Authorization': f'Bearer {self.teacher_token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertTrue(data['success'])
        self.assertIn('data', data)
        
        result = data['data']
        self.assertIn('history', result)
        self.assertIn('pagination', result)
        
        history = result['history']
        self.assertEqual(len(history), 1)
        
        session_data = history[0]
        self.assertEqual(session_data['session_id'], str(self.session.id))
        self.assertEqual(session_data['practice_title'], 'Test Practice')
        self.assertEqual(session_data['status'], 'completed')
        self.assertEqual(session_data['completion_rate'], 0.6)
    
    def test_get_user_practice_history_with_filters(self):
        """测试带过滤条件获取用户练习历史"""
        response = self.client.get(
            f'/api/users/{self.student_user.id}/practice-history?course_id={self.course.id}&page=1&per_page=10',
            headers={'Authorization': f'Bearer {self.teacher_token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertTrue(data['success'])
        result = data['data']
        self.assertEqual(len(result['history']), 1)
        self.assertEqual(result['pagination']['page'], 1)
        self.assertEqual(result['pagination']['per_page'], 10)
    
    def test_get_user_practice_statistics_success(self):
        """测试获取用户个人统计成功"""
        response = self.client.get(
            f'/api/users/{self.student_user.id}/practice-statistics',
            headers={'Authorization': f'Bearer {self.teacher_token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertTrue(data['success'])
        self.assertIn('data', data)
        
        stats = data['data']
        self.assertEqual(stats['user_id'], str(self.student_user.id))
        self.assertEqual(stats['total_practices'], 1)
        self.assertEqual(stats['completed_practices'], 1)
        self.assertEqual(stats['completion_rate'], 100.0)
        self.assertEqual(stats['average_score'], 60.0)
        self.assertGreater(stats['total_time_spent'], 0)
        self.assertIsInstance(stats['strengths'], list)
        self.assertIsInstance(stats['weaknesses'], list)
        self.assertIsInstance(stats['recent_activity'], list)
    
    def test_get_user_wrong_questions_success(self):
        """测试获取用户错题集成功"""
        response = self.client.get(
            f'/api/users/{self.student_user.id}/wrong-questions',
            headers={'Authorization': f'Bearer {self.teacher_token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertTrue(data['success'])
        self.assertIn('data', data)
        
        result = data['data']
        self.assertIn('wrong_questions', result)
        self.assertIn('total_count', result)
        
        wrong_questions = result['wrong_questions']
        self.assertEqual(len(wrong_questions), 2)  # 有2个错题
        
        for question in wrong_questions:
            self.assertIn('question_id', question)
            self.assertIn('question_title', question)
            self.assertIn('error_count', question)
            self.assertGreater(question['error_count'], 0)
    
    def test_get_user_wrong_questions_with_filters(self):
        """测试带过滤条件获取用户错题集"""
        response = self.client.get(
            f'/api/users/{self.student_user.id}/wrong-questions?question_type=single_choice&difficulty=medium',
            headers={'Authorization': f'Bearer {self.teacher_token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertTrue(data['success'])
        result = data['data']
        self.assertEqual(len(result['wrong_questions']), 2)
    
    def test_generate_review_practice_success(self):
        """测试生成复习练习成功"""
        request_data = {
            'question_count': 5,
            'difficulty_range': ['medium'],
            'question_types': ['single_choice']
        }
        
        response = self.client.post(
            f'/api/users/{self.student_user.id}/generate-review-practice',
            data=json.dumps(request_data),
            content_type='application/json',
            headers={'Authorization': f'Bearer {self.teacher_token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertTrue(data['success'])
        self.assertIn('data', data)
        
        result = data['data']
        self.assertIn('review_questions', result)
        self.assertIn('total_count', result)
        self.assertIn('wrong_question_count', result)
        self.assertIn('recommendation_strategy', result)
        
        review_questions = result['review_questions']
        self.assertLessEqual(len(review_questions), 5)
        
        for question in review_questions:
            self.assertIn('question_id', question)
            self.assertIn('title', question)
            self.assertIn('priority', question)
            self.assertIn('is_wrong_question', question)
    
    def test_generate_review_practice_invalid_count(self):
        """测试生成复习练习参数无效"""
        request_data = {
            'question_count': 100,  # 超过限制
            'difficulty_range': ['medium'],
            'question_types': ['single_choice']
        }
        
        response = self.client.post(
            f'/api/users/{self.student_user.id}/generate-review-practice',
            data=json.dumps(request_data),
            content_type='application/json',
            headers={'Authorization': f'Bearer {self.teacher_token}'}
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
    
    def test_user_not_found(self):
        """测试用户不存在的情况"""
        response = self.client.get(
            '/api/users/999/practice-history',
            headers={'Authorization': f'Bearer {self.teacher_token}'}
        )
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
    
    def test_unauthorized_access(self):
        """测试未授权访问"""
        response = self.client.get(
            f'/api/practices/{self.practice.id}/statistics'
        )
        
        self.assertEqual(response.status_code, 401)

if __name__ == '__main__':
    unittest.main()