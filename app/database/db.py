from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)

from app.database.schema import Base
from app.config import DATABASE_URL_ASYNC


"""
Create an async engine.
Defaults to SQLite with aiosqlite driver if DATABASE_URL_ASYNC is not provided.
"""
engine = create_async_engine(DATABASE_URL_ASYNC)

# Create a session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def init_db() -> None:
    """Create all tables if they do not exist (for SQLite learning mode)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
