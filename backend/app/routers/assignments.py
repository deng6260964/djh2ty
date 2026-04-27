from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, case

from app.database import get_db
from app.models.assignment import Assignment, AssignmentStudent
from app.models.student import Student
from app.schemas.assignment import (
    AssignmentCreate, AssignmentUpdate, GradeRequest,
    AssignmentResponse, AssignmentDetailResponse, AssignmentListResponse,
    StudentSubmission, MyAssignmentResponse
)
from app.dependencies import get_admin_user, get_current_student
from app.models.user import User

router = APIRouter(prefix="/assignments", tags=["作业管理"])


@router.get("/my")
async def get_my_assignments(
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_student=Depends(get_current_student),
):
    """小程序端：当前学生的作业列表"""
    query = select(AssignmentStudent, Assignment).join(
        Assignment, AssignmentStudent.assignment_id == Assignment.id
    ).where(AssignmentStudent.student_id == current_student.id)

    if status_filter:
        query = query.where(AssignmentStudent.status == status_filter)

    count_result = await db.execute(
        select(func.count()).select_from(
            select(AssignmentStudent).where(
                AssignmentStudent.student_id == current_student.id
            ).subquery()
        )
    )
    total = count_result.scalar_one()

    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(Assignment.due_date.asc()).offset(offset).limit(page_size)
    )
    rows = result.all()

    items = []
    for row in rows:
        as_obj, asgn = row
        items.append(MyAssignmentResponse(
            id=asgn.id,
            title=asgn.title,
            subject=asgn.subject,
            due_date=asgn.due_date,
            status=as_obj.status,
            score=as_obj.score,
            comment=as_obj.comment,
            created_at=asgn.created_at,
        ))

    return {
        "items": [item.model_dump() for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
    }


@router.get("/{assignment_id}/my")
async def get_my_assignment_detail(
    assignment_id: int,
    db: AsyncSession = Depends(get_db),
    current_student=Depends(get_current_student),
):
    """小程序端：作业详情（含本人提交）"""
    result = await db.execute(
        select(Assignment, AssignmentStudent).join(
            AssignmentStudent,
            and_(
                AssignmentStudent.assignment_id == Assignment.id,
                AssignmentStudent.student_id == current_student.id
            )
        ).where(Assignment.id == assignment_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(
            status_code=404,
            detail={"code": "ASSIGNMENT_NOT_FOUND", "message": "作业不存在或无权访问"},
        )

    asgn, as_obj = row
    return {
        "id": asgn.id,
        "title": asgn.title,
        "content": asgn.content,
        "subject": asgn.subject,
        "due_date": asgn.due_date,
        "status": as_obj.status,
        "submitted_at": as_obj.submitted_at,
        "score": as_obj.score,
        "comment": as_obj.comment,
        "graded_at": as_obj.graded_at,
        "created_at": asgn.created_at,
    }


@router.get("", response_model=AssignmentListResponse)
async def list_assignments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    subject: Optional[str] = Query(None),
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """作业列表"""
    query = select(Assignment)
    if subject:
        query = query.where(Assignment.subject == subject)

    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar_one()

    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(Assignment.created_at.desc()).offset(offset).limit(page_size)
    )
    assignments = result.scalars().all()

    items = []
    for asgn in assignments:
        # 统计各状态
        stats_result = await db.execute(
            select(
                func.count(AssignmentStudent.id).label("total"),
                func.sum(
                    case((AssignmentStudent.status == "submitted", 1), else_=0)
                ).label("submitted"),
                func.sum(
                    case((AssignmentStudent.status == "graded", 1), else_=0)
                ).label("graded"),
            ).where(AssignmentStudent.assignment_id == asgn.id)
        )
        stats = stats_result.one()

        items.append(AssignmentResponse(
            id=asgn.id,
            title=asgn.title,
            content=asgn.content,
            subject=asgn.subject,
            due_date=asgn.due_date,
            student_count=stats.total or 0,
            submitted_count=int(stats.submitted or 0),
            graded_count=int(stats.graded or 0),
            created_at=asgn.created_at,
            updated_at=asgn.updated_at,
        ))

    return AssignmentListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.post("", response_model=AssignmentDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_assignment(
    data: AssignmentCreate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """布置作业"""
    if not data.student_ids:
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_REQUEST", "message": "至少选择一名学生"},
        )

    # 验证学生存在
    students_result = await db.execute(
        select(Student).where(Student.id.in_(data.student_ids))
    )
    students = students_result.scalars().all()
    student_map = {s.id: s for s in students}

    if len(students) != len(data.student_ids):
        raise HTTPException(
            status_code=404,
            detail={"code": "STUDENT_NOT_FOUND", "message": "部分学生不存在"},
        )

    assignment = Assignment(
        title=data.title,
        content=data.content,
        subject=data.subject,
        due_date=data.due_date,
    )
    db.add(assignment)
    await db.flush()

    # 为每个学生创建提交记录
    for student_id in data.student_ids:
        as_record = AssignmentStudent(
            assignment_id=assignment.id,
            student_id=student_id,
            status="pending",
        )
        db.add(as_record)

    await db.commit()
    await db.refresh(assignment)

    # 查询提交记录
    as_result = await db.execute(
        select(AssignmentStudent).where(AssignmentStudent.assignment_id == assignment.id)
    )
    submissions = as_result.scalars().all()

    student_submissions = [
        StudentSubmission(
            student_id=sub.student_id,
            student_name=student_map[sub.student_id].name,
            status=sub.status,
            submitted_at=sub.submitted_at,
            score=sub.score,
            comment=sub.comment,
            graded_at=sub.graded_at,
        )
        for sub in submissions
    ]

    return AssignmentDetailResponse(
        id=assignment.id,
        title=assignment.title,
        content=assignment.content,
        subject=assignment.subject,
        due_date=assignment.due_date,
        created_at=assignment.created_at,
        updated_at=assignment.updated_at,
        students=student_submissions,
    )


@router.get("/{assignment_id}", response_model=AssignmentDetailResponse)
async def get_assignment(
    assignment_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """作业详情（含所有学生完成情况）"""
    result = await db.execute(
        select(Assignment).where(Assignment.id == assignment_id)
    )
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(
            status_code=404,
            detail={"code": "ASSIGNMENT_NOT_FOUND", "message": "作业不存在"},
        )

    # 查询所有学生提交记录
    as_result = await db.execute(
        select(AssignmentStudent, Student.name.label("student_name")).join(
            Student, AssignmentStudent.student_id == Student.id
        ).where(AssignmentStudent.assignment_id == assignment_id)
    )
    rows = as_result.all()

    student_submissions = [
        StudentSubmission(
            student_id=row.AssignmentStudent.student_id,
            student_name=row.student_name,
            status=row.AssignmentStudent.status,
            submitted_at=row.AssignmentStudent.submitted_at,
            score=row.AssignmentStudent.score,
            comment=row.AssignmentStudent.comment,
            graded_at=row.AssignmentStudent.graded_at,
        )
        for row in rows
    ]

    return AssignmentDetailResponse(
        id=assignment.id,
        title=assignment.title,
        content=assignment.content,
        subject=assignment.subject,
        due_date=assignment.due_date,
        created_at=assignment.created_at,
        updated_at=assignment.updated_at,
        students=student_submissions,
    )


@router.put("/{assignment_id}", response_model=AssignmentDetailResponse)
async def update_assignment(
    assignment_id: int,
    data: AssignmentUpdate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """更新作业"""
    result = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(
            status_code=404,
            detail={"code": "ASSIGNMENT_NOT_FOUND", "message": "作业不存在"},
        )

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(assignment, key, value)

    await db.commit()
    await db.refresh(assignment)
    return await get_assignment(assignment_id, current_user, db)


@router.delete("/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assignment(
    assignment_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """删除作业"""
    result = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(
            status_code=404,
            detail={"code": "ASSIGNMENT_NOT_FOUND", "message": "作业不存在"},
        )
    await db.delete(assignment)
    await db.commit()


@router.post("/{assignment_id}/grade/{student_id}")
async def grade_assignment(
    assignment_id: int,
    student_id: int,
    data: GradeRequest,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """批改作业（评分+评语）"""
    result = await db.execute(
        select(AssignmentStudent).where(
            AssignmentStudent.assignment_id == assignment_id,
            AssignmentStudent.student_id == student_id,
        )
    )
    as_record = result.scalar_one_or_none()
    if not as_record:
        raise HTTPException(
            status_code=404,
            detail={"code": "SUBMISSION_NOT_FOUND", "message": "未找到该学生的作业记录"},
        )

    if not (0 <= data.score <= 100):
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_SCORE", "message": "评分必须在 0-100 之间"},
        )

    as_record.score = data.score
    as_record.comment = data.comment
    as_record.status = "graded"
    as_record.graded_at = datetime.utcnow()

    await db.commit()
    await db.refresh(as_record)

    return {
        "assignment_id": assignment_id,
        "student_id": student_id,
        "score": as_record.score,
        "comment": as_record.comment,
        "graded_at": as_record.graded_at,
    }
