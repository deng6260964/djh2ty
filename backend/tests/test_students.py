"""
学生管理模块测试
覆盖用户故事 US-101 ~ US-105
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.student import Student
from app.models.user import User


class TestCreateStudent:
    """US-101 添加学生"""

    async def test_create_student_success(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """TC-STU-001: 正常创建学生 → 201，返回学生信息（US-101 AC2）"""
        payload = {
            "name": "王小华",
            "grade": "初三",
            "subjects": ["数学", "物理"],
            "parent_name": "王爸爸",
            "parent_phone": "13700137000",
            "school": "育才中学",
            "notes": "需要加强函数部分",
        }
        resp = await async_client.post("/api/students", json=payload, headers=auth_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "王小华"
        assert data["grade"] == "初三"
        assert "数学" in data["subjects"]
        assert data["parent_phone"] == "13700137000"
        assert data["is_active"] is True
        assert "id" in data

    async def test_create_student_missing_name(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """TC-STU-002: 缺少必填字段 name → 422（US-101 AC1）"""
        payload = {
            "grade": "初三",
            "subjects": ["数学"],
            "parent_phone": "13700137000",
        }
        resp = await async_client.post("/api/students", json=payload, headers=auth_headers)
        assert resp.status_code == 422

    async def test_create_student_missing_grade(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """TC-STU-003: 缺少必填字段 grade → 422（US-101 AC1）"""
        payload = {
            "name": "测试学生",
            "subjects": ["数学"],
            "parent_phone": "13700137000",
        }
        resp = await async_client.post("/api/students", json=payload, headers=auth_headers)
        assert resp.status_code == 422

    async def test_create_student_missing_subjects(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """TC-STU-004: 缺少必填字段 subjects → 422（US-101 AC1）"""
        payload = {
            "name": "测试学生",
            "grade": "初三",
            "parent_phone": "13700137000",
        }
        resp = await async_client.post("/api/students", json=payload, headers=auth_headers)
        assert resp.status_code == 422

    async def test_create_student_without_auth(self, async_client: AsyncClient):
        """TC-STU-005: 未认证创建学生 → 401"""
        resp = await async_client.post(
            "/api/students",
            json={"name": "未授权", "grade": "初一", "subjects": ["数学"]},
        )
        assert resp.status_code == 401

    async def test_create_student_appears_in_list(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """TC-STU-006: 新建学生立即出现在列表中（US-101 AC2）"""
        unique_name = "独特学生ZZZ"
        await async_client.post(
            "/api/students",
            json={
                "name": unique_name,
                "grade": "高二",
                "subjects": ["化学"],
                "parent_phone": "18888888888",
            },
            headers=auth_headers,
        )
        resp = await async_client.get(
            f"/api/students?search={unique_name}", headers=auth_headers
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert any(s["name"] == unique_name for s in items)


class TestListStudents:
    """US-104 搜索和筛选学生"""

    async def test_list_students_pagination(
        self, async_client: AsyncClient, auth_headers: dict, test_student: Student
    ):
        """TC-STU-007: 获取学生列表（分页）"""
        resp = await async_client.get(
            "/api/students?page=1&page_size=10", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "pages" in data
        assert data["page"] == 1
        assert data["page_size"] == 10

    async def test_search_student_by_name(
        self, async_client: AsyncClient, auth_headers: dict, test_student: Student
    ):
        """TC-STU-008: 按姓名搜索学生（US-104 AC1）"""
        resp = await async_client.get(
            "/api/students?search=张小明", headers=auth_headers
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) >= 1
        assert any(s["name"] == "张小明" for s in items)

    async def test_search_student_partial_name(
        self, async_client: AsyncClient, auth_headers: dict, test_student: Student
    ):
        """TC-STU-009: 模糊搜索（输入部分姓名）"""
        resp = await async_client.get(
            "/api/students?search=张", headers=auth_headers
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) >= 1

    async def test_search_no_results(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """TC-STU-010: 搜索无结果时返回空列表而不是 404（US-104 AC3）"""
        resp = await async_client.get(
            "/api/students?search=根本不存在的名字XYZ123", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total"] == 0

    async def test_filter_active_students(
        self, async_client: AsyncClient, auth_headers: dict, test_student: Student
    ):
        """TC-STU-011: 按 is_active 筛选"""
        resp = await async_client.get(
            "/api/students?is_active=true", headers=auth_headers
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        for s in items:
            assert s["is_active"] is True


class TestGetStudent:
    """US-105 查看学生详情"""

    async def test_get_student_detail(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_student: Student,
    ):
        """TC-STU-012: 获取学生详情（US-105 AC1）"""
        resp = await async_client.get(
            f"/api/students/{test_student.id}", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == test_student.id
        assert data["name"] == "张小明"
        assert "stats" in data
        stats = data["stats"]
        assert "total_courses" in stats
        assert "completed_courses" in stats
        assert "pending_assignments" in stats
        assert "total_paid" in stats
        assert "outstanding" in stats

    async def test_get_nonexistent_student(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """TC-STU-013: 获取不存在的学生 → 404"""
        resp = await async_client.get("/api/students/99999", headers=auth_headers)
        assert resp.status_code == 404
        assert resp.json()["detail"]["code"] == "STUDENT_NOT_FOUND"


class TestUpdateStudent:
    """US-102 编辑学生信息"""

    async def test_update_student_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_student: Student,
    ):
        """TC-STU-014: 更新学生信息成功（US-102 AC2）"""
        new_phone = "18600000001"
        resp = await async_client.put(
            f"/api/students/{test_student.id}",
            json={
                "name": "张小明",
                "grade": "初三",  # 年级升级
                "subjects": ["数学", "英语"],
                "parent_name": "张爸爸",
                "parent_phone": new_phone,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["grade"] == "初三"
        assert data["parent_phone"] == new_phone

    async def test_update_nonexistent_student(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """TC-STU-015: 更新不存在的学生 → 404"""
        resp = await async_client.put(
            "/api/students/99999",
            json={
                "name": "不存在",
                "grade": "初一",
                "subjects": ["数学"],
                "parent_phone": "13000000000",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 404


class TestDeleteStudent:
    """US-103 删除学生（软删除）"""

    async def test_delete_student_soft_delete(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        db: AsyncSession,
    ):
        """TC-STU-016: 软删除学生，is_active 变为 False（US-103 AC2）"""
        # 先创建一个专供删除测试的学生
        from app.models.student import Student

        student = Student(
            name="待删除学生",
            grade="高三",
            subjects=["语文"],
            parent_phone="13100000001",
            is_active=True,
        )
        db.add(student)
        await db.flush()
        student_id = student.id

        resp = await async_client.delete(
            f"/api/students/{student_id}", headers=auth_headers
        )
        assert resp.status_code == 204

        # 验证软删除：is_active = False
        from sqlalchemy import select

        result = await db.execute(
            select(Student).where(Student.id == student_id)
        )
        deleted_student = result.scalar_one_or_none()
        assert deleted_student is not None
        assert deleted_student.is_active is False

    async def test_deleted_student_not_in_active_list(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        db: AsyncSession,
    ):
        """TC-STU-017: 删除后学生从活跃列表消失（US-103 AC3）"""
        from app.models.student import Student

        student = Student(
            name="即将消失的学生",
            grade="高一",
            subjects=["英语"],
            parent_phone="13100000002",
            is_active=True,
        )
        db.add(student)
        await db.flush()
        student_id = student.id

        # 删除
        await async_client.delete(
            f"/api/students/{student_id}", headers=auth_headers
        )

        # 查询时带 is_active=true 过滤
        resp = await async_client.get(
            "/api/students?is_active=true", headers=auth_headers
        )
        items = resp.json()["items"]
        ids_in_list = [s["id"] for s in items]
        assert student_id not in ids_in_list

    async def test_delete_nonexistent_student(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """TC-STU-018: 删除不存在的学生 → 404"""
        resp = await async_client.delete("/api/students/99999", headers=auth_headers)
        assert resp.status_code == 404
