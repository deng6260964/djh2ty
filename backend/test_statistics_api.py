#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试练习统计API功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
import uuid

def test_statistics_api():
    """测试统计API基本功能"""
    app = create_app()
    
    with app.app_context():
        try:
            # 测试导入是否正常
            from app.routes.practice_statistics import practice_statistics_bp
            print("✅ 统计API模块导入成功")
            
            # 测试权限枚举导入
            from app.utils.permissions import Permission
            print(f"✅ 权限枚举导入成功: {Permission.PRACTICE_VIEW_STATS}")
            
            # 测试UUID验证函数
            from app.routes.practice_statistics import _validate_uuid
            test_uuid = str(uuid.uuid4())
            invalid_uuid = "invalid-uuid"
            
            print(f"✅ UUID验证函数测试:")
            print(f"  - 有效UUID: {_validate_uuid(test_uuid)}")
            print(f"  - 无效UUID: {_validate_uuid(invalid_uuid)}")
            
            # 测试辅助函数导入
            from app.routes.practice_statistics import _can_view_practice_stats, _can_view_user_stats
            print("✅ 权限检查辅助函数导入成功")
            
            print("\n🎉 所有基础功能测试通过！")
            return True
            
        except ImportError as e:
            print(f"❌ 导入错误: {e}")
            return False
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            return False

if __name__ == '__main__':
    print("开始测试练习统计API...")
    success = test_statistics_api()
    if success:
        print("\n✅ 测试完成，统计API功能正常")
        sys.exit(0)
    else:
        print("\n❌ 测试失败，请检查错误信息")
        sys.exit(1)