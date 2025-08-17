from datetime import datetime
from app.database import db

class Course(db.Model):
    """课程模型"""
    __tablename__ = 'courses'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    course_type = db.Column(db.Enum('one_to_one', 'one_to_many', name='course_types'), nullable=False)
    max_students = db.Column(db.Integer, default=1, nullable=False)
    schedule = db.Column(db.String(500))  # JSON格式存储时间安排
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 关系定义
    teacher = db.relationship('User', backref='taught_courses', foreign_keys=[teacher_id])
    
    def __repr__(self):
        return f'<Course {self.name}>'
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'course_type': self.course_type,
            'max_students': self.max_students,
            'schedule': self.schedule,
            'teacher_id': self.teacher_id,
            'teacher_name': self.teacher.name if self.teacher else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class CourseEnrollment(db.Model):
    """课程选课关系模型"""
    __tablename__ = 'course_enrollments'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # 关系定义
    course = db.relationship('Course', backref='enrollments')
    student = db.relationship('User', backref='enrolled_courses', foreign_keys=[student_id])
    
    # 唯一约束：同一学生不能重复选择同一课程
    __table_args__ = (db.UniqueConstraint('course_id', 'student_id', name='unique_course_student'),)
    
    def __repr__(self):
        return f'<CourseEnrollment {self.course_id}-{self.student_id}>'
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'course_id': self.course_id,
            'student_id': self.student_id,
            'course_name': self.course.name if self.course else None,
            'student_name': self.student.name if self.student else None,
            'enrolled_at': self.enrolled_at.isoformat() if self.enrolled_at else None,
            'is_active': self.is_active
        }