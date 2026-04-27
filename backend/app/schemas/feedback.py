from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class FeedbackCreate(BaseModel):
    course_id: Optional[int] = None
    student_id: int
    performance: str
    knowledge_mastery: Optional[str] = None
    problems: Optional[str] = None
    next_plan: Optional[str] = None
    rating: Optional[int] = None


class FeedbackUpdate(BaseModel):
    performance: Optional[str] = None
    knowledge_mastery: Optional[str] = None
    problems: Optional[str] = None
    next_plan: Optional[str] = None
    rating: Optional[int] = None


class FeedbackResponse(BaseModel):
    id: int
    course_id: Optional[int] = None
    student_id: int
    student_name: Optional[str] = None
    performance: str
    knowledge_mastery: Optional[str] = None
    problems: Optional[str] = None
    next_plan: Optional[str] = None
    rating: Optional[int] = None
    is_pushed: bool
    pushed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FeedbackListResponse(BaseModel):
    items: List[FeedbackResponse]
    total: int
    page: int
    page_size: int
    pages: int


class FeedbackPushResponse(BaseModel):
    pushed: bool
    pushed_at: datetime


class FeedbackTemplateCreate(BaseModel):
    name: str
    performance: Optional[str] = None
    knowledge_mastery: Optional[str] = None
    problems: Optional[str] = None
    next_plan: Optional[str] = None


class FeedbackTemplateResponse(BaseModel):
    id: int
    name: str
    performance: Optional[str] = None
    knowledge_mastery: Optional[str] = None
    problems: Optional[str] = None
    next_plan: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
