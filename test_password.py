import sqlite3
from werkzeug.security import check_password_hash

# 连接数据库
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# 查询测试用户的密码哈希
cursor.execute('SELECT phone, name, password_hash FROM users WHERE phone IN ("13800138001", "13800138002")')
users = cursor.fetchall()

print("测试密码验证逻辑:")
for user in users:
    phone, name, password_hash = user
    print(f"\n用户: {name} ({phone})")
    print(f"密码哈希: {password_hash[:50]}...")
    
    # 测试正确密码
    is_valid = check_password_hash(password_hash, '123456')
    print(f"密码 '123456' 验证结果: {is_valid}")
    
    # 测试错误密码
    is_invalid = check_password_hash(password_hash, 'wrongpassword')
    print(f"密码 'wrongpassword' 验证结果: {is_invalid}")

conn.close()