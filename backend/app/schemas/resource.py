from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ResourceShareRequest(BaseModel):
    student_ids: List[int]


class ResourceResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    subject: Optional[str] = None
    grade: Optional[str] = None
    file_type: str
    original_name: str
    file_size: int
    created_at: datetime
    updated_at: datetime
    shared_students: Optional[List[int]] = None

    class Config:
        from_attributes = True


class ResourceListResponse(BaseModel):
    items: List[ResourceResponse]
    total: int
    page: int
    page_size: int
    pages: int
