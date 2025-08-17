from datetime import datetime, timedelta
from flask import request, current_app
from flask_jwt_extended import get_jwt, get_jwt_identity
from app.models.user import User
from app.database import db
import logging
import json
from typing import Dict, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class SessionStatus(Enum):
    """会话状态枚举"""

    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    INVALID = "invalid"


@dataclass
class SessionInfo:
    """会话信息数据类"""

    user_id: int
    session_id: str
    ip_address: str
    user_agent: str
    login_time: datetime
    last_activity: datetime
    expires_at: datetime
    status: SessionStatus
    device_info: Optional[Dict] = None
    location_info: Optional[Dict] = None


class SessionManager:
    """用户会话管理器"""

    def __init__(self, app=None):
        self.app = app
        self.active_sessions = {}  # 简单的内存存储，生产环境建议使用Redis
        self.session_timeout = timedelta(hours=24)  # 默认会话超时时间
        self.max_sessions_per_user = 5  # 每个用户最大会话数

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """初始化会话管理器"""
        self.app = app

        # 从配置中获取会话设置
        self.session_timeout = timedelta(
            seconds=app.config.get("SESSION_TIMEOUT_SECONDS", 86400)  # 默认24小时
        )
        self.max_sessions_per_user = app.config.get("MAX_SESSIONS_PER_USER", 5)

    def create_session(self, user: User, jti: str) -> SessionInfo:
        """创建新会话"""
        try:
            # 获取请求信息
            ip_address = self._get_client_ip()
            user_agent = request.headers.get("User-Agent", "Unknown")

            # 创建会话信息
            now = datetime.utcnow()
            session_info = SessionInfo(
                user_id=user.id,
                session_id=jti,
                ip_address=ip_address,
                user_agent=user_agent,
                login_time=now,
                last_activity=now,
                expires_at=now + self.session_timeout,
                status=SessionStatus.ACTIVE,
                device_info=self._parse_device_info(user_agent),
                location_info=self._get_location_info(ip_address),
            )

            # 清理用户的过期会话
            self._cleanup_user_sessions(user.id)

            # 检查用户会话数量限制
            self._enforce_session_limit(user.id)

            # 存储会话
            self.active_sessions[jti] = session_info

            logger.info(
                f"Session created for user {user.email} (ID: {user.id}) from {ip_address}"
            )

            return session_info

        except Exception as e:
            logger.error(f"Error creating session for user {user.id}: {str(e)}")
            raise

    def get_session(self, session_id: str) -> Optional[SessionInfo]:
        """获取会话信息"""
        try:
            session_info = self.active_sessions.get(session_id)

            if not session_info:
                return None

            # 检查会话是否过期
            if self._is_session_expired(session_info):
                self._expire_session(session_id)
                return None

            return session_info

        except Exception as e:
            logger.error(f"Error getting session {session_id}: {str(e)}")
            return None

    def update_session_activity(self, session_id: str) -> bool:
        """更新会话活动时间"""
        try:
            session_info = self.active_sessions.get(session_id)

            if not session_info:
                return False

            # 检查会话是否过期
            if self._is_session_expired(session_info):
                self._expire_session(session_id)
                return False

            # 更新最后活动时间
            session_info.last_activity = datetime.utcnow()

            logger.debug(f"Session activity updated for session {session_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating session activity {session_id}: {str(e)}")
            return False

    def revoke_session(self, session_id: str) -> bool:
        """撤销会话"""
        try:
            session_info = self.active_sessions.get(session_id)

            if not session_info:
                return False

            session_info.status = SessionStatus.REVOKED

            # 从活跃会话中移除
            del self.active_sessions[session_id]

            logger.info(f"Session revoked: {session_id}")
            return True

        except Exception as e:
            logger.error(f"Error revoking session {session_id}: {str(e)}")
            return False

    def revoke_user_sessions(
        self, user_id: int, exclude_session: Optional[str] = None
    ) -> int:
        """撤销用户的所有会话（可排除指定会话）"""
        try:
            revoked_count = 0
            sessions_to_remove = []

            for session_id, session_info in self.active_sessions.items():
                if session_info.user_id == user_id and session_id != exclude_session:
                    session_info.status = SessionStatus.REVOKED
                    sessions_to_remove.append(session_id)
                    revoked_count += 1

            # 移除撤销的会话
            for session_id in sessions_to_remove:
                del self.active_sessions[session_id]

            logger.info(f"Revoked {revoked_count} sessions for user {user_id}")
            return revoked_count

        except Exception as e:
            logger.error(f"Error revoking user sessions for user {user_id}: {str(e)}")
            return 0

    def get_user_sessions(self, user_id: int) -> List[SessionInfo]:
        """获取用户的所有活跃会话"""
        try:
            user_sessions = []

            for session_info in self.active_sessions.values():
                if session_info.user_id == user_id:
                    # 检查会话是否过期
                    if self._is_session_expired(session_info):
                        self._expire_session(session_info.session_id)
                    else:
                        user_sessions.append(session_info)

            return user_sessions

        except Exception as e:
            logger.error(f"Error getting user sessions for user {user_id}: {str(e)}")
            return []

    def validate_session(self, session_id: str) -> bool:
        """验证会话是否有效"""
        try:
            session_info = self.get_session(session_id)

            if not session_info:
                return False

            # 检查会话状态
            if session_info.status != SessionStatus.ACTIVE:
                return False

            # 检查用户是否仍然激活
            user = User.query.get(session_info.user_id)
            if not user or not user.is_active:
                self._expire_session(session_id)
                return False

            # 更新会话活动时间
            self.update_session_activity(session_id)

            return True

        except Exception as e:
            logger.error(f"Error validating session {session_id}: {str(e)}")
            return False

    def cleanup_expired_sessions(self) -> int:
        """清理所有过期会话"""
        try:
            expired_sessions = []

            for session_id, session_info in self.active_sessions.items():
                if self._is_session_expired(session_info):
                    expired_sessions.append(session_id)

            # 移除过期会话
            for session_id in expired_sessions:
                self._expire_session(session_id)

            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
            return len(expired_sessions)

        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {str(e)}")
            return 0

    def get_session_statistics(self) -> Dict:
        """获取会话统计信息"""
        try:
            total_sessions = len(self.active_sessions)
            user_session_counts = {}

            for session_info in self.active_sessions.values():
                user_id = session_info.user_id
                user_session_counts[user_id] = user_session_counts.get(user_id, 0) + 1

            return {
                "total_active_sessions": total_sessions,
                "unique_users": len(user_session_counts),
                "average_sessions_per_user": total_sessions / len(user_session_counts)
                if user_session_counts
                else 0,
                "max_sessions_per_user": max(user_session_counts.values())
                if user_session_counts
                else 0,
            }

        except Exception as e:
            logger.error(f"Error getting session statistics: {str(e)}")
            return {}

    def _get_client_ip(self) -> str:
        """获取客户端IP地址"""
        # 检查代理头
        if request.headers.get("X-Forwarded-For"):
            return request.headers.get("X-Forwarded-For").split(",")[0].strip()
        elif request.headers.get("X-Real-IP"):
            return request.headers.get("X-Real-IP")
        else:
            return request.remote_addr or "Unknown"

    def _parse_device_info(self, user_agent: str) -> Dict:
        """解析设备信息"""
        # 简单的用户代理解析，生产环境可以使用更专业的库
        device_info = {
            "user_agent": user_agent,
            "is_mobile": any(
                mobile in user_agent.lower()
                for mobile in ["mobile", "android", "iphone"]
            ),
            "browser": "Unknown",
            "os": "Unknown",
        }

        # 简单的浏览器检测
        if "chrome" in user_agent.lower():
            device_info["browser"] = "Chrome"
        elif "firefox" in user_agent.lower():
            device_info["browser"] = "Firefox"
        elif "safari" in user_agent.lower():
            device_info["browser"] = "Safari"
        elif "edge" in user_agent.lower():
            device_info["browser"] = "Edge"

        # 简单的操作系统检测
        if "windows" in user_agent.lower():
            device_info["os"] = "Windows"
        elif "mac" in user_agent.lower():
            device_info["os"] = "macOS"
        elif "linux" in user_agent.lower():
            device_info["os"] = "Linux"
        elif "android" in user_agent.lower():
            device_info["os"] = "Android"
        elif "ios" in user_agent.lower():
            device_info["os"] = "iOS"

        return device_info

    def _get_location_info(self, ip_address: str) -> Dict:
        """获取位置信息（简化版）"""
        # 生产环境可以集成IP地理位置服务
        return {"ip_address": ip_address, "country": "Unknown", "city": "Unknown"}

    def _is_session_expired(self, session_info: SessionInfo) -> bool:
        """检查会话是否过期"""
        return datetime.utcnow() > session_info.expires_at

    def _expire_session(self, session_id: str) -> None:
        """使会话过期"""
        session_info = self.active_sessions.get(session_id)
        if session_info:
            session_info.status = SessionStatus.EXPIRED
            del self.active_sessions[session_id]
            logger.info(f"Session expired: {session_id}")

    def _cleanup_user_sessions(self, user_id: int) -> None:
        """清理用户的过期会话"""
        sessions_to_remove = []

        for session_id, session_info in self.active_sessions.items():
            if session_info.user_id == user_id and self._is_session_expired(
                session_info
            ):
                sessions_to_remove.append(session_id)

        for session_id in sessions_to_remove:
            self._expire_session(session_id)

    def _enforce_session_limit(self, user_id: int) -> None:
        """强制执行用户会话数量限制"""
        user_sessions = [
            (sid, sinfo)
            for sid, sinfo in self.active_sessions.items()
            if sinfo.user_id == user_id
        ]

        if len(user_sessions) >= self.max_sessions_per_user:
            # 按登录时间排序，移除最旧的会话
            user_sessions.sort(key=lambda x: x[1].login_time)
            sessions_to_remove = user_sessions[
                : len(user_sessions) - self.max_sessions_per_user + 1
            ]

            for session_id, _ in sessions_to_remove:
                self.revoke_session(session_id)
                logger.info(f"Removed old session {session_id} due to session limit")


# 创建全局会话管理器实例
session_manager = SessionManager()
