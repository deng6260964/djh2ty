from datetime import datetime
from app.database import db

class HomeworkSubmission(db.Model):
    """作业提交模型"""
    __tablename__ = 'homework_submissions'
    
    id = db.Column(db.Integer, primary_key=True)
    homework_id = db.Column(db.Integer, db.ForeignKey('homeworks.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text)  # 文本内容
    submission_files = db.Column(db.Text)  # JSON格式存储文件列表
    score = db.Column(db.Integer)  # 评分
    feedback = db.Column(db.Text)  # 教师反馈
    status = db.Column(db.Enum('draft', 'submitted', 'graded', 'returned', name='submission_status'), 
                      default='draft', nullable=False)
    submitted_at = db.Column(db.DateTime)
    graded_at = db.Column(db.DateTime)
    graded_by = db.Column(db.Integer, db.ForeignKey('users.id'))  # 评分教师
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 关系定义
    homework = db.relationship('Homework', backref='submissions')
    student = db.relationship('User', backref='homework_submissions', foreign_keys=[student_id])
    grader = db.relationship('User', backref='graded_submissions', foreign_keys=[graded_by])
    
    # 唯一约束：同一学生对同一作业只能有一个提交
    __table_args__ = (db.UniqueConstraint('homework_id', 'student_id', name='unique_homework_student'),)
    
    def __repr__(self):
        return f'<HomeworkSubmission {self.homework_id}-{self.student_id}>'
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'homework_id': self.homework_id,
            'homework_title': self.homework.title if self.homework else None,
            'student_id': self.student_id,
            'student_name': self.student.name if self.student else None,
            'content': self.content,
            'submission_files': self.submission_files,
            'score': self.score,
            'feedback': self.feedback,
            'status': self.status,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'graded_at': self.graded_at.isoformat() if self.graded_at else None,
            'graded_by': self.graded_by,
            'grader_name': self.grader.name if self.grader else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def submit(self):
        """提交作业"""
        if self.status == 'draft':
            self.status = 'submitted'
            self.submitted_at = datetime.utcnow()
            return True
        return False
    
    def grade(self, score, feedback=None, grader_id=None):
        """评分"""
        if self.status == 'submitted':
            self.score = score
            self.feedback = feedback
            self.graded_by = grader_id
            self.graded_at = datetime.utcnow()
            self.status = 'graded'
            return True
        return False
    
    @property
    def is_late(self):
        """检查是否迟交"""
        if self.submitted_at and self.homework and self.homework.due_date:
            return self.submitted_at > self.homework.due_date
        return False
    
    @property
    def grade_percentage(self):
        """获取评分百分比"""
        if self.score is not None and self.homework and self.homework.max_score:
            return (self.score / self.homework.max_score) * 100
        return None