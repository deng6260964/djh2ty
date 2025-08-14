import sqlite3
import os
from datetime import datetime
from contextlib import contextmanager

class Database:
    """数据库连接管理类"""
    
    def __init__(self, db_path='database.db'):
        self.db_path = db_path
        self.ensure_db_exists()
    
    def ensure_db_exists(self):
        """确保数据库文件存在"""
        if not os.path.exists(self.db_path):
            # 创建数据库文件
            conn = sqlite3.connect(self.db_path)
            conn.close()
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接的上下文管理器"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 使查询结果可以像字典一样访问
        try:
            yield conn
        finally:
            conn.close()
    
    def execute_query(self, query, params=None):
        """执行查询并返回结果"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()
    
    def execute_insert(self, query, params=None):
        """执行插入操作并返回插入的ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()
            return cursor.lastrowid
    
    def execute_update(self, query, params=None):
        """执行更新操作并返回影响的行数"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()
            return cursor.rowcount
    
    def execute_delete(self, query, params=None):
        """执行删除操作并返回影响的行数"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()
            return cursor.rowcount

# 全局数据库实例
db = Database('database.db')