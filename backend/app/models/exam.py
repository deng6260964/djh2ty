from datetime import datetime
from app.database import db


class Exam(db.Model):
    """考试模型"""

    __tablename__ = "exams"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # 时间设置
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False)  # 考试时长（分钟）

    # 考试配置
    total_points = db.Column(db.Integer, default=100, nullable=False)  # 总分
    passing_score = db.Column(db.Integer, default=60, nullable=False)  # 及格分数
    max_attempts = db.Column(db.Integer, default=1, nullable=False)  # 最大尝试次数
    shuffle_questions = db.Column(db.Boolean, default=False, nullable=False)  # 是否打乱题目顺序
    show_results = db.Column(db.Boolean, default=True, nullable=False)  # 是否显示结果

    # 考试状态
    status = db.Column(
        db.Enum(
            "draft", "published", "in_progress", "ended", "graded", name="exam_status"
        ),
        default="draft",
        nullable=False,
    )

    # 权限设置
    is_public = db.Column(db.Boolean, default=False, nullable=False)
    allowed_students = db.Column(db.Text)  # JSON格式存储允许参加考试的学生ID列表

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # 关系定义
    course = db.relationship("Course", backref="exams")
    creator = db.relationship(
        "User", foreign_keys=[created_by], backref="created_exams"
    )

    def __repr__(self):
        return f"<Exam {self.title}>"

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "course_id": self.course_id,
            "created_by": self.created_by,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_minutes": self.duration_minutes,
            "total_points": self.total_points,
            "passing_score": self.passing_score,
            "max_attempts": self.max_attempts,
            "shuffle_questions": self.shuffle_questions,
            "show_results": self.show_results,
            "is_public": self.is_public,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def get_question_count(self):
        """获取考试题目数量"""
        return ExamQuestion.query.filter_by(exam_id=self.id).count()

    def get_submission_count(self):
        """获取考试提交数量"""
        return ExamSubmission.query.filter_by(exam_id=self.id).count()

    def is_active(self):
        """检查考试是否正在进行"""
        now = datetime.utcnow()
        return self.status == "published" and self.start_time <= now <= self.end_time

    def is_ended(self):
        """检查考试是否已结束"""
        now = datetime.utcnow()
        return now > self.end_time or self.status in ["ended", "graded"]


