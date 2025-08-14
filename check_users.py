import sqlite3
import os

# 检查数据库文件是否存在
db_path = 'database.db'  # 修正数据库路径
if not os.path.exists(db_path):
    print(f"数据库文件不存在: {db_path}")
    exit(1)

print(f"数据库文件存在: {db_path}")

try:
    # 连接数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 检查users表是否存在
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    table_exists = cursor.fetchone()
    
    if not table_exists:
        print("users表不存在")
        conn.close()
        exit(1)
    
    print("users表存在")
    
    # 查询所有用户
    cursor.execute('SELECT phone, name, role FROM users')
    all_users = cursor.fetchall()
    
    print(f"\n数据库中共有 {len(all_users)} 个用户:")
    for user in all_users:
        print(f"  手机号: {user[0]}, 姓名: {user[1]}, 角色: {user[2]}")
    
    # 查询测试用户
    cursor.execute('SELECT phone, name, role FROM users WHERE phone IN ("13800138001", "13800138002")')
    test_users = cursor.fetchall()
    
    print(f"\n测试用户查询结果:")
    if test_users:
        for user in test_users:
            print(f"  手机号: {user[0]}, 姓名: {user[1]}, 角色: {user[2]}")
    else:
        print("  未找到测试用户 (13800138001, 13800138002)")
    
    conn.close()
    
except Exception as e:
    print(f"数据库查询出错: {e}")