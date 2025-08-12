from datetime import datetime
import json
from .database import db

class Exam:
    """考试模型类"""
    
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
            self.start_time = data.get('start_time')
            self.end_time = data.get('end_time')
            self.duration = data.get('duration')
            self.status = data.get('status', 'scheduled')
            self.submitted_at = data.get('submitted_at')
            self.graded_at = data.get('graded_at')
            self.score = data.get('score')
            self.feedback = data.get('feedback')
            self.auto_generated = data.get('auto_generated', False)
            self.allow_review = data.get('allow_review', True)
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
            self.start_time = kwargs.get('start_time')
            self.end_time = kwargs.get('end_time')
            self.duration = kwargs.get('duration')
            self.status = kwargs.get('status', 'scheduled')
            self.submitted_at = kwargs.get('submitted_at')
            self.graded_at = kwargs.get('graded_at')
            self.score = kwargs.get('score')
            self.feedback = kwargs.get('feedback')
            self.auto_generated = kwargs.get('auto_generated', False)
            self.allow_review = kwargs.get('allow_review', True)
            self.created_at = kwargs.get('created_at')
            self.updated_at = kwargs.get('updated_at')
    
    @classmethod
    def create_table(cls):
        """创建考试表"""
        query = '''
            CREATE TABLE IF NOT EXISTS exams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id INTEGER NOT NULL,
                student_id INTEGER NOT NULL,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                question_ids TEXT NOT NULL,
                total_points INTEGER NOT NULL,
                duration INTEGER NOT NULL,
                start_time DATETIME NOT NULL,
                end_time DATETIME NOT NULL,
                status VARCHAR(20) DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'in_progress', 'submitted', 'graded', 'cancelled')),
                submitted_at DATETIME,
                graded_at DATETIME,
                score INTEGER,
                feedback TEXT,
                auto_generated BOOLEAN DEFAULT FALSE,
                allow_review BOOLEAN DEFAULT TRUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (teacher_id) REFERENCES users(id),
                FOREIGN KEY (student_id) REFERENCES users(id)
            )
        '''
        db.execute_query(query)
        
        # 创建索引
        indexes = [
            'CREATE INDEX IF NOT EXISTS idx_exams_teacher_id ON exams(teacher_id)',
            'CREATE INDEX IF NOT EXISTS idx_exams_student_id ON exams(student_id)',
            'CREATE INDEX IF NOT EXISTS idx_exams_status ON exams(status)',
            'CREATE INDEX IF NOT EXISTS idx_exams_start_time ON exams(start_time)',
            'CREATE INDEX IF NOT EXISTS idx_exams_created_at ON exams(created_at)'
        ]
        for index in indexes:
            db.execute_query(index)
    
    @classmethod
    def find_by_id(cls, exam_id):
        """根据ID查找考试"""
        query = 'SELECT * FROM exams WHERE id = ?'
        result = db.execute_query(query, (exam_id,))
        if result:
            return cls.from_dict(dict(result[0]))
        return None
    
    @classmethod
    def get_by_teacher(cls, teacher_id, status=None, start_date=None, end_date=None):
        """获取教师的考试"""
        query = 'SELECT * FROM exams WHERE teacher_id = ?'
        params = [teacher_id]
        
        if status:
            query += ' AND status = ?'
            params.append(status)
        
        if start_date and end_date:
            query += ' AND start_time BETWEEN ? AND ?'
            params.extend([start_date, end_date])
        
        query += ' ORDER BY start_time DESC'
        results = db.execute_query(query, params)
        return [cls.from_dict(dict(row)) for row in results]
    
    @classmethod
    def get_by_student(cls, student_id, status=None, start_date=None, end_date=None):
        """获取学生的考试"""
        query = 'SELECT * FROM exams WHERE student_id = ?'
        params = [student_id]
        
        if status:
            query += ' AND status = ?'
            params.append(status)
        
        if start_date and end_date:
            query += ' AND start_time BETWEEN ? AND ?'
            params.extend([start_date, end_date])
        
        query += ' ORDER BY start_time ASC'
        results = db.execute_query(query, params)
        return [cls.from_dict(dict(row)) for row in results]
    
    @classmethod
    def get_upcoming_exams(cls, student_id, limit=10):
        """获取即将到来的考试"""
        query = '''
            SELECT * FROM exams 
            WHERE student_id = ? AND start_time > datetime('now') AND status = 'scheduled'
            ORDER BY start_time ASC 
            LIMIT ?
        '''
        results = db.execute_query(query, (student_id, limit))
        return [cls.from_dict(dict(row)) for row in results]
    
    @classmethod
    def get_active_exams(cls, student_id):
        """获取正在进行的考试"""
        query = '''
            SELECT * FROM exams 
            WHERE student_id = ? AND status = 'in_progress'
            AND start_time <= datetime('now') AND end_time > datetime('now')
            ORDER BY start_time ASC
        '''
        results = db.execute_query(query, (student_id,))
        return [cls.from_dict(dict(row)) for row in results]
    
    @classmethod
    def get_exam_with_details(cls, exam_id):
        """获取带有详细信息的考试"""
        query = '''
            SELECT e.*, 
                   t.name as teacher_name, t.phone as teacher_phone,
                   s.name as student_name, s.phone as student_phone
            FROM exams e
            LEFT JOIN users t ON e.teacher_id = t.id
            LEFT JOIN users s ON e.student_id = s.id
            WHERE e.id = ?
        '''
        result = db.execute_query(query, (exam_id,))
        if result:
            exam_data = dict(result[0])
            exam = cls.from_dict(exam_data)
            exam.teacher_name = exam_data.get('teacher_name')
            exam.teacher_phone = exam_data.get('teacher_phone')
            exam.student_name = exam_data.get('student_name')
            exam.student_phone = exam_data.get('student_phone')
            return exam
        return None
    
    @classmethod
    def get_statistics(cls, teacher_id, start_date=None, end_date=None):
        """获取考试统计信息"""
        query = '''
            SELECT 
                COUNT(*) as total_count,
                SUM(CASE WHEN status = 'scheduled' THEN 1 ELSE 0 END) as scheduled_count,
                SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress_count,
                SUM(CASE WHEN status = 'submitted' THEN 1 ELSE 0 END) as submitted_count,
                SUM(CASE WHEN status = 'graded' THEN 1 ELSE 0 END) as graded_count,
                SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) as cancelled_count,
                AVG(CASE WHEN score IS NOT NULL THEN CAST(score AS FLOAT) / total_points * 100 ELSE NULL END) as avg_score_percentage
            FROM exams 
            WHERE teacher_id = ?
        '''
        params = [teacher_id]
        
        if start_date and end_date:
            query += ' AND start_time BETWEEN ? AND ?'
            params.extend([start_date, end_date])
        
        result = db.execute_query(query, params)
        return dict(result[0]) if result else {}
    
    @classmethod
    def from_dict(cls, data):
        """从字典创建考试对象"""
        return cls(
            id=data.get('id'),
            teacher_id=data.get('teacher_id'),
            student_id=data.get('student_id'),
            title=data.get('title'),
            description=data.get('description'),
            question_ids=data.get('question_ids'),
            total_points=data.get('total_points'),
            duration=data.get('duration'),
            start_time=data.get('start_time'),
            end_time=data.get('end_time'),
            status=data.get('status', 'scheduled'),
            submitted_at=data.get('submitted_at'),
            graded_at=data.get('graded_at'),
            score=data.get('score'),
            feedback=data.get('feedback'),
            auto_generated=data.get('auto_generated', False),
            allow_review=data.get('allow_review', True),
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
            'duration': self.duration,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'status': self.status,
            'submitted_at': self.submitted_at,
            'graded_at': self.graded_at,
            'score': self.score,
            'feedback': self.feedback,
            'auto_generated': self.auto_generated,
            'allow_review': self.allow_review,
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
        """保存考试"""
        if self.id:
            # 更新现有考试
            query = '''
                UPDATE exams SET 
                    title = ?, description = ?, question_ids = ?, total_points = ?,
                    duration = ?, start_time = ?, end_time = ?, status = ?,
                    submitted_at = ?, graded_at = ?, score = ?, feedback = ?,
                    allow_review = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            '''
            params = (
                self.title, self.description, self.question_ids, self.total_points,
                self.duration, self.start_time, self.end_time, self.status,
                self.submitted_at, self.graded_at, self.score, self.feedback,
                self.allow_review, self.id
            )
            db.execute_update(query, params)
        else:
            # 创建新考试
            query = '''
                INSERT INTO exams (
                    teacher_id, student_id, title, description, question_ids,
                    total_points, duration, start_time, end_time, status,
                    auto_generated, allow_review
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            params = (
                self.teacher_id, self.student_id, self.title, self.description,
                self.question_ids, self.total_points, self.duration,
                self.start_time, self.end_time, self.status,
                self.auto_generated, self.allow_review
            )
            self.id = db.execute_insert(query, params)
        return self
    
    def start(self):
        """开始考试"""
        if self.id and self.status == 'scheduled':
            current_time = datetime.now().isoformat()
            if current_time >= self.start_time and current_time <= self.end_time:
                self.status = 'in_progress'
                query = 'UPDATE exams SET status = "in_progress", updated_at = CURRENT_TIMESTAMP WHERE id = ?'
                db.execute_update(query, (self.id,))
                return True
        return False
    
    def submit(self):
        """提交考试"""
        if self.id and self.status == 'in_progress':
            self.status = 'submitted'
            self.submitted_at = datetime.now().isoformat()
            query = '''
                UPDATE exams SET 
                    status = 'submitted', submitted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            '''
            db.execute_update(query, (self.id,))
            return True
        return False
    
    def grade(self, score, feedback=None):
        """批改考试"""
        if self.id and self.status == 'submitted':
            self.status = 'graded'
            self.score = score
            self.feedback = feedback
            self.graded_at = datetime.now().isoformat()
            query = '''
                UPDATE exams SET 
                    status = 'graded', score = ?, feedback = ?, graded_at = CURRENT_TIMESTAMP, 
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            '''
            db.execute_update(query, (score, feedback, self.id))
            return True
        return False
    
    def cancel(self):
        """取消考试"""
        if self.id and self.status in ['scheduled', 'in_progress']:
            self.status = 'cancelled'
            query = 'UPDATE exams SET status = "cancelled", updated_at = CURRENT_TIMESTAMP WHERE id = ?'
            db.execute_update(query, (self.id,))
            return True
        return False
    
    def delete(self):
        """删除考试"""
        if self.id:
            query = 'DELETE FROM exams WHERE id = ?'
            return db.execute_delete(query, (self.id,))
        return False
    
    def get_questions(self):
        """获取考试中的题目"""
        from .question import Question
        
        question_ids = json.loads(self.question_ids) if isinstance(self.question_ids, str) else self.question_ids
        if not question_ids:
            return []
        
        placeholders = ','.join(['?' for _ in question_ids])
        query = f'SELECT * FROM questions WHERE id IN ({placeholders}) ORDER BY id'
        results = db.execute_query(query, question_ids)
        return [Question.from_dict(dict(row)) for row in results]
    
    def is_active(self):
        """检查考试是否正在进行"""
        current_time = datetime.now().isoformat()
        return (self.status == 'in_progress' and 
                self.start_time <= current_time <= self.end_time)
    
    def is_expired(self):
        """检查考试是否已过期"""
        current_time = datetime.now().isoformat()
        return current_time > self.end_time

class ExamAnswer:
    """考试答案模型类"""
    
    def __init__(self, id=None, exam_id=None, question_id=None, student_answer=None,
                 is_correct=None, points_earned=None, answer_time=None,
                 created_at=None, updated_at=None):
        self.id = id
        self.exam_id = exam_id
        self.question_id = question_id
        self.student_answer = student_answer
        self.is_correct = is_correct
        self.points_earned = points_earned
        self.answer_time = answer_time  # 答题用时（秒）
        self.created_at = created_at
        self.updated_at = updated_at
    
    @classmethod
    def create_table(cls):
        """创建考试答案表"""
        query = '''
            CREATE TABLE IF NOT EXISTS exam_answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exam_id INTEGER NOT NULL,
                question_id INTEGER NOT NULL,
                student_answer TEXT,
                is_correct BOOLEAN,
                points_earned INTEGER DEFAULT 0,
                answer_time INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (exam_id) REFERENCES exams(id),
                FOREIGN KEY (question_id) REFERENCES questions(id),
                UNIQUE(exam_id, question_id)
            )
        '''
        db.execute_query(query)
        
        # 创建索引
        indexes = [
            'CREATE INDEX IF NOT EXISTS idx_exam_answers_exam_id ON exam_answers(exam_id)',
            'CREATE INDEX IF NOT EXISTS idx_exam_answers_question_id ON exam_answers(question_id)'
        ]
        for index in indexes:
            db.execute_query(index)
    
    @classmethod
    def get_by_exam(cls, exam_id):
        """获取考试的所有答案"""
        query = 'SELECT * FROM exam_answers WHERE exam_id = ? ORDER BY question_id'
        results = db.execute_query(query, (exam_id,))
        return [cls.from_dict(dict(row)) for row in results]
    
    @classmethod
    def from_dict(cls, data):
        """从字典创建答案对象"""
        return cls(
            id=data.get('id'),
            exam_id=data.get('exam_id'),
            question_id=data.get('question_id'),
            student_answer=data.get('student_answer'),
            is_correct=data.get('is_correct'),
            points_earned=data.get('points_earned', 0),
            answer_time=data.get('answer_time'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'exam_id': self.exam_id,
            'question_id': self.question_id,
            'student_answer': self.student_answer,
            'is_correct': self.is_correct,
            'points_earned': self.points_earned,
            'answer_time': self.answer_time,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    def save(self):
        """保存答案"""
        if self.id:
            # 更新现有答案
            query = '''
                UPDATE exam_answers SET 
                    student_answer = ?, is_correct = ?, points_earned = ?, 
                    answer_time = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            '''
            params = (self.student_answer, self.is_correct, self.points_earned, 
                     self.answer_time, self.id)
            db.execute_update(query, params)
        else:
            # 创建新答案
            query = '''
                INSERT OR REPLACE INTO exam_answers (
                    exam_id, question_id, student_answer, is_correct, 
                    points_earned, answer_time
                ) VALUES (?, ?, ?, ?, ?, ?)
            '''
            params = (
                self.exam_id, self.question_id, self.student_answer,
                self.is_correct, self.points_earned, self.answer_time
            )
            self.id = db.execute_insert(query, params)
        return self