class ExamQuestion(db.Model):
    """考试题目关联模型"""

    __tablename__ = "exam_questions"

    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey("exams.id"), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey("questions.id"), nullable=False)
    points = db.Column(db.Integer, nullable=False)  # 该题在此考试中的分值
    order_index = db.Column(db.Integer, nullable=False)  # 题目顺序
    is_required = db.Column(db.Boolean, default=True, nullable=False)  # 是否必答

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # 关系定义
    exam = db.relationship("Exam", backref="exam_questions")
    question = db.relationship("Question", backref="exam_questions")

    # 唯一约束：同一考试中不能重复添加同一题目
    __table_args__ = (
        db.UniqueConstraint("exam_id", "question_id", name="unique_exam_question"),
    )

    def __repr__(self):
        return f"<ExamQuestion {self.exam_id}-{self.question_id}>"

    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "exam_id": self.exam_id,
            "question_id": self.question_id,
            "question_title": self.question.title if self.question else None,
            "question_type": self.question.question_type if self.question else None,
            "points": self.points,
            "order_index": self.order_index,
            "is_required": self.is_required,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ExamSubmission(db.Model):
    """考试提交记录模型"""

    __tablename__ = "exam_submissions"

    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey("exams.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # 提交状态
    status = db.Column(
        db.Enum(
            "in_progress", "submitted", "graded", "expired", name="submission_status"
        ),
        default="in_progress",
        nullable=False,
    )

    # 时间记录
    started_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    submitted_at = db.Column(db.DateTime)
    graded_at = db.Column(db.DateTime)

    # 分数记录
    total_score = db.Column(db.Float, default=0.0)  # 总得分
    auto_score = db.Column(db.Float, default=0.0)  # 自动评分得分
    manual_score = db.Column(db.Float, default=0.0)  # 人工评分得分

    # 考试统计
    attempt_number = db.Column(db.Integer, default=1, nullable=False)  # 第几次尝试
    time_spent_minutes = db.Column(db.Integer)  # 实际用时（分钟）

    # 评分信息
    graded_by = db.Column(db.Integer, db.ForeignKey("users.id"))  # 评分教师
    grading_notes = db.Column(db.Text)  # 评分备注

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # 关系定义
    exam = db.relationship("Exam", backref="submissions")
    student = db.relationship(
        "User", backref="exam_submissions", foreign_keys=[student_id]
    )
    grader = db.relationship(
        "User", backref="exam_graded_submissions", foreign_keys=[graded_by]
    )

    def __repr__(self):
        return f"<ExamSubmission {self.exam_id}-{self.student_id}>"

    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "exam_id": self.exam_id,
            "exam_title": self.exam.title if self.exam else None,
            "student_id": self.student_id,
            "student_name": self.student.name if self.student else None,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "submitted_at": self.submitted_at.isoformat()
            if self.submitted_at
            else None,
            "graded_at": self.graded_at.isoformat() if self.graded_at else None,
            "total_score": self.total_score,
            "auto_score": self.auto_score,
            "manual_score": self.manual_score,
            "attempt_number": self.attempt_number,
            "time_spent_minutes": self.time_spent_minutes,
            "graded_by": self.graded_by,
            "grader_name": self.grader.name if self.grader else None,
            "grading_notes": self.grading_notes,
            "is_passed": self.is_passed(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def is_passed(self):
        """检查是否及格"""
        if self.exam and self.total_score is not None:
            return self.total_score >= self.exam.passing_score
        return False

    def calculate_final_score(self):
        """计算最终得分"""
        self.total_score = self.auto_score + self.manual_score
        return self.total_score


class ExamAnswer(db.Model):
    """学生答题记录模型"""

    __tablename__ = "exam_answers"

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(
        db.Integer, db.ForeignKey("exam_submissions.id"), nullable=False
    )
    question_id = db.Column(db.Integer, db.ForeignKey("questions.id"), nullable=False)

    # 答案内容
    answer_content = db.Column(db.Text)  # 学生答案
    is_correct = db.Column(db.Boolean)  # 是否正确（客观题自动判断）

    # 评分信息
    score = db.Column(db.Float, default=0.0)  # 得分
    max_score = db.Column(db.Float, nullable=False)  # 满分
    is_auto_graded = db.Column(db.Boolean, default=False, nullable=False)  # 是否自动评分

    # 评分详情
    graded_by = db.Column(db.Integer, db.ForeignKey("users.id"))  # 评分教师（主观题）
    grading_notes = db.Column(db.Text)  # 评分备注
    graded_at = db.Column(db.DateTime)  # 评分时间

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # 关系定义
    submission = db.relationship("ExamSubmission", backref="answers")
    question = db.relationship("Question", backref="exam_answers")
    grader = db.relationship("User", backref="graded_answers", foreign_keys=[graded_by])

    # 唯一约束：同一提交中不能重复回答同一题目
    __table_args__ = (
        db.UniqueConstraint(
            "submission_id", "question_id", name="unique_submission_question"
        ),
    )

    def __repr__(self):
        return f"<ExamAnswer {self.submission_id}-{self.question_id}>"

    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "submission_id": self.submission_id,
            "question_id": self.question_id,
            "question_title": self.question.title if self.question else None,
            "question_type": self.question.question_type if self.question else None,
            "answer_content": self.answer_content,
            "is_correct": self.is_correct,
            "score": self.score,
            "max_score": self.max_score,
            "is_auto_graded": self.is_auto_graded,
            "graded_by": self.graded_by,
            "grader_name": self.grader.name if self.grader else None,
            "grading_notes": self.grading_notes,
            "graded_at": self.graded_at.isoformat() if self.graded_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def auto_grade(self):
        """自动评分（仅适用于客观题）"""
        if self.question and self.question.question_type in [
            "multiple_choice",
            "true_false",
            "fill_blank",
        ]:
            self.is_correct = self.question.check_answer(self.answer_content)
            if self.is_correct:
                self.score = self.max_score
            else:
                self.score = 0.0
            self.is_auto_graded = True
            self.graded_at = datetime.utcnow()
            return True
        return False
