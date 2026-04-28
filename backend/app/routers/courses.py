from typing import Optional, Dict, List
from datetime import datetime, date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.database import get_db
from app.models.course import Course
from app.models.student import Student
from app.models.assignment import Assignment, AssignmentStudent
from app.models.billing import SubjectPrice, BillingRecord
from app.schemas.course import (
    CourseCreate, CourseUpdate, CourseStatusUpdate,
    ConflictCheckRequest, ConflictCheckResponse, ConflictInfo,
    CourseResponse, CourseListResponse, CalendarCourseItem,
    CopyWeekPreviewRequest, CopyWeekPreviewResponse, CopyWeekPreviewItem,
    CopyWeekConfirmRequest, CopyWeekConfirmResponse, CopyWeekConfirmSkippedItem,
    CourseCompleteRequest, CourseCompleteResponse, CourseDetailV2Response,
    CourseLeaveRequest, CourseMakeupRequest, MakeupPoolResponse,
)
from app.models.feedback import Feedback
from app.dependencies import get_admin_user, get_current_student
from app.models.user import User

router = APIRouter(prefix="/courses", tags=["课程管理"])

AUTO_CHARGE_NOTE = "课程完成自动扣费"
NON_CONFLICT_STATUSES = {
    "cancelled",
    "student_leave_pending_makeup",
    "teacher_leave_pending_makeup",
    "makeup_scheduled",
}


async def _build_balance_map(db: AsyncSession) -> dict[int, float]:
    result = await db.execute(select(BillingRecord))
    records = result.scalars().all()
    balance_map: dict[int, float] = {}
    for record in records:
        balance_map[record.student_id] = balance_map.get(record.student_id, 0.0) + float(record.paid_amount or 0) - float(record.amount or 0)
    return balance_map


def _project_charge(course: Course) -> float:
    hourly_rate = float(course.hourly_rate or 0)
    return round(hourly_rate * ((course.duration or 0) / 60), 2)


async def _ensure_course_auto_charge(db: AsyncSession, course: Course) -> None:
    existing_result = await db.execute(
        select(BillingRecord).where(
            BillingRecord.course_id == course.id,
            BillingRecord.student_id == course.student_id,
            BillingRecord.notes == AUTO_CHARGE_NOTE,
        )
    )
    if existing_result.scalar_one_or_none():
        return

    hourly_rate = float(course.hourly_rate or 0)
    if hourly_rate <= 0:
        price_result = await db.execute(
            select(SubjectPrice).where(SubjectPrice.subject == course.subject)
        )
        price = price_result.scalar_one_or_none()
        if price:
            hourly_rate = float(price.price_per_hour)

    charge_amount = round(hourly_rate * ((course.duration or 0) / 60), 2)
    if charge_amount <= 0:
        return

    db.add(
        BillingRecord(
            student_id=course.student_id,
            course_id=course.id,
            amount=charge_amount,
            paid_amount=0,
            status="paid",
            notes=AUTO_CHARGE_NOTE,
        )
    )


async def _rollback_course_auto_charge(db: AsyncSession, course: Course) -> None:
    result = await db.execute(
        select(BillingRecord).where(
            BillingRecord.course_id == course.id,
            BillingRecord.student_id == course.student_id,
            BillingRecord.notes == AUTO_CHARGE_NOTE,
        )
    )
    for record in result.scalars().all():
        await db.delete(record)


async def _get_student_balance(db: AsyncSession, student_id: int) -> float:
    result = await db.execute(
        select(BillingRecord).where(BillingRecord.student_id == student_id)
    )
    records = result.scalars().all()
    return round(
        sum(float(record.paid_amount or 0) - float(record.amount or 0) for record in records),
        2,
    )


