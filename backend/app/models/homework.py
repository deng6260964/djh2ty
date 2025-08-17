from datetime import datetime
from app.database import db


class Homework(db.Model):
    """作业模型"""

    __tablename__ = "homeworks"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    homework_type = db.Column(
        db.Enum(
            "writing",
            "reading",
            "listening",
            "speaking",
            "mixed",
            name="homework_types",
        ),
        nullable=False,
    )
    max_score = db.Column(db.Integer, default=100, nullable=False)
    due_date = db.Column(db.DateTime, nullable=False)
    instructions = db.Column(db.Text)  # 作业说明
    attachment_files = db.Column(db.Text)  # JSON格式存储附件文件列表
    is_published = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # 关系定义
    course = db.relationship("Course", backref="homeworks")
    teacher = db.relationship(
        "User", backref="assigned_homeworks", foreign_keys=[teacher_id]
    )

    def __repr__(self):
        return f"<Homework {self.title}>"

    def to_dict(self):
        """转换为字典格式"""
        # 处理attachment_files字段
        attachment_files = self.attachment_files
        if attachment_files:
            try:
                import json

                attachment_files = json.loads(attachment_files)
            except (json.JSONDecodeError, TypeError):
                attachment_files = self.attachment_files

        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "course_id": self.course_id,
            "course_name": self.course.name if self.course else None,
            "teacher_id": self.teacher_id,
            "teacher_name": self.teacher.name if self.teacher else None,
            "homework_type": self.homework_type,
            "max_score": self.max_score,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "instructions": self.instructions,
            "attachment_files": attachment_files,
            "is_published": self.is_published,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @property
    def is_overdue(self):
        """检查作业是否已过期"""
        return datetime.utcnow() > self.due_date if self.due_date else False

    @property
    def status(self):
        """获取作业状态"""
        if not self.is_published:
            return "draft"  # 草稿

        now = datetime.utcnow()
        if now < self.due_date:
            return "active"  # 进行中
        else:
            return "closed"  # 已截止

    def get_status_for_student(self, student_id):
        """获取学生视角的作业状态"""
        from app.models.homework_submission import HomeworkSubmission

        # 检查是否有提交记录
        submission = HomeworkSubmission.query.filter_by(
            homework_id=self.id, student_id=student_id
        ).first()

        if not submission:
            if self.is_overdue:
                return "overdue"  # 逾期未提交
            else:
                return "not_started"  # 未开始

        if submission.status == "draft":
            if self.is_overdue:
                return "overdue_draft"  # 逾期草稿
            else:
                return "draft"  # 草稿
        elif submission.status == "submitted":
            return "submitted"  # 已提交
        elif submission.status == "graded":
            return "graded"  # 已批改
        else:
            return "unknown"

    def get_submission_count(self):
        """获取提交数量"""
        from app.models.homework_submission import HomeworkSubmission

        return HomeworkSubmission.query.filter_by(homework_id=self.id).count()

    def get_graded_count(self):
        """获取已评分数量"""
        from app.models.homework_submission import HomeworkSubmission

        return (
            HomeworkSubmission.query.filter_by(homework_id=self.id)
            .filter(HomeworkSubmission.score.isnot(None))
            .count()
        )
