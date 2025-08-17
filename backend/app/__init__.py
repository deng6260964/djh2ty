from flask import Flask, jsonify, request
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from flask_cors import CORS
from config.config import config
from app.utils.config_manager import config_manager
from app.utils.logger import logger_manager
from app.utils.jwt_middleware import JWTMiddleware
from app.utils.session_manager import SessionManager
from app.database import db, migrate
import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime

# 初始化扩展
jwt = JWTManager()
jwt_middleware = None
session_manager = None

def create_app(config_name='development'):
    """应用工厂函数"""
    app = Flask(__name__)
    
    # 加载配置
    from config.config import config
    app.config.from_object(config[config_name])
    
    # 初始化配置管理器
    config_manager.create_directories()
    
    # 初始化日志系统
    logger_manager.setup_app_logger(app)
    logger_manager.log_request(app)
    logger_manager.log_error(app)
    logger_manager.setup_security_logger(app)
    
    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    
    # 绑定扩展到应用对象，供测试和中间件使用
    app.db = db
    app.jwt = jwt
    
    # 初始化JWT中间件和会话管理器
    global jwt_middleware, session_manager
    jwt_middleware = JWTMiddleware()
    jwt_middleware.init_app(app)
    session_manager = SessionManager()
    
    # 使用配置管理器获取CORS配置
    cors_config = config_manager.get_cors_config()
    CORS(app, 
         origins=cors_config['origins'],
         supports_credentials=True,
         allow_headers=cors_config['allow_headers'],
         methods=cors_config['methods'])
    
    # JWT、中间件和错误处理已通过logger_manager配置
    
    # 注册蓝图
    from app.routes.auth import auth_bp
    from app.routes.users import users_bp
    from app.routes.courses import courses_bp
    from app.routes.assignments import assignments_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(courses_bp, url_prefix='/api/courses')
    app.register_blueprint(assignments_bp, url_prefix='/api/assignments')
    
    # 健康检查端点
    @app.route('/api/health')
    def health_check():
        return {'status': 'healthy', 'message': 'English Tutoring System API is running', 'timestamp': datetime.utcnow().isoformat()}
    
    # 错误处理已通过logger_manager配置
    
    return app