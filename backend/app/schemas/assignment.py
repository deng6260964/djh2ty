from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date


class AssignmentCreate(BaseModel):
    title: str
    content: str
    subject: str
    due_date: date
    student_ids: List[int]


class AssignmentUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    subject: Optional[str] = None
    due_date: Optional[date] = None


class GradeRequest(BaseModel):
    score: int
    comment: Optional[str] = None


class StudentSubmission(BaseModel):
    student_id: int
    student_name: str
    status: str
    submitted_at: Optional[datetime] = None
    score: Optional[int] = None
    comment: Optional[str] = None
    graded_at: Optional[datetime] = None


class AssignmentResponse(BaseModel):
    id: int
    title: str
    content: str
    subject: str
    due_date: date
    student_count: int = 0
    submitted_count: int = 0
    graded_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AssignmentDetailResponse(BaseModel):
    id: int
    title: str
    content: str
    subject: str
    due_date: date
    created_at: datetime
    updated_at: datetime
    students: List[StudentSubmission] = []


class AssignmentListResponse(BaseModel):
    items: List[AssignmentResponse]
    total: int
    page: int
    page_size: int
    pages: int


# 小程序端
class MyAssignmentResponse(BaseModel):
    id: int
    title: str
    subject: str
    due_date: date
    status: str
    score: Optional[int] = None
    comment: Optional[str] = None
    created_at: datetime
