from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


class AccountPaymentRecord(BaseModel):
    record_id: int
    amount: float
    paid_at: Optional[datetime] = None
    payment_method: Optional[str] = None
    notes: Optional[str] = None


class AccountChargeRecord(BaseModel):
    record_id: int
    course_id: Optional[int] = None
    subject: Optional[str] = None
    amount: float
    created_at: datetime
    notes: Optional[str] = None


class StudentAccountResponse(BaseModel):
    student_id: int
    student_name: str
    grade: str
    current_balance: float
    total_received: float
    total_charged: float
    estimated_lessons_left: float
    main_subject: Optional[str] = None
    main_subject_hourly_rate: Optional[float] = None
    has_payment_alert: bool
    next_course_id: Optional[int] = None
    next_course_time: Optional[datetime] = None
    next_course_subject: Optional[str] = None
    next_course_projected_charge: Optional[float] = None
    recent_payments: List[AccountPaymentRecord]
    recent_charges: List[AccountChargeRecord]
