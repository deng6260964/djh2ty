from datetime import datetime
import json
from .database import db

class Question:
    """题目模型类"""
    
    def __init__(self, data=None, **kwargs):
        # 如果传入的是字典，使用字典的值
        if isinstance(data, dict):
            self.id = data.get('id')
            self.teacher_id = data.get('teacher_id')
            self.title = data.get('title')
            self.content = data.get('content')
            self.question_type = data.get('question_type') or data.get('type')
            self.difficulty = data.get('difficulty')
            self.category = data.get('category')
            self.tags = data.get('tags')
            self.options = data.get('options')
            self.correct_answer = data.get('correct_answer')
            self.explanation = data.get('explanation')
            self.points = data.get('points', 1)
            self.estimated_time = data.get('estimated_time', 60)
            self.usage_count = data.get('usage_count', 0)
            self.status = data.get('status', 'active')
            self.created_at = data.get('created_at')
            self.updated_at = data.get('updated_at')
        else:
            # 兼容原有的参数方式
            self.id = kwargs.get('id', data)
            self.teacher_id = kwargs.get('teacher_id')
            self.title = kwargs.get('title')
            self.content = kwargs.get('content')
            self.question_type = kwargs.get('question_type') or kwargs.get('type')
            self.difficulty = kwargs.get('difficulty')
            self.category = kwargs.get('category')
            self.tags = kwargs.get('tags')
            self.options = kwargs.get('options')
            self.correct_answer = kwargs.get('correct_answer')
            self.explanation = kwargs.get('explanation')
            self.points = kwargs.get('points', 1)
            self.estimated_time = kwargs.get('estimated_time', 60)
            self.usage_count = kwargs.get('usage_count', 0)
            self.status = kwargs.get('status', 'active')
            self.created_at = kwargs.get('created_at')
            self.updated_at = kwargs.get('updated_at')
    
    @classmethod
    def create_table(cls):
        """创建题目表"""
        query = '''
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id INTEGER NOT NULL,
                title VARCHAR(255) NOT NULL,
                content TEXT NOT NULL,
                question_type VARCHAR(50) NOT NULL CHECK (question_type IN ('single_choice', 'multiple_choice', 'true_false', 'fill_blank', 'essay', 'listening', 'reading')),
                difficulty VARCHAR(20) NOT NULL CHECK (difficulty IN ('easy', 'medium', 'hard')),
                category VARCHAR(100) NOT NULL,
                tags TEXT,
                options TEXT,
                correct_answer TEXT,
                explanation TEXT,
                points INTEGER DEFAULT 1,
                estimated_time INTEGER DEFAULT 60,
                usage_count INTEGER DEFAULT 0,
                status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'archived')),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (teacher_id) REFERENCES users(id)
            )
        '''
        db.execute_query(query)
        
        # 创建索引
        indexes = [
            'CREATE INDEX IF NOT EXISTS idx_questions_teacher_id ON questions(teacher_id)',
            'CREATE INDEX IF NOT EXISTS idx_questions_type ON questions(question_type)',
            'CREATE INDEX IF NOT EXISTS idx_questions_difficulty ON questions(difficulty)',
            'CREATE INDEX IF NOT EXISTS idx_questions_category ON questions(category)',
            'CREATE INDEX IF NOT EXISTS idx_questions_status ON questions(status)',
            'CREATE INDEX IF NOT EXISTS idx_questions_created_at ON questions(created_at)'
        ]
        for index in indexes:
            db.execute_query(index)
    
    @classmethod
    def find_by_id(cls, question_id):
        """根据ID查找题目"""
        query = 'SELECT * FROM questions WHERE id = ?'
        result = db.execute_query(query, (question_id,))
        if result:
            return cls.from_dict(dict(result[0]))
        return None
    
    @classmethod
    def get_by_teacher(cls, teacher_id, category=None, difficulty=None, question_type=None, status='active'):
        """获取教师的题目"""
        query = 'SELECT * FROM questions WHERE teacher_id = ? AND status = ?'
        params = [teacher_id, status]
        
        if category:
            query += ' AND category = ?'
            params.append(category)
        
        if difficulty:
            query += ' AND difficulty = ?'
            params.append(difficulty)
        
        if question_type:
            query += ' AND question_type = ?'
            params.append(question_type)
        
        query += ' ORDER BY created_at DESC'
        results = db.execute_query(query, params)
        return [cls.from_dict(dict(row)) for row in results]
    
    @classmethod
    def search_questions(cls, teacher_id, keyword=None, category=None, difficulty=None, question_type=None, limit=50, offset=0):
        """搜索题目"""
        query = 'SELECT * FROM questions WHERE teacher_id = ? AND status = "active"'
        params = [teacher_id]
        
        if keyword:
            query += ' AND (title LIKE ? OR content LIKE ?)'
            keyword_param = f'%{keyword}%'
            params.extend([keyword_param, keyword_param])
        
        if category:
            query += ' AND category = ?'
            params.append(category)
        
        if difficulty:
            query += ' AND difficulty = ?'
            params.append(difficulty)
        
        if question_type:
            query += ' AND question_type = ?'
            params.append(question_type)
        
        query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
        params.extend([limit, offset])
        
        results = db.execute_query(query, params)
        return [cls.from_dict(dict(row)) for row in results]
    
    @classmethod
    def get_random_questions(cls, teacher_id, count, difficulty_distribution=None, categories=None, question_types=None):
        """随机获取题目（用于自动组卷）"""
        questions = []
        
        if difficulty_distribution:
            # 按难度比例分配
            for difficulty, ratio in difficulty_distribution.items():
                question_count = int(count * ratio)
                if question_count > 0:
                    query = '''
                        SELECT * FROM questions 
                        WHERE teacher_id = ? AND difficulty = ? AND status = "active"
                    '''
                    params = [teacher_id, difficulty]
                    
                    if categories:
                        placeholders = ','.join(['?' for _ in categories])
                        query += f' AND category IN ({placeholders})'
                        params.extend(categories)
                    
                    if question_types:
                        placeholders = ','.join(['?' for _ in question_types])
                        query += f' AND question_type IN ({placeholders})'
                        params.extend(question_types)
                    
                    query += ' ORDER BY RANDOM() LIMIT ?'
                    params.append(question_count)
                    
                    results = db.execute_query(query, params)
                    questions.extend([cls.from_dict(dict(row)) for row in results])
        else:
            # 随机获取
            query = 'SELECT * FROM questions WHERE teacher_id = ? AND status = "active"'
            params = [teacher_id]
            
            if categories:
                placeholders = ','.join(['?' for _ in categories])
                query += f' AND category IN ({placeholders})'
                params.extend(categories)
            
            if question_types:
                placeholders = ','.join(['?' for _ in question_types])
                query += f' AND question_type IN ({placeholders})'
                params.extend(question_types)
            
            query += ' ORDER BY RANDOM() LIMIT ?'
            params.append(count)
            
            results = db.execute_query(query, params)
            questions = [cls.from_dict(dict(row)) for row in results]
        
        return questions
    
    @classmethod
    def get_categories(cls, teacher_id):
        """获取教师的题目分类"""
        query = 'SELECT DISTINCT category FROM questions WHERE teacher_id = ? AND status = "active" ORDER BY category'
        results = db.execute_query(query, (teacher_id,))
        return [row['category'] for row in results]
    
    @classmethod
    def get_statistics(cls, teacher_id):
        """获取题目统计信息"""
        query = '''
            SELECT 
                COUNT(*) as total_count,
                SUM(CASE WHEN difficulty = 'easy' THEN 1 ELSE 0 END) as easy_count,
                SUM(CASE WHEN difficulty = 'medium' THEN 1 ELSE 0 END) as medium_count,
                SUM(CASE WHEN difficulty = 'hard' THEN 1 ELSE 0 END) as hard_count,
                SUM(CASE WHEN question_type = 'single_choice' THEN 1 ELSE 0 END) as single_choice_count,
                SUM(CASE WHEN question_type = 'multiple_choice' THEN 1 ELSE 0 END) as multiple_choice_count,
                SUM(CASE WHEN question_type = 'true_false' THEN 1 ELSE 0 END) as true_false_count,
                SUM(CASE WHEN question_type = 'fill_blank' THEN 1 ELSE 0 END) as fill_blank_count,
                SUM(CASE WHEN question_type = 'essay' THEN 1 ELSE 0 END) as essay_count
            FROM questions 
            WHERE teacher_id = ? AND status = 'active'
        '''
        result = db.execute_query(query, (teacher_id,))
        return dict(result[0]) if result else {}
    
    @classmethod
    def from_dict(cls, data):
        """从字典创建题目对象"""
        return cls(
            id=data.get('id'),
            teacher_id=data.get('teacher_id'),
            title=data.get('title'),
            content=data.get('content'),
            question_type=data.get('question_type'),
            difficulty=data.get('difficulty'),
            category=data.get('category'),
            tags=data.get('tags'),
            options=data.get('options'),
            correct_answer=data.get('correct_answer'),
            explanation=data.get('explanation'),
            points=data.get('points', 1),
            estimated_time=data.get('estimated_time', 60),
            usage_count=data.get('usage_count', 0),
            status=data.get('status', 'active'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'teacher_id': self.teacher_id,
            'title': self.title,
            'content': self.content,
            'question_type': self.question_type,
            'difficulty': self.difficulty,
            'category': self.category,
            'tags': json.loads(self.tags) if isinstance(self.tags, str) else self.tags,
            'options': json.loads(self.options) if isinstance(self.options, str) else self.options,
            'correct_answer': self.correct_answer,
            'explanation': self.explanation,
            'points': self.points,
            'estimated_time': self.estimated_time,
            'usage_count': self.usage_count,
            'status': self.status,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    def save(self):
        """保存题目"""
        if self.id:
            # 更新现有题目
            query = '''
                UPDATE questions SET 
                    title = ?, content = ?, question_type = ?, difficulty = ?,
                    category = ?, tags = ?, options = ?, correct_answer = ?,
                    explanation = ?, points = ?, estimated_time = ?, status = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            '''
            params = (
                self.title, self.content, self.question_type, self.difficulty,
                self.category, self.tags, self.options, self.correct_answer,
                self.explanation, self.points, self.estimated_time, self.status, self.id
            )
            db.execute_update(query, params)
        else:
            # 创建新题目
            query = '''
                INSERT INTO questions (
                    teacher_id, title, content, question_type, difficulty,
                    category, tags, options, correct_answer, explanation,
                    points, estimated_time, usage_count, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            params = (
                self.teacher_id, self.title, self.content, self.question_type,
                self.difficulty, self.category, self.tags, self.options,
                self.correct_answer, self.explanation, self.points,
                self.estimated_time, self.usage_count, self.status
            )
            self.id = db.execute_insert(query, params)
        return self
    
    def delete(self):
        """删除题目（软删除）"""
        if self.id:
            query = 'UPDATE questions SET status = "archived", updated_at = CURRENT_TIMESTAMP WHERE id = ?'
            return db.execute_update(query, (self.id,))
        return False
    
    def increment_usage(self):
        """增加使用次数"""
        if self.id:
            query = 'UPDATE questions SET usage_count = usage_count + 1 WHERE id = ?'
            db.execute_update(query, (self.id,))
            self.usage_count += 1