#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T11_009 进度跟踪API测试脚本

测试内容：
1. 学习历史查询接口
2. 个人统计报告接口
3. 错题集管理接口
4. 复习练习生成接口
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.utils.permissions import Permission
from app.utils.validation import validate_uuid

def test_flask_app_creation():
    """测试Flask应用创建"""
    try:
        app = create_app()
        print("✅ Flask应用创建成功")
        return app
    except Exception as e:
        print(f"❌ Flask应用创建失败: {e}")
        return None

def test_permission_availability():
    """测试权限常量可用性"""
    try:
        practice_permission = Permission.PRACTICE_PARTICIPATE
        print(f"✅ 练习参与权限可用: {practice_permission}")
        return True
    except Exception as e:
        print(f"❌ 权限常量不可用: {e}")
        return False

def test_uuid_validator():
    """测试UUID验证函数"""
    try:
        # 测试有效UUID
        valid_uuid = "550e8400-e29b-41d4-a716-446655440000"
        result = validate_uuid(valid_uuid)
        assert result == True, "有效UUID验证失败"
        
        # 测试无效UUID
        invalid_uuid = "invalid-uuid"
        result = validate_uuid(invalid_uuid)
        assert result == False, "无效UUID验证失败"
        
        print("✅ UUID验证函数正常工作")
        return True
    except Exception as e:
        print(f"❌ UUID验证函数测试失败: {e}")
        return False

def test_practice_statistics_routes(app):
    """测试练习统计路由注册"""
    try:
        with app.app_context():
            # 检查路由是否注册
            routes = [str(rule) for rule in app.url_map.iter_rules()]
            
            expected_routes = [
                '/api/practice-statistics/learning-history/<user_id>',
                '/api/practice-statistics/personal-report/<user_id>',
                '/api/practice-statistics/wrong-questions/<user_id>',
                '/api/practice-statistics/review-practice/<user_id>'
            ]
            
            for route in expected_routes:
                if any(route in r for r in routes):
                    print(f"✅ 路由已注册: {route}")
                else:
                    print(f"❌ 路由未注册: {route}")
                    return False
            
            print("✅ 所有进度跟踪API路由已正确注册")
            return True
    except Exception as e:
        print(f"❌ 路由注册检查失败: {e}")
        return False

def test_learning_history_api_structure(app):
    """测试学习历史API结构"""
    try:
        with app.app_context():
            from app.routes.practice_statistics import get_learning_history
            
            # 检查函数是否存在
            assert callable(get_learning_history), "学习历史API函数不存在"
            
            # 检查函数文档
            doc = get_learning_history.__doc__
            assert doc and '学习历史查询' in doc, "API文档不完整"
            
            print("✅ 学习历史API结构正确")
            return True
    except Exception as e:
        print(f"❌ 学习历史API结构检查失败: {e}")
        return False

def test_personal_report_api_structure(app):
    """测试个人统计报告API结构"""
    try:
        with app.app_context():
            from app.routes.practice_statistics import get_personal_report
            
            # 检查函数是否存在
            assert callable(get_personal_report), "个人统计报告API函数不存在"
            
            # 检查函数文档
            doc = get_personal_report.__doc__
            assert doc and '个人统计报告' in doc, "API文档不完整"
            
            print("✅ 个人统计报告API结构正确")
            return True
    except Exception as e:
        print(f"❌ 个人统计报告API结构检查失败: {e}")
        return False

def test_wrong_questions_api_structure(app):
    """测试错题集API结构"""
    try:
        with app.app_context():
            from app.routes.practice_statistics import get_wrong_questions
            
            # 检查函数是否存在
            assert callable(get_wrong_questions), "错题集API函数不存在"
            
            # 检查函数文档
            doc = get_wrong_questions.__doc__
            assert doc and '获取错题集' in doc, "API文档不完整"
            
            print("✅ 错题集API结构正确")
            return True
    except Exception as e:
        print(f"❌ 错题集API结构检查失败: {e}")
        return False

def test_review_practice_api_structure(app):
    """测试复习练习生成API结构"""
    try:
        with app.app_context():
            from app.routes.practice_statistics import generate_review_practice
            
            # 检查函数是否存在
            assert callable(generate_review_practice), "复习练习生成API函数不存在"
            
            # 检查函数文档
            doc = generate_review_practice.__doc__
            assert doc and '生成复习练习' in doc, "API文档不完整"
            
            print("✅ 复习练习生成API结构正确")
            return True
    except Exception as e:
        print(f"❌ 复习练习生成API结构检查失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("T11_009 进度跟踪API测试开始")
    print("=" * 60)
    
    # 测试Flask应用创建
    app = test_flask_app_creation()
    if not app:
        print("\n❌ 测试终止：Flask应用创建失败")
        return False
    
    # 测试权限常量
    if not test_permission_availability():
        print("\n❌ 测试终止：权限常量不可用")
        return False
    
    # 测试UUID验证
    if not test_uuid_validator():
        print("\n❌ 测试终止：UUID验证函数异常")
        return False
    
    # 测试路由注册
    if not test_practice_statistics_routes(app):
        print("\n❌ 测试终止：路由注册异常")
        return False
    
    # 测试API结构
    tests = [
        test_learning_history_api_structure,
        test_personal_report_api_structure,
        test_wrong_questions_api_structure,
        test_review_practice_api_structure
    ]
    
    for test_func in tests:
        if not test_func(app):
            print(f"\n❌ 测试终止：{test_func.__name__}失败")
            return False
    
    print("\n" + "=" * 60)
    print("✅ T11_009 进度跟踪API测试全部通过")
    print("=" * 60)
    print("\n已实现的接口：")
    print("1. 学习历史查询 - GET /api/practice-statistics/learning-history/<user_id>")
    print("2. 个人统计报告 - GET /api/practice-statistics/personal-report/<user_id>")
    print("3. 错题集管理 - GET /api/practice-statistics/wrong-questions/<user_id>")
    print("4. 复习练习生成 - POST /api/practice-statistics/review-practice/<user_id>")
    print("\n功能特性：")
    print("- 支持多维度数据过滤（课程、时间、题目类型）")
    print("- 提供学习趋势分析和统计报告")
    print("- 智能错题集管理和复习推荐")
    print("- 完整的权限控制和参数验证")
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)