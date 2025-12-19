from datetime import datetime
from zoneinfo import ZoneInfo
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from sqlalchemy import select
from app.models.models import Task, TaskExecution, FrequencyType
from app.core.database import async_session_maker
from app.core.config import get_settings
from app.services.email_service import send_task_result
from app.services.ai_service import ai_service


class SchedulerService:
    def __init__(self):
        settings = get_settings()
        self.default_timezone = ZoneInfo(settings.timezone)  # 默认时区
        self.scheduler = AsyncIOScheduler(timezone=self.default_timezone)
        self._task_emails: dict[int, str] = {}  # task_id -> user_email

    def _get_task_timezone(self, task: Task) -> ZoneInfo:
        """获取任务的时区，如果未指定则使用默认时区"""
        if task.timezone:
            try:
                return ZoneInfo(task.timezone)
            except Exception:
                print(f"[Scheduler] 无效时区 '{task.timezone}'，使用默认时区")
                return self.default_timezone
        return self.default_timezone

    def start(self):
        """启动调度器"""
        if not self.scheduler.running:
            self.scheduler.start()
            print(f"[Scheduler] 调度器已启动，默认时区: {self.default_timezone}")

    def shutdown(self):
        """停止调度器"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            print("[Scheduler] 调度器已停止")

    async def load_tasks_from_db(self):
        """从数据库加载所有活跃任务"""
        async with async_session_maker() as db:
            from app.models.models import User
            result = await db.execute(
                select(Task, User.email)
                .join(User, Task.user_id == User.id)
                .where(Task.is_active == True)
            )
            for task, email in result:
                await self.add_task(task, email)
        print("[Scheduler] 已从数据库加载任务")

    def _get_trigger(self, task: Task):
        """根据任务频率获取触发器"""
        hour, minute = map(int, task.scheduled_time.split(":"))
        task_tz = self._get_task_timezone(task)  # 使用任务时区

        if task.frequency == FrequencyType.ONCE:
            # 一次性任务：使用日期触发器
            if task.scheduled_date:
                # 使用用户指定的日期
                year, month, day = map(int, task.scheduled_date.split("-"))
                run_date = datetime(year, month, day, hour, minute, 0, tzinfo=task_tz)
            else:
                # 未指定日期时，使用当前日期
                now = datetime.now(task_tz)
                run_date = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if run_date <= now:
                    from datetime import timedelta
                    run_date += timedelta(days=1)
            return DateTrigger(run_date=run_date, timezone=task_tz)

        elif task.frequency == FrequencyType.DAILY:
            return CronTrigger(hour=hour, minute=minute, timezone=task_tz)

        elif task.frequency == FrequencyType.WEEKLY:
            # 每周执行，使用用户指定的星期几
            day_of_week = task.day_of_week or "mon"
            return CronTrigger(day_of_week=day_of_week, hour=hour, minute=minute, timezone=task_tz)

        elif task.frequency == FrequencyType.MONTHLY:
            # 每月指定日期执行
            day = task.day_of_month or 1
            return CronTrigger(day=day, hour=hour, minute=minute, timezone=task_tz)

        elif task.frequency == FrequencyType.YEARLY:
            # 每年指定日期执行
            if task.scheduled_date:
                # 解析日期，提取月和日
                _, month, day = map(int, task.scheduled_date.split("-"))
                return CronTrigger(month=month, day=day, hour=hour, minute=minute, timezone=task_tz)
            else:
                # 默认1月1日
                return CronTrigger(month=1, day=1, hour=hour, minute=minute, timezone=task_tz)

        return CronTrigger(hour=hour, minute=minute, timezone=task_tz)

    async def add_task(self, task: Task, user_email: str):
        """添加任务到调度器"""
        job_id = f"task_{task.id}"

        # 先移除已存在的同ID任务
        existing_job = self.scheduler.get_job(job_id)
        if existing_job:
            self.scheduler.remove_job(job_id)

        if not task.is_active:
            return

        self._task_emails[task.id] = user_email

        trigger = self._get_trigger(task)
        self.scheduler.add_job(
            self._execute_task,
            trigger=trigger,
            id=job_id,
            args=[task.id],
            name=task.name,
            replace_existing=True,
        )

        # 更新下次执行时间
        job = self.scheduler.get_job(job_id)
        if job and job.next_run_time:
            async with async_session_maker() as db:
                result = await db.execute(select(Task).where(Task.id == task.id))
                db_task = result.scalar_one_or_none()
                if db_task:
                    db_task.next_run = job.next_run_time
                    await db.commit()
            task_tz = self._get_task_timezone(task)
            print(f"[Scheduler] 已添加任务: {task.name} (ID: {task.id}), 时区: {task_tz}, 下次执行: {job.next_run_time}")
        else:
            print(f"[Scheduler] 已添加任务: {task.name} (ID: {task.id}), 无下次执行时间")

    async def update_task(self, task: Task, user_email: str):
        """更新调度器中的任务"""
        await self.add_task(task, user_email)

    async def remove_task(self, task_id: int):
        """从调度器移除任务"""
        job_id = f"task_{task_id}"
        existing_job = self.scheduler.get_job(job_id)
        if existing_job:
            self.scheduler.remove_job(job_id)
            print(f"[Scheduler] 已移除任务: {task_id}")

        if task_id in self._task_emails:
            del self._task_emails[task_id]

    async def _execute_task(self, task_id: int):
        """执行任务"""
        async with async_session_maker() as db:
            from app.models.models import User

            result = await db.execute(select(Task).where(Task.id == task_id))
            task = result.scalar_one_or_none()

            if not task:
                print(f"[Scheduler] 任务不存在: {task_id}")
                return

            print(f"[Scheduler] 开始执行任务: {task.name}")

            execution = TaskExecution(
                task_id=task_id,
                status="pending",
            )
            db.add(execution)
            await db.commit()

            try:
                # 模拟任务执行（实际项目中可以调用AI接口）
                result_text = await self._process_task_prompt(task.prompt, task.expert_mode)

                # 更新执行记录
                execution.status = "success"
                execution.result = result_text

                # 更新任务状态
                task.last_run = datetime.utcnow()
                task.last_result = result_text

                # 计算下次执行时间
                job = self.scheduler.get_job(f"task_{task_id}")
                if job and job.next_run_time:
                    task.next_run = job.next_run_time
                elif task.frequency == FrequencyType.ONCE:
                    task.is_active = False
                    task.next_run = None

                await db.commit()

                # 发送邮件通知
                user_email = self._task_emails.get(task_id)
                # 如果内存中没有邮箱信息，从数据库查询
                if not user_email:
                    user_result = await db.execute(select(User.email).where(User.id == task.user_id))
                    user_email = user_result.scalar_one_or_none()

                if user_email:
                    await send_task_result(user_email, task.name, result_text)
                else:
                    print(f"[Scheduler] 未找到用户邮箱，跳过发送")

                print(f"[Scheduler] 任务执行成功: {task.name}")

            except Exception as e:
                execution.status = "failed"
                execution.error_message = str(e)
                await db.commit()
                print(f"[Scheduler] 任务执行失败: {task.name}, 错误: {e}")

    async def _process_task_prompt(self, prompt: str, expert_mode: bool) -> str:
        """处理任务提示词，调用AI服务"""
        print(f"[Scheduler] 调用AI服务处理任务指令...")
        result = await ai_service.chat_completion(
            prompt=prompt,
            expert_mode=expert_mode,
        )
        return result


# 全局调度器实例
scheduler_service = SchedulerService()
