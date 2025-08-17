from datetime import datetime
from app.database import db

class QuestionBank(db.Model):
    """题库模型"""
    __tablename__ = 'question_banks'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(100))  # 题库分类：语法、词汇、阅读等
    difficulty_level = db.Column(db.Enum('beginner', 'intermediate', 'advanced', name='difficulty_levels'), 
                                nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_public = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 关系定义
    creator = db.relationship('User', backref='created_question_banks')
    
    def __repr__(self):
        return f'<QuestionBank {self.name}>'
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'difficulty_level': self.difficulty_level,
            'created_by': self.created_by,
            'creator_name': self.creator.name if self.creator else None,
            'is_public': self.is_public,
            'question_count': self.get_question_count(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_question_count(self):
        """获取题目数量"""
        return Question.query.filter_by(question_bank_id=self.id).count()

class Question(db.Model):
    """题目模型"""
    __tablename__ = 'questions'
    
    id = db.Column(db.Integer, primary_key=True)
    question_bank_id = db.Column(db.Integer, db.ForeignKey('question_banks.id'), nullable=False)
    question_type = db.Column(db.Enum('multiple_choice', 'true_false', 'fill_blank', 'essay', 'listening', 'speaking', 
                                     name='question_types'), nullable=False)
    title = db.Column(db.String(500), nullable=False)
    content = db.Column(db.Text, nullable=False)  # 题目内容
    options = db.Column(db.Text)  # JSON格式存储选项（选择题用）
    correct_answer = db.Column(db.Text)  # 正确答案
    explanation = db.Column(db.Text)  # 答案解析
    points = db.Column(db.Integer, default=1, nullable=False)  # 分值
    difficulty_level = db.Column(db.Enum('beginner', 'intermediate', 'advanced', name='question_difficulty_levels'), 
                                nullable=False)
    tags = db.Column(db.String(500))  # 标签，逗号分隔
    audio_file = db.Column(db.String(500))  # 听力题音频文件路径
    image_file = db.Column(db.String(500))  # 图片文件路径
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 关系定义
    question_bank = db.relationship('QuestionBank', backref='questions')
    creator = db.relationship('User', backref='created_questions')
    
    def __repr__(self):
        return f'<Question {self.title[:50]}>'
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'question_bank_id': self.question_bank_id,
            'question_bank_name': self.question_bank.name if self.question_bank else None,
            'question_type': self.question_type,
            'title': self.title,
            'content': self.content,
            'options': self.options,
            'correct_answer': self.correct_answer,
            'explanation': self.explanation,
            'points': self.points,
            'difficulty_level': self.difficulty_level,
            'tags': self.tags.split(',') if self.tags else [],
            'audio_file': self.audio_file,
            'image_file': self.image_file,
            'created_by': self.created_by,
            'creator_name': self.creator.name if self.creator else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def check_answer(self, user_answer):
        """检查答案是否正确"""
        if self.question_type in ['multiple_choice', 'true_false']:
            return str(user_answer).strip().lower() == str(self.correct_answer).strip().lower()
        elif self.question_type == 'fill_blank':
            # 填空题可能有多个正确答案
            correct_answers = [ans.strip().lower() for ans in self.correct_answer.split('|')]
            return str(user_answer).strip().lower() in correct_answers
        else:
            # 主观题需要人工评分
            return None
    
    def get_tags_list(self):
        """获取标签列表"""
        return self.tags.split(',') if self.tags else []
    
    def set_tags_list(self, tags_list):
        """设置标签列表"""
        self.tags = ','.join(tags_list) if tags_list else None