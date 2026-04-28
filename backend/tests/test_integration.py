"""
集成测试 - 完整业务流程
覆盖跨模块的端到端场景
"""
import io
from datetime import date, timedelta, datetime
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.billing import BillingRecord
from app.models.student import Student


class TestCourseWorkflow:
    """场景1: 完整排课流程（US-201/202/204/502）"""

    async def test_full_scheduling_workflow(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        db: AsyncSession,
    ):
        """
        完整排课流程：
        1. 创建学生
        2. 排课（周一 10:00-11:00）
        3. 再次排课同一时间 → 冲突 409
        4. 排课（周一 11:00-12:00）→ 成功（不冲突）
        5. 完成课程（状态改为 completed）
        """
        # 1. 创建学生
        create_student_resp = await async_client.post(
            "/api/students",
            json={
                "name": "集成测试学生A",
                "grade": "初二",
                "subjects": ["数学"],
                "parent_phone": "13000000010",
            },
            headers=auth_headers,
        )
        assert create_student_resp.status_code == 201
        student_id = create_student_resp.json()["id"]

        # 2. 排课：周一 2026-04-06 10:00-11:00
        course_resp = await async_client.post(
            "/api/courses",
            json={
                "student_id": student_id,
                "subject": "数学",
                "start_time": "2026-04-06T10:00:00",
                "end_time": "2026-04-06T11:00:00",
                "location": "线上",
            },
            headers=auth_headers,
        )
        assert course_resp.status_code == 201, f"排课失败: {course_resp.text}"
        course_id = course_resp.json()["id"]
        assert course_resp.json()["status"] == "scheduled"

        # 3. 再次排课同一时间 → 冲突 409
        conflict_resp = await async_client.post(
            "/api/courses",
            json={
                "student_id": student_id,
                "subject": "英语",
                "start_time": "2026-04-06T10:00:00",
                "end_time": "2026-04-06T11:00:00",
            },
            headers=auth_headers,
        )
        assert conflict_resp.status_code == 409
        assert conflict_resp.json()["detail"]["code"] == "COURSE_TIME_CONFLICT"

        # 4. 排课（周一 11:00-12:00）→ 成功（不冲突）
        next_course_resp = await async_client.post(
            "/api/courses",
            json={
                "student_id": student_id,
                "subject": "英语",
                "start_time": "2026-04-06T11:00:00",
                "end_time": "2026-04-06T12:00:00",
            },
            headers=auth_headers,
        )
        assert next_course_resp.status_code == 201, (
            f"紧接排课应成功: {next_course_resp.text}"
        )

        # 5. 完成课程（状态改为 completed）
        complete_resp = await async_client.patch(
            f"/api/courses/{course_id}/status",
            json={"status": "completed"},
            headers=auth_headers,
        )
        assert complete_resp.status_code == 200
        assert complete_resp.json()["status"] == "completed"

    async def test_course_calendar_shows_created_course(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """日历视图中能看到新建的课程"""
        # 创建学生
        s_resp = await async_client.post(
            "/api/students",
            json={
                "name": "日历测试学生",
                "grade": "高一",
                "subjects": ["物理"],
                "parent_phone": "13000000011",
            },
            headers=auth_headers,
        )
        student_id = s_resp.json()["id"]

        # 创建 4 月份的课程
        await async_client.post(
            "/api/courses",
            json={
                "student_id": student_id,
                "subject": "物理",
                "start_time": "2026-04-10T09:00:00",
                "end_time": "2026-04-10T10:00:00",
            },
            headers=auth_headers,
        )

        # 查看日历
        cal_resp = await async_client.get(
            "/api/courses/calendar?year=2026&month=4",
            headers=auth_headers,
        )
        assert cal_resp.status_code == 200
        calendar = cal_resp.json()
        assert "2026-04-10" in calendar


class TestAssignmentWorkflow:
    """场景2: 作业管理流程（US-301/302/303）"""

    async def test_full_assignment_workflow(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        db: AsyncSession,
    ):
        """
        完整作业流程：
        1. 布置作业（选择 2 名学生）
        2. 查看作业，提交情况为"未提交"
        3. 批改作业（给学生A打分）
        4. 查看作业详情，学生A状态变为"已批改"
        """
        due_date = (date.today() + timedelta(days=5)).isoformat()

        # 1. 创建两名学生
        s1_resp = await async_client.post(
            "/api/students",
            json={
                "name": "作业学生甲",
                "grade": "初二",
                "subjects": ["数学"],
                "parent_phone": "13000000020",
            },
            headers=auth_headers,
        )
        s1_id = s1_resp.json()["id"]

        s2_resp = await async_client.post(
            "/api/students",
            json={
                "name": "作业学生乙",
                "grade": "初二",
                "subjects": ["数学"],
                "parent_phone": "13000000021",
            },
            headers=auth_headers,
        )
        s2_id = s2_resp.json()["id"]

        # 2. 布置作业给两名学生
        assign_resp = await async_client.post(
            "/api/assignments",
            json={
                "title": "集成测试作业",
                "subject": "数学",
                "content": "<p>完成练习册第5章</p>",
                "due_date": due_date,
                "student_ids": [s1_id, s2_id],
            },
            headers=auth_headers,
        )
        assert assign_resp.status_code == 201
        assignment_id = assign_resp.json()["id"]
        students_in_assignment = assign_resp.json()["students"]

        # 验证两名学生都是"未提交"状态
        assert len(students_in_assignment) == 2
        for sub in students_in_assignment:
            assert sub["status"] == "pending"

        # 3. 查看作业详情，确认未提交
        detail_resp = await async_client.get(
            f"/api/assignments/{assignment_id}", headers=auth_headers
        )
        assert detail_resp.status_code == 200
        detail_students = detail_resp.json()["students"]
        pending_count = sum(1 for s in detail_students if s["status"] == "pending")
        assert pending_count == 2

        # 4. 批改学生A（s1）的作业
        grade_resp = await async_client.post(
            f"/api/assignments/{assignment_id}/grade/{s1_id}",
            json={"score": 92, "comment": "思路清晰，继续保持"},
            headers=auth_headers,
        )
        assert grade_resp.status_code == 200
        assert grade_resp.json()["score"] == 92

        # 5. 再次查看详情：学生A状态变为 graded，学生B仍为 pending
        detail_resp2 = await async_client.get(
            f"/api/assignments/{assignment_id}", headers=auth_headers
        )
        students_final = detail_resp2.json()["students"]
        s1_sub = next(s for s in students_final if s["student_id"] == s1_id)
        s2_sub = next(s for s in students_final if s["student_id"] == s2_id)

        assert s1_sub["status"] == "graded"
        assert s1_sub["score"] == 92
        assert s2_sub["status"] == "pending"


class TestBillingWorkflow:
    """场景3: 收费流程（US-501/502/503/504/505）"""

    async def test_manual_billing_records_outstanding_workflow(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        db: AsyncSession,
    ):
        """
        完整收费流程：
        1. 设置数学单价 150 元/小时
        2. 为学生创建 3 条收费记录（共 3 节课，450 元）
        3. 查看汇总：应收 450 元
        4. 录入收款 200 元
        5. 查看欠费：250 元
        """
        from sqlalchemy import delete

        # 1. 设置数学单价
        price_resp = await async_client.put(
            "/api/billing/subject-prices/数学",
            json={"price_per_hour": 150.0},
            headers=auth_headers,
        )
        assert price_resp.status_code == 200
        assert float(price_resp.json()["price_per_hour"]) == 150.0

        # 2. 创建学生
        s_resp = await async_client.post(
            "/api/students",
            json={
                "name": "收费测试学生",
                "grade": "高二",
                "subjects": ["数学"],
                "parent_phone": "13000000030",
            },
            headers=auth_headers,
        )
        student_id = s_resp.json()["id"]

        # 清空该学生的收费记录
        await db.execute(
            delete(BillingRecord).where(BillingRecord.student_id == student_id)
        )
        await db.flush()

        # 3. 添加 3 条收费记录（每节课 150 元）
        record_ids = []
        for i in range(3):
            r_resp = await async_client.post(
                "/api/billing/records",
                json={
                    "student_id": student_id,
                    "amount": 150.0,
                    "notes": f"第{i+1}节数学课",
                },
                headers=auth_headers,
            )
            assert r_resp.status_code == 201
            record_ids.append(r_resp.json()["id"])

        # 4. 查看汇总：该学生应收 450
        summary_resp = await async_client.get(
            "/api/billing/summary", headers=auth_headers
        )
        assert summary_resp.status_code == 200
        summary = summary_resp.json()
        # 总应收中包含该学生的 450
        by_student = summary["by_student"]
        student_summary = next(
            (s for s in by_student if s["student_id"] == student_id), None
        )
        assert student_summary is not None
        assert float(student_summary["receivable"]) == 450.0
        assert float(student_summary["paid"]) == 0.0

        # 5. 录入收款 200 元（付给第一条记录）
        pay_resp = await async_client.patch(
            f"/api/billing/records/{record_ids[0]}/pay",
            json={
                "paid_amount": 200.0,
                "payment_method": "wechat",
            },
            headers=auth_headers,
        )
        assert pay_resp.status_code == 200

        # 6. 查看欠费：该学生应出现在欠费列表，按未结清记录统计欠费
        outstanding_resp = await async_client.get(
            "/api/billing/outstanding", headers=auth_headers
        )
        assert outstanding_resp.status_code == 200
        outstanding_list = outstanding_resp.json()

        student_outstanding = next(
            (o for o in outstanding_list if o["student_id"] == student_id), None
        )
        assert student_outstanding is not None
        # 应收 450，记录1已付清（200≥150），记录2+3 欠费 300
        assert float(student_outstanding["outstanding_amount"]) == 300.0


class TestTeacherV2AccountCourseFlow:
    """老师端 V2：学生账户驱动课程运营的目标集成链路"""

    async def test_complete_course_creates_charge_and_updates_account_balance(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """
        目标闭环：
        1. 设置课时单价并给学生预收充值
        2. 排一节 1.5 小时课程
        3. 完成课程
        4. 自动生成扣费记录，并更新学生账户余额

        该用例是评审后补充的 V2 契约测试，要求完成课程时真实生成扣费记录。
        """
        await async_client.put(
            "/api/billing/subject-prices/数学",
            json={"price_per_hour": 120.0},
            headers=auth_headers,
        )
        student_resp = await async_client.post(
            "/api/students",
            json={
                "name": "V2自动扣费学生",
                "grade": "初二",
                "subjects": ["数学"],
                "parent_phone": "13000000902",
            },
            headers=auth_headers,
        )
        assert student_resp.status_code == 201, student_resp.text
        student_id = student_resp.json()["id"]

        recharge_resp = await async_client.post(
            "/api/billing/recharge",
            json={
                "student_id": student_id,
                "paid_amount": 120.0,
                "payment_method": "wechat",
                "notes": "课前预收",
            },
            headers=auth_headers,
        )
        assert recharge_resp.status_code == 201, recharge_resp.text

        course_resp = await async_client.post(
            "/api/courses",
            json={
                "student_id": student_id,
                "subject": "数学",
                "start_time": "2026-05-11T09:00:00",
                "end_time": "2026-05-11T10:30:00",
            },
            headers=auth_headers,
        )
        assert course_resp.status_code == 201, course_resp.text
        course_id = course_resp.json()["id"]

        complete_resp = await async_client.patch(
            f"/api/courses/{course_id}/status",
            json={"status": "completed"},
            headers=auth_headers,
        )
        assert complete_resp.status_code == 200, complete_resp.text
        assert complete_resp.json()["status"] == "completed"

        account_resp = await async_client.get(
            f"/api/billing/students/{student_id}/account",
            headers=auth_headers,
        )
        assert account_resp.status_code == 200, account_resp.text
        account = account_resp.json()
        assert account["total_received"] == 120.0
        assert account["total_charged"] == 180.0
        assert account["current_balance"] == -60.0
        assert len(account["recent_charges"]) == 1
        assert account["recent_charges"][0]["course_id"] == course_id
        assert account["recent_charges"][0]["amount"] == 180.0

    async def test_completed_course_charge_is_idempotent_and_cancel_rolls_back(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """完成课程只扣一次；已扣费课程取消后应回滚自动扣费记录"""
        await async_client.put(
            "/api/billing/subject-prices/数学",
            json={"price_per_hour": 100.0},
            headers=auth_headers,
        )
        student_resp = await async_client.post(
            "/api/students",
            json={
                "name": "V2取消回滚学生",
                "grade": "初二",
                "subjects": ["数学"],
                "parent_phone": "13000000903",
            },
            headers=auth_headers,
        )
        assert student_resp.status_code == 201, student_resp.text
        student_id = student_resp.json()["id"]

        recharge_resp = await async_client.post(
            "/api/billing/recharge",
            json={
                "student_id": student_id,
                "paid_amount": 300.0,
                "payment_method": "wechat",
                "notes": "预收充值",
            },
            headers=auth_headers,
        )
        assert recharge_resp.status_code == 201, recharge_resp.text

        start_time = datetime.now().replace(hour=14, minute=0, second=0, microsecond=0)
        course_resp = await async_client.post(
            "/api/courses",
            json={
                "student_id": student_id,
                "subject": "数学",
                "start_time": start_time.isoformat(),
                "end_time": (start_time + timedelta(minutes=90)).isoformat(),
            },
            headers=auth_headers,
        )
        assert course_resp.status_code == 201, course_resp.text
        course_id = course_resp.json()["id"]

        for _ in range(2):
            complete_resp = await async_client.patch(
                f"/api/courses/{course_id}/status",
                json={"status": "completed"},
                headers=auth_headers,
            )
            assert complete_resp.status_code == 200, complete_resp.text

        account_after_complete_resp = await async_client.get(
            f"/api/billing/students/{student_id}/account",
            headers=auth_headers,
        )
        assert account_after_complete_resp.status_code == 200, account_after_complete_resp.text
        account_after_complete = account_after_complete_resp.json()
        assert account_after_complete["current_balance"] == 150.0
        assert account_after_complete["total_charged"] == 150.0
        course_charges = [
            charge
            for charge in account_after_complete["recent_charges"]
            if charge["course_id"] == course_id
        ]
        assert len(course_charges) == 1

        cancel_resp = await async_client.patch(
            f"/api/courses/{course_id}/status",
            json={"status": "cancelled"},
            headers=auth_headers,
        )
        assert cancel_resp.status_code == 200, cancel_resp.text

        account_after_cancel_resp = await async_client.get(
            f"/api/billing/students/{student_id}/account",
            headers=auth_headers,
        )
        assert account_after_cancel_resp.status_code == 200, account_after_cancel_resp.text
        account_after_cancel = account_after_cancel_resp.json()
        assert account_after_cancel["current_balance"] == 300.0
        assert account_after_cancel["total_charged"] == 0.0
        assert all(
            charge["course_id"] != course_id
            for charge in account_after_cancel["recent_charges"]
        )

    async def test_delete_completed_course_rolls_back_auto_charge(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """删除已自动扣费课程时，也应回滚对应扣费记录"""
        await async_client.put(
            "/api/billing/subject-prices/数学",
            json={"price_per_hour": 100.0},
            headers=auth_headers,
        )
        student_resp = await async_client.post(
            "/api/students",
            json={
                "name": "V2删除回滚学生",
                "grade": "初三",
                "subjects": ["数学"],
                "parent_phone": "13000000904",
            },
            headers=auth_headers,
        )
        assert student_resp.status_code == 201, student_resp.text
        student_id = student_resp.json()["id"]

        recharge_resp = await async_client.post(
            "/api/billing/recharge",
            json={
                "student_id": student_id,
                "paid_amount": 300.0,
                "payment_method": "wechat",
            },
            headers=auth_headers,
        )
        assert recharge_resp.status_code == 201, recharge_resp.text

        start_time = datetime.now().replace(hour=16, minute=0, second=0, microsecond=0)
        course_resp = await async_client.post(
            "/api/courses",
            json={
                "student_id": student_id,
                "subject": "数学",
                "start_time": start_time.isoformat(),
                "end_time": (start_time + timedelta(minutes=60)).isoformat(),
            },
            headers=auth_headers,
        )
        assert course_resp.status_code == 201, course_resp.text
        course_id = course_resp.json()["id"]

        complete_resp = await async_client.patch(
            f"/api/courses/{course_id}/status",
            json={"status": "completed"},
            headers=auth_headers,
        )
        assert complete_resp.status_code == 200, complete_resp.text

        delete_resp = await async_client.delete(
            f"/api/courses/{course_id}",
            headers=auth_headers,
        )
        assert delete_resp.status_code == 204, delete_resp.text

        account_resp = await async_client.get(
            f"/api/billing/students/{student_id}/account",
            headers=auth_headers,
        )
        assert account_resp.status_code == 200, account_resp.text
        account = account_resp.json()
        assert account["current_balance"] == 300.0
        assert account["total_charged"] == 0.0
        assert all(
            charge["course_id"] != course_id
            for charge in account["recent_charges"]
        )

    async def test_course_detail_v2_and_complete_create_feedback_assignment_and_charge(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """课程详情闭环：详情聚合、课后记录、可选作业、完成扣费一次完成"""
        await async_client.put(
            "/api/billing/subject-prices/英语",
            json={"price_per_hour": 120.0},
            headers=auth_headers,
        )
        student_resp = await async_client.post(
            "/api/students",
            json={
                "name": "V2课程详情学生",
                "grade": "初一",
                "subjects": ["英语"],
                "parent_phone": "13000000905",
            },
            headers=auth_headers,
        )
        assert student_resp.status_code == 201, student_resp.text
        student_id = student_resp.json()["id"]

        await async_client.post(
            "/api/billing/recharge",
            json={
                "student_id": student_id,
                "paid_amount": 300.0,
                "payment_method": "wechat",
            },
            headers=auth_headers,
        )

        course_resp = await async_client.post(
            "/api/courses",
            json={
                "student_id": student_id,
                "subject": "英语",
                "start_time": "2026-05-12T18:00:00",
                "end_time": "2026-05-12T19:30:00",
            },
            headers=auth_headers,
        )
        assert course_resp.status_code == 201, course_resp.text
        course_id = course_resp.json()["id"]

        detail_resp = await async_client.get(
            f"/api/courses/{course_id}/detail-v2",
            headers=auth_headers,
        )
        assert detail_resp.status_code == 200, detail_resp.text
        detail = detail_resp.json()
        assert detail["course"]["id"] == course_id
        assert detail["account"]["current_balance"] == 300.0
        assert detail["projected_charge"] == 180.0

        complete_resp = await async_client.post(
            f"/api/courses/{course_id}/complete",
            json={
                "performance": "课堂参与积极，能主动复述重点句型",
                "knowledge_mastery": "一般过去时掌握较稳定",
                "problems": "阅读长句速度偏慢",
                "next_plan": "下节课继续训练阅读分层理解",
                "rating": 4,
                "assignment": {
                    "enabled": True,
                    "title": "一般过去时巩固",
                    "content": "完成讲义第 3 页练习",
                    "due_date": "2026-05-14",
                },
            },
            headers=auth_headers,
        )
        assert complete_resp.status_code == 200, complete_resp.text
        completed = complete_resp.json()
        assert completed["course_status"] == "completed"
        assert completed["charge_amount"] == 180.0
        assert completed["balance_before"] == 300.0
        assert completed["balance_after"] == 120.0
        assert completed["feedback_id"] is not None
        assert completed["assignment_id"] is not None

        account_resp = await async_client.get(
            f"/api/billing/students/{student_id}/account",
            headers=auth_headers,
        )
        assert account_resp.status_code == 200, account_resp.text
        account = account_resp.json()
        assert account["current_balance"] == 120.0
        assert account["recent_charges"][0]["course_id"] == course_id

        feedback_resp = await async_client.get(
            f"/api/feedback/{completed['feedback_id']}",
            headers=auth_headers,
        )
        assert feedback_resp.status_code == 200, feedback_resp.text
        assert feedback_resp.json()["course_id"] == course_id

        assignment_resp = await async_client.get(
            f"/api/assignments/{completed['assignment_id']}",
            headers=auth_headers,
        )
        assert assignment_resp.status_code == 200, assignment_resp.text
        assert assignment_resp.json()["students"][0]["student_id"] == student_id

    async def test_leave_course_enters_makeup_pool_and_makeup_creates_new_course(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """学生/老师请假进入待补课池，安排补课后创建新课程并关闭原待补项"""
        student_resp = await async_client.post(
            "/api/students",
            json={
                "name": "V2待补课学生",
                "grade": "初二",
                "subjects": ["数学"],
                "parent_phone": "13000000906",
            },
            headers=auth_headers,
        )
        assert student_resp.status_code == 201, student_resp.text
        student_id = student_resp.json()["id"]

        course_resp = await async_client.post(
            "/api/courses",
            json={
                "student_id": student_id,
                "subject": "数学",
                "start_time": "2026-05-13T19:00:00",
                "end_time": "2026-05-13T20:30:00",
            },
            headers=auth_headers,
        )
        assert course_resp.status_code == 201, course_resp.text
        course_id = course_resp.json()["id"]

        leave_resp = await async_client.post(
            f"/api/courses/{course_id}/leave",
            json={
                "leave_type": "student",
                "reason": "学生临时生病",
                "turn_to_makeup": True,
            },
            headers=auth_headers,
        )
        assert leave_resp.status_code == 200, leave_resp.text
        assert leave_resp.json()["status"] == "student_leave_pending_makeup"

        pool_resp = await async_client.get("/api/courses/makeup-pool", headers=auth_headers)
        assert pool_resp.status_code == 200, pool_resp.text
        pool_items = pool_resp.json()["items"]
        assert any(item["id"] == course_id for item in pool_items)

        makeup_resp = await async_client.post(
            f"/api/courses/{course_id}/makeup",
            json={
                "start_time": "2026-05-15T19:00:00",
                "end_time": "2026-05-15T20:30:00",
                "notes": "补上 5 月 13 日请假课程",
            },
            headers=auth_headers,
        )
        assert makeup_resp.status_code == 201, makeup_resp.text
        makeup_course = makeup_resp.json()
        assert makeup_course["student_id"] == student_id
        assert makeup_course["status"] == "scheduled"

        pool_after_resp = await async_client.get("/api/courses/makeup-pool", headers=auth_headers)
        assert pool_after_resp.status_code == 200, pool_after_resp.text
        assert all(item["id"] != course_id for item in pool_after_resp.json()["items"])

        original_resp = await async_client.get(f"/api/courses/{course_id}", headers=auth_headers)
        assert original_resp.status_code == 200, original_resp.text
        assert original_resp.json()["status"] == "makeup_scheduled"


class TestStudentDetailWorkflow:
    """场景4: 学生档案完整性验证（US-105）"""

    async def test_student_stats_reflect_courses_and_billing(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        db: AsyncSession,
    ):
        """学生详情统计数据反映课程和收费情况（US-105 AC1）"""
        from sqlalchemy import delete

        # 创建学生
        s_resp = await async_client.post(
            "/api/students",
            json={
                "name": "详情统计学生",
                "grade": "初三",
                "subjects": ["化学"],
                "parent_phone": "13000000040",
            },
            headers=auth_headers,
        )
        student_id = s_resp.json()["id"]

        # 创建 2 节课（1 节 completed，1 节 scheduled）
        c1_resp = await async_client.post(
            "/api/courses",
            json={
                "student_id": student_id,
                "subject": "化学",
                "start_time": "2026-05-01T10:00:00",
                "end_time": "2026-05-01T11:00:00",
            },
            headers=auth_headers,
        )
        c1_id = c1_resp.json()["id"]

        await async_client.post(
            "/api/courses",
            json={
                "student_id": student_id,
                "subject": "化学",
                "start_time": "2026-05-08T10:00:00",
                "end_time": "2026-05-08T11:00:00",
            },
            headers=auth_headers,
        )

        # 完成第 1 节课
        await async_client.patch(
            f"/api/courses/{c1_id}/status",
            json={"status": "completed"},
            headers=auth_headers,
        )

        # 查看学生详情
        detail_resp = await async_client.get(
            f"/api/students/{student_id}", headers=auth_headers
        )
        assert detail_resp.status_code == 200
        stats = detail_resp.json()["stats"]
        assert stats["total_courses"] >= 2
        assert stats["completed_courses"] >= 1


class TestConflictDetectionEdgeCases:
    """冲突检测边界场景（US-202）"""

    async def test_conflict_response_contains_conflicting_course_info(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        db: AsyncSession,
    ):
        """冲突响应中包含冲突课程的详细信息（US-202 AC1）"""
        # 创建学生
        s_resp = await async_client.post(
            "/api/students",
            json={
                "name": "冲突边界学生",
                "grade": "高一",
                "subjects": ["英语"],
                "parent_phone": "13000000050",
            },
            headers=auth_headers,
        )
        student_id = s_resp.json()["id"]

        # 创建基准课程
        base_resp = await async_client.post(
            "/api/courses",
            json={
                "student_id": student_id,
                "subject": "英语",
                "start_time": "2026-06-01T14:00:00",
                "end_time": "2026-06-01T16:00:00",
            },
            headers=auth_headers,
        )
        assert base_resp.status_code == 201

        # 尝试在相同时间再创建一节课
        conflict_resp = await async_client.post(
            "/api/courses",
            json={
                "student_id": student_id,
                "subject": "数学",
                "start_time": "2026-06-01T15:00:00",
                "end_time": "2026-06-01T17:00:00",
            },
            headers=auth_headers,
        )
        assert conflict_resp.status_code == 409
        detail = conflict_resp.json()["detail"]
        assert "code" in detail
        assert detail["code"] == "COURSE_TIME_CONFLICT"
        # 冲突详情中应包含冲突课程信息
        assert "detail" in detail
        conflict_info = detail["detail"]
        assert "student_name" in conflict_info
        assert "start_time" in conflict_info


class TestSearchAndFilterWorkflow:
    """搜索和筛选集成测试（US-104）"""

    async def test_search_students_combined_workflow(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """搜索学生 - 创建后立即可通过姓名搜索到"""
        unique_name = "可搜索集成测试学生ZZZ999"

        # 创建
        create_resp = await async_client.post(
            "/api/students",
            json={
                "name": unique_name,
                "grade": "初一",
                "subjects": ["语文"],
                "parent_phone": "13000000060",
            },
            headers=auth_headers,
        )
        assert create_resp.status_code == 201

        # 通过姓名搜索
        search_resp = await async_client.get(
            f"/api/students?search={unique_name}", headers=auth_headers
        )
        assert search_resp.status_code == 200
        items = search_resp.json()["items"]
        assert len(items) >= 1
        found = next((s for s in items if s["name"] == unique_name), None)
        assert found is not None
        assert found["grade"] == "初一"
