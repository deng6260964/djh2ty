import uuid
from datetime import datetime
from app.database import db


class PracticeAnswer(db.Model):
    """练习答案模型"""

    __tablename__ = "practice_answers"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    practice_session_id = db.Column(db.String(36), db.ForeignKey("practice_sessions.id"), nullable=False)
    practice_question_id = db.Column(db.String(36), db.ForeignKey("practice_questions.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    
    # 答案内容
    answer_content = db.Column(db.Text, nullable=False)  # 用户提交的答案
    
    # 评分信息
    is_correct = db.Column(db.Boolean)  # 是否正确
    score = db.Column(db.Float, default=0.0)  # 得分
    max_score = db.Column(db.Float, default=1.0)  # 满分
    
    # 反馈信息
    feedback = db.Column(db.Text)  # 即时反馈内容
    explanation = db.Column(db.Text)  # 解析说明
    
    # 时间跟踪
    time_spent = db.Column(db.Integer, default=0)  # 答题用时（秒）
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # 答案元数据
    answer_data = db.Column(db.JSON)  # 存储答案的详细数据（如选择题选项、填空题答案等）
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # 关系定义
    user = db.relationship("User", backref="practice_answers")

    # 复合唯一约束：同一会话中的同一题目只能有一个答案
    __table_args__ = (
        db.UniqueConstraint("practice_session_id", "practice_question_id", name="uq_session_question_answer"),
        db.Index("idx_user_answers", "user_id", "submitted_at"),
        db.Index("idx_session_answers", "practice_session_id"),
    )

    def __repr__(self):
        return f"<PracticeAnswer {self.user_id}-{self.practice_question_id}>"

    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "practice_session_id": self.practice_session_id,
            "practice_question_id": self.practice_question_id,
            "user_id": self.user_id,
            "answer_content": self.answer_content,
            "is_correct": self.is_correct,
            "score": self.score,
            "max_score": self.max_score,
            "feedback": self.feedback,
            "explanation": self.explanation,
            "time_spent": self.time_spent,
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
            "answer_data": self.answer_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def to_dict_with_question(self):
        """转换为包含题目信息的字典格式"""
        result = self.to_dict()
        if self.practice_question and self.practice_question.question:
            result["question"] = self.practice_question.question.to_dict()
        return result

    def get_score_percentage(self):
        """获取得分百分比"""
        if self.max_score == 0:
            return 0
        return round((self.score / self.max_score) * 100, 2)

    def is_answered(self):
        """检查是否已答题"""
        return self.answer_content is not None and self.answer_content.strip() != ""

    def is_graded(self):
        """检查是否已评分"""
        return self.is_correct is not None

    def set_correct(self, score=None):
        """设置答案为正确"""
        self.is_correct = True
        if score is not None:
            self.score = score
        else:
            self.score = self.max_score
        self.updated_at = datetime.utcnow()

    def set_incorrect(self, score=0.0):
        """设置答案为错误"""
        self.is_correct = False
        self.score = score
        self.updated_at = datetime.utcnow()

    def set_partial_correct(self, score):
        """设置答案为部分正确"""
        self.is_correct = score >= (self.max_score * 0.5)  # 50%以上算正确
        self.score = score
        self.updated_at = datetime.utcnow()

    @classmethod
    def get_session_answers(cls, session_id):
        """获取会话的所有答案"""
        return cls.query.filter_by(practice_session_id=session_id).all()

    @classmethod
    def get_user_answers_for_practice(cls, user_id, practice_id):
        """获取用户在指定练习中的所有答案"""
        from app.models.practice_session import PracticeSession
        return cls.query.join(PracticeSession).filter(
            PracticeSession.practice_id == practice_id,
            cls.user_id == user_id
        ).all()

    @classmethod
    def get_question_statistics(cls, practice_question_id):
        """获取题目的统计信息"""
        answers = cls.query.filter_by(practice_question_id=practice_question_id).all()
        total_answers = len(answers)
        if total_answers == 0:
            return {
                "total_answers": 0,
                "correct_answers": 0,
                "accuracy_rate": 0,
                "average_score": 0,
                "average_time": 0
            }
        
        correct_answers = sum(1 for answer in answers if answer.is_correct)
        total_score = sum(answer.score for answer in answers)
        total_time = sum(answer.time_spent for answer in answers)
        
        return {
            "total_answers": total_answers,
            "correct_answers": correct_answers,
            "accuracy_rate": round((correct_answers / total_answers) * 100, 2),
            "average_score": round(total_score / total_answers, 2),
            "average_time": round(total_time / total_answers, 2)
        }