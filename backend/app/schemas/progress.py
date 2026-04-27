from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date


class GradeCreate(BaseModel):
    student_id: int
    subject: str
    exam_type: str  # quiz | midterm | final | mock | other
    exam_name: Optional[str] = None
    score: float
    full_score: float = 100.0
    exam_date: date
    notes: Optional[str] = None


class GradeResponse(BaseModel):
    id: int
    student_id: int
    student_name: Optional[str] = None
    subject: str
    exam_type: str
    exam_name: Optional[str] = None
    score: float
    full_score: float
    exam_date: date
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class GradeListResponse(BaseModel):
    items: List[GradeResponse]
    total: int
    page: int
    page_size: int
    pages: int


class GradeTrendItem(BaseModel):
    exam_date: date
    score: float
    full_score: float
    percentage: float
    exam_type: str
    exam_name: Optional[str] = None


class GradeTrendResponse(BaseModel):
    student_name: str
    subject: str
    data: List[GradeTrendItem]


class KnowledgePointCreate(BaseModel):
    student_id: int
    subject: str
    chapter: Optional[str] = None
    point_name: str
    status: str = "todo"  # todo | learning | mastered
    notes: Optional[str] = None


class KnowledgePointUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    chapter: Optional[str] = None


class KnowledgePointResponse(BaseModel):
    id: int
    student_id: int
    subject: str
    chapter: Optional[str] = None
    point_name: str
    status: str
    notes: Optional[str] = None
    updated_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class KnowledgePointListResponse(BaseModel):
    items: List[KnowledgePointResponse]
    total: int
    page: int
    page_size: int
    pages: int


class LearningReportResponse(BaseModel):
    student: dict
    report_period: dict
    course_summary: dict
    grade_trend: List[dict]
    knowledge_points: dict
    assignment_stats: dict
