# -*- coding: utf-8 -*-
"""
日志管理模块
提供统一的日志配置和管理功能
"""

import os
import logging
import logging.handlers
from datetime import datetime
from typing import Optional
from flask import Flask, request, g


class LoggerManager:
    """日志管理器"""

    def __init__(self):
        self.loggers = {}
        self.log_format = (
            "%(asctime)s - %(name)s - %(levelname)s - "
            "[%(filename)s:%(lineno)d] - %(message)s"
        )
        self.date_format = "%Y-%m-%d %H:%M:%S"

    def setup_app_logger(self, app: Flask) -> None:
        """为Flask应用设置日志

        Args:
            app: Flask应用实例
        """
        # 获取日志配置
        log_level = app.config.get("LOG_LEVEL", "INFO")
        log_file = app.config.get("LOG_FILE", "logs/english_tutoring.log")
        max_bytes = app.config.get("LOG_MAX_BYTES", 10 * 1024 * 1024)  # 10MB
        backup_count = app.config.get("LOG_BACKUP_COUNT", 10)

        # 确保日志目录存在
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # 设置日志级别
        numeric_level = getattr(logging, log_level.upper(), logging.INFO)
        app.logger.setLevel(numeric_level)

        # 清除默认处理器
        app.logger.handlers.clear()

        # 创建格式化器
        formatter = logging.Formatter(self.log_format, self.date_format)

        # 控制台处理器
        if app.config.get("DEBUG", False):
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)
            console_handler.setFormatter(formatter)
            app.logger.addHandler(console_handler)

        # 文件处理器（轮转）
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        app.logger.addHandler(file_handler)

        # 错误日志处理器
        error_log_file = log_file.replace(".log", "_error.log")
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        app.logger.addHandler(error_handler)

        app.logger.info(f"日志系统初始化完成 - 级别: {log_level}")

    def get_logger(self, name: str, level: str = "INFO") -> logging.Logger:
        """获取指定名称的日志器

        Args:
            name: 日志器名称
            level: 日志级别

        Returns:
            logging.Logger: 日志器实例
        """
        if name not in self.loggers:
            logger = logging.getLogger(name)
            logger.setLevel(getattr(logging, level.upper(), logging.INFO))

            # 创建处理器
            handler = logging.StreamHandler()
            formatter = logging.Formatter(self.log_format, self.date_format)
            handler.setFormatter(formatter)
            logger.addHandler(handler)

            self.loggers[name] = logger

        return self.loggers[name]

    def log_request(self, app: Flask) -> None:
        """记录请求日志

        Args:
            app: Flask应用实例
        """

        @app.before_request
        def before_request():
            g.start_time = datetime.now()

            # 记录请求信息
            app.logger.info(
                f"请求开始 - {request.method} {request.url} - "
                f"IP: {request.remote_addr} - "
                f"User-Agent: {request.headers.get('User-Agent', 'Unknown')}"
            )

            # 记录请求体（仅POST/PUT/PATCH）
            if request.method in ["POST", "PUT", "PATCH"] and request.is_json:
                try:
                    # 不记录敏感信息
                    data = request.get_json()
                    if data and isinstance(data, dict):
                        # 过滤敏感字段
                        filtered_data = self._filter_sensitive_data(data)
                        app.logger.debug(f"请求数据: {filtered_data}")
                except Exception as e:
                    app.logger.warning(f"无法解析请求数据: {e}")

        @app.after_request
        def after_request(response):
            # 计算请求处理时间
            if hasattr(g, "start_time"):
                duration = (datetime.now() - g.start_time).total_seconds() * 1000

                app.logger.info(
                    f"请求完成 - {request.method} {request.url} - "
                    f"状态码: {response.status_code} - "
                    f"耗时: {duration:.2f}ms"
                )

                # 记录慢请求
                if duration > 1000:  # 超过1秒
                    app.logger.warning(
                        f"慢请求警告 - {request.method} {request.url} - "
                        f"耗时: {duration:.2f}ms"
                    )

            return response

    def log_error(self, app: Flask) -> None:
        """记录错误日志

        Args:
            app: Flask应用实例
        """

        @app.errorhandler(Exception)
        def handle_exception(e):
            # 记录异常详情
            app.logger.error(
                f"未处理异常 - {request.method} {request.url} - " f"错误: {str(e)}",
                exc_info=True,
            )

            # 返回通用错误响应
            from flask import jsonify

            return (
                jsonify({"error": "Internal Server Error", "message": "服务器内部错误，请稍后重试"}),
                500,
            )

    def _filter_sensitive_data(self, data: dict) -> dict:
        """过滤敏感数据

        Args:
            data: 原始数据字典

        Returns:
            dict: 过滤后的数据字典
        """
        sensitive_fields = {
            "password",
            "passwd",
            "pwd",
            "secret",
            "token",
            "key",
            "api_key",
            "access_token",
            "refresh_token",
            "authorization",
            "auth",
            "credential",
            "credentials",
        }

        filtered = {}
        for key, value in data.items():
            if key.lower() in sensitive_fields:
                filtered[key] = "***"
            elif isinstance(value, dict):
                filtered[key] = self._filter_sensitive_data(value)
            else:
                filtered[key] = value

        return filtered

    def setup_security_logger(self, app: Flask) -> None:
        """设置安全日志

        Args:
            app: Flask应用实例
        """
        security_logger = self.get_logger("security", "WARNING")

        @app.before_request
        def security_check():
            # 检查可疑请求
            user_agent = request.headers.get("User-Agent", "")

            # 检查恶意User-Agent
            suspicious_agents = ["sqlmap", "nmap", "nikto", "dirb", "gobuster"]
            if any(agent in user_agent.lower() for agent in suspicious_agents):
                security_logger.warning(
                    f"可疑User-Agent - IP: {request.remote_addr} - "
                    f"User-Agent: {user_agent} - URL: {request.url}"
                )

            # 检查SQL注入尝试
            query_string = request.query_string.decode("utf-8", errors="ignore")
            sql_patterns = ["union", "select", "insert", "delete", "drop", "exec"]
            if any(pattern in query_string.lower() for pattern in sql_patterns):
                security_logger.warning(
                    f"可疑SQL查询 - IP: {request.remote_addr} - "
                    f"查询: {query_string} - URL: {request.url}"
                )


# 全局日志管理器实例
logger_manager = LoggerManager()
