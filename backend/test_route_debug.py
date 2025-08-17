#!/usr/bin/env python3
"""
路由调试脚本
直接测试Flask应用的路由行为
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from flask import url_for

def test_routes():
    """测试路由配置"""
    app = create_app('testing')
    
    with app.app_context():
        print("=== Flask应用路由信息 ===")
        print(f"应用配置: {app.config.get('TESTING')}")
        print(f"调试模式: {app.debug}")
        
        print("\n=== 注册的路由 ===")
        for rule in app.url_map.iter_rules():
            print(f"{rule.rule} -> {rule.endpoint} [{', '.join(rule.methods)}]")
            if 'upload' in rule.rule:
                print(f"  strict_slashes: {rule.strict_slashes}")
        
        print("\n=== 测试URL生成 ===")
        try:
            upload_url = url_for('files.upload_file')
            print(f"upload_file URL: {upload_url}")
        except Exception as e:
            print(f"生成upload_file URL失败: {e}")
        
        print("\n=== 测试客户端请求 ===")
        with app.test_client() as client:
            # 测试不带斜杠的URL
            print("测试 POST /api/files/upload")
            response1 = client.post('/api/files/upload', 
                                   data={'test': 'data'},
                                   follow_redirects=False)
            print(f"状态码: {response1.status_code}")
            print(f"响应头: {dict(response1.headers)}")
            
            # 测试带斜杠的URL
            print("\n测试 POST /api/files/upload/")
            response2 = client.post('/api/files/upload/', 
                                   data={'test': 'data'},
                                   follow_redirects=False)
            print(f"状态码: {response2.status_code}")
            print(f"响应头: {dict(response2.headers)}")
            
            # 测试GET请求
            print("\n测试 GET /api/files/upload")
            response3 = client.get('/api/files/upload', follow_redirects=False)
            print(f"状态码: {response3.status_code}")
            print(f"响应头: {dict(response3.headers)}")

if __name__ == '__main__':
    test_routes()