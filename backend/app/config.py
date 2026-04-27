from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional
import os


class Settings(BaseSettings):
    # 数据库
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/tutoring_assistant"

    # JWT
    SECRET_KEY: str = "dev-secret-key-please-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # 微信小程序
    WECHAT_APP_ID: str = ""
    WECHAT_APP_SECRET: str = ""

    # 文件上传
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 52428800  # 50MB

    # 应用
    APP_NAME: str = "家教辅助系统"
    DEBUG: bool = True
    API_PREFIX: str = "/api"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    @property
    def upload_dir_abs(self) -> str:
        """返回上传目录的绝对路径"""
        if os.path.isabs(self.UPLOAD_DIR):
            return self.UPLOAD_DIR
        # 相对于 backend 目录
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_dir, self.UPLOAD_DIR.lstrip("./"))


settings = Settings()
