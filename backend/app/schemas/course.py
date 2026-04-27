from pydantic import BaseModel, model_validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date


class CourseCreate(BaseModel):
    student_id: int
    subject: str
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None
    notes: Optional[str] = None
    hourly_rate: Optional[float] = None

    @model_validator(mode="after")
    def validate_times(self):
        if self.end_time <= self.start_time:
            raise ValueError("结束时间必须晚于开始时间")
        return self


class CourseUpdate(BaseModel):
    student_id: Optional[int] = None
    subject: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    hourly_rate: Optional[float] = None
    status: Optional[str] = None


class CourseStatusUpdate(BaseModel):
    status: str  # scheduled | completed | cancelled


class ConflictCheckRequest(BaseModel):
    start_time: datetime
    end_time: datetime
    exclude_id: Optional[int] = None


class ConflictInfo(BaseModel):
    course_id: int
    student_name: str
    start_time: datetime
    end_time: datetime


class ConflictCheckResponse(BaseModel):
    has_conflict: bool
    conflict: Optional[ConflictInfo] = None


class CourseResponse(BaseModel):
    id: int
    student_id: int
    student_name: Optional[str] = None
    subject: str
    start_time: datetime
    end_time: datetime
    duration: int
    status: str
    location: Optional[str] = None
    hourly_rate: Optional[float] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CourseListResponse(BaseModel):
    items: List[CourseResponse]
    total: int
    page: int
    page_size: int
    pages: int


class CalendarCourseItem(BaseModel):
    id: int
    student_name: str
    subject: str
    start_time: str
    end_time: str
    status: str
    student_id: int


class CopyWeekPreviewRequest(BaseModel):
    source_week_start: date
    target_week_start: date


class CopyWeekPreviewItem(BaseModel):
    source_course_id: int
    student_id: int
    student_name: str
    subject: str
    source_start_time: datetime
    source_end_time: datetime
    target_start_time: datetime
    target_end_time: datetime
    duration: int
    projected_charge: float
    current_balance: float
    needs_payment: bool
    has_conflict: bool
    status: str
    conflict: Optional[ConflictInfo] = None


class CopyWeekPreviewResponse(BaseModel):
    source_week_start: date
    target_week_start: date
    items: List[CopyWeekPreviewItem]
    total_count: int
    copyable_count: int
    conflict_count: int
    needs_payment_count: int


class CopyWeekConfirmRequest(BaseModel):
    source_week_start: date
    target_week_start: date
    selected_course_ids: List[int]


class CopyWeekConfirmSkippedItem(BaseModel):
    source_course_id: int
    reason: str
    conflict: Optional[ConflictInfo] = None


class CopyWeekConfirmResponse(BaseModel):
    created_count: int
    skipped_count: int
    created_course_ids: List[int]
    skipped_items: List[CopyWeekConfirmSkippedItem]
