from pydantic import BaseModel, EmailStr
from datetime import datetime
from app.models.models import FrequencyType


# 验证码相关
class SendCodeRequest(BaseModel):
    email: EmailStr


class VerifyCodeRequest(BaseModel):
    email: EmailStr
    code: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# 用户相关
class UserResponse(BaseModel):
    id: int
    email: str
    created_at: datetime
    last_login: datetime | None

    class Config:
        from_attributes = True


# 任务相关
class TaskCreate(BaseModel):
    name: str
    frequency: FrequencyType
    scheduled_time: str  # HH:MM格式
    scheduled_date: str | None = None  # YYYY-MM-DD格式，用于once/yearly
    day_of_week: str | None = None  # mon/tue/wed...，用于weekly
    day_of_month: int | None = None  # 1-31，用于monthly
    prompt: str
    expert_mode: bool = False
    timezone: str | None = None  # 用户时区，如 Asia/Shanghai


class TaskUpdate(BaseModel):
    name: str | None = None
    frequency: FrequencyType | None = None
    scheduled_time: str | None = None
    scheduled_date: str | None = None
    day_of_week: str | None = None
    day_of_month: int | None = None
    prompt: str | None = None
    expert_mode: bool | None = None
    is_active: bool | None = None
    timezone: str | None = None  # 用户时区


class TaskResponse(BaseModel):
    id: int
    name: str
    frequency: FrequencyType
    scheduled_time: str
    scheduled_date: str | None
    day_of_week: str | None
    day_of_month: int | None
    prompt: str
    expert_mode: bool
    is_active: bool
    timezone: str | None  # 用户时区
    created_at: datetime
    updated_at: datetime
    last_run: datetime | None
    last_result: str | None
    next_run: datetime | None

    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    tasks: list[TaskResponse]
    total: int


# 任务执行记录
class TaskExecutionResponse(BaseModel):
    id: int
    task_id: int
    executed_at: datetime
    result: str | None
    status: str
    error_message: str | None

    class Config:
        from_attributes = True


# 通用响应
class MessageResponse(BaseModel):
    message: str
    success: bool = True
