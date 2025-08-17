#!/usr/bin/env python3
from app import create_app
from app.models import User, QuestionBank, Question
from app.utils.auth import hash_password
from app import db
import json

def test_update_question():
    app = create_app()
    app.config['TESTING'] = True
    
    with app.app_context():
        # 创建测试数据
        db.drop_all()
        db.create_all()
        
        # 创建管理员用户
        admin = User(email='admin@test.com', name='Admin User', password_hash=hash_password('SuperSecure@2024!'), role='admin')
        db.session.add(admin)
        db.session.commit()
        
        # 创建题库
        bank = QuestionBank(
            name='Test Bank',
            description='Test Description',
            difficulty_level='beginner',
            created_by=admin.id
        )
        db.session.add(bank)
        db.session.commit()
        
        # 创建题目
        question = Question(
            title='Test Question?',
            content='What is the capital of France?',
            question_type='multiple_choice',
            options=json.dumps(['A', 'B', 'C', 'D']),
            correct_answer='A',
            points=5,
            difficulty_level='beginner',
            question_bank_id=bank.id,
            created_by=admin.id
        )
        db.session.add(question)
        db.session.commit()
        
        # 测试客户端
        client = app.test_client()
        
        # 登录获取token
        login_resp = client.post('/api/auth/login', json={
            'email': 'admin@test.com',
            'password': 'SuperSecure@2024!'
        })
        
        print(f"Login status: {login_resp.status_code}")
        print(f"Login response: {login_resp.get_json()}")
        
        if login_resp.status_code == 200:
            token = login_resp.get_json()['access_token']
            headers = {'Authorization': f'Bearer {token}'}
            
            # 测试更新题目
            update_data = {
                'title': 'Updated Question?'
            }
            
            resp = client.put(f'/api/questions/questions/{question.id}', 
                            json=update_data, 
                            headers=headers)
            
            print(f"Update status: {resp.status_code}")
            print(f"Update response: {resp.get_json()}")
            
            if resp.status_code != 200:
                print(f"Error details: {resp.data.decode()}")
        
        # 清理
        db.session.remove()
        db.drop_all()

if __name__ == '__main__':
    test_update_question()