def _copy_course_time(course: Course, source_week_start: date, target_week_start: date) -> tuple[datetime, datetime]:
    source_week_start_dt = datetime.combine(source_week_start, datetime.min.time())
    target_week_start_dt = datetime.combine(target_week_start, datetime.min.time())
    return (
        target_week_start_dt + (course.start_time - source_week_start_dt),
        target_week_start_dt + (course.end_time - source_week_start_dt),
    )


async def _get_week_source_courses(
    db: AsyncSession,
    source_week_start: date,
    selected_course_ids: Optional[list[int]] = None,
):
    source_start_dt = datetime.combine(source_week_start, datetime.min.time())
    source_end_dt = source_start_dt + timedelta(days=7)
    query = (
        select(Course, Student.name.label("student_name"))
        .join(Student, Course.student_id == Student.id)
        .where(
            Course.start_time >= source_start_dt,
            Course.start_time < source_end_dt,
            Course.status != "cancelled",
        )
        .order_by(Course.start_time.asc())
    )
    if selected_course_ids is not None:
        if not selected_course_ids:
            return []
        query = query.where(Course.id.in_(selected_course_ids))
    result = await db.execute(query)
    return result.all()


async def _build_copy_week_preview(
    db: AsyncSession,
    source_week_start: date,
    target_week_start: date,
    selected_course_ids: Optional[list[int]] = None,
):
    rows = await _get_week_source_courses(db, source_week_start, selected_course_ids)
    balance_map = await _build_balance_map(db)
    items: list[CopyWeekPreviewItem] = []

    for course, student_name in rows:
        target_start_time, target_end_time = _copy_course_time(course, source_week_start, target_week_start)
        conflict = await check_time_conflict(db, target_start_time, target_end_time)
        projected_charge = _project_charge(course)
        current_balance = round(balance_map.get(course.student_id, 0.0), 2)
        needs_payment = current_balance < projected_charge
        has_conflict = conflict is not None

        if has_conflict:
            item_status = "conflict"
        elif needs_payment:
            item_status = "needs_payment"
        else:
            item_status = "copyable"

        items.append(
            CopyWeekPreviewItem(
                source_course_id=course.id,
                student_id=course.student_id,
                student_name=student_name,
                subject=course.subject,
                source_start_time=course.start_time,
                source_end_time=course.end_time,
                target_start_time=target_start_time,
                target_end_time=target_end_time,
                duration=course.duration,
                projected_charge=projected_charge,
                current_balance=current_balance,
                needs_payment=needs_payment,
                has_conflict=has_conflict,
                status=item_status,
                conflict=ConflictInfo(**conflict) if conflict else None,
            )
        )

    return items


async def check_time_conflict(
    db: AsyncSession,
    start_time: datetime,
    end_time: datetime,
    exclude_id: Optional[int] = None,
) -> Optional[dict]:
    """检查课程时间冲突，返回冲突课程信息或 None"""
    query = select(Course, Student.name.label("student_name")).join(
        Student, Course.student_id == Student.id
    ).where(
        Course.status.notin_(NON_CONFLICT_STATUSES),
        Course.start_time < end_time,
        Course.end_time > start_time,
    )
    if exclude_id:
        query = query.where(Course.id != exclude_id)

    result = await db.execute(query)
    row = result.first()
    if row:
        course, student_name = row
        return {
            "course_id": course.id,
            "student_name": student_name,
            "start_time": course.start_time.isoformat(),
            "end_time": course.end_time.isoformat(),
        }
    return None


