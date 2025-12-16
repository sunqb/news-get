from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.models import Task, TaskExecution, User
from app.schemas.schemas import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskListResponse,
    TaskExecutionResponse,
    MessageResponse,
)
from app.services.scheduler_service import scheduler_service

router = APIRouter(prefix="/tasks", tags=["任务管理"])


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的所有任务"""
    result = await db.execute(
        select(Task)
        .where(Task.user_id == current_user.id)
        .order_by(Task.created_at.desc())
    )
    tasks = result.scalars().all()
    return TaskListResponse(tasks=tasks, total=len(tasks))


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建新任务"""
    task = Task(
        user_id=current_user.id,
        name=task_data.name,
        frequency=task_data.frequency,
        scheduled_time=task_data.scheduled_time,
        scheduled_date=task_data.scheduled_date,
        day_of_week=task_data.day_of_week,
        day_of_month=task_data.day_of_month,
        prompt=task_data.prompt,
        expert_mode=task_data.expert_mode,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)

    # 添加到调度器（会更新 next_run）
    await scheduler_service.add_task(task, current_user.email)

    # 重新获取任务以包含更新后的 next_run
    await db.refresh(task)

    return task


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取单个任务详情"""
    result = await db.execute(
        select(Task).where(
            and_(Task.id == task_id, Task.user_id == current_user.id)
        )
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在",
        )
    return task


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新任务"""
    result = await db.execute(
        select(Task).where(
            and_(Task.id == task_id, Task.user_id == current_user.id)
        )
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在",
        )

    # 更新字段
    update_data = task_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)

    task.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(task)

    # 更新调度器中的任务（会更新 next_run）
    await scheduler_service.update_task(task, current_user.email)

    # 重新获取任务以包含更新后的 next_run
    await db.refresh(task)

    return task


@router.delete("/{task_id}", response_model=MessageResponse)
async def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除任务"""
    result = await db.execute(
        select(Task).where(
            and_(Task.id == task_id, Task.user_id == current_user.id)
        )
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在",
        )

    # 从调度器中移除
    await scheduler_service.remove_task(task_id)

    await db.delete(task)
    await db.commit()

    return MessageResponse(message="任务已删除")


@router.post("/{task_id}/toggle", response_model=TaskResponse)
async def toggle_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """切换任务启用/禁用状态"""
    result = await db.execute(
        select(Task).where(
            and_(Task.id == task_id, Task.user_id == current_user.id)
        )
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在",
        )

    task.is_active = not task.is_active
    task.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(task)

    # 更新调度器
    if task.is_active:
        await scheduler_service.add_task(task, current_user.email)
        # 重新获取任务以包含更新后的 next_run
        await db.refresh(task)
    else:
        await scheduler_service.remove_task(task_id)
        task.next_run = None
        await db.commit()
        await db.refresh(task)

    return task


@router.post("/{task_id}/test", response_model=MessageResponse)
async def test_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """立即测试执行任务"""
    result = await db.execute(
        select(Task).where(
            and_(Task.id == task_id, Task.user_id == current_user.id)
        )
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在",
        )

    # 立即执行任务
    await scheduler_service._execute_task(task_id)

    return MessageResponse(message="任务测试已触发，结果将发送到您的邮箱")


@router.get("/{task_id}/executions", response_model=list[TaskExecutionResponse])
async def get_task_executions(
    task_id: int,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取任务执行历史"""
    # 验证任务属于当前用户
    task_result = await db.execute(
        select(Task).where(
            and_(Task.id == task_id, Task.user_id == current_user.id)
        )
    )
    if not task_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在",
        )

    result = await db.execute(
        select(TaskExecution)
        .where(TaskExecution.task_id == task_id)
        .order_by(TaskExecution.executed_at.desc())
        .limit(limit)
    )
    return result.scalars().all()
