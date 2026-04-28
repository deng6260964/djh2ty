from typing import Optional
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.database import get_db
from app.models.billing import SubjectPrice, BillingRecord
from app.models.course import Course
from app.models.student import Student
from app.schemas.billing import (
    SubjectPriceUpdate, SubjectPriceResponse,
    BillingRecordCreate, BillingRecordPayRequest, BillingRechargeRequest,
    BillingRecordResponse, BillingRecordListResponse,
    BillingSummaryResponse, StudentBillingSummary, OutstandingStudent,
)
from app.schemas.account import (
    AccountChargeRecord,
    AccountPaymentRecord,
    StudentAccountResponse,
)
from app.dependencies import get_admin_user, get_current_student
from app.models.user import User

router = APIRouter(prefix="/billing", tags=["收费管理"])


async def _get_student_balance_context(db: AsyncSession, student_id: int):
    records_result = await db.execute(
        select(BillingRecord).where(BillingRecord.student_id == student_id).order_by(BillingRecord.created_at.desc())
    )
    records = records_result.scalars().all()
    total_received = round(sum(float(record.paid_amount or 0) for record in records), 2)
    total_charged = round(sum(float(record.amount or 0) for record in records), 2)
    current_balance = round(total_received - total_charged, 2)
    return records, total_received, total_charged, current_balance


async def _build_student_account_response(
    db: AsyncSession,
    student: Student,
) -> StudentAccountResponse:
    records, total_received, total_charged, current_balance = await _get_student_balance_context(db, student.id)

    next_course_result = await db.execute(
        select(Course)
        .where(
            Course.student_id == student.id,
            Course.start_time > datetime.now(),
            Course.status == "scheduled",
        )
        .order_by(Course.start_time.asc())
        .limit(1)
    )
    next_course = next_course_result.scalar_one_or_none()

    main_subject = student.subjects[0] if student.subjects else None
    main_subject_hourly_rate = None
    if main_subject:
        price_result = await db.execute(
            select(SubjectPrice).where(SubjectPrice.subject == main_subject)
        )
        price = price_result.scalar_one_or_none()
        if price:
            main_subject_hourly_rate = float(price.price_per_hour)

    next_course_projected_charge = None
    if next_course:
        hourly_rate = float(next_course.hourly_rate or main_subject_hourly_rate or 0)
        next_course_projected_charge = round(hourly_rate * ((next_course.duration or 0) / 60), 2)

    estimated_lessons_left = 0.0
    if main_subject_hourly_rate and main_subject_hourly_rate > 0:
        estimated_lessons_left = round(current_balance / main_subject_hourly_rate, 1)

    recent_payments = []
    recent_charges = []
    course_cache: dict[int, Course | None] = {}
    for record in records:
        if float(record.paid_amount or 0) > 0 and len(recent_payments) < 5:
            recent_payments.append(
                AccountPaymentRecord(
                    record_id=record.id,
                    amount=float(record.paid_amount or 0),
                    paid_at=record.paid_at,
                    payment_method=record.payment_method,
                    notes=record.notes,
                )
            )
        if float(record.amount or 0) > 0 and len(recent_charges) < 5:
            subject = None
            if record.course_id:
                if record.course_id not in course_cache:
                    course_result = await db.execute(
                        select(Course).where(Course.id == record.course_id)
                    )
                    course_cache[record.course_id] = course_result.scalar_one_or_none()
                course = course_cache[record.course_id]
                if course:
                    subject = course.subject
            recent_charges.append(
                AccountChargeRecord(
                    record_id=record.id,
                    course_id=record.course_id,
                    subject=subject,
                    amount=float(record.amount or 0),
                    created_at=record.created_at,
                    notes=record.notes,
                )
            )

    return StudentAccountResponse(
        student_id=student.id,
        student_name=student.name,
        grade=student.grade,
        current_balance=current_balance,
        total_received=total_received,
        total_charged=total_charged,
        estimated_lessons_left=estimated_lessons_left,
        main_subject=main_subject,
        main_subject_hourly_rate=main_subject_hourly_rate,
        has_payment_alert=bool(
            next_course_projected_charge is not None and current_balance < next_course_projected_charge
        ),
        next_course_id=next_course.id if next_course else None,
        next_course_time=next_course.start_time if next_course else None,
        next_course_subject=next_course.subject if next_course else None,
        next_course_projected_charge=next_course_projected_charge,
        recent_payments=recent_payments,
        recent_charges=recent_charges,
    )


