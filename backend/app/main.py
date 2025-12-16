from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.core.database import init_db
from app.api import auth, tasks
from app.services.scheduler_service import scheduler_service

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    print("[App] 初始化数据库...")
    await init_db()
    print("[App] 启动调度器...")
    scheduler_service.start()
    await scheduler_service.load_tasks_from_db()
    print("[App] 应用启动完成")

    yield

    # 关闭时
    print("[App] 停止调度器...")
    scheduler_service.shutdown()
    print("[App] 应用已关闭")


app = FastAPI(
    title=settings.app_name,
    description="基于邮箱验证码登录的定时任务管理系统",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")


@app.get("/")
async def root():
    return {"message": "News Task Manager API", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
