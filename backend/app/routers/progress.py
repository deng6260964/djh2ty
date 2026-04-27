from typing import Optional
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.database import get_db
from app.models.progress import Grade, KnowledgePoint
from app.models.student import Student
from app.models.course import Course
from app.models.assignment import AssignmentStudent
from app.schemas.progress import (
    GradeCreate, GradeResponse, GradeListResponse,
    GradeTrendItem, GradeTrendResponse,
    KnowledgePointCreate, KnowledgePointUpdate,
    KnowledgePointResponse, KnowledgePointListResponse,
    LearningReportResponse,
)
from app.dependencies import get_admin_user, get_current_student
from app.models.user import User

router = APIRouter(prefix="/progress", tags=["学习进度"])


@router.get("/my")
async def get_my_progress(
    db: AsyncSession = Depends(get_db),
    current_student=Depends(get_current_student),
):
    """小程序端：当前学生的成绩和知识点"""
    # 最近 10 条成绩
    grade_result = await db.execute(
        select(Grade).where(Grade.student_id == current_student.id)
        .order_by(Grade.exam_date.desc()).limit(10)
    )
    grades = grade_result.scalars().all()

    # 知识点汇总
    kp_result = await db.execute(
        select(
            KnowledgePoint.status,
            func.count(KnowledgePoint.id).label("count")
        ).where(KnowledgePoint.student_id == current_student.id)
        .group_by(KnowledgePoint.status)
    )
    kp_stats = {row.status: row.count for row in kp_result.all()}

    return {
        "student_name": current_student.name,
        "recent_grades": [
            {
                "id": g.id,
                "subject": g.subject,
                "exam_type": g.exam_type,
                "exam_name": g.exam_name,
                "score": float(g.score),
                "full_score": float(g.full_score),
                "percentage": round(float(g.score) / float(g.full_score) * 100, 1),
                "exam_date": g.exam_date,
            }
            for g in grades
        ],
        "knowledge_points": {
            "mastered": kp_stats.get("mastered", 0),
            "learning": kp_stats.get("learning", 0),
            "todo": kp_stats.get("todo", 0),
        }
    }


@router.get("/my/grades/trend")
async def get_my_grade_trend(
    subject: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_student=Depends(get_current_student),
):
    """学生端：成绩趋势（按科目）"""
    result = await db.execute(
        select(Grade).where(
            Grade.student_id == current_student.id,
            Grade.subject == subject,
        ).order_by(Grade.exam_date.asc())
    )
    grades = result.scalars().all()

    return {
        "student_name": current_student.name,
        "subject": subject,
        "data": [
            {
                "exam_date": str(g.exam_date),
                "score": float(g.score),
                "full_score": float(g.full_score),
                "percentage": round(float(g.score) / float(g.full_score) * 100, 1),
                "exam_type": g.exam_type,
                "exam_name": g.exam_name,
            }
            for g in grades
        ],
    }


@router.get("/my/knowledge-points")
async def get_my_knowledge_points(
    subject: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_student=Depends(get_current_student),
):
    """学生端：知识点列表"""
    query = select(KnowledgePoint).where(
        KnowledgePoint.student_id == current_student.id
    )
    if subject:
        query = query.where(KnowledgePoint.subject == subject)

    result = await db.execute(
        query.order_by(KnowledgePoint.subject, KnowledgePoint.chapter, KnowledgePoint.point_name)
    )
    kps = result.scalars().all()

    return [
        {
            "id": kp.id,
            "subject": kp.subject,
            "chapter": kp.chapter,
            "point_name": kp.point_name,
            "status": kp.status,
            "notes": kp.notes,
        }
        for kp in kps
    ]


@router.get("/grades", response_model=GradeListResponse)
async def list_grades(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    student_id: Optional[int] = Query(None),
    subject: Optional[str] = Query(None),
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """成绩列表"""
    query = select(Grade)
    conditions = []
    if student_id:
        conditions.append(Grade.student_id == student_id)
    if subject:
        conditions.append(Grade.subject == subject)
    if conditions:
        query = query.where(and_(*conditions))

    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar_one()

    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(Grade.exam_date.desc()).offset(offset).limit(page_size)
    )
    grades = result.scalars().all()

    # 批量获取学生姓名
    student_ids = list({g.student_id for g in grades})
    student_map = {}
    if student_ids:
        s_result = await db.execute(
            select(Student).where(Student.id.in_(student_ids))
        )
        for s in s_result.scalars().all():
            student_map[s.id] = s.name

    items = []
    for g in grades:
        gr = GradeResponse.model_validate(g)
        gr.student_name = student_map.get(g.student_id, "")
        items.append(gr)

    return GradeListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.post("/grades", response_model=GradeResponse, status_code=status.HTTP_201_CREATED)