@router.get("/calendar")
async def get_calendar(
    year: int = Query(...),
    month: int = Query(..., ge=1, le=12),
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, List[CalendarCourseItem]]:
    """日历视图：返回按日期分组的课程"""
    # 计算月份范围
    if month == 12:
        next_year, next_month = year + 1, 1
    else:
        next_year, next_month = year, month + 1

    start_dt = datetime(year, month, 1)
    end_dt = datetime(next_year, next_month, 1)

    result = await db.execute(
        select(Course, Student.name.label("student_name")).join(
            Student, Course.student_id == Student.id
        ).where(
            Course.start_time >= start_dt,
            Course.start_time < end_dt,
        ).order_by(Course.start_time)
    )
    rows = result.all()

    calendar: Dict[str, List[CalendarCourseItem]] = {}
    for row in rows:
        course, student_name = row
        date_key = course.start_time.strftime("%Y-%m-%d")
        if date_key not in calendar:
            calendar[date_key] = []
        calendar[date_key].append(
            CalendarCourseItem(
                id=course.id,
                student_name=student_name,
                student_id=course.student_id,
                subject=course.subject,
                start_time=course.start_time.strftime("%H:%M"),
                end_time=course.end_time.strftime("%H:%M"),
                status=course.status,
            )
        )

    return calendar


