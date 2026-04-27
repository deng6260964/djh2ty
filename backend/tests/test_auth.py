"""
认证模块测试
覆盖用户故事 US-001（老师账号登录）
"""
import pytest
from httpx import AsyncClient

from app.models.user import User
from app.utils.auth import create_access_token, get_password_hash
from datetime import timedelta


class TestLogin:
    """登录相关测试"""

    async def test_login_success(self, async_client: AsyncClient, admin_user: User):
        """TC-AUTH-001: 正常登录，返回 access_token（US-001 AC1）"""
        resp = await async_client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0
        assert data["user"]["username"] == "admin"
        assert data["user"]["role"] == "admin"

    async def test_login_wrong_password(self, async_client: AsyncClient, admin_user: User):
        """TC-AUTH-002: 错误密码登录 → 401（US-001 AC2）"""
        resp = await async_client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "wrong_password"},
        )
        assert resp.status_code == 401
        data = resp.json()
        assert data["detail"]["code"] == "INVALID_CREDENTIALS"
        # 不泄露具体是密码还是用户名错误
        assert "用户名或密码错误" in data["detail"]["message"]

    async def test_login_nonexistent_user(self, async_client: AsyncClient):
        """TC-AUTH-003: 不存在的用户 → 401（US-001 AC2）"""
        resp = await async_client.post(
            "/api/auth/login",
            json={"username": "nonexistent_user_xyz", "password": "password123"},
        )
        assert resp.status_code == 401
        data = resp.json()
        assert data["detail"]["code"] == "INVALID_CREDENTIALS"

    async def test_login_empty_username(self, async_client: AsyncClient):
        """TC-AUTH-004: 空用户名 → 422 验证错误"""
        resp = await async_client.post(
            "/api/auth/login",
            json={"username": "", "password": "admin123"},
        )
        # FastAPI pydantic 验证空字符串，或后端返回 401
        assert resp.status_code in (401, 422)

    async def test_login_disabled_user(self, async_client: AsyncClient, db):
        """TC-AUTH-005: 被禁用的用户 → 401"""
        from app.models.user import User

        disabled_user = User(
            username="disabled_user",
            hashed_password=get_password_hash("password123"),
            role="admin",
            display_name="被禁用用户",
            is_active=False,
        )
        db.add(disabled_user)
        await db.flush()

        resp = await async_client.post(
            "/api/auth/login",
            json={"username": "disabled_user", "password": "password123"},
        )
        assert resp.status_code == 401


class TestAuthMe:
    """获取当前用户信息相关测试"""

    async def test_get_me_with_valid_token(
        self, async_client: AsyncClient, auth_headers: dict, admin_user: User
    ):
        """TC-AUTH-006: 使用有效 token 访问 /api/auth/me → 返回用户信息"""
        resp = await async_client.get("/api/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "admin"
        assert data["role"] == "admin"
        assert data["is_active"] is True

    async def test_get_me_without_token(self, async_client: AsyncClient):
        """TC-AUTH-007: 无 token 访问受保护接口 → 401（US-001 AC3）"""
        resp = await async_client.get("/api/auth/me")
        assert resp.status_code == 401

    async def test_get_me_with_invalid_token(self, async_client: AsyncClient):
        """TC-AUTH-008: 使用无效 token → 401"""
        headers = {"Authorization": "Bearer invalid.token.here"}
        resp = await async_client.get("/api/auth/me", headers=headers)
        assert resp.status_code == 401

    async def test_get_me_with_malformed_bearer(self, async_client: AsyncClient):
        """TC-AUTH-009: Authorization 头格式错误 → 401"""
        headers = {"Authorization": "NotBearer sometoken"}
        resp = await async_client.get("/api/auth/me", headers=headers)
        assert resp.status_code == 401


class TestTokenRefresh:
    """Token 刷新相关测试"""

    async def test_refresh_token_success(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """TC-AUTH-010: 使用有效 token 刷新，返回新 token（US-001 AC1）"""
        resp = await async_client.post("/api/auth/refresh", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["expires_in"] > 0

    async def test_refresh_without_token(self, async_client: AsyncClient):
        """TC-AUTH-011: 无 token 刷新 → 401"""
        resp = await async_client.post("/api/auth/refresh")
        assert resp.status_code == 401

    async def test_refresh_with_expired_token(self, async_client: AsyncClient, admin_user: User):
        """TC-AUTH-012: 使用已过期 token 刷新 → 401（US-001 AC3）"""
        # 创建一个已过期的 token（有效期为负数）
        expired_token = create_access_token(
            data={"sub": str(admin_user.id), "role": "admin"},
            expires_delta=timedelta(seconds=-1),
        )
        headers = {"Authorization": f"Bearer {expired_token}"}
        resp = await async_client.post("/api/auth/refresh", headers=headers)
        assert resp.status_code == 401


class TestProtectedRoutes:
    """受保护路由权限测试"""

    async def test_access_students_without_token(self, async_client: AsyncClient):
        """TC-AUTH-013: 无 token 访问学生列表 → 401"""
        resp = await async_client.get("/api/students")
        assert resp.status_code == 401

    async def test_access_courses_without_token(self, async_client: AsyncClient):
        """TC-AUTH-014: 无 token 访问课程列表 → 401"""
        resp = await async_client.get("/api/courses")
        assert resp.status_code == 401

    async def test_access_billing_without_token(self, async_client: AsyncClient):
        """TC-AUTH-015: 无 token 访问收费管理 → 401"""
        resp = await async_client.get("/api/billing/records")
        assert resp.status_code == 401
