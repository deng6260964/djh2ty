from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, Text, Integer, ForeignKey, Boolean, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.database import Base


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    course_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("courses.id", ondelete="SET NULL"), nullable=True
    )
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False
    )
    performance: Mapped[str] = mapped_column(Text, nullable=False)
    knowledge_mastery: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    problems: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    next_plan: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rating: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)  # 1-5
    is_pushed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    pushed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )


class FeedbackTemplate(Base):
    __tablename__ = "feedback_templates"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    performance: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    knowledge_mastery: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    problems: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    next_plan: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
