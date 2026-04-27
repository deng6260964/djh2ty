from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class NotificationCreate(BaseModel):
    user_ids: List[int]
    title: str
    content: str
    type: str = "manual"
    related_type: Optional[str] = None
    related_id: Optional[int] = None
    send_wechat: bool = False


class NotificationResponse(BaseModel):
    id: int
    user_id: int
    title: str
    content: str
    type: str
    is_read: bool
    related_type: Optional[str] = None
    related_id: Optional[int] = None
    wx_push_status: str
    wx_push_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    items: List[NotificationResponse]
    total: int
    page: int
    page_size: int
    pages: int


class UnreadCountResponse(BaseModel):
    count: int
