from sqlalchemy import select, update, func
from datetime import datetime
from loguru import logger

from app.database.db import get_db
from app.database.schema import User
from app.utils.roles import ROLE_USER, ROLE_ADMIN, ROLE_SUPERADMIN
from app.config import SUPERADMIN_ID


async def add_user(chat_id: int, full_name: str, username: str | None) -> bool:
    """
    添加用户到数据库（若不存在则创建）。
    """
    async for session in get_db():
        try:
            # Check if the user already exists
            result = await session.execute(select(User).filter_by(chat_id=chat_id))
            is_exists = result.scalars().first()

            if not is_exists:
                safe_username = username if username else f"user_{chat_id}"
                new_user = User(
                    chat_id=chat_id,
                    full_name=full_name,
                    username=safe_username,
                    role=ROLE_USER,
                )
                session.add(new_user)
                await session.commit()  # Commit the transaction
                return True
            return False
        except Exception as e:
            logger.error(f"Error adding user: {e}")
            await session.rollback()  # Rollback in case of error
            return False


async def get_user(chat_id: int) -> User | None:
    """根据 chat_id 获取用户。找不到返回 None。"""
    async for session in get_db():
        try:
            result = await session.execute(select(User).filter_by(chat_id=chat_id))
            user = result.scalars().first()
            return user
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            await session.rollback()
            return None


async def set_role(chat_id: int, role: str) -> bool:
    """设置用户角色。"""
    async for session in get_db():
        try:
            await session.execute(
                update(User).filter_by(chat_id=chat_id).values(role=role)
            )
            await session.commit()
            return True
        except Exception as e:
            logger.error(f"Error setting role: {e}")
            await session.rollback()
            return False


async def get_role(chat_id: int) -> str:
    """获取用户角色，默认 user。"""
    async for session in get_db():
        try:
            # 环境层：超管唯一 ID 拥有最高权限
            if SUPERADMIN_ID is not None and chat_id == SUPERADMIN_ID:
                return ROLE_SUPERADMIN
            result = await session.execute(select(User).filter_by(chat_id=chat_id))
            user = result.scalars().first()
            return user.role if user and user.role else ROLE_USER
        except Exception as e:
            logger.error(f"Error getting role: {e}")
            await session.rollback()
            return ROLE_USER


async def set_busy(chat_id: int, is_busy: bool) -> None:
    """设置用户忙碌状态。"""
    async for session in get_db():
        try:
            await session.execute(
                update(User).filter_by(chat_id=chat_id).values(is_busy=is_busy)
            )
            await session.commit()
        except Exception as e:
            logger.error(f"Error setting busy status: {e}")
            await session.rollback()


async def get_busy(chat_id: int) -> bool:
    """获取用户忙碌状态，默认 False。"""
    async for session in get_db():
        try:
            result = await session.execute(select(User).filter_by(chat_id=chat_id))
            user = result.scalars().first()
            return user.is_busy if user else False
        except Exception as e:
            logger.error(f"Error getting busy status: {e}")
            await session.rollback()
            return False


async def update_last_acitivity(chat_id: int) -> None:
    """更新用户最近活跃时间为当前。"""
    async for session in get_db():
        try:
            await session.execute(
                update(User)
                .filter_by(chat_id=chat_id)
                .values(last_activity_at=func.now())
            )
            await session.commit()
        except Exception as e:
            logger.error(f"Error updating last activity: {e}")
            await session.rollback()
