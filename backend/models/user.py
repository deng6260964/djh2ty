from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from .database import db

class User:
    """用户模型类"""
    
    def __init__(self, data=None, **kwargs):
        # 如果传入的是字典，使用字典的值
        if isinstance(data, dict):
            self.id = data.get('id')
            self.phone = data.get('phone')
            self.password_hash = data.get('password_hash')
            self.name = data.get('name')
            self.role = data.get('role')
            self.avatar_url = data.get('avatar_url')
            self.email = data.get('email')
            self.gender = data.get('gender')
            self.birth_date = data.get('birth_date')
            self.address = data.get('address')
            self.emergency_contact = data.get('emergency_contact')
            self.emergency_phone = data.get('emergency_phone')
            self.status = data.get('status', 'active')
            self.last_login_at = data.get('last_login_at')
            self.created_at = data.get('created_at')
            self.updated_at = data.get('updated_at')
        else:
            # 兼容原有的参数方式
            self.id = kwargs.get('id', data)
            self.phone = kwargs.get('phone')
            self.password_hash = kwargs.get('password_hash')
            self.name = kwargs.get('name')
            self.role = kwargs.get('role')
            self.avatar_url = kwargs.get('avatar_url')
            self.email = kwargs.get('email')
            self.gender = kwargs.get('gender')
            self.birth_date = kwargs.get('birth_date')
            self.address = kwargs.get('address')
            self.emergency_contact = kwargs.get('emergency_contact')
            self.emergency_phone = kwargs.get('emergency_phone')
            self.status = kwargs.get('status', 'active')
            self.last_login_at = kwargs.get('last_login_at')
            self.created_at = kwargs.get('created_at')
            self.updated_at = kwargs.get('updated_at')
    
    @classmethod
    def create_table(cls):
        """创建用户表"""
        query = '''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone VARCHAR(20) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                name VARCHAR(100) NOT NULL,
                role VARCHAR(20) NOT NULL CHECK (role IN ('teacher', 'student')),
                avatar_url VARCHAR(255),
                email VARCHAR(100),
                gender VARCHAR(10) CHECK (gender IN ('male', 'female', 'other')),
                birth_date DATE,
                address TEXT,
                emergency_contact VARCHAR(100),
                emergency_phone VARCHAR(20),
                status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'suspended')),
                last_login_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        '''
        db.execute_query(query)
        
        # 创建索引
        indexes = [
            'CREATE UNIQUE INDEX IF NOT EXISTS idx_users_phone ON users(phone)',
            'CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)',
            'CREATE INDEX IF NOT EXISTS idx_users_status ON users(status)',
            'CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at)'
        ]
        for index in indexes:
            db.execute_query(index)
    
    @classmethod
    def find_by_phone(cls, phone):
        """根据手机号查找用户"""
        query = 'SELECT * FROM users WHERE phone = ?'
        result = db.execute_query(query, (phone,))
        if result:
            return cls.from_dict(dict(result[0]))
        return None
    
    @classmethod
    def find_by_id(cls, user_id):
        """根据ID查找用户"""
        query = 'SELECT * FROM users WHERE id = ?'
        result = db.execute_query(query, (user_id,))
        if result:
            return cls.from_dict(dict(result[0]))
        return None
    
    @classmethod
    def get_all_students(cls):
        """获取所有学生"""
        query = 'SELECT * FROM users WHERE role = "student" ORDER BY created_at DESC'
        results = db.execute_query(query)
        return [cls.from_dict(dict(row)) for row in results]
    
    @classmethod
    def from_dict(cls, data):
        """从字典创建用户对象"""
        return cls(
            id=data.get('id'),
            phone=data.get('phone'),
            password_hash=data.get('password_hash'),
            name=data.get('name'),
            role=data.get('role'),
            avatar_url=data.get('avatar_url'),
            email=data.get('email'),
            gender=data.get('gender'),
            birth_date=data.get('birth_date'),
            address=data.get('address'),
            emergency_contact=data.get('emergency_contact'),
            emergency_phone=data.get('emergency_phone'),
            status=data.get('status', 'active'),
            last_login_at=data.get('last_login_at'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )
    
    def to_dict(self, include_password=False):
        """转换为字典"""
        data = {
            'id': self.id,
            'phone': self.phone,
            'name': self.name,
            'role': self.role,
            'avatar_url': self.avatar_url,
            'email': self.email,
            'gender': self.gender,
            'birth_date': self.birth_date,
            'address': self.address,
            'emergency_contact': self.emergency_contact,
            'emergency_phone': self.emergency_phone,
            'status': self.status,
            'last_login_at': self.last_login_at,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
        if include_password:
            data['password_hash'] = self.password_hash
        return data
    
    def save(self):
        """保存用户"""
        if self.id:
            # 更新现有用户
            query = '''
                UPDATE users SET 
                    phone = ?, name = ?, role = ?, avatar_url = ?, email = ?,
                    gender = ?, birth_date = ?, address = ?, emergency_contact = ?,
                    emergency_phone = ?, status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            '''
            params = (
                self.phone, self.name, self.role, self.avatar_url, self.email,
                self.gender, self.birth_date, self.address, self.emergency_contact,
                self.emergency_phone, self.status, self.id
            )
            db.execute_update(query, params)
        else:
            # 创建新用户
            query = '''
                INSERT INTO users (
                    phone, password_hash, name, role, avatar_url, email,
                    gender, birth_date, address, emergency_contact, emergency_phone, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            params = (
                self.phone, self.password_hash, self.name, self.role, self.avatar_url,
                self.email, self.gender, self.birth_date, self.address,
                self.emergency_contact, self.emergency_phone, self.status
            )
            self.id = db.execute_insert(query, params)
        return self
    
    def set_password(self, password):
        """设置密码"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)
    
    def update_last_login(self):
        """更新最后登录时间"""
        query = 'UPDATE users SET last_login_at = CURRENT_TIMESTAMP WHERE id = ?'
        db.execute_update(query, (self.id,))