"""
课程管理模块测试（重点：冲突检测）
覆盖用户故事 US-201 ~ US-205
"""
import pytest
from datetime import datetime
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.student import Student
from app.models.course import Course
from app.models.billing import BillingRecord


class TestCreateCourse:
    """US-201 添加课程"""

    async def test_create_course_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_student: Student,
    ):
        """TC-CRS-001: 正常创建课程 → 201（US-201 AC1/AC2）"""
        payload = {
            "student_id": test_student.id,
            "subject": "数学",
            "start_time": "2026-03-10T14:00:00",
            "end_time": "2026-03-10T15:30:00",
            "location": "线上",
            "notes": "复习二次方程",
        }
        resp = await async_client.post("/api/courses", json=payload, headers=auth_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["subject"] == "数学"
        assert data["student_id"] == test_student.id
        assert data["status"] == "scheduled"
        assert data["duration"] == 90  # 90 分钟

    async def test_create_course_duration_calculation(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_student: Student,
    ):
        """TC-CRS-002: 时长自动计算（US-201 AC3）"""
        payload = {
            "student_id": test_student.id,
            "subject": "英语",
            "start_time": "2026-03-11T09:00:00",
            "end_time": "2026-03-11T09:30:00",
            "location": "线下",
        }
        resp = await async_client.post("/api/courses", json=payload, headers=auth_headers)
        assert resp.status_code == 201
        assert resp.json()["duration"] == 30  # 0.5 小时 = 30 分钟

    async def test_create_course_missing_student(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """TC-CRS-003: 学生不存在 → 404"""
        payload = {
            "student_id": 99999,
            "subject": "数学",
            "start_time": "2026-03-12T10:00:00",
            "end_time": "2026-03-12T11:00:00",
        }
        resp = await async_client.post("/api/courses", json=payload, headers=auth_headers)
        assert resp.status_code == 404

    async def test_create_course_missing_required_fields(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """TC-CRS-004: 缺少必填字段 → 422（US-201 AC1）"""
        # 缺少 end_time
        payload = {
            "student_id": 1,
            "subject": "数学",
            "start_time": "2026-03-12T10:00:00",
        }
        resp = await async_client.post("/api/courses", json=payload, headers=auth_headers)
        assert resp.status_code == 422


class TestConflictDetection:
    """US-202 上课时间冲突检测"""

    async def test_conflict_same_time_slot(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_student: Student,
        test_course: Course,
    ):
        """TC-CRS-005: 同一时间段已有课程 → 409（US-202 AC1/AC2）"""
        # test_course 占用 2026-03-02 10:00-11:00
        payload = {
            "student_id": test_student.id,
            "subject": "英语",
            "start_time": "2026-03-02T10:00:00",  # 完全相同时间段
            "end_time": "2026-03-02T11:00:00",
        }
        resp = await async_client.post("/api/courses", json=payload, headers=auth_headers)
        assert resp.status_code == 409
        data = resp.json()
        assert data["detail"]["code"] == "COURSE_TIME_CONFLICT"

    async def test_conflict_overlap_start(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_student: Student,
        test_course: Course,
    ):
        """TC-CRS-006: 新课开始时间在已有课时间段内 → 409（US-202 AC2）"""
        # test_course: 10:00-11:00，新课: 10:30-11:30（开始时间在已有课段内）
        payload = {
            "student_id": test_student.id,
            "subject": "英语",
            "start_time": "2026-03-02T10:30:00",
            "end_time": "2026-03-02T11:30:00",
        }
        resp = await async_client.post("/api/courses", json=payload, headers=auth_headers)
        assert resp.status_code == 409

    async def test_conflict_overlap_end(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_student: Student,
        test_course: Course,
    ):
        """TC-CRS-007: 新课结束时间在已有课时间段内 → 409（US-202 AC2）"""
        # test_course: 10:00-11:00，新课: 09:30-10:30（结束时间在已有课段内）
        payload = {
            "student_id": test_student.id,
            "subject": "英语",
            "start_time": "2026-03-02T09:30:00",
            "end_time": "2026-03-02T10:30:00",
        }
        resp = await async_client.post("/api/courses", json=payload, headers=auth_headers)
        assert resp.status_code == 409

    async def test_conflict_contains_existing(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_student: Student,
        test_course: Course,
    ):
        """TC-CRS-008: 新课时间包含已有课时间 → 409（US-202 AC2）"""
        # test_course: 10:00-11:00，新课: 09:00-12:00（完全包含已有课）
        payload = {
            "student_id": test_student.id,
            "subject": "英语",
            "start_time": "2026-03-02T09:00:00",
            "end_time": "2026-03-02T12:00:00",
        }
        resp = await async_client.post("/api/courses", json=payload, headers=auth_headers)
        assert resp.status_code == 409

    async def test_no_conflict_adjacent_end_equals_start(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_student: Student,
        test_course: Course,
    ):
        """TC-CRS-009: 边界时间 A结束=B开始 → 不冲突，允许创建（US-202 AC2）"""
        # test_course: 10:00-11:00，新课: 11:00-12:00（紧接开始，不重叠）
        payload = {
            "student_id": test_student.id,
            "subject": "英语",
            "start_time": "2026-03-02T11:00:00",
            "end_time": "2026-03-02T12:00:00",
        }
        resp = await async_client.post("/api/courses", json=payload, headers=auth_headers)
        assert resp.status_code == 201, f"期望 201，实际: {resp.status_code}, {resp.text}"

    async def test_no_conflict_before_existing(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_student: Student,
        test_course: Course,
    ):
        """TC-CRS-010: 新课完全在已有课之前 → 不冲突"""
        # test_course: 10:00-11:00，新课: 08:00-09:00
        payload = {
            "student_id": test_student.id,
            "subject": "英语",
            "start_time": "2026-03-02T08:00:00",
            "end_time": "2026-03-02T09:00:00",
        }
        resp = await async_client.post("/api/courses", json=payload, headers=auth_headers)
        assert resp.status_code == 201

    async def test_check_conflict_endpoint(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_course: Course,
    ):
        """TC-CRS-011: 冲突检测接口（不创建课程）"""
        # 冲突时间
        resp = await async_client.post(
            "/api/courses/check-conflict",
            json={
                "start_time": "2026-03-02T10:00:00",
                "end_time": "2026-03-02T11:00:00",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["has_conflict"] is True
        assert "conflict" in data

    async def test_check_conflict_no_conflict(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_course: Course,
    ):
        """TC-CRS-012: 冲突检测接口 - 无冲突情形"""
        resp = await async_client.post(
            "/api/courses/check-conflict",
            json={
                "start_time": "2026-03-02T14:00:00",
                "end_time": "2026-03-02T15:00:00",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["has_conflict"] is False


class TestCalendarView:
    """US-203 日历视图"""

    async def test_calendar_view_format(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_course: Course,
    ):
        """TC-CRS-013: 日历视图接口返回格式正确（US-203 AC1/AC2）"""
        resp = await async_client.get(
            "/api/courses/calendar?year=2026&month=3",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        # 应该是以日期为 key 的字典
        assert isinstance(data, dict)
        # test_course 在 2026-03-02
        if "2026-03-02" in data:
            day_courses = data["2026-03-02"]
            assert isinstance(day_courses, list)
            assert len(day_courses) >= 1
            course_item = day_courses[0]
            assert "id" in course_item
            assert "student_name" in course_item
            assert "subject" in course_item
            assert "start_time" in course_item
            assert "end_time" in course_item
            assert "status" in course_item

    async def test_calendar_missing_params(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """TC-CRS-014: 日历接口缺少必填参数 → 422"""
        resp = await async_client.get(
            "/api/courses/calendar?year=2026",  # 缺少 month
            headers=auth_headers,
        )
        assert resp.status_code == 422


class TestUpdateCourseStatus:
    """US-204 标记课程状态"""

    async def test_mark_course_completed(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_course: Course,
    ):
        """TC-CRS-015: 标记课程为已完成（US-204 AC1）"""
        resp = await async_client.patch(
            f"/api/courses/{test_course.id}/status",
            json={"status": "completed"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "completed"

    async def test_mark_course_cancelled(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_student: Student,
    ):
        """TC-CRS-016: 标记课程为已取消（US-204 AC1）"""
        # 创建一个新课程
        create_resp = await async_client.post(
            "/api/courses",
            json={
                "student_id": test_student.id,
                "subject": "物理",
                "start_time": "2026-03-15T14:00:00",
                "end_time": "2026-03-15T15:00:00",
            },
            headers=auth_headers,
        )
        course_id = create_resp.json()["id"]

        resp = await async_client.patch(
            f"/api/courses/{course_id}/status",
            json={"status": "cancelled"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "cancelled"

    async def test_invalid_status_value(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_course: Course,
    ):
        """TC-CRS-017: 无效的状态值 → 400"""
        resp = await async_client.patch(
            f"/api/courses/{test_course.id}/status",
            json={"status": "invalid_status"},
            headers=auth_headers,
        )
        assert resp.status_code == 400

    async def test_cancelled_course_not_conflict(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_student: Student,
        db: AsyncSession,
    ):
        """TC-CRS-018: 已取消的课程不参与冲突检测（US-202 AC2）"""
        # 创建一个课程并取消
        course = Course(
            student_id=test_student.id,
            subject="语文",
            start_time=datetime(2026, 3, 20, 14, 0),
            end_time=datetime(2026, 3, 20, 15, 0),
            duration=60,
            status="cancelled",
        )
        db.add(course)
        await db.flush()

        # 在相同时间创建新课程，不应冲突
        resp = await async_client.post(
            "/api/courses",
            json={
                "student_id": test_student.id,
                "subject": "数学",
                "start_time": "2026-03-20T14:00:00",
                "end_time": "2026-03-20T15:00:00",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201, f"已取消的课程不应引发冲突：{resp.text}"


class TestListCourses:
    """课程列表测试"""

    async def test_list_courses(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_course: Course,
    ):
        """TC-CRS-019: 获取课程列表"""
        resp = await async_client.get("/api/courses", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert data["total"] >= 1

    async def test_list_courses_filter_by_student(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_student: Student,
        test_course: Course,
    ):
        """TC-CRS-020: 按学生 ID 过滤课程列表"""
        resp = await async_client.get(
            f"/api/courses?student_id={test_student.id}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) >= 1
        for item in items:
            assert item["student_id"] == test_student.id


class TestCopyWeekCourses:
    """复制上一周课程"""

    async def test_copy_week_preview_marks_conflict_and_payment_risk(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_student: Student,
        test_course: Course,
        db: AsyncSession,
    ):
        """复制预览应标出冲突和收费风险"""
        conflicting_course = Course(
            student_id=test_student.id,
            subject="英语",
            start_time=datetime(2026, 3, 9, 10, 0),
            end_time=datetime(2026, 3, 9, 11, 0),
            duration=60,
            status="scheduled",
            hourly_rate=180.00,
        )
        db.add(conflicting_course)
        await db.flush()

        resp = await async_client.post(
            "/api/courses/copy-week-preview",
            json={
                "source_week_start": "2026-03-02",
                "target_week_start": "2026-03-09",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_count"] == 1
        assert data["conflict_count"] == 1
        assert data["needs_payment_count"] == 1
        item = data["items"][0]
        assert item["source_course_id"] == test_course.id
        assert item["has_conflict"] is True
        assert item["status"] == "conflict"
        assert item["needs_payment"] is True
        assert item["target_start_time"] == "2026-03-09T10:00:00"

    async def test_copy_week_confirm_creates_selected_courses(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_course: Course,
        db: AsyncSession,
    ):
        """复制确认应创建可复制课程"""
        payment = BillingRecord(
            student_id=test_course.student_id,
            amount=0,
            paid_amount=500,
            status="paid",
        )
        db.add(payment)
        await db.flush()

        resp = await async_client.post(
            "/api/courses/copy-week-confirm",
            json={
                "source_week_start": "2026-03-02",
                "target_week_start": "2026-03-09",
                "selected_course_ids": [test_course.id],
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["created_count"] == 1
        assert data["skipped_count"] == 0
        assert len(data["created_course_ids"]) == 1

        copied_result = await db.get(Course, data["created_course_ids"][0])
        assert copied_result is not None
        assert copied_result.start_time == datetime(2026, 3, 9, 10, 0)
        assert copied_result.end_time == datetime(2026, 3, 9, 11, 0)
        assert copied_result.status == "scheduled"
        assert copied_result.subject == test_course.subject

    async def test_copy_week_confirm_skips_conflicting_courses(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_student: Student,
        test_course: Course,
        db: AsyncSession,
    ):
        """复制确认遇到冲突课程时应跳过并返回原因"""
        conflicting_course = Course(
            student_id=test_student.id,
            subject="物理",
            start_time=datetime(2026, 3, 9, 10, 0),
            end_time=datetime(2026, 3, 9, 11, 0),
            duration=60,
            status="scheduled",
            hourly_rate=180.00,
        )
        db.add(conflicting_course)
        await db.flush()

        resp = await async_client.post(
            "/api/courses/copy-week-confirm",
            json={
                "source_week_start": "2026-03-02",
                "target_week_start": "2026-03-09",
                "selected_course_ids": [test_course.id],
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["created_count"] == 0
        assert data["skipped_count"] == 1
        assert data["skipped_items"][0]["reason"] == "conflict"
