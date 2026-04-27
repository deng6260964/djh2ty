"""
pytest 全局 Fixtures
使用 SQLite 内存数据库，完全独立于 PostgreSQL 开发数据库。

兼容方案：
  1. 在导入 app 之前，通过猴子补丁将 PostgreSQL 专有类型替换为 SQLite 兼容类型
     - ARRAY → JSONEncodedList（Text + JSON 序列化）
     - JSONB → JSONEncodedDict（Text + JSON 序列化）
  2. 覆盖 app.database 的 engine 和 session_factory，使其指向 SQLite 测试数据库
  3. 覆盖 FastAPI 的 get_db 依赖，注入测试 Session
  4. lifespan 中的 check_db_connection 会连接测试 SQLite，建表也用测试数据库
"""
import json
import pytest
import pytest_asyncio
from datetime import datetime, timedelta, date
from typing import AsyncGenerator

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import Text, TypeDecorator

import sys
import os

# 确保 backend/ 目录在 Python 路径中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# -----------------------------------------------
# 第一步：定义 SQLite 兼容的替代类型
# -----------------------------------------------

class JSONEncodedList(TypeDecorator):
    """将 Python list 序列化为 JSON 字符串存入 SQLite TEXT 字段（替代 ARRAY）"""
    impl = Text
    cache_ok = True

    def __init__(self, *args, **kwargs):
        super().__init__()

    def process_bind_param(self, value, dialect):
        if value is None:
            return "[]"
        return json.dumps(value, ensure_ascii=False)

    def process_result_value(self, value, dialect):
        if value is None:
            return []
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return []


class JSONEncodedDict(TypeDecorator):
    """将 Python dict 序列化为 JSON 字符串存入 SQLite TEXT 字段（替代 JSONB）"""
    impl = Text
    cache_ok = True

    def __init__(self, *args, **kwargs):
        super().__init__()

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return json.dumps(value, ensure_ascii=False)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return None


# -----------------------------------------------
# 第二步：猴子补丁 PostgreSQL 专有类型
# 直接替换为 TypeDecorator 子类，兼容 mapped_column 类型检查
# -----------------------------------------------
import sqlalchemy.dialects.postgresql as pg_dialect

pg_dialect.ARRAY = JSONEncodedList   # type: ignore
pg_dialect.JSONB = JSONEncodedDict   # type: ignore

# -----------------------------------------------
# 第三步：设置环境变量（在 settings 加载前）
# -----------------------------------------------
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:?cache=shared"
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

# -----------------------------------------------
# 第四步：现在可以安全导入 app（所有 model 会使用替代类型）
# -----------------------------------------------
from app.main import app
from app.database import Base, get_db
import app.database as app_database
from app.models.user import User
from app.models.student import Student
from app.models.course import Course
from app.models.assignment import Assignment, AssignmentStudent
from app.models.billing import SubjectPrice, BillingRecord
from app.models.resource import Resource, ResourceShare
from app.utils.auth import get_password_hash

# -----------------------------------------------
# 第五步：替换 app.database 中的全局 engine 和 session_factory
# NullPool：避免 SQLite 不支持 pool_size 的问题
# -----------------------------------------------
from sqlalchemy.pool import StaticPool

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
)

TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# 覆盖 app.database 全局对象（使 lifespan、check_db_connection 等都走 SQLite）
app_database.engine = test_engine
app_database.AsyncSessionLocal = TestSessionLocal


# -----------------------------------------------
# Fixtures
# -----------------------------------------------

@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_test_tables():
    """session 级别：建表（只执行一次，测试结束后清理）"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    """每个测试独立：测试完毕后清空所有表数据，保证测试间隔离"""
    async with TestSessionLocal() as session:
        try:
            yield session
        finally:
            await session.rollback()
            # SQLite StaticPool 共享同一连接，rollback 不可靠
            # 显式清空所有表数据以保证隔离
            for table in reversed(Base.metadata.sorted_tables):
                await session.execute(table.delete())
            await session.commit()
            await session.close()


@pytest_asyncio.fixture
async def async_client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    HTTP 测试客户端。
    通过 override_get_db 将 FastAPI 的 get_db 依赖替换为测试 Session，
    保证 HTTP 请求与测试 fixture 使用同一个数据库 Session。
    """
    async def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    # lifespan=False 跳过应用启动/关闭的 lifespan（避免连接 PostgreSQL）
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def admin_user(db: AsyncSession) -> User:
    """在测试 DB 中创建 admin 用户"""
    user = User(
        username="admin",
        hashed_password=get_password_hash("admin123"),
        role="admin",
        display_name="测试管理员",
        is_active=True,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def auth_headers(async_client: AsyncClient, admin_user: User) -> dict:
    """登录并返回 Bearer Token Headers"""
    resp = await async_client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    assert resp.status_code == 200, f"登录失败: {resp.text}"
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def test_student(db: AsyncSession, admin_user: User) -> Student:
    """测试学生 A（张小明）"""
    student = Student(
        name="张小明",
        grade="初二",
        subjects=["数学", "英语"],
        parent_name="张爸爸",
        parent_phone="13800138000",
        school="实验中学",
        notes="测试学生A",
        is_active=True,
    )
    db.add(student)
    await db.flush()
    await db.refresh(student)
    return student


@pytest_asyncio.fixture
async def test_student_2(db: AsyncSession, admin_user: User) -> Student:
    """测试学生 B（李小红）"""
    student = Student(
        name="李小红",
        grade="高一",
        subjects=["数学", "物理"],
        parent_name="李妈妈",
        parent_phone="13900139000",
        school="第一中学",
        is_active=True,
    )
    db.add(student)
    await db.flush()
    await db.refresh(student)
    return student


@pytest_asyncio.fixture
async def test_course(db: AsyncSession, test_student: Student) -> Course:
    """测试课程：2026-03-02（周一）10:00-11:00，状态 scheduled"""
    course = Course(
        student_id=test_student.id,
        subject="数学",
        start_time=datetime(2026, 3, 2, 10, 0),
        end_time=datetime(2026, 3, 2, 11, 0),
        duration=60,
        status="scheduled",
        location="线上",
        hourly_rate=150.00,
    )
    db.add(course)
    await db.flush()
    await db.refresh(course)
    return course


@pytest_asyncio.fixture
async def test_subject_price(db: AsyncSession) -> SubjectPrice:
    """测试科目单价：数学 150 元/小时"""
    price = SubjectPrice(
        subject="数学",
        price_per_hour=150.00,
    )
    db.add(price)
    await db.flush()
    await db.refresh(price)
    return price