async def create_grade(
    data: GradeCreate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """记录成绩"""
    student_result = await db.execute(
        select(Student).where(Student.id == data.student_id)
    )
    student = student_result.scalar_one_or_none()
    if not student:
        raise HTTPException(
            status_code=404,
            detail={"code": "STUDENT_NOT_FOUND", "message": "学生不存在"},
        )

    grade = Grade(
        student_id=data.student_id,
        subject=data.subject,
        exam_type=data.exam_type,
        exam_name=data.exam_name,
        score=data.score,
        full_score=data.full_score,
        exam_date=data.exam_date,
        notes=data.notes,
    )
    db.add(grade)
    await db.commit()
    await db.refresh(grade)

    response = GradeResponse.model_validate(grade)
    response.student_name = student.name
    return response


@router.get("/grades/trend", response_model=GradeTrendResponse)
async def get_grade_trend(
    student_id: int = Query(...),
    subject: str = Query(...),
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """成绩趋势（按科目分组）"""
    student_result = await db.execute(
        select(Student).where(Student.id == student_id)
    )
    student = student_result.scalar_one_or_none()
    if not student:
        raise HTTPException(
            status_code=404,
            detail={"code": "STUDENT_NOT_FOUND", "message": "学生不存在"},
        )

    result = await db.execute(
        select(Grade).where(
            Grade.student_id == student_id,
            Grade.subject == subject,
        ).order_by(Grade.exam_date.asc())
    )
    grades = result.scalars().all()

    data = [
        GradeTrendItem(
            exam_date=g.exam_date,
            score=float(g.score),
            full_score=float(g.full_score),
            percentage=round(float(g.score) / float(g.full_score) * 100, 1),
            exam_type=g.exam_type,
            exam_name=g.exam_name,
        )
        for g in grades
    ]

    return GradeTrendResponse(
        student_name=student.name,
        subject=subject,
        data=data,
    )


@router.get("/grades/{grade_id}", response_model=GradeResponse)
async def get_grade(
    grade_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """成绩详情"""
    result = await db.execute(
        select(Grade, Student.name.label("student_name")).join(
            Student, Grade.student_id == Student.id
        ).where(Grade.id == grade_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(
            status_code=404,
            detail={"code": "GRADE_NOT_FOUND", "message": "成绩记录不存在"},
        )
    grade, student_name = row
    response = GradeResponse.model_validate(grade)
    response.student_name = student_name
    return response


@router.delete("/grades/{grade_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_grade(
    grade_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """删除成绩"""
    result = await db.execute(select(Grade).where(Grade.id == grade_id))
    grade = result.scalar_one_or_none()
    if not grade:
        raise HTTPException(
            status_code=404,
            detail={"code": "GRADE_NOT_FOUND", "message": "成绩记录不存在"},
        )
    await db.delete(grade)
    await db.commit()


@router.get("/knowledge-points", response_model=KnowledgePointListResponse)
async def list_knowledge_points(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    student_id: Optional[int] = Query(None),
    subject: Optional[str] = Query(None),
    kp_status: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """知识点列表"""
    query = select(KnowledgePoint)
    conditions = []
    if student_id:
        conditions.append(KnowledgePoint.student_id == student_id)
    if subject:
        conditions.append(KnowledgePoint.subject == subject)
    if kp_status:
        conditions.append(KnowledgePoint.status == kp_status)
    if conditions:
        query = query.where(and_(*conditions))

    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar_one()

    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(KnowledgePoint.subject, KnowledgePoint.chapter, KnowledgePoint.point_name)
        .offset(offset).limit(page_size)
    )
    kps = result.scalars().all()

    items = [KnowledgePointResponse.model_validate(kp) for kp in kps]
    return KnowledgePointListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.post("/knowledge-points", response_model=KnowledgePointResponse, status_code=status.HTTP_201_CREATED)
async def create_knowledge_point(
    data: KnowledgePointCreate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """创建知识点"""
    student_result = await db.execute(
        select(Student).where(Student.id == data.student_id)
    )
    if not student_result.scalar_one_or_none():
        raise HTTPException(
            status_code=404,
            detail={"code": "STUDENT_NOT_FOUND", "message": "学生不存在"},
        )

    # 检查是否已存在（同学生+科目+知识点名）
    existing = await db.execute(
        select(KnowledgePoint).where(
            KnowledgePoint.student_id == data.student_id,
            KnowledgePoint.subject == data.subject,
            KnowledgePoint.point_name == data.point_name,
        )
    )
    kp = existing.scalar_one_or_none()

    if kp:
        # 更新状态
        kp.status = data.status
        kp.notes = data.notes
        kp.chapter = data.chapter
    else:
        kp = KnowledgePoint(
            student_id=data.student_id,
            subject=data.subject,
            chapter=data.chapter,
            point_name=data.point_name,
            status=data.status,
            notes=data.notes,
        )
        db.add(kp)

    await db.commit()
    await db.refresh(kp)
    return KnowledgePointResponse.model_validate(kp)


@router.put("/knowledge-points/{kp_id}", response_model=KnowledgePointResponse)
async def update_knowledge_point(
    kp_id: int,
    data: KnowledgePointUpdate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """更新知识点掌握状态"""
    result = await db.execute(
        select(KnowledgePoint).where(KnowledgePoint.id == kp_id)
    )
    kp = result.scalar_one_or_none()
    if not kp:
        raise HTTPException(
            status_code=404,
            detail={"code": "KP_NOT_FOUND", "message": "知识点不存在"},
        )

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(kp, key, value)

    await db.commit()
    await db.refresh(kp)
    return KnowledgePointResponse.model_validate(kp)


@router.delete("/knowledge-points/{kp_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge_point(
    kp_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """删除知识点"""
    result = await db.execute(select(KnowledgePoint).where(KnowledgePoint.id == kp_id))
    kp = result.scalar_one_or_none()
    if not kp:
        raise HTTPException(status_code=404, detail={"code": "KP_NOT_FOUND", "message": "知识点不存在"})
    await db.delete(kp)
    await db.commit()


@router.get("/report/{student_id}", response_model=LearningReportResponse)
async def get_learning_report(
    student_id: int,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """生成学习报告（JSON 格式，供前端 jsPDF 渲染）"""
    student_result = await db.execute(
        select(Student).where(Student.id == student_id)
    )
    student = student_result.scalar_one_or_none()
    if not student:
        raise HTTPException(
            status_code=404,
            detail={"code": "STUDENT_NOT_FOUND", "message": "学生不存在"},
        )

    # 课程汇总
    course_query = select(Course).where(Course.student_id == student_id)
    course_result = await db.execute(course_query)
    all_courses = course_result.scalars().all()
    completed_courses = [c for c in all_courses if c.status == "completed"]
    total_hours = sum(c.duration for c in completed_courses) / 60.0

    # 成绩趋势（所有科目）
    grade_result = await db.execute(
        select(Grade).where(Grade.student_id == student_id)
        .order_by(Grade.exam_date.asc())
    )
    grades = grade_result.scalars().all()

    grade_trend = [
        {
            "subject": g.subject,
            "exam_date": str(g.exam_date),
            "score": float(g.score),
            "full_score": float(g.full_score),
            "percentage": round(float(g.score) / float(g.full_score) * 100, 1),
            "exam_type": g.exam_type,
            "exam_name": g.exam_name,
        }
        for g in grades
    ]

    # 知识点汇总
    kp_result = await db.execute(
        select(KnowledgePoint).where(KnowledgePoint.student_id == student_id)
    )
    all_kps = kp_result.scalars().all()
    mastered_count = sum(1 for kp in all_kps if kp.status == "mastered")
    learning_count = sum(1 for kp in all_kps if kp.status == "learning")
    todo_count = sum(1 for kp in all_kps if kp.status == "todo")

    kp_details = [
        {
            "id": kp.id,
            "subject": kp.subject,
            "chapter": kp.chapter,
            "point_name": kp.point_name,
            "status": kp.status,
        }
        for kp in all_kps
    ]

    # 作业统计
    asgn_result = await db.execute(
        select(AssignmentStudent).where(AssignmentStudent.student_id == student_id)
    )
    all_submissions = asgn_result.scalars().all()
    submitted_count = sum(1 for a in all_submissions if a.status in ("submitted", "graded"))
    graded_with_score = [a for a in all_submissions if a.score is not None]
    avg_score = (
        sum(a.score for a in graded_with_score) / len(graded_with_score)
        if graded_with_score else 0
    )

    report_start = str(start_date) if start_date else str(
        all_courses[0].start_time.date() if all_courses else datetime.today().date()
    )
    report_end = str(end_date) if end_date else str(datetime.today().date())

    return LearningReportResponse(
        student={"name": student.name, "grade": student.grade},
        report_period={"start": report_start, "end": report_end},
        course_summary={
            "total": len(all_courses),
            "completed": len(completed_courses),
            "total_hours": round(total_hours, 1),
        },
        grade_trend=grade_trend,
        knowledge_points={
            "mastered": mastered_count,
            "learning": learning_count,
            "todo": todo_count,
            "details": kp_details,
        },
        assignment_stats={
            "total": len(all_submissions),
            "submitted": submitted_count,
            "avg_score": round(avg_score, 1),
        },
    )
