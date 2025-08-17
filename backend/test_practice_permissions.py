#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
练习系统权限常量测试脚本
测试T11_010权限常量定义任务的完成情况
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.utils.permissions import (
    Permission, UserRole, PermissionManager,
    practice_management_required, practice_read_required,
    practice_participate_required, practice_view_results_required,
    practice_view_stats_required, practice_view_progress_required
)

def test_practice_permissions():
    """测试练习系统权限常量定义"""
    print("============================================================")
    print("T11_010 练习系统权限常量测试开始")
    print("============================================================")
    
    # 测试权限常量定义
    practice_permissions = [
        Permission.PRACTICE_CREATE,
        Permission.PRACTICE_READ,
        Permission.PRACTICE_UPDATE,
        Permission.PRACTICE_DELETE,
        Permission.PRACTICE_PARTICIPATE,
        Permission.PRACTICE_VIEW_RESULTS,
        Permission.PRACTICE_VIEW_STATS,
        Permission.PRACTICE_VIEW_PROGRESS
    ]
    
    print("\n1. 测试练习权限常量定义:")
    for perm in practice_permissions:
        print(f"✅ {perm.name}: {perm.value}")
    
    # 测试便捷装饰器定义
    print("\n2. 测试便捷权限装饰器:")
    decorators = [
        ('practice_management_required', practice_management_required),
        ('practice_read_required', practice_read_required),
        ('practice_participate_required', practice_participate_required),
        ('practice_view_results_required', practice_view_results_required),
        ('practice_view_stats_required', practice_view_stats_required),
        ('practice_view_progress_required', practice_view_progress_required)
    ]
    
    for name, decorator in decorators:
        if decorator:
            print(f"✅ {name}: 已定义")
        else:
            print(f"❌ {name}: 未定义")
            return False
    
    # 测试角色权限映射
    print("\n3. 测试角色权限映射:")
    
    # 测试管理员权限
    admin_permissions = PermissionManager.get_user_permissions(UserRole.ADMIN.value)
    admin_practice_perms = [p for p in admin_permissions if 'practice' in p.value]
    print(f"✅ 管理员练习权限数量: {len(admin_practice_perms)}")
    
    # 测试教师权限
    teacher_permissions = PermissionManager.get_user_permissions(UserRole.TEACHER.value)
    teacher_practice_perms = [p for p in teacher_permissions if 'practice' in p.value]
    print(f"✅ 教师练习权限数量: {len(teacher_practice_perms)}")
    
    # 测试学生权限
    student_permissions = PermissionManager.get_user_permissions(UserRole.STUDENT.value)
    student_practice_perms = [p for p in student_permissions if 'practice' in p.value]
    print(f"✅ 学生练习权限数量: {len(student_practice_perms)}")
    
    # 测试具体权限检查
    print("\n4. 测试具体权限检查:")
    
    # 管理员应该拥有所有练习权限
    for perm in practice_permissions:
        if PermissionManager.has_permission(UserRole.ADMIN.value, perm):
            print(f"✅ 管理员拥有权限: {perm.value}")
        else:
            print(f"❌ 管理员缺少权限: {perm.value}")
            return False
    
    # 教师应该拥有所有练习权限
    for perm in practice_permissions:
        if PermissionManager.has_permission(UserRole.TEACHER.value, perm):
            print(f"✅ 教师拥有权限: {perm.value}")
        else:
            print(f"❌ 教师缺少权限: {perm.value}")
            return False
    
    # 学生应该拥有部分练习权限
    student_should_have = [
        Permission.PRACTICE_READ,
        Permission.PRACTICE_PARTICIPATE,
        Permission.PRACTICE_VIEW_RESULTS
    ]
    
    student_should_not_have = [
        Permission.PRACTICE_CREATE,
        Permission.PRACTICE_UPDATE,
        Permission.PRACTICE_DELETE,
        Permission.PRACTICE_VIEW_STATS,
        Permission.PRACTICE_VIEW_PROGRESS
    ]
    
    for perm in student_should_have:
        if PermissionManager.has_permission(UserRole.STUDENT.value, perm):
            print(f"✅ 学生拥有权限: {perm.value}")
        else:
            print(f"❌ 学生应该拥有但缺少权限: {perm.value}")
            return False
    
    for perm in student_should_not_have:
        if not PermissionManager.has_permission(UserRole.STUDENT.value, perm):
            print(f"✅ 学生正确不拥有权限: {perm.value}")
        else:
            print(f"❌ 学生不应该拥有权限: {perm.value}")
            return False
    
    print("\n============================================================")
    print("✅ T11_010 练习系统权限常量测试全部通过")
    print("============================================================")
    
    print("\n已定义的练习权限常量:")
    for perm in practice_permissions:
        print(f"- {perm.name}: {perm.value}")
    
    print("\n已定义的便捷装饰器:")
    for name, _ in decorators:
        print(f"- {name}")
    
    print("\n权限映射验证:")
    print(f"- 管理员: 拥有全部{len(admin_practice_perms)}个练习权限")
    print(f"- 教师: 拥有全部{len(teacher_practice_perms)}个练习权限")
    print(f"- 学生: 拥有{len(student_practice_perms)}个练习权限（读取、参与、查看结果）")
    
    return True

if __name__ == "__main__":
    try:
        success = test_practice_permissions()
        if success:
            print("\n🎉 T11_010权限常量定义任务验证成功！")
        else:
            print("\n❌ T11_010权限常量定义任务验证失败！")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)