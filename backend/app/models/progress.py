from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from sqlalchemy import String, DateTime, Text, Integer, ForeignKey, Date, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.database import Base


class Grade(Base):
    __tablename__ = "grades"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False
    )
    subject: Mapped[str] = mapped_column(String(50), nullable=False)
    exam_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # quiz | midterm | final | mock | other
    exam_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    full_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=100)
    exam_date: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())


class KnowledgePoint(Base):
    __tablename__ = "knowledge_points"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False
    )
    subject: Mapped[str] = mapped_column(String(50), nullable=False)
    chapter: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    point_name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="todo")
    # todo | learning | mastered
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
