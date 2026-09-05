from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings


import sys
from sqlalchemy.pool import NullPool
from app.models.base import Base

pool_args = {"poolclass": NullPool} if "pytest" in sys.modules else {"pool_pre_ping": True}
engine = create_async_engine(settings.database_url, future=True, **pool_args)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
