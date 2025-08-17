from datetime import datetime
from app.database import db
import os

class File(db.Model):
    """文件模型"""
    __tablename__ = 'files'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)  # 原始文件名
    stored_filename = db.Column(db.String(255), nullable=False)  # 存储的文件名（通常是UUID）
    file_path = db.Column(db.String(500), nullable=False)  # 文件存储路径
    file_size = db.Column(db.BigInteger, nullable=False)  # 文件大小（字节）
    file_type = db.Column(db.String(100), nullable=False)  # MIME类型
    file_extension = db.Column(db.String(10))  # 文件扩展名
    file_category = db.Column(db.Enum('homework_attachment', 'submission_file', 'question_audio', 
                                     'question_image', 'course_material', 'avatar', 'other', 
                                     name='file_categories'), nullable=False)
    related_id = db.Column(db.Integer)  # 关联的业务对象ID
    related_type = db.Column(db.String(50))  # 关联的业务对象类型
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_public = db.Column(db.Boolean, default=False, nullable=False)
    download_count = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 关系定义
    uploader = db.relationship('User', backref='uploaded_files')
    
    def __repr__(self):
        return f'<File {self.filename}>'
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'filename': self.filename,
            'stored_filename': self.stored_filename,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'file_size_human': self.get_file_size_human(),
            'file_type': self.file_type,
            'file_extension': self.file_extension,
            'file_category': self.file_category,
            'related_id': self.related_id,
            'related_type': self.related_type,
            'uploaded_by': self.uploaded_by,
            'uploader_name': self.uploader.name if self.uploader else None,
            'is_public': self.is_public,
            'download_count': self.download_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_file_size_human(self):
        """获取人类可读的文件大小"""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def get_download_url(self):
        """获取下载URL"""
        return f"/api/files/{self.id}/download"
    
    def increment_download_count(self):
        """增加下载次数"""
        self.download_count += 1
        db.session.commit()
    
    def delete_file(self):
        """删除物理文件"""
        try:
            if os.path.exists(self.file_path):
                os.remove(self.file_path)
            return True
        except Exception as e:
            print(f"Error deleting file {self.file_path}: {e}")
            return False
    
    @staticmethod
    def get_allowed_extensions():
        """获取允许的文件扩展名"""
        return {
            'homework_attachment': ['.pdf', '.doc', '.docx', '.txt', '.jpg', '.jpeg', '.png'],
            'submission_file': ['.pdf', '.doc', '.docx', '.txt', '.jpg', '.jpeg', '.png'],
            'question_audio': ['.mp3', '.wav', '.m4a', '.ogg'],
            'question_image': ['.jpg', '.jpeg', '.png', '.gif', '.svg'],
            'course_material': ['.pdf', '.doc', '.docx', '.ppt', '.pptx', '.txt'],
            'avatar': ['.jpg', '.jpeg', '.png'],
            'other': ['.pdf', '.doc', '.docx', '.txt', '.jpg', '.jpeg', '.png']
        }
    
    @staticmethod
    def is_allowed_file(filename, category):
        """检查文件是否允许上传"""
        allowed_extensions = File.get_allowed_extensions()
        if category not in allowed_extensions:
            return False
        
        file_ext = os.path.splitext(filename)[1].lower()
        return file_ext in allowed_extensions[category]
    
    @staticmethod
    def get_max_file_size(category):
        """获取不同类别文件的最大大小限制（字节）"""
        size_limits = {
            'homework_attachment': 50 * 1024 * 1024,  # 50MB
            'submission_file': 50 * 1024 * 1024,      # 50MB
            'question_audio': 20 * 1024 * 1024,       # 20MB
            'question_image': 10 * 1024 * 1024,       # 10MB
            'course_material': 100 * 1024 * 1024,     # 100MB
            'avatar': 5 * 1024 * 1024,                # 5MB
            'other': 50 * 1024 * 1024                 # 50MB
        }
        return size_limits.get(category, 50 * 1024 * 1024)