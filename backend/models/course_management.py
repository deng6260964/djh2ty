from datetime import datetime
from .database import db

class CourseManagement:
    """课程管理模型类"""
    
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.teacher_id = kwargs.get('teacher_id')
        self.name = kwargs.get('name')
        self.description = kwargs.get('description', '')
        self.grade = kwargs.get('grade')
        self.subject = kwargs.get('subject', 'English')
        self.status = kwargs.get('status', 'active')
        self.created_at = kwargs.get('created_at')
        self.updated_at = kwargs.get('updated_at')
    
    @classmethod
    def create_table(cls):
        """创建课程管理表"""
        query = '''
            CREATE TABLE IF NOT EXISTS course_management (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id INTEGER NOT NULL,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                grade VARCHAR(50) NOT NULL,
                subject VARCHAR(100) DEFAULT 'English',
                status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'archived')),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (teacher_id) REFERENCES users(id)
            )
        '''
        db.execute_query(query)
        
        # 创建索引
        indexes = [
            'CREATE INDEX IF NOT EXISTS idx_course_management_teacher_id ON course_management(teacher_id)',
            'CREATE INDEX IF NOT EXISTS idx_course_management_grade ON course_management(grade)',
            'CREATE INDEX IF NOT EXISTS idx_course_management_subject ON course_management(subject)',
            'CREATE INDEX IF NOT EXISTS idx_course_management_status ON course_management(status)'
        ]
        for index in indexes:
            db.execute_query(index)
    
    @classmethod
    def find_by_id(cls, course_id):
        """根据ID查找课程"""
        query = 'SELECT * FROM course_management WHERE id = ?'
        result = db.execute_query(query, (course_id,))
        if result:
            return cls.from_dict(dict(result[0]))
        return None
    
    @classmethod
    def get_by_teacher(cls, teacher_id):
        """获取教师的课程"""
        query = 'SELECT * FROM course_management WHERE teacher_id = ? ORDER BY created_at DESC'
        results = db.execute_query(query, (teacher_id,))
        return [cls.from_dict(dict(row)) for row in results]
    
    @classmethod
    def get_all_active(cls):
        """获取所有活跃课程"""
        query = 'SELECT * FROM course_management WHERE status = "active" ORDER BY created_at DESC'
        results = db.execute_query(query)
        return [cls.from_dict(dict(row)) for row in results]
    
    @classmethod
    def from_dict(cls, data):
        """从字典创建课程对象"""
        return cls(
            id=data.get('id'),
            teacher_id=data.get('teacher_id'),
            name=data.get('name'),
            description=data.get('description', ''),
            grade=data.get('grade'),
            subject=data.get('subject', 'English'),
            status=data.get('status', 'active'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'teacher_id': self.teacher_id,
            'name': self.name,
            'description': self.description,
            'grade': self.grade,
            'subject': self.subject,
            'status': self.status,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    def save(self):
        """保存课程"""
        if self.id:
            # 更新现有课程
            query = '''
                UPDATE course_management 
                SET name = ?, description = ?, grade = ?, subject = ?, status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            '''
            db.execute_query(query, (self.name, self.description, self.grade, self.subject, self.status, self.id))
        else:
            # 创建新课程
            query = '''
                INSERT INTO course_management (teacher_id, name, description, grade, subject, status)
                VALUES (?, ?, ?, ?, ?, ?)
            '''
            result = db.execute_query(query, (self.teacher_id, self.name, self.description, self.grade, self.subject, self.status))
            if result:
                self.id = db.get_last_insert_id()
    
    def delete(self):
        """删除课程"""
        if self.id:
            query = 'DELETE FROM course_management WHERE id = ?'
            db.execute_query(query, (self.id,))
    
    @classmethod
    def count_by_teacher(cls, teacher_id):
        """统计教师的课程数量"""
        query = 'SELECT COUNT(*) as count FROM course_management WHERE teacher_id = ? AND status = "active"'
        result = db.execute_query(query, (teacher_id,))
        return result[0]['count'] if result else 0