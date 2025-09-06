import asyncio
from app.database.db import engine
from app.database.schema import Base

async def create_tables():
    """创建数据库表"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("数据库表创建完成")

if __name__ == "__main__":
    asyncio.run(create_tables())