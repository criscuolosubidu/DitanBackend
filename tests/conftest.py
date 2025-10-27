"""
测试配置
"""
import pytest
import asyncio
from typing import AsyncGenerator

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.database import Base, get_db
from app.core.auth import hash_password, create_access_token
from app.models.patient import Doctor
from main import app


# 测试数据库 URL（使用内存数据库或独立测试数据库）
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# 创建测试引擎
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
)

# 创建测试会话工厂
test_session_maker = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """创建测试数据库会话"""
    # 创建所有表
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 创建会话
    async with test_session_maker() as session:
        yield session
    
    # 清理所有表
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def test_doctor(db_session: AsyncSession) -> Doctor:
    """创建测试医生"""
    doctor = Doctor(
        username="test_doctor",
        password_hash=hash_password("password123"),
        name="测试医生",
        gender="MALE",
        phone="13900139000",
        department="中医科",
        position="主治医师",
    )
    db_session.add(doctor)
    await db_session.commit()
    await db_session.refresh(doctor)
    return doctor


@pytest.fixture(scope="function")
def auth_token(test_doctor: Doctor) -> str:
    """创建测试认证令牌"""
    return create_access_token(
        data={
            "doctor_id": test_doctor.doctor_id,
            "username": test_doctor.username
        }
    )


@pytest.fixture(scope="function")
def auth_headers(auth_token: str) -> dict:
    """创建认证请求头"""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """创建测试客户端"""
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()

