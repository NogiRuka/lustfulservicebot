from sqlalchemy import select, delete, func

from app.database.schema import User
from app.database.db import get_db
from loguru import logger


async def get_count_of_users() -> int:
    async for session in get_db():
        try:
            # Use func.count() to get the count of users
            result = await session.execute(select(func.count()).select_from(User))
            count = result.scalar()  # Get the scalar result (the count)
            return count
        except Exception as e:
            logger.error(f"Error getting count of users: {e}")
            await session.rollback()
            return 0


async def get_user_data(chat_id: int) -> User:
    async for session in get_db():
        try:
            result = await session.execute(select(User).filter_by(chat_id=chat_id))
            user = result.scalars().first()
            return user
        except Exception as e:
            logger.error(e)
            await session.rollback()
            return False


async def get_all_users_id() -> list[int]:
    async for session in get_db():
        try:
            result = await session.execute(select(User.chat_id))
            users = result.scalars().all()
            return users
        except Exception as e:
            logger.error(e)
            await session.rollback()
            return []


async def remove_user(chat_id: int) -> bool:
    async for session in get_db():
        try:
            await session.execute(delete(User).filter_by(chat_id=chat_id))
            await session.commit()
            return True
        except Exception as e:
            logger.error(e)
            await session.rollback()
            return False
