import os
from datetime import timedelta

class Config:
    """基础配置类"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-string'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    DATABASE_PATH = os.environ.get('DATABASE_PATH') or 'database.db'
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    DATABASE_PATH = 'database.db'

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    DATABASE_PATH = os.environ.get('DATABASE_PATH') or '/app/data/database.db'

class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    DATABASE_PATH = ':memory:'  # 使用内存数据库进行测试

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
}

# 默认配置
default_config = config['development']