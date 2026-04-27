from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update

from app.database import get_db
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import (
    NotificationCreate, NotificationResponse,
    NotificationListResponse, UnreadCountResponse
)
from app.dependencies import get_admin_user, get_current_user

router = APIRouter(prefix="/notifications", tags=["通知管理"])


@router.get("/unread-count", response_model=UnreadCountResponse)
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """未读通知数量"""
    result = await db.execute(
        select(func.count()).where(
            Notification.user_id == current_user.id,
            Notification.is_read == False,
        )
    )
    count = result.scalar_one()
    return UnreadCountResponse(count=count)


@router.patch("/read-all")
async def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """全部标记已读"""
    await db.execute(
        update(Notification).where(
            Notification.user_id == current_user.id,
            Notification.is_read == False,
        ).values(is_read=True)
    )
    await db.commit()
    return {"success": True}


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_read: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """通知列表（当前用户的通知）"""
    query = select(Notification).where(Notification.user_id == current_user.id)
    if is_read is not None:
        query = query.where(Notification.is_read == is_read)

    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar_one()

    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(Notification.created_at.desc()).offset(offset).limit(page_size)
    )
    notifications = result.scalars().all()

    items = [NotificationResponse.model_validate(n) for n in notifications]
    return NotificationListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.post("", response_model=list[NotificationResponse], status_code=status.HTTP_201_CREATED)
async def create_notifications(
    data: NotificationCreate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """批量创建通知"""
    notifications = []
    for user_id in data.user_ids:
        n = Notification(
            user_id=user_id,
            title=data.title,
            content=data.content,
            type=data.type,
            related_type=data.related_type,
            related_id=data.related_id,
            wx_push_status="pending" if data.send_wechat else "skipped",
        )
        db.add(n)
        notifications.append(n)

    await db.flush()
    await db.commit()

    result = []
    for n in notifications:
        await db.refresh(n)
        result.append(NotificationResponse.model_validate(n))

    return result


@router.patch("/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """标记通知已读"""
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
    )
    notification = result.scalar_one_or_none()
    if not notification:
        raise HTTPException(
            status_code=404,
            detail={"code": "NOTIFICATION_NOT_FOUND", "message": "通知不存在"},
        )

    notification.is_read = True
    await db.commit()
    return {"success": True}


@router.post("/send")
async def send_notification(
    data: NotificationCreate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """手动发送通知（批量创建并标记发送）"""
    notifications = []
    for user_id in data.user_ids:
        n = Notification(
            user_id=user_id,
            title=data.title,
            content=data.content,
            type=data.type,
            related_type=data.related_type,
            related_id=data.related_id,
            wx_push_status="sent" if data.send_wechat else "skipped",
            wx_push_at=datetime.utcnow() if data.send_wechat else None,
        )
        db.add(n)
        notifications.append(n)

    await db.flush()
    await db.commit()

    return {
        "success": True,
        "sent_count": len(notifications),
    }
