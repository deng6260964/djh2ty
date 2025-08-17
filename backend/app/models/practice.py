import uuid
from datetime import datetime
from app.database import db


class Practice(db.Model):
    """练习集模型"""

    __tablename__ = "practices"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    creator_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"))
    
    # 练习状态
    status = db.Column(
        db.Enum("draft", "published", "archived", name="practice_status"),
        default="draft",
        nullable=False,
    )
    
    # 练习配置参数
    settings = db.Column(db.JSON)  # 存储练习的各种配置参数
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # 关系定义
    creator = db.relationship("User", backref="created_practices")
    course = db.relationship("Course", backref="practices")
    questions = db.relationship(
        "PracticeQuestion", backref="practice", cascade="all, delete-orphan"
    )
    sessions = db.relationship(
        "PracticeSession", backref="practice", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Practice {self.title}>"

    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "creator_id": self.creator_id,
            "course_id": self.course_id,
            "status": self.status,
            "settings": self.settings,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def get_question_count(self):
        """获取练习题目数量"""
        from app.models.practice_question import PracticeQuestion
        return PracticeQuestion.query.filter_by(practice_id=self.id).count()

    def get_session_count(self):
        """获取练习会话数量"""
        from app.models.practice_session import PracticeSession
        return PracticeSession.query.filter_by(practice_id=self.id).count()

    def is_published(self):
        """检查练习是否已发布"""
        return self.status == "published"

    def is_archived(self):
        """检查练习是否已归档"""
        return self.status == "archived"