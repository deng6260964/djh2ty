from datetime import datetime
from .database import db

class Course:
    """课程模型类"""
    
    def __init__(self, data=None, **kwargs):
        # 如果传入的是字典，使用字典的值
        if isinstance(data, dict):
            self.id = data.get('id')
            self.teacher_id = data.get('teacher_id')
            self.student_id = data.get('student_id')
            self.subject = data.get('subject')
            self.course_time = data.get('course_time')
            self.duration = data.get('duration')
            self.location = data.get('location')
            self.status = data.get('status', 'scheduled')
            self.notes = data.get('notes')
            self.homework_assigned = data.get('homework_assigned')
            self.homework_completed = data.get('homework_completed')
            self.created_at = data.get('created_at')
            self.updated_at = data.get('updated_at')
        else:
            # 兼容原有的参数方式
            self.id = kwargs.get('id', data)
            self.teacher_id = kwargs.get('teacher_id')
            self.student_id = kwargs.get('student_id')
            self.subject = kwargs.get('subject')
            self.course_time = kwargs.get('course_time')
            self.duration = kwargs.get('duration')
            self.location = kwargs.get('location')
            self.status = kwargs.get('status', 'scheduled')
            self.notes = kwargs.get('notes')
            self.homework_assigned = kwargs.get('homework_assigned')
            self.homework_completed = kwargs.get('homework_completed')
            self.created_at = kwargs.get('created_at')
            self.updated_at = kwargs.get('updated_at')
    
    @classmethod
    def create_table(cls):
        """创建课程表"""
        query = '''
            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id INTEGER NOT NULL,
                student_id INTEGER NOT NULL,
                subject VARCHAR(100) NOT NULL,
                course_time DATETIME NOT NULL,
                duration INTEGER NOT NULL,
                location VARCHAR(255),
                status VARCHAR(20) DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'completed', 'cancelled', 'rescheduled')),
                notes TEXT,
                homework_assigned BOOLEAN DEFAULT FALSE,
                homework_completed BOOLEAN DEFAULT FALSE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (teacher_id) REFERENCES users(id),
                FOREIGN KEY (student_id) REFERENCES users(id)
            )
        '''
        db.execute_query(query)
        
        # 创建索引
        indexes = [
            'CREATE INDEX IF NOT EXISTS idx_courses_teacher_id ON courses(teacher_id)',
            'CREATE INDEX IF NOT EXISTS idx_courses_student_id ON courses(student_id)',
            'CREATE INDEX IF NOT EXISTS idx_courses_course_time ON courses(course_time)',
            'CREATE INDEX IF NOT EXISTS idx_courses_status ON courses(status)',
            'CREATE INDEX IF NOT EXISTS idx_courses_subject ON courses(subject)'
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
            query += ' AND course_time BETWEEN ? AND ?'
            params.extend([start_date, end_date])
        
        query += ' ORDER BY course_time ASC'
        results = db.execute_query(query, params)
        return [cls.from_dict(dict(row)) for row in results]
    
    @classmethod
    def get_by_student(cls, student_id, start_date=None, end_date=None):
        """获取学生的课程"""
        query = 'SELECT * FROM courses WHERE student_id = ?'
        params = [student_id]
        
        if start_date and end_date:
            query += ' AND course_time BETWEEN ? AND ?'
            params.extend([start_date, end_date])
        
        query += ' ORDER BY course_time ASC'
        results = db.execute_query(query, params)
        return [cls.from_dict(dict(row)) for row in results]
    
    @classmethod
    def get_upcoming_courses(cls, teacher_id, limit=10):
        """获取即将到来的课程"""
        query = '''
            SELECT * FROM courses 
            WHERE teacher_id = ? AND course_time > datetime('now') AND status = 'scheduled'
            ORDER BY course_time ASC 
            LIMIT ?
        '''
        results = db.execute_query(query, (teacher_id, limit))
        return [cls.from_dict(dict(row)) for row in results]
    
    @classmethod
    def get_courses_with_details(cls, teacher_id=None, student_id=None, start_date=None, end_date=None):
        """获取带有用户详情的课程信息"""
        query = '''
            SELECT c.*, 
                   t.name as teacher_name, t.phone as teacher_phone,
                   s.name as student_name, s.phone as student_phone
            FROM courses c
            LEFT JOIN users t ON c.teacher_id = t.id
            LEFT JOIN users s ON c.student_id = s.id
            WHERE 1=1
        '''
        params = []
        
        if teacher_id:
            query += ' AND c.teacher_id = ?'
            params.append(teacher_id)
        
        if student_id:
            query += ' AND c.student_id = ?'
            params.append(student_id)
        
        if start_date and end_date:
            query += ' AND c.course_time BETWEEN ? AND ?'
            params.extend([start_date, end_date])
        
        query += ' ORDER BY c.course_time ASC'
        results = db.execute_query(query, params)
        
        courses = []
        for row in results:
            course_data = dict(row)
            course = cls.from_dict(course_data)
            course.teacher_name = course_data.get('teacher_name')
            course.teacher_phone = course_data.get('teacher_phone')
            course.student_name = course_data.get('student_name')
            course.student_phone = course_data.get('student_phone')
            courses.append(course)
        
        return courses
    
    @classmethod
    def from_dict(cls, data):
        """从字典创建课程对象"""
        return cls(
            id=data.get('id'),
            teacher_id=data.get('teacher_id'),
            student_id=data.get('student_id'),
            subject=data.get('subject'),
            course_time=data.get('course_time'),
            duration=data.get('duration'),
            location=data.get('location'),
            status=data.get('status', 'scheduled'),
            notes=data.get('notes'),
            homework_assigned=data.get('homework_assigned', False),
            homework_completed=data.get('homework_completed', False),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )
    
    def to_dict(self):
        """转换为字典"""
        data = {
            'id': self.id,
            'teacher_id': self.teacher_id,
            'student_id': self.student_id,
            'subject': self.subject,
            'course_time': self.course_time,
            'duration': self.duration,
            'location': self.location,
            'status': self.status,
            'notes': self.notes,
            'homework_assigned': self.homework_assigned,
            'homework_completed': self.homework_completed,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
        
        # 添加额外的用户信息（如果存在）
        if hasattr(self, 'teacher_name'):
            data['teacher_name'] = self.teacher_name
            data['teacher_phone'] = self.teacher_phone
            data['student_name'] = self.student_name
            data['student_phone'] = self.student_phone
        
        return data
    
    def save(self):
        """保存课程"""
        if self.id:
            # 更新现有课程
            query = '''
                UPDATE courses SET 
                    teacher_id = ?, student_id = ?, subject = ?, course_time = ?,
                    duration = ?, location = ?, status = ?, notes = ?,
                    homework_assigned = ?, homework_completed = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            '''
            params = (
                self.teacher_id, self.student_id, self.subject, self.course_time,
                self.duration, self.location, self.status, self.notes,
                self.homework_assigned, self.homework_completed, self.id
            )
            db.execute_update(query, params)
        else:
            # 创建新课程
            query = '''
                INSERT INTO courses (
                    teacher_id, student_id, subject, course_time, duration,
                    location, status, notes, homework_assigned, homework_completed
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            params = (
                self.teacher_id, self.student_id, self.subject, self.course_time,
                self.duration, self.location, self.status, self.notes,
                self.homework_assigned, self.homework_completed
            )
            self.id = db.execute_insert(query, params)
        return self
    
    def delete(self):
        """删除课程"""
        if self.id:
            query = 'DELETE FROM courses WHERE id = ?'
            return db.execute_delete(query, (self.id,))
        return False