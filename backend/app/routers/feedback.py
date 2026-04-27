from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.database import get_db
from app.models.feedback import Feedback, FeedbackTemplate
from app.models.student import Student
from app.models.user import User
from app.schemas.feedback import (
    FeedbackCreate, FeedbackUpdate, FeedbackResponse, FeedbackListResponse,
    FeedbackPushResponse, FeedbackTemplateCreate, FeedbackTemplateResponse
)
from app.dependencies import get_admin_user, get_current_student

router = APIRouter(prefix="/feedback", tags=["课堂反馈"])


@router.get("/templates", response_model=list[FeedbackTemplateResponse])
async def get_templates(
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """反馈模板列表"""
    result = await db.execute(
        select(FeedbackTemplate).order_by(FeedbackTemplate.created_at.desc())
    )
    templates = result.scalars().all()
    return [FeedbackTemplateResponse.model_validate(t) for t in templates]


@router.post("/templates", response_model=FeedbackTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    data: FeedbackTemplateCreate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """创建反馈模板"""
    template = FeedbackTemplate(
        name=data.name,
        performance=data.performance,
        knowledge_mastery=data.knowledge_mastery,
        problems=data.problems,
        next_plan=data.next_plan,
    )
    db.add(template)
    await db.commit()
    await db.refresh(template)
    return FeedbackTemplateResponse.model_validate(template)


@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """删除反馈模板"""
    result = await db.execute(
        select(FeedbackTemplate).where(FeedbackTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(
            status_code=404,
            detail={"code": "TEMPLATE_NOT_FOUND", "message": "模板不存在"},
        )
    await db.delete(template)
    await db.commit()


@router.get("/my")
async def get_my_feedback(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_student=Depends(get_current_student),
):
    """小程序端：当前学生的反馈"""
    query = select(Feedback).where(
        Feedback.student_id == current_student.id,
        Feedback.is_pushed == True,
    )

    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar_one()

    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(Feedback.created_at.desc()).offset(offset).limit(page_size)
    )
    feedbacks = result.scalars().all()

    items = []
    for f in feedbacks:
        fr = FeedbackResponse.model_validate(f)
        fr.student_name = current_student.name
        items.append(fr)

    return {
        "items": [item.model_dump() for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
    }


@router.get("/my/{feedback_id}")
async def get_my_feedback_detail(
    feedback_id: int,
    db: AsyncSession = Depends(get_db),
    current_student=Depends(get_current_student),
):
    """小程序/学生端：反馈详情"""
    result = await db.execute(
        select(Feedback).where(
            Feedback.id == feedback_id,
            Feedback.student_id == current_student.id,
            Feedback.is_pushed == True,
        )
    )
    feedback = result.scalar_one_or_none()
    if not feedback:
        raise HTTPException(
            status_code=404,
            detail={"code": "FEEDBACK_NOT_FOUND", "message": "反馈不存在或无权访问"},
        )

    fr = FeedbackResponse.model_validate(feedback)
    fr.student_name = current_student.name
    return fr.model_dump()


@router.get("", response_model=FeedbackListResponse)
async def list_feedback(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    student_id: Optional[int] = Query(None),
    is_pushed: Optional[bool] = Query(None),
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """反馈列表"""
    query = select(Feedback)
    conditions = []
    if student_id:
        conditions.append(Feedback.student_id == student_id)
    if is_pushed is not None:
        conditions.append(Feedback.is_pushed == is_pushed)
    if conditions:
        query = query.where(and_(*conditions))

    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar_one()

    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(Feedback.created_at.desc()).offset(offset).limit(page_size)
    )
    feedbacks = result.scalars().all()

    # 批量获取学生姓名
    student_ids = list({f.student_id for f in feedbacks})
    student_map = {}
    if student_ids:
        s_result = await db.execute(
            select(Student).where(Student.id.in_(student_ids))
        )
        for s in s_result.scalars().all():
            student_map[s.id] = s.name

    items = []
    for f in feedbacks:
        fr = FeedbackResponse.model_validate(f)
        fr.student_name = student_map.get(f.student_id, "")
        items.append(fr)

    return FeedbackListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.post("", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def create_feedback(
    data: FeedbackCreate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """创建课堂反馈"""
    # 验证学生存在
    student_result = await db.execute(
        select(Student).where(Student.id == data.student_id)
    )
    student = student_result.scalar_one_or_none()
    if not student:
        raise HTTPException(
            status_code=404,
            detail={"code": "STUDENT_NOT_FOUND", "message": "学生不存在"},
        )

    feedback = Feedback(
        course_id=data.course_id,
        student_id=data.student_id,
        performance=data.performance,
        knowledge_mastery=data.knowledge_mastery,
        problems=data.problems,
        next_plan=data.next_plan,
        rating=data.rating,
    )
    db.add(feedback)
    await db.commit()
    await db.refresh(feedback)

    response = FeedbackResponse.model_validate(feedback)
    response.student_name = student.name
    return response


@router.get("/{feedback_id}", response_model=FeedbackResponse)
async def get_feedback(
    feedback_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """反馈详情"""
    result = await db.execute(
        select(Feedback, Student.name.label("student_name")).join(
            Student, Feedback.student_id == Student.id
        ).where(Feedback.id == feedback_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(
            status_code=404,
            detail={"code": "FEEDBACK_NOT_FOUND", "message": "反馈不存在"},
        )
    feedback, student_name = row
    response = FeedbackResponse.model_validate(feedback)
    response.student_name = student_name
    return response


@router.put("/{feedback_id}", response_model=FeedbackResponse)
async def update_feedback(
    feedback_id: int,
    data: FeedbackUpdate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """更新反馈"""
    result = await db.execute(select(Feedback).where(Feedback.id == feedback_id))
    feedback = result.scalar_one_or_none()
    if not feedback:
        raise HTTPException(
            status_code=404,
            detail={"code": "FEEDBACK_NOT_FOUND", "message": "反馈不存在"},
        )

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(feedback, key, value)

    await db.commit()
    await db.refresh(feedback)
    return await get_feedback(feedback_id, current_user, db)


@router.post("/{feedback_id}/push", response_model=FeedbackPushResponse)
async def push_feedback(
    feedback_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """推送反馈给学生/家长"""
    result = await db.execute(
        select(Feedback, Student).join(
            Student, Feedback.student_id == Student.id
        ).where(Feedback.id == feedback_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(
            status_code=404,
            detail={"code": "FEEDBACK_NOT_FOUND", "message": "反馈不存在"},
        )
    feedback, student = row

    push_time = datetime.utcnow()
    feedback.is_pushed = True
    feedback.pushed_at = push_time

    # 实际微信推送（若有 openid 则尝试推送）
    # 这里标记为已推送，实际推送通过微信 API 实现
    # TODO: 集成微信订阅消息模板时取消注释
    # from app.utils.wechat import send_wechat_subscribe_message
    # if student.user_id:
    #     user_result = await db.execute(select(User).where(User.id == student.user_id))
    #     user = user_result.scalar_one_or_none()
    #     if user and user.openid:
    #         await send_wechat_subscribe_message(user.openid, TEMPLATE_ID, {...})

    await db.commit()

    return FeedbackPushResponse(pushed=True, pushed_at=push_time)
