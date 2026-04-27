from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class ExamQuestionCreate(BaseModel):
    subject: str
    year: Optional[int] = None
    question_type: str  # choice | fill | essay | reading
    content: str
    options: Optional[Dict[str, str]] = None
    answer: str
    explanation: Optional[str] = None
    difficulty: int = 3
    tags: List[str] = []


class ExamQuestionUpdate(BaseModel):
    subject: Optional[str] = None
    year: Optional[int] = None
    question_type: Optional[str] = None
    content: Optional[str] = None
    options: Optional[Dict[str, str]] = None
    answer: Optional[str] = None
    explanation: Optional[str] = None
    difficulty: Optional[int] = None
    tags: Optional[List[str]] = None


class ExamQuestionResponse(BaseModel):
    id: int
    subject: str
    year: Optional[int] = None
    question_type: str
    content: str
    options: Optional[Dict[str, str]] = None
    answer: str
    explanation: Optional[str] = None
    difficulty: int
    tags: List[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ExamQuestionListResponse(BaseModel):
    items: List[ExamQuestionResponse]
    total: int
    page: int
    page_size: int
    pages: int


class VocabularyCreate(BaseModel):
    subject: str = "english"
    word: str
    phonetic: Optional[str] = None
    meaning: str
    example: Optional[str] = None
    level: Optional[str] = None


class VocabularyResponse(BaseModel):
    id: int
    subject: str
    word: str
    phonetic: Optional[str] = None
    meaning: str
    example: Optional[str] = None
    level: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class VocabularyListResponse(BaseModel):
    items: List[VocabularyResponse]
    total: int
    page: int
    page_size: int
    pages: int


class MockExamCreate(BaseModel):
    student_id: int
    title: str
    subject: str
    question_count: int = 20
    question_types: Optional[List[str]] = None
    difficulty_range: Optional[List[int]] = None
    tags: Optional[List[str]] = None


class MockExamResponse(BaseModel):
    id: int
    student_id: int
    title: str
    subject: str
    question_ids: List[int]
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    score: Optional[float] = None
    created_at: datetime
    questions: Optional[List[ExamQuestionResponse]] = None

    class Config:
        from_attributes = True
