import uuid
from datetime import datetime
from app.database import db


class PracticeSession(db.Model):
    """练习会话模型"""

    __tablename__ = "practice_sessions"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    practice_id = db.Column(db.String(36), db.ForeignKey("practices.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    
    # 会话状态
    status = db.Column(
        db.Enum("in_progress", "paused", "completed", "abandoned", name="session_status"),
        default="in_progress",
        nullable=False,
    )
    
    # 进度跟踪
    current_question_index = db.Column(db.Integer, default=0, nullable=False)  # 当前题目索引
    total_questions = db.Column(db.Integer, default=0, nullable=False)  # 总题目数
    answered_questions = db.Column(db.Integer, default=0, nullable=False)  # 已答题目数
    correct_answers = db.Column(db.Integer, default=0, nullable=False)  # 正确答案数
    
    # 时间跟踪
    started_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_activity_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    completed_at = db.Column(db.DateTime)
    total_time_spent = db.Column(db.Integer, default=0)  # 总用时（秒）
    
    # 会话配置和状态数据
    session_data = db.Column(db.JSON)  # 存储会话的各种状态数据
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # 关系定义
    user = db.relationship("User", backref="practice_sessions")
    answers = db.relationship(
        "PracticeAnswer", backref="practice_session", cascade="all, delete-orphan"
    )

    # 复合唯一约束：同一用户对同一练习只能有一个进行中的会话
    __table_args__ = (
        db.Index("idx_user_practice_status", "user_id", "practice_id", "status"),
        db.Index("idx_session_activity", "last_activity_at"),
    )

    def __repr__(self):
        return f"<PracticeSession {self.user_id}-{self.practice_id}>"

    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "practice_id": self.practice_id,
            "user_id": self.user_id,
            "status": self.status,
            "current_question_index": self.current_question_index,
            "total_questions": self.total_questions,
            "answered_questions": self.answered_questions,
            "correct_answers": self.correct_answers,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "last_activity_at": self.last_activity_at.isoformat() if self.last_activity_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "total_time_spent": self.total_time_spent,
            "session_data": self.session_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def get_progress_percentage(self):
        """获取进度百分比"""
        if self.total_questions == 0:
            return 0
        return round((self.answered_questions / self.total_questions) * 100, 2)

    def get_accuracy_percentage(self):
        """获取正确率百分比"""
        if self.answered_questions == 0:
            return 0
        return round((self.correct_answers / self.answered_questions) * 100, 2)

    def is_completed(self):
        """检查会话是否已完成"""
        return self.status == "completed"

    def is_in_progress(self):
        """检查会话是否进行中"""
        return self.status == "in_progress"

    def is_paused(self):
        """检查会话是否已暂停"""
        return self.status == "paused"

    def update_activity(self):
        """更新最后活动时间"""
        self.last_activity_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def complete_session(self):
        """完成会话"""
        self.status = "completed"
        self.completed_at = datetime.utcnow()
        self.update_activity()

    def pause_session(self):
        """暂停会话"""
        self.status = "paused"
        self.update_activity()

    def resume_session(self):
        """恢复会话"""
        self.status = "in_progress"
        self.update_activity()

    @classmethod
    def get_active_session(cls, user_id, practice_id):
        """获取用户在指定练习中的活跃会话"""
        return cls.query.filter_by(
            user_id=user_id,
            practice_id=practice_id,
            status="in_progress"
        ).first()

    @classmethod
    def get_user_sessions(cls, user_id, status=None):
        """获取用户的练习会话列表"""
        query = cls.query.filter_by(user_id=user_id)
        if status:
            query = query.filter_by(status=status)
        return query.order_by(cls.last_activity_at.desc()).all()