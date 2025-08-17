import unittest
import json
from datetime import datetime
from app import create_app
from app.database import db
from app.models.user import User
from app.models.course import Course
from app.models.practice import Practice
from app.models.practice_question import PracticeQuestion
from app.models.practice_session import PracticeSession
from app.models.practice_answer import PracticeAnswer
from app.models.question import QuestionBank, Question
from flask_jwt_extended import create_access_token


class PracticeAPITestCase(unittest.TestCase):
    """练习API测试用例"""

    def setUp(self):
        """测试前设置"""
        self.app = create_app("testing")
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # 创建数据库表
        db.create_all()
        
        # 创建测试用户
        self.admin_user = User(
            name="admin_test",
            email="admin@test.com",
            password_hash="hashed_password",
            role="admin",
            is_active=True
        )
        self.teacher_user = User(
            name="teacher_test",
            email="teacher@test.com",
            password_hash="hashed_password",
            role="teacher",
            is_active=True
        )
        self.student_user = User(
            name="student_test",
            email="student@test.com",
            password_hash="hashed_password",
            role="student",
            is_active=True
        )
        
        db.session.add_all([self.admin_user, self.teacher_user, self.student_user])
        db.session.commit()
        
        # 创建测试课程
        self.course = Course(
            name="测试课程",
            description="测试课程描述",
            course_type="one_to_many",
            teacher_id=self.teacher_user.id,
            max_students=1
        )
        db.session.add(self.course)
        db.session.commit()
        
        # 创建测试题库和题目
        self.question_bank = QuestionBank(
            name="测试题库",
            description="测试题库描述",
            category="编程",
            difficulty_level="intermediate",
            created_by=self.teacher_user.id
        )
        db.session.add(self.question_bank)
        db.session.commit()
        
        self.question = Question(
            question_bank_id=self.question_bank.id,
            title="测试题目标题",
            content="测试题目内容",
            question_type="single_choice",
            options=json.dumps(["选项A", "选项B", "选项C", "选项D"]),
            correct_answer="A",
            explanation="正确答案解析",
            difficulty_level="medium",
            points=10,
            created_by=self.teacher_user.id
        )
        db.session.add(self.question)
        db.session.commit()
        
        # 创建测试练习
        self.practice = Practice(
            title="测试练习",
            description="测试练习描述",
            course_id=self.course.id,
            creator_id=self.teacher_user.id,
            status="published",
            settings={"time_limit": 60, "show_answer": True}
        )
        db.session.add(self.practice)
        db.session.commit()
        
        # 生成JWT令牌
        from app.utils.jwt_middleware import JWTMiddleware
        jwt_middleware = JWTMiddleware()
        
        with self.app.app_context():
            admin_tokens = jwt_middleware.generate_tokens(self.admin_user)
            teacher_tokens = jwt_middleware.generate_tokens(self.teacher_user)
            student_tokens = jwt_middleware.generate_tokens(self.student_user)
            
            self.admin_token = admin_tokens['access_token']
            self.teacher_token = teacher_tokens['access_token']
            self.student_token = student_tokens['access_token']

    def tearDown(self):
        """测试后清理"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def get_auth_headers(self, token):
        """获取认证头"""
        return {"Authorization": f"Bearer {token}"}

    def test_get_practices_as_admin(self):
        """测试管理员获取练习列表"""
        response = self.client.get(
            "/api/practices/",
            headers=self.get_auth_headers(self.admin_token)
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data["success"])
        self.assertIn("practices", data["data"])
        self.assertIn("pagination", data["data"])

    def test_get_practices_as_teacher(self):
        """测试教师获取练习列表"""
        response = self.client.get(
            "/api/practices/",
            headers=self.get_auth_headers(self.teacher_token)
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data["success"])
        self.assertEqual(len(data["data"]["practices"]), 1)

    def test_get_practices_as_student(self):
        """测试学生获取练习列表"""
        response = self.client.get(
            "/api/practices/",
            headers=self.get_auth_headers(self.student_token)
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data["success"])
        # 学生只能看到已发布的练习
        self.assertEqual(len(data["data"]["practices"]), 1)

    def test_create_practice_as_teacher(self):
        """测试教师创建练习"""
        practice_data = {
            "title": "新练习",
            "description": "新练习描述",
            "course_id": self.course.id,
            "settings": {"time_limit": 30, "show_answer": False}
        }
        
        response = self.client.post(
            "/api/practices/",
            data=json.dumps(practice_data),
            content_type="application/json",
            headers=self.get_auth_headers(self.teacher_token)
        )
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["practice"]["title"], "新练习")
        self.assertEqual(data["data"]["practice"]["status"], "draft")

    def test_create_practice_missing_fields(self):
        """测试创建练习缺少必填字段"""
        practice_data = {
            "description": "缺少标题的练习"
        }
        
        response = self.client.post(
            "/api/practices/",
            data=json.dumps(practice_data),
            content_type="application/json",
            headers=self.get_auth_headers(self.teacher_token)
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data["success"])
        self.assertEqual(data["error"], "MISSING_FIELD")

    def test_create_practice_invalid_course(self):
        """测试创建练习时课程不存在"""
        practice_data = {
            "title": "无效课程练习",
            "course_id": 99999
        }
        
        response = self.client.post(
            "/api/practices/",
            data=json.dumps(practice_data),
            content_type="application/json",
            headers=self.get_auth_headers(self.teacher_token)
        )
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertFalse(data["success"])
        self.assertEqual(data["error"], "COURSE_NOT_FOUND")

    def test_get_practice_detail(self):
        """测试获取练习详情"""
        response = self.client.get(
            f"/api/practices/{self.practice.id}",
            headers=self.get_auth_headers(self.teacher_token)
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["practice"]["id"], self.practice.id)
        self.assertEqual(data["data"]["practice"]["title"], "测试练习")

    def test_get_practice_not_found(self):
        """测试获取不存在的练习"""
        response = self.client.get(
            "/api/practices/99999",
            headers=self.get_auth_headers(self.teacher_token)
        )
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertFalse(data["success"])
        self.assertEqual(data["error"], "PRACTICE_NOT_FOUND")

    def test_update_practice(self):
        """测试更新练习"""
        update_data = {
            "title": "更新后的练习标题",
            "description": "更新后的描述",
            "status": "archived"
        }
        
        response = self.client.put(
            f"/api/practices/{self.practice.id}",
            data=json.dumps(update_data),
            content_type="application/json",
            headers=self.get_auth_headers(self.teacher_token)
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["practice"]["title"], "更新后的练习标题")
        self.assertEqual(data["data"]["practice"]["status"], "archived")

    def test_update_practice_access_denied(self):
        """测试非创建者更新练习被拒绝"""
        # 创建另一个教师
        other_teacher = User(
            name="other_teacher",
            email="other@test.com",
            password_hash="hashed_password",
            role="teacher",
            is_active=True
        )
        db.session.add(other_teacher)
        db.session.commit()
        
        from app.utils.jwt_middleware import JWTMiddleware
        jwt_middleware = JWTMiddleware()
        
        with self.app.app_context():
            other_tokens = jwt_middleware.generate_tokens(other_teacher)
            other_token = other_tokens['access_token']
        
        update_data = {"title": "尝试更新"}
        
        response = self.client.put(
            f"/api/practices/{self.practice.id}",
            data=json.dumps(update_data),
            content_type="application/json",
            headers=self.get_auth_headers(other_token)
        )
        
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.data)
        self.assertFalse(data["success"])
        self.assertEqual(data["error"], "ACCESS_DENIED")

    def test_delete_practice(self):
        """测试删除练习"""
        response = self.client.delete(
            f"/api/practices/{self.practice.id}",
            headers=self.get_auth_headers(self.teacher_token)
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data["success"])
        
        # 验证练习已被删除
        deleted_practice = Practice.query.get(self.practice.id)
        self.assertIsNone(deleted_practice)

    def test_delete_practice_with_active_sessions(self):
        """测试删除有活跃会话的练习"""
        # 创建活跃的练习会话
        session = PracticeSession(
            practice_id=self.practice.id,
            user_id=self.student_user.id,
            status="in_progress"
        )
        db.session.add(session)
        db.session.commit()
        
        response = self.client.delete(
            f"/api/practices/{self.practice.id}",
            headers=self.get_auth_headers(self.teacher_token)
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data["success"])
        self.assertEqual(data["error"], "PRACTICE_IN_USE")

    def test_search_practices(self):
        """测试搜索练习"""
        response = self.client.get(
            "/api/practices/?search=测试",
            headers=self.get_auth_headers(self.teacher_token)
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data["success"])
        self.assertEqual(len(data["data"]["practices"]), 1)

    def test_filter_practices_by_status(self):
        """测试按状态过滤练习"""
        response = self.client.get(
            "/api/practices/?status=published",
            headers=self.get_auth_headers(self.teacher_token)
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data["success"])
        self.assertEqual(len(data["data"]["practices"]), 1)
        self.assertEqual(data["data"]["practices"][0]["status"], "published")

    def test_unauthorized_access(self):
        """测试未授权访问"""
        response = self.client.get("/api/practices/")
        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()