#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T11_008 答题处理API测试脚本
测试练习答题处理相关的API功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.utils.permissions import Permission
from app.utils.validation import validate_uuid

def test_practice_answer_api():
    """测试练习答题处理API"""
    print("=== T11_008 答题处理API测试 ===")
    
    # 1. 测试Flask应用创建
    try:
        app = create_app()
        print("✅ Flask应用创建成功")
    except Exception as e:
        print(f"❌ Flask应用创建失败: {e}")
        return False
    
    # 2. 测试权限枚举
    try:
        practice_permission = Permission.PRACTICE_PARTICIPATE
        print(f"✅ 练习参与权限可用: {practice_permission}")
    except Exception as e:
        print(f"❌ 权限枚举不可用: {e}")
        return False
    
    # 3. 测试UUID验证函数
    try:
        test_uuid = "123e4567-e89b-12d3-a456-426614174000"
        is_valid = validate_uuid(test_uuid)
        print(f"✅ UUID验证函数正常: {is_valid}")
    except Exception as e:
        print(f"❌ UUID验证函数异常: {e}")
        return False
    
    # 4. 测试练习会话路由注册
    with app.app_context():
        try:
            # 检查练习会话蓝图是否注册
            blueprints = [bp.name for bp in app.blueprints.values()]
            if 'practice_sessions' in blueprints:
                print("✅ 练习会话路由蓝图注册成功")
            else:
                print(f"❌ 练习会话路由蓝图未注册，已注册蓝图: {blueprints}")
                return False
        except Exception as e:
            print(f"❌ 检查路由蓝图失败: {e}")
            return False
    
    # 5. 测试答题处理相关路由
    with app.app_context():
        try:
            answer_routes = []
            for rule in app.url_map.iter_rules():
                if 'practice-sessions' in rule.rule and any(keyword in rule.rule for keyword in ['submit-answer', 'get-hint', 'skip-question']):
                    answer_routes.append({
                        'endpoint': rule.endpoint,
                        'rule': rule.rule,
                        'methods': list(rule.methods - {'HEAD', 'OPTIONS'})
                    })
            
            print(f"\n发现 {len(answer_routes)} 个答题处理相关路由:")
            for route in answer_routes:
                print(f"  - {route['rule']} [{', '.join(route['methods'])}] -> {route['endpoint']}")
            
            # 验证核心API是否存在
            expected_apis = [
                'submit-answer',  # 提交答案
                'get-hint',       # 获取提示
                'skip-question'   # 跳过题目
            ]
            
            found_apis = []
            for api in expected_apis:
                for route in answer_routes:
                    if api in route['rule']:
                        found_apis.append(api)
                        break
            
            print(f"\n核心答题处理API检查:")
            for api in expected_apis:
                if api in found_apis:
                    print(f"  ✅ {api} API 已实现")
                else:
                    print(f"  ❌ {api} API 未找到")
            
            if len(found_apis) == len(expected_apis):
                print("\n✅ 所有核心答题处理API都已实现")
                return True
            else:
                print(f"\n❌ 缺少 {len(expected_apis) - len(found_apis)} 个核心API")
                return False
                
        except Exception as e:
            print(f"❌ 检查答题处理路由失败: {e}")
            return False

if __name__ == "__main__":
    success = test_practice_answer_api()
    if success:
        print("\n🎉 T11_008 答题处理API测试全部通过！")
        sys.exit(0)
    else:
        print("\n💥 T11_008 答题处理API测试失败！")
        sys.exit(1)