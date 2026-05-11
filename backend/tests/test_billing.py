"""
收费管理模块测试
覆盖用户故事 US-501 ~ US-505
"""
import pytest
from datetime import datetime, date, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.student import Student
from app.models.billing import SubjectPrice, BillingRecord
from app.models.course import Course
from app.models.user import User
from app.utils.auth import get_password_hash


class TestSubjectPrices:
    """US-501 设置科目课时单价"""

    async def test_list_subject_prices_empty(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """TC-BIL-001: 获取科目单价列表（US-501 AC3）"""
        resp = await async_client.get(
            "/api/billing/subject-prices", headers=auth_headers
        )
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_update_subject_price_create_new(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """TC-BIL-002: 设置新科目单价（不存在则创建）（US-501 AC1）"""
        resp = await async_client.put(
            "/api/billing/subject-prices/英语",
            json={"price_per_hour": 160.0},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["subject"] == "英语"
        assert float(data["price_per_hour"]) == 160.0

    async def test_update_subject_price_modify_existing(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_subject_price: SubjectPrice,
    ):
        """TC-BIL-003: 修改已有科目单价（US-501 AC1/AC2）"""
        # test_subject_price: 数学 150 元/小时
        resp = await async_client.put(
            "/api/billing/subject-prices/数学",
            json={"price_per_hour": 180.0},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert float(data["price_per_hour"]) == 180.0

    async def test_subject_price_in_list_after_update(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """TC-BIL-004: 更新单价后出现在列表中（US-501 AC3）"""
        await async_client.put(
            "/api/billing/subject-prices/物理",
            json={"price_per_hour": 200.0},
            headers=auth_headers,
        )
        resp = await async_client.get(
            "/api/billing/subject-prices", headers=auth_headers
        )
        prices = resp.json()
        subjects = [p["subject"] for p in prices]
        assert "物理" in subjects
        phys_price = next(p for p in prices if p["subject"] == "物理")
        assert float(phys_price["price_per_hour"]) == 200.0


class TestBillingRecords:
    """US-503 记录收款 / US-502 自动计算应收费用"""

    async def test_create_billing_record(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_student: Student,
    ):
        """TC-BIL-005: 添加收款记录（US-503 AC1）"""
        resp = await async_client.post(
            "/api/billing/records",
            json={
                "student_id": test_student.id,
                "amount": 300.0,
                "notes": "2小时数学课",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert float(data["amount"]) == 300.0
        assert data["status"] == "unpaid"
        assert data["student_id"] == test_student.id

    async def test_create_billing_record_nonexistent_student(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """TC-BIL-006: 创建收费记录时学生不存在 → 404"""
        resp = await async_client.post(
            "/api/billing/records",
            json={
                "student_id": 99999,
                "amount": 300.0,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 404

    async def test_list_billing_records(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_student: Student,
    ):
        """TC-BIL-007: 获取收费记录列表（分页）"""
        # 先创建记录
        await async_client.post(
            "/api/billing/records",
            json={"student_id": test_student.id, "amount": 150.0},
            headers=auth_headers,
        )

        resp = await async_client.get(
            "/api/billing/records?page=1&page_size=10", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert data["total"] >= 1

    async def test_pay_billing_record_full(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_student: Student,
    ):
        """TC-BIL-008: 全额收款，状态变为 paid（US-503 AC2）"""
        # 创建应收记录
        create_resp = await async_client.post(
            "/api/billing/records",
            json={"student_id": test_student.id, "amount": 300.0},
            headers=auth_headers,
        )
        record_id = create_resp.json()["id"]

        # 全额付款
        resp = await async_client.patch(
            f"/api/billing/records/{record_id}/pay",
            json={
                "paid_amount": 300.0,
                "payment_method": "wechat",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert float(data["paid_amount"]) == 300.0
        assert data["status"] == "paid"

    async def test_pay_billing_record_partial(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_student: Student,
    ):
        """TC-BIL-009: 部分收款，状态变为 partial（US-503 AC2）"""
        create_resp = await async_client.post(
            "/api/billing/records",
            json={"student_id": test_student.id, "amount": 300.0},
            headers=auth_headers,
        )
        record_id = create_resp.json()["id"]

        resp = await async_client.patch(
            f"/api/billing/records/{record_id}/pay",
            json={
                "paid_amount": 150.0,
                "payment_method": "cash",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert float(data["paid_amount"]) == 150.0
        assert data["status"] == "partial"

    async def test_delete_billing_record(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_student: Student,
    ):
        """TC-BIL-010: 删除收费记录（US-503 AC3）"""
        create_resp = await async_client.post(
            "/api/billing/records",
            json={"student_id": test_student.id, "amount": 100.0},
            headers=auth_headers,
        )
        record_id = create_resp.json()["id"]

        resp = await async_client.delete(
            f"/api/billing/records/{record_id}", headers=auth_headers
        )
        assert resp.status_code == 204

    async def test_recharge_creates_prepaid_balance_record(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_student: Student,
    ):
        """TC-BIL-011: 预收充值应直接增加学生余额"""
        resp = await async_client.post(
            "/api/billing/recharge",
            json={
                "student_id": test_student.id,
                "paid_amount": 600.0,
                "payment_method": "wechat",
                "notes": "预收 4 节课",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert float(data["amount"]) == 0.0
        assert float(data["paid_amount"]) == 600.0
        assert data["status"] == "paid"
        assert data["student_id"] == test_student.id

    async def test_my_account_returns_current_student_balance(
        self,
        async_client: AsyncClient,
        db: AsyncSession,
        test_student: Student,
        test_subject_price: SubjectPrice,
    ):
        """学生端账户接口只能读取当前登录学生的余额、扣费和下节课提醒。"""
        student_user = User(
            username="student_account",
            hashed_password=get_password_hash("student123"),
            role="student",
            display_name=test_student.name,
            is_active=True,
        )
        db.add(student_user)
        await db.flush()
        test_student.user_id = student_user.id

        next_course_start = datetime.now() + timedelta(days=1)
        course = Course(
            student_id=test_student.id,
            subject="数学",
            start_time=next_course_start,
            end_time=next_course_start + timedelta(minutes=90),
            duration=90,
            status="scheduled",
            hourly_rate=150.0,
        )
        db.add(course)
        await db.flush()

        db.add(
            BillingRecord(
                student_id=test_student.id,
                paid_amount=300.0,
                amount=0.0,
                status="paid",
                payment_method="wechat",
                notes="预收充值",
            )
        )
        db.add(
            BillingRecord(
                student_id=test_student.id,
                course_id=course.id,
                paid_amount=0.0,
                amount=150.0,
                status="paid",
                notes="课程完成自动扣费",
            )
        )
        await db.flush()

        login_resp = await async_client.post(
            "/api/auth/login",
            json={"username": "student_account", "password": "student123"},
        )
        assert login_resp.status_code == 200
        headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

        resp = await async_client.get("/api/billing/my/account", headers=headers)

        assert resp.status_code == 200
        data = resp.json()
        assert data["student_id"] == test_student.id
        assert data["student_name"] == test_student.name
        assert data["current_balance"] == 150.0
        assert data["total_received"] == 300.0
        assert data["total_charged"] == 150.0
        assert data["next_course_id"] == course.id
        assert data["next_course_projected_charge"] == 225.0
        assert data["has_payment_alert"] is True
        assert len(data["recent_payments"]) == 1
        assert len(data["recent_charges"]) == 1


class TestBillingSummary:
    """US-504 收费汇总报表 / US-505 欠费提醒"""

    async def _setup_billing_data(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        student_id: int,
        amount: float,
        paid_amount: float = 0.0,
    ):
        """辅助：创建收费记录并可选地标记部分付款"""
        create_resp = await async_client.post(
            "/api/billing/records",
            json={"student_id": student_id, "amount": amount},
            headers=auth_headers,
        )
        record_id = create_resp.json()["id"]

        if paid_amount > 0:
            await async_client.patch(
                f"/api/billing/records/{record_id}/pay",
                json={"paid_amount": paid_amount, "payment_method": "cash"},
                headers=auth_headers,
            )

        return record_id

    async def test_billing_summary_total_receivable(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_student: Student,
        db: AsyncSession,
    ):
        """TC-BIL-012: 收费汇总应收总额正确（US-504 AC2）"""
        # 先清空已有记录（通过 db 直接操作）
        from sqlalchemy import delete
        await db.execute(
            delete(BillingRecord).where(BillingRecord.student_id == test_student.id)
        )
        await db.flush()

        # 添加 3 条应收记录
        await self._setup_billing_data(
            async_client, auth_headers, test_student.id, 150.0
        )
        await self._setup_billing_data(
            async_client, auth_headers, test_student.id, 150.0
        )
        await self._setup_billing_data(
            async_client, auth_headers, test_student.id, 150.0
        )

        resp = await async_client.get(
            "/api/billing/summary", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "total_receivable" in data
        assert "total_paid" in data
        assert "total_outstanding" in data
        assert float(data["total_receivable"]) == 450.0
        assert float(data["total_paid"]) == 0.0
        assert float(data["total_outstanding"]) == 450.0

        student_summary = next(
            item for item in data["by_student"] if item["student_id"] == test_student.id
        )
        assert float(student_summary["receivable"]) == 450.0
        assert float(student_summary["paid"]) == 0.0
        assert float(student_summary["outstanding"]) == 450.0

    async def test_billing_summary_outstanding_calculation(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_student: Student,
        db: AsyncSession,
    ):
        """TC-BIL-013: 欠费 = 应收 - 已收（US-502 AC1）"""
        from sqlalchemy import delete
        await db.execute(
            delete(BillingRecord).where(BillingRecord.student_id == test_student.id)
        )
        await db.flush()

        # 应收 450，已付 200
        record_ids = []
        for _ in range(3):
            r_id = await self._setup_billing_data(
                async_client, auth_headers, test_student.id, 150.0
            )
            record_ids.append(r_id)

        # 付款 200
        await async_client.patch(
            f"/api/billing/records/{record_ids[0]}/pay",
            json={"paid_amount": 200.0, "payment_method": "wechat"},
            headers=auth_headers,
        )

        resp = await async_client.get(
            "/api/billing/summary", headers=auth_headers
        )
        data = resp.json()
        assert float(data["total_receivable"]) == 450.0
        assert float(data["total_paid"]) == 200.0
        assert float(data["total_outstanding"]) == 250.0

        student_summary = next(
            item for item in data["by_student"] if item["student_id"] == test_student.id
        )
        assert float(student_summary["receivable"]) == 450.0
        assert float(student_summary["paid"]) == 200.0
        assert float(student_summary["outstanding"]) == 250.0

    async def test_billing_summary_by_student(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_student: Student,
    ):
        """TC-BIL-014: 汇总包含按学生明细（US-504 AC2）"""
        await self._setup_billing_data(
            async_client, auth_headers, test_student.id, 100.0
        )

        resp = await async_client.get(
            "/api/billing/summary", headers=auth_headers
        )
        data = resp.json()
        assert "by_student" in data
        assert isinstance(data["by_student"], list)


class TestOutstandingStudents:
    """US-505 欠费学生列表"""

    async def test_outstanding_students_list(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_student: Student,
        db: AsyncSession,
    ):
        """TC-BIL-015: 欠费学生列表：应收>已收的学生（US-505 AC1）"""
        from sqlalchemy import delete
        await db.execute(
            delete(BillingRecord).where(BillingRecord.student_id == test_student.id)
        )
        await db.flush()

        # 创建一条应收 300，未付款的记录
        await async_client.post(
            "/api/billing/records",
            json={"student_id": test_student.id, "amount": 300.0},
            headers=auth_headers,
        )

        resp = await async_client.get(
            "/api/billing/outstanding", headers=auth_headers
        )
        assert resp.status_code == 200
        outstanding = resp.json()
        assert isinstance(outstanding, list)

        # 找到测试学生
        student_entry = next(
            (o for o in outstanding if o["student_id"] == test_student.id), None
        )
        assert student_entry is not None
        assert float(student_entry["outstanding_amount"]) > 0

    async def test_fully_paid_student_not_in_outstanding(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_student_2: Student,
        db: AsyncSession,
    ):
        """TC-BIL-016: 已全额付款的学生不在欠费列表中"""
        from sqlalchemy import delete
        await db.execute(
            delete(BillingRecord).where(BillingRecord.student_id == test_student_2.id)
        )
        await db.flush()

        # 创建并全额付款
        create_resp = await async_client.post(
            "/api/billing/records",
            json={"student_id": test_student_2.id, "amount": 200.0},
            headers=auth_headers,
        )
        record_id = create_resp.json()["id"]

        await async_client.patch(
            f"/api/billing/records/{record_id}/pay",
            json={"paid_amount": 200.0, "payment_method": "wechat"},
            headers=auth_headers,
        )

        resp = await async_client.get(
            "/api/billing/outstanding", headers=auth_headers
        )
        outstanding = resp.json()
        outstanding_ids = [o["student_id"] for o in outstanding]
        assert test_student_2.id not in outstanding_ids
