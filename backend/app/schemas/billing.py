from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date


class SubjectPriceUpdate(BaseModel):
    price_per_hour: float


class SubjectPriceResponse(BaseModel):
    id: int
    subject: str
    price_per_hour: float
    updated_at: datetime

    class Config:
        from_attributes = True


class BillingRecordCreate(BaseModel):
    student_id: int
    course_id: Optional[int] = None
    amount: float
    notes: Optional[str] = None


class BillingRecordPayRequest(BaseModel):
    paid_amount: float
    payment_method: str  # cash | wechat | alipay | bank | other
    paid_at: Optional[datetime] = None


class BillingRechargeRequest(BaseModel):
    student_id: int
    paid_amount: float
    payment_method: str
    paid_at: Optional[datetime] = None
    notes: Optional[str] = None


class BillingRecordResponse(BaseModel):
    id: int
    student_id: int
    student_name: Optional[str] = None
    course_id: Optional[int] = None
    amount: float
    paid_amount: float
    status: str
    payment_method: Optional[str] = None
    paid_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BillingRecordListResponse(BaseModel):
    items: List[BillingRecordResponse]
    total: int
    page: int
    page_size: int
    pages: int


class StudentBillingSummary(BaseModel):
    student_id: int
    student_name: str
    receivable: float
    paid: float
    outstanding: float


class BillingSummaryResponse(BaseModel):
    period: dict
    total_receivable: float
    total_paid: float
    total_outstanding: float
    by_student: List[StudentBillingSummary]
    by_subject: List[dict]
    monthly_trend: List[dict]


class OutstandingStudent(BaseModel):
    student_id: int
    student_name: str
    grade: str
    outstanding_amount: float
    unpaid_count: int
