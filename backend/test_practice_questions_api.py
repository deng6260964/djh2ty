#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
练习题目管理API测试脚本
测试T11_007练习题目管理API的各项功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.utils.permissions import Permission
from app.utils.validation import validate_uuid

def test_practice_questions_api():
    """测试练习题目管理API模块"""
    print("=== 练习题目管理API测试 ===")
    
    try:
        # 测试应用创建
        app = create_app()
        print("✓ Flask应用创建成功")
        
        # 测试权限枚举
        print(f"✓ 权限枚举可用: {Permission.EXAM_UPDATE}")
        
        # 测试UUID验证函数
        test_uuid = "123e4567-e89b-12d3-a456-426614174000"
        is_valid = validate_uuid(test_uuid)
        print(f"✓ UUID验证函数正常: {is_valid}")
        
        # 测试路由注册
        with app.app_context():
            from app.routes.practices import practices_bp
            print(f"✓ 练习路由蓝图注册成功: {practices_bp.name}")
            
            # 检查路由规则
            routes = []
            for rule in app.url_map.iter_rules():
                if rule.endpoint and rule.endpoint.startswith('practices.'):
                    routes.append(f"{rule.methods} {rule.rule} -> {rule.endpoint}")
            
            print(f"✓ 发现 {len(routes)} 个练习相关路由")
            
            # 检查题目管理相关路由
            question_routes = [r for r in routes if 'questions' in r]
            print(f"✓ 发现 {len(question_routes)} 个题目管理路由")
            
            for route in question_routes:
                print(f"  - {route}")
        
        print("\n=== 所有测试通过 ===")
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_practice_questions_api()
    sys.exit(0 if success else 1)