from datetime import datetime, date, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.database import get_db
from app.models.course import Course
from app.models.student import Student
from app.models.assignment import Assignment, AssignmentStudent
from app.models.billing import BillingRecord
from app.models.notification import Notification
from app.models.feedback import Feedback
from app.dependencies import get_admin_user
from app.models.user import User
from app.schemas.workbench import (
    WorkbenchAssignmentItem,
    WorkbenchCourseItem,
    WorkbenchPaymentAlertItem,
    WorkbenchPendingRecordItem,
    WorkbenchResponse,
    WorkbenchSummary,
)

router = APIRouter(prefix="/dashboard", tags=["仪表盘"])


async def _build_student_context(db: AsyncSession):
    students_result = await db.execute(
        select(Student).where(Student.is_active == True)
    )
    students = students_result.scalars().all()
    student_map = {student.id: student for student in students}

    records_result = await db.execute(select(BillingRecord))
    records = records_result.scalars().all()

    balance_map: dict[int, float] = {student.id: 0.0 for student in students}
    for record in records:
        paid_amount = float(record.paid_amount or 0)
        amount = float(record.amount or 0)
        balance_map[record.student_id] = balance_map.get(record.student_id, 0.0) + paid_amount - amount

    subject_price_result = await db.execute(select(BillingRecord.course_id))
    _ = subject_price_result  # suppress unused in case future extension reuses aggregate shape

    return student_map, balance_map


def _resolve_projected_charge(course: Course) -> float:
    hourly_rate = float(course.hourly_rate or 0)
    duration_hours = course.duration / 60 if course.duration else 0
    return round(hourly_rate * duration_hours, 2)


@router.get("/overview")
async def get_overview(
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """仪表盘总览数据"""
    today = date.today()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())

    month_start = datetime(today.year, today.month, 1)
    if today.month == 12:
        month_end = datetime(today.year + 1, 1, 1)
    else:
        month_end = datetime(today.year, today.month + 1, 1)

    # 今日课程
    today_courses_result = await db.execute(
        select(Course, Student.name.label("student_name")).join(
            Student, Course.student_id == Student.id
        ).where(
            Course.start_time >= today_start,
            Course.start_time <= today_end,
        ).order_by(Course.start_time)
    )
    today_courses = []
    for row in today_courses_result.all():
        course, student_name = row
        today_courses.append({
            "id": course.id,
            "student_name": student_name,
            "subject": course.subject,
            "start_time": course.start_time.strftime("%H:%M"),
            "end_time": course.end_time.strftime("%H:%M"),
            "status": course.status,
        })

    # 未来 7 天课程
    next_week = datetime.combine(today + timedelta(days=7), datetime.max.time())
    upcoming_result = await db.execute(
        select(Course, Student.name.label("student_name")).join(
            Student, Course.student_id == Student.id
        ).where(
            Course.start_time > today_end,
            Course.start_time <= next_week,
            Course.status == "scheduled",
        ).order_by(Course.start_time).limit(10)
    )
    upcoming_courses = []
    for row in upcoming_result.all():
        course, student_name = row
        upcoming_courses.append({
            "id": course.id,
            "student_name": student_name,
            "subject": course.subject,
            "start_time": course.start_time.isoformat(),
            "end_time": course.end_time.isoformat(),
            "status": course.status,
        })

    # 在读学生数
    active_students_result = await db.execute(
        select(func.count()).where(Student.is_active == True)
    )
    active_students = active_students_result.scalar_one()

    # 本月课程数
    month_courses_result = await db.execute(
        select(func.count()).where(
            Course.start_time >= month_start,
            Course.start_time < month_end,
        )
    )
    this_month_courses = month_courses_result.scalar_one()

    # 本月收入（已收款）
    month_income_result = await db.execute(
        select(func.coalesce(func.sum(BillingRecord.paid_amount), 0)).where(
            BillingRecord.paid_at >= month_start,
            BillingRecord.paid_at < month_end,
            BillingRecord.status.in_(["partial", "paid"]),
        )
    )
    this_month_income = float(month_income_result.scalar_one())

    # 待批改作业数
    pending_grading_result = await db.execute(
        select(func.count()).where(AssignmentStudent.status == "submitted")
    )
    pending_grading = pending_grading_result.scalar_one()

    # 欠费总额
    outstanding_result = await db.execute(
        select(
            func.coalesce(func.sum(BillingRecord.amount - BillingRecord.paid_amount), 0)
        ).where(BillingRecord.status.in_(["unpaid", "partial"]))
    )
    outstanding_fee = float(outstanding_result.scalar_one())

    # 未读通知数
    unread_notifications_result = await db.execute(
        select(func.count()).where(
            Notification.user_id == current_user.id,
            Notification.is_read == False,
        )
    )
    unread_notifications = unread_notifications_result.scalar_one()

    # 最近 5 条反馈
    recent_feedback_result = await db.execute(
        select(Feedback, Student.name.label("student_name")).join(
            Student, Feedback.student_id == Student.id
        ).order_by(Feedback.created_at.desc()).limit(5)
    )
    recent_feedback = []
    for row in recent_feedback_result.all():
        feedback, student_name = row
        recent_feedback.append({
            "id": feedback.id,
            "student_name": student_name,
            "performance": feedback.performance[:100] if feedback.performance else "",
            "rating": feedback.rating,
            "is_pushed": feedback.is_pushed,
            "created_at": feedback.created_at.isoformat(),
        })

    return {
        "today_courses": today_courses,
        "stats": {
            "active_students": active_students,
            "this_month_courses": this_month_courses,
            "this_month_income": this_month_income,
            "pending_grading": pending_grading,
            "outstanding_fee": outstanding_fee,
            "unread_notifications": unread_notifications,
        },
        "upcoming_courses": upcoming_courses,
        "recent_feedback": recent_feedback,
    }


