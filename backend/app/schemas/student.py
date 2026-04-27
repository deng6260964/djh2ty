from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class StudentCreate(BaseModel):
    name: str
    grade: str
    subjects: List[str]
    parent_name: Optional[str] = None
    parent_phone: Optional[str] = None
    school: Optional[str] = None
    notes: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None


class StudentUpdate(BaseModel):
    name: Optional[str] = None
    grade: Optional[str] = None
    subjects: Optional[List[str]] = None
    parent_name: Optional[str] = None
    parent_phone: Optional[str] = None
    school: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None
    username: Optional[str] = None
    password: Optional[str] = None


class StudentStats(BaseModel):
    total_courses: int = 0
    completed_courses: int = 0
    pending_assignments: int = 0
    total_paid: float = 0.0
    outstanding: float = 0.0


class StudentResponse(BaseModel):
    id: int
    name: str
    grade: str
    subjects: List[str]
    parent_name: Optional[str] = None
    parent_phone: Optional[str] = None
    school: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool
    user_id: Optional[int] = None
    parent_user_id: Optional[int] = None
    username: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StudentDetailResponse(StudentResponse):
    stats: Optional[StudentStats] = None


class StudentListResponse(BaseModel):
    items: List[StudentResponse]
    total: int
    page: int
    page_size: int
    pages: int
