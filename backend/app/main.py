from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.core.config import get_settings
from app.core.database import init_db
from app.api import auth, tasks
from app.services.scheduler_service import scheduler_service

settings = get_settings()

# 静态文件目录（Docker部署时前端构建产物会放在这里）
STATIC_DIR = Path(__file__).parent.parent / "static"


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

# 注册API路由
app.include_router(auth.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "healthy"}


# 挂载静态文件（如果存在）
if STATIC_DIR.exists():
    # 挂载静态资源（js, css, 图片等）
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    # SPA路由：所有非API请求返回index.html
    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str):
        # API请求不处理
        if full_path.startswith("api/"):
            return {"error": "Not Found"}

        # 尝试返回静态文件
        file_path = STATIC_DIR / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)

        # 其他请求返回index.html（SPA路由）
        return FileResponse(STATIC_DIR / "index.html")
else:
    # 开发模式：没有静态文件时显示API信息
    @app.get("/")
    async def root():
        return {"message": "News Task Manager API", "version": "1.0.0"}
