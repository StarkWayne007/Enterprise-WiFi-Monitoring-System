import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.database.base import Base
from app.database.dependencies import get_db
from app.main import app

TEST_DATABASE_URL = (
    "postgresql+asyncpg://wifi_admin:wifi_dev_password"
    "@localhost:5432/wifi_monitor_test"
)

engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=NullPool,
)

TestSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    yield

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)


@pytest.fixture(autouse=True)
def override_database():
    async def get_test_db():
        async with TestSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = get_test_db

    yield

    app.dependency_overrides.clear()
