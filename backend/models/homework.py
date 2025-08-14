from datetime import datetime
import json
from .database import db

class Homework:
    """作业模型类"""
    
    def __init__(self, data=None, **kwargs):
        if data is not None:
            # 从字典初始化
            self.id = data.get('id')
            self.teacher_id = data.get('teacher_id')
            self.student_id = data.get('student_id')
            self.title = data.get('title')
            self.description = data.get('description')
            question_ids = data.get('question_ids')
            self.question_ids = question_ids if isinstance(question_ids, str) else json.dumps(question_ids or [])
            self.total_points = data.get('total_points')
            self.due_date = data.get('due_date')
            self.status = data.get('status', 'assigned')
            self.submitted_at = data.get('submitted_at')
            self.graded_at = data.get('graded_at')
            self.score = data.get('score')
            self.feedback = data.get('feedback')
            self.auto_generated = data.get('auto_generated', False)
            self.created_at = data.get('created_at')
            self.updated_at = data.get('updated_at')
        else:
            # 从关键字参数初始化
            self.id = kwargs.get('id')
            self.teacher_id = kwargs.get('teacher_id')
            self.student_id = kwargs.get('student_id')
            self.title = kwargs.get('title')
            self.description = kwargs.get('description')
            question_ids = kwargs.get('question_ids')
            self.question_ids = question_ids if isinstance(question_ids, str) else json.dumps(question_ids or [])
            self.total_points = kwargs.get('total_points')
            self.due_date = kwargs.get('due_date')
            self.status = kwargs.get('status', 'assigned')
            self.submitted_at = kwargs.get('submitted_at')
            self.graded_at = kwargs.get('graded_at')
            self.score = kwargs.get('score')
            self.feedback = kwargs.get('feedback')
            self.auto_generated = kwargs.get('auto_generated', False)
            self.created_at = kwargs.get('created_at')
            self.updated_at = kwargs.get('updated_at')
    
    @classmethod
    def create_table(cls):
        """创建作业表"""
        # 先删除现有表（如果存在）
        drop_query = 'DROP TABLE IF EXISTS homework'
        db.execute_query(drop_query)
        
        # 创建新表
        query = '''
            CREATE TABLE homework (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id INTEGER NOT NULL,
                student_id INTEGER NOT NULL,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                question_ids TEXT NOT NULL,
                total_points INTEGER NOT NULL,
                due_date DATETIME NOT NULL,
                status VARCHAR(20) DEFAULT 'assigned' CHECK (status IN ('assigned', 'submitted', 'graded', 'overdue')),
                submitted_at DATETIME,
                graded_at DATETIME,
                score INTEGER,
                feedback TEXT,
                auto_generated BOOLEAN DEFAULT FALSE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (teacher_id) REFERENCES users(id),
                FOREIGN KEY (student_id) REFERENCES users(id)
            )
        '''
        db.execute_query(query)
        
        # 创建索引
        indexes = [
            'CREATE INDEX IF NOT EXISTS idx_homework_teacher_id ON homework(teacher_id)',
            'CREATE INDEX IF NOT EXISTS idx_homework_student_id ON homework(student_id)',
            'CREATE INDEX IF NOT EXISTS idx_homework_status ON homework(status)',
            'CREATE INDEX IF NOT EXISTS idx_homework_due_date ON homework(due_date)',
            'CREATE INDEX IF NOT EXISTS idx_homework_created_at ON homework(created_at)'
        ]
        for index in indexes:
            db.execute_query(index)
    
    @classmethod
    def find_by_id(cls, homework_id):
        """根据ID查找作业"""
        query = 'SELECT * FROM homework WHERE id = ?'
        result = db.execute_query(query, (homework_id,))
        if result:
            return cls.from_dict(dict(result[0]))
        return None
    
    @classmethod
    def get_by_teacher(cls, teacher_id, status=None, start_date=None, end_date=None):
        """获取教师的作业"""
        query = 'SELECT * FROM homework WHERE teacher_id = ?'
        params = [teacher_id]
        
        if status:
            query += ' AND status = ?'
            params.append(status)
        
        if start_date and end_date:
            query += ' AND created_at BETWEEN ? AND ?'
            params.extend([start_date, end_date])
        
        query += ' ORDER BY created_at DESC'
        results = db.execute_query(query, params)
        return [cls.from_dict(dict(row)) for row in results]
    
    @classmethod
    def get_by_student(cls, student_id, status=None, start_date=None, end_date=None):
        """获取学生的作业"""
        query = 'SELECT * FROM homework WHERE student_id = ?'
        params = [student_id]
        
        if status:
            query += ' AND status = ?'
            params.append(status)
        
        if start_date and end_date:
            query += ' AND created_at BETWEEN ? AND ?'
            params.extend([start_date, end_date])
        
        query += ' ORDER BY due_date ASC'
        results = db.execute_query(query, params)
        return [cls.from_dict(dict(row)) for row in results]
    
    @classmethod
    def get_overdue_homework(cls, teacher_id=None):
        """获取过期作业"""
        query = '''
            SELECT * FROM homework 
            WHERE due_date < datetime('now') AND status IN ('assigned', 'submitted')
        '''
        params = []
        
        if teacher_id:
            query += ' AND teacher_id = ?'
            params.append(teacher_id)
        
        query += ' ORDER BY due_date DESC'
        results = db.execute_query(query, params)
        return [cls.from_dict(dict(row)) for row in results]
    
    @classmethod
    def get_homework_with_details(cls, homework_id):
        """获取带有详细信息的作业"""
        query = '''
            SELECT h.*, 
                   t.name as teacher_name, t.phone as teacher_phone,
                   s.name as student_name, s.phone as student_phone
            FROM homework h
            LEFT JOIN users t ON h.teacher_id = t.id
            LEFT JOIN users s ON h.student_id = s.id
            WHERE h.id = ?
        '''
        result = db.execute_query(query, (homework_id,))
        if result:
            homework_data = dict(result[0])
            homework = cls.from_dict(homework_data)
            homework.teacher_name = homework_data.get('teacher_name')
            homework.teacher_phone = homework_data.get('teacher_phone')
            homework.student_name = homework_data.get('student_name')
            homework.student_phone = homework_data.get('student_phone')
            return homework
        return None
    
    @classmethod
    def get_statistics(cls, teacher_id, start_date=None, end_date=None):
        """获取作业统计信息"""
        query = '''
            SELECT 
                COUNT(*) as total_count,
                SUM(CASE WHEN status = 'assigned' THEN 1 ELSE 0 END) as assigned_count,
                SUM(CASE WHEN status = 'submitted' THEN 1 ELSE 0 END) as submitted_count,
                SUM(CASE WHEN status = 'graded' THEN 1 ELSE 0 END) as graded_count,
                SUM(CASE WHEN status = 'overdue' THEN 1 ELSE 0 END) as overdue_count,
                AVG(CASE WHEN score IS NOT NULL THEN CAST(score AS FLOAT) / total_points * 100 ELSE NULL END) as avg_score_percentage
            FROM homework 
            WHERE teacher_id = ?
        '''
        params = [teacher_id]
        
        if start_date and end_date:
            query += ' AND created_at BETWEEN ? AND ?'
            params.extend([start_date, end_date])
        
        result = db.execute_query(query, params)
        return dict(result[0]) if result else {}
    
    @classmethod
    def from_dict(cls, data):
        """从字典创建作业对象"""
        return cls(
            id=data.get('id'),
            teacher_id=data.get('teacher_id'),
            student_id=data.get('student_id'),
            title=data.get('title'),
            description=data.get('description'),
            question_ids=data.get('question_ids'),
            total_points=data.get('total_points'),
            due_date=data.get('due_date'),
            status=data.get('status', 'assigned'),
            submitted_at=data.get('submitted_at'),
            graded_at=data.get('graded_at'),
            score=data.get('score'),
            feedback=data.get('feedback'),
            auto_generated=data.get('auto_generated', False),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )
    
    def to_dict(self):
        """转换为字典"""
        data = {
            'id': self.id,
            'teacher_id': self.teacher_id,
            'student_id': self.student_id,
            'title': self.title,
            'description': self.description,
            'question_ids': json.loads(self.question_ids) if isinstance(self.question_ids, str) else self.question_ids,
            'total_points': self.total_points,
            'due_date': self.due_date,
            'status': self.status,
            'submitted_at': self.submitted_at,
            'graded_at': self.graded_at,
            'score': self.score,
            'feedback': self.feedback,
            'auto_generated': self.auto_generated,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
        
        # 添加额外的用户信息（如果存在）
        if hasattr(self, 'teacher_name'):
            data['teacher_name'] = self.teacher_name
            data['teacher_phone'] = self.teacher_phone
            data['student_name'] = self.student_name
            data['student_phone'] = self.student_phone
        
        return data
    
    def save(self):
        """保存作业"""
        if self.id:
            # 更新现有作业
            query = '''
                UPDATE homework SET 
                    title = ?, description = ?, question_ids = ?, total_points = ?,
                    due_date = ?, status = ?, submitted_at = ?, graded_at = ?,
                    score = ?, feedback = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            '''
            params = (
                self.title, self.description, self.question_ids, self.total_points,
                self.due_date, self.status, self.submitted_at, self.graded_at,
                self.score, self.feedback, self.id
            )
            db.execute_update(query, params)
        else:
            # 创建新作业
            query = '''
                INSERT INTO homework (
                    teacher_id, student_id, title, description, question_ids,
                    total_points, due_date, status, auto_generated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            params = (
                self.teacher_id, self.student_id, self.title, self.description,
                self.question_ids, self.total_points, self.due_date, self.status,
                self.auto_generated
            )
            self.id = db.execute_insert(query, params)
        return self
    
    def submit(self):
        """提交作业"""
        if self.id and self.status == 'assigned':
            self.status = 'submitted'
            self.submitted_at = datetime.now().isoformat()
            query = '''
                UPDATE homework SET 
                    status = 'submitted', submitted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            '''
            db.execute_update(query, (self.id,))
            return True
        return False
    
    def grade(self, score, feedback=None):
        """批改作业"""
        if self.id and self.status == 'submitted':
            self.status = 'graded'
            self.score = score
            self.feedback = feedback
            self.graded_at = datetime.now().isoformat()
            query = '''
                UPDATE homework SET 
                    status = 'graded', score = ?, feedback = ?, graded_at = CURRENT_TIMESTAMP, 
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            '''
            db.execute_update(query, (score, feedback, self.id))
            return True
        return False
    
    def delete(self):
        """删除作业"""
        if self.id:
            query = 'DELETE FROM homework WHERE id = ?'
            return db.execute_delete(query, (self.id,))
        return False
    
    def get_questions(self):
        """获取作业中的题目"""
        from .question import Question
        
        question_ids = json.loads(self.question_ids) if isinstance(self.question_ids, str) else self.question_ids
        if not question_ids:
            return []
        
        placeholders = ','.join(['?' for _ in question_ids])
        query = f'SELECT * FROM questions WHERE id IN ({placeholders}) ORDER BY id'
        results = db.execute_query(query, question_ids)
        return [Question.from_dict(dict(row)) for row in results]

class HomeworkAnswer:
    """作业答案模型类"""
    
    def __init__(self, id=None, homework_id=None, question_id=None, student_answer=None,
                 is_correct=None, points_earned=None, created_at=None, updated_at=None):
        self.id = id
        self.homework_id = homework_id
        self.question_id = question_id
        self.student_answer = student_answer
        self.is_correct = is_correct
        self.points_earned = points_earned
        self.created_at = created_at
        self.updated_at = updated_at
    
    @classmethod
    def create_table(cls):
        """创建作业答案表"""
        query = '''
            CREATE TABLE IF NOT EXISTS homework_answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                homework_id INTEGER NOT NULL,
                question_id INTEGER NOT NULL,
                student_answer TEXT,
                is_correct BOOLEAN,
                points_earned INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (homework_id) REFERENCES homework(id),
                FOREIGN KEY (question_id) REFERENCES questions(id),
                UNIQUE(homework_id, question_id)
            )
        '''
        db.execute_query(query)
        
        # 创建索引
        indexes = [
            'CREATE INDEX IF NOT EXISTS idx_homework_answers_homework_id ON homework_answers(homework_id)',
            'CREATE INDEX IF NOT EXISTS idx_homework_answers_question_id ON homework_answers(question_id)'
        ]
        for index in indexes:
            db.execute_query(index)
    
    @classmethod
    def get_by_homework(cls, homework_id):
        """获取作业的所有答案"""
        query = 'SELECT * FROM homework_answers WHERE homework_id = ? ORDER BY question_id'
        results = db.execute_query(query, (homework_id,))
        return [cls.from_dict(dict(row)) for row in results]
    
    @classmethod
    def from_dict(cls, data):
        """从字典创建答案对象"""
        return cls(
            id=data.get('id'),
            homework_id=data.get('homework_id'),
            question_id=data.get('question_id'),
            student_answer=data.get('student_answer'),
            is_correct=data.get('is_correct'),
            points_earned=data.get('points_earned', 0),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'homework_id': self.homework_id,
            'question_id': self.question_id,
            'student_answer': self.student_answer,
            'is_correct': self.is_correct,
            'points_earned': self.points_earned,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    def save(self):
        """保存答案"""
        if self.id:
            # 更新现有答案
            query = '''
                UPDATE homework_answers SET 
                    student_answer = ?, is_correct = ?, points_earned = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            '''
            params = (self.student_answer, self.is_correct, self.points_earned, self.id)
            db.execute_update(query, params)
        else:
            # 创建新答案
            query = '''
                INSERT OR REPLACE INTO homework_answers (
                    homework_id, question_id, student_answer, is_correct, points_earned
                ) VALUES (?, ?, ?, ?, ?)
            '''
            params = (
                self.homework_id, self.question_id, self.student_answer,
                self.is_correct, self.points_earned
            )
            self.id = db.execute_insert(query, params)
        return self