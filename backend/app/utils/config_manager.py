# -*- coding: utf-8 -*-
"""
配置管理模块
提供配置验证、环境变量管理和配置工具函数
"""

import os
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, env_file: Optional[str] = None):
        """初始化配置管理器
        
        Args:
            env_file: 环境变量文件路径，默认为.env
        """
        self.env_file = env_file or '.env'
        self.load_environment()
    
    def load_environment(self) -> bool:
        """加载环境变量
        
        Returns:
            bool: 是否成功加载
        """
        try:
            if os.path.exists(self.env_file):
                load_dotenv(self.env_file)
                logging.info(f"环境变量已从 {self.env_file} 加载")
                return True
            else:
                logging.warning(f"环境变量文件 {self.env_file} 不存在，使用系统环境变量")
                return False
        except Exception as e:
            logging.error(f"加载环境变量失败: {e}")
            return False
    
    def get_config_value(self, key: str, default: Any = None, required: bool = False) -> Any:
        """获取配置值
        
        Args:
            key: 配置键名
            default: 默认值
            required: 是否为必需配置
            
        Returns:
            配置值
            
        Raises:
            ValueError: 当required=True且配置不存在时
        """
        value = os.environ.get(key, default)
        
        if required and value is None:
            raise ValueError(f"必需的配置项 {key} 未设置")
        
        return value
    
    def validate_config(self, required_keys: list) -> Dict[str, bool]:
        """验证必需的配置项
        
        Args:
            required_keys: 必需的配置键列表
            
        Returns:
            Dict[str, bool]: 配置验证结果
        """
        validation_result = {}
        
        for key in required_keys:
            value = os.environ.get(key)
            validation_result[key] = value is not None and value.strip() != ''
            
            if not validation_result[key]:
                logging.warning(f"配置项 {key} 未设置或为空")
        
        return validation_result
    
    def get_database_config(self) -> Dict[str, str]:
        """获取数据库配置
        
        Returns:
            Dict[str, str]: 数据库配置字典
        """
        env = self.get_config_value('FLASK_ENV', 'development')
        
        if env == 'testing':
            return {
                'uri': 'sqlite:///:memory:',
                'track_modifications': False
            }
        elif env == 'production':
            return {
                'uri': self.get_config_value('DATABASE_URL', required=True),
                'track_modifications': False
            }
        else:  # development
            return {
                'uri': self.get_config_value('DEV_DATABASE_URL', 'sqlite:///dev_english_tutoring.db'),
                'track_modifications': False
            }
    
    def get_jwt_config(self) -> Dict[str, Any]:
        """获取JWT配置
        
        Returns:
            Dict[str, Any]: JWT配置字典
        """
        from datetime import timedelta
        
        return {
            'secret_key': self.get_config_value('JWT_SECRET_KEY', required=True),
            'access_token_expires': timedelta(
                hours=int(self.get_config_value('JWT_ACCESS_TOKEN_HOURS', 1))
            ),
            'refresh_token_expires': timedelta(
                days=int(self.get_config_value('JWT_REFRESH_TOKEN_DAYS', 30))
            ),
            'algorithm': 'HS256'
        }
    
    def get_cors_config(self) -> Dict[str, Any]:
        """获取CORS配置
        
        Returns:
            Dict[str, Any]: CORS配置字典
        """
        origins_str = self.get_config_value('CORS_ORIGINS', 'http://localhost:3000,http://localhost:5173')
        origins = [origin.strip() for origin in origins_str.split(',') if origin.strip()]
        
        return {
            'origins': origins,
            'methods': ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
            'allow_headers': ['Content-Type', 'Authorization']
        }
    
    def get_logging_config(self) -> Dict[str, Any]:
        """获取日志配置
        
        Returns:
            Dict[str, Any]: 日志配置字典
        """
        return {
            'level': self.get_config_value('LOG_LEVEL', 'INFO'),
            'file': self.get_config_value('LOG_FILE', 'logs/english_tutoring.log'),
            'max_bytes': int(self.get_config_value('LOG_MAX_BYTES', 10240000)),
            'backup_count': int(self.get_config_value('LOG_BACKUP_COUNT', 10))
        }
    
    def create_directories(self) -> None:
        """创建必需的目录"""
        directories = [
            'logs',
            'uploads',
            'instance'
        ]
        
        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory)
                logging.info(f"创建目录: {directory}")
    
    def print_config_summary(self) -> None:
        """打印配置摘要"""
        env = self.get_config_value('FLASK_ENV', 'development')
        debug = self.get_config_value('FLASK_DEBUG', '0') == '1'
        
        print("\n=== 配置摘要 ===")
        print(f"环境: {env}")
        print(f"调试模式: {debug}")
        print(f"数据库: {self.get_database_config()['uri']}")
        print(f"日志级别: {self.get_logging_config()['level']}")
        print(f"CORS来源: {', '.join(self.get_cors_config()['origins'])}")
        print("================\n")


# 全局配置管理器实例
config_manager = ConfigManager()