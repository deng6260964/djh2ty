from datetime import datetime
from .database import db

class HomeworkAnswer:
    """作业答案模型"""
    
    def __init__(self, data=None, **kwargs):
        if data:
            # 从字典初始化
            self.id = data.get('id')
            self.homework_id = data.get('homework_id')
            self.student_id = data.get('student_id')
            self.question_id = data.get('question_id')
            self.answer = data.get('answer', '')
            self.is_correct = data.get('is_correct', False)
            self.score = data.get('score', 0)
            self.submitted_at = data.get('submitted_at')
            self.created_at = data.get('created_at')
            self.updated_at = data.get('updated_at')
        else:
            # 从关键字参数初始化
            self.id = kwargs.get('id')
            self.homework_id = kwargs.get('homework_id')
            self.student_id = kwargs.get('student_id')
            self.question_id = kwargs.get('question_id')
            self.answer = kwargs.get('answer', '')
            self.is_correct = kwargs.get('is_correct', False)
            self.score = kwargs.get('score', 0)
            self.submitted_at = kwargs.get('submitted_at')
            self.created_at = kwargs.get('created_at')
            self.updated_at = kwargs.get('updated_at')
    
    @staticmethod
    def create_table():
        """创建作业答案表"""
        query = '''
        CREATE TABLE IF NOT EXISTS homework_answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            homework_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            question_id INTEGER NOT NULL,
            answer TEXT NOT NULL,
            is_correct BOOLEAN DEFAULT FALSE,
            score INTEGER DEFAULT 0,
            submitted_at DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (homework_id) REFERENCES homework(id),
            FOREIGN KEY (student_id) REFERENCES users(id),
            FOREIGN KEY (question_id) REFERENCES questions(id)
        )
        '''
        db.execute_query(query)
        
        # 创建索引
        indexes = [
            'CREATE INDEX IF NOT EXISTS idx_homework_answers_homework_id ON homework_answers(homework_id)',
            'CREATE INDEX IF NOT EXISTS idx_homework_answers_student_id ON homework_answers(student_id)',
            'CREATE INDEX IF NOT EXISTS idx_homework_answers_question_id ON homework_answers(question_id)',
            'CREATE UNIQUE INDEX IF NOT EXISTS idx_homework_answers_unique ON homework_answers(homework_id, student_id, question_id)'
        ]
        
        for index in indexes:
            db.execute_query(index)
    
    @staticmethod
    def find_by_homework_and_student(homework_id, student_id):
        """根据作业ID和学生ID查找答案"""
        query = 'SELECT * FROM homework_answers WHERE homework_id = ? AND student_id = ?'
        results = db.execute_query(query, (homework_id, student_id))
        return [HomeworkAnswer(dict(zip([col[0] for col in db.get_cursor().description], row))) for row in results]
    
    @staticmethod
    def find_by_id(answer_id):
        """根据ID查找答案"""
        query = 'SELECT * FROM homework_answers WHERE id = ?'
        result = db.execute_query(query, (answer_id,))
        if result:
            return HomeworkAnswer(dict(zip([col[0] for col in db.get_cursor().description], result[0])))
        return None
    
    @staticmethod
    def get_student_homework_score(homework_id, student_id):
        """获取学生作业总分"""
        query = 'SELECT SUM(score) as total_score FROM homework_answers WHERE homework_id = ? AND student_id = ?'
        result = db.execute_query(query, (homework_id, student_id))
        return result[0][0] if result and result[0][0] else 0
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'homework_id': self.homework_id,
            'student_id': self.student_id,
            'question_id': self.question_id,
            'answer': self.answer,
            'is_correct': self.is_correct,
            'score': self.score,
            'submitted_at': self.submitted_at,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    def save(self):
        """保存答案"""
        now = datetime.now().isoformat()
        
        if self.id:
            # 更新现有答案
            query = '''
            UPDATE homework_answers 
            SET answer = ?, is_correct = ?, score = ?, submitted_at = ?, updated_at = ?
            WHERE id = ?
            '''
            params = (self.answer, self.is_correct, self.score, self.submitted_at, now, self.id)
            db.execute_query(query, params)
        else:
            # 创建新答案
            self.created_at = now
            self.updated_at = now
            if not self.submitted_at:
                self.submitted_at = now
            
            query = '''
            INSERT INTO homework_answers (homework_id, student_id, question_id, answer, is_correct, score, submitted_at, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            params = (self.homework_id, self.student_id, self.question_id, self.answer, 
                     self.is_correct, self.score, self.submitted_at, self.created_at, self.updated_at)
            self.id = db.execute_insert(query, params)
        
        return self.id