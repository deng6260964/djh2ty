"""
老师端新版工作台与账户聚合接口测试
"""
from datetime import datetime, timedelta

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assignment import Assignment, AssignmentStudent
from app.models.billing import BillingRecord, SubjectPrice
from app.models.course import Course
from app.models.student import Student


class TestWorkbenchEndpoints:
    async def test_workbench_endpoint_returns_aggregated_sections(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        db: AsyncSession,
        test_student: Student,
    ):
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        course_today = Course(
          student_id=test_student.id,
          subject="数学",
          start_time=today_start + timedelta(hours=9),
          end_time=today_start + timedelta(hours=10, minutes=30),
          duration=90,
          status="completed",
          hourly_rate=120,
        )
        course_pending = Course(
          student_id=test_student.id,
          subject="英语",
          start_time=now - timedelta(days=1, hours=3),
          end_time=now - timedelta(days=1, hours=2),
          duration=60,
          status="scheduled",
          hourly_rate=120,
        )
        course_future = Course(
          student_id=test_student.id,
          subject="英语",
          start_time=now + timedelta(days=1),
          end_time=now + timedelta(days=1, hours=1),
          duration=60,
          status="scheduled",
          hourly_rate=120,
        )
        db.add_all([course_today, course_pending, course_future])
        await db.flush()

        assignment = Assignment(
          title="工作台作业",
          subject="数学",
          content="完成练习题",
          due_date=(now + timedelta(days=2)).date(),
        )
        db.add(assignment)
        await db.flush()
        db.add(
          AssignmentStudent(
            assignment_id=assignment.id,
            student_id=test_student.id,
            status="submitted",
            submitted_at=now,
          )
        )
        db.add(
          BillingRecord(
            student_id=test_student.id,
            amount=240,
            paid_amount=120,
            status="partial",
            paid_at=now - timedelta(days=1),
          )
        )
        await db.commit()

        resp = await async_client.get("/api/dashboard/workbench", headers=auth_headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["summary"] == {
            "pending_record_count": 1,
            "today_course_count": 1,
            "payment_alert_count": 1,
            "assignment_review_count": 1,
        }

        assert [item["id"] for item in data["today_courses"]] == [course_today.id]
        today_item = data["today_courses"][0]
        assert today_item["student_id"] == test_student.id
        assert today_item["student_name"] == test_student.name
        assert today_item["subject"] == "数学"
        assert today_item["status"] == "completed"
        assert today_item["current_balance"] == -120.0
        assert today_item["projected_charge"] == 180.0
        assert today_item["needs_payment"] is True

        assert [item["id"] for item in data["pending_records"]] == [course_pending.id]
        pending_item = data["pending_records"][0]
        assert pending_item["student_id"] == test_student.id
        assert pending_item["subject"] == "英语"
        assert pending_item["projected_charge"] == 120.0
        assert pending_item["needs_payment"] is True

        assert [item["next_course_id"] for item in data["payment_alerts"]] == [
            course_future.id
        ]
        payment_alert = data["payment_alerts"][0]
        assert payment_alert["student_id"] == test_student.id
        assert payment_alert["current_balance"] == -120.0
        assert payment_alert["projected_charge"] == 120.0
        assert payment_alert["shortage_amount"] == 240.0

        assert [item["assignment_id"] for item in data["assignment_reviews"]] == [
            assignment.id
        ]
        assignment_item = data["assignment_reviews"][0]
        assert assignment_item["student_id"] == test_student.id
        assert assignment_item["assignment_title"] == "工作台作业"
        assert assignment_item["status"] == "submitted"

    async def test_courses_week_endpoint_marks_weekend_and_payment_risk(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        db: AsyncSession,
        test_student: Student,
    ):
        course = Course(
          student_id=test_student.id,
          subject="数学",
          start_time=datetime(2026, 4, 25, 9, 0, 0),
          end_time=datetime(2026, 4, 25, 10, 30, 0),
          duration=90,
          status="scheduled",
          hourly_rate=150,
        )
        db.add(course)
        db.add(
          BillingRecord(
            student_id=test_student.id,
            amount=300,
            paid_amount=100,
            status="partial",
          )
        )
        await db.commit()

        resp = await async_client.get(
          "/api/courses/week?week_start=2026-04-20",
          headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["week_start"] == "2026-04-20"
        assert len(data["items"]) == 1
        item = data["items"][0]
        assert item["is_weekend"] is True
        assert item["needs_payment"] is True
        assert item["projected_charge"] == 225.0

    async def test_recharge_clears_payment_alert_across_account_and_workbench(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """预收充值后，学生账户和工作台待收费提醒应同步解除"""
        await async_client.put(
            "/api/billing/subject-prices/数学",
            json={"price_per_hour": 120.0},
            headers=auth_headers,
        )
        student_resp = await async_client.post(
            "/api/students",
            json={
                "name": "V2收费提醒学生",
                "grade": "初二",
                "subjects": ["数学"],
                "parent_phone": "13000000901",
            },
            headers=auth_headers,
        )
        assert student_resp.status_code == 201, student_resp.text
        student_id = student_resp.json()["id"]

        tomorrow = datetime.now() + timedelta(days=1)
        course_resp = await async_client.post(
            "/api/courses",
            json={
                "student_id": student_id,
                "subject": "数学",
                "start_time": tomorrow.replace(
                    hour=9, minute=0, second=0, microsecond=0
                ).isoformat(),
                "end_time": tomorrow.replace(
                    hour=10, minute=30, second=0, microsecond=0
                ).isoformat(),
            },
            headers=auth_headers,
        )
        assert course_resp.status_code == 201, course_resp.text
        course_id = course_resp.json()["id"]

        account_before_resp = await async_client.get(
            f"/api/billing/students/{student_id}/account",
            headers=auth_headers,
        )
        assert account_before_resp.status_code == 200, account_before_resp.text
        account_before = account_before_resp.json()
        assert account_before["current_balance"] == 0.0
        assert account_before["has_payment_alert"] is True
        assert account_before["next_course_id"] == course_id
        assert account_before["next_course_projected_charge"] == 180.0

        workbench_before_resp = await async_client.get(
            "/api/dashboard/workbench",
            headers=auth_headers,
        )
        assert workbench_before_resp.status_code == 200, workbench_before_resp.text
        alerts_before = workbench_before_resp.json()["payment_alerts"]
        alert_before = next(
            alert for alert in alerts_before if alert["student_id"] == student_id
        )
        assert alert_before["next_course_id"] == course_id
        assert alert_before["projected_charge"] == 180.0
        assert alert_before["shortage_amount"] == 180.0

        recharge_resp = await async_client.post(
            "/api/billing/recharge",
            json={
                "student_id": student_id,
                "paid_amount": 300.0,
                "payment_method": "wechat",
                "notes": "解除下一节课收费提醒",
            },
            headers=auth_headers,
        )
        assert recharge_resp.status_code == 201, recharge_resp.text

        account_after_resp = await async_client.get(
            f"/api/billing/students/{student_id}/account",
            headers=auth_headers,
        )
        assert account_after_resp.status_code == 200, account_after_resp.text
        account_after = account_after_resp.json()
        assert account_after["current_balance"] == 300.0
        assert account_after["has_payment_alert"] is False
        assert account_after["next_course_id"] == course_id

        workbench_after_resp = await async_client.get(
            "/api/dashboard/workbench",
            headers=auth_headers,
        )
        assert workbench_after_resp.status_code == 200, workbench_after_resp.text
        alerts_after = workbench_after_resp.json()["payment_alerts"]
        assert all(alert["student_id"] != student_id for alert in alerts_after)

    async def test_student_account_endpoint_returns_balance_and_records(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        db: AsyncSession,
        test_student: Student,
    ):
        db.add(SubjectPrice(subject="数学", price_per_hour=120))
        course = Course(
          student_id=test_student.id,
          subject="数学",
          start_time=datetime.now() + timedelta(days=1),
          end_time=datetime.now() + timedelta(days=1, hours=1),
          duration=60,
          status="scheduled",
          hourly_rate=120,
        )
        db.add(course)
        await db.flush()
        db.add_all(
          [
            BillingRecord(
              student_id=test_student.id,
              amount=240,
              paid_amount=0,
              status="unpaid",
              course_id=course.id,
              notes="自动扣费记录",
            ),
            BillingRecord(
              student_id=test_student.id,
              amount=0,
              paid_amount=1000,
              status="paid",
              payment_method="wechat",
              paid_at=datetime.now(),
              notes="家长充值",
            ),
          ]
        )
        await db.commit()

        resp = await async_client.get(
          f"/api/billing/students/{test_student.id}/account",
          headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["student_id"] == test_student.id
        assert data["student_name"] == test_student.name
        assert data["main_subject"] == "数学"
        assert data["current_balance"] == 760.0
        assert data["has_payment_alert"] is False
        assert len(data["recent_payments"]) >= 1
        assert len(data["recent_charges"]) >= 1
