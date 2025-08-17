import uuid
from datetime import datetime
from app.database import db


class PracticeQuestion(db.Model):
    """练习题目关联模型"""

    __tablename__ = "practice_questions"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    practice_id = db.Column(db.String(36), db.ForeignKey("practices.id"), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey("questions.id"), nullable=False)
    
    # 题目在练习中的顺序
    order_index = db.Column(db.Integer, nullable=False, default=0)
    
    # 题目配置参数
    settings = db.Column(db.JSON)  # 存储题目在练习中的特定配置
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # 关系定义
    question = db.relationship("Question", backref="practice_questions")
    answers = db.relationship(
        "PracticeAnswer", backref="practice_question", cascade="all, delete-orphan"
    )

    # 复合唯一约束：同一练习中的题目不能重复
    __table_args__ = (
        db.UniqueConstraint("practice_id", "question_id", name="uq_practice_question"),
        db.Index("idx_practice_order", "practice_id", "order_index"),
    )

    def __repr__(self):
        return f"<PracticeQuestion {self.practice_id}-{self.question_id}>"

    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "practice_id": self.practice_id,
            "question_id": self.question_id,
            "order_index": self.order_index,
            "settings": self.settings,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def to_dict_with_question(self):
        """转换为包含题目信息的字典格式"""
        result = self.to_dict()
        if self.question:
            result["question"] = self.question.to_dict()
        return result

    def get_answer_count(self):
        """获取该题目的答案数量"""
        from app.models.practice_answer import PracticeAnswer
        return PracticeAnswer.query.filter_by(practice_question_id=self.id).count()

    @classmethod
    def get_by_practice_ordered(cls, practice_id):
        """按顺序获取练习中的所有题目"""
        return cls.query.filter_by(practice_id=practice_id).order_by(cls.order_index).all()

    @classmethod
    def get_max_order_index(cls, practice_id):
        """获取练习中题目的最大顺序号"""
        result = db.session.query(db.func.max(cls.order_index)).filter_by(practice_id=practice_id).scalar()
        return result if result is not None else -1