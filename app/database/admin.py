from sqlalchemy import select, delete, func

from app.database.schema import User
from app.database.db import get_db
from loguru import logger


async def get_count_of_users() -> int:
    """获取用户总数。"""
    async for session in get_db():
        try:
            result = await session.execute(select(func.count()).select_from(User))
            count = result.scalar()
            return count
        except Exception as e:
            logger.error(f"获取用户总数失败: {e}")
            await session.rollback()
            return 0


async def get_user_data(chat_id: int) -> User:
    """根据 chat_id 获取用户信息。失败返回 False（维持兼容）。"""
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
    """获取所有用户的 chat_id 列表。"""
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
    """按 chat_id 删除用户。"""
    async for session in get_db():
        try:
            await session.execute(delete(User).filter_by(chat_id=chat_id))
            await session.commit()
            return True
        except Exception as e:
            logger.error(e)
            await session.rollback()
            return False
