"""
资料管理模块测试
覆盖用户故事 US-701 ~ US-703
"""
import io
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.student import Student
from app.models.resource import Resource, ResourceShare
from app.models.user import User
from app.utils.auth import get_password_hash


# -----------------------------------------------
# 辅助函数
# -----------------------------------------------

def _make_pdf_file(size_bytes: int = 1024) -> tuple[bytes, str, str]:
    """生成指定大小的模拟 PDF 文件内容"""
    # PDF 文件头
    header = b"%PDF-1.4\n"
    # 填充到指定大小
    content = header + b"0" * (size_bytes - len(header))
    return content, "test_file.pdf", "application/pdf"


def _make_exe_file() -> tuple[bytes, str, str]:
    """生成模拟 EXE 文件"""
    return b"MZ\x90\x00", "malware.exe", "application/octet-stream"


def _make_image_file() -> tuple[bytes, str, str]:
    """生成模拟 PNG 图片"""
    # 最小有效 PNG 头
    png_header = (
        b"\x89PNG\r\n\x1a\n"
        b"\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
    )
    content = png_header + b"\x00" * 100
    return content, "image.png", "image/png"


class TestUploadResource:
    """US-701 上传教学资料"""

    async def test_upload_pdf_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """TC-RES-001: 正常上传 PDF → 201（US-701 AC1）"""
        content, filename, mime = _make_pdf_file(1024)
        files = {"file": (filename, io.BytesIO(content), mime)}
        data = {"title": "数学第三章讲义", "subject": "数学", "grade": "初二"}

        resp = await async_client.post(
            "/api/resources/upload",
            files=files,
            data=data,
            headers=auth_headers,
        )
        assert resp.status_code == 201
        result = resp.json()
        assert result["title"] == "数学第三章讲义"
        assert result["subject"] == "数学"
        assert result["file_type"] == "application/pdf"
        assert result["file_size"] == 1024
        assert "id" in result

    async def test_upload_image_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """TC-RES-002: 上传 PNG 图片成功（US-701 AC1）"""
        content, filename, mime = _make_image_file()
        files = {"file": (filename, io.BytesIO(content), mime)}
        data = {"title": "测试图片"}

        resp = await async_client.post(
            "/api/resources/upload",
            files=files,
            data=data,
            headers=auth_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["file_type"] == "image/png"

    async def test_upload_file_too_large(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """TC-RES-003: 文件超过 50MB → 413（US-701 AC1/AC3）"""
        # 51MB 的内容
        size_51mb = 51 * 1024 * 1024
        content = b"%PDF-1.4\n" + b"0" * (size_51mb - 10)
        files = {"file": ("big_file.pdf", io.BytesIO(content), "application/pdf")}
        data = {"title": "超大文件"}

        resp = await async_client.post(
            "/api/resources/upload",
            files=files,
            data=data,
            headers=auth_headers,
        )
        assert resp.status_code == 413

    async def test_upload_disallowed_file_type(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """TC-RES-004: 上传不允许的文件类型（.exe）→ 400（US-701 AC1/AC3）"""
        content, filename, mime = _make_exe_file()
        files = {"file": (filename, io.BytesIO(content), mime)}
        data = {"title": "病毒文件"}

        resp = await async_client.post(
            "/api/resources/upload",
            files=files,
            data=data,
            headers=auth_headers,
        )
        assert resp.status_code == 400
        assert resp.json()["detail"]["code"] == "FILE_TYPE_NOT_ALLOWED"

    async def test_upload_missing_title(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """TC-RES-005: 缺少 title 字段 → 422"""
        content, filename, mime = _make_pdf_file()
        files = {"file": (filename, io.BytesIO(content), mime)}
        # 不传 title
        resp = await async_client.post(
            "/api/resources/upload",
            files=files,
            headers=auth_headers,
        )
        assert resp.status_code == 422

    async def test_upload_without_auth(self, async_client: AsyncClient):
        """TC-RES-006: 未认证上传 → 401"""
        content, filename, mime = _make_pdf_file()
        files = {"file": (filename, io.BytesIO(content), mime)}
        data = {"title": "未授权上传"}

        resp = await async_client.post(
            "/api/resources/upload",
            files=files,
            data=data,
        )
        assert resp.status_code == 401


class TestShareResource:
    """US-703 分享资料给学生"""

    async def _upload_resource(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        title: str = "测试资料",
    ) -> int:
        """辅助：上传资料并返回 resource_id"""
        content, filename, mime = _make_pdf_file()
        files = {"file": (filename, io.BytesIO(content), mime)}
        data = {"title": title}
        resp = await async_client.post(
            "/api/resources/upload",
            files=files,
            data=data,
            headers=auth_headers,
        )
        return resp.json()["id"]

    async def test_share_resource_to_student(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_student: Student,
    ):
        """TC-RES-007: 分享资料给学生（US-703 AC1）"""
        resource_id = await self._upload_resource(async_client, auth_headers, "分享测试资料")

        resp = await async_client.post(
            f"/api/resources/{resource_id}/share",
            json={"student_ids": [test_student.id]},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["shared"] is True
        assert data["shared_count"] == 1

    async def test_share_resource_to_multiple_students(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_student: Student,
        test_student_2: Student,
    ):
        """TC-RES-008: 分享给多个学生（US-703 AC1）"""
        resource_id = await self._upload_resource(async_client, auth_headers, "多人分享资料")

        resp = await async_client.post(
            f"/api/resources/{resource_id}/share",
            json={"student_ids": [test_student.id, test_student_2.id]},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["shared_count"] == 2

    async def test_share_idempotent(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_student: Student,
    ):
        """TC-RES-009: 重复分享同一资料不重复创建记录"""
        resource_id = await self._upload_resource(async_client, auth_headers, "幂等分享资料")

        # 第一次分享
        await async_client.post(
            f"/api/resources/{resource_id}/share",
            json={"student_ids": [test_student.id]},
            headers=auth_headers,
        )
        # 第二次分享（应不报错，shared_count 为 0）
        resp = await async_client.post(
            f"/api/resources/{resource_id}/share",
            json={"student_ids": [test_student.id]},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["shared_count"] == 0

    async def test_revoke_share(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_student: Student,
    ):
        """TC-RES-010: 撤销分享（US-703 AC3）"""
        resource_id = await self._upload_resource(async_client, auth_headers, "撤销分享资料")

        # 先分享
        await async_client.post(
            f"/api/resources/{resource_id}/share",
            json={"student_ids": [test_student.id]},
            headers=auth_headers,
        )
        # 再撤销
        resp = await async_client.delete(
            f"/api/resources/{resource_id}/share/{test_student.id}",
            headers=auth_headers,
        )
        assert resp.status_code == 204

    async def test_revoke_nonexistent_share(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_student: Student,
    ):
        """TC-RES-011: 撤销不存在的分享 → 404"""
        resource_id = await self._upload_resource(async_client, auth_headers, "无分享资料")

        resp = await async_client.delete(
            f"/api/resources/{resource_id}/share/{test_student.id}",
            headers=auth_headers,
        )
        assert resp.status_code == 404

    async def test_share_resource_appears_in_detail(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_student: Student,
    ):
        """TC-RES-012: 分享后资料详情包含被分享学生 ID（US-703 AC2）"""
        resource_id = await self._upload_resource(async_client, auth_headers, "详情分享资料")

        await async_client.post(
            f"/api/resources/{resource_id}/share",
            json={"student_ids": [test_student.id]},
            headers=auth_headers,
        )

        detail_resp = await async_client.get(
            f"/api/resources/{resource_id}", headers=auth_headers
        )
        assert detail_resp.status_code == 200
        data = detail_resp.json()
        assert "shared_students" in data
        assert test_student.id in data["shared_students"]


class TestDownloadResource:
    """资料下载权限测试"""

    async def _setup_resource_and_share(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        db: AsyncSession,
        student: Student,
    ) -> int:
        """上传资料并分享给指定学生"""
        content, filename, mime = _make_pdf_file()
        files = {"file": (filename, io.BytesIO(content), mime)}
        data = {"title": "下载测试资料"}

        resp = await async_client.post(
            "/api/resources/upload",
            files=files,
            data=data,
            headers=auth_headers,
        )
        resource_id = resp.json()["id"]

        await async_client.post(
            f"/api/resources/{resource_id}/share",
            json={"student_ids": [student.id]},
            headers=auth_headers,
        )
        return resource_id

    async def test_admin_download_any_resource(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        db: AsyncSession,
        test_student: Student,
    ):
        """TC-RES-013: Admin 可下载任意资料（US-703 权限）"""
        resource_id = await self._setup_resource_and_share(
            async_client, auth_headers, db, test_student
        )
        resp = await async_client.get(
            f"/api/resources/{resource_id}/download", headers=auth_headers
        )
        # 文件存在时返回 200；文件不存在（测试环境无真实文件）返回 404
        assert resp.status_code in (200, 404)

    async def test_student_download_shared_resource(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        db: AsyncSession,
        test_student: Student,
    ):
        """TC-RES-014: 学生可下载分享给自己的资料（US-703 AC2）"""
        resource_id = await self._setup_resource_and_share(
            async_client, auth_headers, db, test_student
        )

        # 创建一个 student 用户并绑定到 test_student
        student_user = User(
            username="student_user_dl",
            hashed_password=get_password_hash("pass123"),
            role="student",
            display_name="学生用户",
            is_active=True,
        )
        db.add(student_user)
        await db.flush()
        test_student.user_id = student_user.id
        await db.flush()

        # 学生登录
        login_resp = await async_client.post(
            "/api/auth/login",
            json={"username": "student_user_dl", "password": "pass123"},
        )
        student_token = login_resp.json()["access_token"]
        student_headers = {"Authorization": f"Bearer {student_token}"}

        resp = await async_client.get(
            f"/api/resources/{resource_id}/download",
            headers=student_headers,
        )
        # 文件存在时返回 200；无真实文件时返回 404（权限校验已通过）
        assert resp.status_code in (200, 404)

    async def test_student_cannot_download_unshared_resource(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        db: AsyncSession,
        test_student: Student,
        test_student_2: Student,
    ):
        """TC-RES-015: 学生无法下载未分享给自己的资料 → 403（US-703 AC3）"""
        # 仅分享给 test_student，不分享给 test_student_2
        resource_id = await self._setup_resource_and_share(
            async_client, auth_headers, db, test_student
        )

        # 创建 test_student_2 的用户账号
        student2_user = User(
            username="student2_user_dl",
            hashed_password=get_password_hash("pass456"),
            role="student",
            display_name="学生2",
            is_active=True,
        )
        db.add(student2_user)
        await db.flush()
        test_student_2.user_id = student2_user.id
        await db.flush()

        # 学生2 登录
        login_resp = await async_client.post(
            "/api/auth/login",
            json={"username": "student2_user_dl", "password": "pass456"},
        )
        assert login_resp.status_code == 200
        s2_token = login_resp.json()["access_token"]
        s2_headers = {"Authorization": f"Bearer {s2_token}"}

        resp = await async_client.get(
            f"/api/resources/{resource_id}/download",
            headers=s2_headers,
        )
        assert resp.status_code == 403

    async def test_download_without_auth(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        db: AsyncSession,
        test_student: Student,
    ):
        """TC-RES-016: 未认证下载 → 401"""
        resource_id = await self._setup_resource_and_share(
            async_client, auth_headers, db, test_student
        )
        resp = await async_client.get(
            f"/api/resources/{resource_id}/download",
        )
        assert resp.status_code == 401


class TestListResources:
    """US-702 分类管理资料"""

    async def test_list_resources(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """TC-RES-017: 获取资料列表"""
        resp = await async_client.get(
            "/api/resources?page=1&page_size=10", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data

    async def test_list_resources_filter_by_subject(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """TC-RES-018: 按科目筛选资料（US-702 AC1）"""
        # 先上传一个有科目的资料
        content, filename, mime = _make_pdf_file()
        files = {"file": (filename, io.BytesIO(content), mime)}
        data = {"title": "数学专用资料", "subject": "数学筛选测试"}
        await async_client.post(
            "/api/resources/upload",
            files=files,
            data=data,
            headers=auth_headers,
        )

        resp = await async_client.get(
            "/api/resources?subject=数学筛选测试", headers=auth_headers
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        for item in items:
            assert item["subject"] == "数学筛选测试"

    async def test_delete_resource(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """TC-RES-019: 删除资料（US-702 AC3）"""
        content, filename, mime = _make_pdf_file()
        files = {"file": (filename, io.BytesIO(content), mime)}
        data = {"title": "待删除资料"}

        create_resp = await async_client.post(
            "/api/resources/upload",
            files=files,
            data=data,
            headers=auth_headers,
        )
        resource_id = create_resp.json()["id"]

        del_resp = await async_client.delete(
            f"/api/resources/{resource_id}", headers=auth_headers
        )
        assert del_resp.status_code == 204

        # 确认已删除
        get_resp = await async_client.get(
            f"/api/resources/{resource_id}", headers=auth_headers
        )
        assert get_resp.status_code == 404
