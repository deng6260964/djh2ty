from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_

from app.database import get_db
from app.models.student import Student
from app.models.course import Course
from app.models.assignment import AssignmentStudent
from app.models.billing import BillingRecord
from app.schemas.student import (
    StudentCreate, StudentUpdate, StudentResponse,
    StudentDetailResponse, StudentListResponse, StudentStats
)
from app.schemas.course import CourseListResponse, CourseResponse
from app.dependencies import get_admin_user, get_current_user
from app.models.user import User
from app.utils.auth import get_password_hash

router = APIRouter(prefix="/students", tags=["学生管理"])


@router.get("", response_model=StudentListResponse)
async def list_students(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    subject: Optional[str] = Query(None),
    grade: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """学生列表（管理端，支持搜索/过滤/分页）"""
    query = select(Student)

    conditions = []
    if search:
        conditions.append(Student.name.ilike(f"%{search}%"))
    if subject:
        conditions.append(Student.subjects.any(subject))
    if grade:
        conditions.append(Student.grade == grade)
    if is_active is not None:
        conditions.append(Student.is_active == is_active)

    if conditions:
        query = query.where(and_(*conditions))

    # 计算总数
    count_result = await db.execute(
        select(func.count()).select_from(
            query.subquery()
        )
    )
    total = count_result.scalar_one()

    # 分页查询
    offset = (page - 1) * page_size
    query = query.order_by(Student.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(query)
    students = result.scalars().all()

    pages = (total + page_size - 1) // page_size

    # 批量获取关联 User 的 username
    user_ids = [s.user_id for s in students if s.user_id]
    user_map = {}
    if user_ids:
        u_result = await db.execute(
            select(User).where(User.id.in_(user_ids))
        )
        for u in u_result.scalars().all():
            user_map[u.id] = u.username

    items = []
    for s in students:
        sr = StudentResponse.model_validate(s)
        if s.user_id and s.user_id in user_map:
            sr.username = user_map[s.user_id]
        items.append(sr)

    return StudentListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.post("", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
async def create_student(
    data: StudentCreate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """创建学生"""
    user_id = None
    username = None

    # 当提供 username + password 时，创建关联的 User 账号
    if data.username and data.password:
        # 检查用户名唯一性
        existing = await db.execute(
            select(User).where(User.username == data.username)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "USERNAME_EXISTS", "message": "用户名已存在"},
            )
        user = User(
            username=data.username,
            hashed_password=get_password_hash(data.password),
            role="student",
            display_name=data.name,
            is_active=True,
        )
        db.add(user)
        await db.flush()
        user_id = user.id
        username = data.username

    student = Student(
        name=data.name,
        grade=data.grade,
        subjects=data.subjects,
        parent_name=data.parent_name,
        parent_phone=data.parent_phone,
        school=data.school,
        notes=data.notes,
        user_id=user_id,
    )
    db.add(student)
    await db.commit()
    await db.refresh(student)

    response = StudentResponse.model_validate(student)
    response.username = username
    return response


@router.get("/{student_id}", response_model=StudentDetailResponse)
async def get_student(
    student_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """学生详情（含统计信息）"""
    result = await db.execute(
        select(Student).where(Student.id == student_id)
    )
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "STUDENT_NOT_FOUND", "message": "学生不存在"},
        )

    # 统计信息
    total_courses_result = await db.execute(
        select(func.count()).where(Course.student_id == student_id)
    )
    total_courses = total_courses_result.scalar_one()

    completed_courses_result = await db.execute(
        select(func.count()).where(
            Course.student_id == student_id,
            Course.status == "completed"
        )
    )
    completed_courses = completed_courses_result.scalar_one()

    pending_assignments_result = await db.execute(
        select(func.count()).where(
            AssignmentStudent.student_id == student_id,
            AssignmentStudent.status == "pending"
        )
    )
    pending_assignments = pending_assignments_result.scalar_one()

    # 计算总已付款和欠款
    paid_result = await db.execute(
        select(func.coalesce(func.sum(BillingRecord.paid_amount), 0)).where(
            BillingRecord.student_id == student_id
        )
    )
    total_paid = float(paid_result.scalar_one())

    receivable_result = await db.execute(
        select(func.coalesce(func.sum(BillingRecord.amount), 0)).where(
            BillingRecord.student_id == student_id
        )
    )
    total_receivable = float(receivable_result.scalar_one())
    outstanding = max(0.0, total_receivable - total_paid)

    stats = StudentStats(
        total_courses=total_courses,
        completed_courses=completed_courses,
        pending_assignments=pending_assignments,
        total_paid=total_paid,
        outstanding=outstanding,
    )

    response = StudentDetailResponse.model_validate(student)
    response.stats = stats
    if student.user_id:
        u_result = await db.execute(
            select(User).where(User.id == student.user_id)
        )
        linked_user = u_result.scalar_one_or_none()
        if linked_user:
            response.username = linked_user.username
    return response


@router.put("/{student_id}", response_model=StudentResponse)
async def update_student(
    student_id: int,
    data: StudentUpdate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """更新学生信息"""
    result = await db.execute(
        select(Student).where(Student.id == student_id)
    )
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "STUDENT_NOT_FOUND", "message": "学生不存在"},
        )

    update_data = data.model_dump(exclude_unset=True)
    req_username = update_data.pop("username", None)
    req_password = update_data.pop("password", None)

    for key, value in update_data.items():
        setattr(student, key, value)

    # 处理 Web 登录账号
    if req_username or req_password:
        if student.user_id:
            # 更新已有 User
            user_result = await db.execute(
                select(User).where(User.id == student.user_id)
            )
            user = user_result.scalar_one_or_none()
            if user:
                if req_username and req_username != user.username:
                    existing = await db.execute(
                        select(User).where(User.username == req_username, User.id != user.id)
                    )
                    if existing.scalar_one_or_none():
                        raise HTTPException(
                            status_code=status.HTTP_409_CONFLICT,
                            detail={"code": "USERNAME_EXISTS", "message": "用户名已存在"},
                        )
                    user.username = req_username
                if req_password:
                    user.hashed_password = get_password_hash(req_password)
        elif req_username and req_password:
            # 创建新 User
            existing = await db.execute(
                select(User).where(User.username == req_username)
            )
            if existing.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={"code": "USERNAME_EXISTS", "message": "用户名已存在"},
                )
            user = User(
                username=req_username,
                hashed_password=get_password_hash(req_password),
                role="student",
                display_name=student.name,
                is_active=True,
            )
            db.add(user)
            await db.flush()
            student.user_id = user.id

    await db.commit()
    await db.refresh(student)

    # 填充 username
    response = StudentResponse.model_validate(student)
    if student.user_id:
        user_result = await db.execute(
            select(User).where(User.id == student.user_id)
        )
        linked_user = user_result.scalar_one_or_none()
        if linked_user:
            response.username = linked_user.username
    return response


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_student(
    student_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """软删除学生（is_active=False）"""
    result = await db.execute(
        select(Student).where(Student.id == student_id)
    )
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "STUDENT_NOT_FOUND", "message": "学生不存在"},
        )

    student.is_active = False
    await db.commit()