@router.get("/week")
async def get_week_courses(
    week_start: date = Query(...),
    student_id: Optional[int] = Query(None),
    subject: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """老师端 7 天周视图课程"""
    del current_user

    week_start_dt = datetime.combine(week_start, datetime.min.time())
    week_end_dt = week_start_dt + timedelta(days=7)

    query = (
        select(Course, Student.name.label("student_name"))
        .join(Student, Course.student_id == Student.id)
        .where(
            Course.start_time >= week_start_dt,
            Course.start_time < week_end_dt,
        )
    )
    if student_id:
        query = query.where(Course.student_id == student_id)
    if subject:
        query = query.where(Course.subject == subject)
    if status_filter:
        query = query.where(Course.status == status_filter)

    result = await db.execute(query.order_by(Course.start_time.asc()))
    rows = result.all()
    balance_map = await _build_balance_map(db)

    items = []
    for course, student_name in rows:
        current_balance = round(balance_map.get(course.student_id, 0.0), 2)
        projected_charge = _project_charge(course)
        items.append(
            {
                "id": course.id,
                "student_id": course.student_id,
                "student_name": student_name,
                "subject": course.subject,
                "start_time": course.start_time.isoformat(),
                "end_time": course.end_time.isoformat(),
                "duration": course.duration,
                "status": course.status,
                "hourly_rate": float(course.hourly_rate or 0),
                "projected_charge": projected_charge,
                "current_balance": current_balance,
                "needs_payment": current_balance < projected_charge,
                "is_weekend": course.start_time.weekday() >= 5,
            }
        )

    return {
        "week_start": week_start.isoformat(),
        "week_end": (week_start + timedelta(days=6)).isoformat(),
        "items": items,
    }


@router.post("/copy-week-preview", response_model=CopyWeekPreviewResponse)
async def copy_week_preview(
    data: CopyWeekPreviewRequest,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """复制上一周课程预览"""
    del current_user

    items = await _build_copy_week_preview(db, data.source_week_start, data.target_week_start)
    return CopyWeekPreviewResponse(
        source_week_start=data.source_week_start,
        target_week_start=data.target_week_start,
        items=items,
        total_count=len(items),
        copyable_count=sum(1 for item in items if not item.has_conflict),
        conflict_count=sum(1 for item in items if item.has_conflict),
        needs_payment_count=sum(1 for item in items if item.needs_payment),
    )


@router.post("/copy-week-confirm", response_model=CopyWeekConfirmResponse)
async def copy_week_confirm(
    data: CopyWeekConfirmRequest,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """确认复制上一周课程"""
    del current_user

    preview_items = await _build_copy_week_preview(
        db,
        data.source_week_start,
        data.target_week_start,
        data.selected_course_ids,
    )
    selected_rows = await _get_week_source_courses(
        db,
        data.source_week_start,
        data.selected_course_ids,
    )
    preview_map = {item.source_course_id: item for item in preview_items}
    created_course_ids: list[int] = []
    skipped_items: list[CopyWeekConfirmSkippedItem] = []

    for course, _student_name in selected_rows:
        preview_item = preview_map.get(course.id)
        if not preview_item:
            continue
        if preview_item.has_conflict:
            skipped_items.append(
                CopyWeekConfirmSkippedItem(
                    source_course_id=course.id,
                    reason="conflict",
                    conflict=preview_item.conflict,
                )
            )
            continue

        copied_course = Course(
            student_id=course.student_id,
            subject=course.subject,
            start_time=preview_item.target_start_time,
            end_time=preview_item.target_end_time,
            duration=course.duration,
            location=course.location,
            notes=course.notes,
            hourly_rate=course.hourly_rate,
            status="scheduled",
        )
        db.add(copied_course)
        await db.flush()
        created_course_ids.append(copied_course.id)

    await db.commit()

    return CopyWeekConfirmResponse(
        created_count=len(created_course_ids),
        skipped_count=len(skipped_items),
        created_course_ids=created_course_ids,
        skipped_items=skipped_items,
    )


@router.post("/check-conflict", response_model=ConflictCheckResponse)
async def check_conflict(
    data: ConflictCheckRequest,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """冲突检测（不创建课程）"""
    conflict = await check_time_conflict(
        db, data.start_time, data.end_time, data.exclude_id
    )
    if conflict:
        return ConflictCheckResponse(
            has_conflict=True,
            conflict=ConflictInfo(**conflict),
        )
    return ConflictCheckResponse(has_conflict=False)


@router.get("/my", response_model=CourseListResponse)
async def get_my_courses(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_student=Depends(get_current_student),
):
    """小程序/学生端：当前学生的课程"""
    query = select(Course).where(Course.student_id == current_student.id)
    if status_filter:
        query = query.where(Course.status == status_filter)
    if start_date:
        query = query.where(Course.start_time >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.where(Course.start_time < datetime.combine(end_date, datetime.max.time()))

    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar_one()

    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(Course.start_time.desc()).offset(offset).limit(page_size)
    )
    courses = result.scalars().all()

    items = []
    for c in courses:
        cr = CourseResponse.model_validate(c)
        cr.student_name = current_student.name
        items.append(cr)

    return CourseListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.get("", response_model=CourseListResponse)
async def list_courses(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    student_id: Optional[int] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """课程列表"""
    query = select(Course)
    conditions = []
    if start_date:
        conditions.append(Course.start_time >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        conditions.append(Course.start_time < datetime.combine(end_date, datetime.max.time()))
    if student_id:
        conditions.append(Course.student_id == student_id)
    if status_filter:
        conditions.append(Course.status == status_filter)
    if conditions:
        query = query.where(and_(*conditions))

    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar_one()

    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(Course.start_time.desc()).offset(offset).limit(page_size)
    )
    courses = result.scalars().all()

    # 批量获取学生姓名
    student_ids = list({c.student_id for c in courses})
    student_map = {}
    if student_ids:
        s_result = await db.execute(
            select(Student).where(Student.id.in_(student_ids))
        )
        for s in s_result.scalars().all():
            student_map[s.id] = s.name

    items = []
    for c in courses:
        cr = CourseResponse.model_validate(c)
        cr.student_name = student_map.get(c.student_id, "")
        items.append(cr)

    return CourseListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.post("", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
async def create_course(
    data: CourseCreate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """创建课程（含冲突检测）"""
    # 验证学生存在
    student_result = await db.execute(
        select(Student).where(Student.id == data.student_id, Student.is_active == True)
    )
    student = student_result.scalar_one_or_none()
    if not student:
        raise HTTPException(
            status_code=404,
            detail={"code": "STUDENT_NOT_FOUND", "message": "学生不存在"},
        )

    # 冲突检测
    conflict = await check_time_conflict(db, data.start_time, data.end_time)
    if conflict:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "COURSE_TIME_CONFLICT",
                "message": "该时间段已有其他课程安排",
                "detail": conflict,
            },
        )

    # 计算时长（分钟）
    duration = int((data.end_time - data.start_time).total_seconds() / 60)

    # 查询科目单价
    hourly_rate = data.hourly_rate
    if not hourly_rate:
        price_result = await db.execute(
            select(SubjectPrice).where(SubjectPrice.subject == data.subject)
        )
        price = price_result.scalar_one_or_none()
        if price:
            hourly_rate = float(price.price_per_hour)

    course = Course(
        student_id=data.student_id,
        subject=data.subject,
        start_time=data.start_time,
        end_time=data.end_time,
        duration=duration,
        location=data.location,
        notes=data.notes,
        hourly_rate=hourly_rate,
        status="scheduled",
    )
    db.add(course)
    await db.commit()
    await db.refresh(course)

    response = CourseResponse.model_validate(course)
    response.student_name = student.name
    return response


@router.get("/makeup-pool", response_model=MakeupPoolResponse)
async def get_makeup_pool(
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """待补课池：学生/老师请假后等待重新安排的课程"""
    del current_user
    result = await db.execute(
        select(Course, Student.name.label("student_name"))
        .join(Student, Course.student_id == Student.id)
        .where(Course.status.in_(["student_leave_pending_makeup", "teacher_leave_pending_makeup"]))
        .order_by(Course.start_time.asc())
    )
    rows = result.all()
    items = []
    for course, student_name in rows:
        response = CourseResponse.model_validate(course)
        response.student_name = student_name
        items.append(response)
    return MakeupPoolResponse(items=items, total=len(items))


@router.get("/{course_id}/detail-v2", response_model=CourseDetailV2Response)
async def get_course_detail_v2(
    course_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """老师端 V2 课程详情：课程、账户、最近反馈和作业摘要"""
    del current_user

    result = await db.execute(
        select(Course, Student).join(
            Student, Course.student_id == Student.id
        ).where(Course.id == course_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(
            status_code=404,
            detail={"code": "COURSE_NOT_FOUND", "message": "课程不存在"},
        )
    course, student = row

    course_response = CourseResponse.model_validate(course)
    course_response.student_name = student.name
    current_balance = await _get_student_balance(db, student.id)
    projected_charge = _project_charge(course)

    feedback_result = await db.execute(
        select(Feedback)
        .where(Feedback.student_id == student.id)
        .order_by(Feedback.created_at.desc())
        .limit(3)
    )
    recent_feedback = [
        {
            "id": item.id,
            "course_id": item.course_id,
            "performance": item.performance,
            "problems": item.problems,
            "next_plan": item.next_plan,
            "rating": item.rating,
            "created_at": item.created_at,
        }
        for item in feedback_result.scalars().all()
    ]

    assignment_result = await db.execute(
        select(Assignment, AssignmentStudent)
        .join(AssignmentStudent, AssignmentStudent.assignment_id == Assignment.id)
        .where(AssignmentStudent.student_id == student.id)
        .order_by(Assignment.created_at.desc())
        .limit(3)
    )
    recent_assignments = [
        {
            "id": assignment.id,
            "title": assignment.title,
            "subject": assignment.subject,
            "due_date": assignment.due_date,
            "status": assignment_student.status,
            "score": assignment_student.score,
        }
        for assignment, assignment_student in assignment_result.all()
    ]

    return CourseDetailV2Response(
        course=course_response,
        student={
            "id": student.id,
            "name": student.name,
            "grade": student.grade,
            "subjects": student.subjects,
            "parent_name": student.parent_name,
            "parent_phone": student.parent_phone,
        },
        account={
            "current_balance": current_balance,
            "projected_charge": projected_charge,
            "needs_payment": current_balance < projected_charge,
        },
        projected_charge=projected_charge,
        recent_feedback=recent_feedback,
        recent_assignments=recent_assignments,
    )


@router.post("/{course_id}/complete", response_model=CourseCompleteResponse)
async def complete_course_v2(
    course_id: int,
    data: CourseCompleteRequest,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """保存课后记录并完成课程，可选同步布置作业和自动扣费"""
    del current_user

    if not data.performance.strip():
        raise HTTPException(
            status_code=422,
            detail={"code": "PERFORMANCE_REQUIRED", "message": "请填写课后记录"},
        )

    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(
            status_code=404,
            detail={"code": "COURSE_NOT_FOUND", "message": "课程不存在"},
        )

    balance_before = await _get_student_balance(db, course.student_id)

    feedback = Feedback(
        course_id=course.id,
        student_id=course.student_id,
        performance=data.performance,
        knowledge_mastery=data.knowledge_mastery,
        problems=data.problems,
        next_plan=data.next_plan,
        rating=data.rating,
    )
    db.add(feedback)
    await db.flush()

    assignment_id = None
    if data.assignment and data.assignment.enabled:
        if not data.assignment.title or not data.assignment.content or not data.assignment.due_date:
            raise HTTPException(
                status_code=422,
                detail={"code": "ASSIGNMENT_REQUIRED", "message": "请填写作业标题、内容和截止日期"},
            )
        assignment = Assignment(
            title=data.assignment.title,
            content=data.assignment.content,
            subject=course.subject,
            due_date=data.assignment.due_date,
        )
        db.add(assignment)
        await db.flush()
        db.add(
            AssignmentStudent(
                assignment_id=assignment.id,
                student_id=course.student_id,
                status="pending",
            )
        )
        assignment_id = assignment.id

    course.status = "completed"
    await _ensure_course_auto_charge(db, course)
    charge_amount = _project_charge(course)
    await db.commit()
    await db.refresh(course)

    balance_after = await _get_student_balance(db, course.student_id)

    return CourseCompleteResponse(
        course_status=course.status,
        charge_amount=charge_amount,
        balance_before=balance_before,
        balance_after=balance_after,
        payment_alert_triggered=balance_after < 0,
        feedback_id=feedback.id,
        assignment_id=assignment_id,
    )


@router.post("/{course_id}/leave", response_model=CourseResponse)
async def mark_course_leave(
    course_id: int,
    data: CourseLeaveRequest,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """标记学生/老师请假，默认转入待补课池"""
    del current_user
    if data.leave_type not in ("student", "teacher"):
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_LEAVE_TYPE", "message": "请假类型必须是 student 或 teacher"},
        )

    result = await db.execute(
        select(Course, Student.name.label("student_name")).join(
            Student, Course.student_id == Student.id
        ).where(Course.id == course_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(
            status_code=404,
            detail={"code": "COURSE_NOT_FOUND", "message": "课程不存在"},
        )
    course, student_name = row
    if course.status == "completed":
        await _rollback_course_auto_charge(db, course)

    if data.turn_to_makeup:
        course.status = f"{data.leave_type}_leave_pending_makeup"
    else:
        course.status = "cancelled"

    leave_label = "学生请假" if data.leave_type == "student" else "老师请假"
    note = f"{leave_label}"
    if data.reason:
        note += f"：{data.reason}"
    course.notes = f"{course.notes or ''}\n{note}".strip()

    await db.commit()
    await db.refresh(course)
    response = CourseResponse.model_validate(course)
    response.student_name = student_name
    return response


@router.post("/{course_id}/makeup", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
async def schedule_makeup_course(
    course_id: int,
    data: CourseMakeupRequest,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """为待补课池中的课程安排补课"""
    del current_user

    result = await db.execute(
        select(Course, Student.name.label("student_name")).join(
            Student, Course.student_id == Student.id
        ).where(Course.id == course_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(
            status_code=404,
            detail={"code": "COURSE_NOT_FOUND", "message": "课程不存在"},
        )
    course, student_name = row
    if course.status not in ("student_leave_pending_makeup", "teacher_leave_pending_makeup"):
        raise HTTPException(
            status_code=400,
            detail={"code": "COURSE_NOT_IN_MAKEUP_POOL", "message": "课程不在待补课池中"},
        )

    conflict = await check_time_conflict(db, data.start_time, data.end_time, exclude_id=course.id)
    if conflict:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "COURSE_TIME_CONFLICT",
                "message": "该时间段已有其他课程安排",
                "detail": conflict,
            },
        )

    duration = int((data.end_time - data.start_time).total_seconds() / 60)
    makeup_course = Course(
        student_id=course.student_id,
        subject=course.subject,
        start_time=data.start_time,
        end_time=data.end_time,
        duration=duration,
        status="scheduled",
        location=course.location,
        hourly_rate=course.hourly_rate,
        notes=data.notes or f"补课，来源课程 #{course.id}",
    )
    db.add(makeup_course)
    course.status = "makeup_scheduled"
    course.notes = f"{course.notes or ''}\n已安排补课 #{makeup_course.id}".strip()
    await db.commit()
    await db.refresh(makeup_course)
    response = CourseResponse.model_validate(makeup_course)
    response.student_name = student_name
    return response


@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(
    course_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """课程详情"""
    result = await db.execute(
        select(Course, Student.name.label("student_name")).join(
            Student, Course.student_id == Student.id
        ).where(Course.id == course_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(
            status_code=404,
            detail={"code": "COURSE_NOT_FOUND", "message": "课程不存在"},
        )
    course, student_name = row
    response = CourseResponse.model_validate(course)
    response.student_name = student_name
    return response


@router.put("/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: int,
    data: CourseUpdate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """更新课程"""
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(
            status_code=404,
            detail={"code": "COURSE_NOT_FOUND", "message": "课程不存在"},
        )

    update_data = data.model_dump(exclude_unset=True)

    # 若修改时间，检测冲突
    new_start = update_data.get("start_time", course.start_time)
    new_end = update_data.get("end_time", course.end_time)
    if "start_time" in update_data or "end_time" in update_data:
        if new_end <= new_start:
            raise HTTPException(status_code=400, detail={"code": "INVALID_TIME", "message": "结束时间必须晚于开始时间"})
        conflict = await check_time_conflict(db, new_start, new_end, exclude_id=course_id)
        if conflict:
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "COURSE_TIME_CONFLICT",
                    "message": "该时间段已有其他课程安排",
                    "detail": conflict,
                },
            )
        update_data["duration"] = int((new_end - new_start).total_seconds() / 60)

    for key, value in update_data.items():
        setattr(course, key, value)

    await db.commit()
    await db.refresh(course)

    # 获取学生名
    s_result = await db.execute(select(Student).where(Student.id == course.student_id))
    student = s_result.scalar_one_or_none()

    response = CourseResponse.model_validate(course)
    response.student_name = student.name if student else ""
    return response


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course(
    course_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """删除课程"""
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(
            status_code=404,
            detail={"code": "COURSE_NOT_FOUND", "message": "课程不存在"},
        )
    await _rollback_course_auto_charge(db, course)
    await db.delete(course)
    await db.commit()


@router.patch("/{course_id}/status", response_model=CourseResponse)
async def update_course_status(
    course_id: int,
    data: CourseStatusUpdate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """更新课程状态"""
    if data.status not in ("scheduled", "completed", "cancelled"):
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_STATUS", "message": "无效的课程状态"},
        )

    result = await db.execute(
        select(Course, Student.name.label("student_name")).join(
            Student, Course.student_id == Student.id
        ).where(Course.id == course_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(
            status_code=404,
            detail={"code": "COURSE_NOT_FOUND", "message": "课程不存在"},
        )
    course, student_name = row
    old_status = course.status
    course.status = data.status

    if data.status == "completed":
        await _ensure_course_auto_charge(db, course)
    elif data.status == "cancelled" and old_status == "completed":
        await _rollback_course_auto_charge(db, course)

    await db.commit()
    await db.refresh(course)

    response = CourseResponse.model_validate(course)
    response.student_name = student_name
    return response
