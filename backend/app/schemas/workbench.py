from datetime import datetime, date
from typing import Optional, List

from pydantic import BaseModel


class WorkbenchCourseItem(BaseModel):
    id: int
    student_id: int
    student_name: str
    subject: str
    start_time: datetime
    end_time: datetime
    status: str
    current_balance: float
    projected_charge: float
    needs_payment: bool


class WorkbenchPendingRecordItem(BaseModel):
    id: int
    student_id: int
    student_name: str
    subject: str
    start_time: datetime
    end_time: datetime
    status: str
    current_balance: float
    projected_charge: float
    needs_payment: bool


class WorkbenchPaymentAlertItem(BaseModel):
    student_id: int
    student_name: str
    grade: str
    current_balance: float
    next_course_id: int
    next_course_time: datetime
    next_course_subject: str
    projected_charge: float
    shortage_amount: float


class WorkbenchAssignmentItem(BaseModel):
    assignment_id: int
    assignment_title: str
    student_id: int
    student_name: str
    subject: str
    submitted_at: Optional[datetime] = None
    status: str


class WorkbenchSummary(BaseModel):
    pending_record_count: int
    today_course_count: int
    payment_alert_count: int
    assignment_review_count: int


class WorkbenchResponse(BaseModel):
    today: date
    summary: WorkbenchSummary
    today_courses: List[WorkbenchCourseItem]
    pending_records: List[WorkbenchPendingRecordItem]
    payment_alerts: List[WorkbenchPaymentAlertItem]
    assignment_reviews: List[WorkbenchAssignmentItem]
