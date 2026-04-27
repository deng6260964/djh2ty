"""
作业管理模块测试
覆盖用户故事 US-301 ~ US-304
"""
import pytest
from datetime import date, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.student import Student
from app.models.assignment import Assignment, AssignmentStudent


class TestCreateAssignment:
    """US-301 布置作业"""

    async def test_create_assignment_single_student(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_student: Student,
    ):
        """TC-ASN-001: 布置作业给单个学生 → 201（US-301 AC2）"""
        due = (date.today() + timedelta(days=7)).isoformat()
        payload = {
            "title": "第三章练习题",
            "subject": "数学",
            "content": "<p>完成课本 P52-P55 练习题 1-10</p>",
            "due_date": due,
            "student_ids": [test_student.id],
        }
        resp = await async_client.post("/api/assignments", json=payload, headers=auth_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "第三章练习题"
        assert data["subject"] == "数学"
        assert len(data["students"]) == 1
        assert data["students"][0]["student_id"] == test_student.id
        assert data["students"][0]["status"] == "pending"

    async def test_create_assignment_multiple_students(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_student: Student,
        test_student_2: Student,
    ):
        """TC-ASN-002: 布置作业给多个学生（US-301 AC2）"""
        due = (date.today() + timedelta(days=7)).isoformat()
        payload = {
            "title": "多人作业测试",
            "subject": "数学",
            "content": "<p>数学练习</p>",
            "due_date": due,
            "student_ids": [test_student.id, test_student_2.id],
        }
        resp = await async_client.post("/api/assignments", json=payload, headers=auth_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert len(data["students"]) == 2
        student_ids = [s["student_id"] for s in data["students"]]
        assert test_student.id in student_ids
        assert test_student_2.id in student_ids

    async def test_create_assignment_empty_student_list(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """TC-ASN-003: 未选择学生 → 400"""
        payload = {
            "title": "无学生作业",
            "subject": "数学",
            "content": "<p>内容</p>",
            "due_date": date.today().isoformat(),
            "student_ids": [],
        }
        resp = await async_client.post("/api/assignments", json=payload, headers=auth_headers)
        assert resp.status_code == 400

    async def test_create_assignment_nonexistent_student(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """TC-ASN-004: 包含不存在的学生 ID → 404"""
        payload = {
            "title": "无效学生作业",
            "subject": "数学",
            "content": "<p>内容</p>",
            "due_date": date.today().isoformat(),
            "student_ids": [99999],
        }
        resp = await async_client.post("/api/assignments", json=payload, headers=auth_headers)
        assert resp.status_code == 404

    async def test_create_assignment_missing_title(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_student: Student,
    ):
        """TC-ASN-005: 缺少标题 → 422"""
        payload = {
            "subject": "数学",
            "content": "<p>内容</p>",
            "due_date": date.today().isoformat(),
            "student_ids": [test_student.id],
        }
        resp = await async_client.post("/api/assignments", json=payload, headers=auth_headers)
        assert resp.status_code == 422


class TestListAssignments:
    """US-302 查看作业完成情况"""

    async def test_list_assignments(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_student: Student,
    ):
        """TC-ASN-006: 获取作业列表（分页）"""
        # 先创建作业
        due = (date.today() + timedelta(days=7)).isoformat()
        await async_client.post(
            "/api/assignments",
            json={
                "title": "列表测试作业",
                "subject": "英语",
                "content": "<p>内容</p>",
                "due_date": due,
                "student_ids": [test_student.id],
            },
            headers=auth_headers,
        )

        resp = await async_client.get(
            "/api/assignments?page=1&page_size=10", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 1
        # 检查列表中每项包含统计字段
        for item in data["items"]:
            assert "student_count" in item
            assert "submitted_count" in item
            assert "graded_count" in item

    async def test_get_assignment_detail(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_student: Student,
    ):
        """TC-ASN-007: 获取作业详情（含学生完成情况）（US-302 AC1）"""
        due = (date.today() + timedelta(days=7)).isoformat()
        create_resp = await async_client.post(
            "/api/assignments",
            json={
                "title": "详情测试作业",
                "subject": "物理",
                "content": "<p>内容</p>",
                "due_date": due,
                "student_ids": [test_student.id],
            },
            headers=auth_headers,
        )
        assignment_id = create_resp.json()["id"]

        resp = await async_client.get(
            f"/api/assignments/{assignment_id}", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == assignment_id
        assert "students" in data
        assert len(data["students"]) == 1
        student_sub = data["students"][0]
        assert student_sub["status"] == "pending"
        assert student_sub["score"] is None


class TestGradeAssignment:
    """US-303 批改作业"""

    async def _create_assignment_with_student(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        student_id: int,
        title: str = "批改测试作业",
    ) -> int:
        """辅助方法：创建作业并返回 assignment_id"""
        due = (date.today() + timedelta(days=7)).isoformat()
        resp = await async_client.post(
            "/api/assignments",
            json={
                "title": title,
                "subject": "数学",
                "content": "<p>内容</p>",
                "due_date": due,
                "student_ids": [student_id],
            },
            headers=auth_headers,
        )
        return resp.json()["id"]

    async def test_grade_assignment_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_student: Student,
    ):
        """TC-ASN-008: 批改作业（评分+评语），状态变为 graded（US-303 AC1/AC2）"""
        assignment_id = await self._create_assignment_with_student(
            async_client, auth_headers, test_student.id, "批改测试1"
        )

        resp = await async_client.post(
            f"/api/assignments/{assignment_id}/grade/{test_student.id}",
            json={"score": 85, "comment": "整体掌握较好，第8题计算有误"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["score"] == 85
        assert data["comment"] == "整体掌握较好，第8题计算有误"
        assert "graded_at" in data

        # 确认详情中状态为 graded
        detail_resp = await async_client.get(
            f"/api/assignments/{assignment_id}", headers=auth_headers
        )
        students = detail_resp.json()["students"]
        student_sub = next(s for s in students if s["student_id"] == test_student.id)
        assert student_sub["status"] == "graded"
        assert student_sub["score"] == 85

    async def test_grade_assignment_regrading(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_student: Student,
    ):
        """TC-ASN-009: 重复批改 → 覆盖之前记录（US-303 AC3）"""
        assignment_id = await self._create_assignment_with_student(
            async_client, auth_headers, test_student.id, "重新批改测试"
        )

        # 第一次批改
        await async_client.post(
            f"/api/assignments/{assignment_id}/grade/{test_student.id}",
            json={"score": 70, "comment": "一般"},
            headers=auth_headers,
        )

        # 第二次批改（覆盖）
        resp = await async_client.post(
            f"/api/assignments/{assignment_id}/grade/{test_student.id}",
            json={"score": 90, "comment": "订正后很好"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["score"] == 90
        assert data["comment"] == "订正后很好"

    async def test_grade_invalid_score_above_100(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_student: Student,
    ):
        """TC-ASN-010: 评分超过 100 → 400（US-303 AC1）"""
        assignment_id = await self._create_assignment_with_student(
            async_client, auth_headers, test_student.id, "无效分数测试"
        )

        resp = await async_client.post(
            f"/api/assignments/{assignment_id}/grade/{test_student.id}",
            json={"score": 101, "comment": ""},
            headers=auth_headers,
        )
        assert resp.status_code == 400

    async def test_grade_invalid_score_below_0(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_student: Student,
    ):
        """TC-ASN-011: 评分低于 0 → 400"""
        assignment_id = await self._create_assignment_with_student(
            async_client, auth_headers, test_student.id, "负分测试"
        )

        resp = await async_client.post(
            f"/api/assignments/{assignment_id}/grade/{test_student.id}",
            json={"score": -1, "comment": ""},
            headers=auth_headers,
        )
        assert resp.status_code == 400

    async def test_grade_nonexistent_assignment(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_student: Student,
    ):
        """TC-ASN-012: 批改不存在的作业 → 404"""
        resp = await async_client.post(
            f"/api/assignments/99999/grade/{test_student.id}",
            json={"score": 80, "comment": ""},
            headers=auth_headers,
        )
        assert resp.status_code == 404

    async def test_grade_wrong_student(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_student: Student,
        test_student_2: Student,
    ):
        """TC-ASN-013: 批改未分配该作业的学生 → 404"""
        assignment_id = await self._create_assignment_with_student(
            async_client, auth_headers, test_student.id, "只有学生A的作业"
        )
        # 尝试批改学生 B（未分配此作业）
        resp = await async_client.post(
            f"/api/assignments/{assignment_id}/grade/{test_student_2.id}",
            json={"score": 80, "comment": ""},
            headers=auth_headers,
        )
        assert resp.status_code == 404
