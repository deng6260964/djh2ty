import time
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from app.config import settings
from app.database import check_db_connection, create_tables
from app.routers import auth, students, courses, assignments
from app.routers import feedback, resources, progress, billing
from app.routers import notifications, exam, dashboard


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("启动家教辅助系统后端...")

    # 确保上传目录存在
    import os
    os.makedirs(settings.upload_dir_abs, exist_ok=True)
    logger.info(f"上传目录: {settings.upload_dir_abs}")

    # 检查数据库连接
    db_ok = await check_db_connection()
    if not db_ok:
        logger.warning("数据库连接失败，请检查 PostgreSQL 是否运行")

    # 自动建表（开发环境）
    if settings.DEBUG:
        try:
            await create_tables()
            await _init_default_data()
        except Exception as e:
            logger.error(f"数据表初始化失败: {e}")

    logger.info(f"服务启动成功，API 文档: http://localhost:8000{settings.API_PREFIX}/docs")
    yield
    logger.info("服务已关闭")


async def _init_default_data():
    """初始化默认数据（首次启动）"""
    from app.database import AsyncSessionLocal
    from app.models.user import User
    from app.models.billing import SubjectPrice
    from app.utils.auth import get_password_hash
    from sqlalchemy import select

    async with AsyncSessionLocal() as session:
        # 检查是否已有 admin 用户
        result = await session.execute(
            select(User).where(User.username == "admin")
        )
        if not result.scalar_one_or_none():
            admin = User(
                username="admin",
                hashed_password=get_password_hash("admin123"),
                role="admin",
                display_name="管理员",
                is_active=True,
            )
            session.add(admin)
            logger.info("创建默认管理员账户 admin/admin123")

        # 初始化科目单价
        price_result = await session.execute(select(SubjectPrice))
        if not price_result.scalars().first():
            default_prices = [
                ("数学", 150.00),
                ("英语", 150.00),
                ("物理", 150.00),
                ("化学", 150.00),
                ("语文", 120.00),
                ("生物", 130.00),
                ("历史", 120.00),
                ("地理", 120.00),
            ]
            for subject, price in default_prices:
                session.add(SubjectPrice(subject=subject, price_per_hour=price))
            logger.info("初始化默认科目单价")

        await session.commit()


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.APP_NAME,
    description="家教辅助系统后端 API - 支持学生管理、排课、作业、收费等功能",
    version="1.0.0",
    docs_url=f"{settings.API_PREFIX}/docs",
    redoc_url=f"{settings.API_PREFIX}/redoc",
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
    lifespan=lifespan,
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else ["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()

    logger.info(f"[{request_id}] {request.method} {request.url.path}")

    response = await call_next(request)

    duration = round((time.time() - start_time) * 1000, 2)
    logger.info(f"[{request_id}] {response.status_code} ({duration}ms)")

    response.headers["X-Request-Id"] = request_id
    return response


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"未处理的异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "code": "INTERNAL_ERROR",
            "message": "服务器内部错误，请稍后重试",
        }
    )


# 注册路由
prefix = settings.API_PREFIX
app.include_router(auth.router, prefix=prefix)
app.include_router(students.router, prefix=prefix)
app.include_router(courses.router, prefix=prefix)
app.include_router(assignments.router, prefix=prefix)
app.include_router(feedback.router, prefix=prefix)
app.include_router(resources.router, prefix=prefix)
app.include_router(progress.router, prefix=prefix)
app.include_router(billing.router, prefix=prefix)
app.include_router(notifications.router, prefix=prefix)
app.include_router(exam.router, prefix=prefix)
app.include_router(dashboard.router, prefix=prefix)


# 健康检查（无需认证）
@app.get(f"{prefix}/health", tags=["健康检查"])
async def health_check():
    return {"status": "ok", "service": settings.APP_NAME}


# 根路径重定向
@app.get("/", include_in_schema=False)
async def root():
    return {"message": f"欢迎使用{settings.APP_NAME}，API 文档: {settings.API_PREFIX}/docs"}
