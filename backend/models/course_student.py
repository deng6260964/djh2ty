from datetime import datetime
from .database import db

class CourseStudent:
    """课程学生关联模型类"""
    
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.course_id = kwargs.get('course_id')
        self.student_id = kwargs.get('student_id')
        self.enrollment_date = kwargs.get('enrollment_date')
        self.status = kwargs.get('status', 'enrolled')
        self.created_at = kwargs.get('created_at')
        self.updated_at = kwargs.get('updated_at')
    
    @classmethod
    def create_table(cls):
        """创建课程学生关联表"""
        query = '''
            CREATE TABLE IF NOT EXISTS course_students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER NOT NULL,
                student_id INTEGER NOT NULL,
                enrollment_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(20) DEFAULT 'enrolled' CHECK (status IN ('enrolled', 'dropped', 'completed')),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
                FOREIGN KEY (student_id) REFERENCES users(id),
                UNIQUE(course_id, student_id)
            )
        '''
        db.execute_query(query)
        
        # 创建索引
        indexes = [
            'CREATE INDEX IF NOT EXISTS idx_course_students_course_id ON course_students(course_id)',
            'CREATE INDEX IF NOT EXISTS idx_course_students_student_id ON course_students(student_id)',
            'CREATE INDEX IF NOT EXISTS idx_course_students_status ON course_students(status)'
        ]
        for index in indexes:
            db.execute_query(index)
    
    @classmethod
    def find_by_id(cls, id):
        """根据ID查找记录"""
        query = 'SELECT * FROM course_students WHERE id = ?'
        result = db.execute_query(query, (id,))
        if result:
            return cls.from_dict(dict(result[0]))
        return None
    
    @classmethod
    def get_by_course(cls, course_id):
        """获取课程的所有学生"""
        query = '''
            SELECT cs.*, u.name as student_name, u.phone as student_phone
            FROM course_students cs
            LEFT JOIN users u ON cs.student_id = u.id
            WHERE cs.course_id = ? AND cs.status = 'enrolled'
            ORDER BY cs.enrollment_date ASC
        '''
        results = db.execute_query(query, (course_id,))
        enrollments = []
        for row in results:
            enrollment_data = dict(row)
            enrollment = cls.from_dict(enrollment_data)
            enrollment.student_name = enrollment_data.get('student_name')
            enrollment.student_phone = enrollment_data.get('student_phone')
            enrollments.append(enrollment)
        return enrollments
    
    @classmethod
    def get_by_student(cls, student_id):
        """获取学生的所有课程"""
        query = '''
            SELECT cs.*, c.title as course_title, c.subject, c.level
            FROM course_students cs
            LEFT JOIN courses c ON cs.course_id = c.id
            WHERE cs.student_id = ? AND cs.status = 'enrolled'
            ORDER BY cs.enrollment_date DESC
        '''
        results = db.execute_query(query, (student_id,))
        enrollments = []
        for row in results:
            enrollment_data = dict(row)
            enrollment = cls.from_dict(enrollment_data)
            enrollment.course_title = enrollment_data.get('course_title')
            enrollment.course_subject = enrollment_data.get('subject')
            enrollment.course_level = enrollment_data.get('level')
            enrollments.append(enrollment)
        return enrollments
    
    @classmethod
    def is_enrolled(cls, course_id, student_id):
        """检查学生是否已报名课程"""
        query = 'SELECT COUNT(*) as count FROM course_students WHERE course_id = ? AND student_id = ? AND status = "enrolled"'
        result = db.execute_query(query, (course_id, student_id))
        return result[0]['count'] > 0 if result else False
    
    @classmethod
    def get_enrollment_count(cls, course_id):
        """获取课程的报名人数"""
        query = 'SELECT COUNT(*) as count FROM course_students WHERE course_id = ? AND status = "enrolled"'
        result = db.execute_query(query, (course_id,))
        return result[0]['count'] if result else 0
    
    @classmethod
    def from_dict(cls, data):
        """从字典创建对象"""
        return cls(
            id=data.get('id'),
            course_id=data.get('course_id'),
            student_id=data.get('student_id'),
            enrollment_date=data.get('enrollment_date'),
            status=data.get('status', 'enrolled'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )
    
    def to_dict(self):
        """转换为字典"""
        data = {
            'id': self.id,
            'course_id': self.course_id,
            'student_id': self.student_id,
            'enrollment_date': self.enrollment_date,
            'status': self.status,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
        
        # 添加额外信息（如果存在）
        if hasattr(self, 'student_name'):
            data['student_name'] = self.student_name
            data['student_phone'] = self.student_phone
        
        if hasattr(self, 'course_title'):
            data['course_title'] = self.course_title
            data['course_subject'] = self.course_subject
            data['course_level'] = self.course_level
        
        return data
    
    def save(self):
        """保存记录"""
        if self.id:
            # 更新现有记录
            query = '''
                UPDATE course_students SET 
                    course_id = ?, student_id = ?, enrollment_date = ?, status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            '''
            params = (self.course_id, self.student_id, self.enrollment_date, self.status, self.id)
            db.execute_update(query, params)
        else:
            # 创建新记录
            query = '''
                INSERT INTO course_students (course_id, student_id, enrollment_date, status)
                VALUES (?, ?, ?, ?)
            '''
            params = (self.course_id, self.student_id, self.enrollment_date, self.status)
            self.id = db.execute_insert(query, params)
        return self
    
    def delete(self):
        """删除记录"""
        if self.id:
            query = 'DELETE FROM course_students WHERE id = ?'
            return db.execute_delete(query, (self.id,))
        return False