@router.get("/subject-prices", response_model=list[SubjectPriceResponse])
async def list_subject_prices(
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """科目单价列表"""
    result = await db.execute(
        select(SubjectPrice).order_by(SubjectPrice.subject)
    )
    prices = result.scalars().all()
    return [SubjectPriceResponse.model_validate(p) for p in prices]


@router.put("/subject-prices/{subject}", response_model=SubjectPriceResponse)
async def update_subject_price(
    subject: str,
    data: SubjectPriceUpdate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """更新科目单价（不存在则创建）"""
    result = await db.execute(
        select(SubjectPrice).where(SubjectPrice.subject == subject)
    )
    price = result.scalar_one_or_none()

    if price:
        price.price_per_hour = data.price_per_hour
    else:
        price = SubjectPrice(
            subject=subject,
            price_per_hour=data.price_per_hour,
        )
        db.add(price)

    await db.commit()
    await db.refresh(price)
    return SubjectPriceResponse.model_validate(price)


@router.get("/records", response_model=BillingRecordListResponse)
async def list_billing_records(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    student_id: Optional[int] = Query(None),
    record_status: Optional[str] = Query(None, alias="status"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """收费记录列表"""
    query = select(BillingRecord)
    conditions = []
    if student_id:
        conditions.append(BillingRecord.student_id == student_id)
    if record_status:
        conditions.append(BillingRecord.status == record_status)
    if start_date:
        conditions.append(BillingRecord.created_at >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        conditions.append(BillingRecord.created_at <= datetime.combine(end_date, datetime.max.time()))
    if conditions:
        query = query.where(and_(*conditions))

    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar_one()

    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(BillingRecord.created_at.desc()).offset(offset).limit(page_size)
    )
    records = result.scalars().all()

    # 批量获取学生姓名
    student_ids = list({r.student_id for r in records})
    student_map = {}
    if student_ids:
        s_result = await db.execute(
            select(Student).where(Student.id.in_(student_ids))
        )
        for s in s_result.scalars().all():
            student_map[s.id] = s.name

    items = []
    for r in records:
        br = BillingRecordResponse.model_validate(r)
        br.student_name = student_map.get(r.student_id, "")
        items.append(br)

    return BillingRecordListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.post("/records", response_model=BillingRecordResponse, status_code=status.HTTP_201_CREATED)
async def create_billing_record(
    data: BillingRecordCreate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """手动创建收费记录"""
    student_result = await db.execute(
        select(Student).where(Student.id == data.student_id)
    )
    student = student_result.scalar_one_or_none()
    if not student:
        raise HTTPException(
            status_code=404,
            detail={"code": "STUDENT_NOT_FOUND", "message": "学生不存在"},
        )

    record = BillingRecord(
        student_id=data.student_id,
        course_id=data.course_id,
        amount=data.amount,
        paid_amount=0,
        status="unpaid",
        notes=data.notes,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    response = BillingRecordResponse.model_validate(record)
    response.student_name = student.name
    return response


@router.patch("/records/{record_id}/pay", response_model=BillingRecordResponse)
async def pay_billing_record(
    record_id: int,
    data: BillingRecordPayRequest,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """记录收款"""
    result = await db.execute(
        select(BillingRecord).where(BillingRecord.id == record_id)
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(
            status_code=404,
            detail={"code": "RECORD_NOT_FOUND", "message": "收费记录不存在"},
        )

    record.paid_amount = data.paid_amount
    record.payment_method = data.payment_method
    record.paid_at = data.paid_at or datetime.utcnow()

    # 自动更新状态
    if float(record.paid_amount) >= float(record.amount):
        record.status = "paid"
    elif float(record.paid_amount) > 0:
        record.status = "partial"
    else:
        record.status = "unpaid"

    await db.commit()
    await db.refresh(record)

    student_result = await db.execute(
        select(Student).where(Student.id == record.student_id)
    )
    student = student_result.scalar_one_or_none()

    response = BillingRecordResponse.model_validate(record)
    response.student_name = student.name if student else ""
    return response


@router.post("/recharge", response_model=BillingRecordResponse, status_code=status.HTTP_201_CREATED)
async def recharge_student_balance(
    data: BillingRechargeRequest,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """预收充值，直接增加学生余额"""
    del current_user

    student_result = await db.execute(
        select(Student).where(Student.id == data.student_id)
    )
    student = student_result.scalar_one_or_none()
    if not student:
        raise HTTPException(
            status_code=404,
            detail={"code": "STUDENT_NOT_FOUND", "message": "学生不存在"},
        )

    record = BillingRecord(
        student_id=data.student_id,
        course_id=None,
        amount=0,
        paid_amount=data.paid_amount,
        status="paid",
        payment_method=data.payment_method,
        paid_at=data.paid_at or datetime.utcnow(),
        notes=data.notes,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    response = BillingRecordResponse.model_validate(record)
    response.student_name = student.name
    return response


@router.delete("/records/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_billing_record(
    record_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """删除收费记录"""
    result = await db.execute(
        select(BillingRecord).where(BillingRecord.id == record_id)
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(
            status_code=404,
            detail={"code": "RECORD_NOT_FOUND", "message": "收费记录不存在"},
        )
    await db.delete(record)
    await db.commit()


@router.get("/summary", response_model=BillingSummaryResponse)
async def get_billing_summary(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """收费汇总报表"""
    query = select(BillingRecord)
    conditions = []
    if start_date:
        conditions.append(BillingRecord.created_at >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        conditions.append(BillingRecord.created_at <= datetime.combine(end_date, datetime.max.time()))
    if conditions:
        query = query.where(and_(*conditions))

    result = await db.execute(query)
    all_records = result.scalars().all()

    total_receivable = sum(float(r.amount) for r in all_records)
    total_paid = sum(float(r.paid_amount) for r in all_records)
    total_outstanding = max(0, total_receivable - total_paid)

    # 按学生汇总
    student_ids = list({r.student_id for r in all_records})
    student_map = {}
    if student_ids:
        s_result = await db.execute(
            select(Student).where(Student.id.in_(student_ids))
        )
        for s in s_result.scalars().all():
            student_map[s.id] = s

    by_student_map: dict = {}
    for r in all_records:
        sid = r.student_id
        if sid not in by_student_map:
            s = student_map.get(sid)
            by_student_map[sid] = {
                "student_id": sid,
                "student_name": s.name if s else "",
                "receivable": 0.0,
                "paid": 0.0,
                "outstanding": 0.0,
            }
        by_student_map[sid]["receivable"] += float(r.amount)
        by_student_map[sid]["paid"] += float(r.paid_amount)

    by_student = []
    for item in by_student_map.values():
        item["outstanding"] = max(0, item["receivable"] - item["paid"])
        by_student.append(StudentBillingSummary(**item))

    # 按科目汇总（通过关联课程）
    by_subject: dict = {}
    for r in all_records:
        if r.course_id:
            course_result = await db.execute(
                select(Course).where(Course.id == r.course_id)
            )
            course = course_result.scalar_one_or_none()
            if course:
                subject = course.subject
                by_subject[subject] = by_subject.get(subject, 0.0) + float(r.amount)

    by_subject_list = [
        {"subject": k, "total": v} for k, v in sorted(by_subject.items())
    ]

    return BillingSummaryResponse(
        period={
            "start": str(start_date) if start_date else "",
            "end": str(end_date) if end_date else "",
        },
        total_receivable=total_receivable,
        total_paid=total_paid,
        total_outstanding=total_outstanding,
        by_student=by_student,
        by_subject=by_subject_list,
        monthly_trend=[],
    )


@router.get("/outstanding", response_model=list[OutstandingStudent])
async def get_outstanding_students(
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """欠费学生列表"""
    # 查询所有学生及其欠费情况
    result = await db.execute(
        select(
            Student.id,
            Student.name,
            Student.grade,
            func.coalesce(func.sum(BillingRecord.amount - BillingRecord.paid_amount), 0).label("outstanding_amount"),
            func.count(BillingRecord.id).label("unpaid_count"),
        ).join(
            BillingRecord, BillingRecord.student_id == Student.id
        ).where(
            BillingRecord.status.in_(["unpaid", "partial"])
        ).group_by(Student.id, Student.name, Student.grade)
        .having(func.sum(BillingRecord.amount - BillingRecord.paid_amount) > 0)
        .order_by(func.sum(BillingRecord.amount - BillingRecord.paid_amount).desc())
    )
    rows = result.all()

    return [
        OutstandingStudent(
            student_id=row.id,
            student_name=row.name,
            grade=row.grade,
            outstanding_amount=float(row.outstanding_amount),
            unpaid_count=row.unpaid_count,
        )
        for row in rows
    ]


@router.get("/students/{student_id}/account", response_model=StudentAccountResponse)
async def get_student_account(
    student_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """学生账户概览"""
    del current_user

    student_result = await db.execute(
        select(Student).where(Student.id == student_id, Student.is_active == True)
    )
    student = student_result.scalar_one_or_none()
    if not student:
        raise HTTPException(
            status_code=404,
            detail={"code": "STUDENT_NOT_FOUND", "message": "学生不存在"},
        )

    return await _build_student_account_response(db, student)


@router.get("/my/account", response_model=StudentAccountResponse)
async def get_my_student_account(
    db: AsyncSession = Depends(get_db),
    current_student: Student = Depends(get_current_student),
):
    """学生/家长端：当前学生账户余额与最近扣费，只读。"""
    return await _build_student_account_response(db, current_student)
