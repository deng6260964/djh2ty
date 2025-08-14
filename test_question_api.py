#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json

# 配置
BASE_URL = "http://127.0.0.1:5001/api"

def login():
    """登录获取token"""
    url = f"{BASE_URL}/auth/login"
    data = {
        "phone": "13800138001",
        "password": "123456"
    }
    response = requests.post(url, json=data)
    if response.status_code == 200:
        result = response.json()
        return result['data']['access_token']
    else:
        print(f"登录失败: {response.text}")
        return None

def test_create_question(token):
    """测试创建题目"""
    url = f"{BASE_URL}/questions"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "title": "测试题目",
        "content": "这是一个测试题目内容",
        "type": "multiple_choice",
        "difficulty": "easy",
        "category": "测试",
        "points": 2,
        "options": ["选项A", "选项B", "选项C", "选项D"],
        "correct_answer": "选项A",
        "explanation": "这是解析"
    }
    
    print("测试创建题目...")
    print(f"请求数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
    
    response = requests.post(url, json=data, headers=headers)
    print(f"响应状态码: {response.status_code}")
    print(f"响应内容: {response.text}")
    
    if response.status_code == 201:
        result = response.json()
        return result['data']['question']['id']
    else:
        return None

def test_update_question(token, question_id):
    """测试更新题目"""
    url = f"{BASE_URL}/questions/{question_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "title": "更新后的测试题目",
        "content": "这是更新后的题目内容",
        "explanation": "这是更新后的解析"
    }
    
    print(f"\n测试更新题目 ID: {question_id}...")
    print(f"请求数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
    
    response = requests.put(url, json=data, headers=headers)
    print(f"响应状态码: {response.status_code}")
    print(f"响应内容: {response.text}")
    
    return response.status_code == 200

def test_delete_question(token, question_id):
    """测试删除题目"""
    url = f"{BASE_URL}/questions/{question_id}"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    print(f"\n测试删除题目 ID: {question_id}...")
    
    response = requests.delete(url, headers=headers)
    print(f"响应状态码: {response.status_code}")
    print(f"响应内容: {response.text}")
    
    return response.status_code == 200

def test_list_questions(token):
    """测试获取题目列表"""
    url = f"{BASE_URL}/questions"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    print("\n测试获取题目列表...")
    
    response = requests.get(url, headers=headers)
    print(f"响应状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        questions = result['data']['questions']
        print(f"题目总数: {result['data']['pagination']['total']}")
        for q in questions:
            print(f"- ID: {q['id']}, 标题: {q['title']}, 类型: {q['question_type']}")
    else:
        print(f"响应内容: {response.text}")
    
    return response.status_code == 200

if __name__ == "__main__":
    print("开始测试题目管理API...")
    
    # 1. 登录获取token
    token = login()
    if not token:
        print("登录失败，退出测试")
        exit(1)
    
    print(f"登录成功，获取到token: {token[:50]}...")
    
    # 2. 测试获取题目列表
    test_list_questions(token)
    
    # 3. 测试创建题目
    question_id = test_create_question(token)
    if question_id:
        print(f"\n题目创建成功，ID: {question_id}")
        
        # 4. 测试更新题目
        if test_update_question(token, question_id):
            print("题目更新成功")
        else:
            print("题目更新失败")
        
        # 5. 测试删除题目
        if test_delete_question(token, question_id):
            print("题目删除成功")
        else:
            print("题目删除失败")
    else:
        print("题目创建失败")
    
    print("\nAPI测试完成")