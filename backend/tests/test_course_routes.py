import pytest
import json
from datetime import datetime, timedelta
from app.database import db
from app.models.user import User
from app.models.course import Course, CourseEnrollment
from app.utils.auth import hash_password
import uuid

class TestCourseRoutes:
    """课程管理路由测试类"""
    
    def test_get_courses_success(self, client, admin_user):
        """测试获取课程列表成功"""
        # 创建管理员认证头
        login_response = client.post('/api/auth/login', json={
            'email': admin_user.email,
            'password': 'SuperUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        response = client.get('/api/courses', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'courses' in data['data']
        assert 'pagination' in data['data']
        assert isinstance(data['data']['courses'], list)
    
    def test_get_courses_with_filters(self, client, teacher_user):
        """测试带过滤条件的课程列表"""
        login_response = client.post('/api/auth/login', json={
            'email': teacher_user.email,
            'password': 'EduUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # 创建测试课程
        with client.application.app_context():
            course = Course(
                name='Test Course',
                description='Test Description',
                course_type='one_on_one',
                max_students=1,
                teacher_id=teacher_user.id,
                is_active=True,
                created_at=datetime.utcnow()
            )
            db.session.add(course)
            db.session.commit()
        
        # 测试课程类型过滤
        response = client.get('/api/courses?course_type=one_on_one&page=1&per_page=10', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'courses' in data['data']
        for course in data['data']['courses']:
            assert course['course_type'] == 'one_on_one'
    
    def test_get_course_by_id_success(self, client, teacher_user):
        """测试根据ID获取课程成功"""
        login_response = client.post('/api/auth/login', json={
            'email': teacher_user.email,
            'password': 'EduUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # 创建测试课程
        with client.application.app_context():
            course = Course(
                name='Test Course Detail',
                description='Test Description Detail',
                course_type='one_to_many',
                max_students=3,
                teacher_id=teacher_user.id,
                is_active=True,
                created_at=datetime.utcnow()
            )
            db.session.add(course)
            db.session.commit()
            course_id = course.id
        
        response = client.get(f'/api/courses/{course_id}', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        course_info = data['data']['course']
        assert course_info['id'] == course_id
        assert course_info['name'] == 'Test Course Detail'
        assert course_info['course_type'] == 'one_to_many'
    
    def test_get_course_by_id_not_found(self, client, teacher_user):
        """测试获取不存在的课程"""
        login_response = client.post('/api/auth/login', json={
            'email': teacher_user.email,
            'password': 'EduUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        response = client.get('/api/courses/99999', headers=headers)
        
        assert response.status_code == 404
        data = response.get_json()
        assert data['success'] is False
        assert data['error'] == 'COURSE_NOT_FOUND'
    
    def test_create_course_success(self, client, teacher_user):
        """测试创建课程成功"""
        login_response = client.post('/api/auth/login', json={
            'email': teacher_user.email,
            'password': 'EduUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        course_data = {
            'name': 'New Course',
            'description': 'New Course Description',
            'course_type': 'one_on_one',
            'max_students': 1
        }
        
        response = client.post('/api/courses', json=course_data, headers=headers)
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True
        course_info = data['data']['course']
        assert course_info['name'] == course_data['name']
        assert course_info['description'] == course_data['description']
        assert course_info['course_type'] == course_data['course_type']
        assert course_info['teacher_id'] == teacher_user.id
        
        # 验证课程已创建
        with client.application.app_context():
            course = Course.query.filter_by(name=course_data['name']).first()
            assert course is not None
            assert course.is_active is True
    
    def test_create_course_invalid_type(self, client, teacher_user):
        """测试创建课程时使用无效类型"""
        login_response = client.post('/api/auth/login', json={
            'email': teacher_user.email,
            'password': 'EduUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        course_data = {
            'name': 'Invalid Type Course',
            'description': 'Invalid Type Description',
            'course_type': 'invalid_type',
            'max_students': 1
        }
        
        response = client.post('/api/courses', json=course_data, headers=headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert data['error'] == 'INVALID_COURSE_TYPE'
    
    def test_create_course_invalid_max_students(self, client, teacher_user):
        """测试创建课程时使用无效最大学生数"""
        login_response = client.post('/api/auth/login', json={
            'email': teacher_user.email,
            'password': 'EduUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # 测试一对多课程超过3人限制
        course_data = {
            'name': 'Too Many Students Course',
            'description': 'Too Many Students Description',
            'course_type': 'one_to_many',
            'max_students': 5  # 超过3人限制
        }
        
        response = client.post('/api/courses', json=course_data, headers=headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert data['error'] == 'INVALID_MAX_STUDENTS'
    
    def test_update_course_success(self, client, teacher_user):
        """测试更新课程成功"""
        login_response = client.post('/api/auth/login', json={
            'email': teacher_user.email,
            'password': 'EduUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # 创建测试课程
        with client.application.app_context():
            course = Course(
                name='Original Course',
                description='Original Description',
                course_type='one_on_one',
                max_students=1,
                teacher_id=teacher_user.id,
                is_active=True,
                created_at=datetime.utcnow()
            )
            db.session.add(course)
            db.session.commit()
            course_id = course.id
        
        update_data = {
            'name': 'Updated Course',
            'description': 'Updated Description'
        }
        
        response = client.put(f'/api/courses/{course_id}', json=update_data, headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        course_info = data['data']['course']
        assert course_info['name'] == update_data['name']
        assert course_info['description'] == update_data['description']
    
    def test_update_course_unauthorized(self, client, teacher_user):
        """测试更新其他教师的课程（未授权）"""
        # 创建另一个教师
        with client.application.app_context():
            other_teacher = User(
                email=f'other_teacher_{uuid.uuid4().hex[:8]}@example.com',
                name='Other Teacher',
                password_hash=hash_password('OtherTeacher123!'),
                role='teacher',
                is_active=True,
                created_at=datetime.utcnow()
            )
            db.session.add(other_teacher)
            db.session.commit()
            
            # 创建其他教师的课程
            course = Course(
                name='Other Teacher Course',
                description='Other Teacher Description',
                course_type='one_on_one',
                max_students=1,
                teacher_id=other_teacher.id,
                is_active=True,
                created_at=datetime.utcnow()
            )
            db.session.add(course)
            db.session.commit()
            course_id = course.id
        
        # 使用第一个教师的token尝试更新其他教师的课程
        login_response = client.post('/api/auth/login', json={
            'email': teacher_user.email,
            'password': 'EduUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        update_data = {
            'name': 'Unauthorized Update'
        }
        
        response = client.put(f'/api/courses/{course_id}', json=update_data, headers=headers)
        
        assert response.status_code == 403
        data = response.get_json()
        assert data['success'] is False
        assert data['error'] == 'ACCESS_DENIED'
    
    def test_delete_course_success(self, client, teacher_user):
        """测试删除课程成功（软删除）"""
        login_response = client.post('/api/auth/login', json={
            'email': teacher_user.email,
            'password': 'EduUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # 创建测试课程
        with client.application.app_context():
            course = Course(
                name='Course to Delete',
                description='Course to Delete Description',
                course_type='one_on_one',
                max_students=1,
                teacher_id=teacher_user.id,
                is_active=True,
                created_at=datetime.utcnow()
            )
            db.session.add(course)
            db.session.commit()
            course_id = course.id
        
        response = client.delete(f'/api/courses/{course_id}', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        
        # 验证课程已软删除
        with client.application.app_context():
            course = Course.query.get(course_id)
            assert course is not None
            assert course.is_active is False
    
    def test_delete_course_with_enrollments(self, client, teacher_user, test_user):
        """测试删除有学生选课的课程（应该失败）"""
        login_response = client.post('/api/auth/login', json={
            'email': teacher_user.email,
            'password': 'EduUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # 创建测试课程和选课记录
        with client.application.app_context():
            course = Course(
                name='Course with Enrollments',
                description='Course with Enrollments Description',
                course_type='one_to_many',
                max_students=3,
                teacher_id=teacher_user.id,
                is_active=True,
                created_at=datetime.utcnow()
            )
            db.session.add(course)
            db.session.commit()
            
            enrollment = CourseEnrollment(
                course_id=course.id,
                student_id=test_user.id,
                is_active=True,
                enrolled_at=datetime.utcnow()
            )
            db.session.add(enrollment)
            db.session.commit()
            course_id = course.id
        
        response = client.delete(f'/api/courses/{course_id}', headers=headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert data['error'] == 'COURSE_HAS_ENROLLMENTS'
    
    def test_enroll_course_success(self, client, teacher_user, test_user):
        """测试选课成功"""
        # 学生登录
        login_response = client.post('/api/auth/login', json={
            'email': test_user.email,
            'password': 'TestPass123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # 创建测试课程
        with client.application.app_context():
            course = Course(
                name='Course for Enrollment',
                description='Course for Enrollment Description',
                course_type='one_to_many',
                max_students=3,
                teacher_id=teacher_user.id,
                is_active=True,
                created_at=datetime.utcnow()
            )
            db.session.add(course)
            db.session.commit()
            course_id = course.id
        
        response = client.post(f'/api/courses/{course_id}/enroll', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        
        # 验证选课记录已创建
        with client.application.app_context():
            enrollment = CourseEnrollment.query.filter_by(
                course_id=course_id, student_id=test_user.id, is_active=True
            ).first()
            assert enrollment is not None
    
    def test_enroll_course_already_enrolled(self, client, teacher_user, test_user):
        """测试重复选课"""
        # 学生登录
        login_response = client.post('/api/auth/login', json={
            'email': test_user.email,
            'password': 'TestPass123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # 创建测试课程和选课记录
        with client.application.app_context():
            course = Course(
                name='Already Enrolled Course',
                description='Already Enrolled Course Description',
                course_type='one_to_many',
                max_students=3,
                teacher_id=teacher_user.id,
                is_active=True,
                created_at=datetime.utcnow()
            )
            db.session.add(course)
            db.session.commit()
            
            enrollment = CourseEnrollment(
                course_id=course.id,
                student_id=test_user.id,
                is_active=True,
                enrolled_at=datetime.utcnow()
            )
            db.session.add(enrollment)
            db.session.commit()
            course_id = course.id
        
        response = client.post(f'/api/courses/{course_id}/enroll', headers=headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert data['error'] == 'ALREADY_ENROLLED'
    
    def test_unenroll_course_success(self, client, teacher_user, test_user):
        """测试退课成功"""
        # 学生登录
        login_response = client.post('/api/auth/login', json={
            'email': test_user.email,
            'password': 'TestPass123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # 创建测试课程和选课记录
        with client.application.app_context():
            course = Course(
                name='Course for Unenrollment',
                description='Course for Unenrollment Description',
                course_type='one_to_many',
                max_students=3,
                teacher_id=teacher_user.id,
                is_active=True,
                created_at=datetime.utcnow()
            )
            db.session.add(course)
            db.session.commit()
            
            enrollment = CourseEnrollment(
                course_id=course.id,
                student_id=test_user.id,
                is_active=True,
                enrolled_at=datetime.utcnow()
            )
            db.session.add(enrollment)
            db.session.commit()
            course_id = course.id
        
        response = client.delete(f'/api/courses/{course_id}/unenroll', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        
        # 验证选课记录已软删除
        with client.application.app_context():
            enrollment = CourseEnrollment.query.filter_by(
                course_id=course_id, student_id=test_user.id
            ).first()
            assert enrollment is not None
            assert enrollment.is_active is False
    
    def test_get_course_students(self, client, teacher_user, test_user):
        """测试获取课程学生列表"""
        # 教师登录
        login_response = client.post('/api/auth/login', json={
            'email': teacher_user.email,
            'password': 'EduUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # 创建测试课程和选课记录
        with client.application.app_context():
            course = Course(
                name='Course with Students',
                description='Course with Students Description',
                course_type='one_to_many',
                max_students=3,
                teacher_id=teacher_user.id,
                is_active=True,
                created_at=datetime.utcnow()
            )
            db.session.add(course)
            db.session.commit()
            
            enrollment = CourseEnrollment(
                course_id=course.id,
                student_id=test_user.id,
                is_active=True,
                enrolled_at=datetime.utcnow()
            )
            db.session.add(enrollment)
            db.session.commit()
            course_id = course.id
        
        response = client.get(f'/api/courses/{course_id}/students', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'students' in data['data']
        assert len(data['data']['students']) == 1
        assert data['data']['students'][0]['id'] == test_user.id
    
    def test_get_my_courses(self, client, teacher_user, test_user):
        """测试获取我的课程"""
        # 学生登录
        login_response = client.post('/api/auth/login', json={
            'email': test_user.email,
            'password': 'TestPass123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # 创建测试课程和选课记录
        with client.application.app_context():
            course = Course(
                name='My Course',
                description='My Course Description',
                course_type='one_to_many',
                max_students=3,
                teacher_id=teacher_user.id,
                is_active=True,
                created_at=datetime.utcnow()
            )
            db.session.add(course)
            db.session.commit()
            
            enrollment = CourseEnrollment(
                course_id=course.id,
                student_id=test_user.id,
                is_active=True,
                enrolled_at=datetime.utcnow()
            )
            db.session.add(enrollment)
            db.session.commit()
        
        response = client.get('/api/courses/my-courses', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'courses' in data['data']
        assert len(data['data']['courses']) == 1
        assert data['data']['courses'][0]['name'] == 'My Course'
    
    def test_update_course_schedule(self, client, teacher_user):
        """测试更新课程时间安排"""
        login_response = client.post('/api/auth/login', json={
            'email': teacher_user.email,
            'password': 'EduUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # 创建测试课程
        with client.application.app_context():
            course = Course(
                name='Schedule Course',
                description='Schedule Course Description',
                course_type='one_on_one',
                max_students=1,
                teacher_id=teacher_user.id,
                is_active=True,
                created_at=datetime.utcnow()
            )
            db.session.add(course)
            db.session.commit()
            course_id = course.id
        
        schedule_data = {
            'schedule': [
                {
                    'day_of_week': 1,  # Monday
                    'start_time': '09:00',
                    'end_time': '10:00'
                },
                {
                    'day_of_week': 3,  # Wednesday
                    'start_time': '14:00',
                    'end_time': '15:00'
                }
            ]
        }
        
        response = client.put(f'/api/courses/{course_id}/schedule', json=schedule_data, headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        
        # 验证时间安排已更新
        with client.application.app_context():
            course = Course.query.get(course_id)
            assert course.schedule is not None
            assert len(course.schedule) == 2
    
    def test_check_schedule_conflicts(self, client, teacher_user):
        """测试检查时间安排冲突"""
        login_response = client.post('/api/auth/login', json={
            'email': teacher_user.email,
            'password': 'EduUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # 创建已有时间安排的课程
        with client.application.app_context():
            course = Course(
                name='Existing Schedule Course',
                description='Existing Schedule Course Description',
                course_type='one_on_one',
                max_students=1,
                teacher_id=teacher_user.id,
                schedule=[
                    {
                        'day_of_week': 1,
                        'start_time': '09:00',
                        'end_time': '10:00'
                    }
                ],
                is_active=True,
                created_at=datetime.utcnow()
            )
            db.session.add(course)
            db.session.commit()
        
        conflict_data = {
            'teacher_id': teacher_user.id,
            'schedule': [
                {
                    'day_of_week': 1,  # Same day
                    'start_time': '09:30',  # Overlapping time
                    'end_time': '10:30'
                }
            ]
        }
        
        response = client.post('/api/courses/schedule/conflicts', json=conflict_data, headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['has_conflicts'] is True
        assert len(data['data']['conflicts']) > 0
    
    def test_get_available_times(self, client, teacher_user):
        """测试获取可用时间段"""
        login_response = client.post('/api/auth/login', json={
            'email': teacher_user.email,
            'password': 'EduUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        response = client.get(f'/api/courses/schedule/available-times?teacher_id={teacher_user.id}', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'available_times' in data['data']
        assert isinstance(data['data']['available_times'], list)
    
    def test_get_course_statistics_overview(self, client, admin_user):
        """测试获取课程统计概览"""
        login_response = client.post('/api/auth/login', json={
            'email': admin_user.email,
            'password': 'SuperUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        response = client.get('/api/courses/statistics/overview', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'total_courses' in data['data']
        assert 'total_enrollments' in data['data']
        assert 'course_types' in data['data']
        assert 'teacher_statistics' in data['data']
    
    def test_get_enrollment_statistics(self, client, admin_user):
        """测试获取选课统计"""
        login_response = client.post('/api/auth/login', json={
            'email': admin_user.email,
            'password': 'SuperUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        response = client.get('/api/courses/statistics/enrollments', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'enrollment_statistics' in data['data']
    
    def test_get_popular_courses(self, client, admin_user):
        """测试获取热门课程统计"""
        login_response = client.post('/api/auth/login', json={
            'email': admin_user.email,
            'password': 'SuperUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        response = client.get('/api/courses/statistics/popular-courses?limit=5', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'popular_courses' in data['data']
    
    def test_get_teacher_performance(self, client, teacher_user):
        """测试获取教师表现统计"""
        login_response = client.post('/api/auth/login', json={
            'email': teacher_user.email,
            'password': 'EduUser123!'
        })
        access_token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        response = client.get(f'/api/courses/statistics/teacher-performance?teacher_id={teacher_user.id}', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'teacher_info' in data['data']
        assert 'performance_summary' in data['data']
        assert 'course_details' in data['data']