@router.get("/workbench", response_model=WorkbenchResponse)
async def get_workbench(
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """老师工作台聚合数据"""
    del current_user

    today = date.today()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    now = datetime.now()

    student_map, balance_map = await _build_student_context(db)

    today_courses_result = await db.execute(
        select(Course).where(
            Course.start_time >= today_start,
            Course.start_time <= today_end,
        ).order_by(Course.start_time)
    )
    today_courses_raw = today_courses_result.scalars().all()

    today_courses = []
    for course in today_courses_raw:
        student = student_map.get(course.student_id)
        if not student:
            continue
        current_balance = round(balance_map.get(course.student_id, 0.0), 2)
        projected_charge = _resolve_projected_charge(course)
        today_courses.append(
            WorkbenchCourseItem(
                id=course.id,
                student_id=course.student_id,
                student_name=student.name,
                subject=course.subject,
                start_time=course.start_time,
                end_time=course.end_time,
                status=course.status,
                current_balance=current_balance,
                projected_charge=projected_charge,
                needs_payment=current_balance < projected_charge,
            )
        )

    pending_records_result = await db.execute(
        select(Course).where(
            and_(
                Course.end_time < now,
                Course.status == "scheduled",
            )
        ).order_by(Course.end_time.asc()).limit(10)
    )
    pending_records_raw = pending_records_result.scalars().all()

    pending_records = []
    for course in pending_records_raw:
        student = student_map.get(course.student_id)
        if not student:
            continue
        pending_records.append(
            WorkbenchPendingRecordItem(
                id=course.id,
                student_id=course.student_id,
                student_name=student.name,
                subject=course.subject,
                start_time=course.start_time,
                end_time=course.end_time,
                status=course.status,
                current_balance=round(balance_map.get(course.student_id, 0.0), 2),
                projected_charge=_resolve_projected_charge(course),
                needs_payment=round(balance_map.get(course.student_id, 0.0), 2) < _resolve_projected_charge(course),
            )
        )

    next_courses_result = await db.execute(
        select(Course).where(
            and_(
                Course.start_time > now,
                Course.status == "scheduled",
            )
        ).order_by(Course.start_time.asc())
    )
    next_courses_raw = next_courses_result.scalars().all()
    next_course_by_student: dict[int, Course] = {}
    for course in next_courses_raw:
        if course.student_id not in next_course_by_student:
            next_course_by_student[course.student_id] = course

    payment_alerts = []
    for student_id, course in next_course_by_student.items():
        student = student_map.get(student_id)
        if not student:
            continue
        current_balance = round(balance_map.get(student_id, 0.0), 2)
        projected_charge = _resolve_projected_charge(course)
        if current_balance >= projected_charge:
            continue
        payment_alerts.append(
            WorkbenchPaymentAlertItem(
                student_id=student_id,
                student_name=student.name,
                grade=student.grade,
                current_balance=current_balance,
                next_course_id=course.id,
                next_course_time=course.start_time,
                next_course_subject=course.subject,
                projected_charge=projected_charge,
                shortage_amount=round(projected_charge - current_balance, 2),
            )
        )

    assignment_result = await db.execute(
        select(AssignmentStudent, Assignment, Student.name.label("student_name"))
        .join(Assignment, AssignmentStudent.assignment_id == Assignment.id)
        .join(Student, AssignmentStudent.student_id == Student.id)
        .where(AssignmentStudent.status == "submitted")
        .order_by(AssignmentStudent.submitted_at.desc().nullslast(), Assignment.id.desc())
        .limit(10)
    )

    assignment_reviews = []
    for assignment_student, assignment, student_name in assignment_result.all():
        assignment_reviews.append(
            WorkbenchAssignmentItem(
                assignment_id=assignment.id,
                assignment_title=assignment.title,
                student_id=assignment_student.student_id,
                student_name=student_name,
                subject=assignment.subject,
                submitted_at=assignment_student.submitted_at,
                status=assignment_student.status,
            )
        )

    return WorkbenchResponse(
        today=today,
        summary=WorkbenchSummary(
            pending_record_count=len(pending_records),
            today_course_count=len(today_courses),
            payment_alert_count=len(payment_alerts),
            assignment_review_count=len(assignment_reviews),
        ),
        today_courses=today_courses,
        pending_records=pending_records,
        payment_alerts=payment_alerts,
        assignment_reviews=assignment_reviews,
    )
