from datetime import datetime
from sqlalchemy import String, DateTime, Boolean, Text, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
import enum


class FrequencyType(str, enum.Enum):
    ONCE = "once"          # 一次
    DAILY = "daily"        # 每天
    WEEKLY = "weekly"      # 每周
    MONTHLY = "monthly"    # 每月
    YEARLY = "yearly"      # 每年


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_login: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class VerificationCode(Base):
    __tablename__ = "verification_codes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), index=True)
    code: Mapped[str] = mapped_column(String(6))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False)


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(index=True)
    name: Mapped[str] = mapped_column(String(255))
    frequency: Mapped[FrequencyType] = mapped_column(SQLEnum(FrequencyType))
    scheduled_time: Mapped[str] = mapped_column(String(10))  # HH:MM格式
    scheduled_date: Mapped[str | None] = mapped_column(String(10), nullable=True)  # YYYY-MM-DD格式，用于once/yearly
    day_of_week: Mapped[str | None] = mapped_column(String(10), nullable=True)  # mon/tue/wed...，用于weekly
    day_of_month: Mapped[int | None] = mapped_column(nullable=True)  # 1-31，用于monthly
    prompt: Mapped[str] = mapped_column(Text)
    expert_mode: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_run: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_result: Mapped[str | None] = mapped_column(Text, nullable=True)
    next_run: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class TaskExecution(Base):
    __tablename__ = "task_executions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(index=True)
    executed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    result: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50))  # success, failed, pending
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
