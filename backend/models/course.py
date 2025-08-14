from datetime import datetime
from .database import db

class Course:
    """课程模型类"""
    
    def __init__(self, data=None, **kwargs):
        # 如果传入的是字典，使用字典的值
        if isinstance(data, dict):
            self.id = data.get('id')
            self.teacher_id = data.get('teacher_id')
            self.title = data.get('title')
            self.subject = data.get('subject')
            self.level = data.get('level')
            self.start_time = data.get('start_time')
            self.end_time = data.get('end_time')
            self.location = data.get('location')
            self.max_students = data.get('max_students', 30)
            self.description = data.get('description')
            self.status = data.get('status', 'active')
            self.created_at = data.get('created_at')
            self.updated_at = data.get('updated_at')
        else:
            # 兼容原有的参数方式
            self.id = kwargs.get('id', data)
            self.teacher_id = kwargs.get('teacher_id')
            self.title = kwargs.get('title')
            self.subject = kwargs.get('subject')
            self.level = kwargs.get('level')
            self.start_time = kwargs.get('start_time')
            self.end_time = kwargs.get('end_time')
            self.location = kwargs.get('location')
            self.max_students = kwargs.get('max_students', 30)
            self.description = kwargs.get('description')
            self.status = kwargs.get('status', 'active')
            self.created_at = kwargs.get('created_at')
            self.updated_at = kwargs.get('updated_at')
    
    @classmethod
    def create_table(cls):
        """创建课程表"""
        query = '''
            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id INTEGER NOT NULL,
                title VARCHAR(255) NOT NULL,
                subject VARCHAR(100) NOT NULL,
                level VARCHAR(50) NOT NULL,
                start_time DATETIME NOT NULL,
                end_time DATETIME NOT NULL,
                location VARCHAR(255),
                max_students INTEGER DEFAULT 30,
                description TEXT,
                status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'completed')),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (teacher_id) REFERENCES users(id)
            )
        '''
        db.execute_query(query)
        
        # 创建索引
        indexes = [
            'CREATE INDEX IF NOT EXISTS idx_courses_teacher_id ON courses(teacher_id)',
            'CREATE INDEX IF NOT EXISTS idx_courses_subject ON courses(subject)',
            'CREATE INDEX IF NOT EXISTS idx_courses_level ON courses(level)',
            'CREATE INDEX IF NOT EXISTS idx_courses_start_time ON courses(start_time)',
            'CREATE INDEX IF NOT EXISTS idx_courses_status ON courses(status)'
        ]
        for index in indexes:
            db.execute_query(index)
    
    @classmethod
    def find_by_id(cls, course_id):
        """根据ID查找课程"""
        query = 'SELECT * FROM courses WHERE id = ?'
        result = db.execute_query(query, (course_id,))
        if result:
            return cls.from_dict(dict(result[0]))
        return None
    
    @classmethod
    def get_by_teacher(cls, teacher_id, start_date=None, end_date=None):
        """获取教师的课程"""
        query = 'SELECT * FROM courses WHERE teacher_id = ?'
        params = [teacher_id]
        
        if start_date and end_date:
            query += ' AND start_time BETWEEN ? AND ?'
            params.extend([start_date, end_date])
        
        query += ' ORDER BY start_time ASC'
        results = db.execute_query(query, params)
        return [cls.from_dict(dict(row)) for row in results]
    
    @classmethod
    def get_upcoming_courses(cls, teacher_id, limit=10):
        """获取即将到来的课程"""
        query = '''
            SELECT * FROM courses 
            WHERE teacher_id = ? AND start_time > datetime('now') AND status = 'active'
            ORDER BY start_time ASC 
            LIMIT ?
        '''
        results = db.execute_query(query, (teacher_id, limit))
        return [cls.from_dict(dict(row)) for row in results]
    
    @classmethod
    def get_all_active(cls):
        """获取所有活跃课程"""
        query = 'SELECT * FROM courses WHERE status = "active" ORDER BY start_time ASC'
        results = db.execute_query(query)
        return [cls.from_dict(dict(row)) for row in results]
    
    @classmethod
    def from_dict(cls, data):
        """从字典创建课程对象"""
        return cls(
            id=data.get('id'),
            teacher_id=data.get('teacher_id'),
            title=data.get('title'),
            subject=data.get('subject'),
            level=data.get('level'),
            start_time=data.get('start_time'),
            end_time=data.get('end_time'),
            location=data.get('location'),
            max_students=data.get('max_students', 30),
            description=data.get('description'),
            status=data.get('status', 'active'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'teacher_id': self.teacher_id,
            'title': self.title,
            'subject': self.subject,
            'level': self.level,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'location': self.location,
            'max_students': self.max_students,
            'description': self.description,
            'status': self.status,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    def save(self):
        """保存课程"""
        if self.id:
            # 更新现有课程
            query = '''
                UPDATE courses SET 
                    teacher_id = ?, title = ?, subject = ?, level = ?,
                    start_time = ?, end_time = ?, location = ?, max_students = ?,
                    description = ?, status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            '''
            params = (
                self.teacher_id, self.title, self.subject, self.level,
                self.start_time, self.end_time, self.location, self.max_students,
                self.description, self.status, self.id
            )
            db.execute_update(query, params)
        else:
            # 创建新课程
            query = '''
                INSERT INTO courses (
                    teacher_id, title, subject, level, start_time, end_time,
                    location, max_students, description, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            params = (
                self.teacher_id, self.title, self.subject, self.level,
                self.start_time, self.end_time, self.location, self.max_students,
                self.description, self.status
            )
            self.id = db.execute_insert(query, params)
        return self
    
    def delete(self):
        """删除课程"""
        if self.id:
            query = 'DELETE FROM courses WHERE id = ?'
            return db.execute_delete(query, (self.id,))
        return False