from datetime import datetime
from .database import db

class Student:
    """学生模型类"""
    
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.user_id = kwargs.get('user_id')
        self.student_number = kwargs.get('student_number')
        self.grade = kwargs.get('grade')
        self.class_name = kwargs.get('class_name')
        self.school = kwargs.get('school')
        self.parent_name = kwargs.get('parent_name')
        self.parent_phone = kwargs.get('parent_phone')
        self.enrollment_date = kwargs.get('enrollment_date')
        self.status = kwargs.get('status', 'active')
        self.created_at = kwargs.get('created_at')
        self.updated_at = kwargs.get('updated_at')
    
    @classmethod
    def create_table(cls):
        """创建学生表"""
        # 先删除现有表（如果存在）
        drop_query = 'DROP TABLE IF EXISTS students'
        db.execute_query(drop_query)
        
        # 创建新表
        query = '''
            CREATE TABLE students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                student_number VARCHAR(50) UNIQUE,
                grade VARCHAR(20),
                class_name VARCHAR(50),
                school VARCHAR(100),
                parent_name VARCHAR(100),
                parent_phone VARCHAR(20),
                enrollment_date DATE,
                status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'graduated')),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        '''
        db.execute_query(query)
        
        # 创建索引
        indexes = [
            'CREATE INDEX IF NOT EXISTS idx_students_user_id ON students(user_id)',
            'CREATE INDEX IF NOT EXISTS idx_students_student_number ON students(student_number)',
            'CREATE INDEX IF NOT EXISTS idx_students_grade ON students(grade)',
            'CREATE INDEX IF NOT EXISTS idx_students_status ON students(status)'
        ]
        for index in indexes:
            db.execute_query(index)
    
    @classmethod
    def find_by_id(cls, student_id):
        """根据ID查找学生"""
        query = 'SELECT * FROM students WHERE id = ?'
        result = db.execute_query(query, (student_id,))
        if result:
            return cls.from_dict(dict(result[0]))
        return None
    
    @classmethod
    def find_by_user_id(cls, user_id):
        """根据用户ID查找学生"""
        query = 'SELECT * FROM students WHERE user_id = ?'
        result = db.execute_query(query, (user_id,))
        if result:
            return cls.from_dict(dict(result[0]))
        return None
    
    @classmethod
    def find_by_student_number(cls, student_number):
        """根据学号查找学生"""
        query = 'SELECT * FROM students WHERE student_number = ?'
        result = db.execute_query(query, (student_number,))
        if result:
            return cls.from_dict(dict(result[0]))
        return None
    
    @classmethod
    def get_all(cls, status=None):
        """获取所有学生"""
        if status:
            query = 'SELECT * FROM students WHERE status = ? ORDER BY created_at DESC'
            results = db.execute_query(query, (status,))
        else:
            query = 'SELECT * FROM students ORDER BY created_at DESC'
            results = db.execute_query(query)
        return [cls.from_dict(dict(row)) for row in results]
    
    @classmethod
    def get_by_grade(cls, grade):
        """根据年级获取学生"""
        query = 'SELECT * FROM students WHERE grade = ? AND status = "active" ORDER BY student_number'
        results = db.execute_query(query, (grade,))
        return [cls.from_dict(dict(row)) for row in results]
    
    @classmethod
    def from_dict(cls, data):
        """从字典创建学生对象"""
        return cls(
            id=data.get('id'),
            user_id=data.get('user_id'),
            student_number=data.get('student_number'),
            grade=data.get('grade'),
            class_name=data.get('class_name'),
            school=data.get('school'),
            parent_name=data.get('parent_name'),
            parent_phone=data.get('parent_phone'),
            enrollment_date=data.get('enrollment_date'),
            status=data.get('status', 'active'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'student_number': self.student_number,
            'grade': self.grade,
            'class_name': self.class_name,
            'school': self.school,
            'parent_name': self.parent_name,
            'parent_phone': self.parent_phone,
            'enrollment_date': self.enrollment_date,
            'status': self.status,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    def save(self):
        """保存学生信息"""
        if self.id:
            # 更新现有学生
            query = '''
                UPDATE students 
                SET student_number = ?, grade = ?, class_name = ?, school = ?, 
                    parent_name = ?, parent_phone = ?, enrollment_date = ?, status = ?, 
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            '''
            db.execute_query(query, (
                self.student_number, self.grade, self.class_name, self.school,
                self.parent_name, self.parent_phone, self.enrollment_date, self.status,
                self.id
            ))
        else:
            # 创建新学生
            query = '''
                INSERT INTO students (user_id, student_number, grade, class_name, school, 
                                    parent_name, parent_phone, enrollment_date, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            result = db.execute_query(query, (
                self.user_id, self.student_number, self.grade, self.class_name, self.school,
                self.parent_name, self.parent_phone, self.enrollment_date, self.status
            ))
            if result:
                self.id = db.get_last_insert_id()
    
    def delete(self):
        """删除学生"""
        if self.id:
            query = 'DELETE FROM students WHERE id = ?'
            db.execute_query(query, (self.id,))
    
    @classmethod
    def count_all(cls, status='active'):
        """统计学生总数"""
        query = 'SELECT COUNT(*) as count FROM students WHERE status = ?'
        result = db.execute_query(query, (status,))
        return result[0]['count'] if result else 0
    
    @classmethod
    def count_by_grade(cls, grade, status='active'):
        """按年级统计学生数量"""
        query = 'SELECT COUNT(*) as count FROM students WHERE grade = ? AND status = ?'
        result = db.execute_query(query, (grade, status))
        return result[0]['count'] if result else 0