@router.get("/{student_id}/courses", response_model=CourseListResponse)
async def get_student_courses(
    student_id: int,
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """某学生的课程历史"""
    student_result = await db.execute(
        select(Student).where(Student.id == student_id)
    )
    if not student_result.scalar_one_or_none():
        raise HTTPException(
            status_code=404,
            detail={"code": "STUDENT_NOT_FOUND", "message": "学生不存在"},
        )

    query = select(Course).where(Course.student_id == student_id)
    if status:
        query = query.where(Course.status == status)

    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar_one()

    offset = (page - 1) * page_size
    query = query.order_by(Course.start_time.desc()).offset(offset).limit(page_size)
    result = await db.execute(query)
    courses = result.scalars().all()

    pages = (total + page_size - 1) // page_size

    # 获取学生姓名
    student_res = await db.execute(select(Student).where(Student.id == student_id))
    student_obj = student_res.scalar_one_or_none()
    student_name = student_obj.name if student_obj else ""

    items = []
    for c in courses:
        cr = CourseResponse.model_validate(c)
        cr.student_name = student_name
        items.append(cr)

    return CourseListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/{student_id}/billing-summary")
async def get_student_billing_summary(
    student_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """某学生的收费汇总"""
    student_result = await db.execute(
        select(Student).where(Student.id == student_id)
    )
    student = student_result.scalar_one_or_none()
    if not student:
        raise HTTPException(
            status_code=404,
            detail={"code": "STUDENT_NOT_FOUND", "message": "学生不存在"},
        )

    # 统计
    stats = await db.execute(
        select(
            func.coalesce(func.sum(BillingRecord.amount), 0).label("total_receivable"),
            func.coalesce(func.sum(BillingRecord.paid_amount), 0).label("total_paid"),
            func.count(BillingRecord.id).label("total_records"),
        ).where(BillingRecord.student_id == student_id)
    )
    row = stats.one()

    return {
        "student_id": student_id,
        "student_name": student.name,
        "total_receivable": float(row.total_receivable),
        "total_paid": float(row.total_paid),
        "outstanding": float(max(0, row.total_receivable - row.total_paid)),
        "total_records": row.total_records,
    }
